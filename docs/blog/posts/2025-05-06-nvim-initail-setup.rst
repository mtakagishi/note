.. post:: 2025-05-06
   :tags: nvim, 初期設定, linux, editor, setup, dev-environment, sudoedit
   :category: 開発環境
   :language: ja
   :author: mtakagishi

================================================================
Neovimの導入と初期設定、sudoeditとの関連と注意点
================================================================

WindowsでVSCodeという開発スタイルで十分ですが、あえてLinux環境で開発を行うならvi系のエディタを極めるのも一つの選択肢です。
この記事では、Neovimの導入と初期設定を整理します。また、避けるべきsudo nvimコマンドとsudoeditについてもまとめます。

.. contents:: 目次
  :local:
  :depth: 2

1. Neovim のインストール
==========================

以下のコマンドでインストールできます：

.. code-block:: bash

  # Ubuntu / Debian 系

  sudo apt install neovim

  # macOS (Homebrew)

  brew install neovim

  # インストール確認

  nvim --version

2. 設定ディレクトリと構成ファイルの準備
============================================

nvim の設定ファイル置き場は下記です。初期では手動でフォルダとファイルを作成します：

  .. code-block:: bash

    mkdir -p ~/.config/nvim
    touch ~/.config/nvim/init.vim

既に `init.vim` がある場合は、以下のコマンドでコピーします：

  .. code-block:: bash

    mkdir -p ~/.config/nvim
    cp init.vim ~/.config/nvim/

3. 初期 `init.vim` のサンプル
===============================

以下は最低限の使いやすさを備えた `init.vim` の例です：

.. code-block:: vim

  set number              " 行番号を表示
  set relativenumber      " 相対行番号
  set tabstop=4           " タブ幅を4に
  set shiftwidth=4
  set expandtab           " タブの代わりにスペース
  set smartindent         " スマートインデント
  set clipboard=unnamedplus  " クリップボード連携
  set hidden              " 編集中でもバッファ切り替え可

  " --- 検索 ---
  set ignorecase          " 大文字小文字を無視
  set smartcase           " ただし大文字が含まれていたら区別
  set incsearch           " インクリメンタルサーチ
  set hlsearch            " 検索結果をハイライト

  " --- カラースキーム ---
  syntax on
  colorscheme default

  " --- ファイル保存時の自動処理（例：トレーリングスペース削除） ---
  autocmd BufWritePre * :%s/\\s\\+$//e

4. エイリアス
=============================================================

エイリアスの推奨設定
-----------------------

.. code-block:: bash
  
  # ~/.bashrc または ~/.zshrc に追加
  alias vim='nvim'
  alias view='nvim -R'
  alias vimdiff='nvim -d'

.. note:: 
   `vim` や `view` のエイリアスを設定することで、nvim をより快適に利用できます。
   ただし、ここでは、`vi` だけはオリジナルのままにしておきます。純粋に `vi` を使いたいときもあるからです。


5. sudo nvim は 避けるべき
============================================

`sudo nvim` は非推奨
-----------------------

nvim は以下の場所に一時ファイルやセッションファイルを保存します：

.. code-block:: bash

  ~/.local/state/nvim
  ~/.local/share/nvim

ログインユーザの環境下で初のnevimの起動を `sudo nvim` として実行してしまうと、これらのファイルが root 所有になり、以降の通常起動でエラーが発生します。

例：発生するエラー
-----------------------

.. code-block:: vim

  E886: System error while opening ShaDa file /home/user/.local/state/nvim/shada/main.shada for reading: permission denied
  E303: Unable to create directory "/home/user/.local/state/nvim" for swap file, recovery impossible: permission denied
  E303: Unable to open swap file for "test", recovery impossible

対策： `sudoedit` を使う
---------------------------

安全に root 権限のファイルを編集する方法

.. code-block:: bash

  export SUDO_EDITOR=nvim
  sudoedit /etc/your-config.conf

この方法では、nvim はユーザー権限のまま一時ファイルを編集し、保存時に root が上書きします。

所有権の修復が必要な場合
---------------------------

.. code-block:: bash

  sudo chown -R $USER:$USER ~/.local/state/nvim ~/.local/share/nvim


6. まとめ
===========

neovim の導入と初期設定、sudoedit との関連についてまとめました。
今後は、プラグインの導入や設定を進めていく予定です。

.. rubric:: 記事情報

:投稿日: 2025-05-06
:投稿者: mtakagishi
