.. post:: 2025-05-18
   :tags: pre-commit, github-actions, ci, automation, python
   :category: dev-environment
   :author: mtakagishi
   :language: ja

pre-commit フックを GitHub Actions で自動更新する
====================================================

`pre-commit autoupdate` を定期的に自動実行し、フックのバージョン更新PRを GitHub Actions 経由で作成する仕組みを紹介します。

.. contents::
   :local:
   :depth: 2

なぜ自動更新が必要か
----------------------

- フックのバージョンは手動更新しないと古くなる
- セキュリティパッチや仕様変更を取り込みたい
- ローカルで `pre-commit` を使っていないユーザの変更にも効く

設定ファイル例
----------------

以下を ``.github/workflows/pre-commit-autoupdate.yml`` に配置します：

.. code-block:: yaml

   name: pre-commit autoupdate

   on:
     schedule:
       - cron: '0 0 1 * *'  # 毎月1日 (UTC)
     workflow_dispatch:

   jobs:
     autoupdate:
       runs-on: ubuntu-latest

       steps:
         - uses: actions/checkout@v4
           with:
             fetch-depth: 0

         - uses: actions/setup-python@v5
           with:
             python-version: '3.11'

         - name: Install pre-commit
           run: |
             pip install pre-commit

         - name: Run autoupdate
           run: |
             pre-commit autoupdate
             git diff --exit-code || echo "Hooks updated"

         - name: Create PR
           uses: peter-evans/create-pull-request@v6
           with:
             commit-message: "chore: pre-commit hooks autoupdate"
             title: "chore: Update pre-commit hooks"
             body: |
               This PR updates the pre-commit hook versions.
             branch: chore/pre-commit-autoupdate
             delete-branch: true

注意点と推奨運用
------------------

- 生成されたPRは手動でレビュー＆マージ
- 差分を確認して問題なければ取り込む
- `pre-commit run --all-files` で CI による整合性チェックを追加すると安全

おわりに
--------

自動更新の仕組みを組み込んでおくことで、運用コストを下げつつ、継続的にクリーンな開発環境を保つことができます。

.. rubric:: 記事情報

:投稿日: 2025-05-18
:著者: mtakagishi
