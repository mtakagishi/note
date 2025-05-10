.. post:: 2025-05-08
   :tags: neovim,vim-plugin, vim-plug, Copilot, 補完, 開発環境
   :category: Neovim設定
   :author: mtakagishi
   :language: ja

Neovimでのプラグイン管理とGitHub Copilot導入メモ
==================================================================

Neovimをインストールした直後の環境に、最小限のプラグインを導入して、自動補完環境を構築した記録です。
最初の段階では `vim-plug` をプラグインマネージャとして採用し、1つ目のプラグインとして GitHub Copilot を導入しました。

.. contents::
   :local:

背景と目的
----------

「Neovim を軽量で自分好みに育てたい」「まずは1つずつプラグインを理解しながら導入したい」という思想のもと、
自動補完に優れた GitHub Copilot を導入しました。

現在は Copilot が無料枠でも使えるようになっており、手軽に試すには最適なプラグインです。

vim-plug の導入
----------------

まずは、プラグイン管理ツール `vim-plug` を導入します。
プラグイン管理ツールとしては他に、luaベースの `lazy.nvim` が急速に発展していることは認識していますが、
vim-plugは10年以上の実績と情報量で仕様も枯れていて、バニラからプラグインを試していくには対応しやすい環境となります。

.. code-block:: bash

   curl -fLo ~/.local/share/nvim/site/autoload/plug.vim --create-dirs \
     https://raw.githubusercontent.com/junegunn/vim-plug/master/plug.vim

init.vim には以下のように記述します：

.. code-block:: vim

   call plug#begin('~/.local/share/nvim/plugged')

   " GitHub Copilot プラグイン
   Plug 'github/copilot.vim'

   call plug#end()

vim-plug の基本コマンドと利用タイミング
------------------------------------------

- ``:PlugInstall`` – プラグインのインストール
- ``:PlugUpdate`` – 既存プラグインの更新
- ``:PlugClean`` – 不要になったプラグインの削除（!付きで確認なし）

初回セットアップ時には ``:PlugInstall`` を実行すればOKです。

自動化したい場合は以下のようのコマンドラインからも実行できるので参考にしてください：

.. code-block:: bash

   nvim --headless +PlugInstall +qall

GitHub Copilot の導入とセットアップ
-----------------------------------

プラグインに Copilot を採用した理由：

- GitHub アカウントがあれば **無料で利用可能**
- Pythonや他言語に対して非常に高精度な補完を提示
- ワンラインではなく、**複数行の関数定義補完も可能**

既に上記 init.vimの記述とPlugInstallの実行で必要ファイルはDLされています。copilotと連携したい場合は、初回にセットアップが必要です：

.. code-block:: vim

   :Copilot setup

表示された URL をローカルのブラウザで開き、認証コードを入力すれば連携完了です。

導入時のエラー対処法
----------------------

- **Node.js が必要**：``Copilot setup`` 時に ``Node.js not found in PATH`` と出たら、node.jsのインストールが必要です。``sudo apt install -y nodejs npm`` でもよいですが、本記事では、nvmでNode.jsをインストールしました。nvmはNode.jsのバージョン管理ツールで、複数のNode.jsを簡単に切り替えられます。

  .. code-block:: bash

     curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh | bash
     export NVM_DIR="$HOME/.nvm"
     . "$NVM_DIR/nvm.sh"
     nvm install --lts

  また、次回以降のログインでもNode.jsが使えるように、以下を ``.bashrc`` または ``.zshrc`` に追記しておきます：

  .. code-block:: shell

     export NVM_DIR="$HOME/.nvm"
     [ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"

- **SSH接続環境でブラウザが開けない** ： ``:Copilot setup`` 実行時に表示されるコードとURLをコピーし、
  ローカルPCのブラウザで以下のURLを開きます：

  - URL： https://github.com/login/device

  ブラウザで表示された入力欄に、Neovimで表示された認証コード（例: ``ABCD-EFGH`` ）を入力すればOKです。

- **認証コードが通らない** ：期限切れの場合があるため、再度 ``:Copilot setup`` を実行

- **SSH接続環境で'xdg-open'エラーは無視** ：
  Error SERVER_REQUEST_HANDLER_ERROR:
  Vim:E475: Invalid value for argument cmd: 'xdg-open' is not executable
  は、無視して問題ない

- **Setupが完了したことを確認する** ：
  Neovimを再起動し、以下のコマンドを実行してみます：

  .. code-block:: vim

     :Copilot status

  これで、 ``Ready`` と表示されていれば、Copilotとの連携が完了しています。

今後の補完プラグイン導入に向けた注意点
---------------------------------------

多くの補完エンジン（例：``nvim-cmp``）は、補完候補の選択や確定に ``<Tab>`` キーを利用します。
一方で GitHub Copilot もデフォルトで ``<Tab>`` による補完受け入れを設定しているため、
両者が同時に有効になると **キー操作の競合が発生** してしまいます。

将来的な拡張を見据えて、あらかじめ Copilot のキーマッピングを変更しておくことで、
他の補完エンジンと共存しやすくなります。

以下を ``init.vim`` に追記しておくことで、Copilot の補完受け入れを ``<C-J>`` （Ctrl+J）に変更できます：

.. code-block:: vim

   let g:copilot_no_tab_map = v:true
   imap <silent><script><expr> <C-J> copilot#Accept("\<CR>")

.. attention::
  この設定を適用する場合は、Copilot の補完受け入れキーを `<C-J>` したことを忘れないようにしましょう。

まとめ
------

- `vim-plug` にて、いちからvimプラグインを試せる環境を構築。
- Copilot を導入するだけでも十分強力
- 今後も様々なプラグインを試すことを考慮しキーマッピングを調整


.. rubric:: 記事情報

:投稿日: 2025-05-08
:投稿者: mtakagishi
