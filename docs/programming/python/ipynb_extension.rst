*********************************************************
Python実行環境Jupyterの拡張子ipynbについて
*********************************************************
:更新: 2023-05-05

本記事の概要
=================
* 拡張子ipynbはJupyterで使われるファイルで、IPython Notebookが由来です。
* Poetryを活用してJupyterを起動する手順をまとめました。

前提環境
=================
* Windows11
* Pythonインストール済み
* poetryインストール済み

Jupyter開始方法
=================
Jupyterがインストールされていない、起動方法が分からないという想定で記載しています。

.. code-block:: shell
  :caption: 作業ディレクトリへ移動
  
  cd ipynbファイル格納フォルダ


.. code-block:: shell
  :caption: poetry初期化、プロンプト確認事項は全て[Enter]でOK

  poetry config virtualenvs.in-project true
  poetry init

.. code-block:: shell
  :caption: 仮想環境とJupyterのインストール

  poetry install
  poetry add jupyter

.. code-block:: shell
  :caption: jupyter起動

  poetry run jupyter notebook

成功すると次の画像のようにブラウザが立ち上がります。

.. image:: https://pbs.twimg.com/media/FvXB12NaUAIKjPt?format=png&name=small

