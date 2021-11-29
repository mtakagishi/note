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
無料で取得できる `freenom`_ を使いました。 [#domain]_

ドメインの設定
--------------------
公式サイトの「Configure an apex domain」という手順 [#dns]_ を参考に設定します。

ドメインプロバイダからは、netlifyが指定するDNSを設定しておき、netlifyDNS側で、Netlifyレコードという特殊なDNSレコードを設定します。

あるいは、ドメインプロバイダー側のDNSにAレコードとしてルートをNetlifyのLBのIPを直接指定、CNAMEレコードをwwwからapexサブドメインへ設定しても動作します。

独自ドメインで確認
=======================
設定したURLにアクセスして確認します。httpsまで設定されてれば成功です。上手くいかない場合は、netlifyの管理画面でエラー状況を確認できますので対処しましょう。


.. _freenom: https://www.freenom.com/ja/index.html

.. [#version] https://github.com/netlify/build-image/blob/xenial/included_software.md

.. [#dns] https://docs.netlify.com/domains-https/custom-domains/configure-external-dns/

.. [#domain]  有料ドメインについてはググってください。

.. |date| date::