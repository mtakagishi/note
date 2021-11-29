#################################################
Angularについて
#################################################
Last Updated on 2021-04-17

.. |date| date::

基礎情報
==================================================

* `Wikipedia <https://ja.wikipedia.org/wiki/Angular>`_ 
* `公式ドキュメント <https://angular.jp/docs>`_ 
* SPAフレームワーク
* Angular2.0以降（AngularJS ≠ Angular）
* Google＋コミュニティにてメンテ
* 年2回のアップデート

必要知識
==================================================
* JavaScript
* HTML
* CSS
* Nodejs
* npm package manager

.. hint:: TypeScriptの知識は役に立つが必須でない

Angular CLIのインストール
==================================================

以下のコマンドを実行::

  sudo npm install -g @angular/cli

Angular CLIのアップグレード方法
==================================================

Angular CLIのアップグレードしたいときのコマンド::

  sudo npm uninstall -g angular-cli @angular/cli
  npm cache clean --force
  sudo npm install -g @angular/cli

Angular初期化
==================================================

以下でmy-appを作ってみる::

  ng new my-app

Angular実行
==================================================

実行すると4200ポートで初期画面を表示::

  cd my-app
  ng serve --open

.. figure:: /ex/angular/welcome.png

NextStepsのコマンド群
=================================================
上記画像の、NextStepsにある各ボタンには、それぞれのコマンドが表示される。

新規コンポーネントの作成::

  ng generate component xyz

AngularMaterialのインストール::

  ng add @angular/material

AngularPWAのインストール::

  ng add @angular/pwa

.. note::

  PWAは「Progressive Web Apps」のこと。スマートフォンで動作可能なネイティブアプリと遜色ないWebサイト。 `Googleチェックリスト <https://web.dev/pwa-checklist/>`_ がある。

依存モジュールのインストール::

  ng add ______

テストの実行・常駐::

  ng test

本番向けビルド::

  ng build --prod

公式ドキュメントのセットアップとしては以上。引き続き概念の解説やチュートリアルが用意されている。
