"""
Copilot チャットセッションを Markdown に書き出すスクリプト。

使い方:
    rye run python export_sessions.py              # 全セッションを出力
    rye run python export_sessions.py --latest     # 最新1件だけ
    rye run python export_sessions.py --session <id>  # 特定セッション
    rye run python export_sessions.py --out <path>    # 出力先を指定
    rye run python export_sessions.py --list          # セッション一覧だけ表示
"""

import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


# VS Code User データ配下の既定パス
APPDATA = os.environ.get("APPDATA")
DEFAULT_WORKSPACE_STORAGE_DIR = (
    Path(APPDATA) / "Code" / "User" / "workspaceStorage"
    if APPDATA
    else Path.home() / "AppData" / "Roaming" / "Code" / "User" / "workspaceStorage"
)

# 出力先の既定（このリポジトリ配下の作業ログ用フォルダ）
DEFAULT_OUT_DIR = Path(__file__).parent / "_notes" / "sessions"


# --------------------------------------------------------------------------- #
# JSONL パーサ
# --------------------------------------------------------------------------- #

def _strip_xml_wrappers(text: str) -> str:
    """Copilot が付加する XML ラッパーを除去して純粋なユーザー入力だけを返す。"""
    # <userRequest> タグがあればその中身を優先
    m = re.search(r"<userRequest>([\s\S]*?)</userRequest>", text)
    if m:
        return m.group(1).strip()
    # その他の内部タグを除去
    for tag in (
        "context", "editorContext", "reminderInstructions",
        "environment_info", "workspace_info", "userMemory",
        "sessionMemory", "repoMemory", "attachments", "skills",
        "instructions", "agents",
    ):
        text = re.sub(rf"<{tag}>[\s\S]*?</{tag}>", "", text)
    return text.strip()


def parse_jsonl(file_path: Path, workspace_id: str | None = None) -> dict | None:
    """
    1つの .jsonl ファイルをパースしてセッション dict を返す。
    プロンプトが1件もなければ None を返す。
    """
    session_id = file_path.stem
    start_time: str = ""
    turns: list[dict] = []        # {"role": "user"|"assistant", "content": str, "ts": str}
    current_assistant_chunks: list[str] = []

    try:
        raw = file_path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None

    for line in raw.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            ev = json.loads(line)
        except json.JSONDecodeError:
            continue

        ev_type = ev.get("type", "")
        data = ev.get("data") or {}
        ts = ev.get("timestamp", "")

        if ev_type == "session.start":
            session_id = data.get("sessionId") or session_id
            start_time = data.get("startTime") or ts

        elif ev_type == "user.message":
            # アシスタントの途中チャンクがあれば確定させる
            if current_assistant_chunks:
                turns.append({
                    "role": "assistant",
                    "content": "".join(current_assistant_chunks).strip(),
                    "ts": ts,
                })
                current_assistant_chunks = []
            content = _strip_xml_wrappers(data.get("content") or "")
            if content:
                turns.append({"role": "user", "content": content, "ts": ts})

        elif ev_type == "assistant.message":
            content = (data.get("content") or "").strip()
            if content:
                current_assistant_chunks.append(content)

        elif ev_type == "assistant.turn_end":
            if current_assistant_chunks:
                turns.append({
                    "role": "assistant",
                    "content": "".join(current_assistant_chunks).strip(),
                    "ts": ts,
                })
                current_assistant_chunks = []

    # ファイル末端でも未確定チャンクを回収
    if current_assistant_chunks:
        turns.append({
            "role": "assistant",
            "content": "".join(current_assistant_chunks).strip(),
            "ts": "",
        })

    user_turns = [t for t in turns if t["role"] == "user"]
    if not user_turns:
        return None

    title = _derive_title(user_turns[0]["content"])
    return {
        "session_id": session_id,
        "start_time": start_time,
        "title": title,
        "turns": turns,
        "workspace_id": workspace_id,
        "file": file_path,
    }


