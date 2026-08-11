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
from note.knowledge_harness.collect_evidence import (
    CollectionLimits,
    EvidenceInput,
    FetchResult,
    RetrievalError,
    collect_evidence,
)
from note.knowledge_harness.screen_safety import SafetyInput, screen_safety


class CollectEvidenceTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary_directory.name)
        captured = capture_request(
            CaptureInput(
                run_id="run-evidence",
                question_ja="公開情報を根拠として収集するには？",
                source_ref="issue:2",
                source_kind="public_issue",
                created_at="2026-08-11T11:00:00Z",
            ),
            self.root / "requests",
        )
        authorized = authorize_run(
            AuthorizationInput(
                request_path=captured.request_path,
                labels=[DEFAULT_RUN_LABEL],
                required_label=DEFAULT_RUN_LABEL,
                created_at="2026-08-11T11:01:00Z",
            ),
            self.root / "authorized",
        )
        screened = screen_safety(
            SafetyInput(authorized.authorization_path, "auto", [], "2026-08-11T11:02:00Z"),
            self.root / "screened",
        )
        self.screening_path = screened.screening_path
        self.sources_path = self.root / "sources.json"
        self.output_dir = self.root / "evidence"
        self.evidence_input = EvidenceInput(
            self.screening_path,
            self.sources_path,
            "2026-08-11T11:03:00Z",
        )

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def _write_sources(self, sources: list[dict]) -> None:
        self.sources_path.write_text(
            json.dumps({"sources": sources}, ensure_ascii=False), encoding="utf-8"
        )

    @staticmethod
    def _success(url: str) -> FetchResult:
        return FetchResult(url, 200, "text/html", f"body:{url}".encode())

    def test_collects_classified_sources_and_metrics(self) -> None:
        self._write_sources(
            [
                {
                    "url": "https://docs.example.com/spec",
                    "source_type": "primary",
                    "title": "公式仕様",
                    "publisher": "Example",
                    "summary_ja": "公式仕様の要約",
                    "confidence": "high",
                    "confidence_reason": "公式文書のため",
                    "search_round": 1,
                    "query": "example 公式仕様",
                    "topics": ["仕様"],
                },
                {
                    "url": "https://community.example.net/review",
                    "source_type": "community",
                    "title": "利用者の評価",
                    "contradictions": ["公式説明と性能評価が異なる"],
                    "uncertainties": ["評価時のバージョンが不明"],
                    "search_round": 2,
                    "query": "example 評価",
                },
            ]
        )

        result = collect_evidence(self.evidence_input, self.output_dir, fetcher=self._success)
        saved = json.loads(result.evidence_path.read_text(encoding="utf-8"))

        self.assertEqual((result.state_after, result.result), ("EVIDENCE_READY", "ADVANCE"))
        self.assertEqual(len(saved["evidence"]), 2)
        self.assertEqual(saved["metrics"]["primary_source_rate"], 0.5)
        self.assertEqual(saved["metrics"]["contradiction_sources"], 1)
        self.assertIn("情報源間の矛盾があります。", saved["uncertainties"])
        self.assertNotIn("body:https", result.evidence_path.read_text(encoding="utf-8"))

    def test_deduplicates_urls_and_limits_each_domain(self) -> None:
        self._write_sources(
            [
                {"url": "https://example.com/a#one", "source_type": "primary"},
                {"url": "https://example.com/a#two", "source_type": "primary"},
                {"url": "https://example.com/b", "source_type": "secondary"},
            ]
        )
        limited = replace(
            self.evidence_input,
            limits=CollectionLimits(per_domain=1),
        )

        result = collect_evidence(limited, self.output_dir, fetcher=self._success)
        saved = json.loads(result.evidence_path.read_text(encoding="utf-8"))

        self.assertEqual(len(saved["evidence"]), 1)
        self.assertEqual(saved["metrics"]["excluded"]["DUPLICATE_SOURCE"], 1)
        self.assertEqual(saved["metrics"]["excluded"]["DOMAIN_LIMIT"], 1)

    def test_retries_temporary_failure_and_records_permanent_failure(self) -> None:
        self._write_sources(
            [
                {"url": "https://retry.example/a", "source_type": "primary"},
                {"url": "https://missing.example/b", "source_type": "secondary"},
            ]
        )
        calls: dict[str, int] = {}

        def fetch(url: str) -> FetchResult:
            calls[url] = calls.get(url, 0) + 1
            if "retry" in url and calls[url] == 1:
                raise RetrievalError("timeout", retryable=True)
            if "missing" in url:
                raise RetrievalError("HTTP 404", retryable=False)
            return self._success(url)

        result = collect_evidence(self.evidence_input, self.output_dir, fetcher=fetch)
        saved = json.loads(result.evidence_path.read_text(encoding="utf-8"))

        self.assertEqual(result.result, "ADVANCE")
        self.assertEqual(calls["https://retry.example/a"], 2)
        self.assertEqual(calls["https://missing.example/b"], 1)
        self.assertEqual(saved["retrieval_failures"][0]["reason"], "HTTP 404")

    def test_all_temporary_failures_are_retryable_error(self) -> None:
        self._write_sources([{"url": "https://example.com/a", "source_type": "primary"}])

        def fail(_url: str) -> FetchResult:
            raise RetrievalError("timeout", retryable=True)

        result = collect_evidence(self.evidence_input, self.output_dir, fetcher=fail)
        saved = json.loads(result.evidence_path.read_text(encoding="utf-8"))

        self.assertEqual((result.state_after, result.result), ("SCREENED", "RETRYABLE_ERROR"))
        self.assertEqual(saved["retrieval_failures"][0]["attempts"], 3)

    def test_no_candidates_is_hold_without_human_action(self) -> None:
        self._write_sources([])

        result = collect_evidence(self.evidence_input, self.output_dir, fetcher=self._success)
        saved = json.loads(result.evidence_path.read_text(encoding="utf-8"))

        self.assertEqual((result.state_after, result.result), ("HOLD", "HOLD"))
        self.assertEqual(saved["required_human_action"], "none")

    def test_identical_rerun_does_not_rewrite(self) -> None:
        self._write_sources([{"url": "https://example.com/a", "source_type": "primary"}])
        first = collect_evidence(self.evidence_input, self.output_dir, fetcher=self._success)
        first_mtime = first.evidence_path.stat().st_mtime_ns

        second = collect_evidence(self.evidence_input, self.output_dir, fetcher=self._success)

        self.assertFalse(second.changed)
        self.assertEqual(second.evidence_path.stat().st_mtime_ns, first_mtime)

    def test_completed_scope_stops_before_remaining_candidates(self) -> None:
        self._write_sources(
            [
                {"url": "https://example.com/a", "source_type": "primary", "complete_scope": True},
                {"url": "https://other.example/b", "source_type": "secondary"},
            ]
        )

        result = collect_evidence(self.evidence_input, self.output_dir, fetcher=self._success)
        saved = json.loads(result.evidence_path.read_text(encoding="utf-8"))

        self.assertEqual(len(saved["evidence"]), 1)
        self.assertEqual(saved["metrics"]["excluded"]["EARLY_STOP_SCOPE_COMPLETE"], 1)

    def test_rejects_non_advanced_screening(self) -> None:
        data = json.loads(self.screening_path.read_text(encoding="utf-8"))
        data["result"] = "HOLD"
        self.screening_path.write_text(json.dumps(data), encoding="utf-8")
        self._write_sources([])

        with self.assertRaisesRegex(ValueError, "SCREENED / ADVANCE"):
            collect_evidence(self.evidence_input, self.output_dir, fetcher=self._success)


if __name__ == "__main__":
    unittest.main()
