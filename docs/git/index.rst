#################################################
git
#################################################
Last Updated on 2021-04-17


基本コマンド
=====================================

:git add .: 変化のあったファイルをすべてステージング（コミット候補）へ
:git commit -m "message": ローカルでにメッセージをつけてコミット
:git push: githubにプッシュ

ブランチ関連
=====================================

:git branch: ローカルブランチの一覧を表示
:git branch -r: リモートブランチの一覧を表示
:git branch -a: 全てのブランチの一覧を表示
:git branch <新ブランチ>: ブランチを作るが切り替えない
:git checkout <新ブランチ>: ブランチを作って切り替える
:git checkout <既存ブランチ>: 既存ブランチに切り替える
:git diff <別ブランチ> --name-only: <別ブランチ>から変更のあるファイル名だけを表示
:git rebase <別ブランチ>: <別ブランチ>の最新内容を取り込む
:git remote prune origin --dry-run: ローカルに残ってしまったリモートブランチの残骸を確認する
:git remote prune origin: ローカルに残ってしまったリモートブランチの残骸を削除する
:git branch -d <削除ブランチ>: ローカルブランチを削除
:git branch -D <削除ブランチ>: ローカルブランチを強制削除

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

.. |date| date::