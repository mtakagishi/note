*****************************
Python環境の準備
*****************************
Last Updated on 2021-08-22

Python仮想環境準備
===========================
Pythonは事前にインストールしておく。今回は、Python環境をキレイに保つために仮想環境で分離。 `poetry`_ を利用しました。

`インストール手順は本家参照 <https://python-poetry.org/docs/#installation>`_ 

.. hint::
  pip install poetry は推奨手順ではないので注意

venv環境を独立するためのconfig確認・設定::

	poetry config --list
	poetry config virtualenvs.in-project true

pyproject.tomlの作成::

	poetry init

仮想環境の作成::

	poetry install

.venvフォルダが作成され、以後、poetry add コマンドでパッケージを追加できます。

Pythonコードも触るかもしれないので下記を念のため追加

	poetry add --dev flake8 autopep8 pylint

.. _poetry: https://python-poetry.org/
.. |date| date::