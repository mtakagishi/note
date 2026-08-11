"""O-13 Record Outcomeの記録処理とCLI。"""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Sequence

from note.knowledge_harness.storage import (
    json_text,
    read_created_at,
    validate_run_id,
    write_if_changed,
)

RESULTS = (
    "ADVANCE",
    "NO_CANDIDATE",
    "REJECTED",
    "HOLD",
    "RETRYABLE_ERROR",
)
PRODUCERS = ("program", "skill_agent", "ai_judge", "human")
HUMAN_ACTIONS = ("none", "publication", "policy", "privacy", "exception")
STATE_PATTERN = re.compile(r"^[A-Z][A-Z0-9_]{0,63}$")


@dataclass(frozen=True)
class Outcome:
    """共通Operation契約とO-13固有情報。"""

    run_id: str
    input_refs: list[str]
    state_before: str
    state_after: str
    result: str
    reason_codes: list[str]
    summary_ja: str
    uncertainties: list[str]
    created_at: str
    producer: str
    artifact_refs: list[str] = field(default_factory=list)
    verification_refs: list[str] = field(default_factory=list)
    next_action: str = "なし"
    human_action: str = "none"
    source_operation: str = ""
    operation_metrics: dict[str, int | float] = field(default_factory=dict)
    schema_version: int = 1


@dataclass(frozen=True)
class RecordResult:
    """記録先と更新有無。"""

    outcome_path: Path
    handoff_path: Path
    metrics_path: Path
    changed: bool


def _validate(outcome: Outcome) -> None:
    validate_run_id(outcome.run_id)
    if not STATE_PATTERN.fullmatch(outcome.state_before):
        raise ValueError("state_beforeは大文字英数字とアンダースコアで指定してください")
    if not STATE_PATTERN.fullmatch(outcome.state_after):
        raise ValueError("state_afterは大文字英数字とアンダースコアで指定してください")
    if outcome.result not in RESULTS:
        raise ValueError(f"resultは{', '.join(RESULTS)}のいずれかにしてください")
    if outcome.producer not in PRODUCERS:
        raise ValueError(f"producerは{', '.join(PRODUCERS)}のいずれかにしてください")
    if outcome.human_action not in HUMAN_ACTIONS:
        raise ValueError(f"human_actionは{', '.join(HUMAN_ACTIONS)}のいずれかにしてください")
    if not outcome.reason_codes:
        raise ValueError("reason_codesを一件以上指定してください")
    if not outcome.summary_ja.strip():
        raise ValueError("summary_jaを指定してください")
    if not outcome.created_at.strip():
        raise ValueError("created_atを指定してください")
    if outcome.operation_metrics and not outcome.source_operation.strip():
        raise ValueError("operation_metricsを記録する場合はsource_operationを指定してください")


def _list_items(values: Sequence[str]) -> str:
    if not values:
        return "- なし"
    return "\n".join(f"- {value}" for value in values)


def _handoff_text(outcome: Outcome) -> str:
    return f"""# HANDOFF {outcome.run_id}

## 完了

- 状態: `{outcome.state_before}` → `{outcome.state_after}`
- 結果: `{outcome.result}`
- 記録者: `{outcome.producer}`
- 記録時刻: `{outcome.created_at}`

## 要約

{outcome.summary_ja}

## 理由コード

{_list_items(outcome.reason_codes)}

## 入力参照

{_list_items(outcome.input_refs)}

## 成果物

{_list_items(outcome.artifact_refs)}

## 検証

{_list_items(outcome.verification_refs)}

## 不確実性

{_list_items(outcome.uncertainties)}

## 人間判断

- 種類: `{outcome.human_action}`

## 次の一手

- {outcome.next_action}
"""


