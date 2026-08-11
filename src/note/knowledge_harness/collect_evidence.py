"""O-04 Collect Evidenceの公開情報取得とCLI。"""

from __future__ import annotations

import argparse
import hashlib
import json
import socket
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Callable, Sequence

from note.knowledge_harness.storage import json_text, read_created_at, write_if_changed

SOURCE_TYPES = ("primary", "secondary", "community", "discovery_only")
CONFIDENCE_LEVELS = ("high", "medium", "low", "unknown")


@dataclass(frozen=True)
class CollectionLimits:
    """O-04の初期収集上限。"""

    search_rounds: int = 3
    queries_per_round: int = 4
    retrievals: int = 20
    adopted_sources: int = 12
    per_domain: int = 3
    max_seconds: float = 900
    retries: int = 2


@dataclass(frozen=True)
class FetchResult:
    """URL取得結果。本文は成果物へ保存しない。"""

    final_url: str
    status: int
    content_type: str
    body: bytes


class RetrievalError(Exception):
    """取得失敗と再試行可能性。"""

    def __init__(self, message: str, *, retryable: bool) -> None:
        super().__init__(message)
        self.retryable = retryable


@dataclass(frozen=True)
class EvidenceInput:
    """O-04へ渡すScreening Resultと情報源候補。"""

    screening_path: Path
    sources_path: Path
    created_at: str
    limits: CollectionLimits = CollectionLimits()


@dataclass(frozen=True)
class EvidenceResult:
    """Evidence Setの保存結果。"""

    evidence_path: Path
    changed: bool
    state_after: str
    result: str


Fetcher = Callable[[str], FetchResult]
Clock = Callable[[], float]


def _read_json(path: Path, label: str) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as error:
        raise ValueError(f"{label}が見つかりません: {path}") from error
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"{label}をJSONとして読めません: {path}") from error


def _read_screening(path: Path) -> dict[str, Any]:
    screening = _read_json(path, "Screening Result")
    if not isinstance(screening, dict):
        raise ValueError("Screening ResultはJSONオブジェクトである必要があります")
    if screening.get("operation_id") != "O-03":
        raise ValueError("O-03が生成したScreening Resultだけを受け付けます")
    if screening.get("state_after") != "SCREENED" or screening.get("result") != "ADVANCE":
        raise ValueError("SCREENED / ADVANCEのScreening Resultだけを収集できます")
    run_id = screening.get("run_id")
    request = screening.get("screened_request")
    if not isinstance(run_id, str) or not isinstance(request, dict):
        raise ValueError("Screening Resultの必須項目が不正です")
    return screening


def _read_sources(path: Path) -> list[dict[str, Any]]:
    data = _read_json(path, "情報源候補")
    sources = data.get("sources") if isinstance(data, dict) else None
    if not isinstance(sources, list):
        raise ValueError("情報源候補にはsources配列が必要です")
    normalized: list[dict[str, Any]] = []
    for index, source in enumerate(sources, start=1):
        if not isinstance(source, dict):
            raise ValueError(f"情報源候補{index}はJSONオブジェクトで指定してください")
        url = source.get("url")
        source_type = source.get("source_type")
        if not isinstance(url, str) or urllib.parse.urlsplit(url).scheme not in {"http", "https"}:
            raise ValueError(f"情報源候補{index}のurlは公開HTTP(S) URLで指定してください")
        if source_type not in SOURCE_TYPES:
            raise ValueError(f"情報源候補{index}のsource_typeが不正です")
        confidence = source.get("confidence", "unknown")
        if confidence not in CONFIDENCE_LEVELS:
            raise ValueError(f"情報源候補{index}のconfidenceが不正です")
        search_round = source.get("search_round", 1)
        query = source.get("query", "")
        if not isinstance(search_round, int) or search_round < 1 or not isinstance(query, str):
            raise ValueError(f"情報源候補{index}の検索情報が不正です")
        normalized.append({**source, "confidence": confidence, "search_round": search_round, "query": query})
    return normalized


def _canonical_url(url: str) -> str:
    parts = urllib.parse.urlsplit(url)
    return urllib.parse.urlunsplit(
        (parts.scheme.casefold(), parts.netloc.casefold(), parts.path or "/", parts.query, "")
    )


def _domain(url: str) -> str:
    return (urllib.parse.urlsplit(url).hostname or "").casefold()


def _default_fetch(url: str) -> FetchResult:
    request = urllib.request.Request(url, headers={"User-Agent": "mtakagishi-note-evidence/1.0"})
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            body = response.read(2_000_001)
            if len(body) > 2_000_000:
                raise RetrievalError("本文が2MBの取得上限を超えました", retryable=False)
            return FetchResult(
                final_url=response.geturl(),
                status=response.status,
                content_type=response.headers.get_content_type(),
                body=body,
            )
    except urllib.error.HTTPError as error:
        raise RetrievalError(
            f"HTTP {error.code}", retryable=error.code == 429 or error.code >= 500
        ) from error
    except (urllib.error.URLError, TimeoutError, socket.timeout) as error:
        raise RetrievalError(f"接続エラー: {error.reason if hasattr(error, 'reason') else error}", retryable=True) from error


