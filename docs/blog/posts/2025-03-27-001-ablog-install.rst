.. post:: 2025-03-29
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
  	
  `公式ページ（Cross-referencing Blog Pages） <https://ablog.readthedocs.io/en/stable/manual/cross-referencing-blog-pages.html>`_ 

サイドバー
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


  `公式ページ（Templating and Themes Support） <https://ablog.readthedocs.io/en/stable/manual/templates-themes.html>`_ 


所感
========================

Sphinxの機能を拡張するAblogは、ブログ運用には非常に便利。記事の管理や一覧表示、アーカイブの自動生成など、ブログ運用に必要な機能が揃っている。また記事に未来日を指定すると自動でドラフト扱いとしてビルド対象から除外されて公開されない機能も便利。

.. rubric:: 記事情報

:投稿日: 2025-03-27
:投稿者: mtakagishi