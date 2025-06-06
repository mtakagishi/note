.. post:: 2025-05-14
   :tags: iPad, SSH, iSH, Terminal, Remote-Access
   :category: dev-environment
   :author: mtakagishi
   :language: ja

iPad上でSSH環境を無料で整える方法（iSH + OpenSSH）
==========================================================

**無料アプリ iSH を使って、iPad上にSSH環境を構築する手順** をまとめました。
ここまででLinuxにzsh + neovim + tmux での環境を整えてきたのでSSH接続さえ確立できれば、いつでも作業が可能になります。

.. contents:
   :local:
   :depth: 2

背景と目的
------------

iPadには標準でターミナルが存在しないため、Linux的な作業やSSH経由でのポートフォワーディングを行うには工夫が必要です。
有料アプリ（Blink ShellやTermius Pro）もありますが、**無料で完結したい** という場面では、iSHの活用が有力な選択肢です。

使用するツール
-----------------

- **iSH** （App Storeから無料で入手可能）
- **OpenSSH** （Alpineパッケージとして追加）

iSHはAlpine Linuxに類似した軽量仮想環境であり、パッケージ管理に`apk`を使用します。

導入手順
-----------

1. **iSHをApp Storeからインストール**
2. iSHを起動し、次のコマンドを実行：

   .. code-block:: sh

      apk update
      apk add openssh

   これで `ssh`, `scp`, `sftp` などのコマンドが利用可能になります。

3. SSH接続してみる：

   .. code-block:: sh

      ssh -i .ssh/key user@remote-host

   必要に応じて `.ssh/config` を整備して、接続先を整理することも可能です。

ポートフォワーディング（ローカルトンネル）
----------------------------------------------

iSH内で以下のように実行すれば、iPadローカルでポートフォワーディングが利用できます：

.. code-block:: sh

   ssh -i .ssh/key -L 8080:localhost:8000 user@remote-host

- iPad側の `localhost:8080` にアクセスすると、リモートホストの `localhost:8000` にトンネルされます。

これで、リモートホストで簡易的に動作中のWebサーバにもアクセス可能になります。

viで抜けられないときの対処
----------------------------

iPadなどのタブレットキーボードでは、`vi` などのエディタを起動した際に `ESC` キーが見つからず困ることがあります。
iPadでは次の操作で `ESC` の代用が可能であることを知っておくと良いです。：

- ソフトウェアキーボード： ``Ctrl`` + ``[`` を押す


色や表示のカスタマイズ
-------------------------

iSHはデフォルトでLightモードなので、好みに応じてダークモードへの変更も可能。

画面上部の「歯車アイコン」から変更できます。

まとめ
--------

iSH + OpenSSH を使えば、iPad上でも軽快なターミナル環境が手に入ります。
ポートフォワーディングまで含めた機能を**無料で実現** できる点が魅力です。

接続先のLinux側ではzsh + neovim + tmuxといった環境が整って入れば、外出先で手軽にサイト管理ができそうです。

.. rubric:: 記事情報

:投稿日: 2025-05-14
:著者: mtakagishi
