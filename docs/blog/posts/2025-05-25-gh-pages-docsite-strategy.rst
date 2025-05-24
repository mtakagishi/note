.. post:: 2025-05-25
   :tags: GitHub Pages, mkdocs, sphinx, netlify, static site
   :category: ドキュメント運営
   :author: mtakagishi
   :language: ja

===================================================================
gh-pagesブランチで運用するドキュメント公開とその比較知識の整理
===================================================================

GitHub Pages の gh-pages ブランチを活用したドキュメント公開の仕組みについて、学びの多かった内容を整理する。

本記事では、以下の観点をまとめる：

- GitHub Pages の仕組み
- gh-pages 運用の基本コマンドと設定
- mkdocs の自動化支援（gh-deploy）
- sphinx との連携手法（ghp-import）
- Netlifyとの比較整理

.. contents::
   :local:
   :depth: 2

GitHub Pages と gh-pages ブランチの関係
===========================================

GitHub Pages は、GitHub リポジトリの中に静的HTMLファイルを含むブランチ（通常は ``gh-pages`` ）を用意し、それをウェブ公開する仕組み。

次のようなURLで公開される：

::

   https://<ユーザー名>.github.io/<リポジトリ名>/

また、独自ドメインを使用する場合は ``CNAME`` ファイルをブランチに含めることで対応可能。

---

gh-pages 運用に必要な Git コマンド例
=========================================

Sphinx や MkDocs で生成された ``_build/html`` や ``site/`` を ``gh-pages`` ブランチに手動で反映するには、以下のようなGit操作を行う。

::

   git checkout --orphan gh-pages
   git rm -rf .
   cp -r _build/html/* .
   touch .nojekyll
   echo "example.com" > CNAME
   git add .
   git commit -m "Publish docs"
   git push origin gh-pages

- ``--orphan`` で履歴なしの新規ブランチを作成
- ``.nojekyll`` によりJekyll処理を無効化
- ``CNAME`` により独自ドメイン指定が可能

---

mkdocs gh-deploy の自動処理
=================================

MkDocs では、以下のコマンドを使うだけで上記一連の処理を自動化できる：

::

   mkdocs gh-deploy

このコマンドの内部では：

- ``mkdocs build`` でHTML生成
- 一時ブランチを経由して ``gh-pages`` に ``site/`` の中身を配置
- ``CNAME`` ファイルも自動でコピー（ルートに存在すれば）

非常に簡潔で、初心者にもやさしい運用が可能。


Sphinx では ghp-import の活用が定番
=====================================

Sphinxでは標準で ``gh-pages`` 対応がないため、次のように ``ghp-import`` パッケージを活用するのが一般的。

::

   pip install ghp-import
   make html
   ghp-import -n -p -f _build/html

- ``-n``: `.nojekyll` を追加
- ``-p``: 自動でpushする
- ``-f``: 強制上書き

CI/CDなどに組み込んで、GitHub Actions等と連携することも多い。

---

Netlifyとの比較
===============

Netlifyも静的サイトのホスティングに強く、次のような特徴がある：

.. list-table::
   :header-rows: 1
   :widths: 20 40 40

   * - 項目
     - GitHub Pages（gh-pages）
     - Netlify
   * - ビルド自動化
     - GitHub Actions等で手動構築
     - GUIで簡単に設定可能
   * - PRプレビュー
     - ✖（標準機能なし）
     - ✔ 自動でPreview URL生成
   * - カスタムドメイン
     - CNAMEで対応（SSLは自前）
     - 自動SSL対応、DNS管理も可能
   * - 動的機能
     - ✖ 静的HTMLのみ
     - ✔ Forms / Functions などあり

---

まとめ
======

- ``gh-pages`` ブランチを理解することで、軽量な静的サイト運用が可能となる
- Sphinx/MkDocs であれば、HTML出力 → gh-pages反映 の流れをCI/CDに組み込むことで、完全自動化も視野に入る
- Netlifyとの比較では、 **PRプレビューやSSLの自動管理** など、利便性の高さが目立つ
- 一方、GitHub Pagesの軽量性とGitHub一体運用のわかりやすさも大きな魅力


今後、自身の用途やチームの構成に応じて、 **「自動化の手間」と「ホスティング機能の豊富さ」** を天秤にかけて使い分けていきたい。

.. rubric:: 記事情報

:著者: mtakagishi
:投稿日: 2025-05-25
