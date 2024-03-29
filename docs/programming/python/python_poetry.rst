******************************************************
Poetryを使ったパッケージ管理
******************************************************
:更新: 2024-01-03

仮想環境+パッケージ管理ツール

`公式サイト <https://python-poetry.org/>`_ 

インストール
=================

公式HPにインストールコマンドがあるのでターミナルから実行します。

`公式HPのインストール手順へ <https://python-poetry.org/docs/#installation>`_ 

.. hint::
  pipx でのインストールが推奨に切り替わりました。
  Windowsの方でPowershellコマンドでインストールして来た方、pipxでの管理への切替をおすすめします。

基本コマンド
=============
:バージョン確認: poetry --version
:pyproject.toml作成: poetry init
:PKGをinstall: poetry install
:依存PKGを最新化: poetry update
:PKG追加: poetry add [pkg]
:開発用PKG追加: poetry add --dev [pkg]
:GITHUBのPKGを追加: poetry add git+https://github.com/repo/pkg.git
:PKG削除: poetry remove [pkg]


venv設定
====================
:設定確認: poetry config --list
:venv分離設定: poetry config virtualenvs.in-project true

in-projectはTrueにしておくと該当プロジェクトに閉じた影響範囲で管理されます。--localオプションをつけると、poetry.tomlに記録されてgit管理できるようになります。

venv環境を独立するためのconfig確認・設定::

	poetry config --list
	poetry config virtualenvs.in-project true

poetry self update 履歴
==============================================================================
Windows版では、度々self updateがNGになります。pipx版になったことで改善が期待できそうです。
以下は、Powershellコマンドでインストールしていた時代の過去の対処法のメモです。

環境::

  Windows 10 Pro 20H2
  Python 3.9.7

1.1.6⇒1.1.7(2021/08/14)
-------------------------------------------------------
.. error:: 
  | ModuleNotFoundError: No module named 'msgpack.exceptions'

.. hint::
  | 更新手順

  * %USERPROFILE%\.poetry フォルダを削除
  * 推奨手順のインストールを実行

  (Invoke-WebRequest -Uri https://raw.githubusercontent.com/python-poetry/poetry/master/get-poetry.py -UseBasicParsing).Content | python -

1.1.7⇒1.1.8(2021/08/22)
-------------------------------------------------------
.. error:: 
  | ModuleNotFoundError: No module named 'crashtest.inspector'

.. hint::
  | 更新手順 = 前回同様で復旧

.. note:: 
  | issue修正待ちです。
  | https://github.com/python-poetry/poetry/issues/2681

1.1.8⇒1.1.9(2021/09/19)
-------------------------------------------------------
.. hint::
  | 更新手順 = 前回同様で復旧

1.1.9⇒1.1.11(2021/11/2)
-------------------------------------------------------
.. error:: 
  $ ModuleNotFoundError: No module named 'cleo'

.. hint::
  | 更新手順 = 前回同様で復旧

.. hint:: 
  | 2021-12-18 追記
  | Windows版 Python3.10.1において、
  | poetryの依存モジュールがいくつか漏れてるようです。下記コマンドで一次凌ぎ。
  | > pip install cleo tomlkit poetry.core requests cachecontrol cachy html5lib pkginfo virtualenv lockfile
  | https://github.com/python-poetry/poetry/issues/553

1.1.13(2022/3/7)
-------------------------------------------------------
.. hint::
  | 不調のため再インストール
  | 更新手順 = 前回同様で復旧


1.4.2(2023/05/03)
------------------------------
環境::

  Windows 11 Pro 22H2
  Python 3.11.3

.. hint:: 
  | %USERPROFILE%.poetry は存在せず従来手順から変更
  | %APPDATA%\pypoetry が存在するのでこのフォルダを削除する

.. error:: 
  FileNotFoundError: [WinError 3] 指定されたパスが見つかりません。: 'C:\\Users\\username\\AppData\\Roaming\\Python\\Scripts\\poetry.exe'

.. hint:: 
  | このエラーが追加で発生。該当ファイルを手動削除し再実行
  | 再実行しインストール成功
  | 最後に環境変数のPATHに追加　C:\Users\username\AppData\Roaming\Python\Scripts
