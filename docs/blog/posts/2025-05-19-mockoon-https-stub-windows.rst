.. post:: 2025-05-19
   :tags: mockoon, stub, api, https, rest, windows
   :category: dev-environment
   :author: mtakagishi
   :language: ja

================================================================
REST APIのStubを手早い立上げにMockoonを使った記録
================================================================

REST APIの本実装が遅れてたり、昔作ったスタブが動かなくなっていたり、ともかく急ぎで、フロントエンド開発や結合テストを行う必要性に迫られるケースという局面に最近よく遭遇します。
とにかく「今すぐ」「最低限のStubが必要」という状況でMockoonが便利そうなので導入手順をまとめました。

.. contents::
   :local:
   :depth: 2


背景と目的
==================

- REST実装が別チーム実装、開発遅れや提供サーバの不具合でREST APIが利用できない
- 早急にHTTPS通信でレスポンスを返すStubが必要
- 本番APIのURLに差し替えるだけで移行できる構成にしたい
- 共同開発者はPythonに不慣れなため、ノーコード・GUIツールが望ましい
- Dockerは利用不可（社内制限あり）

この条件をすべて満たす手段として、**Mockoon** を採用しました。

Mockoonとは
==================

`Mockoon <https://mockoon.com/>`_ は、GUIベースでREST APIのStubを定義できる無料のツールです。

特徴：

- ノーコードでGET/POSTなどのRESTエンドポイントを作成可能
- GUIでの操作が直感的
- HTTPS対応（自己署名証明書の自動生成）
- レスポンスの遅延、ヘッダー、条件分岐なども柔軟に設定可能
- 設定はJSONファイルでエクスポートでき、CLIやチーム内共有にも対応
- ライセンスはMITなのでテスト利用にも適している

導入ステップ（Windows環境）
==============================

1. Windowsの場合Microfost Storeからインストール可能です。他のOSは `公式サイト <https://mockoon.com/download>`_ を参照してください。

2. Mockoonを起動し、「New environment」でStub環境を作成
   - 保存のためのexploreが開くので該当環境を保存するファイル名を指定＝新環境が作成されます
   - ポートを 任意の番号へ 変更（任意）※デフォルトは3001
   - 必要に応じて「Enable HTTPS」を有効化
   - 必要に応じて「Enable CORS」もONにする

3. `+ Add route` で以下のようなStubエンドポイントを作成
   - crudでGET/POST/PUT/DELETEの操作が自動で作成するのは新規APIの調整で便利そうですが、 ここではGET/POSTなどで取り急ぎ立上げたいので「Http Route」を選択
   - /api/test-resource などのエンドポイントを指定
   - メソッドはGET/POST/PUT/DELETE を選択可能
   - レスポンスは固定のJSONを指定できるのでRESTチームと整合したJSONサンプルを指定

4. サーバーを「Start」で起動し、HTTPでアクセス確認
   例：
   ::

     curl -k http://localhost:3001/api/test-resource


所感
==================

flackやFastapiも選択肢として考えましたが、手早く立ち上げるには前提知識やセッティングの手間から考えて、
もう少し便利なものがないかと探していたところ、Mockoonに辿り着きました。
想像以上に便利で手早く立ち上げられるので非常に助かりました。同様のニーズがる方には是非お勧めしたいです。

MITライセンスということなで実プロジェクトでの利用のハードルも低いのも魅力です。Mockoonの開発者の方に感謝です。

.. rubric:: 記事情報

:著者: mtakagishi
:投稿日: 2025-05-19
