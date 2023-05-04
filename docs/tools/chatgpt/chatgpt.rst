.. _autogpt-installation-and-setup:

PoetryでAutoGPTインストールとセットアップ
========================================================

Poetryを使ったAutoGPTのインストールと設定を行いについて説明します。

Poetryを使ったAutoGPTのインストール
----------------------------------------------------------------

1. まだPoetryをインストールしていない場合は、`Poetryの本家サイト <https://python-poetry.org/docs/#installation>`_ を参考にインストールしてください。2023/05/02時点では以下となります:

   .. code-block:: bash
     :caption: Linux, macOS, Windows (WSL):

     curl -sSL https://install.python-poetry.org | python3 -

   .. code-block:: powershell
     :caption: Windows (Powershell):

     (Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | py -

2. AutoGPTリポジトリをクローンします:

   .. code-block:: bash

      git clone -b v0.3.0 https://github.com/Significant-Gravitas/Auto-GPT.git

.. tip:: releaseタグをつけると比較的安定した一式が手に入ります。

3. AutoGPTディレクトリに移動します:

   .. code-block:: bash

     cd autogpt

4. ``pyproject.toml`` に次の内容を追記します。

   .. code-block:: toml
     :caption: 追加toml

     [tool.poetry]
     name = "your_project_name"
     version = "0.1.0"
     description = ""
     authors = ["Your Name <you@example.com>"]
     
     [tool.poetry.dependencies]
     python = "^3.9"
     beautifulsoup4 = ">=4.12.2"
     colorama = "0.4.6"
     distro = "1.8.0"
     openai = "0.27.2"
     playsound = "1.2.2"
     python-dotenv = "1.0.0"
     pyyaml = "6.0"
     readability-lxml = "0.8.1"
     requests = "*"
     tiktoken = "0.3.3"
     gTTS = "2.3.1"
     docker = "*"
     duckduckgo-search = "*"
     # google-api-python-client = "*"
     google-api-python-client = {git = "https://github.com/googleapis/google-api-python-client.git", branch = "main"}
     pinecone-client = "2.2.1"
     redis = "*"
     orjson = "3.8.10"
     Pillow = "*"
     selenium = "4.1.4"
     webdriver-manager = "*"
     jsonschema = "*"
     tweepy = "*"
     click = "*"
     charset-normalizer = ">=3.1.0"
     spacy = ">=3.0.0,<4.0.0"
     en-core-web-sm = {url = "https://github.com/explosion/spacy-models/releases/download/en_core_web_sm-3.5.0/en_core_web_sm-3.5.0-py3-none-any.whl"}
     
     [tool.poetry.dev-dependencies]
     coverage = "*"
     flake8 = "*"
     numpy = "*"
     pre-commit = "*"
     black = "*"
     isort = "*"
     gitpython = "3.1.31"
     auto-gpt-plugin-template = "*"
     mkdocs = "*"
     pymdown-extensions = "*"
     openapi-python-client = "0.13.4"
     pytest = "*"
     asynctest = "*"
     pytest-asyncio = "*"
     pytest-benchmark = "*"
     pytest-cov = "*"
     pytest-integration = "*"
     pytest-mock = "*"
     vcrpy = "*"
     pytest-recording = "*"

.. tip:: バージョンアップに伴い上記内容は変化します。ChatGPTに最新のrequirement.txtの内容を入力しpoetry用に出力させてください。
.. tip::
  ``poetry install`` でエラーが発生する場合は、ChatGPTにエラー内容を貼り付けて対処方法を聞いてください。
  私の場合は ``CalledProcessError`` が発生しましたが、ChatGPTにエラーを質問すると、google-api-python-clientのGitリポジトリのデフォルトブランチがmasterではなく、mainであることを解説するとともに正しい記述方法を教えてくれました。


6. 必要パッケージをインストールします:

   .. code-block:: bash

      poetry install

OpenAI APIキーの取得
----------------------------------------

1. OpenAIのウェブサイトにアクセスします: `https://www.openai.com/ <https://www.openai.com/>`_

2. 右上の「Sign in」ボタンをクリックして、アカウントにログインします。アカウントがない場合は、「Create an account」をクリックして新しいアカウントを作成してください。

3. ログイン後、ダッシュボードにアクセスします。`https://platform.openai.com/ <https://platform.openai.com/>`_

4. 右上のPersonalから「View API Keys」をクリックします。

5. 「API Keys」ページで、「Create new secretkey」ボタンをクリックします。

6. 新しいAPIキーが生成され、表示されます。このAPIキーをコピーし、Pythonプロジェクトで使用してください。

プロジェクトでのOpenAI APIキーの使用
------------------------------------------------------------------

1. ``cp .env.template .env`` とコマンドを入力してファイルをコピーし、 ``.env`` ファイル内の ``OPENAI_API_KEY=`` という文字列の箇所にAPIキーを引用符やスペースなしで入力します。

Custom Search API の設定
------------------------------------------------------------------

Google API の APIキー
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
1. GCPコンソールから、Google API サービスに登録してAPIキーを取得する

2. envファイルの ``GOOGLE_API_KEY=`` という文字列の箇所にAPIキーをセット

CUSTOM SEARCH ENGINE の ID
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

1. `検索エンジン <https://programmablesearchengine.google.com/u/0/controlpanel/all>`_ から新しいエンジンを作成

2. envファイルの ``CUSTOM_SEARCH_ENGINE_ID=`` という文字列の箇所にAPIキーをセット

動作確認
-------------------------------------------------------------

poetry shell としておけば、インストールしたパッケージが利用したPython環境として動作可能です。

  .. code-block:: bash
    :caption: AutoGPTの起動
    
    poetry shell
    ./run.sh


試しに、 ``tell me a single joke`` と打込んで動作を確認しましょう。

  .. code-block:: bash
    :caption: テスト用スクリプト
    
    I Want To AutoGPT to: tell me a single joke

.. rubric:: 参考URL

* `【完全自動型AI】AutoGPTを徹底解剖！使い方をご紹介 <https://bocek.co.jp/media/service/902/>`_ 
* `【さよならChatGPT】過去一ヤバい完全自動AI「AutoGPT」のインストール手順と使い方 <https://youtu.be/31eZz-aqY6E>`_ 
