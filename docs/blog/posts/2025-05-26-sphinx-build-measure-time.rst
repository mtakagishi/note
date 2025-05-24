.. post:: 2025-05-26
   :tags: Sphinx, Windows, Linux, PowerShell, timeコマンド, パフォーマンス
   :category: sphinx
   :author: mtakagishi
   :language: ja

=============================================================
Sphinxビルド時間の計測手段（timeコマンドとMeasure-Command）
=============================================================

Sphinxで多言語サイトを構築・運用していると、ドキュメントビルドの所要時間が徐々に伸びてくることがあります。性能改善の第一歩として重要なのが、 **現状のビルド処理にどの程度時間がかかっているのか** を把握することです。

本記事では、Sphinxビルドの処理時間を簡易に測定するための基本的な方法についてまとめます。

.. contents::
   :local:
   :depth: 2


Linux/macOSの場合: ``time`` コマンド
=======================================

LinuxやmacOSなどのUnix系環境では、以下のように ``time`` コマンドを使うことで、任意のコマンドの実行にかかった時間を簡単に測定できます。

.. code-block:: bash

   time sphinx-build -E -a -b html ./source ./build _build/ja -D ja

実行後に表示される例：

.. code-block:: text

   real    0m12.345s
   user    0m10.678s
   sys     0m1.234s

- ``real`` は実際に経過した時間（壁時計時間）
- ``user`` はユーザ空間で使ったCPU時間（Python処理など）
- ``sys`` はシステム空間で使ったCPU時間（ファイルI/Oなど）

この手法は、複雑な準備なしで全体所要時間を知ることができ、最も手軽です。

----

Windowsの場合: ``Measure-Command`` （PowerShell）
=====================================================

Windows環境では、``time`` コマンドは利用できません。代わりに、PowerShellの ``Measure-Command`` を使って処理時間を計測します。

.. code-block:: powershell

   Measure-Command { sphinx-build -E -a -b html ./source ./build _build/ja -D ja }

実行結果の例：

.. code-block:: text

   TotalSeconds      : 10.657

このように ``TotalSeconds`` や ``TotalMilliseconds`` の項目で、コマンドの実行にかかった時間を確認できます。

----

補足：Pythonコードに計測を埋め込む方法
=======================================

OSに依存しない方法として、Pythonコード内で ``time`` モジュールを使って処理時間をログ出力するのも有効です。

.. code-block:: python

   import time

   start = time.time()
   # 処理...
   elapsed = time.time() - start
   print(f"処理時間: {elapsed:.2f}秒")

Sphinxをカスタムコマンドやsetup.pyから呼び出している場合には、こうした計測を埋め込むことで、言語ごとの時間や各処理の詳細も把握できます。

----

まとめ
======

Sphinxのような静的サイトジェネレーターでは、処理時間の把握が運用改善の第一歩です。以下の方法を状況に応じて使い分けましょう：

- Linux/macOS： ``time`` コマンド（最も簡単）
- Windows： ``Measure-Command`` （PowerShell標準）
- クロスプラットフォーム： Pythonの ``time`` モジュール

今後はこれらの計測結果をもとに、不要なキャッシュの削除や並列ビルドの導入など、段階的な改善へとつなげていく予定です。

.. rubric:: 記事情報

:著者: mtakagishi
:投稿日: 2025-05-26
