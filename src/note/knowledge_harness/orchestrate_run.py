"""O-01〜O-03を横断する最小 Orchestrator。"""

from __future__ import annotations

import argparse
import json
from datetime import date, datetime
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Sequence

from note.knowledge_harness.authorize_run import AuthorizationInput, authorize_run
from note.knowledge_harness.build_evidence_packet import PacketInput, build_evidence_packet
from note.knowledge_harness.apply_feedback import FeedbackInput, apply_feedback
from note.knowledge_harness.capture_request import CaptureInput, capture_request
from note.knowledge_harness.collect_evidence import (
    CollectionLimits,
    EvidenceInput,
    Fetcher,
    collect_evidence,
)
from note.knowledge_harness.draft_article import DraftInput, draft_article
from note.knowledge_harness.decide_publication import PublicationDecisionInput, decide_publication
from note.knowledge_harness.judge_candidate import JudgeInput, judge_candidate
from note.knowledge_harness.plan_article import PlanInput, plan_article
from note.knowledge_harness.prepare_review import ReviewInput, prepare_review
from note.knowledge_harness.outcomes import Outcome, record_outcome
from note.knowledge_harness.screen_safety import SafetyInput, screen_safety
from note.knowledge_harness.storage import json_text, write_if_changed
from note.knowledge_harness.validate_draft import ValidationInput, validate_draft


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
    packet_draft_path: Path | None = None
    judgment_path: Path | None = None
    plan_draft_path: Path | None = None
    proposal_path: Path | None = None
    validation_judgment_path: Path | None = None
    review_proposal_path: Path | None = None
    review_as_of_date: date | None = None
    review_posts_dir: Path | None = None
    publication_pr_snapshot_path: Path | None = None
    publication_human_decision_path: Path | None = None
    publication_repository: str | None = None
    publication_pr_number: int | None = None
    publication_base: str = "main"
    publication_authorized_actors: tuple[str, ...] = ()
    feedback_proposal_path: Path | None = None
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
    next_action = _next_action_for_summary(stop_reason, completed_operations, state_after, result)
    return {
        "schema_version": 1,
        "operation_id": "O-15-a",
        "run_id": orchestration_input.run_id,
        "created_at": orchestration_input.created_at,
        "started_at": orchestration_input.created_at,
        "finished_at": orchestration_input.created_at,
        "execution_order": completed_operations,
        "completed_operations": completed_operations,
        "state_after": state_after,
        "result": result,
        "stop_reason": stop_reason,
        "resume_position": resume_position,
        "input_refs": [orchestration_input.source_ref],
        "next_action": next_action,
    }


def _feedback_artifact_paths(run_output_dir: Path) -> tuple[Path, Path]:
    revised_draft_path = run_output_dir / "revised_draft.rst"
    revised_manifest_path = run_output_dir / "revision_manifest.json"
    if revised_draft_path.exists() or revised_manifest_path.exists():
        return revised_draft_path, revised_manifest_path
    return run_output_dir / "draft.rst", run_output_dir / "draft_manifest.json"