def _derive_title(text: str) -> str:
    cleaned = text.replace("\n", " ").strip()
    if len(cleaned) <= 80:
        return cleaned
    return cleaned[:77] + "..."


def _safe_get(obj: Any, path: list[Any]) -> Any:
    cur = obj
    for key in path:
        if isinstance(key, int):
            if not isinstance(cur, list) or key < 0 or key >= len(cur):
                return None
            cur = cur[key]
        else:
            if not isinstance(cur, dict):
                return None
            cur = cur.get(key)
    return cur


def _extract_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, (int, float, bool)):
        return str(value)
    if isinstance(value, list):
        chunks = [_extract_text(v) for v in value]
        return "\n".join([c for c in chunks if c]).strip()
    if isinstance(value, dict):
        for key in ("text", "value", "content", "message", "inputText"):
            if key in value:
                txt = _extract_text(value.get(key))
                if txt:
                    return txt
        parts = value.get("parts")
        if parts is not None:
            txt = _extract_text(parts)
            if txt:
                return txt
    return ""


def _extract_tool_message(item: dict[str, Any]) -> str:
    for key in ("pastTenseMessage", "invocationMessage"):
        msg = item.get(key)
        txt = _extract_text(msg)
        if txt:
            return txt
    return ""


def _collect_keyed_strings(obj: Any, target_keys: set[str]) -> list[str]:
    """指定キーにぶら下がる文字列値を再帰収集する。"""
    found: list[str] = []

    def _walk(value: Any) -> None:
        if isinstance(value, dict):
            for k, v in value.items():
                key = str(k).lower()
                if key in target_keys and isinstance(v, str) and v.strip():
                    found.append(v.strip())
                _walk(v)
        elif isinstance(value, list):
            for item in value:
                _walk(item)

    _walk(obj)
    return found


def _classify_session_type(state: dict[str, Any], requests: list[dict[str, Any]]) -> tuple[str, str]:
    """
    セッション種別を判定する。
    優先順: provider/sessionType -> mode -> model。
    """
    tokens: list[str] = []

    def _add(value: Any) -> None:
        if isinstance(value, str) and value.strip():
            tokens.append(value.strip().lower())

    # 1) provider/sessionType 系 (最優先)
    for path in (
        ["sessionType"],
        ["providerType"],
        ["provider"],
        ["providerId"],
        ["chatProvider"],
        ["agentProvider"],
    ):
        _add(_safe_get(state, path))

    keyed = _collect_keyed_strings(
        state,
        {
            "sessiontype",
            "providertype",
            "provider",
            "providerid",
            "chatprovider",
            "agentprovider",
            "extensionid",
        },
    )
    for v in keyed:
        _add(v)

    provider_joined = " ".join(tokens)
    if "openai.chatgpt" in provider_joined or "codex" in provider_joined:
        return "codex", "provider"

    # 2) mode 系
    mode_tokens: list[str] = []
    for path in (
        ["inputState", "mode", "id"],
        ["inputState", "mode", "kind"],
        ["mode", "id"],
        ["mode", "kind"],
    ):
        v = _safe_get(state, path)
        if isinstance(v, str) and v.strip():
            mode_tokens.append(v.strip().lower())

    mode_joined = " ".join(mode_tokens)
    if "codex" in mode_joined:
        return "codex", "mode"

    # 3) model 系 (フォールバック)
    model_tokens: list[str] = []
    for path in (
        ["selectedModel", "id"],
        ["selectedModel", "name"],
        ["selectedModel", "metadata", "family"],
        ["selectedModel", "metadata", "model"],
    ):
        v = _safe_get(state, path)
        if isinstance(v, str) and v.strip():
            model_tokens.append(v.strip().lower())

    for req in requests:
        if not isinstance(req, dict):
            continue
        rid = req.get("modelId")
        if isinstance(rid, str) and rid.strip():
            model_tokens.append(rid.strip().lower())
        result_model_id = _safe_get(req, ["result", "metadata", "modelId"])
        if isinstance(result_model_id, str) and result_model_id.strip():
            model_tokens.append(result_model_id.strip().lower())

    model_joined = " ".join(model_tokens)
    if "codex" in model_joined:
        return "codex", "model"

    return "chat", "default"


