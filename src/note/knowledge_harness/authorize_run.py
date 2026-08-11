"""O-02 Authorize Runの実行許可判定とCLI。"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Sequence

from note.knowledge_harness.storage import (
    json_text,
    read_created_at,
    validate_run_id,
    write_if_changed,
)

DEFAULT_RUN_LABEL = "knowledge-harness:run"


@dataclass(frozen=True)
class AuthorizationInput:
    """O-02へ渡すRequestとラベル情報。"""

    request_path: Path
    labels: list[str]
    required_label: str
    created_at: str


@dataclass(frozen=True)
class AuthorizationResult:
    """実行許可の判定結果と保存先。"""

    authorization_path: Path
    changed: bool
    state_after: str
    result: str


def _read_request(path: Path) -> dict[str, Any]:
    try:
        request = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as error:
        raise ValueError(f"Requestが見つかりません: {path}") from error
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"RequestをJSONとして読めません: {path}") from error

    if not isinstance(request, dict):
        raise ValueError("RequestはJSONオブジェクトである必要があります")
    run_id = request.get("run_id")
    if not isinstance(run_id, str):
        raise ValueError("Requestにrun_idがありません")
    validate_run_id(run_id)
    if request.get("operation_id") != "O-01":
        raise ValueError("O-01が生成したRequestだけを受け付けます")
    if request.get("state_after") != "CAPTURED" or request.get("result") != "ADVANCE":
        raise ValueError("CAPTURED / ADVANCEのRequestだけを実行許可判定できます")
    return request


def _validate(authorization_input: AuthorizationInput) -> None:
    if not authorization_input.required_label.strip():
        raise ValueError("required_labelを指定してください")
    if not authorization_input.created_at.strip():
        raise ValueError("created_atを指定してください")


def _record(
    authorization_input: AuthorizationInput, request: dict[str, Any]
) -> dict[str, Any]:
    labels = sorted({label.strip() for label in authorization_input.labels if label.strip()})
    authorized = authorization_input.required_label in labels
    if authorized:
        state_after = "AUTHORIZED"
        result = "ADVANCE"
        reason_codes = ["RUN_LABEL_PRESENT"]
        summary_ja = "明示的な実行ラベルを確認し、後続処理を許可しました。"
        next_action = "O-03 Screen Safetyへ渡す"
    else:
        state_after = "CAPTURED"
        result = "HOLD"
        reason_codes = ["RUN_LABEL_MISSING"]
        summary_ja = "明示的な実行ラベルがないため、状態を変えずに待機します。"
        next_action = "実行ラベルを待つ。人間へ質問・催促しない"

    return {
        "schema_version": 1,
        "operation_id": "O-02",
        "run_id": request["run_id"],
        "input_refs": [str(authorization_input.request_path)],
        "state_before": "CAPTURED",
        "state_after": state_after,
        "result": result,
        "reason_codes": reason_codes,
        "summary_ja": summary_ja,
        "uncertainties": [],
        "created_at": authorization_input.created_at,
        "producer": "program",
        "next_action": next_action,
        "required_human_action": "none",
        "required_label": authorization_input.required_label,
        "labels": labels,
        "request": request,
    }


def authorize_run(
    authorization_input: AuthorizationInput, output_dir: Path
) -> AuthorizationResult:
    """明示的なラベルがある場合だけRequestをAUTHORIZEDへ進める。"""

    _validate(authorization_input)
    request = _read_request(authorization_input.request_path)
    record = _record(authorization_input, request)
    authorization_path = output_dir / str(request["run_id"]) / "authorization.json"
    changed = write_if_changed(authorization_path, json_text(record))
    return AuthorizationResult(
        authorization_path=authorization_path,
        changed=changed,
        state_after=str(record["state_after"]),
        result=str(record["result"]),
    )


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="O-02 Authorize Runを実行します")
    parser.add_argument("--request-file", required=True, type=Path)
    parser.add_argument("--label", action="append", default=[], dest="labels")
    parser.add_argument("--required-label", default=DEFAULT_RUN_LABEL)
    parser.add_argument("--created-at")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("_notes/knowledge_harness/authorized"),
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = _parser()
    args = parser.parse_args(argv)
    try:
        request = _read_request(args.request_file)
    except ValueError as error:
        parser.error(str(error))
    authorization_path = args.output_dir / str(request["run_id"]) / "authorization.json"
    created_at = args.created_at or read_created_at(authorization_path)
    if created_at is None:
        created_at = datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")

    authorization_input = AuthorizationInput(
        request_path=args.request_file,
        labels=args.labels,
        required_label=args.required_label,
        created_at=created_at,
    )
    try:
        result = authorize_run(authorization_input, args.output_dir)
    except ValueError as error:
        parser.error(str(error))

    status = "更新しました" if result.changed else "変更はありません"
    print(f"{status}: {result.authorization_path} ({result.state_after}/{result.result})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
