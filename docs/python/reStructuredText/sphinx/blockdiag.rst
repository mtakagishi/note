***************************************************
sphinxでブロック図など
***************************************************

以下のような図を記入できるようにsphinxを拡張できます。

* ブロック図(blockdiag)
* シーケンス図(seqdiag)
* アクティビティ図(actdiag)
* 論理ネットワーク図(nwdiag)

設定
==========

必要も追加モジュール
---------------------------
* sphinxcontrib-blockdiag
* sphinxcontrib-seqdiag
* sphinxcontrib-actdiag
* sphinxcontrib-nwdiag

pip、poetry、requrements.txtなど、環境に応じて追加する。

pipの場合::

  pip install sphinxcontrib-actdiag sphinxcontrib-blockdiag sphinxcontrib-nwdiag sphinxcontrib-seqdiag

poetryの場合::

  poetry add sphinxcontrib-actdiag sphinxcontrib-blockdiag sphinxcontrib-nwdiag sphinxcontrib-seqdiag

conf.pyに拡張を記入
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

HTML化での形式選択
-----------------------
PNG か SV

.. code-block:: python
  :caption: conf.py
  :linenos:
  
  # blockdiag
  blockdiag_html_image_format = 'SVG'

日本語対応
------------------
日本語に対応するにはフォントファイルが必要。フォントファイルはttf形式。

今回は`IPAexフォント <https://moji.or.jp/ipafont/>`_ で対応。IPAのライセンスに従い入手したZIPを回答しttfファイルをsphinxが参照できる場所に配置し、conf.pyにpathを指定しておきました。

.. code-block:: python
  :caption: conf.py
  :linenos:
  
  # blockdiag-font
  blockdiag_fontpath = 'docs/_font/ipaexg.ttf'

基本的な書き方
====================
blockdiagディレクティブ内に記載  詳細 ⇒ [#]_

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




