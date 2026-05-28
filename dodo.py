import filecmp
import os
import shutil
import subprocess
import time
from pathlib import Path

LANGUAGES = ["ja", "en"]

buildername = "html"
sourcedir = "docs"
output_base = "docs/_build/html"
doctree_base = "docs/_build/doctrees"


def build_lang(lang):
    lang_output = f"{output_base}/{lang}"
    lang_doctree = f"{doctree_base}_{lang}"
    args = [
        "sphinx-build",
        "-b",
        buildername,
        "-d",
        lang_doctree,
        sourcedir,
        lang_output,
        "-D",
        f"language={lang}",
    ]
    print(f"[INFO] ビルド開始: {lang}")
    subprocess.run(args, check=True)
    print(f"[INFO] ビルド完了: {lang}")


def copy_if_different(src, dst):
    if not os.path.exists(src):
        return
    if not os.path.exists(dst) or not filecmp.cmp(src, dst, shallow=False):
        shutil.copy(src, dst)
        print(f"[COPY] {src} → {dst}")


def task_doc():
    """多言語Sphinxビルド + staticファイルコピー"""

    def run():
        start = time.time()
        for lang in LANGUAGES:
            build_lang(lang)

        files_to_copy = ["index.html", "robots.txt", "ads.txt", "style.css", "cmp.js"]
        for file in files_to_copy:
            copy_if_different(f"static/{file}", f"{output_base}/{file}")

        # sitemap copy
        sitemap_src = f"{output_base}/ja/sitemap.xml"
        sitemap_dst = f"{output_base}/sitemap.xml"
        copy_if_different(sitemap_src, sitemap_dst)

        print(f"✨ 全ビルド完了。所要時間: {time.time() - start:.2f} 秒")

    return {"actions": [run], "verbosity": 2}


def task_gettext():
    """gettext + sphinx-intl"""

    def run():
        subprocess.run(
            ["sphinx-build", "-b", "gettext", ".", "_build/_intl/gettext"],
            check=True,
            cwd="docs",
        )
        for lang in LANGUAGES:
            subprocess.run(
                ["sphinx-intl", "update", "-p", "_build/_intl/gettext", "-l", lang],
                check=True,
                cwd="docs",
            )

    return {"actions": [run], "verbosity": 2}


def _unquote_po_line(line):
    line = line.strip()
    if not (line.startswith('"') and line.endswith('"')):
        return ""
    body = line[1:-1]
    return body.replace(r"\\n", "\n").replace(r'\\"', '"').replace(r"\\\\", "\\")


def _parse_po_entries(text):
    entries = []
    comments = []
    msgid_parts = []
    msgstr_parts = []
    mode = None

    def flush_entry():
        nonlocal comments, msgid_parts, msgstr_parts, mode
        if not msgid_parts and not msgstr_parts:
            comments = []
            mode = None
            return
        msgid = "".join(msgid_parts)
        msgstr = "".join(msgstr_parts)
        entries.append(
            {
                "msgid": msgid,
                "msgstr": msgstr,
                "fuzzy": any("fuzzy" in c for c in comments),
            }
        )
        comments = []
        msgid_parts = []
        msgstr_parts = []
        mode = None

    for raw in text.splitlines() + [""]:
        line = raw.rstrip("\n")
        if not line.strip():
            flush_entry()
            continue

        if line.startswith("#"):
            # 空行なしで連続するpoでも、次エントリのコメントで区切る。
            if (msgid_parts or msgstr_parts) and mode == "msgstr":
                flush_entry()
            comments.append(line.lower())
            continue

        if line.startswith("msgid "):
            # 行間なしのmsgid開始に備えて前エントリを確定する。
            if msgid_parts or msgstr_parts:
                flush_entry()
            mode = "msgid"
            msgid_parts = [_unquote_po_line(line[6:])]
            continue

        if line.startswith("msgstr "):
            mode = "msgstr"
            msgstr_parts = [_unquote_po_line(line[7:])]
            continue

        if line.startswith('"'):
            if mode == "msgid":
                msgid_parts.append(_unquote_po_line(line))
            elif mode == "msgstr":
                msgstr_parts.append(_unquote_po_line(line))

    return entries


def task_intl_validate():
    """英語poファイルの未翻訳・fuzzy状態をレポートする"""

    def run():
        base = Path("docs/locale/en/LC_MESSAGES")
        report_path = Path("docs/_build/_intl/validation-report.md")
        report_path.parent.mkdir(parents=True, exist_ok=True)

        if not base.exists():
            report_path.write_text("# Translation Validation Report\n\n対象ディレクトリがありません。\n", encoding="utf-8")
            print("[WARN] docs/locale/en/LC_MESSAGES が存在しません")
            return

        rows = []
        totals = {"total": 0, "untranslated": 0, "fuzzy": 0, "same": 0}

        def priority_score(untranslated, fuzzy, same, total):
            # 未翻訳を最優先、次にfuzzy、最後に同一文を重み付け。
            density = (untranslated + fuzzy + same) / total if total > 0 else 0
            return untranslated * 100 + fuzzy * 40 + same * 10 + int(density * 100)

        def priority_label(score):
            if score >= 150:
                return "high"
            if score >= 40:
                return "medium"
            if score > 0:
                return "low"
            return "ok"

        for po in sorted(base.rglob("*.po")):
            text = po.read_text(encoding="utf-8", errors="replace")
            entries = _parse_po_entries(text)
            normal_entries = [e for e in entries if e["msgid"] != ""]
            total = len(normal_entries)
            untranslated = sum(1 for e in normal_entries if e["msgstr"].strip() == "")
            fuzzy = sum(1 for e in normal_entries if e["fuzzy"])
            same = sum(1 for e in normal_entries if e["msgstr"].strip() == e["msgid"].strip() and e["msgstr"].strip() != "")

            totals["total"] += total
            totals["untranslated"] += untranslated
            totals["fuzzy"] += fuzzy
            totals["same"] += same

            score = priority_score(untranslated, fuzzy, same, total)
            label = priority_label(score)
            rows.append((po.as_posix(), total, untranslated, fuzzy, same, score, label))

        rows.sort(key=lambda r: r[5], reverse=True)

        lines = [
            "# Translation Validation Report",
            "",
            f"- Total entries: {totals['total']}",
            f"- Untranslated: {totals['untranslated']}",
            f"- Fuzzy: {totals['fuzzy']}",
            f"- Same as msgid: {totals['same']}",
            "",
            "| File | Total | Untranslated | Fuzzy | Same as msgid | Priority score | Priority |",
            "| --- | ---: | ---: | ---: | ---: | ---: | --- |",
        ]

        for row in rows:
            lines.append(
                f"| {row[0]} | {row[1]} | {row[2]} | {row[3]} | {row[4]} | {row[5]} | {row[6]} |"
            )

        report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        print(f"[INFO] 翻訳検証レポートを出力しました: {report_path}")

    return {"actions": [run], "verbosity": 2}
