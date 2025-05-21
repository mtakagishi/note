.. post:: 2025-05-22
   :tags: mkdocs, github, poetry, ドキュメント, static-site
   :category: 実践メモ
   :author: mtakagishi
   :language: ja

Poetry と MkDocs を使って GitHub Pages に自己紹介ページを公開する手順メモ
===============================================================================

Poetry でパッケージ管理しながら、MkDocs を使って簡単な静的ページを作成し、GitHub Pages に公開するまでの手順を整理した実践メモです。

.. contents::
   :local:

背景
----

個人プロフィールを簡単に公開できる方法として、MkDocs を選定。加えて依存関係を明示的に管理するため、Poetry を用いることにした。

Poetry + MkDocs による静的サイト作成の手順
----------------------------------------------

以下のように進めた。

1. プロジェクトディレクトリ作成と初期化::

    mkdir my-profile
    cd my-profile
    poetry init --name "my-profile" -n
    poetry add mkdocs

2. ドキュメントディレクトリ作成::

    mkdir docs
    echo "# 自己紹介ページ" > docs/index.md

3. `docs/index.md` を以下のように編集::

    # 自己紹介

    こんにちは、名無しの権兵衛 です。

    - 所属: ○○会社のエンジニア
    - 興味: Python / Vim / ドキュメント管理
    - 趣味: 宇宙や歴史の考察

4. `mkdocs.yml` 作成::

    site_name: 名無しの権兵衛 の自己紹介
    theme:
      name: material

    ※ material テーマを使う場合は `poetry add mkdocs-material` も実行。

5. ローカルで確認::

    poetry run mkdocs serve

    ブラウザで http://localhost:8000 を開く。

GitHub リポジトリとの連携と公開
-----------------------------------------

1. GitHub 上でリポジトリ（例: my-profile）を作成し、初期化::

    git init
    git add .
    git commit -m "initial commit"
    git remote add origin https://github.com/<ユーザー名>/my-profile.git
    git push -u origin master


    ※ ssh 接続を使用する場合は、以下のようにリモートURLを設定します。

       git remote set-url origin git remote set-url origin git@github.com:<ユーザー名>/my-profile.git

2. GitHub Pages にデプロイ::

    poetry run mkdocs gh-deploy
    自動的に `gh-pages` ブランチが作成され、GitHub Pages から公開される。
    公開URL: https://<ユーザー名>.github.io/my-profile/
    GitHub Pages の設定は、リポジトリの Settings > Pages で確認できます。

手順通りに作成してみた実際のページ
-----------------------------------------

`ページリンク <https://mtakagishi.github.io/github-io-test/>`_

学びと今後の応用
----------------------

- `mkdocs gh-deploy` は `mkdocs` 本体に含まれるコマンド
- `gh-deploy` により、GitHub Pages の設定が簡単になる。

備考
----

リモートURLの切替を確認するには::

    git remote -v

SSHのテスト接続::

    ssh -T git@github.com

---

必要に応じて、GitHub Actions による自動デプロイや、複数ページの構成などにも拡張できます。

.. rubric:: 記事情報

:著者: mtakagishi
:投稿日: 2025-05-22
