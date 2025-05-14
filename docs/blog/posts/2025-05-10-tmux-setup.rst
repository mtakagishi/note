.. post:: 2025-05-10
   :tags: linux, tmux, terminal, dev-environment, cheat-sheet
   :category: 開発環境
   :language: ja
   :title: tmux 導入メモ

===============
tmux導入メモ
===============

linux環境でセッションが切れても再開できる仕掛けであるtmuxについて導入し利用していきます。インストールと最小限の操作方法をまとめました。

.. contents::
   :local:
   :depth: 2

インストール
============

.. code-block:: bash

   sudo apt update
   sudo apt install -y tmux

バージョン確認：

.. code-block:: bash

   tmux -V

---

最低限おさえておきたい操作
==========================

セッション操作
---------------

- 新規セッション作成: ``tmux``
- 新規セッション作成(名前付き): ``tmux new -s mysession``
- セッション一覧: ``tmux ls``
- セッションへ接続: ``tmux attach -t mysession``
- セッションへ接続(簡易版): ``tmux a``
- セッション離脱（デタッチ）: ``Ctrl-b d``
- セッション終了: セッション内で ``exit`` または ``Ctrl-d``
- tmuxの再起動: ``tmux kill-server``

ウィンドウ操作
---------------

- 新規ウィンドウ作成: ``Ctrl-b c``
- ウィンドウ切り替え: ``Ctrl-b n`` （次） / ``Ctrl-b p`` （前）
- ウィンドウ名変更: ``Ctrl-b ,``

ペイン操作
----------
- ペイン分割: ``Ctrl-b %`` （縦） / ``Ctrl-b "`` （横）
- ペインの切り替え: ``Ctrl-b o`` （次のペイン） / ``Ctrl-b ;`` （前のペイン）
- ペインの切り替え: ``Ctrl-b`` + 矢印キー
- ペイン最大化: ``Ctrl-b z`` （再度押すと元に戻る）
- ペインのサイズ調整: ``Ctrl-b`` → ``:`` , ``resize-pane -D/U/L/R``

.. note::
   - ペイン分割のデフォルトキー割り当ては分かりにくい。キー変更は.tmux.conf設定を参照。

---

.tmux.conf の最低限設定
==========================

`"` や `%` によるペイン分割操作を、より直感的な記号に置き換えた設定です。
また、デフォルトの分割キーは無効化しています。

以下を ``~/.tmux.conf`` に記載：

.. code-block:: bash

   bind '\' split-window -h   # 横分割
   bind - split-window -v     # 縦分割
   unbind '"'
   unbind %

この設定により、以下の操作が可能になります：

- ``Ctrl-b \\`` : 横（左右）に分割
- ``Ctrl-b -`` : 縦（上下）に分割

記号の形状から、分割方向が直感的にわかるようになります。

---

まとめ
======

今回の記事では、以下のポイントを紹介しました：

- tmux のインストール
- セッション・ウィンドウ・ペインの基本操作
- `.tmux.conf` による最小限のキーバインド改善

.. rubric:: 記事情報

:投稿日: 2025-05-10
:著者: mtakagishi
