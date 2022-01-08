#################################################
Sphinxの立ち上げ（github＋Netlify利用）
#################################################
Last Updated on 2021-08-13

Sphinxを導入し、github/netlify に連携することで簡単に管理できる自前のサイトを構築したので手順をまとめました。


********************************
環境について
********************************
Last Updated on 2021-08-14

本記事執筆時点の作業環境。

OS
======================
Windows10 1909

Python
======================
3.9

cmd::

	python

とすれば、Microsoft Storeからインストールできます。

edtor
======================
VSCODE 1.50.1

cmd::

	code

とすれば、Microsoft Storeからインストールできます。

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


********************************
Sphinx
********************************
Last Updated on 2021-08-22

Sphinx初期整備
==============================
Sphinxパッケージ追加::

	poetry add --dev sphinx

Sphinx初期化する。フォルダターゲットはdocsとした::

	portry run sphinx-quickstart docs

docsが初期化されているのでビルドしてみる。

	poetry run sphinx-build docs docs/_build/ja

docs/_build/ja/index.html [#i18n]_ を開くとビルド結果を確認できる

sphinx-autobuildによる効率化
========================================================
sphinx-autobuildを利用すると、ビルドとブラウザ確認を効率化できます

sphinx-autobuild追加::

	poetry add --dev sphinx-autobuild

以降、下記コマンドを一度実行すれば、http://127.0.0.1:8000 でページ確認でき、自動ビルド・自動リロードされる。

	poerty run sphinx-autobuild docs docs/_build/ja

sphinx-autobuild起動の効率化
======================================
起動効率化の方針
------------------------
sphinx-autobuildの存在だけでもとても効率的なのだが『poetry add sphinx-autobuild』を打ち込むのは面倒。そこで `2019年に向けてPythonのモダンな開発環境について考える`_ という記事を参考に下記コマンドで実行する効率化を目指す::

	poetry run doc //NG

結論としてはこのコマンドでの実現はムリだった。poetryで指定できる[tool.poetry.scripts]は引数指定ができない。この仕様は変更予定はなく、今後もメインストリームに組み込まれる予定はないし、プラグイン開発待ちだが時間がかかりそう [#task]_

natさんにより、 `poethepoet`_ という暫定パッケージを開発してくれているのでこれを活用する。4文字ふえるが、目指すは下記でのコマンド起動す::

	poetry run poe doc

暫定パッケージを使うことを以外は `2019年に向けてPythonのモダンな開発環境について考える`_ と同一方針。詳細はURLを参照してください。

poethepoetを追加::

	poetry add --dev poethepoet

setup.pyの整備
-------------------------

setup.pyを整備します。

.. code-block::
  :caption: setup.py
  :linenos:
  
    import os
    import subprocess
    from setuptools import setup, Command
    
    
    class SimpleCommand(Command):
        user_options = []
    
        def initialize_options(self):
            pass
    
        def finalize_options(self):
            pass
    
    
    class DocCommand(SimpleCommand):
        def run(self):
            subprocess.call(["sphinx-autobuild", "docs", "docs/_build/ja"])
    
    
    setup(
        cmdclass={
            "doc": DocCommand,
        },
    )


上記setup.pyにより、下記コマンドから実行されるようになる::

	poetry run setup.py doc

pyproject.tomlの整備
-------------------------

.. code-block:: toml
	:caption: pyproject.toml
	:linenos:

	[tool.poe.tasks]
	  doc = "python setup.py doc"

ここまで整備すると、以下コマンドでsphinx-autobuildが起動するようになります::

	poetry run poe doc


テーマ
============
テーマは `pydata-sphinx-theme`_ を採用。
* conf.pyで下記対応可能

	* github、twitterへのリンク
	* navバーの設定
	* Google Analyticsの設定

* bootstrap4対応
* Pandas、NumPy、など主要パッケージで採用

pydata-sphinx-themeのインストール::

	poetry add --dev pydata-sphinx-theme

conf.pyの整備::

	html_theme = "pydata_sphinx_theme"

その他、詳細は `pydata-sphinx-theme`_ を参照



.. _2019年に向けてPythonのモダンな開発環境について考える: https://techblog.asahi-net.co.jp/entry/2018/11/19/103455



********************************
githubとの連携
********************************
Last Updated on 2021-04-17

特別な対応は特にない。リポジトリを作成してコミットする。

github準備
==============================
* アカウント取得
* リポジトリ作成：netlify連携のためPublicで作成
* ソースを反映：git initからpushまでのガイドがgithubサイトにあり

githubへssh通信する
==========================
コマンドラインから対応できると便利なので対応しておく

鍵の生成
------------
生成コマンド::

	ssh-keygen -t rsa
	
.ssh/id_rsa（秘密鍵）/.ssh/id_rsa.pub（公開鍵） が生成される

公開鍵をクリップボードへ
-----------------------------------
win::

	clip < ~/.ssh/id_rsa.pub

mac::

	pbcopy < ~/.ssh/id_rsa.pub

githubへ登録
-------------------
「Add SSH Key」というメニューから、クリップボードの内容を貼り付け

githubの.ssh/config
------------------------

~/.ssh/config::

	Host my.github.com
	    HostName github.com
	    User git
	    Port  22
	    Hostname  github
	    IdentityFile  ~/.ssh/id_rsa
	    TCPKeepAlive    yes
	    IdentitiesOnly     yes

github接続確認
---------------------
確認コマンド::

	ssh -T git@my.github.com


(参考)gitlabの場合
==========================
netlifyはgitlabも対応している。gitlabの場合のssh接続確認方法。

gitlabの.ssh/config
---------------------

~/.ssh/config::

	Host my.gitlab.com
	    HostName   gitlab.com
	    User  git
	    Port    22
	    IdentityFile   ~/.ssh/config/id_rsa
	    TCPKeepAlive  yes
	    IdentitiesOnly    yes

gitlab続確認
-------------------

確認コマンド::

	ssh -T git@my.gitlab.com

********************************
netlify連携
********************************
Last Updated on 2021-04-17

netlifyは、githubリポジトリを指定すると、定義したビルドルールに従ってnetlify上の仮想マシンにデプロイして、指定パスをrootとしたサイト公開まで行ってくれます。

netlify連携準備
===================
bulid定義
-------------------
指定したリポジトリにあるnetlify.tomlを読み込んでビルドする仕様になってますので以下を用意します。

.. code-block:: toml
  :caption: netlify.toml
  :linenos:

  [build]
    publish = "docs/_build/ja"
    command = "sphinx-build docs/ docs/_build/ja"

publishが公開するフォルダ。commandがビルド時に使われるコマンドです。

pythonバージョン
-------------------
netlifyでデフォルトで立ち上がる仮想環境は 2020年11月現在、Ubuntu 16.04で、Pythonバージョンは2.7がデフォルトです。バージョンを指定する場合、rutime.txtというファイルにバージョン番号だけ記載しておきます。

.. code-block:: shell
  :caption: runtime.txt
  :linenos:

  3.7

なお、Pythonは、2.7、3.5と3.7を選択できます。これ以外のバージョンは指定してもエラーになります。 [#version]_

netlify github連携
==============================
netlifyにはgithubアカウントでログイン可能です。ログインしビルド対象のリポジトリ連携します。「New Site from git」から特に迷うことなく連携できます。

サイト確認
==============
https://jolly-brown-b98547.netlify.app/ のようなランダムなURLでサイトが公開されます。確認してみましょう

URLを独自ドメインに変更する
===========================================
ドメインを取得してURLを変更することが可能です。

ドメイン取得
-----------------
お試し用には無料で取得できる `freenom`_ で十分です。 [#domain]_

ドメインの設定
--------------------
公式サイトの「Configure an apex domain」という手順 [#dns]_ を参考に設定します。

ドメインプロバイダからは、netlifyが指定するDNSを設定しておき、netlifyDNS側で、Netlifyレコードという特殊なDNSレコードを設定します。

あるいは、ドメインプロバイダー側のDNSにAレコードとしてルートをNetlifyのLBのIPを直接指定、CNAMEレコードをwwwからapexサブドメインへ設定しても動作します。

独自ドメインで確認
=======================
設定したURLにアクセスして確認します。httpsまで設定されてれば成功です。上手くいかない場合は、netlifyの管理画面でエラー状況を確認できますので対処しましょう。

.. rubric:: 関連リンク

.. _poethepoet: https://github.com/nat-n
.. _pydata-sphinx-theme: https://pydata-sphinx-theme.readthedocs.io/en/latest/
.. [#i18n] jaフォルダについて。個人的にi18nを体感するためにjaフォルダとして分離した。英語版は docs/_build/en にビルドされることを想定。現実には個人ブログで多言語化は考慮不要。
.. [#task] https://github.com/python-poetry/poetry/pull/591#issuecomment-504762152

.. _freenom: https://www.freenom.com/ja/index.html
.. [#version] https://github.com/netlify/build-image/blob/xenial/included_software.md
.. [#dns] https://docs.netlify.com/domains-https/custom-domains/configure-external-dns/
.. [#domain]  当サイトはfreenomで試行後、googleドメインでドメイン取得し直しました。



.. |date| date::