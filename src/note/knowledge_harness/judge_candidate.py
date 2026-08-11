"""O-06 Judge Candidateの検証・保存処理とCLI。"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Sequence

from note.knowledge_harness.storage import json_text, read_created_at, validate_run_id, write_if_changed

REQUIRED_AXES = (
    "evidence_sufficiency",
    "novelty",
    "reader_value",
    "author_specific_question",
)
ALL_AXES = (*REQUIRED_AXES, "uncertainty_impact")
VERDICTS = {"PASS", "FAIL", "UNCERTAIN"}
IMPACT_LEVELS = {"LOW", "MEDIUM", "HIGH"}
PASS_CONFIDENCE_THRESHOLD = 0.70


@dataclass(frozen=True)
class JudgeInput:
    """O-06へ渡すEvidence PacketとAI Judgeの判定案。"""

    packet_path: Path
    judgment_path: Path
    created_at: str


@dataclass(frozen=True)
class JudgeResult:
    """Candidate Decisionの保存結果。"""

    decision_path: Path
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


def _read_packet(path: Path) -> dict[str, Any]:
    packet = _read_json(path, "Evidence Packet")
    if not isinstance(packet, dict):
        raise ValueError("Evidence PacketはJSONオブジェクトである必要があります")
    if packet.get("operation_id") != "O-05":
        raise ValueError("O-05が生成したEvidence Packetだけを受け付けます")
    if packet.get("state_after") != "PACKET_READY" or packet.get("result") != "ADVANCE":
        raise ValueError("PACKET_READY / ADVANCEのEvidence Packetだけを判定できます")
    run_id = packet.get("run_id")
    if not isinstance(run_id, str):
        raise ValueError("Evidence Packetのrun_idが不正です")
    validate_run_id(run_id)
    if not isinstance(packet.get("topics"), list) or not isinstance(packet.get("past_articles"), dict):
        raise ValueError("Evidence Packetの必須項目が不正です")
    return packet


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
    if "summary_ja" in packet and packet["summary_ja"] is not None:
        refs.add("summary_ja")
    if "screened_request" in packet and packet["screened_request"] is not None:
        refs.add("screened_request")
    for topic in packet["topics"]:
        if not isinstance(topic, dict) or not isinstance(topic.get("topic_id"), str):
            raise ValueError("Evidence Packetのtopicsが不正です")
        topic_ref = f"topics/{topic['topic_id']}"
        refs.add(topic_ref)
        refs.update(_item_refs(topic.get("items"), f"{topic_ref}/items", "topic.items"))
    past_articles = packet["past_articles"]
    for group in ("known_items", "difference_candidates", "recheck_items"):
        refs.update(
            _item_refs(
                past_articles.get(group, []),
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


def _confidence(value: Any, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not 0 <= value <= 1:
        raise ValueError(f"{label}は0から1の数値にしてください")
    return float(value)


def _evaluation(value: Any, axis: str, valid_refs: set[str]) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"evaluations.{axis}はJSONオブジェクトで指定してください")
    submitted_verdict = value.get("verdict")
    if submitted_verdict not in VERDICTS:
        raise ValueError(f"evaluations.{axis}.verdictが不正です")
    confidence = _confidence(value.get("confidence"), f"evaluations.{axis}.confidence")
    reason_ja = _nonempty(value.get("reason_ja"), f"evaluations.{axis}.reason_ja")
    packet_refs = value.get("packet_refs")
    if not isinstance(packet_refs, list) or not packet_refs:
        raise ValueError(f"evaluations.{axis}.packet_refsを一件以上指定してください")
    if any(not isinstance(ref, str) or ref not in valid_refs for ref in packet_refs):
        raise ValueError(f"evaluations.{axis}が存在しないPacket項目を参照しています")
    verdict = submitted_verdict
    normalization_reasons: list[str] = []
    if verdict == "PASS" and confidence < PASS_CONFIDENCE_THRESHOLD:
        verdict = "UNCERTAIN"
        normalization_reasons.append("PASS_CONFIDENCE_BELOW_THRESHOLD")
    return {
        "verdict": verdict,
        "submitted_verdict": submitted_verdict,
        "confidence": confidence,
        "reason_ja": reason_ja,
        "packet_refs": list(dict.fromkeys(packet_refs)),
        "normalization_reasons": normalization_reasons,
    }


def _validate_judgment(judgment: Any, packet: dict[str, Any]) -> tuple[dict[str, Any], str]:
    if not isinstance(judgment, dict):
        raise ValueError("判定案はJSONオブジェクトである必要があります")
    rubric_version = _nonempty(judgment.get("rubric_version"), "rubric_version")
    judge_id = _nonempty(judgment.get("judge_id"), "judge_id")
    raw_evaluations = judgment.get("evaluations")
    if not isinstance(raw_evaluations, dict) or set(raw_evaluations) != set(ALL_AXES):
        raise ValueError("evaluationsには5評価軸を過不足なく指定してください")
    valid_refs = _packet_refs(packet)
    evaluations = {
        axis: _evaluation(raw_evaluations[axis], axis, valid_refs) for axis in ALL_AXES
    }
    impact = raw_evaluations["uncertainty_impact"].get("impact")
    if impact not in IMPACT_LEVELS:
        raise ValueError("evaluations.uncertainty_impact.impactが不正です")
    evaluations["uncertainty_impact"]["impact"] = impact
    past_status = packet["past_articles"].get("status")
    if past_status != "COMPARED" and evaluations["novelty"]["verdict"] == "PASS":
        evaluations["novelty"]["verdict"] = "UNCERTAIN"
        evaluations["novelty"]["normalization_reasons"].append(
            "NOVELTY_UNCONFIRMED_WITHOUT_PAST_ARTICLE"
        )
    return {"rubric_version": rubric_version, "judge_id": judge_id, "evaluations": evaluations}, impact


def _decision(evaluations: dict[str, dict[str, Any]], impact: str) -> tuple[str, str, list[str]]:
    failed = [axis for axis in REQUIRED_AXES if evaluations[axis]["verdict"] == "FAIL"]
    if failed:
        return "NO_CANDIDATE", "NO_CANDIDATE", ["REQUIRED_AXIS_FAILED", *failed]
    uncertain = [axis for axis in REQUIRED_AXES if evaluations[axis]["verdict"] == "UNCERTAIN"]
    if uncertain or impact == "HIGH":
        reasons = ["JUDGMENT_UNCERTAIN"]
        reasons.extend(uncertain)
        if impact == "HIGH":
            reasons.append("HIGH_IMPACT_UNCERTAINTY")
        return "HOLD", "HOLD", reasons
    return "CANDIDATE_ACCEPTED", "ADVANCE", ["ALL_REQUIRED_AXES_PASSED"]


def judge_candidate(judge_input: JudgeInput, output_dir: Path) -> JudgeResult:
    """AI Judgeの判定案を検証し、Candidate Decisionを保存する。"""

    if not judge_input.created_at.strip():
        raise ValueError("created_atを指定してください")
    packet = _read_packet(judge_input.packet_path)
    judgment = _read_json(judge_input.judgment_path, "判定案")
    validated, impact = _validate_judgment(judgment, packet)
    state_after, result, reason_codes = _decision(validated["evaluations"], impact)
    run_id = str(packet["run_id"])
    record = {
        "schema_version": 1,
        "operation_id": "O-06",
        "run_id": run_id,
        "input_refs": [str(judge_input.packet_path), str(judge_input.judgment_path)],
        "state_before": "PACKET_READY",
        "state_after": state_after,
        "result": result,
        "reason_codes": reason_codes,
        "created_at": judge_input.created_at,
        "producer": "ai_judge_and_program",
        "rubric_version": validated["rubric_version"],
        "judge_id": validated["judge_id"],
        "evaluations": validated["evaluations"],
        "next_action": "O-07 Plan Articleへ渡す" if result == "ADVANCE" else "なし",
        "required_human_action": "none",
    }
    decision_path = output_dir / run_id / "candidate_decision.json"
    changed = write_if_changed(decision_path, json_text(record))
    return JudgeResult(decision_path, changed, state_after, result)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="O-06 Judge Candidateを実行します")
    parser.add_argument("--packet-file", required=True, type=Path)
    parser.add_argument("--judgment-file", required=True, type=Path)
    parser.add_argument("--created-at")
    parser.add_argument("--output-dir", type=Path, default=Path("_notes/knowledge_harness/decisions"))
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = _parser()
    args = parser.parse_args(argv)
    try:
        packet = _read_packet(args.packet_file)
        decision_path = args.output_dir / str(packet["run_id"]) / "candidate_decision.json"
        created_at = args.created_at or read_created_at(decision_path)
        if created_at is None:
            created_at = datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")
        result = judge_candidate(
            JudgeInput(args.packet_file, args.judgment_file, created_at), args.output_dir
        )
    except ValueError as error:
        parser.error(str(error))
    status = "更新しました" if result.changed else "変更はありません"
    print(f"{status}: {result.decision_path} ({result.state_after}/{result.result})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
