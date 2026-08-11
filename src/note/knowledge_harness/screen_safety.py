"""O-03 Screen Safetyの安全性検査とCLI。"""

from __future__ import annotations

import argparse
import json
import re
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

ASSESSMENTS = ("auto", "private", "uncertain")
DEFAULT_RESTRICTED_MARKERS = (
    "社外秘",
    "部外秘",
    "非公開会話",
    "私的な会話",
    "confidential",
    "internal only",
)
SECRET_PATTERNS = (
    re.compile(r"gh[pousr]_[A-Za-z0-9]{20,}"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    re.compile(
        r"\b(?:api[_ -]?key|access[_ -]?token|password|secret)\b\s*[:=]\s*[^\s]{8,}",
        re.IGNORECASE,
    ),
)
EMAIL_PATTERN = re.compile(r"(?<![\w.+-])[\w.+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
PHONE_PATTERN = re.compile(r"(?<!\d)0\d{1,4}-\d{1,4}-\d{3,4}(?!\d)")


@dataclass(frozen=True)
class SafetyInput:
    """O-03へ渡すAuthorizationと補助判定。"""

    authorization_path: Path
    assessment: str
    restricted_terms: list[str]
    created_at: str


@dataclass(frozen=True)
class SafetyResult:
    """安全性検査の結果と保存先。"""

    screening_path: Path
    changed: bool
    state_after: str
    result: str


@dataclass(frozen=True)
class ScreeningDecision:
    """機密値を含まない判定結果。"""

    state_after: str
    result: str
    reason_codes: list[str]
    summary_ja: str
    uncertainties: list[str]
    next_action: str
    required_human_action: str
    findings: list[str]
    question_ja: str
    source_ref: str


def _read_authorization(path: Path) -> dict[str, Any]:
    try:
        authorization = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as error:
        raise ValueError(f"Authorizationが見つかりません: {path}") from error
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"AuthorizationをJSONとして読めません: {path}") from error

    if not isinstance(authorization, dict):
        raise ValueError("AuthorizationはJSONオブジェクトである必要があります")
    run_id = authorization.get("run_id")
    if not isinstance(run_id, str):
        raise ValueError("Authorizationにrun_idがありません")
    validate_run_id(run_id)
    if authorization.get("operation_id") != "O-02":
        raise ValueError("O-02が生成したAuthorizationだけを受け付けます")
    if (
        authorization.get("state_after") != "AUTHORIZED"
        or authorization.get("result") != "ADVANCE"
    ):
        raise ValueError("AUTHORIZED / ADVANCEのAuthorizationだけを検査できます")
    return authorization


def _request_payload(authorization: dict[str, Any]) -> dict[str, str]:
    captured = authorization.get("request")
    payload = captured.get("request") if isinstance(captured, dict) else None
    if not isinstance(payload, dict):
        raise ValueError("AuthorizationにO-01のRequest本文がありません")

    required = ("question_ja", "source_ref", "source_kind")
    if any(not isinstance(payload.get(name), str) for name in required):
        raise ValueError("Request本文の必須項目が不正です")
    return {name: str(payload[name]) for name in required}


def _contains_secret(text: str) -> bool:
    return any(pattern.search(text) for pattern in SECRET_PATTERNS)


def _contains_restricted_marker(text: str, restricted_terms: Sequence[str]) -> bool:
    normalized = text.casefold()
    terms = (*DEFAULT_RESTRICTED_MARKERS, *restricted_terms)
    return any(term.strip().casefold() in normalized for term in terms if term.strip())


def _pii_findings(text: str) -> list[str]:
    findings: list[str] = []
    if EMAIL_PATTERN.search(text):
        findings.append("EMAIL_MASKED")
    if PHONE_PATTERN.search(text):
        findings.append("PHONE_MASKED")
    return findings


def _redact_pii(text: str) -> str:
    text = EMAIL_PATTERN.sub("[REDACTED_EMAIL]", text)
    return PHONE_PATTERN.sub("[REDACTED_PHONE]", text)


def _rejected_decision(findings: list[str]) -> ScreeningDecision:
    return ScreeningDecision(
        state_after="REJECTED",
        result="REJECTED",
        reason_codes=["SENSITIVE_INPUT_REJECTED"],
        summary_ja="秘密情報または明確な非公開情報を検出したため、処理対象外としました。",
        uncertainties=[],
        next_action="O-13 Record Outcomeへ渡す",
        required_human_action="none",
        findings=findings,
        question_ja="[REDACTED_REJECTED_INPUT]",
        source_ref="[REDACTED_REJECTED_INPUT]",
    )


def _uncertain_decision() -> ScreeningDecision:
    return ScreeningDecision(
        state_after="HOLD",
        result="HOLD",
        reason_codes=["PUBLICATION_STATUS_UNCERTAIN"],
        summary_ja="公開可能性を自動判定できないため、内容を保持せず待機します。",
        uncertainties=["入力を公開処理へ使用してよいか確認できていません。"],
        next_action="公開可能性だけを人間へ確認する",
        required_human_action="privacy",
        findings=["PUBLICATION_STATUS_UNCERTAIN"],
        question_ja="[WITHHELD_PENDING_CONFIRMATION]",
        source_ref="[WITHHELD_PENDING_CONFIRMATION]",
    )


def _screen_content(
    payload: dict[str, str], assessment: str, restricted_terms: Sequence[str]
) -> ScreeningDecision:
    combined = f"{payload['question_ja']}\n{payload['source_ref']}"
    if assessment == "private":
        return _rejected_decision(["DECLARED_PRIVATE_INPUT"])
    if assessment == "uncertain":
        return _uncertain_decision()

    findings: list[str] = []
    if _contains_secret(combined):
        findings.append("SECRET_DETECTED")
    if _contains_restricted_marker(combined, restricted_terms):
        findings.append("RESTRICTED_CONTENT_DETECTED")
    if findings:
        return _rejected_decision(findings)

    pii_findings = _pii_findings(combined)
    masked = bool(pii_findings)
    return ScreeningDecision(
        state_after="SCREENED",
        result="ADVANCE",
        reason_codes=["SENSITIVE_DATA_MASKED" if masked else "SAFETY_SCREEN_PASSED"],
        summary_ja=(
            "安全にマスクできる情報を除去し、後続処理へ渡します。"
            if masked
            else "明確な秘密情報、個人情報、非公開情報は検出されませんでした。"
        ),
        uncertainties=[],
        next_action="O-04 Collect Evidenceへ渡す",
        required_human_action="none",
        findings=pii_findings,
        question_ja=_redact_pii(payload["question_ja"]),
        source_ref=_redact_pii(payload["source_ref"]),
    )


def _validate(safety_input: SafetyInput) -> None:
    if safety_input.assessment not in ASSESSMENTS:
        raise ValueError(f"assessmentは{', '.join(ASSESSMENTS)}のいずれかにしてください")
    if not safety_input.created_at.strip():
        raise ValueError("created_atを指定してください")


def screen_safety(safety_input: SafetyInput, output_dir: Path) -> SafetyResult:
    """Authorizationを検査し、安全な情報だけを冪等に保存する。"""

    _validate(safety_input)
    authorization = _read_authorization(safety_input.authorization_path)
    payload = _request_payload(authorization)
    decision = _screen_content(payload, safety_input.assessment, safety_input.restricted_terms)
    run_id = str(authorization["run_id"])
    record = {
        "schema_version": 1,
        "operation_id": "O-03",
        "run_id": run_id,
        "input_refs": [str(safety_input.authorization_path)],
        "state_before": "AUTHORIZED",
        "state_after": decision.state_after,
        "result": decision.result,
        "reason_codes": decision.reason_codes,
        "summary_ja": decision.summary_ja,
        "uncertainties": decision.uncertainties,
        "created_at": safety_input.created_at,
        "producer": "program",
        "next_action": decision.next_action,
        "required_human_action": decision.required_human_action,
        "findings": decision.findings,
        "screened_request": {
            "run_id": run_id,
            "question_ja": decision.question_ja,
            "source_ref": decision.source_ref,
            "source_kind": payload["source_kind"],
        },
    }
    screening_path = output_dir / run_id / "screening.json"
    changed = write_if_changed(screening_path, json_text(record))
    return SafetyResult(
        screening_path=screening_path,
        changed=changed,
        state_after=decision.state_after,
        result=decision.result,
    )


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="O-03 Screen Safetyを実行します")
    parser.add_argument("--authorization-file", required=True, type=Path)
    parser.add_argument("--assessment", choices=ASSESSMENTS, default="auto")
    parser.add_argument("--restricted-term", action="append", default=[], dest="restricted_terms")
    parser.add_argument("--created-at")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("_notes/knowledge_harness/screened"),
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = _parser()
    args = parser.parse_args(argv)
    try:
        authorization = _read_authorization(args.authorization_file)
    except ValueError as error:
        parser.error(str(error))
    screening_path = args.output_dir / str(authorization["run_id"]) / "screening.json"
    created_at = args.created_at or read_created_at(screening_path)
    if created_at is None:
        created_at = datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")

    safety_input = SafetyInput(
        authorization_path=args.authorization_file,
        assessment=args.assessment,
        restricted_terms=args.restricted_terms,
        created_at=created_at,
    )
    try:
        result = screen_safety(safety_input, args.output_dir)
    except ValueError as error:
        parser.error(str(error))

    status = "更新しました" if result.changed else "変更はありません"
    print(f"{status}: {result.screening_path} ({result.state_after}/{result.result})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
