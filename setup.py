import os
import subprocess
from setuptools import setup, Command


class SimpleCommand(Command):
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass


class DocCommand(SimpleCommand):
    def run(self):
        # subprocess.call(["sphinx-autobuild", "docs", "docs/_build/ja"])
        subprocess.call(["sphinx-autobuild", "docs", "docs/_build"])


# class DocEnglishCommand(SimpleCommand):
#     def run(self):
#         subprocess.call(["sphinx-build", "-M", "gettext", "docs", "docs/_build/ja"])
#         subprocess.call(["sphinx-intl", "update", "-d", "docs/locales",
#                          "-p", "_build/ja/gettext", "-l", "en"])
#         subprocess.call(["sphinx-autobuild", "docs",
#                          "docs/_build/en", "-D", "language=en"])


setup(
    # use_scm_version=True, poetryで使えない。
    # poetry-dynamic-versioningを検討するか諦める。
    cmdclass={
        "doc": DocCommand,
        # "doc_en": DocEnglishCommand,
    },
)
