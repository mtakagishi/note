********************************
githubとの連携
********************************
Last Updated on 2021-04-17

特別な対応は特にない。リポジトリを作成してコミットする。

github準備
==============================
* アカウント取得
* リポジトリ作成：netlify連携のためPublicで作成
* ソースを反映：git initからpushまでのガイドがgithubサイトにあり

githubへssh通信する
==========================
コマンドラインから対応できると便利なので対応しておく

鍵の生成
------------
生成コマンド::

	ssh-keygen -t rsa
	
.ssh/id_rsa（秘密鍵）/.ssh/id_rsa.pub（公開鍵） が生成される

公開鍵をクリップボードへ
-----------------------------------
win::

	clip < ~/.ssh/id_rsa.pub

mac::

	pbcopy < ~/.ssh/id_rsa.pub

githubへ登録
-------------------
「Add SSH Key」というメニューから、クリップボードの内容を貼り付け

githubの.ssh/config
------------------------

~/.ssh/config::

	Host my.github.com
	    HostName github.com
	    User git
	    Port  22
	    Hostname  github
	    IdentityFile  ~/.ssh/id_rsa
	    TCPKeepAlive    yes
	    IdentitiesOnly     yes

github接続確認
---------------------
確認コマンド::

	ssh -T git@my.github.com


(参考)gitlabの場合
==========================
netlifyはgitlabも対応している。gitlabの場合のssh接続確認方法。

gitlabの.ssh/config
---------------------

~/.ssh/config::

	Host my.gitlab.com
	    HostName   gitlab.com
	    User  git
	    Port    22
	    IdentityFile   ~/.ssh/config/id_rsa
	    TCPKeepAlive  yes
	    IdentitiesOnly    yes

gitlab続確認
-------------------

確認コマンド::

	ssh -T git@my.gitlab.com


.. |date| date::


