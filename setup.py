import os
import subprocess
from setuptools import setup, Command
import shutil

LANGUAGES = ['ja']  # 'ja', 'en', 'zh', 'es', 'fr', 'hi'

class SimpleCommand(Command):
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass


class DocCommand(SimpleCommand):
    def run(self):
        buildername = "html"
        sourcedir = "docs"
        outputdir = "docs/_build/html"
        for lang in LANGUAGES:
            args = ["sphinx-build", "-b", buildername,
                    sourcedir, f"{outputdir}/{lang}", "-D", f"language={lang}"]
            subprocess.call(args)
        files_to_copy = [
            "index.html",
            "robots.txt",
            "ads.txt",
            "style.css",
            "cmp.js",
        ]
        # staticファイルを個別にコピー
        for file_path in files_to_copy:
            shutil.copy(f"static/{file_path}", outputdir)
        # sitemap.xmlを個別にコピー
        shutil.copy(f"{outputdir}/ja/sitemap.xml", outputdir)


class GettextCommand(SimpleCommand):
    def run(self):
        os.chdir('docs')  # カレントディレクトリが重要
        buildername = "gettext"
        sourcedir = "."
        outputdir = "_build/gettext"

        # .pot生成
        subprocess.call(
            ["sphinx-build", "-b", buildername, sourcedir, outputdir])
        # .po抽出
        for lang in LANGUAGES:
            # デフォルト言語はjaのためスキップする
            if lang == "ja":
                continue
            args = ["sphinx-intl", "update", "-p",
                    outputdir, "-l", lang]
            subprocess.call(args)


setup(
    cmdclass={
        "doc": DocCommand,
        "gettext": GettextCommand,
    },
)
