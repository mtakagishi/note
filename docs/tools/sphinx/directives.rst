sphinxで使えるディレクティブ集
==========================================
* ディレクティブとはマークアップ言語における一般的なブロックのことです

toctree
--------------------------------
* Table of contentsの略
* toctreeに指定できない文字列

  * genindex
  * modindex
  * search
  * _(アンダースコア) で始まる名前

ディレクティブ::

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

例::

  .. code-block:: python
    :caption: サンプル
    :linenos:
    :emphasize-lines: 4
    
    def factorial(x):
      if x == 0:
          return 1
          # 強調
      else:
          return x * factorial(x - 1)

出力

.. code-block:: python
  :caption: サンプル
  :linenos:
  :emphasize-lines: 4
  
  def factorial(x):
    if x == 0:
        return 1
        # 強調
    else:
        return x * factorial(x - 1)


todo
------------------------------------
ディレクティブ::

  .. todo:: ディレクティブ紹介例に掲載のTODO

レンダリング後:

.. todo:: ディレクティブ紹介例に掲載のTODO


todolist
------------------------------------
ディレクティブ::

  .. todolist::

レンダリング後:

.. todolist::


code
------------------------------------
ディレクティブ::

  .. code-block:: shell

    echo Hello world

レンダリング後:

.. code-block:: shell

  echo Hello world


image
------------------------------------
ディレクティブ::
  
  .. image:: https://unsplash.it/336/280/?random

レンダリング後:

.. image:: https://unsplash.it/336/280/?random


figure
------------------------------------
ディレクティブ::

  .. figure:: /_static/logo.png
  
レンダリング後:

.. figure:: /_static/logo.png

link
------------------------------------
ディレクティブ::

  `Title <http://link>`_ 

レンダリング後:

`Title <http://link>`_ 

admonition
------------------------------------
ディレクティブ::

  .. admonition:: lorem30

  Lorem ipsum dolor sit amet consectetur adipisicing elit. Recusandae placeat quia, magnam iusto cum beatae adipisci. Omnis nisi alias dolor. Quidem et fugiat minima saepe atque sed totam quibusdam perspiciatis!


レンダリング後:

.. admonition:: lorem30

  Lorem ipsum dolor sit amet consectetur adipisicing elit. Recusandae placeat quia, magnam iusto cum beatae adipisci. Omnis nisi alias dolor. Quidem et fugiat minima saepe atque sed totam quibusdam perspiciatis!

attention
------------------------------------
ディレクティブ::

  .. attention:: attention

レンダリング後:

.. attention:: attention

note
------------------------------------
ディレクティブ::

  .. note:: note
  
レンダリング後:

.. note:: note


warning
------------------------------------
ディレクティブ::

  .. warning:: warning

レンダリング後:

.. warning:: warning


error
------------------------------------
ディレクティブ::

  .. error:: error
  
レンダリング後:

.. error:: error


hint
------------------------------------
ディレクティブ::

  .. hint:: hint
  
レンダリング後:

.. hint:: hint


important
------------------------------------
ディレクティブ::

  .. important:: important
  

レンダリング後:

.. important:: important


caution
------------------------------------
ディレクティブ::

  .. caution:: caution
  
レンダリング後:

.. caution:: caution


danger
------------------------------------
ディレクティブ::

  .. danger:: danger
  
レンダリング後:

.. danger:: danger


tip
------------------------------------
ディレクティブ::

  .. tip:: tip
  

レンダリング後:

.. tip:: tip



rubric
------------------------------------
ディレクティブ::

  .. rubric:: rubric
  

レンダリング後:

.. rubric:: rubric


math
------------------------------------
ディレクティブ::

  :math:`\sqrt{16}` 

レンダリング後:

:math:`\sqrt{16}` 

command
------------------------------------
ディレクティブ::

  :command:`Title` 

レンダリング後:

:command:`Title` 

file
------------------------------------
ディレクティブ::

  :file:`path` 

レンダリング後:

:file:`path` 

guilabel
------------------------------------
ディレクティブ::

  :guilabel:`Title` 

レンダリング後:

:guilabel:`Title` 

key
------------------------------------
ディレクティブ::

  :kbd:`shortcut` 

レンダリング後:

:kbd:`shortcut` 

menu
------------------------------------
ディレクティブ::

  :menuselection:`Title --> Title2` 

レンダリング後:

:menuselection:`Title --> Title2` 

