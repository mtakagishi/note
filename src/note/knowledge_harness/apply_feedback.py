"""O-12 Apply Feedbackの限定修正・追跡・保存処理とCLI。"""

from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Sequence

from note.knowledge_harness.draft_article import _validate_body
from note.knowledge_harness.storage import json_text, read_created_at, validate_run_id, write_if_changed

MAX_AI_REVISIONS = 2


@dataclass(frozen=True)
class FeedbackInput:
    decision_path: Path
    draft_path: Path
    manifest_path: Path
    proposal_path: Path
    created_at: str


@dataclass(frozen=True)
class FeedbackResult:
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


def _inputs(value: FeedbackInput) -> tuple[dict[str, Any], str, dict[str, Any], dict[str, Any]]:
    decision = _read_json(value.decision_path, "Publication Decision")
    manifest = _read_json(value.manifest_path, "Draft manifest")
    proposal = _read_json(value.proposal_path, "修正文案")
    try:
        draft = value.draft_path.read_text(encoding="utf-8")
    except (FileNotFoundError, OSError) as error:
        raise ValueError(f"Draftを読めません: {value.draft_path}") from error
    if not isinstance(decision, dict) or decision.get("operation_id") != "O-11":
        raise ValueError("O-11が生成したPublication Decisionだけを受け付けます")
    if decision.get("state_after") != "REVISION" or decision.get("result") != "ADVANCE":
        raise ValueError("REVISION / ADVANCEのPublication Decisionだけを受け付けます")
    if not isinstance(manifest, dict) or manifest.get("operation_id") not in {"O-08", "O-12"}:
        raise ValueError("O-08またはO-12が生成したDraft manifestだけを受け付けます")
    expected_state = "DRAFT_READY" if manifest.get("operation_id") == "O-08" else "REVISED"
    if manifest.get("state_after") != expected_state or manifest.get("result") != "ADVANCE":
        raise ValueError("正常なDraft manifestだけを受け付けます")
    run_id = decision.get("run_id")
    if not isinstance(run_id, str) or manifest.get("run_id") != run_id:
        raise ValueError("Publication DecisionとDraft manifestのrun_idが一致しません")
    validate_run_id(run_id)
    if manifest.get("draft_sha256") != hashlib.sha256(draft.encode("utf-8")).hexdigest():
        raise ValueError("DraftのSHA-256がmanifestと一致しません")
    if not isinstance(proposal, dict):
        raise ValueError("修正文案はJSONオブジェクトで指定してください")
    return decision, draft, manifest, proposal


def _requested(decision: dict[str, Any]) -> dict[str, Any]:
    human = decision.get("human_decision")
    if not isinstance(human, dict) or human.get("decision") != "revision":
        raise ValueError("今回限りの修正要求が見つかりません")
    source = human.get("source")
    if not isinstance(source, dict):
        raise ValueError("修正要求のGitHub参照が不正です")
    return {
        "instruction_ja": _nonempty(human.get("instruction_ja"), "instruction_ja"),
        "target_ja": _nonempty(human.get("target_ja"), "target_ja"),
        "scope": human.get("scope"),
        "source": {
            "url": _nonempty(source.get("url"), "source.url"),
            "reference_id": _nonempty(source.get("reference_id"), "source.reference_id"),
            "target_commit_sha": _nonempty(source.get("target_commit_sha"), "source.target_commit_sha"),
        },
    }


def _blocks(manifest: dict[str, Any]) -> tuple[dict[str, dict[str, Any]], list[dict[str, Any]]]:
    sections = manifest.get("sections")
    if not isinstance(sections, list) or not sections:
        raise ValueError("Draft manifestのsectionsが不正です")
    result: dict[str, dict[str, Any]] = {}
    for section in sections:
        if not isinstance(section, dict) or not isinstance(section.get("blocks"), list):
            raise ValueError("Draft manifestのsectionが不正です")
        for block in section["blocks"]:
            if not isinstance(block, dict):
                raise ValueError("Draft manifestのblockが不正です")
            block_id = _nonempty(block.get("block_id"), "block_id")
            if block_id in result:
                raise ValueError(f"block_idが重複しています: {block_id}")
            result[block_id] = block
    return result, sections


def _validate_changes(
    proposal: dict[str, Any], request: dict[str, Any], known: dict[str, dict[str, Any]]
) -> list[tuple[str, str, list[str]]]:
    if (proposal.get("instruction_ja"), proposal.get("target_ja")) != (request["instruction_ja"], request["target_ja"]):
        raise ValueError("修正文案の指示または対象がPublication Decisionと一致しません")
    changes = proposal.get("changes")
    if not isinstance(changes, list) or not changes:
        raise ValueError("changesを一件以上指定してください")
    seen: set[str] = set()
    validated: list[tuple[str, str, list[str]]] = []
    for index, change in enumerate(changes, start=1):
        if not isinstance(change, dict):
            raise ValueError(f"changes[{index}]が不正です")
        block_id = _nonempty(change.get("block_id"), f"changes[{index}].block_id")
        if block_id in seen or block_id not in known:
            raise ValueError(f"変更対象block_idが重複または不明です: {block_id}")
        seen.add(block_id)
        original = _nonempty(known[block_id].get("body_rst"), f"{block_id}.body_rst")
        body = _validate_body(change.get("body_rst"), f"changes[{index}].body_rst")
        if body == original:
            raise ValueError(f"変更後本文が変更前と同じです: {block_id}")
        supplied_refs = change.get("packet_refs")
        if supplied_refs != known[block_id].get("packet_refs"):
            raise ValueError(f"Packet参照を変更できません: {block_id}")
        validated.append((block_id, body, supplied_refs))
    return validated


