.. post:: 2025-05-03
   :tags: zsh, starship, linux, shell
   :category: シェル環境
   :language: ja
   :author: mtakagishi

==============================================================================
zsh + starship で始めるモダンシェル環境セットアップ
==============================================================================

新しく入手した Linux を “bash のまま” で妥協しない。zsh と高速・多機能プロンプト starship を導入し、最低限押さえておきたい設定を一気に整えモダンなシェル環境を構築します。

.. contents::
   :local:
   :depth: 2

はじめに
========

クラウドの VM や WSL、Raspberry Pi──どんな Linux を入手しても最初は ``bash`` が標準です。
もちろんそのままでも作業はできますが、zshは拡張性にもすぐれ、MacOSのデフォルトログインシェルに採用されるなど、今後は主流になる可能性を秘めています。
さらに **starship** を組み合わせれば、情報量の多いプロンプトを極小コストで表示でき、どんな言語スタックでも一貫した開発体験が得られます。

本記事では **「最短 30 分で *使える* zsh 環境」** を目標に、

* zsh の導入とログインシェル変更
* 必須 & 人気のプラグイン／設定 (.zshrc)
* starship の概要とインストール
* 最低限知っておきたい starship のカスタマイズポイント

をまとめます。
**コピペで動くコマンド** を中心に書いているので、作業ログ代わりにどうぞ。

前提条件
========

* Linux (Debian/Ubuntu 系を例にしますが、Fedora/Arch でも読み替え可)
* sudo 権限を持つユーザーでログイン済み
* ネットワーク接続

**Tip:** 既存の ``.bashrc`` に独自エイリアスがある場合は終盤で zsh に移植します。忘れずバックアップを取っておきましょう。

Step 0 ─ システムを最新化
=========================

.. code-block:: bash

   sudo apt update && sudo apt upgrade -y   # Debian/Ubuntu
   # sudo dnf update -y                     # Fedora
   # sudo pacman -Syu                       # Arch

Step 1 ─ zsh を導入し、ログインシェルに設定
=============================================

1. **インストール**

   .. code-block:: bash

      sudo apt install -y zsh     # または dnf install zsh / pacman -S zsh

2. **標準シェルを切り替え**

   .. code-block:: bash

      chsh -s "$(command -v zsh)"

   反映には再ログインが必要です。SSH セッションなら ``exit`` →再接続で OK。

3. **初回起動ウィザードはスキップ**
   ``zsh`` を初めて起動すると設定ウィザードが走りますが、ここでは **(q) quit** を選択してスキップします。

Step 2 ─ zsh設定ファイル .zshrc
================================

1. ``~/.zshrc`` を作っておきます。

   .. code-block:: bash

      touch ~/.zshrc   # 空の設定ファイルを作成

2. ``.bashrc`` から **alias/function/export** を中心に移植します。

   .. code-block:: zsh

      # --- alias
      alias ll='ls -alF'
      alias la='ls -A'
      alias l='ls -CF'

Step 3 ─ starship を導入する
=================================

starship は Rust 製の高速プロンプト。git ブランチ、言語バージョン、exit code など “今ほしい情報” を自動で表示します。

1. **インストール**

   .. code-block:: bash

      curl -sS https://starship.rs/install.sh | sh  -s -- -y

   Rust toolchain を入れずとも単体バイナリで動くため軽量です。

2. **Nerd Font をインストール**

   unzip fontconfig が必要です。

   .. code-block:: bash

      sudo apt install -y unzip fontconfig

   フォントフォルダを作成し、Nerd Font をダウンロードします。

   .. code-block:: bash

      mkdir -p ~/.local/share/fonts
      cd ~/.local/share/fonts
      curl -LO https://github.com/ryanoasis/nerd-fonts/releases/latest/download/FiraCode.zip
      unzip FiraCode.zip
      rm FiraCode.zip

   フォントキャッシュを更新します。

   .. code-block:: bash

      fc-cache -fv

   フォントをターミナルから直接表示して確認します。

   .. code-block:: bash

      echo -e "\ufb00 \ufb13 \ue0b0 \uf09b"

   ﬀ や ﬓ などのアイコンが表示されれば成功です。全てが?が表示される場合は、フォントが正しくインストールされていません。

3. **設定ファイルを作成**

   starshipの初期ファイルの空の設定ファイルを作成します。

   .. code-block:: bash

      mkdir -p ~/.config && touch ~/.config/starship.toml


   starship.tomlに以下を書き込みます。 `最新はこちらを確認 <https://starship.rs/config/>`_

   .. code-block:: toml

      # Get editor completions based on the config schema
      "$schema" = 'https://starship.rs/config-schema.json'

      # Inserts a blank line between shell prompts
      add_newline = true

      # Replace the '❯' symbol in the prompt with '➜'
      [character] # The name of the module we are configuring is 'character'
      success_symbol = '[➜](bold green)' # The 'success_symbol' segment is being set to '➜' with the color 'bold green'

      # Disable the package module, hiding it from the prompt completely
      [package]
      disabled = true"

4. **シェルへ組み込み**

   ``.zshrc`` の最後に ``eval "$(starship init zsh)"`` を追記します。

   .. code-block:: zsh

      # --- starship
      eval "$(starship init zsh)"

   zshを再起動して反映します。

   .. code-block:: bash

      exec zsh   # または source ~/.zshrc


まとめ
======

これで zsh + starship によるモダンなシェル環境が使える状態になりました。
今後は、必要に応じてプラグインの追加などについて触れていきます。


.. rubric:: 参考リンク

* zsh 公式ドキュメント — https://zsh.sourceforge.io/
* starship スターターガイド — https://starship.rs/guide/

.. rubric:: 記事情報

:投稿日: 2025-05-03
:著者: mtakagishi