def _request_response_to_text(response: Any) -> str:
    if isinstance(response, str):
        return response.strip()

    if not isinstance(response, list):
        return _extract_text(response)

    chunks: list[str] = []
    for item in response:
        if not isinstance(item, dict):
            txt = _extract_text(item)
            if txt:
                chunks.append(txt)
            continue

        kind = item.get("kind")
        if kind == "thinking":
            continue
        if kind == "toolInvocationSerialized":
            tool_msg = _extract_tool_message(item)
            if tool_msg:
                chunks.append(f"[TOOL] {tool_msg}")
            continue

        txt = _extract_text(item.get("value"))
        if txt:
            chunks.append(txt)

    return "\n\n".join([c for c in chunks if c]).strip()


def _to_iso_from_ms(ts: Any) -> str:
    if not isinstance(ts, (int, float)):
        return ""
    try:
        return datetime.fromtimestamp(ts / 1000, tz=timezone.utc).isoformat().replace("+00:00", "Z")
    except (OverflowError, ValueError):
        return ""


def _ensure_container(parent: Any, key: Any) -> Any:
    if isinstance(key, int):
        if not isinstance(parent, list):
            return None
        while len(parent) <= key:
            parent.append({})
        return parent[key]
    if not isinstance(parent, dict):
        return None
    if key not in parent:
        parent[key] = {}
    return parent[key]


def _set_path(state: dict[str, Any], path: list[Any], value: Any, kind: int) -> None:
    if not path:
        return

    cur: Any = state
    for i, key in enumerate(path[:-1]):
        next_key = path[i + 1]
        if isinstance(key, int):
            if not isinstance(cur, list):
                return
            while len(cur) <= key:
                cur.append([] if isinstance(next_key, int) else {})
            if cur[key] is None:
                cur[key] = [] if isinstance(next_key, int) else {}
            cur = cur[key]
        else:
            if not isinstance(cur, dict):
                return
            if key not in cur or cur[key] is None:
                cur[key] = [] if isinstance(next_key, int) else {}
            cur = cur[key]

    leaf = path[-1]
    if isinstance(leaf, int):
        if not isinstance(cur, list):
            return
        while len(cur) <= leaf:
            cur.append(None)
        cur[leaf] = value
        return

    if not isinstance(cur, dict):
        return

    # kind=2 は配列への追記差分になるケースがある
    if kind == 2 and isinstance(cur.get(leaf), list) and isinstance(value, list):
        cur[leaf].extend(value)
    else:
        cur[leaf] = value


def parse_chat_session_jsonl(file_path: Path, workspace_id: str) -> dict | None:
    state: dict[str, Any] = {}

    try:
        raw = file_path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None

    for line in raw.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            ev = json.loads(line)
        except json.JSONDecodeError:
            continue

        kind = ev.get("kind")
        if kind == 0 and isinstance(ev, dict):
            base = ev.get("v")
            if isinstance(base, dict):
                state = base.copy()
            else:
                state = ev.copy()
            continue

        if kind in (1, 2):
            path = ev.get("k")
            value = ev.get("v")
            if isinstance(path, list):
                _set_path(state, path, value, kind)

    session_id = str(state.get("sessionId") or file_path.stem)
    creation = state.get("creationDate")
    if isinstance(creation, (int, float)):
        start_time = _to_iso_from_ms(creation) or str(creation)
    else:
        start_time = str(creation or "")

    mode_id = str(_safe_get(state, ["inputState", "mode", "id"]) or "")
    model_family = str(_safe_get(state, ["selectedModel", "metadata", "family"]) or "")
    title = str(state.get("customTitle") or "").strip()

    requests = state.get("requests")
    if not isinstance(requests, list):
        requests = []

    turns: list[dict[str, str]] = []
    for req in requests:
        if not isinstance(req, dict):
            continue

        req_ts = _to_iso_from_ms(req.get("timestamp"))
        user_text = _extract_text(req.get("message"))
        if user_text:
            turns.append({"role": "user", "content": user_text, "ts": req_ts})

        assistant_text = _request_response_to_text(req.get("response"))
        if assistant_text:
            turns.append({"role": "assistant", "content": assistant_text, "ts": req_ts})

    if not title:
        first_user = next((t for t in turns if t["role"] == "user"), None)
        title = _derive_title(first_user["content"]) if first_user else session_id

    # CHAT/CODEX 判定
    session_type, type_source = _classify_session_type(state, requests)

    return {
        "session_id": session_id,
        "start_time": start_time,
        "title": title,
        "turns": turns,
        "workspace_id": workspace_id,
        "file": file_path,
        "mode": mode_id,
        "model_family": model_family,
        "type": session_type,
        "type_source": type_source,
        "has_chat_session": True,
    }


