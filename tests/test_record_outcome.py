import json
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from note.knowledge_harness.outcomes import Outcome, record_outcome


class RecordOutcomeTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.output_dir = Path(self.temporary_directory.name) / "outcomes"
        self.outcome = Outcome(
            run_id="run-20260811-001",
            input_refs=["issue:2"],
            state_before="VALIDATED",
            state_after="REVIEW_READY",
            result="ADVANCE",
            reason_codes=["DRAFT_PR_READY"],
            summary_ja="Draft PRを作成し、公開判断を待てる状態になりました。",
            uncertainties=[],
            created_at="2026-08-11T00:00:00Z",
            producer="program",
            artifact_refs=["pr:6"],
            verification_refs=["unittest:pass"],
            next_action="人間がDraft PRを確認する",
            human_action="publication",
        )

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def test_creates_outcome_handoff_and_metrics(self) -> None:
        result = record_outcome(self.outcome, self.output_dir)

        self.assertTrue(result.changed)
        saved = json.loads(result.outcome_path.read_text(encoding="utf-8"))
        metrics = json.loads(result.metrics_path.read_text(encoding="utf-8"))
        handoff = result.handoff_path.read_text(encoding="utf-8")
        self.assertEqual(saved["run_id"], self.outcome.run_id)
        self.assertEqual(metrics["total_runs"], 1)
        self.assertEqual(metrics["human_actions"], {"publication": 1})
        self.assertIn("## 次の一手", handoff)
        self.assertIn(self.outcome.summary_ja, handoff)

    def test_identical_rerun_does_not_rewrite_or_duplicate(self) -> None:
        first = record_outcome(self.outcome, self.output_dir)
        first_mtime = first.outcome_path.stat().st_mtime_ns

        second = record_outcome(self.outcome, self.output_dir)
        metrics = json.loads(second.metrics_path.read_text(encoding="utf-8"))

        self.assertFalse(second.changed)
        self.assertEqual(second.outcome_path.stat().st_mtime_ns, first_mtime)
        self.assertEqual(metrics["total_runs"], 1)

    def test_same_run_id_updates_existing_record(self) -> None:
        record_outcome(self.outcome, self.output_dir)
        updated = replace(
            self.outcome,
            state_before="REVIEW_READY",
            state_after="APPROVED",
            result="ADVANCE",
            reason_codes=["PUBLICATION_APPROVED"],
            summary_ja="公開が承認されました。",
            human_action="publication",
        )

        result = record_outcome(updated, self.output_dir)
        metrics = json.loads(result.metrics_path.read_text(encoding="utf-8"))
        saved = json.loads(result.outcome_path.read_text(encoding="utf-8"))

        self.assertTrue(result.changed)
        self.assertEqual(saved["state_after"], "APPROVED")
        self.assertEqual(metrics["total_runs"], 1)
        self.assertEqual(metrics["reason_codes"], {"PUBLICATION_APPROVED": 1})

    def test_rejects_run_id_that_could_escape_output_directory(self) -> None:
        invalid = replace(self.outcome, run_id="../outside")

        with self.assertRaisesRegex(ValueError, "run_id"):
            record_outcome(invalid, self.output_dir)


if __name__ == "__main__":
    unittest.main()
