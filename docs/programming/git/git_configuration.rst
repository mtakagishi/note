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

日本語PATHの文字化け回避::

  git config --global core.quotepath false

