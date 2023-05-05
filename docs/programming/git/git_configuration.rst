gitに関するTips集
=====================================
:更新: 2023-05-05

httpでclone後にsshに変更したい
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


コマンドラインでgithubと連携したい
------------------------------------------------

- キーペアを作成する

.. code-block:: sh
  
  ssh-keygen -t ed25519 -C "username@email.com"

- githubにログインして公開キーを登録する。次のコマンドでクリップボードに保存できる。

.. code-block:: sh

  clip < ~/.ssh/id_ed25519.pub

- sshの設定を修正する

.. code-block:: sh
  :caption: ~/.ssh/config::
  
  Host my.github.com
  HostName github.com
  User git
  Port  22
  Hostname  github
  IdentityFile  ~/.ssh/id_ed25519
  TCPKeepAlive    yes
  IdentitiesOnly     yes

- github連携を確認する

.. code-block:: sh

  ssh -T git@my.github.com

githubコマンドエラー関連
-------------------------------------------------

`githubのトラブルシューティング <https://docs.github.com/ja/authentication/troubleshooting-ssh>`_ 

.. note:: 
  ``ssh-keygen -R github.com`` というコマンドで直った経験あり

