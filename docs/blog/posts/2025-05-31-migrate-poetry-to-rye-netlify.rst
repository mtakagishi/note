.. post:: 2025-05-31
   :tags: Python, Rye, Poetry, Netlify, Pre-commit
   :category: 開発環境
   :author: mtakagishi
   :language: ja

PoetryからRyeへの移行と、Netlifyビルドの完全対応
====================================================

Poetryで管理していたPythonプロジェクトを、最近注目されているRyeに移行し、
さらにNetlifyでのデプロイまでを通して構成を整えた。この記事では、その手順と要点を記録しておく。

移行にあたり、以下のポイントを押さえて対応した：

- 既存のPoetryプロジェクトからの安全な移行
- pre-commitによるRuff設定の見直し
- RyeバイナリのNetlify上でのインストールと実行
- Pythonバージョンによる依存解決失敗の原因と対策
- pipとの切り分け（requirements.txt方式の回避）

.. contents::
   :local:
   :depth: 2

----

移行前の状態
=============

- Poetryで管理（``pyproject.toml``, ``poetry.lock`` あり）
- ``.venv/`` , ``setup.py`` , ``poetry.toml`` なども存在
- Netlifyでは、 ``requirements.txt`` と ``pip install`` によるビルド運用

----

Ryeへの移行手順
================

1. 現状をタグでバックアップ：

   .. code-block:: bash

      git tag before-rye

2. Poetry関連のファイル削除：

   .. code-block:: bash

      rm poetry.lock poetry.toml setup.py
      rm -rf .venv/

3. ``setup.py`` を一時退避して ``rye init`` ：

   .. code-block:: bash

      mv setup.py setup.py.bak
      rye init

4. 必要パッケージのインストール:

   .. code-block:: bash

      rye add sphinx pydata-sphinx-theme myst-parser

5. 開発パッケージのインストール:

   .. code-block:: bash

      rye add --dev sphinx-autobuild doc8 esbonio rstcheck pre-commit doit ruff

6. Pythonバージョンを明示：

   .. code-block:: bash

      echo "3.12.9" > .python-version

7. ``pyproject.toml`` をRye形式に手動で修正し、Ruffの設定も正規化：

   .. code-block:: toml

      [tool.ruff]
      line-length = 120
      extend-select = ["I", "C901"]

      [tool.ruff.lint.mccabe]
      max-complexity = 10

8. ``requires-python`` の条件を修正：

   .. code-block:: toml

      requires-python = ">=3.12"

----

Netlifyでの対応
================

Ryeの公式インストールスクリプトは ``curl | bash`` 形式だが、Netlifyでは ``curl -sSf https://rye.astral.sh/get | bash`` の方式でエラーとなったので、代わりにRyeバイナリをダウンロードして展開する方式を採用した。

.. code-block:: toml

   [build]
   command = """
     wget -q https://github.com/astral-sh/rye/releases/latest/download/rye-x86_64-linux.gz
     gunzip rye-x86_64-linux.gz
     chmod +x rye-x86_64-linux
     ./rye-x86_64-linux self install --yes
     . $HOME/.rye/env
     rye sync
     rye run doit doc
   """
   publish = "docs/_build/html"

   [build.environment]
   PYTHON_VERSION = "3.13"
   LANG = "ja_JP.UTF-8"
   LANGUAGE = "ja_JP:ja"
   LC_ALL = "ja_JP.UTF-8"
   TZ = "Asia/Tokyo"

----

トラブルと対策まとめ
=======================

- poetry時代の ``pyproject.toml`` が残っているとあると `rye init` が失敗する → 削除する
- ``setup.py`` があると `rye init` が失敗する → 一時退避すればOK
- ``pyproject.toml`` に ``requires-python = ">=3.8"`` があると、Ryeが3.8を使ってしまう →  ``">=3.12"`` に修正
- ``max-complexity`` の設定が間違っているとRuffでエラー → ``[tool.ruff.lint.mccabe]`` に正しく記載

----

まとめ
==========

Ryeは開発者体験が非常に良い一方で、NetlifyのようなCI環境での対応には少し工夫が必要だった。
移行はやり切れた。poetryとの違い、性能メリットを感じることもできた。今後はryeを基点にした開発にシフトしノウハウを蓄積したい。

.. rubric:: 記事情報

:著者: mtakagishi
:公開日: 2025-05-31
