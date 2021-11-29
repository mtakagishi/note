Docstringの記法
=================================

Docstringとは
---------------
* Pythonコードの関数などの仕様を記載するための記述
* トリプルクオートで囲う
* reStructuredText記法で書くことが可能
* reStructuredTextスタイル，Numpyスタイル，Googleスタイルの3つ

reStructuredTextスタイル
---------------------------------

reStructuredTextスタイル::

  :param path: The path of the file to wrap
  :type path: str
  :param field_storage: The :class:`FileStorage` instance to wrap
  :type field_storage: FileStorage
  :param temporary: Whether or not to delete the file when the File
    instance is destructed
  :type temporary: bool
  :returns: A buffered writable file descriptor
  :rtype: BufferedFileStorage

:param path: The path of the file to wrap
:type path: str
:param field_storage: The :class:`FileStorage` instance to wrap
:type field_storage: FileStorage
:param temporary: Whether or not to delete the file when the File
   instance is destructed
:type temporary: bool
:returns: A buffered writable file descriptor
:rtype: BufferedFileStorage

Numpyスタイル
---------------------------------

Numpyスタイル::

  """Example function with types documented in the docstring.

  `PEP 484`_ type annotations are supported. If attribute, parameter, and
  return types are annotated according to `PEP 484`_, they do not need to be
  included in the docstring:

  Parameters
  ----------
  param1 : int
      The first parameter.
  param2 : str
      The second parameter.

  Returns
  -------
  bool
      True if successful, False otherwise.

  .. _PEP 484:
      https://www.python.org/dev/peps/pep-0484/

  """

"""Example function with types documented in the docstring.

`PEP 484`_ type annotations are supported. If attribute, parameter, and
return types are annotated according to `PEP 484`_, they do not need to be
included in the docstring:

Parameters
----------
param1 : int
    The first parameter.
param2 : str
    The second parameter.

Returns
-------
bool
    True if successful, False otherwise.

.. _PEP 484:
    https://www.python.org/dev/peps/pep-0484/

"""


Googleスタイル
---------------------------------

Googleスタイル::
  
  """Example function with PEP 484 type annotations.

  Args:
      param1: The first parameter.
      param2: The second parameter.

  Returns:
      The return value. True for success, False otherwise.

  """

"""Example function with PEP 484 type annotations.

Args:
    param1: The first parameter.
    param2: The second parameter.

Returns:
    The return value. True for success, False otherwise.
"""