ディレクティブ
=================================
* ディレクティブとはマークアップ言語における一般的なブロック。
* sphinxによるカスタムディレクティブも含め便利なものをまとめておく。

toctree
--------------------------------
* Table of contentsの略
* 利用禁止ドキュメント名

  * genindex
  * modindex
  * search
  * _(アンダースコア) で始まる名前

ディレクティブ表記::

  .. toctree::
    :maxdepth: 2
    :numbered:
    :caption: caption text
    :name: name text
    :titlesonly:
    :glob:
    :hidden:
    :includehidden:

    intro
    All about strings <strings>
    datatypes
    intro*
    recipe/*

code-block
-----------------------------------

code-blockディレクティブ例::

  .. code-block:: python
    :caption: Pythonサンプル
    :linenos:
    :emphasize-lines: 4
    
    def factorial(x):
      if x == 0:
          return 1
          # ライン強調テスト
      else:
          return x * factorial(x - 1)

出力

.. code-block:: python
  :caption: Pythonサンプル
  :linenos:
  :emphasize-lines: 4
  
  def factorial(x):
    if x == 0:
        return 1
        # ライン強調テスト
    else:
        return x * factorial(x - 1)


todo
------------------------------------
ディレクティブ表記::

  .. todo:: ディレクティブ紹介例に掲載のTODO

レンダリング後:

.. todo:: ディレクティブ紹介例に掲載のTODO


todolist
------------------------------------
ディレクティブ表記::

  .. todolist::

レンダリング後:

.. todolist::


code
------------------------------------
ディレクティブ表記::

  .. code-block:: shell

    echo Hello world

レンダリング後:

.. code-block:: shell

  echo Hello world


image
------------------------------------
ディレクティブ表記::
  
  .. image:: https://unsplash.it/336/280/?random

レンダリング後:

.. image:: https://unsplash.it/336/280/?random


figure
------------------------------------
ディレクティブ表記::

  .. figure:: /_static/logo.png
  
レンダリング後:

.. figure:: /_static/logo.png

link
------------------------------------
ディレクティブ表記::

  `Title <http://link>`_ 

レンダリング後:

`Title <http://link>`_ 

attention
------------------------------------
ディレクティブ表記::

  .. attention:: attention

レンダリング後:

.. attention:: attention

note
------------------------------------
ディレクティブ表記::

  .. note:: note
  
レンダリング後:

.. note:: note


warning
------------------------------------
ディレクティブ表記::

  .. warning:: warning

レンダリング後:

.. warning:: warning


error
------------------------------------
ディレクティブ表記::

  .. error:: error
  
レンダリング後:

.. error:: error


hint
------------------------------------
ディレクティブ表記::

  .. hint:: hint
  
レンダリング後:

.. hint:: hint


important
------------------------------------
ディレクティブ表記::

  .. important:: important
  

レンダリング後:

.. important:: important


caution
------------------------------------
ディレクティブ表記::

  .. caution:: caution
  
レンダリング後:

.. caution:: caution


danger
------------------------------------
ディレクティブ表記::

  .. danger:: danger
  
レンダリング後:

.. danger:: danger


tip
------------------------------------
ディレクティブ表記::

  .. tip:: tip
  

レンダリング後:

.. tip:: tip



rubric
------------------------------------
ディレクティブ表記::

  .. rubric:: rubric
  

レンダリング後:

.. rubric:: rubric


math
------------------------------------
ディレクティブ表記::

  :math:`\sqrt{16}` 

レンダリング後:

:math:`\sqrt{16}` 

command
------------------------------------
ディレクティブ表記::

  :command:`Title` 

レンダリング後:

:command:`Title` 

file
------------------------------------
ディレクティブ表記::

  :file:`path` 

レンダリング後:

:file:`path` 

guilabel
------------------------------------
ディレクティブ表記::

  :guilabel:`Title` 

レンダリング後:

:guilabel:`Title` 

key
------------------------------------
ディレクティブ表記::

  :kbd:`shortcut` 

レンダリング後:

:kbd:`shortcut` 

menu
------------------------------------
ディレクティブ表記::

  :menuselection:`Title --> Title2` 

レンダリング後:

:menuselection:`Title --> Title2` 


.. |date| date::