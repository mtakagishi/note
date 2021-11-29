==========================================================================================
SphinxにGoogle Analyticsのタグを埋め込む方法
==========================================================================================
Last Updated on 2021-08-14

note:: 

| pydata_sphinx_themeテーマをベースにした記事です。
| アナリティクスはGA4形式とUA形式の新旧2種がありますが、
| v0.6.2(2021/04/26)以降、両方に対応されてます。

一般的な方法
====================
| conf.pyに設定すればOKです。
| v0.6.2にてGA4形式にも対応されました。
| UA-で始まるかG-で始まるかで自動で判断されます。

conf.py:: 

  html_theme_options = {
      "google_analytics_id": "UA-XXXXXXXXX-N",
  }

別の解決方法
====================

.. note:: 

  | v0.6.2より前はGA4が対応されていませんでした。
  | こちらはtempleteを拡張する方法です。
  | "basic/layout.html" からの派生テーマなら同じ方法で行けるはずです。

* conf.py の template_path の設定を確認
* layout.htmlを用意し、template_path配下に作成。
* googleアナリティクス設定の「ウェブストリームの詳細」画面を参考に下記のように「layout.html」格納

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


.. |date| date::