def _metadata(source: dict[str, Any]) -> dict[str, Any]:
    fields = (
        "title", "publisher", "author", "published_at", "updated_at", "target_version",
        "relevant_excerpt", "summary_ja", "supports", "limitations", "confidence",
        "confidence_reason", "relation", "contradictions", "uncertainties", "topics",
    )
    return {name: source.get(name) for name in fields}


def _validate_limits(limits: CollectionLimits) -> None:
    values = (
        limits.search_rounds, limits.queries_per_round, limits.retrievals,
        limits.adopted_sources, limits.per_domain, limits.max_seconds,
    )
    if any(value <= 0 for value in values) or limits.retries < 0:
        raise ValueError("収集上限は正数、retriesは0以上で指定してください")


def _excluded_reason(
    source: dict[str, Any],
    limits: CollectionLimits,
    queries: dict[int, set[str]],
    seen_urls: set[str],
    domains: Counter[str],
) -> str | None:
    search_round = source["search_round"]
    query = source["query"].strip()
    if search_round > limits.search_rounds:
        return "SEARCH_ROUND_LIMIT"
    if query and query not in queries[search_round] and len(queries[search_round]) >= limits.queries_per_round:
        return "QUERY_LIMIT"
    canonical = _canonical_url(source["url"])
    if canonical in seen_urls:
        return "DUPLICATE_SOURCE"
    if domains[_domain(canonical)] >= limits.per_domain:
        return "DOMAIN_LIMIT"
    return None


def _fetch_with_retries(
    url: str,
    limits: CollectionLimits,
    fetcher: Fetcher,
    clock: Clock,
    started: float,
    attempts_used: int,
) -> tuple[FetchResult | None, RetrievalError | None, int, int]:
    last_error: RetrievalError | None = None
    attempts = 0
    for attempts in range(1, limits.retries + 2):
        if attempts_used >= limits.retrievals or clock() - started >= limits.max_seconds:
            break
        attempts_used += 1
        try:
            return fetcher(url), None, attempts, attempts_used
        except RetrievalError as error:
            last_error = error
            if not error.retryable:
                break
    return None, last_error, attempts, attempts_used


def _decision(evidence_count: int, failures: list[dict[str, Any]]) -> tuple[str, str, list[str], str]:
    if evidence_count:
        return (
            "EVIDENCE_READY",
            "ADVANCE",
            ["EVIDENCE_COLLECTED"],
            f"公開情報源を{evidence_count}件取得し、不足と失敗を含めて記録しました。",
        )
    if failures and all(item["retryable"] for item in failures):
        return (
            "SCREENED",
            "RETRYABLE_ERROR",
            ["TEMPORARY_RETRIEVAL_FAILURE"],
            "一時的な取得失敗だけが残ったため、再試行可能な状態で終了しました。",
        )
    return (
        "HOLD",
        "HOLD",
        ["NO_EVIDENCE_RETRIEVED"],
        "情報源を取得できなかったため、取得不能の記録を残して保留しました。",
    )


def _uncertainties(
    sources: list[dict[str, Any]], failures: list[dict[str, Any]], excluded: Counter[str]
) -> list[str]:
    values = {
        str(value)
        for source in sources
        if isinstance(source.get("uncertainties"), list)
        for value in source["uncertainties"]
    }
    if any(source.get("contradictions") for source in sources):
        values.add("情報源間の矛盾があります。")
    if failures:
        values.add("取得できなかった情報源があります。")
    if excluded:
        values.add("収集上限または重複排除により未取得の候補があります。")
    return sorted(values)


def _preserve_elapsed_if_unchanged(path: Path, record: dict[str, Any]) -> None:
    if not path.exists():
        return
    try:
        previous = json.loads(path.read_text(encoding="utf-8"))
        previous_elapsed = previous["metrics"]["elapsed_seconds"]
        candidate = json.loads(json.dumps(record))
        candidate["metrics"]["elapsed_seconds"] = previous_elapsed
    except (OSError, json.JSONDecodeError, KeyError, TypeError):
        return
    if candidate == previous:
        record["metrics"]["elapsed_seconds"] = previous_elapsed


