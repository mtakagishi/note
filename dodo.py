import filecmp
import os
import shutil
import subprocess
import time

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
        os.chdir("docs")
        subprocess.run(
            ["sphinx-build", "-b", "gettext", ".", "_build/_intl/gettext"], check=True
        )
        for lang in LANGUAGES:
            subprocess.run(
                ["sphinx-intl", "update", "-p", "_build/_intl/gettext", "-l", lang],
                check=True,
            )

    return {"actions": [run], "verbosity": 2}
