.. post:: 2025-05-20
   :tags: tmux, Terminal, ssh, copy-mode, cheat-sheet
   :category: Terminal
   :author: mtakagishi
   :language: ja

tmuxでvi操作でコピーするcopy-modeまとめ
============================================================
SSH経由でリモートのUbuntuに接続し、tmux上で作業しているときに、
**Vimのような操作感でコピーができる** ととても便利です。
本記事では、tmuxでの `copy-mode` を使って、**マウスを使わずにキーボードだけで文字列を選択・コピーする方法** を紹介します。

.. contents::
    :local:
    :depth: 2


前提環境
--------

- Windows Terminal（クライアント側）
- SSH接続先は Ubuntu
- tmux バージョン 1.9 以上推奨

tmux 初期設定（.tmux.conf）
---------------------------

以下の内容を `~/.tmux.conf` に記載しておくことで、`vi` 操作とマウス対応が可能になります。

.. code-block::

   # Vim風キーバインドを有効に
   setw -g mode-keys vi

   # マウス操作を有効に（必要に応じて）
   set -g mouse on

設定を反映するには、tmux再起動またはセッション内で次を実行します。

.. code-block:: bash

   tmux source-file ~/.tmux.conf

copy-mode によるキーボードコピー手順
---------------------------------------

1. **copy-modeに入る**

   .. code-block::

      Ctrl + b → [

2. **カーソルを移動する（Vim風）**

   - `h`, `j`, `k`, `l` : 左・下・上・右に移動
   - `w`, `b`           : 単語単位で移動
   - `0`, `$`           : 行頭、行末
   - `g`, `G`           : バッファの先頭、末尾

3. **範囲選択を開始する**

   .. code-block::

      Space

4. **コピーを確定する**

   .. code-block::

      Enter

5. **貼り付ける場合**

   .. code-block::

      Ctrl + b → ]

Windows側へのコピーについて
-----------------------------

tmuxのバッファはUbuntu側にあるため、Windowsのクリップボードに直接コピーはできません。

代替手段:

- **Windows Terminal のマウス選択＋右クリック** でコピー
- `tmux` 上でファイルに書き出し、`scp` や `VSCode Remote` で取得
- Linux側で `xclip` や `wl-copy` を使ってホスト側に送る（GUIがある場合）

まとめ
------

.. list-table::
   :widths: 20 80
   :header-rows: 1

   * - 操作
     - 内容
   * - `Ctrl + b` → `[`
     - copy-mode に入る
   * - Vim操作（`hjkl`, `w`, `b`, など）
     - カーソル移動
   * - `Space`
     - 範囲選択を開始
   * - `Enter`
     - 選択をコピー
   * - `Ctrl + b` → `]`
     - コピー内容を貼り付け（tmux内）

この操作を知って慣れておくと、tmux上での作業効率が上がりそうです。是非慣れていきたい。

.. rubric:: 記事情報

:投稿者: mtakagishi
:投稿日: 2025-05-20
