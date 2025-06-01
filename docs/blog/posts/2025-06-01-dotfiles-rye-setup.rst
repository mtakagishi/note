.. post:: 2025-06-01
   :tags: dotfiles, rye, Python, シェル環境
   :category: Python開発環境
   :author: mtakagishi
   :language: ja

dotfiles管理における Rye 環境構築の整備ポイント
==================================================

Poetry から Rye への移行を機に、bare-repo方式の dotfiles 管理で
Python 開発環境の構築手順を再整理しました。

この記事では、Rye の導入における dotfiles 側の整備ポイントについてまとめます。

.. contents::
   :local:
   :depth: 2

背景と目的
----------

これまで Python プロジェクトのパッケージ管理には ``poetry`` を使っていましたが、
より軽量かつ高速な ``rye`` へ移行しました。

dotfiles では、複数の開発環境へセットアップを自動で再現できるようにするため、
Rye の導入手順や設定も自動化・明示化しています。

対応方針の概要
----------------

1. ``.rye/`` 配下は原則 dotfiles では管理しない（再現可能な生成物）
2. ``install.sh`` に Rye の導入処理を記述
3. PATH設定・補完設定は ``.zshrc`` などシェル設定ファイルに明示
4. 必要であれば ``.rye/settings.toml`` のみ管理対象とする

具体的な実装内容
------------------

``install.sh`` への追加例
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

    # ~/.config/bootstrap/install.sh の一部
    export RYE_HOME="$HOME/.rye"

    if [ -x "$RYE_HOME/shims/rye" ]; then
        echo "[INFO] Rye is already installed."
    else
        echo "[INFO] Installing Rye..."
        curl -sSf https://rye-up.com/get | RYE_INSTALL_OPTION="--yes" bash
    fi

    echo "[INFO] Installing global tools..."
    rye install ruff doc8 pre-commit doit

``.zshrc`` での設定（dotfiles管理対象）
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

シェルの設定は ``install.sh`` からの自動追記は行わず、
dotfiles で管理している ``.zshrc`` に以下を明示的に記述します。

.. code-block:: shell

    # Rye の shim を PATH に追加
    export PATH="$HOME/.rye/shims:$PATH"

    # Rye の補完を有効化
    eval "$(rye self completion)"

これにより、スクリプトでの動的操作に頼らず、設定が明示的かつ再現可能になります。

``.gitignore`` での除外指定
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: text

    .rye/
    !.rye/settings.toml  # 必要に応じてのみ管理

整備対象と除外対象の整理
-------------------------

.. list-table::
   :header-rows: 1

   * - 項目
     - 管理対象
     - 備考
   * - install.sh
     - ○
     - Rye の導入自動化処理
   * - .zshrc
     - ○
     - PATH や補完設定を明示的に記述
   * - .rye/shims/
     - ×
     - 自動生成される
   * - .rye/venvs/
     - ×
     - 仮想環境。除外必須
   * - .rye/tools/
     - ×
     - 再インストール可能な生成物
   * - .rye/settings.toml
     - △（任意）
     - default-python などの設定用途

まとめ
------

Rye の導入は非常にシンプルで、dotfiles との相性も良好です。

特に ``install.sh`` では導入とツールインストールに徹し、
設定ファイル（``.zshrc`` など）は明示的に管理することで、
再現性・可読性の高い開発環境を構築できます。

Poetry よりも軽量な選択肢として Rye を検討している方には、
dotfiles との組み合わせによる導入をおすすめします。

.. rubric:: 記事情報

:著者: mtakagishi
:公開日: 2025-06-01
