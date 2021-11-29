******************************************************
Poetryを使ったパッケージ管理
******************************************************
Last Updated on 2021-09-19

仮想環境+パッケージ管理ツール

`公式サイト <https://python-poetry.org/>`_ 

インストール
=================

公式HPにインストールコマンドがあるのでターミナルから実行します。

`公式HPのインストール手順へ <https://python-poetry.org/docs/#installation>`_ 

.. hint::
  :kbd:`pip install --user poetry`  の利用は非推奨。
  非推奨手順ではself update が利用できない。

2021/04/17実施のインストール記録
---------------------------------------------
実際にインストールした時のログ

インストールコマンド::

  PS C:\WINDOWS\system32> (Invoke-WebRequest -Uri https://raw.githubusercontent.com/python-poetry/poetry/master/get-poetry.py -UseBasicParsing).Content | python -
  Retrieving Poetry metadata
  
  # Welcome to Poetry!
  
  This will download and install the latest version of Poetry,
  a dependency and package manager for Python.
  
  It will add the `poetry` command to Poetry's bin directory, located at:
  
  %USERPROFILE%\.poetry\bin
  
  This path will then be added to your `PATH` environment variable by
  modifying the `HKEY_CURRENT_USER/Environment/PATH` registry key.
  
  You can uninstall at any time by executing this script with the --uninstall option,
  and these changes will be reverted.
  
  Installing version: 1.1.6
    - Downloading poetry-1.1.6-win32.tar.gz (52.15MB)
  
  Poetry (1.1.6) is installed now. Great!
  
  To get started you need Poetry's bin directory (%USERPROFILE%\.poetry\bin) in your `PATH`
  environment variable. Future applications will automatically have the
  correct environment, but you may need to restart your current shell.

.. hint:: 環境変数などは自動で置き換わる。ターミナルは再起動が必要。

基本コマンド
=============
:バージョン確認: poetry --version
:設定確認: poetry config --list
:venv分離: poetry config virtualenvs.in-project true
:新規PKG: poetry new
:pyproject.toml作成: poetry init
:pyproject.tomlベースにinstall: poetry installpo
:依存PKGを最新化: poetry update
:PKG追加: poetry add [pkg]
:開発者PKG追加: poetry add --dev [pkg]
:GITHUBのPKGを追加: poetry add git+https://github.com/repo/pkg.git
:PKG削除: poetry remove [pkg]
:poetry自体のupdate: poetry self update


基本設定
====================
in-projectはTrueにしておくと該当プロジェクトに閉じた影響範囲でパッケージ管理できるのでオススメです。

venv環境を独立するためのconfig確認・設定::

	poetry config --list
	poetry config virtualenvs.in-project true

poetry self update 履歴
==============================================================================
非推奨インストール方法ではself updateがNG。
しかし推奨インストールでもself updateがerrorとなった。
そこで対処法のメモを記録しておく。

環境::

  Windows 10 Pro 20H2
  Python 3.9.7

1.1.6から1.1.7(2021/08/14)
-------------------------------------------------------
.. error:: 
  | ModuleNotFoundError: No module named 'msgpack.exceptions'

.. hint::
  | 更新手順

  * %USERPROFILE%\.poetry フォルダを削除
  * 推奨手順のインストールを実行

  (Invoke-WebRequest -Uri https://raw.githubusercontent.com/python-poetry/poetry/master/get-poetry.py -UseBasicParsing).Content | python -

1.1.7から1.1.8(2021/08/22)
-------------------------------------------------------
.. error:: 
  | ModuleNotFoundError: No module named 'crashtest.inspector'

.. hint::
  | 更新手順 = 前回同様で復旧

.. note:: 
  | issueが出てますね。修正待ちです。
  | https://github.com/python-poetry/poetry/issues/2681

1.1.8から1.1.9(2021/09/19)
-------------------------------------------------------
.. hint::
  | 更新手順 = 前回同様で復旧

1.1.9から1.1.11(2021/11/2)
-------------------------------------------------------
.. error:: 
  $ ModuleNotFoundError: No module named 'cleo'
  が発生するようになったのでアップデート

.. hint::
  | 更新手順 = 前回同様で復旧



.. |date| date::
