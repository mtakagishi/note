マルチ言語対応のSphinxドキュメント作成手順
=============================================

記事更新日：2023/5/3

.. note:: 
  実行環境はWindows10

1. 必要なパッケージをインストールする
---------------------------------------

.. code-block:: bash

   pip install sphinx
   pip install sphinx-intl

2. Sphinxプロジェクトを作成する
---------------------------------------

.. code-block:: bash

   sphinx-quickstart

3. conf.pyファイルを開いて、言語とロケールの設定を追加・変更する
------------------------------------------------------------------

まず、言語設定を追加して、デフォルトの言語を指定します。例えば、デフォルト言語を日本語に設定する場合、以下のようにします。

.. code-block:: python

   # conf.py
   language = 'ja'

次に、他の言語の設定を追加します。言語ごとに専用のディレクトリを作成し、その中に翻訳済みのドキュメントを格納します。

.. code-block:: python

   # conf.py
   locale_dirs = ['locale/']
   gettext_compact = False

4. デフォルト言語の.potファイルを生成する
------------------------------------------------------------------------

.. code-block:: bash

   make.bat gettext

.. tip:: 
  pot は ``Potable Object Template`` 


5. 生成された.potファイルを、各言語の.poファイルに変換する
-----------------------------------------------------------------

英語、スペイン語、アラビア語、ドイツ語を対象とする場合は次のように記述します。

.. code-block:: bash

   sphinx-intl update -p _build/gettext -l en -l es -l ar -l de

.. tip:: 
  .po ファイルのPOは``Portable Object``、 .mo ファイルのMOは``Machine Object``


6. .poファイルを編集して翻訳を追加する
----------------------------------------------

例えば、``locale/ja/LC_MESSAGES/index.po``を開いて日本語翻訳を追加します。

7. 翻訳済みのドキュメントをビルドする
----------------------------------------------

.. code-block:: bash

  sphinx-build -b html . _build/html/ja
  sphinx-build -b html . _build/html/en -D language=en
  sphinx-build -b html . _build/html/es -D language=es
  sphinx-build -b html . _build/html/ar -D language=ar
  sphinx-build -b html . _build/html/de -D language=de

.. tip:: 
  sphinx-build のビルドオプションは ``-M`` と ``-b`` があり、``-b`` を使う。``-M`` を用いるとoutputフォルダの下に独自にhtmlフォルダが作成されるため同じサイトにデプロイしたい場合には不便。


8. 言語ごとのビルド済みHTMLファイルが``_build/html``ディレクトリに格納されていることを確認する
------------------------------------------------------------------------------------------------------------------------

これで、Sphinxを使って複数言語に対応するドキュメントが作成できました。言語間のリンクやナビゲーションを追加するには、テンプレートをカスタマイズする必要があります

.. rubric:: 参考URL
* `Sphinxドキュメントの国際化対応をやってみた <https://dev.classmethod.jp/articles/sphinx-i18n/>`_ 
* `国際化対応済みのSphinxドキュメントに言語切り替えボタンを実装する <https://dev.classmethod.jp/articles/implement-sphinx-i18n-switch-button/>`_ 
