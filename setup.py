import os
import subprocess
from setuptools import setup, Command
import shutil
import time
import filecmp

LANGUAGES = ['ja', 'en']  # 'ja', 'en', 'zh', 'es', 'fr', 'hi'

buildername = "html"
sourcedir = "docs"
output_base = "docs/_build/html"
doctree_base = "docs/_build/doctrees"

def build_lang(lang):
    lang_output = f"{output_base}/{lang}"
    lang_doctree = f"{doctree_base}_{lang}"
    args = [
        "sphinx-build",
        "-b", buildername,
        "-d", lang_doctree,
        sourcedir,
        lang_output,
        "-D", f"language={lang}"
    ]
    print(f"[INFO] ビルド開始: {lang}")
    subprocess.run(args, check=True)
    print(f"[INFO] ビルド完了: {lang}")


class SimpleCommand(Command):
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass


class DocCommand(SimpleCommand):
    def run(self):
        start_time = time.time()

        for lang in LANGUAGES:
            build_lang(lang)

        def copy_if_different(src, dst):
            if not os.path.exists(src):
                return
            if not os.path.exists(dst) or not filecmp.cmp(src, dst, shallow=False):
                shutil.copy(src, dst)
                print(f"[COPY] {src} → {dst}")

        files_to_copy = [
            "index.html",
            "robots.txt",
            "ads.txt",
            "style.css",
            "cmp.js",
        ]
        for file_path in files_to_copy:
            src_path = f"static/{file_path}"
            dst_path = f"{output_base}/{file_path}"
            copy_if_different(src_path, dst_path)

        sitemap_src = f"{output_base}/ja/sitemap.xml"
        sitemap_dst = f"{output_base}/sitemap.xml"
        copy_if_different(sitemap_src, sitemap_dst)

        elapsed = time.time() - start_time
        print(f"✨ 全ビルド完了。所要時間: {elapsed:.2f} 秒")


class GettextCommand(SimpleCommand):
    def run(self):
        os.chdir('docs')  # カレントディレクトリが重要
        buildername = "gettext"
        sourcedir = "."
        outputdir = "_build/_intl/gettext"

        # .pot生成
        subprocess.call(
            ["sphinx-build", "-b", buildername, sourcedir, outputdir])
        # .po抽出
        for lang in LANGUAGES:
            args = ["sphinx-intl", "update", "-p",
                    outputdir, "-l", lang]
            subprocess.call(args)


setup(
    cmdclass={
        "doc": DocCommand,
        "gettext": GettextCommand,
    },
)
