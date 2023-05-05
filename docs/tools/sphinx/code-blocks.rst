Sphinxでコードブロックを記述する方法
========================================

| リテラルブロックかcode-blockディレクティブを使う。

リテラルブロック
-----------------------------------

例::

  サンプル::

    def factorial(x):
        if x == 0:
            return 1
        else:
            return x * factorial(x - 1)

出力

サンプル::

  def factorial(x):
      if x == 0:
          return 1
      else:
          return x * factorial(x - 1)


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
          # ライン強調テスト
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