def _read_outcomes(output_dir: Path) -> list[dict[str, Any]]:
    outcomes: list[dict[str, Any]] = []
    for path in sorted(output_dir.glob("*/outcome.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if isinstance(data, dict) and data.get("run_id") == path.parent.name:
            outcomes.append(data)
    return outcomes


def _metrics(outcomes: Sequence[dict[str, Any]]) -> dict[str, Any]:
    results = Counter(str(item.get("result", "UNKNOWN")) for item in outcomes)
    reason_codes = Counter(
        str(code) for item in outcomes for code in item.get("reason_codes", [])
    )
    human_actions = Counter(
        str(item.get("human_action", "none")) for item in outcomes
    )
    operation_metrics: dict[str, dict[str, Any]] = {}
    for item in outcomes:
        operation = item.get("source_operation")
        values = item.get("operation_metrics")
        if not isinstance(operation, str) or not operation or not isinstance(values, dict):
            continue
        aggregate = operation_metrics.setdefault(operation, {"runs": 0, "totals": {}})
        aggregate["runs"] += 1
        for name, value in values.items():
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                aggregate["totals"][str(name)] = aggregate["totals"].get(str(name), 0) + value
    return {
        "schema_version": 1,
        "total_runs": len(outcomes),
        "results": dict(sorted(results.items())),
        "reason_codes": dict(sorted(reason_codes.items())),
        "human_actions": dict(sorted(human_actions.items())),
        "operation_metrics": operation_metrics,
    }


def _read_operation_metrics(path: Path | None) -> dict[str, int | float]:
    if path is None:
        return {}
    data = _read_json_object(path, "Operation Metrics")
    metrics = data.get("metrics")
    if not isinstance(metrics, dict):
        raise ValueError("Operation Metricsファイルにmetricsがありません")
    return {
        str(name): value
        for name, value in metrics.items()
        if isinstance(value, (int, float)) and not isinstance(value, bool)
    }


def _read_json_object(path: Path, label: str) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"{label}をJSONとして読めません: {path}") from error
    if not isinstance(data, dict):
        raise ValueError(f"{label}はJSONオブジェクトである必要があります")
    return data


def record_outcome(outcome: Outcome, output_dir: Path) -> RecordResult:
    """Outcomeを冪等に保存し、全runのMetricsを再集計する。"""

    _validate(outcome)
    run_dir = output_dir / outcome.run_id
    outcome_path = run_dir / "outcome.json"
    handoff_path = run_dir / "HANDOFF.md"
    metrics_path = output_dir / "metrics.json"

    outcome_changed = write_if_changed(outcome_path, json_text(asdict(outcome)))
    handoff_changed = write_if_changed(handoff_path, _handoff_text(outcome))
    metrics_changed = write_if_changed(
        metrics_path, json_text(_metrics(_read_outcomes(output_dir)))
    )
    return RecordResult(
        outcome_path=outcome_path,
        handoff_path=handoff_path,
        metrics_path=metrics_path,
        changed=outcome_changed or handoff_changed or metrics_changed,
    )


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="O-13 Record Outcomeを記録します")
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--state-before", required=True)
    parser.add_argument("--state-after", required=True)
    parser.add_argument("--result", required=True, choices=RESULTS)
    parser.add_argument("--reason-code", required=True, action="append", dest="reason_codes")
    parser.add_argument("--summary-ja", required=True)
    parser.add_argument("--producer", required=True, choices=PRODUCERS)
    parser.add_argument("--input-ref", action="append", default=[], dest="input_refs")
    parser.add_argument("--uncertainty", action="append", default=[], dest="uncertainties")
    parser.add_argument("--artifact-ref", action="append", default=[], dest="artifact_refs")
    parser.add_argument("--verification-ref", action="append", default=[], dest="verification_refs")
    parser.add_argument("--next-action", default="なし")
    parser.add_argument("--human-action", default="none", choices=HUMAN_ACTIONS)
    parser.add_argument("--source-operation", default="")
    parser.add_argument("--operation-metrics-file", type=Path)
    parser.add_argument("--created-at")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("_notes/knowledge_harness/outcomes"),
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    created_at = args.created_at or read_created_at(
        args.output_dir / args.run_id / "outcome.json"
    )
    if created_at is None:
        created_at = datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")

    try:
        operation_metrics = _read_operation_metrics(args.operation_metrics_file)
    except ValueError as error:
        _parser().error(str(error))
    outcome = Outcome(
        run_id=args.run_id,
        input_refs=args.input_refs,
        state_before=args.state_before,
        state_after=args.state_after,
        result=args.result,
        reason_codes=args.reason_codes,
        summary_ja=args.summary_ja,
        uncertainties=args.uncertainties,
        created_at=created_at,
        producer=args.producer,
        artifact_refs=args.artifact_refs,
        verification_refs=args.verification_refs,
        next_action=args.next_action,
        human_action=args.human_action,
        source_operation=args.source_operation,
        operation_metrics=operation_metrics,
    )
    try:
        result = record_outcome(outcome, args.output_dir)
    except ValueError as error:
        _parser().error(str(error))

    status = "更新しました" if result.changed else "変更はありません"
    print(f"{status}: {result.outcome_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
