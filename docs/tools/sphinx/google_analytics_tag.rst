==========================================================================================
SphinxにGoogle Analyticsのタグを埋め込む方法
==========================================================================================
Last Updated on 2023-05-05

.. note:: 
  | pydata_sphinx_themeが前提の記事です。
  | アナリティクスはGA4形式とUA形式の新旧2種がありますが、
  | v0.6.2(2021/04/26)以降、両方に対応されてます。

一般的な方法
====================
| conf.pyに設定可能です。
| v0.6.2にてGA4形式にも対応されました。
| 最新バージョンではUA形式は対応できなくなりました。

conf.py:: 

  html_theme_options["analytics"] = {
      "google_analytics_id": "G-XXXXXXXXXX",
  }

別の解決方法
====================

.. note:: 

  | pydata_sphinx_themeではv0.6.2より前のバージョンはGA4が対応されていませんでした。
  | 以下は当時に行った代替策です。
  
* layout.htmlをtemplate_path配下に作成。
* 下記の対応版「layout.html」格納

layout.html::

  {% extends "pydata_sphinx_theme/layout.html" %}
  {%- block htmltitle %}
  <title>{{ title|striptags|e }}{{ titlesuffix }}</title>
  <!-- Global site tag (gtag.js) - Google Analytics -->
  <script async src="https://www.googletagmanager.com/gtag/js?id=G-XXXXXXXXXX"></script>
  <script>
    window.dataLayer = window.dataLayer || [];
    function gtag(){dataLayer.push(arguments);}
    gtag('js', new Date());

    gtag('config', 'G-XXXXXXXXXX');
  </script>
  {%- endblock %}

