.. post:: 2025-05-16
   :tags: pre-commit, lint, formatter, CI, python, markdown
   :category: dev-environment
   :author: mtakagishi
   :language: ja

pre-commit 導入メモ
==========================================================

本記事では、Git コミット前にコードやドキュメントの整形・チェックを自動で行うツール **pre-commit** について、導入方法と活用を整理します

.. contents:
   :local:
   :depth: 2

はじめに：pre-commit とは
--------------------------

`pre-commit` は、Git の「コミット前フック」を簡単に管理・運用するための Python 製ツールです。以下のような作業を自動化できます：

- ファイル末尾の改行チェック
- Python コードの整形（Black）
- Markdown や reStructuredText の文法チェック
- YAML / JSON / TOML の構文検査
- セキュリティ的に危険なコードの検出（Bandit など）

インストールと初期設定
------------------------

まずは `pre-commit` をインストールします。仮想環境でもシステム全体でも OK です。

.. code-block:: bash

   pip install pre-commit

もしくは `pipx` 派の方は：

.. code-block:: bash

   pipx install pre-commit

次に、プロジェクトのルートに ``.pre-commit-config.yaml`` を用意します。

基本的な例：

.. code-block:: yaml

   repos:
     - repo: https://github.com/pre-commit/pre-commit-hooks
       rev: v4.5.0
       hooks:
         - id: end-of-file-fixer
         - id: trailing-whitespace

     - repo: https://github.com/psf/black
       rev: 24.3.0
       hooks:
         - id: black

     - repo: https://github.com/pycqa/flake8
       rev: 6.1.0
       hooks:
         - id: flake8

フックのインストール：

.. code-block:: bash

   pre-commit install

これで、次回の ``git commit`` 時に自動的にチェックが走るようになります。


バージョン管理と自動更新
--------------------------

すべてのフックにはバージョン（rev）が指定されており、次のコマンドで一括更新できます：

.. code-block:: bash

   pre-commit autoupdate


pre-commit によるドキュメントチェック
---------------------------------------

Markdown や reStructuredText のような軽量マークアップも pre-commit によって整備できます。

- ``doctoc``：Markdown の目次自動生成
- ``mdformat``：Markdown の自動整形（Python製）
- ``doc8``：reStructuredText のルールチェック
- ``rstcheck``：Sphinx 向けの構文検証

pre-commit で自動目次生成や API ドキュメント整形を行えば、**ドキュメントの陳腐化を防止** しつつ、**差分として明示できる** のが大きな利点です。

全てのファイルをチェックしたい場合は以下コマンドを使います:

.. code-block:: bash

   pre-commit run --all-files

pre-commitは、自動でフォーマット修正などを行うため意図せずファイル変更してしまう場合があります。その時は、以下のコマンドで直近コミットまで戻せます：

.. code-block:: bash

   git restore --source=HEAD --staged --worktree .

pre-commit の徹底
--------------------------

コミットのたびにフックが実行されることで、次のような効果があります：

- 品質維持が“自動”で担保される
- Lint/整形のルール統一が強制される
- CI で気づく前に、ローカルで問題を検出できる

チームで運用する場合には、README や CONTRIBUTING に以下を明記することで定着が進みます：

.. code-block:: bash

   pre-commit install

まとめ
--------------------------------------------

pre-commitに関する導入の基本を整理しました。
今後、網羅的な設定や、CIへの連携なども検討していきたいと思います。

.. rubric:: 記事情報

:投稿日: 2025-05-16
:著者: mtakagishi
