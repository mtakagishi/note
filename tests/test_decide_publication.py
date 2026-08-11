import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from note.knowledge_harness.decide_publication import PublicationDecisionInput, decide_publication


class DecidePublicationTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.article = self.root / "article.rst"
        self.packet = self.root / "review.json"
        self.snapshot = self.root / "pr.json"
        self.human = self.root / "human.json"
        self.output = self.root / "decisions"
        self.article.write_text("公開候補です。\n", encoding="utf-8")
        review = {"operation_id": "O-10", "run_id": "run-decision", "state_after": "REVIEW_READY", "result": "ADVANCE", "publication_candidate": {"path": str(self.article), "sha256": hashlib.sha256(self.article.read_bytes()).hexdigest()}, "pr_preparation": {"head_branch": "article/run-decision"}}
        snapshot = {"repository": "mtakagishi/note", "number": 99, "base": "main", "head": "article/run-decision", "head_sha": "abc123", "url": "https://github.com/mtakagishi/note/pull/99", "merged": False, "merged_by": None, "merge_commit_sha": None}
        self.packet.write_text(json.dumps(review), encoding="utf-8")
        self.snapshot.write_text(json.dumps(snapshot), encoding="utf-8")

    def tearDown(self) -> None:
        self.temp.cleanup()

    def _value(self, human: bool = False) -> PublicationDecisionInput:
        return PublicationDecisionInput(self.packet, self.article, self.snapshot, self.human if human else None, "mtakagishi/note", 99, "main", ("mtakagishi",), "2026-08-11T21:00:00Z")

    def _decision(self, kind: str, **extra: object) -> None:
        decision = {"decision": kind, "actor": "mtakagishi", "decided_at": "2026-08-11T20:00:00Z", "reason_ja": "内容を確認しました。", "source": {"url": "https://github.com/mtakagishi/note/pull/99#issuecomment-1", "reference_id": "comment-1", "target_commit_sha": "abc123"}}
        decision.update(extra)
        self.human.write_text(json.dumps({"decisions": [decision]}, ensure_ascii=False), encoding="utf-8")

    def _run(self, human: bool = False):
        return decide_publication(self._value(human), self.output)

    def test_merge_by_authorized_actor_approves(self) -> None:
        snapshot = json.loads(self.snapshot.read_text())
        snapshot.update({"merged": True, "merged_by": "mtakagishi", "merge_commit_sha": "merge123"})
        self.snapshot.write_text(json.dumps(snapshot), encoding="utf-8")
        result = self._run()
        record = json.loads(result.decision_path.read_text(encoding="utf-8"))
        self.assertEqual((result.state_after, result.result), ("APPROVED", "ADVANCE"))
        self.assertEqual(record["human_guidance_ja"]["status_ja"], "公開を承認しました")

    def test_revision_advances_to_o12(self) -> None:
        self._decision("revision", instruction_ja="冒頭を簡潔にしてください。", target_ja="冒頭段落")
        result = self._run(True)
        record = json.loads(result.decision_path.read_text(encoding="utf-8"))
        self.assertEqual(result.state_after, "REVISION")
        self.assertEqual(record["human_decision"]["scope"], "THIS_ARTICLE_ONLY")
        self.assertIn("O-12", record["next_action"])

    def test_reject_holds_without_more_human_action(self) -> None:
        self._decision("reject")
        result = self._run(True)
        record = json.loads(result.decision_path.read_text(encoding="utf-8"))
        self.assertEqual((result.state_after, result.result), ("HOLD", "HOLD"))
        self.assertEqual(record["required_human_action"], "none")

    def test_policy_candidate_holds(self) -> None:
        options = [{"option_ja": "維持", "impact_ja": "公開しません。"}, {"option_ja": "変更", "impact_ja": "今後の規則が変わります。"}]
        self._decision("policy_candidate", problem_ja="恒久方針が必要です。", options=options)
        record = json.loads(self._run(True).decision_path.read_text(encoding="utf-8"))
        self.assertEqual(record["required_human_action"], "policy")
        self.assertEqual(record["human_guidance_ja"]["status_ja"], "方針判断のため保留します")

    def test_no_response_holds(self) -> None:
        record = json.loads(self._run().decision_path.read_text(encoding="utf-8"))
        self.assertEqual(record["reason_codes"], ["NO_HUMAN_RESPONSE"])

    def test_unauthorized_actor_holds(self) -> None:
        self._decision("reject")
        raw = json.loads(self.human.read_text(encoding="utf-8"))
        raw["decisions"][0]["actor"] = "outsider"
        self.human.write_text(json.dumps(raw), encoding="utf-8")
        record = json.loads(self._run(True).decision_path.read_text(encoding="utf-8"))
        self.assertEqual(record["reason_codes"], ["AMBIGUOUS_OR_UNAUTHORIZED_DECISION"])

    def test_commit_mismatch_holds(self) -> None:
        self._decision("reject")
        raw = json.loads(self.human.read_text(encoding="utf-8"))
        raw["decisions"][0]["source"]["target_commit_sha"] = "old"
        self.human.write_text(json.dumps(raw), encoding="utf-8")
        self.assertEqual(self._run(True).result, "HOLD")

    def test_multiple_decisions_hold(self) -> None:
        self._decision("reject")
        raw = json.loads(self.human.read_text(encoding="utf-8"))
        raw["decisions"].append(dict(raw["decisions"][0]))
        self.human.write_text(json.dumps(raw), encoding="utf-8")
        self.assertEqual(self._run(True).result, "HOLD")

    def test_merge_and_decision_conflict_holds(self) -> None:
        self._decision("reject")
        snapshot = json.loads(self.snapshot.read_text())
        snapshot.update({"merged": True, "merged_by": "mtakagishi", "merge_commit_sha": "merge123"})
        self.snapshot.write_text(json.dumps(snapshot), encoding="utf-8")
        self.assertEqual(self._run(True).result, "HOLD")

    def test_rejects_article_sha_mismatch(self) -> None:
        self.article.write_text("改変", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "SHA-256"):
            self._run()

    def test_rejects_pr_identity_mismatch(self) -> None:
        value = PublicationDecisionInput(self.packet, self.article, self.snapshot, None, "other/repo", 99, "main", ("mtakagishi",), "now")
        with self.assertRaisesRegex(ValueError, "repository"):
            decide_publication(value, self.output)

    def test_is_idempotent(self) -> None:
        first = self._run()
        mtime = first.decision_path.stat().st_mtime_ns
        second = self._run()
        self.assertFalse(second.changed)
        self.assertEqual(mtime, second.decision_path.stat().st_mtime_ns)


if __name__ == "__main__":
    unittest.main()
