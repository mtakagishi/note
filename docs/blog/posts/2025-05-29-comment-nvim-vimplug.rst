.. post:: 2025-05-29
   :tags: Neovim, Vim, Plugin, Lua, Terminal
   :category: 開発環境
   :author: mtakagishi
   :language: ja

Neovimで選択範囲をコメントアウト：comment.nvimをvim-plugで導入する
======================================================================

Neovimを使用していると、特にコードの一定範囲をコメントアウトしたい場面は多いです。
本記事では、Lua製の軽量プラグイン `comment.nvim` を `vim-plug` で導入し、
ファイルタイプに応じたコメントのON/OFFをスムーズに行う方法を紹介します。

.. contents::
   :local:
   :depth: 2

導入手順（vim-plug + init.vim）
--------------------------------

`~/.config/nvim/init.vim` に以下を追記します：

.. code-block:: text

   " comment.nvim を追加
   Plug 'numToStr/Comment.nvim'

   " Luaプラグインの初期化
   lua << EOF
   require('Comment').setup()
   EOF

Neovim を起動後、以下のコマンドを実行します：

.. code-block:: vim

   :PlugInstall

これでプラグインが導入され、有効化されます。

基本的な操作方法
------------------

`comment.nvim` はファイルタイプごとに適切なコメント記号（例: `//` , `#` , `--` , `<!-- -->` など）を自動で使い分けてくれます。

ノーマルモードでの操作:

.. list-table::
   :header-rows: 1

   * - キー
     - 動作内容
   * - ``gcc``
     - 現在行を行コメントトグル
   * - ``gbc``
     - 現在行をブロックコメントトグル

ビジュアルモードでの操作:

.. list-table::
   :header-rows: 1

   * - キー
     - 動作内容
   * - ``gc``
     - 選択範囲の行コメントトグル
   * - ``gb``
     - 選択範囲のブロックコメントトグル

キーバインドの覚え方
---------------------

- ``gc`` →  *go comment* （コメント操作）
- ``gb`` →  *go block* （ブロックコメント）
- ``gcc`` → 現在行の *go comment current*
- Vimの ``g`` プレフィックス文化と一致しており、覚えやすい設計です。

commentstringの確認
---------------------

現在のファイルタイプにおけるコメント記法は以下で確認できます：

.. code-block:: vim

   :set commentstring?

この値をもとに `comment.nvim` は適切なコメント記号を選択しています。

まとめ
--------

- Neovim におけるコメント操作を快適にするには `comment.nvim` が最適
- `vim-plug` でも簡単に導入可能
- ファイルタイプに応じたコメントを自動的に扱ってくれるため、設定いらずで便利
- Vim文化に沿ったキーバインドで覚えやすい

Vim/Neovim を使った開発効率化に、ぜひ導入してみてください。

.. rubric:: 記事情報

:著者: mtakagishi
:投稿日: 2025-05-29.. rubric:: 記事情報
