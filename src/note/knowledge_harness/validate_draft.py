"""O-09 Validate DraftのProgram検査、AI Judge検証、CLI。"""

from __future__ import annotations

import argparse
import difflib
import hashlib
import io
import json
import re
import unicodedata
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Sequence

from docutils import nodes
from docutils.core import publish_doctree

from note.knowledge_harness.screen_safety import (
    DEFAULT_RESTRICTED_MARKERS,
    EMAIL_PATTERN,
    PHONE_PATTERN,
    SECRET_PATTERNS,
)
from note.knowledge_harness.storage import json_text, read_created_at, validate_run_id, write_if_changed

AI_AXES = (
    "factual_grounding",
    "semantic_leap",
    "reader_value",
    "plan_alignment",
    "uncertainty_handling",
)
VERDICTS = {"PASS", "FAIL", "UNCERTAIN"}
PASS_CONFIDENCE_THRESHOLD = 0.70
DUPLICATE_SIMILARITY_THRESHOLD = 0.85
URL_PATTERN = re.compile(r"https?://[^\s<>()\"']+")
INLINE_TARGET_PATTERN = re.compile(r"<([^>]+)>")
REQUIRED_METADATA = (
    ":記事状態:",
    ":公開日:",
    ":情報基準日:",
    ":対象バージョン:",
    ":生成動機:",
    ":AI担当範囲:",
    ":人間の確認範囲:",
)


@dataclass(frozen=True)
class ValidationInput:
    """O-09へ渡すDraft一式とAI Judge案。"""

    draft_path: Path
    manifest_path: Path
    plan_path: Path
    packet_path: Path
    judgment_path: Path
    created_at: str


@dataclass(frozen=True)
class ValidationResult:
    """Validation Reportと修正済みDraftの保存結果。"""

    report_path: Path
    validated_draft_path: Path
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


def _read_inputs(value: ValidationInput) -> tuple[str, dict[str, Any], dict[str, Any], dict[str, Any]]:
    try:
        draft = value.draft_path.read_text(encoding="utf-8")
    except (FileNotFoundError, OSError) as error:
        raise ValueError(f"Draftを読めません: {value.draft_path}") from error
    manifest = _read_json(value.manifest_path, "Draft manifest")
    plan = _read_json(value.plan_path, "Article Plan")
    packet = _read_json(value.packet_path, "Evidence Packet")
    if not isinstance(manifest, dict) or manifest.get("operation_id") != "O-08":
        raise ValueError("O-08が生成したDraft manifestだけを受け付けます")
    if manifest.get("state_after") != "DRAFT_READY" or manifest.get("result") != "ADVANCE":
        raise ValueError("DRAFT_READY / ADVANCEのDraftだけを検証できます")
    if not isinstance(plan, dict) or plan.get("operation_id") != "O-07":
        raise ValueError("O-07が生成したArticle Planだけを受け付けます")
    if plan.get("state_after") != "PLAN_READY" or plan.get("result") != "ADVANCE":
        raise ValueError("PLAN_READY / ADVANCEのArticle Planだけを検証できます")
    if not isinstance(packet, dict) or packet.get("operation_id") != "O-05":
        raise ValueError("O-05が生成したEvidence Packetだけを受け付けます")
    run_id = manifest.get("run_id")
    if not isinstance(run_id, str) or plan.get("run_id") != run_id or packet.get("run_id") != run_id:
        raise ValueError("Draft、Article Plan、Evidence Packetのrun_idが一致しません")
    validate_run_id(run_id)
    if not isinstance(manifest.get("sections"), list) or not isinstance(plan.get("sections"), list):
        raise ValueError("Draft manifestまたはArticle Planのsectionsが不正です")
    return draft, manifest, plan, packet


def _finding(severity: str, code: str, message_ja: str, **details: Any) -> dict[str, Any]:
    return {"severity": severity, "code": code, "message_ja": message_ja, **details}


