# SphinxでMarkdownを扱うには

SphinxでMarkdown扱えるように設定する。  

## 追加インストール

```bash
  poetry add myst-parser
```

## conf.py

```python
  extensions = ['myst_parser']
  source_suffix = {
    '.rst': 'restructuredtext',
    '.txt': 'markdown',
    '.md': 'markdown',
  }
```

## 確認

このページはMarkdownで記述。  
うまく表示されてるようなのでOK.

