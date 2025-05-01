.. post:: 2025-05-01
  :tags: linux, setup, メンテナンス, 初期設定
  :category: 環境構築
  :author: mtakagishi
  :language: ja

============================
Linux環境で行う初回作業
============================

新しくLinux環境を手に入れたとき、毎回行う作業があります。しかし、その作業内容を毎回調べ直すのは非効率です。本記事では、私が行っている初回セットアップと、その後の保守作業についてまとめました。主にUbuntuベースの環境を想定しています。

.. contents::
   :local:
   :depth: 2

rootユーザでの初期作業
============================

最初に、rootユーザまたはsudo権限を持ったユーザで以下の作業を行います。

パッケージの更新
-------------------

.. code-block:: bash

   sudo apt update && sudo apt upgrade -y

基本ツールのインストール
--------------------------------------

開発や設定に必要な最低限のツールをインストールします。

.. code-block:: bash

   sudo apt install -y build-essential git curl vim

日本語フォントのインストール
--------------------------------------

日本語表示に必要なフォントをインストールします。

.. code-block:: bash

   sudo apt install -y fonts-noto-cjk

ロケール設定
--------------------------------------

日本語ロケールを設定します。

.. code-block:: bash

   sudo apt install -y language-pack-ja
   sudo locale-gen ja_JP.UTF-8   
   sudo update-locale LANG=ja_JP.UTF-8
   source /etc/default/locale

設定が反映されているか確認します。

.. code-block:: bash

   locale

出力の一部に以下が含まれていればOKです。

::

   LANG=ja_JP.UTF-8

タイムゾーン設定
--------------------------------------

JST（日本標準時）に設定します。

.. code-block:: bash

   sudo timedatectl set-timezone Asia/Tokyo

確認コマンド：

.. code-block:: bash

   timedatectl

出力例：

::

   Time zone: Asia/Tokyo (JST, +0900)

ファイアウォールの設定
--------------------------------------

基本的なセキュリティ設定を行います。

.. code-block:: bash

   sudo apt install -y ufw
   sudo ufw enable
   sudo ufw allow OpenSSH

確認コマンド：

.. code-block:: bash

   sudo ufw status verbose

出力例：

::

   To                         Action      From
   --                         ------      ----
   22/tcp (OpenSSH)           ALLOW IN    Anywhere
   22/tcp (OpenSSH (v6))      ALLOW IN    Anywhere (v6)

パッケージの定期メンテナンス
--------------------------------------

`cron` で定期的に不要なパッケージの削除を行います。

.. code-block:: bash

   sudo tee /etc/cron.d/apt-autoremove > /dev/null <<EOF
   17 3 1 * *   root   apt update -qq && apt -y autoremove && apt -y clean
   EOF

作業用ユーザの追加と権限設定
--------------------------------------

作業用ユーザを作成し、sudo権限を付与します。

.. code-block:: bash

   sudo adduser your-username
   sudo usermod -aG sudo your-username

ユーザでの初期作業
=========================

ここからは、作成した作業用ユーザ（例: `your-username`）に切り替えて行います。

SSH公開鍵の設定
--------------------------------------

SSHでの接続に備えて、`.ssh/authorized_keys` に公開鍵を配置します。

.. code-block:: bash

   mkdir -p ~/.ssh
   chmod 700 ~/.ssh
   echo "your-public-key" >> ~/.ssh/authorized_keys
   chmod 600 ~/.ssh/authorized_keys

接続確認
--------------------------------------

別マシンからSSH接続できることを確認します。

.. code-block:: bash

   ssh your-username@your-server-ip

まとめ
=============

この記事では、Linux環境で最初に行うべき基本的なセットアップ手順と、最低限のメンテナンスについてまとめました。毎回調べ直す手間を省くため、自分用のリファレンスとして活用していきます。必要に応じて随時更新予定です。

.. rubric:: 記事情報

:投稿日: 2025-05-01
:投稿者: mtakagishi
