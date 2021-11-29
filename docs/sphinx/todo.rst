===============================
SphinxでTODO管理をする方法
===============================
Last Updated on 2021-08-14

 sphinxで作ったサイトで、書きかけの記事にtodoをマーキングしておいたり、サイト全体のtodoをリスト化することができます。

設定
-----------
package::

  なし

conf.py::

  extensions = ['sphinx.ext.todo' ]

  [extensions]
  todo_include_todos=True

使い方
----------

todoを書く::

  .. todo:: todo-text

todoをリストアップする::

  .. todolist::

  .. |date| date::