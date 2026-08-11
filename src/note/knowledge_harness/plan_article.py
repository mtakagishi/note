"""O-07 Plan Articleの検証・保存処理とCLI。"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Sequence

from note.knowledge_harness.storage import json_text, read_created_at, validate_run_id, write_if_changed

STRUCTURE_PATTERNS = {
    "TUTORIAL",
    "CONCEPT_EXPLANATION",
    "CHANGE_ANALYSIS",
    "TROUBLESHOOTING",
    "DECISION_RECORD",
}
UNCERTAINTY_ACTIONS = {"DISCLOSE", "LIMIT_CLAIM", "EXCLUDE"}


@dataclass(frozen=True)
class PlanInput:
    """O-07へ渡すCandidate Decision、Evidence Packet、計画案。"""

    decision_path: Path
    packet_path: Path
    draft_path: Path
    created_at: str


@dataclass(frozen=True)
class PlanResult:
    """Article Planの保存結果。"""

    plan_path: Path
    changed: bool
    state_after: str
    result: str


def _read_json(path: Path, label: str) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as error:
        raise ValueError(f"{label}が見つかりません: {path}") from error
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"{label}をJSONとして読めません: {path}") from error


def _nonempty(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label}は空でない文字列にしてください")
    return value.strip()


def _string_list(value: Any, label: str, *, allow_empty: bool = False) -> list[str]:
    if not isinstance(value, list) or (not value and not allow_empty):
        raise ValueError(f"{label}は{'' if allow_empty else '一件以上の'}配列にしてください")
    items = [_nonempty(item, f"{label}の要素") for item in value]
    if len(items) != len(set(items)):
        raise ValueError(f"{label}に重複があります")
    return items


def _read_inputs(decision_path: Path, packet_path: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    decision = _read_json(decision_path, "Candidate Decision")
    packet = _read_json(packet_path, "Evidence Packet")
    if not isinstance(decision, dict) or decision.get("operation_id") != "O-06":
        raise ValueError("O-06が生成したCandidate Decisionだけを受け付けます")
    if decision.get("state_after") != "CANDIDATE_ACCEPTED" or decision.get("result") != "ADVANCE":
        raise ValueError("CANDIDATE_ACCEPTED / ADVANCEのCandidate Decisionだけを計画できます")
    if not isinstance(packet, dict) or packet.get("operation_id") != "O-05":
        raise ValueError("O-05が生成したEvidence Packetだけを受け付けます")
    if packet.get("state_after") != "PACKET_READY" or packet.get("result") != "ADVANCE":
        raise ValueError("PACKET_READY / ADVANCEのEvidence Packetだけを計画できます")
    run_id = decision.get("run_id")
    if not isinstance(run_id, str) or packet.get("run_id") != run_id:
        raise ValueError("Candidate DecisionとEvidence Packetのrun_idが一致しません")
    validate_run_id(run_id)
    if not isinstance(packet.get("topics"), list) or not isinstance(packet.get("past_articles"), dict):
        raise ValueError("Evidence Packetの必須項目が不正です")
    return decision, packet


def _item_refs(values: Any, prefix: str, label: str) -> set[str]:
    if not isinstance(values, list):
        raise ValueError(f"Evidence Packetの{label}が不正です")
    refs: set[str] = set()
    for item in values:
        if not isinstance(item, dict) or not isinstance(item.get("item_id"), str):
            raise ValueError(f"Evidence Packetの{label}が不正です")
        refs.add(f"{prefix}/{item['item_id']}")
    return refs


def _packet_refs(packet: dict[str, Any]) -> set[str]:
    refs = {"past_articles"}
    for field in ("summary_ja", "screened_request"):
        if field in packet and packet[field] is not None:
            refs.add(field)
    for topic in packet["topics"]:
        if not isinstance(topic, dict) or not isinstance(topic.get("topic_id"), str):
            raise ValueError("Evidence Packetのtopicsが不正です")
        prefix = f"topics/{topic['topic_id']}"
        refs.add(prefix)
        refs.update(_item_refs(topic.get("items"), f"{prefix}/items", "topic.items"))
    for group in ("known_items", "difference_candidates", "recheck_items"):
        refs.update(
            _item_refs(
                packet["past_articles"].get(group, []),
                f"past_articles/{group}",
                f"past_articles.{group}",
            )
        )
    for field in ("uncertainties", "retrieval_failures"):
        values = packet.get(field, [])
        if not isinstance(values, list):
            raise ValueError(f"Evidence Packetの{field}が不正です")
        refs.update(f"{field}/{index}" for index in range(len(values)))
    return refs


def _references(value: Any, label: str, valid_refs: set[str]) -> list[str]:
    refs = _string_list(value, label)
    if any(ref not in valid_refs for ref in refs):
        raise ValueError(f"{label}が存在しないPacket項目を参照しています")
    return refs


def _sections(value: Any, valid_refs: set[str]) -> list[dict[str, Any]]:
    if not isinstance(value, list) or not value:
        raise ValueError("sectionsを一件以上指定してください")
    sections: list[dict[str, Any]] = []
    seen: set[str] = set()
    for index, section in enumerate(value, start=1):
        label = f"sections[{index}]"
        if not isinstance(section, dict):
            raise ValueError(f"{label}はJSONオブジェクトで指定してください")
        section_id = _nonempty(section.get("section_id"), f"{label}.section_id")
        if section_id in seen:
            raise ValueError(f"section_idが重複しています: {section_id}")
        seen.add(section_id)
        sections.append(
            {
                "section_id": section_id,
                "heading_ja": _nonempty(section.get("heading_ja"), f"{label}.heading_ja"),
                "purpose_ja": _nonempty(section.get("purpose_ja"), f"{label}.purpose_ja"),
                "reader_takeaway_ja": _nonempty(
                    section.get("reader_takeaway_ja"), f"{label}.reader_takeaway_ja"
                ),
                "packet_refs": _references(
                    section.get("packet_refs"), f"{label}.packet_refs", valid_refs
                ),
            }
        )
    return sections


def _excluded_topics(value: Any) -> list[dict[str, str]]:
    if not isinstance(value, list):
        raise ValueError("excluded_topicsは配列にしてください")
    return [
        {
            "topic_ja": _nonempty(item.get("topic_ja") if isinstance(item, dict) else None, f"excluded_topics[{index}].topic_ja"),
            "reason_ja": _nonempty(item.get("reason_ja") if isinstance(item, dict) else None, f"excluded_topics[{index}].reason_ja"),
        }
        for index, item in enumerate(value, start=1)
    ]


def _uncertainty_treatments(value: Any, packet: dict[str, Any]) -> list[dict[str, str]]:
    if not isinstance(value, list):
        raise ValueError("uncertainty_treatmentsは配列にしてください")
    expected = {f"uncertainties/{index}" for index in range(len(packet.get("uncertainties", [])))}
    treatments: list[dict[str, str]] = []
    seen: set[str] = set()
    for index, item in enumerate(value, start=1):
        label = f"uncertainty_treatments[{index}]"
        if not isinstance(item, dict):
            raise ValueError(f"{label}はJSONオブジェクトで指定してください")
        packet_ref = _nonempty(item.get("packet_ref"), f"{label}.packet_ref")
        if packet_ref not in expected or packet_ref in seen:
            raise ValueError("不確実性の参照は実在し、重複しないようにしてください")
        seen.add(packet_ref)
        action = item.get("action")
        if action not in UNCERTAINTY_ACTIONS:
            raise ValueError(f"{label}.actionが不正です")
        treatments.append(
            {
                "packet_ref": packet_ref,
                "action": action,
                "reason_ja": _nonempty(item.get("reason_ja"), f"{label}.reason_ja"),
            }
        )
    if seen != expected:
        raise ValueError("Evidence Packetの全不確実性に扱いを指定してください")
    return treatments


def _plan(draft: dict[str, Any], packet: dict[str, Any], valid_refs: set[str]) -> dict[str, Any]:
    central_message = _nonempty(draft.get("central_message_ja"), "central_message_ja")
    if "\n" in central_message or "\r" in central_message:
        raise ValueError("central_message_jaは一文として一行で指定してください")
    structure_pattern = draft.get("structure_pattern")
    if structure_pattern not in STRUCTURE_PATTERNS:
        raise ValueError("structure_patternが不正です")
    return {
        "mode": "PLAN",
        "plan_version": _nonempty(draft.get("plan_version"), "plan_version"),
        "planner_id": _nonempty(draft.get("planner_id"), "planner_id"),
        "working_title_ja": _nonempty(draft.get("working_title_ja"), "working_title_ja"),
        "central_message_ja": central_message,
        "target_readers": _string_list(draft.get("target_readers"), "target_readers"),
        "search_intents": _string_list(draft.get("search_intents"), "search_intents"),
        "structure_pattern": structure_pattern,
        "sections": _sections(draft.get("sections"), valid_refs),
        "excluded_topics": _excluded_topics(draft.get("excluded_topics")),
        "uncertainty_treatments": _uncertainty_treatments(
            draft.get("uncertainty_treatments"), packet
        ),
        "author_context_ref": str(draft.get("author_context_ref", "")).strip() or None,
    }


def _questions(draft: dict[str, Any], valid_refs: set[str]) -> dict[str, Any]:
    values = draft.get("questions")
    if not isinstance(values, list) or not 1 <= len(values) <= 3:
        raise ValueError("questionsは一件以上3件以下にしてください")
    questions: list[dict[str, Any]] = []
    seen: set[str] = set()
    for index, item in enumerate(values, start=1):
        label = f"questions[{index}]"
        if not isinstance(item, dict):
            raise ValueError(f"{label}はJSONオブジェクトで指定してください")
        question_id = _nonempty(item.get("question_id"), f"{label}.question_id")
        if question_id in seen:
            raise ValueError(f"question_idが重複しています: {question_id}")
        seen.add(question_id)
        if item.get("question_kind") != "AUTHOR_MOTIVATION":
            raise ValueError("質問はAUTHOR_MOTIVATIONだけに限定してください")
        questions.append(
            {
                "question_id": question_id,
                "question_kind": "AUTHOR_MOTIVATION",
                "question_ja": _nonempty(item.get("question_ja"), f"{label}.question_ja"),
                "purpose_ja": _nonempty(item.get("purpose_ja"), f"{label}.purpose_ja"),
                "packet_refs": _references(
                    item.get("packet_refs"), f"{label}.packet_refs", valid_refs
                ),
            }
        )
    return {
        "mode": "AUTHOR_QUESTION",
        "plan_version": _nonempty(draft.get("plan_version"), "plan_version"),
        "planner_id": _nonempty(draft.get("planner_id"), "planner_id"),
        "question_reason_ja": _nonempty(draft.get("question_reason_ja"), "question_reason_ja"),
        "questions": questions,
    }


def plan_article(plan_input: PlanInput, output_dir: Path) -> PlanResult:
    """計画案を検証し、Article Planまたは一度限りの質問を保存する。"""

    if not plan_input.created_at.strip():
        raise ValueError("created_atを指定してください")
    _, packet = _read_inputs(plan_input.decision_path, plan_input.packet_path)
    draft = _read_json(plan_input.draft_path, "Article Plan案")
    if not isinstance(draft, dict):
        raise ValueError("Article Plan案はJSONオブジェクトである必要があります")
    valid_refs = _packet_refs(packet)
    mode = draft.get("mode")
    if mode == "PLAN":
        content = _plan(draft, packet, valid_refs)
        state_after, result = "PLAN_READY", "ADVANCE"
        reason_codes = ["ARTICLE_PLAN_BUILT"]
    elif mode == "AUTHOR_QUESTION":
        content = _questions(draft, valid_refs)
        state_after, result = "HOLD", "HOLD"
        reason_codes = ["AUTHOR_MOTIVATION_REQUIRED"]
    else:
        raise ValueError("modeはPLANまたはAUTHOR_QUESTIONにしてください")
    run_id = str(packet["run_id"])
    plan_path = output_dir / run_id / "article_plan.json"
    existing = _read_json(plan_path, "既存Article Plan") if plan_path.exists() else None
    if isinstance(existing, dict) and existing.get("state_after") == "HOLD":
        if mode == "AUTHOR_QUESTION" and existing.get("questions") != content["questions"]:
            raise ValueError("人間への質問は一回だけです。別の質問へ差し替えできません")
        if mode == "PLAN" and not content["author_context_ref"]:
            raise ValueError("質問後の計画には公開可能なauthor_context_refが必要です")
    record = {
        "schema_version": 1,
        "operation_id": "O-07",
        "run_id": run_id,
        "input_refs": [
            str(plan_input.decision_path),
            str(plan_input.packet_path),
            str(plan_input.draft_path),
        ],
        "state_before": "CANDIDATE_ACCEPTED",
        "state_after": state_after,
        "result": result,
        "reason_codes": reason_codes,
        "created_at": plan_input.created_at,
        "producer": "skill_agent_and_program",
        **content,
        "next_action": "O-08 Draft Articleへ渡す" if result == "ADVANCE" else "著者の回答を待つ",
        "required_human_action": "none" if result == "ADVANCE" else "exception",
    }
    changed = write_if_changed(plan_path, json_text(record))
    return PlanResult(plan_path, changed, state_after, result)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="O-07 Plan Articleを実行します")
    parser.add_argument("--decision-file", required=True, type=Path)
    parser.add_argument("--packet-file", required=True, type=Path)
    parser.add_argument("--draft-file", required=True, type=Path)
    parser.add_argument("--created-at")
    parser.add_argument("--output-dir", type=Path, default=Path("_notes/knowledge_harness/plans"))
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = _parser()
    args = parser.parse_args(argv)
    try:
        decision, _ = _read_inputs(args.decision_file, args.packet_file)
        plan_path = args.output_dir / str(decision["run_id"]) / "article_plan.json"
        created_at = args.created_at or read_created_at(plan_path)
        if created_at is None:
            created_at = datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")
        result = plan_article(
            PlanInput(args.decision_file, args.packet_file, args.draft_file, created_at),
            args.output_dir,
        )
    except ValueError as error:
        parser.error(str(error))
    status = "更新しました" if result.changed else "変更はありません"
    print(f"{status}: {result.plan_path} ({result.state_after}/{result.result})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
