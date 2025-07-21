.. post:: 2025-07-27
   :tags: pre-commit, mypy, update
   :category: 運用改善
   :language: ja

pre-commit テンプレートを更新（mypy 対応と default Python 指定）
==================================================================

以前紹介した pre-commit のテンプレートに対し、以下のアップデートを行った。

:doc:`pre-commit テンプレート <2025-05-17-pre-commit-template>` の内容を更新。

主な変更点
-----------------

1. default_language_version の追加

   Python のバージョンを明示することで、pre-commit が仮想環境構築時に意図しない Python バージョン（例: 3.13）を掴むのを防ぐ。

   .. code-block:: yaml

      default_language_version:
        python: python3.11

2. mypy の pre-commit フック対応

   型チェックを pre-commit に統合することで、ローカル／CI におけるチェックの一貫性を確保。

   また、よく使われる `types-*` 系を `additional_dependencies` に指定している。

   .. code-block:: yaml

      - repo: https://github.com/pre-commit/mirrors-mypy
        rev: 'v1.10.0'
        hooks:
          - id: mypy
            args: [--install-types]
            additional_dependencies:
              - typing-extensions
              - types-requests
              - types-toml
              - types-PyYAML
              - types-setuptools
              - types-python-dateutil
              - pydantic
              - pydantic-settings


.. rubric:: 記事情報

:著者: mtakagishi
:公開日: 2025-07-27