def _mechanical_fix(text: str) -> tuple[str, list[str]]:
    fixes: list[str] = []
    lines = text.splitlines()
    stripped = [line.rstrip() for line in lines]
    if lines != stripped:
        fixes.append("TRAILING_WHITESPACE_REMOVED")
    for index in range(1, len(stripped)):
        line = stripped[index]
        previous = stripped[index - 1]
        if previous and len(set(line)) == 1 and line[0] in "=-~^#*+" and len(line) != len(previous):
            stripped[index] = line[0] * len(previous)
            fixes.append("GENERATED_HEADING_ADORNMENT_FIXED")
    fixed = "\n".join(stripped).rstrip("\n") + "\n"
    if not text.endswith("\n"):
        fixes.append("FINAL_NEWLINE_ADDED")
    return fixed, list(dict.fromkeys(fixes))


def _block_findings(
    draft: str, blocks: Any, seen_blocks: set[str]
) -> list[dict[str, Any]]:
    if not isinstance(blocks, list):
        return [_finding("ERROR", "INVALID_MANIFEST_BLOCKS", "manifestのblocksが不正です。")]
    findings: list[dict[str, Any]] = []
    for block in blocks:
        if not isinstance(block, dict):
            findings.append(_finding("ERROR", "INVALID_MANIFEST_BLOCK", "manifestのblockが不正です。"))
            continue
        block_id = block.get("block_id")
        body = block.get("body_rst")
        refs = block.get("packet_refs")
        if not isinstance(block_id, str) or block_id in seen_blocks:
            findings.append(_finding("ERROR", "DUPLICATE_BLOCK_ID", "block_idが不正または重複しています。"))
        else:
            seen_blocks.add(block_id)
        if not isinstance(body, str) or body not in draft:
            findings.append(_finding("ERROR", "BLOCK_BODY_MISMATCH", "manifestの本文ブロックがDraftに存在しません。", block_id=block_id))
        elif block.get("sha256") != hashlib.sha256(body.encode("utf-8")).hexdigest():
            findings.append(_finding("ERROR", "BLOCK_SHA_MISMATCH", "本文ブロックのSHA-256が一致しません。", block_id=block_id))
        if not isinstance(refs, list) or not refs:
            findings.append(_finding("ERROR", "INVALID_BLOCK_REFS", "本文ブロックのPacket参照が不正です。", block_id=block_id))
    return findings


def _manifest_findings(draft: str, manifest: dict[str, Any], plan: dict[str, Any]) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    actual_sha = hashlib.sha256(draft.encode("utf-8")).hexdigest()
    if manifest.get("draft_sha256") != actual_sha:
        findings.append(_finding("ERROR", "DRAFT_SHA_MISMATCH", "DraftのSHA-256がmanifestと一致しません。"))
    manifest_ids: list[str] = []
    seen_blocks: set[str] = set()
    for section in manifest["sections"]:
        if not isinstance(section, dict):
            findings.append(_finding("ERROR", "INVALID_MANIFEST_SECTION", "manifestの節が不正です。"))
            continue
        manifest_ids.append(str(section.get("section_id")))
        findings.extend(_block_findings(draft, section.get("blocks", []), seen_blocks))
    plan_ids = [section.get("section_id") for section in plan["sections"] if isinstance(section, dict)]
    if manifest_ids != plan_ids:
        findings.append(_finding("ERROR", "SECTION_ORDER_MISMATCH", "manifestとArticle Planの節IDまたは順序が一致しません。"))
    return findings


def _rst_findings(text: str) -> list[dict[str, Any]]:
    warning_stream = io.StringIO()
    try:
        tree = publish_doctree(
            text,
            settings_overrides={"halt_level": 6, "report_level": 1, "warning_stream": warning_stream},
        )
    except Exception as error:
        return [_finding("ERROR", "RST_PARSE_FAILED", f"reStructuredTextを解析できません: {error}")]
    findings: list[dict[str, Any]] = []
    for message in tree.findall(nodes.system_message):
        level = int(message.get("level", 0))
        findings.append(
            _finding(
                "ERROR" if level >= 3 else "WARNING",
                "RST_SYSTEM_MESSAGE",
                message.astext(),
                level=level,
            )
        )
    for marker in REQUIRED_METADATA:
        if marker not in text:
            findings.append(_finding("ERROR", "MISSING_METADATA", f"必須metadataがありません: {marker}"))
    return findings


