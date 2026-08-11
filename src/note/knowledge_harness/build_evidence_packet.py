"""O-05 Build Evidence Packetの検証・保存処理とCLI。"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Sequence

from note.knowledge_harness.storage import json_text, read_created_at, write_if_changed

ITEM_KINDS = ("fact", "inference", "unconfirmed", "community_reaction", "contradiction")


@dataclass(frozen=True)
class PacketInput:
    """O-05へ渡すEvidence SetとSkill / Agentの整理案。"""

    evidence_path: Path
    draft_path: Path
    created_at: str


@dataclass(frozen=True)
class PacketResult:
    """Evidence Packetの保存結果。"""

    packet_path: Path
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


def _read_evidence(path: Path) -> dict[str, Any]:
    evidence_set = _read_json(path, "Evidence Set")
    if not isinstance(evidence_set, dict):
        raise ValueError("Evidence SetはJSONオブジェクトである必要があります")
    if evidence_set.get("operation_id") != "O-04":
        raise ValueError("O-04が生成したEvidence Setだけを受け付けます")
    if evidence_set.get("state_after") != "EVIDENCE_READY" or evidence_set.get("result") != "ADVANCE":
        raise ValueError("EVIDENCE_READY / ADVANCEのEvidence Setだけを整理できます")
    if not isinstance(evidence_set.get("run_id"), str) or not isinstance(evidence_set.get("evidence"), list):
        raise ValueError("Evidence Setの必須項目が不正です")
    return evidence_set


def _source_catalog(evidence_set: dict[str, Any]) -> dict[str, dict[str, Any]]:
    catalog: dict[str, dict[str, Any]] = {}
    for index, source in enumerate(evidence_set["evidence"], start=1):
        if not isinstance(source, dict):
            raise ValueError(f"Evidence Setの情報源{index}が不正です")
        source_id = source.get("source_id")
        source_type = source.get("source_type")
        if not isinstance(source_id, str) or not source_id or source_id in catalog:
            raise ValueError("Evidence Setのsource_idは一意な非空文字列にしてください")
        if source_type not in {"primary", "secondary", "community", "discovery_only"}:
            raise ValueError(f"{source_id}のsource_typeが不正です")
        catalog[source_id] = source
    if not catalog:
        raise ValueError("Evidence Setに利用可能な情報源がありません")
    return catalog


def _nonempty(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label}は空でない文字列にしてください")
    return value.strip()


def _validate_item(
    item: Any,
    label: str,
    catalog: dict[str, dict[str, Any]],
    seen_ids: set[str],
) -> dict[str, Any]:
    if not isinstance(item, dict):
        raise ValueError(f"{label}はJSONオブジェクトで指定してください")
    item_id = _nonempty(item.get("item_id"), f"{label}.item_id")
    if item_id in seen_ids:
        raise ValueError(f"item_idが重複しています: {item_id}")
    seen_ids.add(item_id)
    kind = item.get("kind")
    if kind not in ITEM_KINDS:
        raise ValueError(f"{label}.kindは{', '.join(ITEM_KINDS)}から選んでください")
    statement = _nonempty(item.get("statement_ja"), f"{label}.statement_ja")
    source_ids = item.get("source_ids")
    if not isinstance(source_ids, list) or not source_ids:
        raise ValueError(f"{label}.source_idsを一件以上指定してください")
    if any(not isinstance(source_id, str) or source_id not in catalog for source_id in source_ids):
        raise ValueError(f"{label}が存在しないsource_idを参照しています")
    unique_source_ids = list(dict.fromkeys(source_ids))
    if kind == "contradiction" and len(unique_source_ids) < 2:
        raise ValueError(f"{label}の矛盾には二件以上のsource_idが必要です")
    if kind == "community_reaction" and not any(
        catalog[source_id]["source_type"] in {"secondary", "community"}
        for source_id in unique_source_ids
    ):
        raise ValueError(f"{label}の世間的反応にはsecondaryまたはcommunity情報源が必要です")
    return {
        "item_id": item_id,
        "kind": kind,
        "statement_ja": statement,
        "source_ids": unique_source_ids,
        "source_types": sorted({catalog[source_id]["source_type"] for source_id in unique_source_ids}),
        "notes_ja": str(item.get("notes_ja", "")).strip(),
    }


def _validate_items(
    values: Any,
    label: str,
    catalog: dict[str, dict[str, Any]],
    seen_ids: set[str],
    *,
    allow_empty: bool = False,
) -> list[dict[str, Any]]:
    if not isinstance(values, list) or (not values and not allow_empty):
        raise ValueError(f"{label}は{'' if allow_empty else '一件以上の'}配列にしてください")
    return [
        _validate_item(item, f"{label}[{index}]", catalog, seen_ids)
        for index, item in enumerate(values, start=1)
    ]


def _validate_topics(
    values: Any, catalog: dict[str, dict[str, Any]], seen_ids: set[str]
) -> list[dict[str, Any]]:
    if not isinstance(values, list) or not values:
        raise ValueError("topicsを一件以上指定してください")
    topics: list[dict[str, Any]] = []
    topic_ids: set[str] = set()
    for index, topic in enumerate(values, start=1):
        if not isinstance(topic, dict):
            raise ValueError(f"topics[{index}]はJSONオブジェクトで指定してください")
        topic_id = _nonempty(topic.get("topic_id"), f"topics[{index}].topic_id")
        if topic_id in topic_ids:
            raise ValueError(f"topic_idが重複しています: {topic_id}")
        topic_ids.add(topic_id)
        topics.append(
            {
                "topic_id": topic_id,
                "title_ja": _nonempty(topic.get("title_ja"), f"topics[{index}].title_ja"),
                "items": _validate_items(topic.get("items"), f"topics[{index}].items", catalog, seen_ids),
            }
        )
    return topics


def _past_articles(
    value: Any, catalog: dict[str, dict[str, Any]], seen_ids: set[str]
) -> dict[str, Any]:
    if value is None:
        value = {}
    if not isinstance(value, dict):
        raise ValueError("past_articlesはJSONオブジェクトで指定してください")
    refs = value.get("article_refs", [])
    if not isinstance(refs, list) or any(not isinstance(ref, str) or not ref.strip() for ref in refs):
        raise ValueError("past_articles.article_refsは空でない文字列の配列にしてください")
    groups = {
        name: _validate_items(value.get(name, []), f"past_articles.{name}", catalog, seen_ids, allow_empty=True)
        for name in ("known_items", "difference_candidates", "recheck_items")
    }
    if not refs and (groups["known_items"] or groups["difference_candidates"]):
        raise ValueError("過去記事参照なしで既知事項や差分候補を推測できません")
    return {
        "article_refs": list(dict.fromkeys(ref.strip() for ref in refs)),
        "status": "COMPARED" if refs else "UNCONFIRMED_NO_PAST_ARTICLE",
        **groups,
    }


def _draft(path: Path) -> dict[str, Any]:
    draft = _read_json(path, "Packet整理案")
    if not isinstance(draft, dict):
        raise ValueError("Packet整理案はJSONオブジェクトである必要があります")
    return draft


def build_evidence_packet(packet_input: PacketInput, output_dir: Path) -> PacketResult:
    """Skill / Agentの整理案を検証し、追跡可能なEvidence Packetを保存する。"""

    if not packet_input.created_at.strip():
        raise ValueError("created_atを指定してください")
    evidence_set = _read_evidence(packet_input.evidence_path)
    catalog = _source_catalog(evidence_set)
    draft = _draft(packet_input.draft_path)
    seen_ids: set[str] = set()
    topics = _validate_topics(draft.get("topics"), catalog, seen_ids)
    past_articles = _past_articles(draft.get("past_articles"), catalog, seen_ids)
    summary_ja = _nonempty(draft.get("summary_ja"), "summary_ja")
    source_catalog = [
        {
            "source_id": source_id,
            "source_type": source["source_type"],
            "url": source.get("url"),
            "final_url": source.get("final_url"),
            "title": source.get("metadata", {}).get("title") if isinstance(source.get("metadata"), dict) else None,
        }
        for source_id, source in catalog.items()
    ]
    inherited_uncertainties = evidence_set.get("uncertainties", [])
    inherited_failures = evidence_set.get("retrieval_failures", [])
    if not isinstance(inherited_uncertainties, list) or not isinstance(inherited_failures, list):
        raise ValueError("Evidence Setの不確実性または取得失敗が不正です")
    run_id = str(evidence_set["run_id"])
    record = {
        "schema_version": 1,
        "operation_id": "O-05",
        "run_id": run_id,
        "input_refs": [str(packet_input.evidence_path), str(packet_input.draft_path)],
        "state_before": "EVIDENCE_READY",
        "state_after": "PACKET_READY",
        "result": "ADVANCE",
        "reason_codes": ["EVIDENCE_PACKET_BUILT"],
        "summary_ja": summary_ja,
        "uncertainties": inherited_uncertainties,
        "created_at": packet_input.created_at,
        "producer": "skill_agent",
        "next_action": "O-06 Judge Candidateへ渡す",
        "required_human_action": "none",
        "screened_request": evidence_set.get("screened_request"),
        "topics": topics,
        "past_articles": past_articles,
        "source_catalog": source_catalog,
        "retrieval_failures": inherited_failures,
        "evidence_metrics": evidence_set.get("metrics", {}),
    }
    packet_path = output_dir / run_id / "evidence_packet.json"
    changed = write_if_changed(packet_path, json_text(record))
    return PacketResult(packet_path, changed, "PACKET_READY", "ADVANCE")


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="O-05 Build Evidence Packetを実行します")
    parser.add_argument("--evidence-file", required=True, type=Path)
    parser.add_argument("--draft-file", required=True, type=Path)
    parser.add_argument("--created-at")
    parser.add_argument("--output-dir", type=Path, default=Path("_notes/knowledge_harness/packets"))
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    evidence_set = _read_evidence(args.evidence_file)
    packet_path = args.output_dir / str(evidence_set["run_id"]) / "evidence_packet.json"
    created_at = args.created_at or read_created_at(packet_path)
    if created_at is None:
        created_at = datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")
    try:
        result = build_evidence_packet(
            PacketInput(args.evidence_file, args.draft_file, created_at), args.output_dir
        )
    except ValueError as error:
        _parser().error(str(error))
    status = "更新しました" if result.changed else "変更はありません"
    print(f"{status}: {result.packet_path} ({result.state_after}/{result.result})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
