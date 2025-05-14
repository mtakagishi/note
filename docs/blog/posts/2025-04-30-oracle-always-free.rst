.. post:: 2025-04-30
  :tags: oracle, free-tier, linux, ssh
  :category: 環境構築
  :author: mtakagishi
  :language: ja

================================================================================
Oracle Cloud で 無料 Linux 環境を手に入れる
================================================================================

Oracle Cloud Free Tierで無料インスタンスを作成し、WindowsからSSH接続するまでの手順を記録します。

.. contents::
   :local:
   :depth: 2

概要
====

クラウド上に **無料** で使える Linux サーバを確保し、環境構築のたびに発生する手間を最小化するための記録です。頻繁に行わない作業ほど手順を忘れがちなので、この記事を備忘録として残します。

目的
====

- 無料で Ubuntu 24.04 環境を手に入れる
- Windows から SSH で接続できることを確認する

前提
====

- Oracle Cloud アカウント（Free Tier）を保持している

新規インスタンス作成
====================

Basic Information
-----------------

- **Name** : ``oracle-private``
- **Image**: *Canonical Ubuntu 24.04 Minimal*
- **Shape**: VM.Standard.A1.Flex (OCPU = 1, Memory = 1 GB)
- **Always Free–eligible** という表記があることを確認

Networking & SSH
----------------

#. *Add SSH keys* で **Generate SSH key pair** を選択
#. ローカルに ``ssh-key-{日付}.key`` (秘密鍵) と ``ssh-key-{日付}.key.pub`` (公開鍵) を保存
#. .ssh フォルダに ``ssh-key-{日付}.key`` を移動し、パーミッションを変更

.. note::

   鍵ファイルは後でダウンロードできないので忘れずに保存します。

パブリック IP の確認
--------------------

インスタンス作成完了後、*Instance Details* 画面に表示される **Public IP** を控えます（以下 ``{ip}`` で表記）。

Windows からの SSH 接続
=======================

.. code-block:: powershell

   ssh -i .\ssh-key-{日付}.key ubuntu@{ip}

パーミッションエラーが出る場合
------------------------------

.. code-block:: text

   Permission 0644 for 'C:\\Users\\me\\.ssh\\sh-key-{日付}.key' are too open.

秘密鍵の属性を ``600`` に変更すると解消できます。

.. code-block:: bash

   chmod 600 ~/.ssh/sh-key-{日付}.key

接続確認
--------

ログイン後に ``uname -a`` が返れば接続成功です。

まとめ
======

- Oracle Cloud **Always Free** を使えば 10 分ほどでパーソナル Linux サーバを構築できる
- SSH 鍵のパーミッション設定に注意
- これでどこからでも同じ開発環境にアクセス可能。今後は Tmux の設定を深掘り予定 🚀

参考リンク
==========

- `Oracle Cloud Always Free FAQ <https://docs.oracle.com/.../free-tier-faq.html>`_
- `公式ドキュメント – SSH の設定 <https://docs.oracle.com/.../ssh-access.html>`_

.. rubric:: 記事情報

:投稿日: 2025-04-01
:著者: mtakagishi