def collect_evidence(
    evidence_input: EvidenceInput,
    output_dir: Path,
    *,
    fetcher: Fetcher = _default_fetch,
    clock: Clock = time.monotonic,
) -> EvidenceResult:
    """候補URLを上限付きで取得し、欠落や矛盾を含むEvidence Setを保存する。"""

    _validate_limits(evidence_input.limits)
    if not evidence_input.created_at.strip():
        raise ValueError("created_atを指定してください")
    screening = _read_screening(evidence_input.screening_path)
    sources = _read_sources(evidence_input.sources_path)
    limits = evidence_input.limits
    started = clock()
    seen_urls: set[str] = set()
    queries: dict[int, set[str]] = defaultdict(set)
    domains: Counter[str] = Counter()
    evidence: list[dict[str, Any]] = []
    failures: list[dict[str, Any]] = []
    excluded: Counter[str] = Counter()
    retrieval_attempts = 0

    for source in sources:
        if clock() - started >= limits.max_seconds:
            excluded["TIME_LIMIT_REACHED"] += 1
            break
        reason = _excluded_reason(source, limits, queries, seen_urls, domains)
        if reason:
            excluded[reason] += 1
            continue
        if len(evidence) >= limits.adopted_sources or retrieval_attempts >= limits.retrievals:
            excluded["COLLECTION_LIMIT"] += 1
            break
        search_round = source["search_round"]
        query = source["query"].strip()
        queries[search_round].add(query) if query else None
        canonical = _canonical_url(source["url"])
        seen_urls.add(canonical)
        domain = _domain(canonical)
        fetched, last_error, attempts, retrieval_attempts = _fetch_with_retries(
            canonical, limits, fetcher, clock, started, retrieval_attempts
        )
        if fetched is None:
            failures.append(
                {
                    "url": canonical,
                    "source_type": source["source_type"],
                    "attempts": attempts,
                    "retryable": bool(last_error and last_error.retryable),
                    "reason": str(last_error or "収集上限へ到達しました"),
                    "metadata": _metadata(source),
                }
            )
            continue

        domains[domain] += 1
        evidence.append(
            {
                "source_id": f"source-{len(evidence) + 1:03d}",
                "url": canonical,
                "final_url": fetched.final_url,
                "source_type": source["source_type"],
                "retrieved_at": evidence_input.created_at,
                "http_status": fetched.status,
                "content_type": fetched.content_type,
                "content_sha256": hashlib.sha256(fetched.body).hexdigest(),
                "byte_count": len(fetched.body),
                "search_round": search_round,
                "query": query,
                "metadata": _metadata(source),
            }
        )
        if source.get("complete_scope") is True:
            excluded["EARLY_STOP_SCOPE_COMPLETE"] += len(sources) - len(seen_urls)
            break

    state_after, result, reason_codes, summary = _decision(len(evidence), failures)

    source_counts = Counter(item["source_type"] for item in evidence)
    metrics = {
        "candidate_sources": len(sources),
        "search_queries": sum(len(values) for values in queries.values()),
        "retrieval_attempts": retrieval_attempts,
        "retrieval_successes": len(evidence),
        "retrieval_success_rate": round(len(evidence) / retrieval_attempts, 4) if retrieval_attempts else 0.0,
        "adopted_sources": len(evidence),
        "primary_source_rate": round(source_counts["primary"] / len(evidence), 4) if evidence else 0.0,
        "source_types": dict(sorted(source_counts.items())),
        "retrieval_failures": len(failures),
        "excluded": dict(sorted(excluded.items())),
        "contradiction_sources": sum(bool(item.get("contradictions")) for item in sources),
        "uncertainty_sources": sum(bool(item.get("uncertainties")) for item in sources),
        "elapsed_seconds": round(clock() - started, 3),
    }
    run_id = str(screening["run_id"])
    record = {
        "schema_version": 1,
        "operation_id": "O-04",
        "run_id": run_id,
        "input_refs": [str(evidence_input.screening_path), str(evidence_input.sources_path)],
        "state_before": "SCREENED",
        "state_after": state_after,
        "result": result,
        "reason_codes": reason_codes,
        "summary_ja": summary,
        "uncertainties": _uncertainties(sources, failures, excluded),
        "created_at": evidence_input.created_at,
        "producer": "program",
        "next_action": "O-05 Build Evidence Packetへ渡す" if evidence else "O-13 Record Outcomeへ渡す",
        "required_human_action": "none",
        "screened_request": screening["screened_request"],
        "evidence": evidence,
        "retrieval_failures": failures,
        "metrics": metrics,
        "limits": evidence_input.limits.__dict__,
    }
    evidence_path = output_dir / run_id / "evidence.json"
    _preserve_elapsed_if_unchanged(evidence_path, record)
    changed = write_if_changed(evidence_path, json_text(record))
    return EvidenceResult(evidence_path, changed, state_after, result)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="O-04 Collect Evidenceを実行します")
    parser.add_argument("--screening-file", required=True, type=Path)
    parser.add_argument("--sources-file", required=True, type=Path)
    parser.add_argument("--created-at")
    parser.add_argument("--output-dir", type=Path, default=Path("_notes/knowledge_harness/evidence"))
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    screening = _read_screening(args.screening_file)
    evidence_path = args.output_dir / str(screening["run_id"]) / "evidence.json"
    created_at = args.created_at or read_created_at(evidence_path)
    if created_at is None:
        created_at = datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")
    try:
        result = collect_evidence(
            EvidenceInput(args.screening_file, args.sources_file, created_at), args.output_dir
        )
    except ValueError as error:
        _parser().error(str(error))
    status = "更新しました" if result.changed else "変更はありません"
    print(f"{status}: {result.evidence_path} ({result.state_after}/{result.result})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
