Sphinxでコードブロックを記述する方法
========================================

| リテラルブロックかcode-blockディレクティブを使う。

リテラルブロックの場合
-----------------------------------

リテラルブロック例::

  Pythonサンプル::

    def factorial(x):
        if x == 0:
            return 1
        else:
            return x * factorial(x - 1)

出力

Pythonサンプル::

  def factorial(x):
      if x == 0:
          return 1
      else:
          return x * factorial(x - 1)


code-blockの場合
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

