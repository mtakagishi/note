"""O-01〜O-03を横断する最小 Orchestrator。"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Sequence

from note.knowledge_harness.authorize_run import AuthorizationInput, authorize_run
from note.knowledge_harness.capture_request import CaptureInput, capture_request
from note.knowledge_harness.collect_evidence import (
    CollectionLimits,
    EvidenceInput,
    Fetcher,
    collect_evidence,
)
from note.knowledge_harness.screen_safety import SafetyInput, screen_safety
from note.knowledge_harness.storage import json_text, write_if_changed


@dataclass(frozen=True)
class OrchestrationInput:
    """最小オーケストレータへ渡す入力。"""

    run_id: str
    question_ja: str
    source_ref: str
    source_kind: str
    labels: list[str]
    required_label: str
    assessment: str
    restricted_terms: list[str]
    created_at: str
    sources_path: Path | None = None
    evidence_limits: CollectionLimits = CollectionLimits()


@dataclass(frozen=True)
class OrchestrationResult:
    """横断実行結果と保存先。"""

    summary_path: Path
    changed: bool
    state_after: str
    result: str


def _summary_record(
    orchestration_input: OrchestrationInput,
    completed_operations: list[str],
    stop_reason: str | None,
    resume_position: str | None,
    state_after: str,
    result: str,
) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "operation_id": "O-15-a",
        "run_id": orchestration_input.run_id,
        "created_at": orchestration_input.created_at,
        "started_at": orchestration_input.created_at,
        "finished_at": orchestration_input.created_at,
        "execution_order": ["O-01", "O-02", "O-03"],
        "completed_operations": completed_operations,
        "state_after": state_after,
        "result": result,
        "stop_reason": stop_reason,
        "resume_position": resume_position,
        "input_refs": [orchestration_input.source_ref],
        "next_action": "O-04 Collect Evidenceへ渡す" if result == "ADVANCE" else "処理を停止して再開位置を確認する",
    }


def orchestrate_run(
    orchestration_input: OrchestrationInput,
    output_dir: Path,
    *,
    fetcher: Fetcher | None = None,
) -> OrchestrationResult:
    """O-01〜O-04を順に実行し、停止条件に応じて要約を保存する。"""

    run_output_dir = output_dir / orchestration_input.run_id
    completed_operations: list[str] = []
    stop_reason: str | None = None
    resume_position: str | None = None
    state_after = "RECEIVED"
    result = "HOLD"

    capture_input = CaptureInput(
        run_id=orchestration_input.run_id,
        question_ja=orchestration_input.question_ja,
        source_ref=orchestration_input.source_ref,
        source_kind=orchestration_input.source_kind,
        created_at=orchestration_input.created_at,
    )
    capture_result = capture_request(capture_input, output_dir)
    completed_operations.append("O-01")
    state_after = capture_result.state_after
    result = capture_result.result

    if capture_result.state_after != "CAPTURED" or capture_result.result != "ADVANCE":
        stop_reason = "REQUEST_HOLD"
        resume_position = "O-01"
        summary_path = run_output_dir / "orchestration-summary.json"
        record = _summary_record(
            orchestration_input,
            completed_operations,
            stop_reason,
            resume_position,
            state_after,
            result,
        )
        changed = write_if_changed(summary_path, json_text(record))
        return OrchestrationResult(summary_path=summary_path, changed=changed, state_after=state_after, result=result)

    request_path = run_output_dir / "request.json"
    authorization_input = AuthorizationInput(
        request_path=request_path,
        labels=list(orchestration_input.labels),
        required_label=orchestration_input.required_label,
        created_at=orchestration_input.created_at,
    )
    authorization_result = authorize_run(authorization_input, output_dir)
    completed_operations.append("O-02")
    state_after = authorization_result.state_after
    result = authorization_result.result

    if authorization_result.state_after != "AUTHORIZED" or authorization_result.result != "ADVANCE":
        stop_reason = "RUN_LABEL_MISSING"
        resume_position = "O-02"
        summary_path = run_output_dir / "orchestration-summary.json"
        record = _summary_record(
            orchestration_input,
            completed_operations,
            stop_reason,
            resume_position,
            state_after,
            result,
        )
        changed = write_if_changed(summary_path, json_text(record))
        return OrchestrationResult(summary_path=summary_path, changed=changed, state_after=state_after, result=result)

    authorization_path = run_output_dir / "authorization.json"
    safety_input = SafetyInput(
        authorization_path=authorization_path,
        assessment=orchestration_input.assessment,
        restricted_terms=list(orchestration_input.restricted_terms),
        created_at=orchestration_input.created_at,
    )
    safety_result = screen_safety(safety_input, output_dir)
    completed_operations.append("O-03")
    state_after = safety_result.state_after
    result = safety_result.result

    if safety_result.state_after not in {"SCREENED"} or safety_result.result != "ADVANCE":
        stop_reason = "SCREENING_HOLD"
        resume_position = "O-03"
    else:
        if orchestration_input.sources_path is None:
            stop_reason = "EVIDENCE_INPUT_MISSING"
            resume_position = "O-04"
            state_after = "SCREENED"
            result = "HOLD"
        else:
            evidence_input = EvidenceInput(
                screening_path=run_output_dir / "screening.json",
                sources_path=orchestration_input.sources_path,
                created_at=orchestration_input.created_at,
                limits=orchestration_input.evidence_limits,
            )
            evidence_result = collect_evidence(evidence_input, output_dir, fetcher=fetcher)
            completed_operations.append("O-04")
            state_after = evidence_result.state_after
            result = evidence_result.result
            stop_reason = None
            resume_position = None

    summary_path = run_output_dir / "orchestration-summary.json"
    record = _summary_record(
        orchestration_input,
        completed_operations,
        stop_reason,
        resume_position,
        state_after,
        result,
    )
    changed = write_if_changed(summary_path, json_text(record))
    return OrchestrationResult(summary_path=summary_path, changed=changed, state_after=state_after, result=result)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="O-01〜O-03を横断する最小Orchestratorを実行します")
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--question-ja", required=True)
    parser.add_argument("--source-ref", required=True)
    parser.add_argument("--source-kind", required=True, choices=("public_issue", "approved_input", "unconfirmed_input"))
    parser.add_argument("--label", action="append", default=[], dest="labels")
    parser.add_argument("--required-label", default="knowledge-harness:run")
    parser.add_argument("--assessment", choices=("auto", "private", "uncertain"), default="auto")
    parser.add_argument("--restricted-term", action="append", default=[], dest="restricted_terms")
    parser.add_argument("--created-at")
    parser.add_argument("--output-dir", type=Path, default=Path("_notes/knowledge_harness/runs"))
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = _parser()
    args = parser.parse_args(argv)
    orchestration_input = OrchestrationInput(
        run_id=args.run_id,
        question_ja=args.question_ja,
        source_ref=args.source_ref,
        source_kind=args.source_kind,
        labels=args.labels,
        required_label=args.required_label,
        assessment=args.assessment,
        restricted_terms=args.restricted_terms,
        created_at=args.created_at or "2026-08-11T00:00:00Z",
    )
    result = orchestrate_run(orchestration_input, args.output_dir)
    print(f"{result.summary_path} ({result.state_after}/{result.result})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
