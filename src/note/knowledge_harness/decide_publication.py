"""O-11 Decide Publicationの人間判断検証・保存処理とCLI。"""

from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Sequence

from note.knowledge_harness.storage import json_text, read_created_at, validate_run_id, write_if_changed

DECISIONS = {"revision", "reject", "policy_candidate"}


@dataclass(frozen=True)
class PublicationDecisionInput:
    review_packet_path: Path
    article_path: Path
    pr_snapshot_path: Path
    human_decision_path: Path | None
    expected_repository: str
    expected_pr_number: int
    expected_base: str
    authorized_actors: tuple[str, ...]
    created_at: str


@dataclass(frozen=True)
class PublicationDecisionResult:
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


def _review_packet(path: Path) -> dict[str, Any]:
    packet = _read_json(path, "Review Packet")
    if not isinstance(packet, dict) or packet.get("operation_id") != "O-10":
        raise ValueError("O-10が生成したReview Packetだけを受け付けます")
    if packet.get("state_after") != "REVIEW_READY" or packet.get("result") != "ADVANCE":
        raise ValueError("REVIEW_READY / ADVANCEのReview Packetだけを受け付けます")
    run_id = packet.get("run_id")
    if not isinstance(run_id, str):
        raise ValueError("Review Packetのrun_idが不正です")
    validate_run_id(run_id)
    return packet


def _validate_article(packet: dict[str, Any], path: Path) -> None:
    candidate = packet.get("publication_candidate")
    if not isinstance(candidate, dict) or candidate.get("path") != str(path):
        raise ValueError("公開候補のパスがReview Packetと一致しません")
    try:
        actual_sha = hashlib.sha256(path.read_bytes()).hexdigest()
    except (FileNotFoundError, OSError) as error:
        raise ValueError(f"公開候補を読めません: {path}") from error
    if candidate.get("sha256") != actual_sha:
        raise ValueError("公開候補のSHA-256がReview Packetと一致しません")


def _validate_snapshot(packet: dict[str, Any], snapshot: Any, value: PublicationDecisionInput) -> dict[str, Any]:
    if not isinstance(snapshot, dict):
        raise ValueError("PR snapshotはJSONオブジェクトで指定してください")
    expected_head = packet.get("pr_preparation", {}).get("head_branch")
    checks = (
        (snapshot.get("repository") == value.expected_repository, "repository"),
        (snapshot.get("number") == value.expected_pr_number, "PR番号"),
        (snapshot.get("base") == value.expected_base, "base"),
        (snapshot.get("head") == expected_head, "head"),
    )
    mismatches = [label for passed, label in checks if not passed]
    if mismatches:
        raise ValueError(f"PR snapshotが期待値と一致しません: {', '.join(mismatches)}")
    _nonempty(snapshot.get("url"), "PR snapshot.url")
    _nonempty(snapshot.get("head_sha"), "PR snapshot.head_sha")
    return snapshot


def _source(value: Any) -> dict[str, str]:
    if not isinstance(value, dict):
        raise ValueError("判断のsourceを指定してください")
    return {
        "url": _nonempty(value.get("url"), "source.url"),
        "reference_id": _nonempty(value.get("reference_id"), "source.reference_id"),
        "target_commit_sha": _nonempty(value.get("target_commit_sha"), "source.target_commit_sha"),
    }


def _structured_decision(raw: Any) -> dict[str, Any] | None:
    if raw is None:
        return None
    if not isinstance(raw, dict) or not isinstance(raw.get("decisions"), list):
        raise ValueError("人間判断はdecisions配列で指定してください")
    if len(raw["decisions"]) != 1:
        return {"conflict": True, "count": len(raw["decisions"])}
    decision = raw["decisions"][0]
    if not isinstance(decision, dict) or decision.get("decision") not in DECISIONS:
        raise ValueError("人間判断のdecisionが不正です")
    validated: dict[str, Any] = {
        "decision": decision["decision"],
        "actor": _nonempty(decision.get("actor"), "actor"),
        "decided_at": _nonempty(decision.get("decided_at"), "decided_at"),
        "reason_ja": _nonempty(decision.get("reason_ja"), "reason_ja"),
        "source": _source(decision.get("source")),
    }
    if decision["decision"] == "revision":
        validated["instruction_ja"] = _nonempty(decision.get("instruction_ja"), "instruction_ja")
        validated["target_ja"] = _nonempty(decision.get("target_ja"), "target_ja")
        validated["scope"] = "THIS_ARTICLE_ONLY"
    if decision["decision"] == "policy_candidate":
        options = decision.get("options")
        if not isinstance(options, list) or not 2 <= len(options) <= 3:
            raise ValueError("恒久方針候補のoptionsは2件以上3件以下にしてください")
        validated["problem_ja"] = _nonempty(decision.get("problem_ja"), "problem_ja")
        validated["options"] = [
            {
                "option_ja": _nonempty(item.get("option_ja") if isinstance(item, dict) else None, "option_ja"),
                "impact_ja": _nonempty(item.get("impact_ja") if isinstance(item, dict) else None, "impact_ja"),
            }
            for item in options
        ]
    return validated