def _next_action_for_summary(
    stop_reason: str | None,
    completed_operations: list[str],
    state_after: str,
    result: str,
) -> str:
    if stop_reason == "REQUEST_HOLD":
        return "O-01 Capture Requestの入力を補完して再開する"
    if stop_reason == "RUN_LABEL_MISSING":
        return "O-02 Authorize Runの入力を補完して再開する"
    if stop_reason == "SCREENING_HOLD":
        return "O-03 Safety Screenを再実行して再開する"
    if stop_reason == "EVIDENCE_INPUT_MISSING":
        return "O-04 Collect Evidenceの入力を補完して再開する"
    if stop_reason == "EVIDENCE_COLLECTION_HOLD":
        return "O-04 Collect Evidenceを再実行して再開する"
    if stop_reason == "PACKET_DRAFT_MISSING":
        return "O-05 Evidence Packetの入力を補完して再開する"
    if stop_reason == "PACKET_BUILD_HOLD":
        return "O-05 Evidence Packetを再実行して再開する"
    if stop_reason == "JUDGMENT_INPUT_MISSING":
        return "O-06 Candidate Judgmentの入力を補完して再開する"
    if stop_reason == "CANDIDATE_DECISION_HOLD":
        return "O-06 Candidate Judgmentを再実行して再開する"
    if stop_reason == "PLAN_DRAFT_MISSING":
        return "O-07 Plan Articleの入力を補完して再開する"
    if stop_reason == "PLAN_ARTICLE_HOLD":
        return "O-07 Plan Articleを再実行して再開する"
    if stop_reason == "DRAFT_PROPOSAL_MISSING":
        return "O-08 Draft Articleの入力を補完して再開する"
    if stop_reason == "DRAFT_ARTICLE_HOLD":
        return "O-08 Draft Articleを再実行して再開する"
    if stop_reason == "VALIDATION_JUDGMENT_MISSING":
        return "O-09 Validate Draftの入力を補完して再開する"
    if stop_reason == "VALIDATION_HOLD":
        return "O-09 Validate Draftを再実行して再開する"
    if stop_reason == "REVIEW_PROPOSAL_MISSING":
        return "O-10 Prepare Reviewの入力を補完して再開する"
    if stop_reason == "PREPARE_REVIEW_HOLD":
        return "O-10 Prepare Reviewを再実行して再開する"
    if stop_reason == "PUBLICATION_DECISION_INPUT_MISSING":
        return "O-11 Decide Publicationの入力を補完して再開する"
    if stop_reason == "PUBLICATION_DECISION_HOLD":
        return "O-11 Decide Publicationを再実行して再開する"
    if stop_reason == "FEEDBACK_PROPOSAL_MISSING":
        return "O-12 Apply Feedbackの入力を補完して再開する"
    if stop_reason == "APPLY_FEEDBACK_HOLD":
        return "O-12 Apply Feedbackを再実行して再開する"
    if "O-13" in completed_operations and state_after == "APPROVED" and result == "ADVANCE":
        return "処理完了"
    if state_after == "APPROVED" and result == "ADVANCE":
        return "O-13 Record Outcomeへ渡す"
    if state_after == "REVISED" and result == "ADVANCE":
        return "O-09 Validate Draftへ戻す"
    if state_after == "REVISION" and result == "ADVANCE":
        return "O-12 Apply Feedbackへ渡す"
    if state_after == "REVIEW_READY" and result == "ADVANCE":
        return "O-11 Decide Publicationへ渡す"
    if state_after == "VALIDATED" and result == "ADVANCE":
        return "O-10 Prepare Reviewへ渡す"
    if state_after == "DRAFT_READY" and result == "ADVANCE":
        return "O-09 Validate Draftへ渡す"
    if state_after == "PLAN_READY" and result == "ADVANCE":
        return "O-08 Draft Articleへ渡す"
    if state_after == "CANDIDATE_ACCEPTED" and result == "ADVANCE":
        return "O-07 Plan Articleへ渡す"
    return "処理を停止して再開位置を確認する"


