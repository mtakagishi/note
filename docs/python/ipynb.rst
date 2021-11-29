*********************************************
拡張子ipynbの開き方
*********************************************
Last Updated on 2021-10-26

* ipynb拡張子は、jupyterのファイルです。
* jupyterをインストールしてない端末だったり、jupyterファイルであることを忘れているとハマります。
* ここでは応急処置をまとめました。


前提
=================
* pythonとpoetryコマンドが使える状況
* jupyterがインストールされてない or 開き方がわからない
* 端末のPython環境をあまり汚したくない
* とにかくjupyterで開けば何とかなる。

手順
================
* cd [ipynbファイルのあるフォルダ]
* poetry config virtualenvs.in-project true
* poetry init
* poetry install
* poetry add jupyter
* poetry run jupyter notebook

これで既定のブラウザでjupyterが開くのでipynbが参照できる。

追加モジュールメモ
==========================
numpy pandasも欲しくなるがpython3.9.0では不整合が起きて下記バージョン指定で対応したメモ
* poetry add numpy@^1.19.4 pandas@^1.1.4 matplotlib

pandasメモ
====================
NAという文字列をNAとして扱う
  keep_default_na=False
Windowsで改行をLFにしたい　
  line_terminator='\n'
Shift_JISで扱いたい
  encoding='cp932'
csvのformat
  quoting=csv.QUOTE_ALL
  quoting=csv.QUOTE_MINIMAL
  quoting=csv.QUOTE_NONNUMERIC
  quoting=csv.QUOTE_NONE
重複行の削除
  df.drop_duplicates()

to_csvで分割::
  
  k = 10000  # 1DataFrameあたりの行数
  dfs = [df.loc[i:i+k-1, :] for i in range(0, len(df), k)]
  for i, df_i in enumerate(dfs):
    fname = str(i) + ".csv"
    df_i.to_csv(fname)

.. |date| date::