.. post:: 2025-05-12
   :tags: oracle-cloud, ssh, tunnel, sphinx, ablog, preview, ubuntu
   :category: ドキュメント管理
   :author: mtakagishi
   :language: ja

=======================================================================
Oracle Cloud上の開発用HTTPサーバにSSHトンネルでアクセスする方法
=======================================================================

Sphinx + ablog による静的サイトを Oracle Cloud 上の Ubuntu サーバで管理しているとき、
``git push`` 前にローカルでの表示確認を行いたいケースがあります。
外部からHTTPで直接アクセスできない状況でも、SSHトンネルを活用すれば開発中のサイトの確認が可能です。

この記事では、Oracle CloudのFree Tierインスタンスに立てたUbuntuサーバ上でHTTPサーバを一時的に起動し、
SSHトンネルで自宅ブラウザから接続・確認する方法を紹介します。

.. contents:
   :local:
   :depth: 2


背景
----

- サーバは Oracle Cloud の Always Free 枠で稼働
- Sphinx + ablog によるドキュメントやブログ記事をメンテナンス中
- ``make html`` 後の ``_build/html`` をブラウザで確認したい
- ただし、開発用ポート（例: 8000）が外部に公開されておらず、直接アクセスできない

実現方法：SSHトンネル
----------------------

SSH接続が可能であれば、SSHの **ポートフォワーディング（ローカルフォワード）** 機能を使って、
サーバ内の ``localhost:8000`` を自宅の ``localhost:8000`` に見せることができます。

1. サーバ側で簡易HTTPサーバを起動
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

   cd ~/my-site/_build/html
   python3 -m http.server 8000

サーバ内から ``curl http://localhost:8000`` で正常に応答することを確認します。

2. クライアント側（Windows）でSSHトンネルを張る
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

PowerShell または コマンドプロンプトで以下を実行：

.. code-block:: bash

   ssh -i path/to/private_key -L 8000:localhost:8000 ubuntu@<サーバのグローバルIP> -N

- ``-i``：秘密鍵の指定
- ``-L``：ローカルポート8000をサーバのlocalhost:8000に転送
- ``-N``：コマンド実行せず、接続だけ行う

成功すれば、**ブラウザで ``http://localhost:8000`` にアクセス** することで、
開発中のHTML出力を確認できます。

備考
----

- SSHトンネルは接続中のみ有効。ターミナルを閉じると切断されます
- PuTTYでも同様の設定が可能（GUIでトンネルを追加）
- Oracle CloudのセキュリティリストやUFW設定を変更せずに利用可能

まとめ
------

本手法により、Sphinx + ablog のサイトを **Gitにpushする前の状態で視覚的に確認できる方法** を整えることができました。

.. code-block:: text

   サーバ：Oracle Cloud Ubuntu (Free Tier)
   確認方法：python3 -m http.server 8000
   アクセス手段：ssh -L 8000:localhost:8000 ... -N
   ブラウザ確認：localhost:8000

外部公開せずに安全に開発環境を構築・確認する方法として、今後も活用できそうです。

.. note::
  Oracle Cloud 側でポート 8001 を外部公開する設定（セキュリティリストやUFWの調整）も試みましたが、
  接続確立できず、原因の特定に至りませんでした。ホスティングが目的ではないので諦めました。


.. rubric:: 記事情報

:投稿日: 2025-05-12
:著者: mtakagishi
