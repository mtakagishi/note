# note.mtakagishi

[![MIT license](https://img.shields.io/badge/License-MIT-blue.svg)](https://lbesson.mit-license.org/) [![Netlify Status](https://api.netlify.com/api/v1/badges/cf669616-af9c-424e-bd66-d00fe89e9420/deploy-status)](https://app.netlify.com/sites/jolly-brown-b98547/deploys)

## URL

- https://mtakagishi.com
- https://jolly-brown-b98547.netlify.app/

## サイト趣旨

- IT 関連の技術メモ、作業記録、運用ログを残す個人ブログ。
- 日本語記事を原稿の正とし、英語ページは翻訳版として公開する。

## 開発環境

現在の実運用は Rye を前提にしています。古い Poetry 前提の手順は使いません。

- Python: 3.12 以上
- Netlify build 環境: Python 3.13
- パッケージ管理: Rye
- ドキュメント生成: Sphinx + ablog
- タスク実行: doit

## Windows / VS Code での初期セットアップ

Rye を未導入の場合は、先に Rye をインストールしてください。

まず、Windows の VS Code ターミナルで次を確認します。

```powershell
python --version
rye --version
```

どちらかが見つからない場合は、Python または Rye のインストール、もしくは PATH 設定を確認してください。

```powershell
git clone https://github.com/mtakagishi/note.git
cd note
rye sync
```

`.venv` を削除して作り直したい場合も、リポジトリ直下で次を実行します。

```powershell
rye sync
```

## ビルド方法

サイト全体をビルドします。

```powershell
rye run doit doc
```

ビルド成果物は次に出力されます。

```text
docs/_build/html
```

多言語ビルドの出力先は次の通りです。

```text
docs/_build/html/ja
docs/_build/html/en
```

## localhost での確認方法

ビルド後に、リポジトリ直下で次を実行します。

```powershell
rye run python simple_http_server.py --open-browser
```

ポートを指定する場合:

```powershell
rye run python simple_http_server.py -p 8123 --open-browser
```

既定ポートは `8000` です。

ビルド済みで、現在の Python から直接起動できる場合は、次のバッチファイルも使えます。

```powershell
.\run_simple_http_server.bat
```

## 記事の置き場所

ブログ記事は次に置きます。

```text
docs/blog/posts/
```

ファイル名は原則として次の形式にします。

```text
YYYY-MM-DD-slug.rst
```

記事冒頭には ablog の `post` directive を書きます。

```rst
.. post:: 2025-07-27
   :tags: pre-commit, mypy, update
   :category: 運用改善
   :author: mtakagishi
   :language: ja
```

## 翻訳方法

gettext / sphinx-intl 用の `.po` ファイルを更新します。

```powershell
rye run doit gettext
```

英語翻訳は `docs/locale/en/LC_MESSAGES/` 配下の `.po` ファイルを編集します。

英訳補助スクリプトを使う場合:

```powershell
rye run python translate-po-ja-en.py docs/locale/en/LC_MESSAGES/対象ファイル.po
```

機械翻訳後は、公開前に日本語原文との意味ズレがないか確認します。

翻訳状態の機械チェックを行う場合:

```powershell
rye run doit intl_validate
```

検証レポートは次に出力されます。

```text
docs/_build/_intl/validation-report.md
```

運用ガイド:

- `docs/agents/po-validation-guide.md`
- `docs/agents/translation-workflow.md`

## Netlify / GitHub Actions

Netlify の設定は `netlify.toml` にあります。

- build command: `rye sync` の後に `rye run doit doc`
- publish directory: `docs/_build/html`

GitHub Actions の `.github/workflows/netlify-scheduled-deploy.yml` は、毎日 JST 0:00 に Netlify Build Hook を呼び出します。

`NETLIFY_BUILD_HOOK` は GitHub Secrets に保存し、リポジトリや記事中に実値を書かないでください。

## メンテナンスメモ

- `docs/_build/` は生成物なので直接編集しない。
- `.mo` と `.pot` は生成物なのでコミットしない。
- Markdown も技術的には使えるが、このブログでは原則 `.rst` を使う。
- `blog_path = "blog/posts"` は Netlify 上の `/blog` と `/blog.html` の衝突回避に関係するため、安易に変更しない。
- `blog_future` は予約投稿運用に影響するため、変更前に意図を確認する。

## Proxy メモ

### pip

```ini
[global]
proxy = [user:passwd@]http://proxy:port
```

### shell

```bash
export HTTP_PROXY="http://proxy:port"
export HTTPS_PROXY="http://proxy:port"
```

### git

```bash
git config --global http.proxy http://proxy:port
git config --global https.proxy http://proxy:port
```
