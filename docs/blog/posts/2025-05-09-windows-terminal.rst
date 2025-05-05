.. post:: 2025-05-09
   :tags: Windows, WSL, Terminal, 開発環境, コンソール
   :category: 開発環境構築
   :language: ja
   :title: Windows Terminal + WSL メモ

Windows Terminal + WSL　メモ
====================================================

Windows Terminal + WSLの利用の自分用メモです。

WSL + Terminal で実現できること
---------------------------------

- Linux コマンドライン環境に即座にアクセスできる。
- TrueColor や Nerd Font 対応により neovim や tmux の画面が美しく表示される。
- Windows ↔ Linux 間のファイル操作がスムーズ。
- 分割ペインやタブの活用により作業が快適に。

Windows Terminal のインストール
-----------------------------------------

microsoft store からインストール

WSL のインストール
--------------------

.. code-block:: bash

  wsl --install

設定ファイルの場所と編集方法
-------------------------------

* `Ctrl + ,` で GUI 設定画面を表示し、右上の「設定ファイルを開く」
* `Ctrl + Shift,` で JSON 設定ファイルを直接編集

.. note:: 
  開始ディレクトリが ``%USERPROFILE%`` 


Windows ↔ Linux 間のファイルアクセス
------------------------------------------

WSL に保存したファイルを Windows 側から操作したい場合、以下のパスが便利です：

.. list-table:: Windows ↔ Linux 間のファイルアクセス
   :header-rows: 1

   * - 操作
     - 説明
   * - Windows → WSL
     - \\wsl$\Ubuntu\home\<user> をエクスプローラで開く
   * - WSL → Windows
     - /mnt/c/Users/<username>/ でWindowsのファイルへアクセス可能


キーボードショートカット（デフォルト）
-------------------------------------------

Windows Terminal のショートカットには、作業効率を向上させる便利な操作が多数あります。とくに **ペインの分割と移動** は、リモート作業における複数のセッション管理で役立ちます。

.. list-table:: よく使うキーボードショートカット
   :header-rows: 1

   * - 操作
     - キー
   * - 新しいタブを開く
     - Ctrl + Shift + T
   * - ペインを横に分割
     - Alt + Shift + -
   * - ペインを縦に分割
     - Alt + Shift + +
   * - ペイン間の移動
     - Alt + ← / → / ↑ / ↓
   * - ペインサイズの調整
     - Ctrl + Shift + ← / → / ↑ / ↓


分割ペインを使って、1つのターミナルウィンドウ内で複数のSSH接続やログ確認などを並行して扱えるため、シェル作業の効率が向上します。

まとめ
------

Windows Terminal ＋ WSLで今のところは十分だと思います。

.. rubric:: 記事情報

:投稿日: 2025-05-09
:投稿者: mtakagishi
