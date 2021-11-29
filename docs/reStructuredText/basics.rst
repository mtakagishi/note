基本的な書き方
*******************************

セクション
=================================

rst記述::

  #####
  Title
  #####

| 使用可能な文字：\= \- \` \: \' \" \~ \^ \_ \* \+ \# \< \> `
| タイトル文字の下、または上下につける

スタイルガイドによると以下。

* \# 部: オーバーライン付き
* \* 章: オーバーライン付き
* \=, セクション
* \-, サブセクション
* \^, サブサブセクション
* \", パラグラフ


パラグラフ
=================================
文章の塊、段落の塊は、1行以上の空行で区切る。

改行（ラインブロック）
=================================================
マークダウンの感覚で文末にスペース2つ入れても改行されない。
文頭に | を入れる。

ラインブロック::

  | Lend us a couple of bob till Thursday.
  | I'm absolutely skint.
  | But I'm expecting a postal order and I can pay you back
    as soon as it comes.
  | Love, Ewan.

出力結果

| Lend us a couple of bob till Thursday.
| I'm absolutely skint.
| But I'm expecting a postal order and I can pay you back
  as soon as it comes.
| Love, Ewan.


インラインマークアップ
=================================
文章内で利用できる装飾

ボールド
--------------------------
\*\*太文字\*\* ⇒ **太文字**


コードサンプル
--------------------------
\`\`コードサンプル\`\` ⇒ ``コードサンプル``

数式
--------------------------
\:math\:\`\\sqrt\{16\}\` ⇒ :math:`\sqrt{16}`

キーボード
--------------------------

\:kbd\:\`shortcut\` 　⇒　:kbd:`shortcut` 


リテラルブロック
=================================
リテラルブロック\:\:
  リテラルブロック内容

出力結果
-------------
リテラルブロック::

  リテラルブロック内容


コードの挿入
=================================
リテラルブロックを使う。Sphinxならcodeディレクティブを使うとオプション指定で細かい表現が可能

リテラルブロックの場合
-----------------------------------

リテラルブロック例::

  Pythonサンプル::

    def factorial(x):
        if x == 0:
            return 1
        else:
            return x * factorial(x - 1)

出力

Pythonサンプル::

  def factorial(x):
      if x == 0:
          return 1
      else:
          return x * factorial(x - 1)


リスト
=================================
箇条書き
-------------------------------
箇条書き::

  * this is
  * a list

    * with a nested list
    * and some subitems

  * and here the parent list continues

箇条書き(表示）

* this is
* a list

  * with a nested list
  * and some subitems

* and here the parent list continues

番号付き
-------------------------------

番号付き::

  1. This is a numbered list.
  2. It has two items too.
  #. This is a numbered list.
  #. It has two items too.

番号付き(表示)

1. This is a numbered list.
2. It has two items too.
#. This is a numbered list.
#. It has two items too.

用語
-------------------------------

用語::

  term1
    Definition 1.

  term2
    Definition 2, paragraph 1.

    Definition 2, paragraph 2.

  term3 : classifier
    Definition 3.

  term4 : classifier one : classifier two
    Definition 4.

用語(表示)

term1
  Definition 1.

term2
  Definition 2, paragraph 1.

  Definition 2, paragraph 2.

term3 : classifier
  Definition 3.

term4 : classifier one : classifier two
  Definition 4.

項目リスト
-------------------------------

項目リスト::

  :fieldname1: Field content
  :fieldname12: Field content
  :fieldname123: Field content
  :fieldname1234: Field content


項目リスト(表示)

:fieldname1: Field content
:fieldname12: Field content
:fieldname123: Field content
:fieldname1234: Field content

リンク
=================================

外部リンク
-------------------------------

外部リンク1::

  `Link text <https://domain.invalid/>`_ 

外部リンク2::

  This is a paragraph that contains `a link`_.
  .. _a link: https://domain.invalid/

内部リンク
-------------------------------

内部リンク表現::

  .. _my-reference-label:

  Section to cross-reference
  --------------------------

  This is the text of the section.

  It refers to the section itself, see :ref:`my-reference-label`.


テーブル
=================================
Table Fromatter
---------------------------------------
プレーンテキストでの表の表現は、整形が煩雑になるので、VSCODE利用している場合はプラグインが便利

Table Fromatterのインストール
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
VSCODE拡張から Table Formatter をインストール

使用方法
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

| 変換前の書式はサンプルに記載
| :kbd:`Ctrl + Shift + P` から『Table: Format Current』

グリッド
-------------------------------
Table Fromatter書式::

  +
  ||Mon|Tue|Wed|Thu|Fri|
  +=
  |田中|(^^)|(xx)|(xx)|('')|(^^)|
  +-
  |鈴木|(^^)|(^^)|('')|(xx)|(^^)|
  +

フォーマット後::

  +------+------+------+------+------+------+
  |      | Mon  | Tue  | Wed  | Thu  | Fri  |
  +======+======+======+======+======+======+
  | 田中 | (^^) | (xx) | (xx) | ('') | (^^) |
  +------+------+------+------+------+------+
  | 鈴木 | (^^) | (^^) | ('') | (xx) | (^^) |
  +------+------+------+------+------+------+

実際の表示

+------+------+------+------+------+------+
|      | Mon  | Tue  | Wed  | Thu  | Fri  |
+======+======+======+======+======+======+
| 田中 | (^^) | (xx) | (xx) | ('') | (^^) |
+------+------+------+------+------+------+
| 鈴木 | (^^) | (^^) | ('') | (xx) | (^^) |
+------+------+------+------+------+------+


シンプル
-------------------------------

Table Fromatter書式::

  =
  Input . Output
  -
  A B "A or B" A_and_B
  = = = =
  False False False False
  True False True False
  =

フォーマット後::

  =====  =====  ========  =======
  Input    .     Output
  -----  -----  --------  -------
    A      B    "A or B"  A_and_B
  =====  =====  ========  =======
  False  False  False     False
  True   False  True      False
  =====  =====  ========  =======


実際の表示

=====  =====  ========  =======
Input    .     Output
-----  -----  --------  -------
  A      B    "A or B"  A_and_B
=====  =====  ========  =======
False  False  False     False
True   False  True      False
=====  =====  ========  =======


.. rubric:: 注釈

