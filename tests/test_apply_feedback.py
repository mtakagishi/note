import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from note.knowledge_harness.apply_feedback import FeedbackInput, apply_feedback


class ApplyFeedbackTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.decision = self.root / "decision.json"
        self.draft = self.root / "draft.rst"
        self.manifest = self.root / "manifest.json"
        self.proposal = self.root / "proposal.json"
        self.output = self.root / "revisions"
        text = "題名\n====\n\n最初の段落です。\n\n変更しない段落です。\n"
        self.draft.write_text(text, encoding="utf-8")
        decision = {
            "operation_id": "O-11",
            "run_id": "run-feedback",
            "state_after": "REVISION",
            "result": "ADVANCE",
            "human_decision": {
                "decision": "revision",
                "instruction_ja": "冒頭を簡潔にしてください。",
                "target_ja": "冒頭段落",
                "scope": "THIS_ARTICLE_ONLY",
                "source": {
                    "url": "https://github.com/mtakagishi/note/pull/99#issuecomment-1",
                    "reference_id": "comment-1",
                    "target_commit_sha": "abc123",
                },
            },
        }
        sections = [
            {
                "section_id": "s1",
                "blocks": [
                    {
                        "block_id": "b1",
                        "body_rst": "最初の段落です。",
                        "packet_refs": ["fact-1"],
                        "sha256": hashlib.sha256("最初の段落です。".encode()).hexdigest(),
                    },
                    {
                        "block_id": "b2",
                        "body_rst": "変更しない段落です。",
                        "packet_refs": ["fact-2"],
                        "sha256": hashlib.sha256("変更しない段落です。".encode()).hexdigest(),
                    },
                ],
            }
        ]
        manifest = {
            "operation_id": "O-08",
            "run_id": "run-feedback",
            "state_after": "DRAFT_READY",
            "result": "ADVANCE",
            "draft_sha256": hashlib.sha256(text.encode()).hexdigest(),
            "sections": sections,
        }
        proposal = {
            "instruction_ja": "冒頭を簡潔にしてください。",
            "target_ja": "冒頭段落",
            "changes": [{"block_id": "b1", "body_rst": "簡潔な冒頭です。", "packet_refs": ["fact-1"]}],
        }
        self.decision.write_text(json.dumps(decision, ensure_ascii=False), encoding="utf-8")
        self.manifest.write_text(json.dumps(manifest, ensure_ascii=False), encoding="utf-8")
        self.proposal.write_text(json.dumps(proposal, ensure_ascii=False), encoding="utf-8")

    def tearDown(self) -> None:
        self.temp.cleanup()

    def _run(self):
        return apply_feedback(
            FeedbackInput(self.decision, self.draft, self.manifest, self.proposal, "2026-08-11T22:00:00Z"), self.output
        )

    def test_applies_only_requested_block(self) -> None:
        result = self._run()
        revised = result.draft_path.read_text(encoding="utf-8")
        record = json.loads(result.manifest_path.read_text(encoding="utf-8"))
        self.assertEqual((result.state_after, result.result), ("REVISED", "ADVANCE"))
        self.assertIn("簡潔な冒頭です。", revised)
        self.assertIn("変更しない段落です。", revised)
        self.assertEqual(record["revision_count"], 1)
        self.assertEqual(record["revisions"][0]["block_id"], "b1")

    def test_rejects_non_revision_decision(self) -> None:
        raw = json.loads(self.decision.read_text(encoding="utf-8"))
        raw["state_after"] = "HOLD"
        self.decision.write_text(json.dumps(raw), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "REVISION"):
            self._run()

    def test_rejects_run_id_mismatch(self) -> None:
        raw = json.loads(self.manifest.read_text(encoding="utf-8"))
        raw["run_id"] = "other"
        self.manifest.write_text(json.dumps(raw), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "run_id"):
            self._run()

    def test_rejects_draft_sha_mismatch(self) -> None:
        self.draft.write_text("改変", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "SHA-256"):
            self._run()

    def test_rejects_instruction_mismatch(self) -> None:
        raw = json.loads(self.proposal.read_text(encoding="utf-8"))
        raw["instruction_ja"] = "別の指示"
        self.proposal.write_text(json.dumps(raw), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "一致"):
            self._run()

    def test_rejects_unknown_or_duplicate_block(self) -> None:
        raw = json.loads(self.proposal.read_text(encoding="utf-8"))
        raw["changes"][0]["block_id"] = "unknown"
        self.proposal.write_text(json.dumps(raw), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "不明"):
            self._run()

    def test_rejects_packet_reference_change(self) -> None:
        raw = json.loads(self.proposal.read_text(encoding="utf-8"))
        raw["changes"][0]["packet_refs"] = ["new-fact"]
        self.proposal.write_text(json.dumps(raw), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "Packet参照"):
            self._run()

    def test_rejects_unchanged_body(self) -> None:
        raw = json.loads(self.proposal.read_text(encoding="utf-8"))
        raw["changes"][0]["body_rst"] = "最初の段落です。"
        self.proposal.write_text(json.dumps(raw), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "同じ"):
            self._run()

    def test_third_revision_holds_without_applying(self) -> None:
        raw = json.loads(self.manifest.read_text(encoding="utf-8"))
        raw.update({"operation_id": "O-12", "state_after": "REVISED", "revision_count": 2})
        self.manifest.write_text(json.dumps(raw, ensure_ascii=False), encoding="utf-8")
        result = self._run()
        record = json.loads(result.manifest_path.read_text(encoding="utf-8"))
        self.assertEqual((result.state_after, result.result), ("HOLD", "HOLD"))
        self.assertEqual(record["reason_codes"], ["REVISION_LIMIT_EXCEEDED"])
        self.assertEqual(result.draft_path.read_text(encoding="utf-8"), self.draft.read_text(encoding="utf-8"))

    def test_second_revision_is_allowed(self) -> None:
        raw = json.loads(self.manifest.read_text(encoding="utf-8"))
        raw.update({"operation_id": "O-12", "state_after": "REVISED", "revision_count": 1})
        self.manifest.write_text(json.dumps(raw, ensure_ascii=False), encoding="utf-8")
        record = json.loads(self._run().manifest_path.read_text(encoding="utf-8"))
        self.assertEqual(record["revision_count"], 2)

    def test_is_idempotent(self) -> None:
        first = self._run()
        mtime = first.manifest_path.stat().st_mtime_ns
        second = self._run()
        self.assertFalse(second.changed)
        self.assertEqual(mtime, second.manifest_path.stat().st_mtime_ns)


if __name__ == "__main__":
    unittest.main()
