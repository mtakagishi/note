.. post:: 2025-05-11
   :tags: zsh, zsh-plugin, dotfiles, shell
   :category: terminal
   :author: MASATO TAKAGISHI
   :language: ja
   :title: 最小構成で導入する Zsh プラグイン

Zsh での最小構成の Zsh プラグイン導入方法を紹介します。
本記事では、プラグインマネージャを使わずに手動で導入し、必須プラグインの構成を整理します。

.. contents::
   :local:
   :depth: 2

概要
====
- Starship を事前に導入済み　⇒ :doc:`2025-05-03-initail-setup-zsh`
- 最低限のプラグインのみ
- `.zshrc` だけで完結

対象プラグイン
==============

以下はすべて **Starship と競合しない** ものです。

- ``zsh-autosuggestions``：過去の履歴などから自動補完を提示
- ``zsh-syntax-highlighting``：入力中のコマンド構文を色分け
- ``zsh-completions``：公式以外の補完も含めて強化

プラグインの手動導入
=====================

以下のコードを ``.zshrc`` に記述することで、**初回のみ clone し、2回目以降はスキップ** できます。

.. code-block:: zsh

    ZSH_PLUGIN_DIR="$HOME/.zsh/plugins"
    mkdir -p "$ZSH_PLUGIN_DIR"

    install_zsh_plugin() {
      local name=$1
      local url=$2
      local dir="$ZSH_PLUGIN_DIR/$name"
      if [ ! -d "$dir" ]; then
        echo "[INFO] Installing $name ..."
        git clone --depth=1 "$url" "$dir"
      fi
    }

    install_zsh_plugin "zsh-autosuggestions" "https://github.com/zsh-users/zsh-autosuggestions"
    install_zsh_plugin "zsh-syntax-highlighting" "https://github.com/zsh-users/zsh-syntax-highlighting"
    install_zsh_plugin "zsh-completions" "https://github.com/zsh-users/zsh-completions"

    source "$ZSH_PLUGIN_DIR/zsh-autosuggestions/zsh-autosuggestions.zsh"
    source "$ZSH_PLUGIN_DIR/zsh-completions/zsh-completions.plugin.zsh"
    source "$ZSH_PLUGIN_DIR/zsh-syntax-highlighting/zsh-syntax-highlighting.zsh"

Starship との順序関係
======================

Starship を使っている場合、``.zshrc`` の先頭で初期化する必要があります。

.. code-block:: zsh

    eval "$(starship init zsh)"

    # その後にプラグイン読み込みを行うこと
    source "$ZSH_PLUGIN_DIR/zsh-autosuggestions/zsh-autosuggestions.zsh"
    ...

dotfiles管理として、Git 管理から除外する
=============================================================

プラグインは clone すれば再取得できるため、Git 管理から除外すべきです。

.. code-block:: sh

    # Zsh プラグインは Git 管理対象外
    .zsh/plugins/

まとめ
======

zsh の最小構成のプラグイン導入により補完機能が充実して、コマンドの入力が効率化されます。


.. rubric:: 記事情報

:投稿日: 2025-05-11
:投稿者: mtakagishi
