.. post:: 2025-04-01
  :tags: ablog,sphinx,netlify
  :category: サイト管理
  :author: mtakagishi
  :language: ja

============================
ブログ運用にAblogを活用する
============================

純粋なSphinxの機能よりも、もう少しブログっぽく運用したい場合にAblogを活用すると便利

Ablogとは
========================
sphinxの拡張機能で、ブログのような形式で記事を管理できる。カテゴリやタグを設定しておけば、それに基づいて記事一覧を生成してくれるのが便利。

Ablogでできるようになること
----------------------------------
- カテゴリやタグで記事を分類
- 記事一覧の自動生成
- 自動アーカイブ
- サイドバーサポート
- ドラフト記事の作成

Ablogのインストール
========================
pipやposetry addでインストールし、conf.pyを少しいじればすぐ使える。`詳細は公式ドキュメント参照 <https://ablog.readthedocs.io>`_ 


記事作成
========================

blogフォルダを作成し、その中に記事を作成。ファイルは手動作成でもよいし ``ablog post new-post`` で作成してもよい。

.. code-block:: rst
  :caption: blog/2025-03-27-new-post.rst

  .. post:: 2025-03-27
    :tags: sphinx, ablog
    :category: python

  新しい記事
  ================

  これは新しい記事です。

記事一覧
========================

index.rstに以下のように記述すると、最新の5件の記事が表示される。

.. code-block:: rst
  :caption: blog/index.rst

  .. postlist:: 5
     :date: %Y/%m/%d
     :format: {title} ({date})
     :excerpts:
     :expand: Read more ...

その他の機能
========================

自動アーカイブ
------------------------

Ablogはビルド時に自動でアーカイブ実行される。以下のような記述をすると、アーカイブページへのリンクが簡単に設置できる。

.. code-block:: rst
  :caption: blog/index.rst

  - :ref:`タグ一覧 <blog-tags>`
  - :ref:`カテゴリ一覧 <blog-categories>`
  - :ref:`アーカイブ <blog-archives>`

.. rubric:: 参考URL

`公式ページ（Cross-referencing Blog Pages） <https://ablog.readthedocs.io/en/stable/manual/cross-referencing-blog-pages.html>`_ 


サイドバーサポート
------------------------

サイドバーには、タグ一覧やカテゴリ一覧、アーカイブへのリンクを設置することができる。当サイトの場合、secondary_sidebar_itemsに以下のように設定している。

.. code-block:: python
  :caption: conf.py

  html_theme_options = {
    "secondary_sidebar_items": {
      "**": [
        "ablog/recentposts.html",
        "ablog/tagcloud.html",
        "ablog/categories.html",
        "ablog/archives.html",
      ],
    },
  }

.. rubric:: 参考URL

`公式ページ（Templating and Themes Support） <https://ablog.readthedocs.io/en/stable/manual/templates-themes.html>`_ 

ドラフト記事の作成
------------------------

記事のdate属性を未来日にしておけば、その記事はドラフト扱い。ビルド時には表示されない。sphinxは静的ページなので、未来日にビルドし直す必要がある。


所感
========================

日々の勉強メモを残せるように継続の基盤にしたいという思いは達成できそう。カテゴリやタグの整理自動や、ドラフト記事の作成などは重宝しそう。折角の機会なので、これを機にブログを継続していきたい。

.. rubric:: 記事情報

:投稿日: 2025-04-01
:投稿者: mtakagishi