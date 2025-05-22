.. post:: 2025-05-23
   :tags: MkDocs, mkdocstrings, Python, ドキュメント, GitHub Pages
   :category: documentation
   :author: mtakagishi
   :language: ja

==========================================================================
MkDocs + mkdocstrings で Python コード連動のドキュメントを公開
==========================================================================

Python のコードから自動で API ドキュメントを生成し、それを MkDocs を使って GitHub Pages 上に公開するまでの体験を行ったので、その手順と感想をまとめておきます。

.. contents::
   :local:
   :depth: 2

概要
====

- 使用ツール: MkDocs, mkdocstrings, Poetry
- 目的: Python コードの docstring を API ドキュメントとして Markdown 上に展開し、公開まで一貫して試すこと
- 成果: 関数の引数・戻り値などが表形式で整然と表示される見やすいドキュメントを作成・公開できた

導入手順
========

1. Poetry プロジェクトの初期化::

    poetry init


2. 必要パッケージの導入::

    poetry add --group docs mkdocs 'mkdocstrings[python]' mkdocs-material

3. MkDocs プロジェクトの初期化::

    poetry run mkdocs new docs

4. `mkdocs.yml` の編集::

    site_name: My Project Docs
    theme:
      name: material
    nav:
      - Home: index.md
      - API: api.md
    plugins:
      - search
      - mkdocstrings:
          default_handler: python

5. API ドキュメント用ファイルを作成（`docs/api.md`）::

    ::: myproject.hello

6. サンプルコードの作成（`myproject/hello.py`）::

    def greet(name: str) -> str:
        """名前に挨拶を返します

        Args:
            name (str): 対象の名前

        Returns:
            str: 挨拶文
        """
        return f"Hello, {name}!"

7. ローカルで確認::

    poetry run mkdocs serve

8. GitHub Pages への公開::

    poetry run mkdocs gh-deploy

感想
====

- docstring が自動で整形され、非常に見やすい表形式で API 仕様が表示されるのが便利
- Markdown ベースで編集できるため、Sphinx よりも導入・修正が簡単に感じた
- コードとの連動性が高く、変更があってもドキュメントにすぐ反映できる安心感がある
- `mkdocstrings` を通じて、型ヒントや Google-style docstring の価値も改めて実感した

今後は、この構成をテンプレート化したり、CI連携で自動更新の仕組みも導入していきたい。

.. rubric:: 記事情報


:著者: mtakagishi
:投稿日: 2025-05-23