# --------------------------------------------------------------------------- #
# セッション一覧取得
# --------------------------------------------------------------------------- #

def find_transcript_dirs(
    workspace_storage_dir: Path,
    workspace_id: str | None = None,
) -> list[tuple[str, Path]]:
    """workspaceStorage 配下から Copilot transcripts ディレクトリを見つける。"""
    found: list[tuple[str, Path]] = []

    if workspace_id:
        target = workspace_storage_dir / workspace_id / "GitHub.copilot-chat" / "transcripts"
        if target.exists():
            return [(workspace_id, target)]
        return []

    if not workspace_storage_dir.exists():
        return []

    for entry in workspace_storage_dir.iterdir():
        if not entry.is_dir():
            continue
        transcripts = entry / "GitHub.copilot-chat" / "transcripts"
        if transcripts.exists():
            found.append((entry.name, transcripts))
    return found


def find_chat_session_dirs(
    workspace_storage_dir: Path,
    workspace_id: str | None = None,
) -> list[tuple[str, Path]]:
    found: list[tuple[str, Path]] = []

    if workspace_id:
        target = workspace_storage_dir / workspace_id / "chatSessions"
        if target.exists():
            return [(workspace_id, target)]
        return []

    if not workspace_storage_dir.exists():
        return []

    for entry in workspace_storage_dir.iterdir():
        if not entry.is_dir():
            continue
        chat_sessions = entry / "chatSessions"
        if chat_sessions.exists():
            found.append((entry.name, chat_sessions))
    return found


def load_transcript_sessions(transcript_dirs: list[tuple[str, Path]]) -> list[dict]:
    sessions: list[dict] = []
    for ws_id, transcripts_dir in transcript_dirs:
        for jsonl_file in transcripts_dir.glob("*.jsonl"):
            s = parse_jsonl(jsonl_file, workspace_id=ws_id)
            if s:
                s["has_transcript"] = True
                s["has_chat_session"] = False
                s["type"] = "chat"
                sessions.append(s)

    return sessions


def load_chat_sessions(chat_session_dirs: list[tuple[str, Path]]) -> list[dict]:
    sessions: list[dict] = []
    for ws_id, chat_dir in chat_session_dirs:
        for jsonl_file in chat_dir.glob("*.jsonl"):
            s = parse_chat_session_jsonl(jsonl_file, workspace_id=ws_id)
            if s:
                s["has_transcript"] = False
                sessions.append(s)

    return sessions


def _sort_sessions_desc(sessions: list[dict]) -> None:

    # 新しい順にソート
    def _sort_key(s):
        t = s["start_time"]
        if not t:
            return datetime.min.replace(tzinfo=timezone.utc)
        try:
            return datetime.fromisoformat(t.replace("Z", "+00:00"))
        except ValueError:
            return datetime.min.replace(tzinfo=timezone.utc)

    sessions.sort(key=_sort_key, reverse=True)


