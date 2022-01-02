********************************
Sphinx
********************************
Last Updated on 2021-08-22

Sphinx初期整備
==============================
Sphinxパッケージ追加::

	poetry add --dev sphinx

Sphinx初期化する。フォルダターゲットはdocsとした::

	portry run sphinx-quickstart docs

docsが初期化されているのでビルドしてみる。

	poetry run sphinx-build docs docs/_build/ja

docs/_build/ja/index.html [#i18n]_ を開くとビルド結果を確認できる

sphinx-autobuildによる効率化
========================================================
sphinx-autobuildを利用すると、ビルドとブラウザ確認を効率化できます

sphinx-autobuild追加::

	poetry add --dev sphinx-autobuild

以降、下記コマンドを一度実行すれば、http://127.0.0.1:8000 でページ確認でき、自動ビルド・自動リロードされる。

	poerty run sphinx-autobuild docs docs/_build/ja

sphinx-autobuild起動の効率化
======================================
起動効率化の方針
------------------------
sphinx-autobuildの存在だけでもとても効率的なのだが『poetry add sphinx-autobuild』を打ち込むのは面倒。そこで `2019年に向けてPythonのモダンな開発環境について考える`_ という記事を参考に下記コマンドで実行する効率化を目指す::

	poetry run doc //NG

結論としてはこのコマンドでの実現はムリだった。poetryで指定できる[tool.poetry.scripts]は引数指定ができない。この仕様は変更予定はなく、今後もメインストリームに組み込まれる予定はないし、プラグイン開発待ちだが時間がかかりそう [#task]_

natさんにより、 `poethepoet`_ という暫定パッケージを開発してくれているのでこれを活用する。4文字ふえるが、目指すは下記でのコマンド起動す::

	poetry run poe doc

暫定パッケージを使うことを以外は `2019年に向けてPythonのモダンな開発環境について考える`_ と同一方針。詳細はURLを参照してください。

poethepoetを追加::

	poetry add --dev poethepoet

setup.pyの整備
-------------------------

setup.pyを整備します。

.. code-block::
  :caption: setup.py
  :linenos:
  
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
            subprocess.call(["sphinx-autobuild", "docs", "docs/_build/ja"])
    
    
    setup(
        cmdclass={
            "doc": DocCommand,
        },
    )


上記setup.pyにより、下記コマンドから実行されるようになる::

	poetry run setup.py doc

pyproject.tomlの整備
-------------------------

.. code-block:: toml
	:caption: pyproject.toml
	:linenos:

	[tool.poe.tasks]
	  doc = "python setup.py doc"

ここまで整備すると、以下コマンドでsphinx-autobuildが起動するようになります::

	poetry run poe doc


テーマ
============
テーマは `pydata-sphinx-theme`_ を採用。
* conf.pyで下記対応可能

	* github、twitterへのリンク
	* navバーの設定
	* Google Analyticsの設定

* bootstrap4対応
* Pandas、NumPy、など主要パッケージで採用

pydata-sphinx-themeのインストール::

	poetry add --dev pydata-sphinx-theme

conf.pyの整備::

	html_theme = "pydata_sphinx_theme"

その他、詳細は `pydata-sphinx-theme`_ を参照


.. |date| date::

.. _2019年に向けてPythonのモダンな開発環境について考える: https://techblog.asahi-net.co.jp/entry/2018/11/19/103455

.. _poethepoet: https://github.com/nat-n
.. _pydata-sphinx-theme: https://pydata-sphinx-theme.readthedocs.io/en/latest/

.. [#i18n] jaフォルダについて。個人的にi18nを体感するためにjaフォルダとして分離した。英語版は docs/_build/en にビルドされることを想定。現実には個人ブログで多言語化は考慮不要。

.. [#task] https://github.com/python-poetry/poetry/pull/591#issuecomment-504762152
