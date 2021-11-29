==========================================================================================
Sphinxのsitemapを構築する
==========================================================================================
Last Updated on 2021-08-20

追加パッケージ
---------------------------------
sphinx-sitemap::

  poetry add sphinx-sitemap

conf.pyの設定例
---------------------------------

conf.py::

  # 以下を追記します。
  extensions = ['sphinx_sitemap']

  html_baseurl = 'https://mtakagishi.tk/'
  html_extra_path = ['robots.txt']


検索エンジンクローラ対応
---------------------------------
  
conf.pyと同じ階層に、robots.txt を配置しておく。

robots.txt::

  User-agent: *
  Sitemap: https://mtakagishi.tk/sitemap.xml

テスト
--------------------------------

Google Search Console	の場合、以下でテスト可能です。配置したsitemapが許可されているか確認しましょう。
https://www.google.com/webmasters/tools/robots-testing-tool


.. |date| date::