import json
import tempfile
import unittest
from pathlib import Path

from note.knowledge_harness.orchestrate_run import (
    OrchestrationInput,
    OrchestrationResult,
    orchestrate_run,
)


class OrchestrateRunTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.output_dir = Path(self.temporary_directory.name) / "runs"
        self.orchestration_input = OrchestrationInput(
            run_id="run-20260811-003",
            question_ja="公開 Issue から記事候補を安全に取り込むには？",
            source_ref="issue:9",
            source_kind="public_issue",
            labels=["knowledge-harness:run"],
            required_label="knowledge-harness:run",
            assessment="auto",
            restricted_terms=[],
            created_at="2026-08-11T09:00:00Z",
        )

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def test_complete_flow_advances_through_all_operations(self) -> None:
        result = orchestrate_run(self.orchestration_input, self.output_dir)
        saved = json.loads(result.summary_path.read_text(encoding="utf-8"))

        self.assertTrue(result.changed)
        self.assertEqual(result.state_after, "SCREENED")
        self.assertEqual(result.result, "ADVANCE")
        self.assertEqual(saved["completed_operations"], ["O-01", "O-02", "O-03"])
        self.assertTrue((self.output_dir / self.orchestration_input.run_id / "request.json").exists())
        self.assertTrue((self.output_dir / self.orchestration_input.run_id / "authorization.json").exists())
        self.assertTrue((self.output_dir / self.orchestration_input.run_id / "screening.json").exists())

    def test_missing_label_stops_before_screening(self) -> None:
        input_without_label = self.orchestration_input
        input_without_label = input_without_label.__class__(
            run_id=input_without_label.run_id,
            question_ja=input_without_label.question_ja,
            source_ref=input_without_label.source_ref,
            source_kind=input_without_label.source_kind,
            labels=[],
            required_label="knowledge-harness:run",
            assessment=input_without_label.assessment,
            restricted_terms=input_without_label.restricted_terms,
            created_at=input_without_label.created_at,
        )

        result = orchestrate_run(input_without_label, self.output_dir)
        saved = json.loads(result.summary_path.read_text(encoding="utf-8"))

        self.assertEqual(result.state_after, "CAPTURED")
        self.assertEqual(result.result, "HOLD")
        self.assertEqual(saved["completed_operations"], ["O-01", "O-02"])
        self.assertEqual(saved["stop_reason"], "RUN_LABEL_MISSING")
        self.assertEqual(saved["resume_position"], "O-02")
        self.assertFalse((self.output_dir / self.orchestration_input.run_id / "screening.json").exists())

    def test_repeated_run_is_idempotent(self) -> None:
        first = orchestrate_run(self.orchestration_input, self.output_dir)
        second = orchestrate_run(self.orchestration_input, self.output_dir)

        self.assertTrue(first.changed)
        self.assertFalse(second.changed)
        self.assertEqual(second.summary_path.stat().st_mtime_ns, first.summary_path.stat().st_mtime_ns)


if __name__ == "__main__":
    unittest.main()
