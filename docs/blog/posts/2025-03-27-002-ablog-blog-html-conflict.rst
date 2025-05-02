.. post:: 2025-04-02
  :tags: ablog,sphinx,netlify,トラブルシューティング
  :category: サイト管理
  :author: mtakagishi
  :language: ja

================================================================================
ablogで"/blog.html"と"/blog/index.html"の競合への対処
================================================================================

ablog を使ってブログサイトを構築していたところ、ビルド後の出力で ``/blog.html`` と ``/blog/index.html`` の両方が生成されてしまい、URLの扱いやリンクの挙動で混乱する場面がありました。本記事ではその原因と対処法についてまとめておきます。

問題の発生状況
================

以下のような構成で Sphinx + ablog を使用：

- ``blog/index.rst`` を作成し、自作のブログトップページを定義
- ``conf.py`` の設定は ``blog_path=blog`` (デフォルト値)

この状態でビルドすると、以下の2つの HTML ファイルが生成される：

- ``/blog.html`` （ablog が自動生成する全記事一覧ページ）
- ``/blog/index.html`` （自分で作成した ``blog/index.rst`` のビルド結果）

その結果、以下のような衝突が発生：

- ``toctree`` のリンク先が ``/blog`` か ``/blog/index.html`` かで揺れる
- Netlify 上で ``/blog`` にアクセスすると ``/blog.html`` が優先される

原因と仕様
================================

ablog はデフォルトで ``blog_path = "blog"`` の設定となっており、  
この場合、自動的に ``/blog.html`` を全記事一覧ページとして生成します。  
一方で ``blog/index.rst`` を作ると、それは ``/blog/index.html`` になる。

つまり、``/blog.html`` と ``/blog/index.html`` が**別物として**同時に存在してしまうのが問題。

対処法
================================

自分の ``blog/index.rst`` を維持したまま、ablog の出力と衝突しないようにするには  
``conf.py`` にて ``blog_path`` の値を変更するのが有効。

たとえば、以下のように設定：

.. code-block:: python

    blog_path = "blog/posts"

これにより：

- ablog が生成する全記事一覧ページ → ``/blog/posts.html``
- 自作の ``blog/index.rst`` → ``/blog/index.html``

と、役割が分離され、衝突や混乱を回避可能。

補足：Netlify でのURL優先順
================================

Netlify では ``/blog`` にアクセスした場合、``/blog.html`` を優先して表示します（静的ファイルベースのルール）。  
したがって netlifyのリダイレクト設定を使った誘導という手もできなくはないが、フォルダ構成を正したほうがスマート：

.. code-block:: shell
  :caption: _redirects

  /blog   /blog/index.html   200


まとめ
================================

- ablog は ``blog_path`` の設定により自動出力先が決まる
- ``blog/index.rst`` を作るなら ``blog_path`` を別にするのが安全
- 静的出力では ``/blog`` が ``/blog.html`` と扱われる点にも注意


.. rubric:: 記事情報

:投稿日: 2025-04-02
:投稿者: mtakagishi
