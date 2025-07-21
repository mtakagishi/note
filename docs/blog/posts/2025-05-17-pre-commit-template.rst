.. post:: 2025-05-17
   :tags: pre-commit, lint, formatter, config, python, yaml
   :category: dev-environment
   :author: mtakagishi
   :language: ja

pre-commit フックの設定網羅テンプレート
==================================================================================

本記事では、Git のコミット前に自動実行できる `pre-commit` のフックを幅広く網羅し、設定例（テンプレート）として整理しておきます。
「まずはすべて入れて、不要なものを削る」という使い方を想定しています。

.. contents::
   :local:
   :depth: 2

YAML 設定ファイルの例
----------------------

以下は、`.pre-commit-config.yaml` に記述するテンプレートです。

.. code-block:: yaml

   default_language_version:
     python: python3.11

   repos:
     # 基本チェック
     - repo: https://github.com/pre-commit/pre-commit-hooks
       rev: v4.5.0
       hooks:
         - id: end-of-file-fixer
         - id: trailing-whitespace
         - id: check-yaml
         - id: check-json

     # Python用フォーマッタ／Lint
     - repo: https://github.com/psf/black
       rev: 24.3.0
       hooks:
         - id: black

     - repo: https://github.com/pre-commit/mirrors-isort
       rev: v5.12.0
       hooks:
         - id: isort

     - repo: https://github.com/pycqa/flake8
       rev: 6.1.0
       hooks:
         - id: flake8

     - repo: https://github.com/asottile/pyupgrade
       rev: v3.15.0
       hooks:
         - id: pyupgrade
           args: ["--py310-plus"]

     # reStructuredText / Markdown チェック
     - repo: https://github.com/myint/rstcheck
       rev: v6.2.4
       hooks:
         - id: rstcheck

     - repo: https://github.com/ducu37/markdownlint
       rev: v0.0.5
       hooks:
         - id: markdownlint

     - repo: https://github.com/PyCQA/doc8
       rev: 1.1.2
       hooks:
         - id: doc8

     # YAML / TOML
     - repo: https://github.com/pre-commit/mirrors-yamllint
       rev: v1.32.0
       hooks:
         - id: yamllint

     - repo: https://github.com/pappasam/toml-sort
       rev: 0.22.1
       hooks:
         - id: toml-sort
           args: ["--all", "--write"]

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
              - pandas
              - numpy
              - pydantic
              - pydantic-settings

     # セキュリティチェック
     - repo: https://github.com/PyCQA/bandit
       rev: 1.7.6
       hooks:
         - id: bandit
           args: ["-ll", "-r", "src"]

     - repo: https://github.com/zricethezav/gitleaks
       rev: v8.18.1
       hooks:
         - id: gitleaks

     # Shellスクリプト
     - repo: https://github.com/koalaman/shellcheck-precommit
       rev: v0.9.0
       hooks:
         - id: shellcheck

     # スペルチェック
     - repo: https://github.com/lucasdemarchi/codespell
       rev: v2.2.6
       hooks:
         - id: codespell

     # Terraform / Docker (optional)
     - repo: https://github.com/antonbabenko/pre-commit-terraform
       rev: v1.79.0
       hooks:
         - id: terraform_fmt
         - id: terraform_validate

     - repo: https://github.com/hadolint/hadolint
       rev: v2.12.0
       hooks:
         - id: hadolint

pyproject.toml オプション設定例
----------------------------------

オプション設定は `pyproject.toml` に設定します：

.. code-block:: toml

   [tool.black]
   line-length = 120

   [tool.flake8]
   max-line-length = 120
   max-complexity = 10
   extend-ignore = ["E203", "W503"]

   [tool.doc8]
   ignore = ["D001", "D002", "D004"]

   [tool.rstcheck]
   report_level = "WARNING"


このテンプレートをベースに、必要な項目だけを選び、実プロジェクトに合わせてカスタマイズしてみてください。

.. rubric :: 記事情報

:投稿日: 2025-05-17
:更新日: 2025-07-27
:著者: mtakagishi