def merge_sessions(chat_sessions: list[dict], transcript_sessions: list[dict]) -> list[dict]:
    merged: dict[str, dict] = {}

    for s in transcript_sessions:
        merged[s["session_id"]] = dict(s)

    for cs in chat_sessions:
        sid = cs["session_id"]
        if sid not in merged:
            merged[sid] = dict(cs)
            continue

        base = merged[sid]
        base["has_chat_session"] = True

        # chatSessions 側のメタを優先
        if cs.get("start_time"):
            base["start_time"] = cs["start_time"]
        if cs.get("title"):
            base["title"] = cs["title"]
        if cs.get("workspace_id"):
            base["workspace_id"] = cs["workspace_id"]
        if cs.get("mode"):
            base["mode"] = cs["mode"]
        if cs.get("model_family"):
            base["model_family"] = cs["model_family"]
        if cs.get("type"):
            base["type"] = cs["type"]

        # 本文は chatSessions を優先（空なら transcripts 維持）
        if cs.get("turns"):
            base["turns"] = cs["turns"]

    sessions = list(merged.values())
    _sort_sessions_desc(sessions)
    return sessions


# --------------------------------------------------------------------------- #
# Markdown 生成
# --------------------------------------------------------------------------- #

def _fmt_dt(iso: str) -> str:
    if not iso:
        return "不明"
    try:
        dt = datetime.fromisoformat(iso.replace("Z", "+00:00"))
        # ローカル表示（JST 固定）
        local = dt.astimezone()
        return local.strftime("%Y-%m-%d %H:%M:%S")
    except ValueError:
        return iso


def generate_markdown(sessions: list[dict]) -> str:
    now = datetime.now().strftime("%Y-%m-%d")
    lines = [
        "# Copilot Chat Sessions Export",
        "",
        f"> 生成日: {now}  ",
        f"> セッション数: {len(sessions)}",
        "",
        "---",
        "",
        "## 目次",
        "",
    ]

    for i, s in enumerate(sessions, 1):
        anchor = f"session-{i}"
        date_str = _fmt_dt(s["start_time"])
        lines.append(f"{i}. [{s['title']}](#{anchor}) — *{date_str}*")

    lines += ["", "---", ""]

    for i, s in enumerate(sessions, 1):
        anchor = f"session-{i}"
        date_str = _fmt_dt(s["start_time"])
        lines += [
            f'<a id="{anchor}"></a>',
            "",
            f"## Session {i}: {s['title']}",
            "",
            f"**Date:** {date_str}  ",
            f"**Session ID:** `{s['session_id']}`  ",
            f"**ターン数:** {len([t for t in s['turns'] if t['role'] == 'user'])}",
            "",
        ]

        for turn in s["turns"]:
            if turn["role"] == "user":
                lines += [
                    "### User",
                    "",
                    turn["content"],
                    "",
                ]
            else:
                lines += [
                    "### Assistant",
                    "",
                    turn["content"],
                    "",
                ]

        lines += ["---", ""]

    return "\n".join(lines)


