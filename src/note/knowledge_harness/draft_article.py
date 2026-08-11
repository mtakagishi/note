"""O-08 Draft Articleの検証・描画・保存処理とCLI。"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Sequence

from note.knowledge_harness.storage import json_text, read_created_at, validate_run_id, write_if_changed

UNSAFE_DIRECTIVE = re.compile(
    r"^\s*\.\.\s+(?:raw|include|literalinclude|image|figure|post)::",
    re.IGNORECASE | re.MULTILINE,
)
HEADING_ADORNMENT = re.compile(r"^[=\-~^#*+]{3,}\s*$", re.MULTILINE)


@dataclass(frozen=True)
class DraftInput:
    """O-08へ渡すArticle Plan、Evidence Packet、節別本文案。"""

    plan_path: Path
    packet_path: Path
    proposal_path: Path
    created_at: str


@dataclass(frozen=True)
class DraftResult:
    """Draftとmanifestの保存結果。"""

    draft_path: Path
    manifest_path: Path
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


def _read_inputs(plan_path: Path, packet_path: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    plan = _read_json(plan_path, "Article Plan")
    packet = _read_json(packet_path, "Evidence Packet")
    if not isinstance(plan, dict) or plan.get("operation_id") != "O-07":
        raise ValueError("O-07が生成したArticle Planだけを受け付けます")
    if plan.get("state_after") != "PLAN_READY" or plan.get("result") != "ADVANCE":
        raise ValueError("PLAN_READY / ADVANCEのArticle PlanだけをDraft化できます")
    if not isinstance(packet, dict) or packet.get("operation_id") != "O-05":
        raise ValueError("O-05が生成したEvidence Packetだけを受け付けます")
    if packet.get("state_after") != "PACKET_READY" or packet.get("result") != "ADVANCE":
        raise ValueError("PACKET_READY / ADVANCEのEvidence PacketだけをDraft化できます")
    run_id = plan.get("run_id")
    if not isinstance(run_id, str) or packet.get("run_id") != run_id:
        raise ValueError("Article PlanとEvidence Packetのrun_idが一致しません")
    validate_run_id(run_id)
    if not isinstance(plan.get("sections"), list) or not plan["sections"]:
        raise ValueError("Article Planのsectionsが不正です")
    if not isinstance(plan.get("uncertainty_treatments"), list):
        raise ValueError("Article Planのuncertainty_treatmentsが不正です")
    return plan, packet


def _refs(value: Any, label: str) -> list[str]:
    if not isinstance(value, list) or not value:
        raise ValueError(f"{label}を一件以上指定してください")
    refs = [_nonempty(ref, f"{label}の要素") for ref in value]
    if len(refs) != len(set(refs)):
        raise ValueError(f"{label}に重複があります")
    return refs


def _uncertainty_rules(plan: dict[str, Any]) -> tuple[set[str], set[str]]:
    required: set[str] = set()
    excluded: set[str] = set()
    for index, treatment in enumerate(plan["uncertainty_treatments"], start=1):
        if not isinstance(treatment, dict):
            raise ValueError(f"uncertainty_treatments[{index}]が不正です")
        packet_ref = _nonempty(
            treatment.get("packet_ref"), f"uncertainty_treatments[{index}].packet_ref"
        )
        action = treatment.get("action")
        if action in {"DISCLOSE", "LIMIT_CLAIM"}:
            required.add(packet_ref)
        elif action == "EXCLUDE":
            excluded.add(packet_ref)
        else:
            raise ValueError(f"uncertainty_treatments[{index}].actionが不正です")
    return required, excluded


def _validate_body(value: Any, label: str) -> str:
    body = _nonempty(value, label)
    if UNSAFE_DIRECTIVE.search(body):
        raise ValueError(f"{label}に許可されないreStructuredText directiveがあります")
    if HEADING_ADORNMENT.search(body):
        raise ValueError(f"{label}にPlan外の見出しを追加できません")
    return body


def _validate_sections(
    proposal: dict[str, Any], plan: dict[str, Any]
) -> tuple[list[dict[str, Any]], set[str]]:
    proposed = proposal.get("sections")
    if not isinstance(proposed, list):
        raise ValueError("sectionsは配列にしてください")
    planned = plan["sections"]
    proposed_ids = [item.get("section_id") if isinstance(item, dict) else None for item in proposed]
    planned_ids = [item.get("section_id") if isinstance(item, dict) else None for item in planned]
    if proposed_ids != planned_ids:
        raise ValueError("Article Planの全節を同じIDと順序で指定してください")
    block_ids: set[str] = set()
    used_refs: set[str] = set()
    sections: list[dict[str, Any]] = []
    for index, (section, planned_section) in enumerate(zip(proposed, planned, strict=True), start=1):
        label = f"sections[{index}]"
        if not isinstance(section, dict) or not isinstance(planned_section, dict):
            raise ValueError(f"{label}が不正です")
        allowed_refs = set(_refs(planned_section.get("packet_refs"), f"{label}のPlan参照"))
        blocks = section.get("blocks")
        if not isinstance(blocks, list) or not blocks:
            raise ValueError(f"{label}.blocksを一件以上指定してください")
        validated_blocks: list[dict[str, Any]] = []
        section_refs: set[str] = set()
        for block_index, block in enumerate(blocks, start=1):
            block_label = f"{label}.blocks[{block_index}]"
            if not isinstance(block, dict):
                raise ValueError(f"{block_label}はJSONオブジェクトで指定してください")
            block_id = _nonempty(block.get("block_id"), f"{block_label}.block_id")
            if block_id in block_ids:
                raise ValueError(f"block_idが重複しています: {block_id}")
            block_ids.add(block_id)
            body_rst = _validate_body(block.get("body_rst"), f"{block_label}.body_rst")
            packet_refs = _refs(block.get("packet_refs"), f"{block_label}.packet_refs")
            if not set(packet_refs) <= allowed_refs:
                raise ValueError(f"{block_label}がPlan外のPacket項目を参照しています")
            section_refs.update(packet_refs)
            used_refs.update(packet_refs)
            validated_blocks.append(
                {
                    "block_id": block_id,
                    "body_rst": body_rst,
                    "packet_refs": packet_refs,
                    "sha256": hashlib.sha256(body_rst.encode("utf-8")).hexdigest(),
                }
            )
        sections.append(
            {
                "section_id": section["section_id"],
                "heading_ja": _nonempty(planned_section.get("heading_ja"), f"{label}.heading_ja"),
                "blocks": validated_blocks,
                "used_packet_refs": sorted(section_refs),
                "planned_packet_refs": sorted(allowed_refs),
            }
        )
    return sections, used_refs


def _metadata(packet: dict[str, Any]) -> dict[str, Any]:
    versions: list[str] = []
    catalog = packet.get("source_catalog", [])
    if isinstance(catalog, list):
        for source in catalog:
            value = source.get("target_version") if isinstance(source, dict) else None
            if isinstance(value, str) and value.strip() and value.strip() not in versions:
                versions.append(value.strip())
    return {
        "language": "ja",
        "article_state": "Draft",
        "publication_date": "未確定",
        "information_as_of": packet.get("created_at") or "未確認",
        "target_versions": versions or ["未確認"],
    }


def _render(plan: dict[str, Any], sections: list[dict[str, Any]], metadata: dict[str, Any]) -> str:
    title = _nonempty(plan.get("working_title_ja"), "working_title_ja")
    lines = [
        title,
        "=" * len(title),
        "",
        f":記事状態: {metadata['article_state']}",
        f":公開日: {metadata['publication_date']}",
        f":情報基準日: {metadata['information_as_of']}",
        f":対象バージョン: {', '.join(metadata['target_versions'])}",
        ":生成動機: Article Planで採用された中心メッセージを公開可能な記事案へ展開するため。",
        ":AI担当範囲: Article PlanとEvidence Packetに基づく日本語Draftの生成。",
        ":人間の確認範囲: O-09検証後の事実性、表現、最終公開判断。",
        "",
    ]
    for section in sections:
        heading = section["heading_ja"]
        lines.extend([heading, "-" * len(heading), ""])
        for block in section["blocks"]:
            lines.extend([block["body_rst"], ""])
    return "\n".join(lines).rstrip() + "\n"


def _ensure_nonpublication_output(output_dir: Path) -> None:
    target = output_dir.resolve()
    publication_root = (Path.cwd() / "docs" / "blog" / "posts").resolve()
    if target == publication_root or target.is_relative_to(publication_root):
        raise ValueError("O-08はdocs/blog/posts/へDraftを配置できません")


def draft_article(draft_input: DraftInput, output_dir: Path) -> DraftResult:
    """本文案を検証し、追跡可能なreStructuredText Draftを保存する。"""

    if not draft_input.created_at.strip():
        raise ValueError("created_atを指定してください")
    _ensure_nonpublication_output(output_dir)
    plan, packet = _read_inputs(draft_input.plan_path, draft_input.packet_path)
    proposal = _read_json(draft_input.proposal_path, "本文案")
    if not isinstance(proposal, dict):
        raise ValueError("本文案はJSONオブジェクトである必要があります")
    draft_version = _nonempty(proposal.get("draft_version"), "draft_version")
    drafter_id = _nonempty(proposal.get("drafter_id"), "drafter_id")
    sections, used_refs = _validate_sections(proposal, plan)
    required_uncertainties, excluded_uncertainties = _uncertainty_rules(plan)
    if not required_uncertainties <= used_refs:
        raise ValueError("DISCLOSEまたはLIMIT_CLAIMの不確実性を本文へ反映してください")
    if excluded_uncertainties & used_refs:
        raise ValueError("EXCLUDEの不確実性を本文へ含めないでください")
    for section in sections:
        required_refs = set(section["planned_packet_refs"]) - excluded_uncertainties
        if not required_refs <= set(section["used_packet_refs"]):
            raise ValueError(f"{section['section_id']}の全計画参照を本文へ対応付けてください")
    metadata = _metadata(packet)
    draft_text = _render(plan, sections, metadata)
    run_id = str(plan["run_id"])
    run_dir = output_dir / run_id
    draft_path = run_dir / "draft.rst"
    manifest_path = run_dir / "draft_manifest.json"
    manifest = {
        "schema_version": 1,
        "operation_id": "O-08",
        "run_id": run_id,
        "input_refs": [
            str(draft_input.plan_path),
            str(draft_input.packet_path),
            str(draft_input.proposal_path),
        ],
        "state_before": "PLAN_READY",
        "state_after": "DRAFT_READY",
        "result": "ADVANCE",
        "reason_codes": ["ARTICLE_DRAFT_BUILT"],
        "created_at": draft_input.created_at,
        "producer": "skill_agent_and_program",
        "draft_version": draft_version,
        "drafter_id": drafter_id,
        "metadata": metadata,
        "sections": sections,
        "draft_sha256": hashlib.sha256(draft_text.encode("utf-8")).hexdigest(),
        "artifacts": [str(draft_path), str(manifest_path)],
        "next_action": "O-09 Validate Draftへ渡す",
        "required_human_action": "none",
    }
    draft_changed = write_if_changed(draft_path, draft_text)
    manifest_changed = write_if_changed(manifest_path, json_text(manifest))
    return DraftResult(
        draft_path, manifest_path, draft_changed or manifest_changed, "DRAFT_READY", "ADVANCE"
    )


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="O-08 Draft Articleを実行します")
    parser.add_argument("--plan-file", required=True, type=Path)
    parser.add_argument("--packet-file", required=True, type=Path)
    parser.add_argument("--proposal-file", required=True, type=Path)
    parser.add_argument("--created-at")
    parser.add_argument("--output-dir", type=Path, default=Path("_notes/knowledge_harness/drafts"))
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = _parser()
    args = parser.parse_args(argv)
    try:
        plan, _ = _read_inputs(args.plan_file, args.packet_file)
        manifest_path = args.output_dir / str(plan["run_id"]) / "draft_manifest.json"
        created_at = args.created_at or read_created_at(manifest_path)
        if created_at is None:
            created_at = datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")
        result = draft_article(
            DraftInput(args.plan_file, args.packet_file, args.proposal_file, created_at),
            args.output_dir,
        )
    except ValueError as error:
        parser.error(str(error))
    status = "更新しました" if result.changed else "変更はありません"
    print(f"{status}: {result.draft_path} ({result.state_after}/{result.result})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
