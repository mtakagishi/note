.. post:: 2025-06-02
   :tags: Sphinx, blockdiag, Pillow, Graphviz, 可視化, トラブル対応
   :category: 開発メモ
   :author: mtakagishi
   :language: ja


====================================================
blockdiagの代替手段を模索したが断念した記録
====================================================


sphinxcontrib.blockdiagについて、Pillow 9.5 依存がボトルネックだったので、諸々の移行対応を試みたが、最終的に移行を断念した記録です。

.. contents::
   :local:
   :depth: 2

背景と目的
-----------

`sphinxcontrib.blockdiag` を用いて時系列図を可視化していたサイトを管理していました。
しかし、blockdiag は `Pillow 9.5` に依存しており、以降の Pillow 10.x 以降では非互換となってしまった。

`Pillow 9.5` のインストールも pip 上では終了しており、代替手段を模索する必要が生じた。

試したこと
-----------

1. **Graphvizへの移行を試行**

    - blockdiag の構文を手作業で Graphviz の DOT 記法に変換。
    - `graphviz` ディレクティブを使って `sphinx` 上で描画。
    - しかし、横幅・縦幅の調整に限界を感じた。
    - 各ノードの大きさ指定や折返し等も Graphviz 側では厳しい。

2. **図の分割検討**

    - グループ単位で図を分割し、複数の図に展開する構成を試みる。
    - やはり、横幅・縦幅の調整に限界を感じた。

3. **blockdiag継続のための Pillow 9.5 固定**

    - Pillow 9.5 の公式 wheel 提供が停止されていた。
    - fork による維持を試みた。
    - 公式の `9.5.x` ブランチを fork。
    - `setup.py` の `get_version()` を修正。
    - Poetry の git 依存指定でインストールには成功。
    - しかし、最終的に Sphinx ビルド時に `AssertionError: len(context) = 1` という深刻なエラーが発生。
    - 他のパッケージとの依存関係の複雑さを踏まえこの手も断念。

結論
----------------

- blockdiag による図の可視化は、現時点では維持・移行ともに困難と判断。
- 該当ページの管理をいったん **中断** し、代替の可視化方法やツールが整備されるまで凍結する。


.. rubric:: 記事情報

:著者: mtakagishi
:公開日: 2025-06-02
