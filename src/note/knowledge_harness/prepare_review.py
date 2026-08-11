"""O-10 Prepare Reviewの公開候補・Review Packet生成処理とCLI。"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from typing import Any, Sequence
from zoneinfo import ZoneInfo

from note.knowledge_harness.storage import json_text, read_created_at, validate_run_id, write_if_changed

SLUG_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
POST_DATE_PATTERN = re.compile(r"^\.\. post::\s*(\d{4}-\d{2}-\d{2})\s*$", re.MULTILINE)
METADATA_PATTERN = re.compile(r"^:(記事状態|公開日):.*(?:\n|$)", re.MULTILINE)


@dataclass(frozen=True)
class ReviewInput:
    """O-10へ渡す検証済み成果物と公開準備案。"""

    validated_draft_path: Path
    validation_report_path: Path
    plan_path: Path
    packet_path: Path
    proposal_path: Path
    created_at: str
    as_of_date: date


@dataclass(frozen=True)
class ReviewResult:
    """公開候補とReview Packetの保存結果。"""

    article_path: Path
    review_packet_path: Path
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


def _require_artifact(
    artifact: Any,
    *,
    operation_id: str,
    state_after: str,
    label: str,
) -> dict[str, Any]:
    if not isinstance(artifact, dict) or artifact.get("operation_id") != operation_id:
        raise ValueError(f"{operation_id}が生成した{label}だけを受け付けます")
    if artifact.get("state_after") != state_after or artifact.get("result") != "ADVANCE":
        raise ValueError(f"{state_after} / ADVANCEの{label}だけを受け付けます")
    return artifact


def _read_inputs(value: ReviewInput) -> tuple[str, dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]]:
    try:
        draft = value.validated_draft_path.read_text(encoding="utf-8")
    except (FileNotFoundError, OSError) as error:
        raise ValueError(f"検証済みDraftを読めません: {value.validated_draft_path}") from error
    report = _read_json(value.validation_report_path, "Validation Report")
    plan = _read_json(value.plan_path, "Article Plan")
    packet = _read_json(value.packet_path, "Evidence Packet")
    proposal = _read_json(value.proposal_path, "公開準備案")
    report = _require_artifact(report, operation_id="O-09", state_after="VALIDATED", label="Validation Report")
    plan = _require_artifact(plan, operation_id="O-07", state_after="PLAN_READY", label="Article Plan")
    packet = _require_artifact(packet, operation_id="O-05", state_after="PACKET_READY", label="Evidence Packet")
    run_id = report.get("run_id")
    if not isinstance(run_id, str) or plan.get("run_id") != run_id or packet.get("run_id") != run_id:
        raise ValueError("Validation Report、Article Plan、Evidence Packetのrun_idが一致しません")
    validate_run_id(run_id)
    actual_sha = hashlib.sha256(draft.encode("utf-8")).hexdigest()
    if report.get("validated_draft_sha256") != actual_sha:
        raise ValueError("検証済みDraftのSHA-256がValidation Reportと一致しません")
    guidance = report.get("human_guidance_ja")
    if not isinstance(guidance, dict) or not isinstance(guidance.get("summary_ja"), str):
        raise ValueError("Validation Reportに人間向け日本語案内がありません")
    if not isinstance(proposal, dict):
        raise ValueError("公開準備案はJSONオブジェクトである必要があります")
    return draft, report, plan, packet, proposal


def _string_list(value: Any, label: str) -> list[str]:
    if not isinstance(value, list) or not value:
        raise ValueError(f"{label}を一件以上指定してください")
    items = [_nonempty(item, f"{label}の要素") for item in value]
    if len(items) != len(set(items)):
        raise ValueError(f"{label}に重複があります")
    return items


def _proposal(value: dict[str, Any]) -> dict[str, Any]:
    slug = _nonempty(value.get("slug"), "slug")
    if not SLUG_PATTERN.fullmatch(slug):
        raise ValueError("slugは小文字英数字をハイフンで区切ってください")
    return {
        "review_version": _nonempty(value.get("review_version"), "review_version"),
        "preparer_id": _nonempty(value.get("preparer_id"), "preparer_id"),
        "final_title_ja": _nonempty(value.get("final_title_ja"), "final_title_ja"),
        "slug": slug,
        "tags": _string_list(value.get("tags"), "tags"),
        "category_ja": _nonempty(value.get("category_ja"), "category_ja"),
        "author": _nonempty(value.get("author"), "author"),
    }


def _used_dates(posts_dir: Path) -> set[date]:
    used: set[date] = set()
    if not posts_dir.exists():
        return used
    for path in posts_dir.glob("*.rst"):
        match = re.match(r"^(\d{4}-\d{2}-\d{2})-", path.name)
        if match:
            try:
                used.add(date.fromisoformat(match.group(1)))
            except ValueError:
                pass
        try:
            content = path.read_text(encoding="utf-8")
        except OSError:
            continue
        for post_date in POST_DATE_PATTERN.findall(content):
            try:
                used.add(date.fromisoformat(post_date))
            except ValueError:
                pass
    return used


def _publication_date(posts_dir: Path, as_of: date) -> date:
    candidate = as_of + timedelta(days=1)
    used = _used_dates(posts_dir)
    while candidate in used:
        candidate += timedelta(days=1)
    return candidate


def _existing_publication_date(review_packet_path: Path, run_id: str) -> date | None:
    if not review_packet_path.exists():
        return None
    existing = _read_json(review_packet_path, "既存Review Packet")
    if not isinstance(existing, dict) or existing.get("run_id") != run_id:
        raise ValueError("既存Review Packetのrun_idが一致しません")
    candidate = existing.get("publication_candidate")
    raw_date = candidate.get("publication_date") if isinstance(candidate, dict) else None
    try:
        return date.fromisoformat(raw_date) if isinstance(raw_date, str) else None
    except ValueError as error:
        raise ValueError("既存Review Packetの公開日が不正です") from error


def _render_article(draft: str, proposal: dict[str, Any], publication_date: date) -> str:
    lines = draft.splitlines()
    if len(lines) < 2 or not lines[0].strip():
        raise ValueError("検証済みDraftのタイトルを確認できません")
    index = 2 if set(lines[1].strip()) == {"="} else 1
    body = "\n".join(lines[index:]).lstrip("\n") + "\n"
    body = METADATA_PATTERN.sub("", body)
    title = proposal["final_title_ja"]
    header = [
        f".. post:: {publication_date.isoformat()}",
        f"   :tags: {', '.join(proposal['tags'])}",
        f"   :category: {proposal['category_ja']}",
        f"   :author: {proposal['author']}",
        "   :language: ja",
        "",
        title,
        "=" * len(title),
        "",
        ":記事状態: 公開候補",
        f":公開日: {publication_date.isoformat()}",
    ]
    return "\n".join(header) + "\n" + body


def _refs(plan: dict[str, Any]) -> list[str]:
    refs: list[str] = []
    for section in plan.get("sections", []):
        if isinstance(section, dict) and isinstance(section.get("packet_refs"), list):
            refs.extend(ref for ref in section["packet_refs"] if isinstance(ref, str))
    return list(dict.fromkeys(refs))


def prepare_review(value: ReviewInput, posts_dir: Path, output_dir: Path) -> ReviewResult:
    """検証済みDraftから公開候補と日本語Review Packetを生成する。"""

    if not value.created_at.strip():
        raise ValueError("created_atを指定してください")
    draft, report, plan, packet, raw_proposal = _read_inputs(value)
    proposal = _proposal(raw_proposal)
    run_id = str(report["run_id"])
    review_packet_path = output_dir / run_id / "review_packet.json"
    publication_date = _existing_publication_date(review_packet_path, run_id)
    if publication_date is None:
        publication_date = _publication_date(posts_dir, value.as_of_date)
    article_path = posts_dir / f"{publication_date.isoformat()}-{proposal['slug']}.rst"
    article = _render_article(draft, proposal, publication_date)
    packet_uncertainties = packet.get("uncertainties", [])
    uncertainties = packet_uncertainties if isinstance(packet_uncertainties, list) else []
    review_packet = {
        "schema_version": 1,
        "operation_id": "O-10",
        "run_id": run_id,
        "state_before": "VALIDATED",
        "state_after": "REVIEW_READY",
        "result": "ADVANCE",
        "reason_codes": ["PUBLICATION_REVIEW_PREPARED"],
        "created_at": value.created_at,
        "producer": "skill_agent_and_program",
        "review_version": proposal["review_version"],
        "preparer_id": proposal["preparer_id"],
        "publication_candidate": {
            "title_ja": proposal["final_title_ja"],
            "publication_date": publication_date.isoformat(),
            "path": str(article_path),
            "sha256": hashlib.sha256(article.encode("utf-8")).hexdigest(),
        },
        "review_summary_ja": {
            "status": "公開候補の確認待ち",
            "meaning": "自動検証済みの日本語記事です。まだ公開は承認されていません。",
            "central_message": _nonempty(plan.get("central_message_ja"), "central_message_ja"),
            "evidence_refs": _refs(plan),
            "uncertainties": uncertainties,
            "validation_summary": report.get("human_guidance_ja", {}),
            "ai_scope": "検証済みDraftへの公開用metadata付与とレビュー資料の準備。",
            "human_scope": "記事内容を確認し、次の4つから一つを選ぶ最終公開判断。",
            "choices": [
                {"decision": "merge", "label_ja": "公開を承認する", "effect_ja": "PRをマージし、記事を公開対象にします。"},
                {"decision": "revision", "label_ja": "今回だけ修正を求める", "effect_ja": "具体的な修正後に再検証します。"},
                {"decision": "reject", "label_ja": "公開しない", "effect_ja": "この記事候補を棄却します。"},
                {"decision": "policy_candidate", "label_ja": "今後の方針として検討する", "effect_ja": "今回は保留し、恒久方針候補を別途検討します。"},
            ],
            "if_no_response": "回答がない場合は公開せず、保留状態を維持します。",
        },
        "input_integrity": {
            "validated_draft": {"path": str(value.validated_draft_path), "sha256": report["validated_draft_sha256"]},
            "validation_report": {"path": str(value.validation_report_path), "sha256": hashlib.sha256(value.validation_report_path.read_bytes()).hexdigest()},
            "article_plan": {"path": str(value.plan_path), "sha256": hashlib.sha256(value.plan_path.read_bytes()).hexdigest()},
            "evidence_packet": {"path": str(value.packet_path), "sha256": hashlib.sha256(value.packet_path.read_bytes()).hexdigest()},
        },
        "pr_preparation": {
            "dedupe_key": run_id,
            "head_branch": f"article/{run_id}",
            "commit_message": f"記事公開候補を準備: {proposal['final_title_ja']}",
            "title": f"記事公開候補: {proposal['final_title_ja']}",
            "body_ja": "Review Packetを確認し、公開承認、今回だけの修正要求、棄却、恒久方針候補から一つを選んでください。回答がない場合は公開しません。",
            "draft": True,
        },
        "artifacts": [str(article_path), str(review_packet_path)],
        "next_action": "O-11 Decide Publicationで人間の最終公開判断を待つ",
        "required_human_action": "publication",
    }
    article_changed = write_if_changed(article_path, article)
    packet_changed = write_if_changed(review_packet_path, json_text(review_packet))
    return ReviewResult(article_path, review_packet_path, article_changed or packet_changed, "REVIEW_READY", "ADVANCE")


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="O-10 Prepare Reviewを実行します")
    parser.add_argument("--validated-draft-file", required=True, type=Path)
    parser.add_argument("--validation-report-file", required=True, type=Path)
    parser.add_argument("--plan-file", required=True, type=Path)
    parser.add_argument("--packet-file", required=True, type=Path)
    parser.add_argument("--proposal-file", required=True, type=Path)
    parser.add_argument("--created-at")
    parser.add_argument("--as-of-date", type=date.fromisoformat)
    parser.add_argument("--posts-dir", type=Path, default=Path("docs/blog/posts"))
    parser.add_argument("--output-dir", type=Path, default=Path("_notes/knowledge_harness/reviews"))
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = _parser()
    args = parser.parse_args(argv)
    try:
        report = _read_json(args.validation_report_file, "Validation Report")
        if not isinstance(report, dict) or not isinstance(report.get("run_id"), str):
            raise ValueError("Validation Reportのrun_idが不正です")
        packet_path = args.output_dir / report["run_id"] / "review_packet.json"
        created_at = args.created_at or read_created_at(packet_path)
        if created_at is None:
            created_at = datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")
        as_of = args.as_of_date or datetime.now(ZoneInfo("Asia/Tokyo")).date()
        result = prepare_review(
            ReviewInput(args.validated_draft_file, args.validation_report_file, args.plan_file, args.packet_file, args.proposal_file, created_at, as_of),
            args.posts_dir,
            args.output_dir,
        )
    except ValueError as error:
        parser.error(str(error))
    status = "更新しました" if result.changed else "変更はありません"
    print(f"{status}: {result.review_packet_path} ({result.state_after}/{result.result})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
