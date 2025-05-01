.. post:: 2025-05-04
   :tags: dotfiles, git, ci, dev-environment
   :category: 開発環境
   :language: ja
   :author: mtakagishi

=====================================================================
Linux環境で自分専用環境を再現する
=====================================================================

Linux新環境で手早く自分専用の環境を立ち上げる手順と考え方をまとめます。

.. contents:: 目次
   :local:
   :depth: 2

------------------------------------------------------------------
環境立上げは、3Stepで完結
------------------------------------------------------------------

実際には3コマンドを実行するだけです。README.mdにも記載して置記、いつでも参照できるようにしています。

1. 必要なパッケージのインストール
2. dotfiles の bare-repo 方式での管理
3. install.sh の実行

内容は以下となります。

.. code-block:: bash

  # 1) 必要なパッケージのインストール
  sudo apt update -y && sudo apt install -y git curl vim

  # 2) dotfiles の bare-repo 方式での管理
  git clone --bare https://github.com/mtakagishi/dotfiles.git $HOME/.dotfiles \
  && git --git-dir=$HOME/.dotfiles --work-tree=$HOME checkout \
  && git --git-dir=$HOME/.dotfiles --work-tree=$HOME \
        config --local status.showUntrackedFiles no

  # 3) install.sh の実行
  bash ~/.config/bootstrap/install.sh


------------------------------------------------------------------
考え方・運用方法の整理
------------------------------------------------------------------

* 立上げ手順に影響せずメンテナンス可能

  * dotfilesはBare-repo方式で管理、育成の都度gitへpush
  * セットアップ手順はinstall.shにまとめる。育成の都度編集しgitへpush
 
------------------------------------------------------------------
CI による品質維持
------------------------------------------------------------------

Github Actions を使って、install.sh の品質を維持します。

* `.github/workflows/dotfiles-ci.yml` という、CIを設定ファイルを追加。
* push や pull_request トリガに加え、週次実行も設定
* 記載内容は、`こちら <https://github.com/mtakagishi/dotfiles/blob/main/.github/workflows/dotfiles-ci.yml>`_ を参照

------------------------------------------------------------------
バッジの追加
------------------------------------------------------------------

README.mdに、CIのバッジを追加して、視覚的に確認できるようにします。

* CIのバッジは、以下のように記載します。

  .. code-block:: markdown

    ![Dotfiles Setup](https://github.com/mtakagishi/dotfiles/actions/workflows/dotfiles-ci.yml/badge.svg)

* バッジの表示は以下のようになります。

  .. image:: https://github.com/mtakagishi/dotfiles/actions/workflows/dotfiles-ci.yml/badge.svg
    :target: https://github.com/mtakagishi/dotfiles/actions/workflows/dotfiles-ci.yml
    :alt: Dotfiles Setup




------------------------------------------------------------------
おわりに
------------------------------------------------------------------

ここでまとめた手順・考え方で、いつでも自分カスタムの環境を再現できます。
また、CIは、git pushトリガと、週次トリガで確認し、バッジで視覚的に確認することで品質を維持することができます。


参考リンク
===========

* `ArchWiki 「Dotfiles — bare-repo 方式」 <https://wiki.archlinux.jp/index.php/ドットファイル>`_ 
* `The bare minimum to keep dot files in git（Liv Blog） <https://liv.pink/post/2022-04-27-the-bare-minimum-to-keep-dot-files-in-git/>`_ 
* `dotfiles CI の具体例（ashishb/dotfiles） <https://github.com/ashishb/dotfiles>`_ 
* `dotload — install.sh <https://github.com/cli-stuff/dotload>`_ 

.. rubric:: 記事情報

:投稿日: 2025-05-04
:投稿者: mtakagishi