def orchestrate_run(
    orchestration_input: OrchestrationInput,
    output_dir: Path,
    *,
    fetcher: Fetcher | None = None,
) -> OrchestrationResult:
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

            if evidence_result.state_after != "EVIDENCE_READY" or evidence_result.result != "ADVANCE":
                stop_reason = "EVIDENCE_COLLECTION_HOLD"
                resume_position = "O-04"
            elif orchestration_input.packet_draft_path is None:
                stop_reason = "PACKET_DRAFT_MISSING"
                resume_position = "O-05"
                state_after = evidence_result.state_after
                result = "HOLD"
            else:
                packet_input = PacketInput(
                    evidence_path=run_output_dir / "evidence.json",
                    draft_path=orchestration_input.packet_draft_path,
                    created_at=orchestration_input.created_at,
                )
                packet_result = build_evidence_packet(packet_input, output_dir)
                completed_operations.append("O-05")
                state_after = packet_result.state_after
                result = packet_result.result

                if packet_result.state_after != "PACKET_READY" or packet_result.result != "ADVANCE":
                    stop_reason = "PACKET_BUILD_HOLD"
                    resume_position = "O-05"
                elif orchestration_input.judgment_path is None:
                    stop_reason = "JUDGMENT_INPUT_MISSING"
                    resume_position = "O-06"
                    state_after = packet_result.state_after
                    result = "HOLD"
                else:
                    judgment_input = JudgeInput(
                        packet_path=run_output_dir / "evidence_packet.json",
                        judgment_path=orchestration_input.judgment_path,
                        created_at=orchestration_input.created_at,
                    )
                    judgment_result = judge_candidate(judgment_input, output_dir)
                    completed_operations.append("O-06")
                    state_after = judgment_result.state_after
                    result = judgment_result.result

                    if judgment_result.state_after != "CANDIDATE_ACCEPTED" or judgment_result.result != "ADVANCE":
                        stop_reason = "CANDIDATE_DECISION_HOLD"
                        resume_position = "O-06"
                    elif orchestration_input.plan_draft_path is None:
                        stop_reason = "PLAN_DRAFT_MISSING"
                        resume_position = "O-07"
                        state_after = judgment_result.state_after
                        result = "HOLD"
                    else:
                        plan_input = PlanInput(
                            decision_path=run_output_dir / "candidate_decision.json",
                            packet_path=run_output_dir / "evidence_packet.json",
                            draft_path=orchestration_input.plan_draft_path,
                            created_at=orchestration_input.created_at,
                        )
                        plan_result = plan_article(plan_input, output_dir)
                        completed_operations.append("O-07")
                        state_after = plan_result.state_after
                        result = plan_result.result

                        if plan_result.state_after != "PLAN_READY" or plan_result.result != "ADVANCE":
                            stop_reason = "PLAN_ARTICLE_HOLD"
                            resume_position = "O-07"
                        elif orchestration_input.proposal_path is None:
                            stop_reason = "DRAFT_PROPOSAL_MISSING"
                            resume_position = "O-08"
                            state_after = plan_result.state_after
                            result = "HOLD"
                        else:
                            draft_input = DraftInput(
                                plan_path=run_output_dir / "article_plan.json",
                                packet_path=run_output_dir / "evidence_packet.json",
                                proposal_path=orchestration_input.proposal_path,
                                created_at=orchestration_input.created_at,
                            )
                            draft_result = draft_article(draft_input, output_dir)
                            completed_operations.append("O-08")
                            state_after = draft_result.state_after
                            result = draft_result.result

                            if draft_result.state_after != "DRAFT_READY" or draft_result.result != "ADVANCE":
                                stop_reason = "DRAFT_ARTICLE_HOLD"
                                resume_position = "O-08"
                            elif orchestration_input.validation_judgment_path is None:
                                stop_reason = "VALIDATION_JUDGMENT_MISSING"
                                resume_position = "O-09"
                                state_after = draft_result.state_after
                                result = "HOLD"
                            else:
                                validation_input = ValidationInput(
                                    draft_path=run_output_dir / "draft.rst",
                                    manifest_path=run_output_dir / "draft_manifest.json",
                                    plan_path=run_output_dir / "article_plan.json",
                                    packet_path=run_output_dir / "evidence_packet.json",
                                    judgment_path=orchestration_input.validation_judgment_path,
                                    created_at=orchestration_input.created_at,
                                )
                                validation_result = validate_draft(validation_input, output_dir)
                                completed_operations.append("O-09")
                                state_after = validation_result.state_after
                                result = validation_result.result
                                if validation_result.state_after != "VALIDATED" or validation_result.result != "ADVANCE":
                                    stop_reason = "VALIDATION_HOLD"
                                    resume_position = "O-09"
                                elif orchestration_input.review_proposal_path is None:
                                    stop_reason = "REVIEW_PROPOSAL_MISSING"
                                    resume_position = "O-10"
                                    state_after = validation_result.state_after
                                    result = "HOLD"
                                else:
                                    as_of_date = orchestration_input.review_as_of_date
                                    if as_of_date is None:
                                        as_of_date = datetime.fromisoformat(
                                            orchestration_input.created_at.replace("Z", "+00:00")
                                        ).date()
                                    posts_dir = orchestration_input.review_posts_dir or (output_dir / "review_posts")
                                    review_input = ReviewInput(
                                        validated_draft_path=run_output_dir / "validated_draft.rst",
                                        validation_report_path=run_output_dir / "validation_report.json",
                                        plan_path=run_output_dir / "article_plan.json",
                                        packet_path=run_output_dir / "evidence_packet.json",
                                        proposal_path=orchestration_input.review_proposal_path,
                                        created_at=orchestration_input.created_at,
                                        as_of_date=as_of_date,
                                    )
                                    review_result = prepare_review(review_input, posts_dir, output_dir)
                                    completed_operations.append("O-10")
                                    state_after = review_result.state_after
                                    result = review_result.result
                                    if review_result.state_after != "REVIEW_READY" or review_result.result != "ADVANCE":
                                        stop_reason = "PREPARE_REVIEW_HOLD"
                                        resume_position = "O-10"
                                    elif (
                                        orchestration_input.publication_pr_snapshot_path is None
                                        or orchestration_input.publication_repository is None
                                        or orchestration_input.publication_pr_number is None
                                        or not orchestration_input.publication_authorized_actors
                                    ):
                                        stop_reason = "PUBLICATION_DECISION_INPUT_MISSING"
                                        resume_position = "O-11"
                                        state_after = review_result.state_after
                                        result = "HOLD"
                                    else:
                                        # Review Packetのpublication_candidate.pathを正として記事パスを復元する。
                                        review_packet = json.loads((run_output_dir / "review_packet.json").read_text(encoding="utf-8"))
                                        candidate = review_packet.get("publication_candidate", {})
                                        article_path = Path(candidate.get("path", ""))
                                        publication_input = PublicationDecisionInput(
                                            review_packet_path=run_output_dir / "review_packet.json",
                                            article_path=article_path,
                                            pr_snapshot_path=orchestration_input.publication_pr_snapshot_path,
                                            human_decision_path=orchestration_input.publication_human_decision_path,
                                            expected_repository=orchestration_input.publication_repository,
                                            expected_pr_number=orchestration_input.publication_pr_number,
                                            expected_base=orchestration_input.publication_base,
                                            authorized_actors=orchestration_input.publication_authorized_actors,
                                            created_at=orchestration_input.created_at,
                                        )
                                        publication_result = decide_publication(publication_input, output_dir)
                                        completed_operations.append("O-11")
                                        state_after = publication_result.state_after
                                        result = publication_result.result
                                        if publication_result.state_after == "APPROVED" and publication_result.result == "ADVANCE":
                                            stop_reason = None
                                            resume_position = None
                                        elif publication_result.state_after == "REVISION" and publication_result.result == "ADVANCE":
                                            if orchestration_input.feedback_proposal_path is None:
                                                stop_reason = "FEEDBACK_PROPOSAL_MISSING"
                                                resume_position = "O-12"
                                                state_after = publication_result.state_after
                                                result = "HOLD"
                                            else:
                                                feedback_draft_path, feedback_manifest_path = _feedback_artifact_paths(run_output_dir)
                                                feedback_input = FeedbackInput(
                                                    decision_path=run_output_dir / "publication_decision.json",
                                                    draft_path=feedback_draft_path,
                                                    manifest_path=feedback_manifest_path,
                                                    proposal_path=orchestration_input.feedback_proposal_path,
                                                    created_at=orchestration_input.created_at,
                                                )
                                                feedback_result = apply_feedback(feedback_input, output_dir)
                                                completed_operations.append("O-12")
                                                state_after = (
                                                    feedback_result.state_after
                                                    if feedback_result.state_after == "REVISED"
                                                    else "REVISION"
                                                )
                                                result = feedback_result.result
                                                if feedback_result.state_after == "REVISED" and feedback_result.result == "ADVANCE":
                                                    revalidation_input = ValidationInput(
                                                        draft_path=run_output_dir / "revised_draft.rst",
                                                        manifest_path=run_output_dir / "revision_manifest.json",
                                                        plan_path=run_output_dir / "article_plan.json",
                                                        packet_path=run_output_dir / "evidence_packet.json",
                                                        judgment_path=orchestration_input.validation_judgment_path,
                                                        created_at=orchestration_input.created_at,
                                                    )
                                                    revalidation_result = validate_draft(revalidation_input, output_dir)
                                                    completed_operations.append("O-09")
                                                    state_after = revalidation_result.state_after
                                                    result = revalidation_result.result
                                                    if revalidation_result.state_after == "VALIDATED" and revalidation_result.result == "ADVANCE":
                                                        stop_reason = None
                                                        resume_position = None
                                                    else:
                                                        stop_reason = "VALIDATION_HOLD"
                                                        resume_position = "O-09"
                                                else:
                                                    stop_reason = "APPLY_FEEDBACK_HOLD"
                                                    resume_position = "O-12"
                                        else:
                                            stop_reason = "PUBLICATION_DECISION_HOLD"
                                            resume_position = "O-11"

    if stop_reason is None and state_after == "APPROVED" and result == "ADVANCE":
        publication_decision = json.loads((run_output_dir / "publication_decision.json").read_text(encoding="utf-8"))
        publication_reasons = publication_decision.get("reason_codes", [])
        reason_codes = publication_reasons if isinstance(publication_reasons, list) and publication_reasons else ["PUBLICATION_APPROVED"]
        outcome = Outcome(
            run_id=orchestration_input.run_id,
            input_refs=[orchestration_input.source_ref],
            state_before=str(publication_decision.get("state_before", "REVIEW_READY")),
            state_after=state_after,
            result=result,
            reason_codes=[str(code) for code in reason_codes],
            summary_ja="公開判断が承認され、Outcomeを記録しました。",
            uncertainties=[],
            created_at=orchestration_input.created_at,
            producer="program",
            artifact_refs=[
                str(run_output_dir / "publication_decision.json"),
                str(run_output_dir / "review_packet.json"),
            ],
            verification_refs=[str(run_output_dir / "orchestration-summary.json")],
            next_action="処理完了",
            human_action="none",
            source_operation="O-11",
        )
        record_outcome(outcome, output_dir)
        completed_operations.append("O-13")

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
    parser.add_argument("--judgment-path", type=Path)
    parser.add_argument("--plan-draft-path", type=Path)
    parser.add_argument("--proposal-path", type=Path)
    parser.add_argument("--validation-judgment-path", type=Path)
    parser.add_argument("--review-proposal-path", type=Path)
    parser.add_argument("--review-as-of-date", type=date.fromisoformat)
    parser.add_argument("--review-posts-dir", type=Path)
    parser.add_argument("--publication-pr-snapshot-path", type=Path)
    parser.add_argument("--publication-human-decision-path", type=Path)
    parser.add_argument("--publication-repository")
    parser.add_argument("--publication-pr-number", type=int)
    parser.add_argument("--publication-base", default="main")
    parser.add_argument("--publication-authorized-actor", action="append", default=[])
    parser.add_argument("--feedback-proposal-path", type=Path)
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
        judgment_path=args.judgment_path,
        plan_draft_path=args.plan_draft_path,
        proposal_path=args.proposal_path,
        validation_judgment_path=args.validation_judgment_path,
        review_proposal_path=args.review_proposal_path,
        review_as_of_date=args.review_as_of_date,
        review_posts_dir=args.review_posts_dir,
        publication_pr_snapshot_path=args.publication_pr_snapshot_path,
        publication_human_decision_path=args.publication_human_decision_path,
        publication_repository=args.publication_repository,
        publication_pr_number=args.publication_pr_number,
        publication_base=args.publication_base,
        publication_authorized_actors=tuple(args.publication_authorized_actor),
        feedback_proposal_path=args.feedback_proposal_path,
    )
    result = orchestrate_run(orchestration_input, args.output_dir)
    print(f"{result.summary_path} ({result.state_after}/{result.result})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
