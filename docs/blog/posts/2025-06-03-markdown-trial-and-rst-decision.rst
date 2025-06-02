.. post:: 2025-06-03
   :tags: ablog, markdown, myst, rst, 記事運用
   :category: ブログ運用
   :author: mtakagishi
   :language: ja

======================================================
Markdown導入の検討と、reStructuredText継続の判断
======================================================

Sphinx + ablog において、記事を reStructuredText ではなく Markdown で書く運用を検討した。

MyST-Parser を導入することで、Sphinx は Markdown を理解可能となり、以下のような設定を行うことで `.md` ファイルでの投稿も実現できることが確認された。

.. code-block:: python

   extensions = [
       "ablog",
       "myst_parser",
   ]

   myst_enable_extensions = [
       "colon_fence",
       "deflist",
       "attrs_block",
       "html_admonition",
       "html_image",
       "substitution",
       "replacements",
   ]

Markdown 側では、以下のような front-matter を冒頭に記述することで `.. post::` 相当の意味を持たせることができる。

.. code-block:: markdown

   ---
   title: Markdownで書いた記事
   date: 2025-06-03
   tags: [ablog, myst, markdown]
   author: mtakagishi
   ---

さらに、MyST記法を用いることで `note` や `warning` 、 `toctree` といった Sphinx ディレクティブの一部も Markdown 上で再現可能であることも確認された。

.. code-block:: markdown

   :::note
   これは注意書きです。
   :::

しかし、ChatGPT上でMarkdown形式の記事案を得ようとした場合、チャット欄がMarkdownを自動的にレンダリングしてしまうという問題に直面した。

たとえば `:::{note}` のような構文は、ユーザーがコピーペーストしようとした段階で展開表示されてしまい、正しく貼り付けることができない。
これはUI設計上の仕様であり、ユーザー側からの回避は困難である。

このため、Markdownでの編集やテンプレート設計をChatGPTと協調して行うには現時点で限界があると判断した。

よって、今後の記事運用については、引き続き `.rst` 形式をベースとした運用を継続する方針とする。

Markdown記法に関しては、今後 Sphinx 本体や ablog、MyST 側の進化や、ChatGPTのMarkdown出力制御手段が改善された段階で、再度検討の余地があるだろう。

---

この検討記録は、自身の技術的試行錯誤と選択のログとして、ブログ上に残しておく。

.. rubric:: 記事情報

:著者: mtakagishi
:公開日: 2025-06-03
