"""O-01 Capture Requestの受付処理とCLI。"""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Sequence

from note.knowledge_harness.storage import (
    json_text,
    read_created_at,
    validate_run_id,
    write_if_changed,
)

SOURCE_KINDS = ("public_issue", "approved_input", "unconfirmed_input")


@dataclass(frozen=True)
class CaptureInput:
    """O-01へ渡す最小入力。"""

    run_id: str
    question_ja: str
    source_ref: str
    source_kind: str
    created_at: str


@dataclass(frozen=True)
class CaptureResult:
    """受付結果と保存先。"""

    request_path: Path
    changed: bool
    state_after: str
    result: str


def _validate(capture_input: CaptureInput) -> None:
    validate_run_id(capture_input.run_id)
    if not capture_input.question_ja.strip():
        raise ValueError("question_jaを一文以上指定してください")
    if not capture_input.source_ref.strip():
        raise ValueError("source_refを指定してください")
    if capture_input.source_kind not in SOURCE_KINDS:
        raise ValueError(f"source_kindは{', '.join(SOURCE_KINDS)}のいずれかにしてください")
    if not capture_input.created_at.strip():
        raise ValueError("created_atを指定してください")


def _record(capture_input: CaptureInput) -> dict[str, Any]:
    publication_confirmed = capture_input.source_kind != "unconfirmed_input"
    if publication_confirmed:
        state_after = "CAPTURED"
        result = "ADVANCE"
        reason_codes = ["REQUEST_CAPTURED"]
        summary_ja = "公開可能な入力を記事候補の依頼として受け付けました。"
        uncertainties: list[str] = []
        next_action = "O-02 Authorize Runへ渡す"
        required_human_action = "none"
    else:
        state_after = "HOLD"
        result = "HOLD"
        reason_codes = ["PUBLICATION_CONFIRMATION_REQUIRED"]
        summary_ja = "入力の公開可能性が未確認のため、後続処理を開始しません。"
        uncertainties = ["入力を公開処理へ使用してよいか確認されていません。"]
        next_action = "公開可能性だけを人間へ確認する"
        required_human_action = "privacy"

    return {
        "schema_version": 1,
        "operation_id": "O-01",
        "run_id": capture_input.run_id,
        "input_refs": [capture_input.source_ref],
        "state_before": "RECEIVED",
        "state_after": state_after,
        "result": result,
        "reason_codes": reason_codes,
        "summary_ja": summary_ja,
        "uncertainties": uncertainties,
        "created_at": capture_input.created_at,
        "producer": "program",
        "next_action": next_action,
        "required_human_action": required_human_action,
        "request": asdict(capture_input),
    }


def capture_request(capture_input: CaptureInput, output_dir: Path) -> CaptureResult:
    """入力を検証し、同じrun_idのRequestを冪等に保存する。"""

    _validate(capture_input)
    record = _record(capture_input)
    request_path = output_dir / capture_input.run_id / "request.json"
    changed = write_if_changed(request_path, json_text(record))
    return CaptureResult(
        request_path=request_path,
        changed=changed,
        state_after=str(record["state_after"]),
        result=str(record["result"]),
    )


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="O-01 Capture Requestを実行します")
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--question-ja", required=True)
    parser.add_argument("--source-ref", required=True)
    parser.add_argument("--source-kind", required=True, choices=SOURCE_KINDS)
    parser.add_argument("--created-at")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("_notes/knowledge_harness/requests"),
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = _parser()
    args = parser.parse_args(argv)
    request_path = args.output_dir / args.run_id / "request.json"
    created_at = args.created_at or read_created_at(request_path)
    if created_at is None:
        created_at = datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")

    capture_input = CaptureInput(
        run_id=args.run_id,
        question_ja=args.question_ja,
        source_ref=args.source_ref,
        source_kind=args.source_kind,
        created_at=created_at,
    )
    try:
        result = capture_request(capture_input, args.output_dir)
    except ValueError as error:
        parser.error(str(error))

    status = "更新しました" if result.changed else "変更はありません"
    print(f"{status}: {result.request_path} ({result.state_after}/{result.result})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