def _allowed_urls(packet: dict[str, Any]) -> set[str]:
    urls: set[str] = set()
    catalog = packet.get("source_catalog", [])
    if isinstance(catalog, list):
        for source in catalog:
            if isinstance(source, dict):
                for field in ("url", "final_url"):
                    value = source.get(field)
                    if isinstance(value, str) and value:
                        urls.add(value.rstrip("/"))
    return urls


def _link_findings(text: str, packet: dict[str, Any], repo_root: Path) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    allowed = _allowed_urls(packet)
    for raw_url in URL_PATTERN.findall(text):
        url = raw_url.rstrip(".,;:)]}")
        if url.rstrip("/") not in allowed:
            findings.append(_finding("ERROR", "UNPLANNED_EXTERNAL_URL", "Evidence Packetにない外部URLです。", target=url))
    root = repo_root.resolve()
    for target in INLINE_TARGET_PATTERN.findall(text):
        target = target.strip()
        if target.startswith(("http://", "https://", "#", "mailto:")):
            continue
        resolved = (root / target).resolve()
        if not resolved.is_relative_to(root):
            findings.append(_finding("ERROR", "LOCAL_LINK_TRAVERSAL", "ローカル参照がリポジトリ外を指しています。", target=target))
        elif not resolved.exists():
            findings.append(_finding("ERROR", "LOCAL_LINK_MISSING", "ローカル参照先が存在しません。", target=target))
    return findings


def _normalize(value: str) -> str:
    normalized = unicodedata.normalize("NFKC", value).lower()
    return "".join(char for char in normalized if char.isalnum())


def _duplicate_findings(text: str, posts_dir: Path) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    lines = text.splitlines()
    title = next((line.strip() for line in lines if line.strip()), "")
    normalized_title = _normalize(title)
    normalized_text = _normalize(text)
    if not posts_dir.exists():
        return findings
    for path in posts_dir.glob("*.rst"):
        try:
            existing = path.read_text(encoding="utf-8")
        except OSError:
            continue
        existing_title = next((line.strip() for line in existing.splitlines() if line.strip()), "")
        if normalized_title and _normalize(existing_title) == normalized_title:
            findings.append(_finding("ERROR", "DUPLICATE_TITLE", "既存記事と正規化タイトルが一致します。", path=str(path)))
            continue
        similarity = difflib.SequenceMatcher(None, normalized_text, _normalize(existing)).ratio()
        if similarity >= DUPLICATE_SIMILARITY_THRESHOLD:
            findings.append(_finding("WARNING", "DUPLICATE_BODY_CANDIDATE", "既存記事との本文類似度が0.85以上です。", path=str(path), similarity=round(similarity, 4)))
    return findings


def _safety_findings(text: str) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    if any(pattern.search(text) for pattern in SECRET_PATTERNS):
        findings.append(_finding("ERROR", "SECRET_DETECTED", "秘密情報の可能性がある値を検出しました。"))
    if any(marker.lower() in text.lower() for marker in DEFAULT_RESTRICTED_MARKERS):
        findings.append(_finding("ERROR", "NONPUBLIC_MARKER_DETECTED", "非公開マーカーを検出しました。"))
    if EMAIL_PATTERN.search(text):
        findings.append(_finding("ERROR", "EMAIL_DETECTED", "マスクされていないメールアドレスを検出しました。"))
    if PHONE_PATTERN.search(text):
        findings.append(_finding("ERROR", "PHONE_DETECTED", "マスクされていない電話番号を検出しました。"))
    return findings


def _reference_catalog(manifest: dict[str, Any]) -> tuple[set[str], set[str]]:
    block_ids: set[str] = set()
    packet_refs: set[str] = set()
    for section in manifest["sections"]:
        if isinstance(section, dict) and isinstance(section.get("blocks"), list):
            for block in section["blocks"]:
                if isinstance(block, dict):
                    if isinstance(block.get("block_id"), str):
                        block_ids.add(block["block_id"])
                    if isinstance(block.get("packet_refs"), list):
                        packet_refs.update(ref for ref in block["packet_refs"] if isinstance(ref, str))
    return block_ids, packet_refs


