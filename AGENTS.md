# AGENTS.md

## このリポジトリについて

このリポジトリは、Sphinx + ablog で作成している個人技術ブログです。

公開サイトは日本語を主軸としつつ、英語ページも公開対象にします。ただし、運用者本人は日本語のみを理解するため、作業説明・判断材料・提案・確認事項は必ず日本語で書いてください。

## 基本方針

- すべてのやり取り、作業説明、提案、レビューコメントは日本語で行う。
- 記事本文の元原稿は日本語を正とする。
- 英語ページは翻訳版として扱う。
- 英語翻訳を作る場合でも、意味の確認や変更理由は日本語で説明する。
- 英語だけの説明、英語だけのコメント、英語だけの運用メモを残さない。

## ビルド

- パッケージ管理は Rye を使う。Poetry 前提で作業しない。
- 依存関係の同期は次を使う。

```bash
rye sync
```

- サイト全体のビルドは次を使う。

```bash
rye run doit doc
```

- ビルド成果物は `docs/_build/html` に出力される。
- `docs/_build/` 配下の生成物は原則として直接編集しない。

## 記事作成

- ブログ記事は `docs/blog/posts/` に置く。
- 記事形式は原則 reStructuredText、拡張子は `.rst` とする。
- ファイル名は次の形式にする。

```text
YYYY-MM-DD-slug.rst
```

例:

```text
2025-07-27-pre-commit-template-update-mypy.rst
```

- 記事冒頭には ablog の `post` directive を置く。

```rst
.. post:: 2025-07-27
   :tags: pre-commit, mypy, update
   :category: 運用改善
   :author: mtakagishi
   :language: ja
```

- ファイル名の日付と `.. post::` の日付は、原則一致させる。
- 新規記事の本文は日本語で書く。
- 英語記事を直接書くのではなく、日本語記事から翻訳する。

## 翻訳

- 翻訳は Sphinx gettext / sphinx-intl の仕組みを使う。
- gettext 更新は次を使う。

```bash
rye run doit gettext
```

- 翻訳ファイルは `docs/locale/en/LC_MESSAGES/` 配下の `.po` ファイルを編集する。
- `.mo` と `.pot` は生成物なので、原則コミットしない。
- 英訳補助スクリプトを使う場合は次の形式にする。

```bash
rye run python translate-po-ja-en.py docs/locale/en/LC_MESSAGES/対象ファイル.po
```

- 機械翻訳した英語は、公開前に日本語原文との意味ズレがないか確認する。
- Codex が翻訳を提案する場合、英訳だけでなく「日本語での要約・変更理由」も添える。

## Netlify / GitHub Actions

- Netlify の公開ディレクトリは `docs/_build/html`。
- Netlify のビルドコマンドは `rye run doit doc` を前提にする。
- GitHub Actions は Netlify の Build Hook を定期実行するために使っている。
- `NETLIFY_BUILD_HOOK` は秘密情報なので、記事・ログ・設定例に実値を書かない。

## 運用上の注意

- README に古い Poetry 前提の記述が残っている場合があるため、現在の実運用は `pyproject.toml`, `dodo.py`, `netlify.toml` を優先して判断する。
- `blog_future` の設定は予約投稿運用に影響するため、変更前に必ず意図を確認する。
- `blog_path = "blog/posts"` は `/blog` と `/blog.html` の衝突回避に関係しているため、安易に変更しない。
- Markdown も技術的には使えるが、このブログでは原則 `.rst` を使う。
- 既存記事の大規模な書き換えや形式変換は、明示的に依頼された場合だけ行う。

## Codex への指示

- 作業前に、変更対象と理由を日本語で簡潔に説明する。
- 作業後に、変更内容・確認したこと・残課題を日本語で報告する。
- 英語の設定名やコマンドはそのまま使ってよいが、説明は日本語にする。
- 運用者が日本語のみ理解する前提で、判断が必要な点は日本語で確認する。
- ブログ公開上、英語読者も意識するが、管理・編集・レビューの基準言語は日本語とする。

## ログから記事を書くエージェント

- ユーザーが AI とのやりとりログを指定してブログ記事作成を依頼した場合は、`docs/agents/ai-log-blog-writer.md` の手順に従う。
- 例: `copilot-session-latest-2026-05-27.md` を元に記事を書く依頼。
- ログから記事化する場合も、説明・確認・インタビューは必ず日本語で行う。
- 記事の日付は必ず未来日にし、`docs/blog/posts/` で未使用の最初の日付を使う。
- 1 日 1 記事の原則を守り、必要なら記事作成前にユーザーへ不足情報を確認する。
