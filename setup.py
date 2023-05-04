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
        # languages = ['ja', 'en', 'zh', 'es', 'fr', 'hi']
        languages = ['ja']
        buildername = "html"
        sourcedir = "docs"
        outputdir = "docs/_build/html"
        for lang in languages:
            subprocess.call(["sphinx-build", "-b", buildername,
                            sourcedir, outputdir + "/"+lang+"/", "-D", "language="+lang])


class GettextCommand(SimpleCommand):
    def run(self):
        os.chdir('docs')
        # languages = ['ja', 'en', 'zh', 'es', 'fr', 'hi']
        languages = ['ja']
        buildername = "gettext"
        sourcedir = "."
        outputdir = "_build/gettext"
        subprocess.call(
            ["sphinx-build", "-b", buildername, sourcedir, outputdir])
        for lang in languages:
            subprocess.call(["sphinx-intl", "update", "-p",
                            outputdir, "-l", lang])


setup(
    cmdclass={
        "doc": DocCommand,
        "gettext": GettextCommand,
    },
)