def _confidence(value: Any, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not 0 <= value <= 1:
        raise ValueError(f"{label}は0から1の数値にしてください")
    return float(value)


def _judge(judgment: Any, manifest: dict[str, Any]) -> tuple[dict[str, Any], bool]:
    if not isinstance(judgment, dict):
        raise ValueError("AI Judge案はJSONオブジェクトである必要があります")
    raw = judgment.get("evaluations")
    if not isinstance(raw, dict) or set(raw) != set(AI_AXES):
        raise ValueError("evaluationsには5評価軸を過不足なく指定してください")
    block_catalog, ref_catalog = _reference_catalog(manifest)
    evaluations: dict[str, Any] = {}
    has_failure = False
    for axis in AI_AXES:
        value = raw[axis]
        if not isinstance(value, dict) or value.get("verdict") not in VERDICTS:
            raise ValueError(f"evaluations.{axis}.verdictが不正です")
        submitted = value["verdict"]
        confidence = _confidence(value.get("confidence"), f"evaluations.{axis}.confidence")
        verdict = "UNCERTAIN" if submitted == "PASS" and confidence < PASS_CONFIDENCE_THRESHOLD else submitted
        block_ids = value.get("block_ids")
        packet_refs = value.get("packet_refs")
        if not isinstance(block_ids, list) or not block_ids or any(item not in block_catalog for item in block_ids):
            raise ValueError(f"evaluations.{axis}が存在しないDraftブロックを参照しています")
        if not isinstance(packet_refs, list) or not packet_refs or any(item not in ref_catalog for item in packet_refs):
            raise ValueError(f"evaluations.{axis}が存在しないPacket項目を参照しています")
        evaluations[axis] = {
            "verdict": verdict,
            "submitted_verdict": submitted,
            "confidence": confidence,
            "reason_ja": _nonempty(value.get("reason_ja"), f"evaluations.{axis}.reason_ja"),
            "block_ids": list(dict.fromkeys(block_ids)),
            "packet_refs": list(dict.fromkeys(packet_refs)),
        }
        has_failure = has_failure or verdict != "PASS"
    policy = judgment.get("policy_change_candidate", {"required": False})
    if not isinstance(policy, dict) or not isinstance(policy.get("required"), bool):
        raise ValueError("policy_change_candidate.requiredが不正です")
    validated_policy: dict[str, Any] = {"required": policy["required"]}
    if policy["required"]:
        options = policy.get("options")
        if not isinstance(options, list) or not 2 <= len(options) <= 3:
            raise ValueError("方針変更候補のoptionsは2件以上3件以下にしてください")
        validated_policy.update(
            {
                "title_ja": _nonempty(policy.get("title_ja"), "policy_change_candidate.title_ja"),
                "problem_ja": _nonempty(policy.get("problem_ja"), "policy_change_candidate.problem_ja"),
                "options": [
                    {
                        "option_ja": _nonempty(option.get("option_ja") if isinstance(option, dict) else None, "option_ja"),
                        "impact_ja": _nonempty(option.get("impact_ja") if isinstance(option, dict) else None, "impact_ja"),
                    }
                    for option in options
                ],
            }
        )
    return {
        "rubric_version": _nonempty(judgment.get("rubric_version"), "rubric_version"),
        "judge_id": _nonempty(judgment.get("judge_id"), "judge_id"),
        "evaluations": evaluations,
        "policy_change_candidate": validated_policy,
    }, has_failure or validated_policy["required"]


def validate_draft(
    value: ValidationInput,
    output_dir: Path,
    *,
    posts_dir: Path = Path("docs/blog/posts"),
    repo_root: Path = Path("."),
) -> ValidationResult:
    """DraftをProgramとAI Judgeで検査し、Validation Reportを保存する。"""

    if not value.created_at.strip():
        raise ValueError("created_atを指定してください")
    draft, manifest, plan, packet = _read_inputs(value)
    judgment = _read_json(value.judgment_path, "AI Judge案")
    corrected, fixes = _mechanical_fix(draft)
    findings = _manifest_findings(draft, manifest, plan)
    findings.extend(_rst_findings(corrected))
    findings.extend(_link_findings(corrected, packet, repo_root))
    findings.extend(_duplicate_findings(corrected, posts_dir))
    findings.extend(_safety_findings(corrected))
    validated_judgment, judge_failed = _judge(judgment, manifest)
    program_failed = any(finding["severity"] == "ERROR" for finding in findings)
    blocked = program_failed or judge_failed
    state_after, result = ("HOLD", "HOLD") if blocked else ("VALIDATED", "ADVANCE")
    reasons = ["DRAFT_VALIDATION_FAILED"] if blocked else ["DRAFT_VALIDATED"]
    if validated_judgment["policy_change_candidate"]["required"]:
        reasons.append("POLICY_CHANGE_REQUIRED")
    run_id = str(manifest["run_id"])
    run_dir = output_dir / run_id
    validated_draft_path = run_dir / "validated_draft.rst"
    report_path = run_dir / "validation_report.json"
    report = {
        "schema_version": 1,
        "operation_id": "O-09",
        "run_id": run_id,
        "input_refs": [str(value.draft_path), str(value.manifest_path), str(value.plan_path), str(value.packet_path), str(value.judgment_path)],
        "state_before": "DRAFT_READY",
        "state_after": state_after,
        "result": result,
        "reason_codes": reasons,
        "created_at": value.created_at,
        "producer": "program_and_ai_judge",
        "program_validation": {
            "passed": not program_failed,
            "findings": findings,
            "auto_fixes": fixes,
            "auto_fix_passes": 1 if fixes else 0,
        },
        "ai_validation": validated_judgment,
        "validated_draft_sha256": hashlib.sha256(corrected.encode("utf-8")).hexdigest(),
        "artifacts": [str(validated_draft_path), str(report_path)],
        "next_action": "O-10 Prepare Reviewへ渡す" if result == "ADVANCE" else "公開せず保留する",
        "required_human_action": "policy" if validated_judgment["policy_change_candidate"]["required"] else "none",
    }
    draft_changed = write_if_changed(validated_draft_path, corrected)
    report_changed = write_if_changed(report_path, json_text(report))
    return ValidationResult(report_path, validated_draft_path, draft_changed or report_changed, state_after, result)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="O-09 Validate Draftを実行します")
    parser.add_argument("--draft-file", required=True, type=Path)
    parser.add_argument("--manifest-file", required=True, type=Path)
    parser.add_argument("--plan-file", required=True, type=Path)
    parser.add_argument("--packet-file", required=True, type=Path)
    parser.add_argument("--judgment-file", required=True, type=Path)
    parser.add_argument("--created-at")
    parser.add_argument("--posts-dir", type=Path, default=Path("docs/blog/posts"))
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    parser.add_argument("--output-dir", type=Path, default=Path("_notes/knowledge_harness/validations"))
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = _parser()
    args = parser.parse_args(argv)
    try:
        manifest = _read_json(args.manifest_file, "Draft manifest")
        if not isinstance(manifest, dict) or not isinstance(manifest.get("run_id"), str):
            raise ValueError("Draft manifestのrun_idが不正です")
        report_path = args.output_dir / manifest["run_id"] / "validation_report.json"
        created_at = args.created_at or read_created_at(report_path)
        if created_at is None:
            created_at = datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")
        result = validate_draft(
            ValidationInput(args.draft_file, args.manifest_file, args.plan_file, args.packet_file, args.judgment_file, created_at),
            args.output_dir,
            posts_dir=args.posts_dir,
            repo_root=args.repo_root,
        )
    except ValueError as error:
        parser.error(str(error))
    status = "更新しました" if result.changed else "変更はありません"
    print(f"{status}: {result.report_path} ({result.state_after}/{result.result})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
