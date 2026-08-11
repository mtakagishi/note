import json
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from note.knowledge_harness.authorize_run import (
    DEFAULT_RUN_LABEL,
    AuthorizationInput,
    authorize_run,
)
from note.knowledge_harness.capture_request import CaptureInput, capture_request


class AuthorizeRunTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        root = Path(self.temporary_directory.name)
        captured = capture_request(
            CaptureInput(
                run_id="run-20260811-003",
                question_ja="明示的なラベルがあるときだけ実行するには？",
                source_ref="issue:8",
                source_kind="public_issue",
                created_at="2026-08-11T09:00:00Z",
            ),
            root / "requests",
        )
        self.request_path = captured.request_path
        self.output_dir = root / "authorized"
        self.authorization_input = AuthorizationInput(
            request_path=self.request_path,
            labels=[DEFAULT_RUN_LABEL],
            required_label=DEFAULT_RUN_LABEL,
            created_at="2026-08-11T09:01:00Z",
        )

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def test_required_label_authorizes_run(self) -> None:
        result = authorize_run(self.authorization_input, self.output_dir)
        saved = json.loads(result.authorization_path.read_text(encoding="utf-8"))

        self.assertEqual(result.state_after, "AUTHORIZED")
        self.assertEqual(result.result, "ADVANCE")
        self.assertEqual(saved["reason_codes"], ["RUN_LABEL_PRESENT"])
        self.assertEqual(saved["required_human_action"], "none")

    def test_missing_label_keeps_state_without_prompting_human(self) -> None:
        waiting = replace(self.authorization_input, labels=[])

        result = authorize_run(waiting, self.output_dir)
        saved = json.loads(result.authorization_path.read_text(encoding="utf-8"))

        self.assertEqual(result.state_after, "CAPTURED")
        self.assertEqual(result.result, "HOLD")
        self.assertEqual(saved["reason_codes"], ["RUN_LABEL_MISSING"])
        self.assertEqual(saved["required_human_action"], "none")
        self.assertIn("催促しない", saved["next_action"])

    def test_unrelated_labels_do_not_authorize_run(self) -> None:
        waiting = replace(self.authorization_input, labels=["bug", "documentation"])

        result = authorize_run(waiting, self.output_dir)

        self.assertEqual(result.state_after, "CAPTURED")
        self.assertEqual(result.result, "HOLD")

    def test_identical_rerun_does_not_rewrite(self) -> None:
        first = authorize_run(self.authorization_input, self.output_dir)
        first_mtime = first.authorization_path.stat().st_mtime_ns

        second = authorize_run(self.authorization_input, self.output_dir)

        self.assertFalse(second.changed)
        self.assertEqual(second.authorization_path.stat().st_mtime_ns, first_mtime)

    def test_adding_label_updates_same_run(self) -> None:
        waiting = replace(self.authorization_input, labels=[])
        first = authorize_run(waiting, self.output_dir)

        second = authorize_run(self.authorization_input, self.output_dir)
        saved = json.loads(second.authorization_path.read_text(encoding="utf-8"))

        self.assertEqual(first.authorization_path, second.authorization_path)
        self.assertEqual(saved["state_after"], "AUTHORIZED")
        self.assertEqual(len(list(self.output_dir.glob("*/authorization.json"))), 1)

    def test_hold_request_cannot_be_authorized(self) -> None:
        root = Path(self.temporary_directory.name)
        held = capture_request(
            CaptureInput(
                run_id="run-20260811-held",
                question_ja="公開可能性が未確認の問い",
                source_ref="local:input",
                source_kind="unconfirmed_input",
                created_at="2026-08-11T09:00:00Z",
            ),
            root / "requests",
        )
        invalid = replace(self.authorization_input, request_path=held.request_path)

        with self.assertRaisesRegex(ValueError, "CAPTURED / ADVANCE"):
            authorize_run(invalid, self.output_dir)


if __name__ == "__main__":
    unittest.main()
