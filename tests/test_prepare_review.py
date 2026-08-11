import hashlib
import json
import tempfile
import unittest
from datetime import date
from pathlib import Path

from note.knowledge_harness.prepare_review import ReviewInput, prepare_review


class PrepareReviewTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary_directory.name)
        self.posts_dir = self.root / "posts"
        self.output_dir = self.root / "reviews"
        self.draft_path = self.root / "validated.rst"
        self.report_path = self.root / "validation.json"
        self.plan_path = self.root / "plan.json"
        self.packet_path = self.root / "packet.json"
        self.proposal_path = self.root / "proposal.json"
        self.created_at = "2026-08-11T20:00:00Z"
        self._write_inputs()

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def _draft(self) -> str:
        return """仮の題名
==========

:記事状態: Draft
:公開日: 未確定
:情報基準日: 2026-08-11T10:00:00Z
:対象バージョン: 2.0
:生成動機: 根拠を伝えるため。
:AI担当範囲: Draft生成。
:人間の確認範囲: 最終公開判断。

変更点
------

検証済みの本文です。
"""

    def _write_inputs(self) -> None:
        draft = self._draft()
        self.draft_path.write_text(draft, encoding="utf-8")
        report = {
            "operation_id": "O-09",
            "run_id": "run-review",
            "state_after": "VALIDATED",
            "result": "ADVANCE",
            "validated_draft_sha256": hashlib.sha256(draft.encode()).hexdigest(),
            "human_guidance_ja": {"status_label_ja": "検証合格", "summary_ja": "まだ公開されません。"},
        }
        plan = {
            "operation_id": "O-07",
            "run_id": "run-review",
            "state_after": "PLAN_READY",
            "result": "ADVANCE",
            "central_message_ja": "変更点を安全に確認できます。",
            "sections": [{"section_id": "section-001", "packet_refs": ["topics/topic-001/items/item-001"]}],
        }
        packet = {
            "operation_id": "O-05",
            "run_id": "run-review",
            "state_after": "PACKET_READY",
            "result": "ADVANCE",
            "uncertainties": [{"uncertainty_id": "uncertainty-001", "description_ja": "一部は未確認です。"}],
        }
        proposal = {
            "review_version": "review-v1",
            "preparer_id": "preparer-test",
            "final_title_ja": "変更を安全に確認する方法",
            "slug": "safe-change-review",
            "tags": ["運用", "検証"],
            "category_ja": "運用改善",
            "author": "mtakagishi",
        }
        for path, content in ((self.report_path, report), (self.plan_path, plan), (self.packet_path, packet), (self.proposal_path, proposal)):
            path.write_text(json.dumps(content, ensure_ascii=False), encoding="utf-8")

    def _run(self):
        value = ReviewInput(self.draft_path, self.report_path, self.plan_path, self.packet_path, self.proposal_path, self.created_at, date(2026, 8, 11))
        return prepare_review(value, self.posts_dir, self.output_dir)

    def test_prepares_publication_candidate_and_japanese_review_packet(self) -> None:
        result = self._run()
        article = result.article_path.read_text(encoding="utf-8")
        packet = json.loads(result.review_packet_path.read_text(encoding="utf-8"))
        self.assertEqual(result.article_path.name, "2026-08-12-safe-change-review.rst")
        self.assertIn(".. post:: 2026-08-12", article)
        self.assertIn(":language: ja", article)
        self.assertIn("変更を安全に確認する方法", article)
        self.assertNotIn(":記事状態: Draft", article)
        self.assertEqual(packet["review_summary_ja"]["status"], "公開候補の確認待ち")
        self.assertEqual(len(packet["review_summary_ja"]["choices"]), 4)
        self.assertIn("公開せず", packet["review_summary_ja"]["if_no_response"])
        self.assertEqual((result.state_after, result.result), ("REVIEW_READY", "ADVANCE"))

    def test_uses_first_unused_future_date(self) -> None:
        self.posts_dir.mkdir()
        (self.posts_dir / "2026-08-12-existing.rst").write_text(".. post:: 2026-08-12\n", encoding="utf-8")
        (self.posts_dir / "other.rst").write_text(".. post:: 2026-08-13\n", encoding="utf-8")
        self.assertEqual(self._run().article_path.name, "2026-08-14-safe-change-review.rst")

    def test_rejects_nonvalidated_report(self) -> None:
        report = json.loads(self.report_path.read_text(encoding="utf-8"))
        report["state_after"] = "HOLD"
        report["result"] = "HOLD"
        self.report_path.write_text(json.dumps(report), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "VALIDATED / ADVANCE"):
            self._run()

    def test_rejects_draft_sha_mismatch(self) -> None:
        self.draft_path.write_text(self._draft() + "改変\n", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "SHA-256"):
            self._run()

    def test_rejects_run_id_mismatch(self) -> None:
        plan = json.loads(self.plan_path.read_text(encoding="utf-8"))
        plan["run_id"] = "other-run"
        self.plan_path.write_text(json.dumps(plan), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "run_id"):
            self._run()

    def test_rejects_abnormal_upstream_state(self) -> None:
        plan = json.loads(self.plan_path.read_text(encoding="utf-8"))
        plan["state_after"] = "HOLD"
        self.plan_path.write_text(json.dumps(plan), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "PLAN_READY / ADVANCE"):
            self._run()

    def test_requires_japanese_validation_guidance(self) -> None:
        report = json.loads(self.report_path.read_text(encoding="utf-8"))
        report.pop("human_guidance_ja")
        self.report_path.write_text(json.dumps(report), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "日本語案内"):
            self._run()

    def test_rejects_unsafe_slug(self) -> None:
        proposal = json.loads(self.proposal_path.read_text(encoding="utf-8"))
        proposal["slug"] = "../Unsafe Slug"
        self.proposal_path.write_text(json.dumps(proposal), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "slug"):
            self._run()

    def test_rejects_duplicate_tags(self) -> None:
        proposal = json.loads(self.proposal_path.read_text(encoding="utf-8"))
        proposal["tags"] = ["運用", "運用"]
        self.proposal_path.write_text(json.dumps(proposal), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "重複"):
            self._run()

    def test_preserves_validated_body(self) -> None:
        article = self._run().article_path.read_text(encoding="utf-8")
        self.assertIn("検証済みの本文です。", article)
        self.assertIn(":情報基準日: 2026-08-11T10:00:00Z", article)

    def test_records_integrity_and_pr_dedupe_key(self) -> None:
        result = self._run()
        packet = json.loads(result.review_packet_path.read_text(encoding="utf-8"))
        self.assertEqual(packet["pr_preparation"]["dedupe_key"], "run-review")
        self.assertEqual(packet["pr_preparation"]["head_branch"], "article/run-review")
        self.assertTrue(packet["pr_preparation"]["draft"])
        self.assertEqual(packet["input_integrity"]["validated_draft"]["sha256"], hashlib.sha256(self._draft().encode()).hexdigest())

    def test_is_idempotent(self) -> None:
        first = self._run()
        article_mtime = first.article_path.stat().st_mtime_ns
        packet_mtime = first.review_packet_path.stat().st_mtime_ns
        second = self._run()
        self.assertFalse(second.changed)
        self.assertEqual(article_mtime, second.article_path.stat().st_mtime_ns)
        self.assertEqual(packet_mtime, second.review_packet_path.stat().st_mtime_ns)


if __name__ == "__main__":
    unittest.main()
