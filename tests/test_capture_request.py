import json
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from note.knowledge_harness.capture_request import CaptureInput, capture_request


class CaptureRequestTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.output_dir = Path(self.temporary_directory.name) / "requests"
        self.capture_input = CaptureInput(
            run_id="run-20260811-002",
            question_ja="公開Issueから記事候補を安全に受け付けるには？",
            source_ref="issue:7",
            source_kind="public_issue",
            created_at="2026-08-11T08:00:00Z",
        )

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def test_public_issue_is_captured_without_human_action(self) -> None:
        result = capture_request(self.capture_input, self.output_dir)
        saved = json.loads(result.request_path.read_text(encoding="utf-8"))

        self.assertTrue(result.changed)
        self.assertEqual(result.state_after, "CAPTURED")
        self.assertEqual(result.result, "ADVANCE")
        self.assertEqual(saved["required_human_action"], "none")
        self.assertEqual(saved["request"]["question_ja"], self.capture_input.question_ja)

    def test_unconfirmed_input_holds_for_publication_confirmation_only(self) -> None:
        unconfirmed = replace(self.capture_input, source_kind="unconfirmed_input")

        result = capture_request(unconfirmed, self.output_dir)
        saved = json.loads(result.request_path.read_text(encoding="utf-8"))

        self.assertEqual(result.state_after, "HOLD")
        self.assertEqual(saved["reason_codes"], ["PUBLICATION_CONFIRMATION_REQUIRED"])
        self.assertEqual(saved["required_human_action"], "privacy")
        self.assertEqual(saved["next_action"], "公開可能性だけを人間へ確認する")

    def test_identical_rerun_does_not_rewrite(self) -> None:
        first = capture_request(self.capture_input, self.output_dir)
        first_mtime = first.request_path.stat().st_mtime_ns

        second = capture_request(self.capture_input, self.output_dir)

        self.assertFalse(second.changed)
        self.assertEqual(second.request_path.stat().st_mtime_ns, first_mtime)

    def test_same_run_id_updates_existing_request(self) -> None:
        capture_request(self.capture_input, self.output_dir)
        updated = replace(self.capture_input, question_ja="更新した問い")

        result = capture_request(updated, self.output_dir)
        saved = json.loads(result.request_path.read_text(encoding="utf-8"))

        self.assertTrue(result.changed)
        self.assertEqual(saved["request"]["question_ja"], "更新した問い")

    def test_empty_question_is_rejected(self) -> None:
        invalid = replace(self.capture_input, question_ja="  ")

        with self.assertRaisesRegex(ValueError, "question_ja"):
            capture_request(invalid, self.output_dir)


if __name__ == "__main__":
    unittest.main()
