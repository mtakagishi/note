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


def load_sessions(transcript_dirs: list[tuple[str, Path]]) -> list[dict]:
    sessions = []
    for ws_id, transcripts_dir in transcript_dirs:
        for jsonl_file in transcripts_dir.glob("*.jsonl"):
            s = parse_jsonl(jsonl_file, workspace_id=ws_id)
            if s:
                sessions.append(s)

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
        print(f"[INFO] 読み込み中: {args.transcripts_dir}")
    else:
        transcript_dirs = find_transcript_dirs(
            DEFAULT_WORKSPACE_STORAGE_DIR,
            workspace_id=args.workspace_id,
        )
        if not transcript_dirs:
            print(
                "[ERROR] transcripts が見つかりませんでした。"
                f" 探索先: {DEFAULT_WORKSPACE_STORAGE_DIR}",
                file=sys.stderr,
            )
            sys.exit(1)
        print(
            f"[INFO] 読み込み対象: {len(transcript_dirs)} ディレクトリ"
            f" (探索先: {DEFAULT_WORKSPACE_STORAGE_DIR})"
        )

    sessions = load_sessions(transcript_dirs)

    if not sessions:
        print("[INFO] セッションが見つかりませんでした。")
        return

    # --list モード
    if args.list:
        print(f"\n{'#':>2}  {'Date':<22}  {'Session ID':<38}  Title")
        print("-" * 100)
        for i, s in enumerate(sessions, 1):
            print(f"{i:>2}  {_fmt_dt(s['start_time']):<22}  {s['session_id']:<38}  {s['title'][:40]}")
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
