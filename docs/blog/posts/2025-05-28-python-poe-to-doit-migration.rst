.. post:: 2025-05-28
   :tags: Python, Poetry, doit, pre-commit, タスク管理, 開発環境
   :category: Python開発環境
   :author: mtakagishi
   :language: ja

Python開発環境での poethepoet → doit への移行とベストプラクティス
======================================================================

Poetry を使った Python プロジェクトで、これまで `poethepoet` を使ってタスク管理をしていたが、以下の理由から `doit` への移行を行った。

- より柔軟な依存関係管理とカスタマイズが可能
- 複数タスクの依存や並列実行への対応が容易
- Sphinx 多言語ビルドや静的ファイルコピーなどを整理したかった
- `setup.py` に書いていたカスタムコマンドを `dodo.py` に統合したかった

.. contents::
    :local:
    :depth: 2

背景と現状
----------

従来の構成では以下のような形でタスクを管理していた：

- `poetry run poe doc` → `python setup.py doc`
- `poetry run poe gettext` → `python setup.py gettext`
- `setup.py` に `doc` / `gettext` コマンドクラスを定義
- pyproject.toml の `[tool.poe.tasks]` でラップ

この構成は、ある程度うまく動作していたが、次のような課題もあった：

- `setup.py` に依存してしまう点（非推奨方向）
- タスクの柔軟な定義（ファイル依存・再実行判定）には限界
- `pre-commit` の導入との併用が中途半端

doit への移行ステップ
----------------------

1. まず `doit` を開発依存として追加：

   .. code-block:: bash

      poetry add -D doit

2. プロジェクトルートに `dodo.py` を作成し、以下のようにタスクを定義：

   .. code-block:: python

      from doit import create_after
      import subprocess, shutil, os, time, filecmp

      LANGUAGES = ['ja', 'en']
      def task_doc():
          def run():
              for lang in LANGUAGES:
                  subprocess.run([
                      "sphinx-build", "-b", "html", "-D", f"language={lang}",
                      "docs", f"docs/_build/html/{lang}", "-d", f"docs/_build/doctrees_{lang}"
                  ], check=True)
              shutil.copy("static/index.html", "docs/_build/html/index.html")
          return {'actions': [run]}

3. 動作確認：

   .. code-block:: bash

      poetry run doit list
      poetry run doit doc

4. 問題なければ `poe` を削除：

   .. code-block:: bash

      poetry remove poe

   併せて `[tool.poe.tasks]` セクションも `pyproject.toml` から削除。

5. `.doit.db.db` は Git 管理対象外とするため、`.gitignore` に以下を追加：

   .. code-block:: text

      .doit.db.db

pre-commit の併用
------------------

コードフォーマットや静的解析は `pre-commit` で行うように変更。

.. code-block:: yaml

   repos:
     - repo: https://github.com/psf/black
       rev: 25.1.0
       hooks:
         - id: black
     - repo: https://github.com/pre-commit/mirrors-isort
       rev: v5.10.1
       hooks:
         - id: isort
     - repo: https://github.com/PyCQA/flake8
       rev: 7.2.0
       hooks:
         - id: flake8

利点まとめ
----------

- `doit` は Python ベースで拡張性が高く、再実行判定も優秀
- `setup.py` を廃止し、 `pyproject.toml` 中心の構成へ整理できた
- `pre-commit` によってコミット前のチェックも統一的に管理
- タスクの実行結果キャッシュも `.doit.db.db` により最適化

.. rubric:: 記事情報

:著者: mtakagishi
:投稿日: 2025-05-28
