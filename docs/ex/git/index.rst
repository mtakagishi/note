#################################################
git
#################################################
Last Updated on 2021-04-17


初心者向け
=====================================

初心者は、以下3つのコマンドから

:git add .: 変化のあったファイルをすべてステージング（コミット候補）へ
:git commit -m "message": ローカルでにメッセージをつけてコミット
:git push: githubにプッシュ

設定関連
=====================================

httpでcloneして後からsshに変更したい場合
-----------------------------------------
状態確認コマンド::

  $ git remote -v
  
変更コマンド::

  $ git remote set-url origin git@github.com:user/repo.git

改行コードワーニング対策
------------------------------------

改行コードのワーニング::

  warning: LF will be replaced by CRLF in …
  The file will have its original line endings in your working directory

このワーニングを回避するには::

  git config --global core.autoCRLF false

gitメモ
  conflict
    競合があるとローカルファイルに競合した箇所が記述されているので手動で直す
  



.. |date| date::