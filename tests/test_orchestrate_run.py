import json
import tempfile
import unittest
from pathlib import Path

from note.knowledge_harness.collect_evidence import CollectionLimits, FetchResult
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
            sources_path=None,
            evidence_limits=CollectionLimits(search_rounds=1, queries_per_round=1, retrievals=1, adopted_sources=1, per_domain=1, max_seconds=60, retries=0),
        )

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def test_complete_flow_advances_through_all_operations(self) -> None:
        sources_path = self.output_dir / "sources.json"
        sources_path.parent.mkdir(parents=True, exist_ok=True)
        sources_path.write_text(
            json.dumps(
                {
                    "sources": [
                        {
                            "url": "https://example.com/spec",
                            "source_type": "primary",
                            "search_round": 1,
                            "query": "example spec",
                        }
                    ]
                }
            ),
            encoding="utf-8",
        )
        input_with_sources = self.orchestration_input.__class__(
            run_id=self.orchestration_input.run_id,
            question_ja=self.orchestration_input.question_ja,
            source_ref=self.orchestration_input.source_ref,
            source_kind=self.orchestration_input.source_kind,
            labels=self.orchestration_input.labels,
            required_label=self.orchestration_input.required_label,
            assessment=self.orchestration_input.assessment,
            restricted_terms=self.orchestration_input.restricted_terms,
            created_at=self.orchestration_input.created_at,
            sources_path=sources_path,
            evidence_limits=self.orchestration_input.evidence_limits,
        )

        def fetch(url: str) -> FetchResult:
            return FetchResult(url, 200, "text/html", f"body:{url}".encode())

        result = orchestrate_run(input_with_sources, self.output_dir, fetcher=fetch)
        saved = json.loads(result.summary_path.read_text(encoding="utf-8"))

        self.assertTrue(result.changed)
        self.assertEqual(result.state_after, "EVIDENCE_READY")
        self.assertEqual(result.result, "ADVANCE")
        self.assertEqual(saved["completed_operations"], ["O-01", "O-02", "O-03", "O-04"])
        self.assertTrue((self.output_dir / self.orchestration_input.run_id / "request.json").exists())
        self.assertTrue((self.output_dir / self.orchestration_input.run_id / "authorization.json").exists())
        self.assertTrue((self.output_dir / self.orchestration_input.run_id / "screening.json").exists())
        self.assertTrue((self.output_dir / self.orchestration_input.run_id / "evidence.json").exists())

    def test_missing_sources_stops_before_evidence_collection(self) -> None:
        result = orchestrate_run(self.orchestration_input, self.output_dir)
        saved = json.loads(result.summary_path.read_text(encoding="utf-8"))

        self.assertEqual(result.state_after, "SCREENED")
        self.assertEqual(result.result, "HOLD")
        self.assertEqual(saved["completed_operations"], ["O-01", "O-02", "O-03"])
        self.assertEqual(saved["stop_reason"], "EVIDENCE_INPUT_MISSING")
        self.assertEqual(saved["resume_position"], "O-04")

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