# --------------------------------------------------------------------------- #
# エントリポイント
# --------------------------------------------------------------------------- #

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Copilot チャットセッションを Markdown に書き出す"
    )
    parser.add_argument(
        "--transcripts-dir",
        type=Path,
        default=None,
        help="transcripts ディレクトリのパス（指定時はこのディレクトリのみ対象）",
    )
    parser.add_argument(
        "--workspace-id",
        type=str,
        default=None,
        help="workspaceStorage の特定 workspace id に限定する",
    )
    parser.add_argument(
        "--type",
        type=str,
        choices=["all", "chat", "codex"],
        default="all",
        help="セッション種別で絞り込む（all/chat/codex）",
    )
    parser.add_argument(
        "--recent",
        type=int,
        default=None,
        help="新しい順に先頭 N 件だけ対象にする",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=None,
        help="出力ファイルパス（省略時は自動命名）",
    )
    parser.add_argument(
        "--latest",
        action="store_true",
        help="最新1件だけ出力する",
    )
    parser.add_argument(
        "--session",
        type=str,
        default=None,
        help="特定のセッション ID だけ出力する",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="セッション一覧を表示するだけ（ファイルは生成しない）",
    )
    args = parser.parse_args()

    if args.transcripts_dir:
        if not args.transcripts_dir.exists():
            print(
                f"[ERROR] transcripts ディレクトリが見つかりません: {args.transcripts_dir}",
                file=sys.stderr,
            )
            sys.exit(1)
        transcript_dirs = [("manual", args.transcripts_dir)]
        chat_session_dirs: list[tuple[str, Path]] = []
        print(f"[INFO] 読み込み中: {args.transcripts_dir}")
    else:
        transcript_dirs = find_transcript_dirs(
            DEFAULT_WORKSPACE_STORAGE_DIR,
            workspace_id=args.workspace_id,
        )
        chat_session_dirs = find_chat_session_dirs(
            DEFAULT_WORKSPACE_STORAGE_DIR,
            workspace_id=args.workspace_id,
        )
        if not transcript_dirs and not chat_session_dirs:
            print(
                "[ERROR] transcripts / chatSessions が見つかりませんでした。"
                f" 探索先: {DEFAULT_WORKSPACE_STORAGE_DIR}",
                file=sys.stderr,
            )
            sys.exit(1)
        print(
            f"[INFO] 読み込み対象: transcripts={len(transcript_dirs)},"
            f" chatSessions={len(chat_session_dirs)}"
            f" (探索先: {DEFAULT_WORKSPACE_STORAGE_DIR})"
        )

    transcript_sessions = load_transcript_sessions(transcript_dirs)
    chat_sessions = load_chat_sessions(chat_session_dirs)
    sessions = merge_sessions(chat_sessions, transcript_sessions)

    if args.type != "all":
        sessions = [s for s in sessions if s.get("type", "chat") == args.type]

    if args.recent is not None:
        if args.recent <= 0:
            print("[ERROR] --recent は 1 以上を指定してください。", file=sys.stderr)
            sys.exit(1)
        sessions = sessions[: args.recent]

    if not sessions:
        print("[INFO] セッションが見つかりませんでした。")
        return

    # --list モード
    if args.list:
        print(f"\n{'#':>2}  {'Date':<19}  {'Type':<6}  {'Workspace':<14}  {'Session ID':<36}  Title")
        print("-" * 140)
        for i, s in enumerate(sessions, 1):
            ws = str(s.get("workspace_id") or "")[:14]
            st = str(s.get("type") or "chat")
            print(
                f"{i:>2}  {_fmt_dt(s['start_time']):<19}  {st:<6}  {ws:<14}"
                f"  {s['session_id']:<36}  {s['title'][:40]}"
            )
        return

    # フィルタ
    if args.session:
        sessions = [s for s in sessions if s["session_id"] == args.session]
        if not sessions:
            print(f"[ERROR] セッション ID '{args.session}' が見つかりませんでした。", file=sys.stderr)
            sys.exit(1)
    elif args.latest:
        sessions = sessions[:1]

    # 出力先
    out_path: Path
    if args.out:
        out_path = args.out
    else:
        date_tag = datetime.now().strftime("%Y-%m-%d")
        if args.session:
            out_path = DEFAULT_OUT_DIR / f"copilot-session-{args.session[:8]}-{date_tag}.md"
        elif args.latest:
            out_path = DEFAULT_OUT_DIR / f"copilot-session-latest-{date_tag}.md"
        else:
            out_path = DEFAULT_OUT_DIR / f"copilot-sessions-{date_tag}.md"

    out_path.parent.mkdir(parents=True, exist_ok=True)
    markdown = generate_markdown(sessions)
    out_path.write_text(markdown, encoding="utf-8")
    print(f"[OK] 保存しました: {out_path}")
    print(f"     セッション数: {len(sessions)}")


if __name__ == "__main__":
    main()
