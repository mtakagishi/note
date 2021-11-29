#################################################
Docker
#################################################
Last Updated on 2021-04-17

プロキシ環境下のdocker-compose
==============================================

通常のdocker-compose::

    build:
      context: .
      dockerfile: Dockerfile
    image: image-name


build句を上記のような記載で、proxy環境下ゆえにでビルド都合が悪い場合の応急対応

* .envファイルを配置。各自のプロキシ事情に沿った情報を記入
* networkはホストPCと共有
* ビルド実行内部の環境変数としてプロキシを設定
* docker-compose up --build -d でリビルド立上げでOK

.. code-block:: ini
  :caption: .env(新規作成)
  :linenos:

  http_proxy="http://yourproxy:port"
  https_proxy="http://yourproxy:port"


.. code-block:: yaml
  :caption: docker-compose(修正例)
  :linenos:
  :emphasize-lines: 4-7

    build:
      context: .
      dockerfile: Dockerfile
      network: host
      args:
        http_proxy: ${http_proxy}
        https_proxy: ${https_proxy}
    image: image-name


.. |date| date::

