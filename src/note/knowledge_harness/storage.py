"""Knowledge Harnessのローカル成果物を安全に保存する共通処理。"""

from __future__ import annotations

import json
import re
import tempfile
from pathlib import Path
from typing import Any

RUN_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")


def validate_run_id(run_id: str) -> None:
    """run_idがディレクトリ名として安全であることを確認する。"""

    if not RUN_ID_PATTERN.fullmatch(run_id):
        raise ValueError("run_idは英数字で始まる128文字以内の英数字・._-にしてください")


def json_text(data: Any) -> str:
    """成果物用の安定したJSON文字列を返す。"""

    return json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def write_if_changed(path: Path, content: str) -> bool:
    """内容が変わる場合だけ、一時ファイルから原子的に置き換える。"""

    if path.exists() and path.read_text(encoding="utf-8") == content:
        return False

    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        "w", encoding="utf-8", newline="\n", dir=path.parent, delete=False
    ) as temporary:
        temporary.write(content)
        temporary_path = Path(temporary.name)
    temporary_path.replace(path)
    return True


def read_created_at(path: Path) -> str | None:
    """既存成果物に有効なcreated_atがあれば返す。"""

    if not path.exists():
        return None
    try:
        value = json.loads(path.read_text(encoding="utf-8")).get("created_at")
    except (OSError, json.JSONDecodeError, AttributeError):
        return None
    return value if isinstance(value, str) and value else None