def _outcome(snapshot: dict[str, Any], decision: dict[str, Any] | None, actors: set[str]) -> tuple[str, str, list[str], dict[str, Any]]:
    merged = snapshot.get("merged") is True
    if merged:
        actor = snapshot.get("merged_by")
        valid = isinstance(actor, str) and actor in actors and isinstance(snapshot.get("merge_commit_sha"), str)
        conflict = decision is not None
        if valid and not conflict:
            return "APPROVED", "ADVANCE", ["PUBLICATION_APPROVED"], {
                "status_ja": "公開を承認しました",
                "meaning_ja": "対象PRのmergeを確認しました。O-13で結果を記録します。",
                "human_action_required": False,
            }
        return "HOLD", "HOLD", ["AMBIGUOUS_OR_UNAUTHORIZED_DECISION"], {
            "status_ja": "判断を確認できないため保留します",
            "meaning_ja": "merge情報と判断入力に矛盾があるか、判断者を確認できません。公開扱いにしません。",
            "human_action_required": True,
        }
    if decision is None:
        return "HOLD", "HOLD", ["NO_HUMAN_RESPONSE"], {
            "status_ja": "回答待ちのため保留します",
            "meaning_ja": "回答がないため公開しません。",
            "human_action_required": True,
        }
    if decision.get("conflict") or decision.get("actor") not in actors or decision.get("source", {}).get("target_commit_sha") != snapshot.get("head_sha"):
        return "HOLD", "HOLD", ["AMBIGUOUS_OR_UNAUTHORIZED_DECISION"], {
            "status_ja": "判断を確認できないため保留します",
            "meaning_ja": "複数・矛盾する判断、対象外の判断者、またはcommit不整合があります。公開しません。",
            "human_action_required": True,
        }
    kind = decision["decision"]
    if kind == "revision":
        return "REVISION", "ADVANCE", ["REVISION_REQUESTED"], {
            "status_ja": "修正後に再確認します",
            "meaning_ja": "今回の記事だけに修正を反映し、O-12から再検証します。",
            "human_action_required": False,
        }
    if kind == "reject":
        return "HOLD", "HOLD", ["PUBLICATION_REJECTED"], {
            "status_ja": "公開しません",
            "meaning_ja": "人間がこの記事候補を棄却しました。O-13で結果を記録します。",
            "human_action_required": False,
        }
    return "HOLD", "HOLD", ["POLICY_CHANGE_CANDIDATE"], {
        "status_ja": "方針判断のため保留します",
        "meaning_ja": "今回は公開せず、恒久方針候補を別途検討します。",
        "human_action_required": True,
    }


def decide_publication(value: PublicationDecisionInput, output_dir: Path) -> PublicationDecisionResult:
    if not value.created_at.strip() or not value.authorized_actors:
        raise ValueError("created_atとauthorized_actorsを指定してください")
    packet = _review_packet(value.review_packet_path)
    _validate_article(packet, value.article_path)
    snapshot = _validate_snapshot(packet, _read_json(value.pr_snapshot_path, "PR snapshot"), value)
    raw_decision = _read_json(value.human_decision_path, "人間判断") if value.human_decision_path else None
    decision = _structured_decision(raw_decision)
    state_after, result, reasons, guidance = _outcome(snapshot, decision, set(value.authorized_actors))
    run_id = str(packet["run_id"])
    decision_path = output_dir / run_id / "publication_decision.json"
    record = {
        "schema_version": 1,
        "operation_id": "O-11",
        "run_id": run_id,
        "state_before": "REVIEW_READY",
        "state_after": state_after,
        "result": result,
        "reason_codes": reasons,
        "summary_ja": guidance["meaning_ja"],
        "human_guidance_ja": guidance,
        "created_at": value.created_at,
        "producer": "human_and_program",
        "pr": snapshot,
        "human_decision": decision,
        "input_refs": [str(value.review_packet_path), str(value.article_path), str(value.pr_snapshot_path)],
        "next_action": "O-12 Apply Feedbackへ渡す" if state_after == "REVISION" else "O-13 Record Outcomeへ渡す",
        "required_human_action": "policy" if reasons == ["POLICY_CHANGE_CANDIDATE"] else ("publication" if guidance["human_action_required"] else "none"),
    }
    changed = write_if_changed(decision_path, json_text(record))
    return PublicationDecisionResult(decision_path, changed, state_after, result)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="O-11 Decide Publicationを実行します")
    parser.add_argument("--review-packet-file", required=True, type=Path)
    parser.add_argument("--article-file", required=True, type=Path)
    parser.add_argument("--pr-snapshot-file", required=True, type=Path)
    parser.add_argument("--human-decision-file", type=Path)
    parser.add_argument("--repository", required=True)
    parser.add_argument("--pr-number", required=True, type=int)
    parser.add_argument("--base", default="main")
    parser.add_argument("--authorized-actor", required=True, action="append")
    parser.add_argument("--created-at")
    parser.add_argument("--output-dir", type=Path, default=Path("_notes/knowledge_harness/decisions"))
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = _parser()
    args = parser.parse_args(argv)
    try:
        packet = _review_packet(args.review_packet_file)
        output_path = args.output_dir / packet["run_id"] / "publication_decision.json"
        created_at = args.created_at or read_created_at(output_path) or datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")
        result = decide_publication(
            PublicationDecisionInput(args.review_packet_file, args.article_file, args.pr_snapshot_file, args.human_decision_file, args.repository, args.pr_number, args.base, tuple(args.authorized_actor), created_at),
            args.output_dir,
        )
    except ValueError as error:
        parser.error(str(error))
    status = "更新しました" if result.changed else "変更はありません"
    print(f"{status}: {result.decision_path} ({result.state_after}/{result.result})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
