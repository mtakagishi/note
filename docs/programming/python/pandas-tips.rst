.. _pandas-tips:

Pandas Tips: 便利な使い方とテクニック
====================================

NAという文字列をNAとして扱う
----------------------------

.. code-block:: python

  keep_default_na=False

Windowsで改行をLFにしたい
--------------------------

.. code-block:: python

  line_terminator='\n'

Shift_JISで扱いたい
--------------------

.. code-block:: python

  encoding='cp932'

CSVのformat
------------

.. code-block:: python

  quoting=csv.QUOTE_ALL
  quoting=csv.QUOTE_MINIMAL
  quoting=csv.QUOTE_NONNUMERIC
  quoting=csv.QUOTE_NONE

重複行の削除
------------

.. code-block:: python

  df.drop_duplicates()

カラムに列追加
--------------

.. code-block:: python

  df['name_state'] = df['name'].str.cat(df['state'], sep=' in ')

カラムのリネーム
---------------

.. code-block:: python

  df_new = df.rename(columns={'A': 'Col_1', 'C': 'Col_3'})

表の結合
--------

.. code-block:: python

  print(df_ab.merge(df_ac))
  print(pd.merge(df_ab, df_ac, on='a'))
  print(pd.merge(df_ab, df_ac, on='a', how='outer'))

where句のように一致列で絞り込み
-----------------------------

.. code-block:: python

  print(df['state'] == 'CA')

文字列検索
---------

.. code-block:: python

  # 特定の文字列を含む
  print(df[df['name'].str.contains('li')])

  # 特定の文字列で終わる
  print(df[df['name'].str.endswith('li')])

  # 特定の文字列で始まる
  print(df[df['name'].str.startswith('li')])

  # 正規表現のパターンに一致する
  print(df[df['name'].str.match('li')])

省略表示の制御
--------------

.. code-block:: python

  pd.set_option('display.max_rows', 500)
  pd.set_option('display.max_columns', 500)
  pd.set_option('display.max_seq_items', 500)

オプションのリセット
--------------------

.. code-block:: python

  pd.reset_option('display.max_seq_items')

条件に応じた値の変更
--------------------

.. code-block:: python

  df.loc[df['A'] < 0, 'A'] = -10

小数点以下の切り上げ
--------------------

.. code-block:: python

  # float計算値をintに変換したものとの差が0以上のもの1プラスする

to_csvで分割
------------

.. code-block:: python

  k = 10000  # 1DataFrameあたりの行数
  dfs = [df.loc[i:i+k-1, :] for i in range(0, len(df), k)]
  for i, df_i in enumerate(dfs):
    fname = str(i) + ".csv"
    df_i.to_csv(fname)
