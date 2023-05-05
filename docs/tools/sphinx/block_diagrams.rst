***************************************************
sphinxでフロー図を表現する
***************************************************

フロー図などを作図可能なSphinxの拡張機能

* ブロック図(blockdiag)
* シーケンス図(seqdiag)
* アクティビティ図(actdiag)
* 論理ネットワーク図(nwdiag)

設定方法
==========

パッケージインストール
---------------------------
* sphinxcontrib-blockdiag
* sphinxcontrib-seqdiag
* sphinxcontrib-actdiag
* sphinxcontrib-nwdiag

pip::

  pip install sphinxcontrib-actdiag sphinxcontrib-blockdiag sphinxcontrib-nwdiag sphinxcontrib-seqdiag

poetry::

  poetry add sphinxcontrib-actdiag sphinxcontrib-blockdiag sphinxcontrib-nwdiag sphinxcontrib-seqdiag

conf.pythのextensions設定
--------------------------------

.. code-block:: python
  :caption: conf.py
  :linenos:
  
  extensions = [
    'sphinxcontrib.blockdiag',
    'sphinxcontrib.seqdiag',
    'sphinxcontrib.actdiag',
    'sphinxcontrib.nwdiag',
    'sphinxcontrib.rackdiag',
    'sphinxcontrib.packetdiag',
  ]

イメージファイル形式選択の指定
----------------------------------------------
PNG か SV

.. code-block:: python
  :caption: conf.py
  :linenos:
  
  # blockdiag
  blockdiag_html_image_format = 'SVG'

日本語フォント
------------------
日本語文字列を出力可能にするためにフォントファイルttf形式のファイルが必要となる。

`IPAexフォント <https://moji.or.jp/ipafont/>`_


conf.pythのfont設定
--------------------------------

.. code-block:: python
  :caption: conf.py
  :linenos:
  
  # blockdiag-font
  blockdiag_fontpath = 'docs/_font/ipaexg.ttf'

書き方のサンプル
====================
blockdiagディレクティブ内に記載 [#]_

.. code-block:: python
  :linenos:
  
  code
  .. blockdiag::

    blockdiag {
      // ノード設定
      A [label = "春"];
      B [label = "夏"];
      C [label = "秋"];
      D [label = "冬"];

      // ラベル
      A -> B [label = "梅雨", textcolor="orange"];
      B -> C [label = "残暑", textcolor="pink"];
      C -> D [label = "紅葉", textcolor="red"];
      D -> A [label = "花見", textcolor="green"];
    }


.. blockdiag::

  blockdiag {
    //orientation = portrait;
    // ノード設定
    A [label = "春"];
    B [label = "夏"];
    C [label = "秋"];
    D [label = "冬"];

    // 接続線ラベル
    A -> B [label = "梅雨", textcolor="orange"];
    B -> C [label = "残暑", textcolor="pink"];
    C -> D [label = "紅葉", textcolor="red"];
    D -> A [label = "花見", textcolor="green"];
  }

.. rubric:: 関連リンク

* .. [#] `blockdiag公式ドキュメント <http://blockdiag.com/ja/index.html>`_ 
