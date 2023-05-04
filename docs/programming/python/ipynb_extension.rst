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
* poetry config --list
* poetry init
* poetry install
* poetry add jupyter
* poetry run jupyter notebook

これで既定のブラウザでjupyterが開くのでipynbが参照できる。

Recent Changes
--------------

.. git_changelog::