def _apply(
    draft: str, manifest: dict[str, Any], proposal: dict[str, Any], request: dict[str, Any]
) -> tuple[str, list[dict[str, Any]], list[dict[str, Any]]]:
    known, sections = _blocks(manifest)
    changes = _validate_changes(proposal, request, known)
    revisions: list[dict[str, Any]] = []
    revised = draft
    replacements: dict[str, str] = {}
    for block_id, body, supplied_refs in changes:
        original = str(known[block_id]["body_rst"]).strip()
        if revised.count(original) != 1:
            raise ValueError(f"変更前本文をDraft内で一意に特定できません: {block_id}")
        revised = revised.replace(original, body, 1)
        replacements[block_id] = body
        revisions.append(
            {
                "block_id": block_id,
                "instruction_ja": request["instruction_ja"],
                "target_ja": request["target_ja"],
                "packet_refs": supplied_refs,
                "before_sha256": hashlib.sha256(original.encode("utf-8")).hexdigest(),
                "after_sha256": hashlib.sha256(body.encode("utf-8")).hexdigest(),
                "source": request["source"],
            }
        )
    updated_sections = json.loads(json.dumps(sections, ensure_ascii=False))
    for section in updated_sections:
        for block in section["blocks"]:
            if block["block_id"] in replacements:
                block["body_rst"] = replacements[block["block_id"]]
                block["sha256"] = hashlib.sha256(block["body_rst"].encode("utf-8")).hexdigest()
    return revised, updated_sections, revisions


def apply_feedback(value: FeedbackInput, output_dir: Path) -> FeedbackResult:
    if not value.created_at.strip():
        raise ValueError("created_atを指定してください")
    decision, draft, manifest, proposal = _inputs(value)
    request = _requested(decision)
    if request["scope"] != "THIS_ARTICLE_ONLY":
        raise ValueError("今回の記事だけを対象とする修正要求に限定します")
    revision_count = manifest.get("revision_count", 0)
    if not isinstance(revision_count, int) or revision_count < 0:
        raise ValueError("revision_countが不正です")
    if revision_count >= MAX_AI_REVISIONS:
        state_after, result, reasons = "HOLD", "HOLD", ["REVISION_LIMIT_EXCEEDED"]
        revised, sections, revisions = draft, manifest["sections"], []
        guidance = {
            "status_ja": "修正回数の上限に達したため保留します",
            "meaning_ja": "3回目のAI修正は実行しません。",
            "human_action_required": True,
        }
    else:
        revised, sections, revisions = _apply(draft, manifest, proposal, request)
        revision_count += 1
        state_after, result, reasons = "REVISED", "ADVANCE", ["FEEDBACK_APPLIED"]
        guidance = {
            "status_ja": "修正しました。再検証します",
            "meaning_ja": "指定された箇所だけを修正し、O-09へ戻します。",
            "human_action_required": False,
        }
    run_id = str(decision["run_id"])
    run_dir = output_dir / run_id
    draft_path = run_dir / "revised_draft.rst"
    manifest_path = run_dir / "revision_manifest.json"
    record = {
        "schema_version": 1,
        "operation_id": "O-12",
        "run_id": run_id,
        "state_before": "REVISION",
        "state_after": state_after,
        "result": result,
        "reason_codes": reasons,
        "created_at": value.created_at,
        "producer": "skill_agent_and_program",
        "revision_count": revision_count,
        "request": request,
        "revisions": revisions,
        "sections": sections,
        "draft_sha256": hashlib.sha256(revised.encode("utf-8")).hexdigest(),
        "input_refs": [
            str(value.decision_path),
            str(value.draft_path),
            str(value.manifest_path),
            str(value.proposal_path),
        ],
        "artifacts": [str(draft_path), str(manifest_path)],
        "human_guidance_ja": guidance,
        "next_action": "O-09 Validate Draftへ戻す" if result == "ADVANCE" else "O-13 Record Outcomeへ渡す",
        "required_human_action": "none" if result == "ADVANCE" else "exception",
    }
    draft_changed = write_if_changed(draft_path, revised)
    manifest_changed = write_if_changed(manifest_path, json_text(record))
    return FeedbackResult(draft_path, manifest_path, draft_changed or manifest_changed, state_after, result)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="O-12 Apply Feedbackを実行します")
    parser.add_argument("--decision-file", required=True, type=Path)
    parser.add_argument("--draft-file", required=True, type=Path)
    parser.add_argument("--manifest-file", required=True, type=Path)
    parser.add_argument("--proposal-file", required=True, type=Path)
    parser.add_argument("--created-at")
    parser.add_argument("--output-dir", type=Path, default=Path("_notes/knowledge_harness/revisions"))
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = _parser()
    args = parser.parse_args(argv)
    try:
        decision = _read_json(args.decision_file, "Publication Decision")
        run_id = _nonempty(decision.get("run_id") if isinstance(decision, dict) else None, "run_id")
        manifest_path = args.output_dir / run_id / "revision_manifest.json"
        created_at = (
            args.created_at
            or read_created_at(manifest_path)
            or datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")
        )
        result = apply_feedback(
            FeedbackInput(args.decision_file, args.draft_file, args.manifest_file, args.proposal_file, created_at),
            args.output_dir,
        )
    except ValueError as error:
        parser.error(str(error))
    status = "更新しました" if result.changed else "変更はありません"
    print(f"{status}: {result.draft_path} ({result.state_after}/{result.result})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
