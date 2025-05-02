.. post:: 2025-05-05
   :tags: sphinx, ablog, netlify, github-actions, 自動化, セキュリティ
   :category: ドキュメント管理
   :author: mtakagishi
   :language: ja

===================================================================
Sphinx + ablog でDraftを自動公開するための自動ビルドの設定
===================================================================

Sphinx + ablog でのブログ運営では「投稿日を未来日にしておく」ことで、ドラフト記事を準備できます。しかし、公開日以降にビルドが走らない限りWebサイトには反映されません。本記事では自動ビルドを実行する方法を考察します。

背景と課題
==========

ablog では ``.. post:: YYYY-MM-DD`` のように記事日付を設定しますが、日付が未来である場合、その記事はドラフトとして無視されます。

例えば2025-05-05現在、以下のような記事を書いたとしても：

.. code:: rst

   .. post:: 2025-06-01
      :tags: future
      :category: ブログ運用

      公開は6月1日を予定しています。

この記事が実際にビルド出力されるのは、 **6月1日以降に Sphinx を再ビルドしたとき** です。

本サイトは、Netlifyでサイトを公開していますが、Netlifyでは GitHub への push がビルドトリガとなっているため、「未来記事の自動公開」には対応していません。

そのため、 **未来日を迎えた後に自動で再ビルドを実行する仕組み** については別途検討する必要があります。

本サイトの環境
=================
本サイトは、以下のような環境で運用しています。同じような環境の方は参考にしてください。

- **Sphinx** + **ablog** で構築
- **GitHub** でソースコード管理
- **Netlify** でホスティング

解決策：GitHub Actions × Netlify Build Hook
========================================================

Netlify では、特定の URL に対して POST リクエストを送信することで、任意のタイミングでビルドを実行できる **Build Hook** 機能を提供しています。

この Build Hook に対して、GitHub Actions の定期実行（cron）機能を使って毎日決まった時間にアクセスすれば、自動的にビルドが発生します。

これにより、未来日を過ぎた ablog の記事が毎日チェックされ、自動公開されるようになります。

設定手順
========

1. **NetlifyでBuild Hookを作成**

   1. Netlify の管理画面にアクセス
   2. 対象サイト →「Site configrations」→「Build & deploy」→「Build hooks」
   3. Add build hook
      - Hook name: 任意（例: `Daily Scheduled Deploy`）
      - Branch: `main` （または使用中のブランチ）

   4. 作成後に表示される URL（例：`https://api.netlify.com/build_hooks/xxxxxxxxxxxxxx`）を控えておく

2. **GitHub Secrets に Build Hook を登録（セキュリティ対応）**

   Build Hook の URL は知られてしまうと誰でもビルドを発動できてしまうため、**GitHub Secrets** で安全に管理します。

   - GitHub リポジトリ → Settings → Secrets and variables → Actions
   - 「New repository secret」
     - Name: `NETLIFY_BUILD_HOOK`
     - Value: Netlify で取得した Build Hook URL

3. **GitHub Actions ワークフローを作成**

   リポジトリの `.github/workflows/` フォルダに以下のようなファイルを作成：


   .. code-block:: yaml
      :caption: .github/workflows/netlify-scheduled-deploy.yml
      :linenos:

      name: Netlify Scheduled Deploy

      on:
        schedule:
          - cron: '0 15 * * *'  # JST 0:00（= UTC 15:00）
        workflow_dispatch:      # 手動実行も可能

      jobs:
        trigger-netlify:
          runs-on: ubuntu-latest
          steps:
            - name: Trigger Netlify Build via Secret
              run: |
                curl -X POST -d '{}' "${{ secrets.NETLIFY_BUILD_HOOK }}"

   🔹 `workflow_dispatch` を追加することで、必要に応じて GitHub 上から手動でビルドを実行することもできます。

4. **コミットして GitHub に反映**

   作成した `.yml` をコミット・プッシュすれば、毎日自動的に Netlify ビルドが行われるようになります。

セキュリティ上の注意点
========================

- **Build Hook URL はトークンと同じ扱いで、絶対に公開しないこと**
- `.env` ファイルで管理する場合は、`.gitignore` に含めてリポジトリに含めないようにする
- GitHub Secrets を使えば、ログ出力などにもマスクが自動でかかるため安心

補足
====

- cron は UTC ベースのため、日本時間（JST）で定期実行したい場合は9時間引く必要があります
- 毎日 0 時 JST に実行したい場合 → `cron: '0 15 * * *'`
- 週次・月次への変更も可能（例: 毎週月曜 JST 0 時 → `'0 15 * * 1'`）

まとめ
======

ablog で未来日記事を予約投稿として管理した場合、Netlifyでホスティングしている以上は、通常はgit pushしない限りビルドされないため、公開されません。
今回、Netlify の Build Hook と GitHub Actions の `cron` 実行を組み合わせることで、 **定期的にビルドをトリガし、記事の自動公開を実現** しました。

本スタックは、GitHub Actions + Netlify の組み合わせで、コストもかからないのがうれしいところです。


.. rubric:: 記事情報

:投稿日: 2025-05-05
:投稿者: mtakagishi
