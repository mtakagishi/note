sphinxで索引ページを作成する
==========================================

sphinxでは、索引ページを作成する機能があります。

索引ページとは
------------------
本の巻末で見つけるアルファベット順、50音順に並んだ用語集のようなページのこと。

当サイトの場合
----------------
当サイトの索引ページ　⇒　:ref:`genindex`


仕組み
-----------------
* sphinxがhtmlビルド時に genindex.html を勝手に作ってくれます。
* :kbd:`\:ref\:\`genindex\`` とすることで索引へのリンクを張ることができます。
* 各rstページの「indexディレクティブ」「glossaryディレクティブ」から単語を集めて索引化します。

.. tip:: 
  toctree で索引へのリンクさせたい場合は、genindex.rstを作成します [#toctree]_

indexディレクティブ
-------------------------

indexディレクティブ::

  .. index :: <entries>

* 表示は特にされず、索引に収集されるための印のように使う。
* 複数の単語の索引に紐づけることができる。⇒ [#index]_

.. tip:: 
  * 全て最初の文字で分類され、ひらがな、カタカナ、漢字は別文字扱い。日本語としては使いにくい
  * Sphinx拡張の記事 [#kana-text]_ で日本語で柔軟な索引が作れるとの情報。試したが、当サイトが環境事情でPython3.7のためコンパイルが通らず、評価できずにいる。
  
glossaryディレクティブ
-----------------------------
glossaryディレクティブ::

  ../ glossary ::

    term 1 : た
    term 2 : た
      Definition of both terms.

* glossaryは用語集として昨日する。単なる印であるIndexと違い、用語が表示される。
* グルーピングの概念がある。漢字などを何らかの50音のカナに集約させれば50音に紐づく索引のように作成は可能。



* .. [#toctree] `How can i include the genindex in a Sphinx TOC? <https://stackoverflow.com/questions/36235578/how-can-i-include-the-genindex-in-a-sphinx-toc>`_ 
* .. [#index] `インデックス生成のためのマークアップ <https://www.sphinx-doc.org/ja/master/usage/restructuredtext/directives.html#index-generating-markup>`_ 
* .. [#kana-text] `【Sphinx拡張】索引と用語集のかな文字対応 <https://qiita.com/koKekkoh/items/4563b63fdb8eaa3ef4f9>`_ 


