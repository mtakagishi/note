.. post:: 2025-05-24
   :tags: Python, タスク自動化, doit, Sphinx
   :category: ツール
   :author: mtakagishi
   :language: ja

=============================================
Python製タスク自動化ツール「doit」の基本
=============================================

Pythonで書けるタスク自動化ツール「doit」について、基本的な考え方と導入方法、簡単な使用例までを整理した作業メモです。

.. contents::
   :local:
   :depth: 2

概要
====

doit は、Makefile的なタスク自動化の仕組みを、Pythonの文法で柔軟に記述できるツールです。
Sphinxのビルドや、リント・テストなどの定型作業を記述しておけば、差分検出によって必要なタスクだけを自動実行できます。

インストール
============

.. code-block:: bash

   pip install doit

または Poetry を使う場合は以下のようにインストールします。

.. code-block:: bash

   poetry add --group dev doit

最小構成のタスク定義
======================

ファイル名は ``dodo.py`` とするのが基本です。

.. code-block:: python

   def task_hello():
       return {
           'actions': ['echo "Hello, world!"'],
       }

実行は次のように行います。

.. code-block:: bash

   doit        # すべてのタスクを実行
   doit list   # タスク一覧を表示
   doit hello  # タスクhelloだけを実行

入出力ファイルを使った例
==========================

.. code-block:: python

   def task_build_docs():
       return {
           'actions': ['sphinx-build -b html docs build'],
           'file_dep': ['docs/conf.py', 'docs/index.rst'],
           'targets': ['build/index.html'],
           'clean': True,
       }

- ``file_dep``: 入力ファイル（依存ファイル）
- ``targets``: 出力ファイル（ビルド済みならスキップ可能）
- ``clean``: ``doit clean`` 実行時に削除対象に含める

Python関数によるアクション
=============================

.. code-block:: python

   def say_hello(name):
       print(f"Hello, {name}!")

   def task_greet():
       return {
           'actions': [(say_hello, ['Alice'])],
       }

よくある用途
===============

.. list-table:: よく使われるdoitの用途
   :widths: 15 85
   :header-rows: 1

   * - 用途
     - 内容
   * - ドキュメント
     - SphinxやMkDocsのビルド
   * - テスト
     - pytestやunittestなどの実行
   * - リント
     - flake8, black, mypyなど
   * - 複数ステップ
     - ステップ間の依存関係も記述可能
   * - 自動監視
     - ``doit auto`` でファイルの変更を監視

補足
====

プロジェクトが大きくなった場合、 ``tasks`` ディレクトリにタスクを分割して記述し、 ``dodo.py`` からインポートすることもできます。

まとめ
======

Pythonで定義でき、柔軟で再利用性の高いタスク自動化が可能になるdoitは、小規模〜中規模のプロジェクトでの効率化に非常に便利です。今後は、PoetryやSphinx、CIツールなどと連携させた構成についても検討していく予定です。
