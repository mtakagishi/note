VSCODEでキーボードが効かなくなった場合の対処方法
=======================================================================

VSCODEに以下のようなエラー::

  command 'restructuredtext.editor.listEditing.onEnterKey' not found

そして、エンターキーなどが効かなくなる症状

解決1
--------
:kbd:`Ctrl` + :kbd:`Enter` 

というおまじないで効くようになる場合がある

解決2
------------
* キーボードショートカットの設定を開く

  * ユーザ設定 →　キーボードショートカット

    または

  * :kbd:`Ctl` + :kbd:`K` → :kbd:`Ctl` + :kbd:`S`

* restructuredtext.editor.listEditingで検索
* 効かなかったキーの設定を削除

.. rubric:: 参考URL

https://github.com/vscode-restructuredtext/vscode-restructuredtext/issues/314
