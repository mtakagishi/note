.. post:: 2025-05-02
   :tags: dotfiles, linux, bare-repo, chezmoi, dev-environment
   :category: 環境構築
   :author: mtakagishi
   :language: ja
   

=====================================================================
Bare‑repo方式ではじめる Linux dotfiles 管理
=====================================================================

本記事ではBare-repo方式でのdotfiles管理について整理します。dotbot / yadm / homeshick / chezmoi などdotfile管理マネージャがありますが、初期ではgitだけで完結する Bare‑repo方式で十分です。いつか、困るようなことがあれば、dotfile管理マネージャ への移行を再検討することにします。

.. contents:: 目次
   :local:
   :depth: 2

はじめに
========
長期的に快適な開発体験を維持するうえで ``dotfiles`` のバージョン管理は
欠かせません。本記事では **Bare‑repo 方式** を用いて最小コストで管理を
始める手順を整理します。

- **対象読者** : 新規 Linux 環境を手に入れたばかりで、まずは手軽に
  dotfiles 管理を始めたい人
- **ゴール**   :

  1. Bare‑repo 方式を使った初期立ち上げができる
  2. 日々の変更を安全に運用できる
  3. 新しいマシンが来ても数コマンドで環境を再現できる
  4. chezmoi への乗り換え判断材料を得る

Bare‑repo 方式とは
===================
ホームディレクトリをそのままワークツリーにし、``$HOME/.dotfiles`` を
**ベアリポジトリ** として扱うシンプルな手法です。利点と欠点を整理すると

.. list-table:: Bare‑repo 方式の概要
   :header-rows: 1
   :widths: 20 40 40

   * - 観点
     - メリット
     - デメリット
   * - 手軽さ
     - Git だけで完結、追加ツール不要
     - コマンドが長くなりがち (alias 推奨)
   * - 可搬性
     - 他環境で ``git clone --bare`` だけで再現
     - OS ごとの分岐やテンプレートは手動管理
   * - セキュリティ
     - 秘密鍵などを除外しやすい (.gitignore)
     - 意図せず公開リポジトリへ push しない注意が必要

Git の基本設定 (初回のみ)
==============================
以下の設定は **一度だけ** 実行しておけば、以降すべての Git リポジトリに反映されます。

.. code-block:: bash

   git config --global user.name "Your Name"
   git config --global user.email "you@example.com"
   git config --global init.defaultBranch main   # 初期ブランチ名を main に統一


初期立ち上げ手順
=================
1. **ベアリポジトリを作成**

   .. code-block:: bash

      git init --bare "$HOME/.dotfiles"

2. **便利エイリアスを用意**

   .. code-block:: bash

      alias dot='git --git-dir=$HOME/.dotfiles/ --work-tree=$HOME'
      echo "alias dot='git --git-dir=$HOME/.dotfiles/ --work-tree=$HOME'" >>~/.bashrc

3. **Git の設定を調整** — git管理外のファイルを非表示にする

   .. code-block:: bash

      dot config --local status.showUntrackedFiles no

4. **最初のコミット & リモート登録**

   .. code-block:: bash

      dot remote add origin git@github.com:<YOUR-USER>/dotfiles.git
      dot add ~/.bashrc ~/.gitconfig
      dot commit -m "Initial commit"
      dot push -u origin main

日々の運用フロー
================
1. 変更確認::

      dot status

2. 差分確認::

      dot diff <file>

3. 追加・コミット・プッシュ::

      dot add <file>
      dot commit -m "Update tmux.conf: enable mouse mode"
      dot push

4. **マシン固有設定の扱い**

   * ``.config/machine-specific/`` などに分離し ``.git/info/exclude`` に登録
   * 代替: *includeIf* 機能でホスト名ごとに読み込む Git 設定を分割

新規環境セットアップ
====================
新しいサーバや WSL に入ったら以下だけで再現できます。

.. code-block:: bash

   git clone --bare git@github.com:<YOUR-USER>/dotfiles.git $HOME/.dotfiles
   alias dot='git --git-dir=$HOME/.dotfiles/ --work-tree=$HOME'
   dot checkout
   dot config --local status.showUntrackedFiles no

.. warning:: ``dot checkout`` で既存ファイルと衝突した場合は上書きされます。
   バックアップが必要なら ``--force`` を付けずにエラー一覧を確認し、
   該当ファイルを退避してから再実行してください。

既存環境の最新化
================
.. code-block:: bash

   dot pull --rebase

Conflicted ファイルがあれば通常の Git と同様に解決します。

その他考慮すべきシーン
======================
* **秘密情報の暗号化** — pass/git‑crypt/sops と組み合わせる
* **GUI アプリの設定ディレクトリが巨大** — シンボリックリンクで一部のみ管理
* **OS・ディストリ別の差分** — Makefile で分岐、または includeIf
* **自動同期** — GitHub Actions + SSH で定期 push/pull

dotfile管理マネージャについて
=============================================
* dotbot / yadm / homeshick / chezmoi などdotfile管理に特化したツールがある
* chezmoi は特に人気

.. note:: 将来的に
   - Mac や Windows (WSL) を含む複数 OS を横断
   - dotfiles に秘密情報が増える
   といったニーズが出たら 管理マネージャ への移行を検討する。

まとめ
======
Bare‑repo 方式は **Git だけ** で始められる最短ルートです。まずは運用に
慣れて “dotfiles を育てる” ことに集中し、複雑化してきたタイミングで
dotfiles管理マネージャへの移行を検討すると学習コストも分散できます。

なお、現状の私のリポジトリURLは以下です。育成中ですが興味があれば覗いてみてください。

* `mtakagishi's dotfiles <https://github.com/mtakagishi/dotfiles>`_ 


参考リンク
==========
* `Atlassian Git Tutorial <https://www.atlassian.com/git/tutorials/dotfiles>`_
* `chezmoi 公式ドキュメント <https://www.chezmoi.io>`_

.. rubric:: 記事情報

:投稿日: 2025-05-02
:投稿者: mtakagishi
