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
from note.knowledge_harness.screen_safety import SafetyInput, screen_safety


class ScreenSafetyTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary_directory.name)
        self.authorization_path = self._authorization(
            "安全性を確認してから根拠収集へ進むには？"
        )
        self.output_dir = self.root / "screened"
        self.safety_input = SafetyInput(
            authorization_path=self.authorization_path,
            assessment="auto",
            restricted_terms=[],
            created_at="2026-08-11T10:02:00Z",
        )

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def _authorization(self, question_ja: str, *, run_id: str = "run-20260811-004") -> Path:
        captured = capture_request(
            CaptureInput(
                run_id=run_id,
                question_ja=question_ja,
                source_ref="issue:9",
                source_kind="public_issue",
                created_at="2026-08-11T10:00:00Z",
            ),
            self.root / "requests",
        )
        authorized = authorize_run(
            AuthorizationInput(
                request_path=captured.request_path,
                labels=[DEFAULT_RUN_LABEL],
                required_label=DEFAULT_RUN_LABEL,
                created_at="2026-08-11T10:01:00Z",
            ),
            self.root / "authorized",
        )
        return authorized.authorization_path

    def test_clean_input_advances_without_human_action(self) -> None:
        result = screen_safety(self.safety_input, self.output_dir)
        saved = json.loads(result.screening_path.read_text(encoding="utf-8"))

        self.assertEqual(result.state_after, "SCREENED")
        self.assertEqual(result.result, "ADVANCE")
        self.assertEqual(saved["required_human_action"], "none")
        self.assertEqual(saved["reason_codes"], ["SAFETY_SCREEN_PASSED"])

    def test_maskable_personal_data_is_removed_and_advances(self) -> None:
        email = "person@example.com"
        authorization_path = self._authorization(
            f"連絡先 {email} と 090-1234-5678 を除いて扱う",
            run_id="run-maskable",
        )
        safety_input = replace(self.safety_input, authorization_path=authorization_path)

        result = screen_safety(safety_input, self.output_dir)
        output = result.screening_path.read_text(encoding="utf-8")
        saved = json.loads(output)

        self.assertEqual(result.state_after, "SCREENED")
        self.assertNotIn(email, output)
        self.assertNotIn("090-1234-5678", output)
        self.assertIn("[REDACTED_EMAIL]", saved["screened_request"]["question_ja"])
        self.assertIn("[REDACTED_PHONE]", saved["screened_request"]["question_ja"])

    def test_secret_is_rejected_without_copying_value(self) -> None:
        secret = "ghp_123456789012345678901234567890"
        authorization_path = self._authorization(
            f"token={secret} を使う",
            run_id="run-secret",
        )
        safety_input = replace(self.safety_input, authorization_path=authorization_path)

        result = screen_safety(safety_input, self.output_dir)
        output = result.screening_path.read_text(encoding="utf-8")

        self.assertEqual(result.state_after, "REJECTED")
        self.assertNotIn(secret, output)
        self.assertIn("SECRET_DETECTED", output)

    def test_restricted_marker_is_rejected(self) -> None:
        authorization_path = self._authorization("社外秘の情報を含む", run_id="run-restricted")
        safety_input = replace(self.safety_input, authorization_path=authorization_path)

        result = screen_safety(safety_input, self.output_dir)

        self.assertEqual(result.result, "REJECTED")

    def test_custom_restricted_term_is_rejected(self) -> None:
        authorization_path = self._authorization("PROJECT-CODEの仕様", run_id="run-custom")
        safety_input = replace(
            self.safety_input,
            authorization_path=authorization_path,
            restricted_terms=["PROJECT-CODE"],
        )

        result = screen_safety(safety_input, self.output_dir)

        self.assertEqual(result.result, "REJECTED")

    def test_uncertain_input_is_withheld_and_requests_only_privacy_decision(self) -> None:
        uncertain = replace(self.safety_input, assessment="uncertain")

        result = screen_safety(uncertain, self.output_dir)
        saved = json.loads(result.screening_path.read_text(encoding="utf-8"))

        self.assertEqual(result.state_after, "HOLD")
        self.assertEqual(saved["required_human_action"], "privacy")
        self.assertEqual(saved["screened_request"]["question_ja"], "[WITHHELD_PENDING_CONFIRMATION]")

    def test_identical_rerun_does_not_rewrite(self) -> None:
        first = screen_safety(self.safety_input, self.output_dir)
        first_mtime = first.screening_path.stat().st_mtime_ns

        second = screen_safety(self.safety_input, self.output_dir)

        self.assertFalse(second.changed)
        self.assertEqual(second.screening_path.stat().st_mtime_ns, first_mtime)

    def test_waiting_authorization_cannot_be_screened(self) -> None:
        captured = capture_request(
            CaptureInput(
                run_id="run-waiting",
                question_ja="ラベル待ちの問い",
                source_ref="issue:10",
                source_kind="public_issue",
                created_at="2026-08-11T10:00:00Z",
            ),
            self.root / "requests",
        )
        waiting = authorize_run(
            AuthorizationInput(
                request_path=captured.request_path,
                labels=[],
                required_label=DEFAULT_RUN_LABEL,
                created_at="2026-08-11T10:01:00Z",
            ),
            self.root / "authorized",
        )
        invalid = replace(self.safety_input, authorization_path=waiting.authorization_path)

        with self.assertRaisesRegex(ValueError, "AUTHORIZED / ADVANCE"):
            screen_safety(invalid, self.output_dir)


if __name__ == "__main__":
    unittest.main()
