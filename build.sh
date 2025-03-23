#!/bin/bash
set -euo pipefail # シェルスクリプトのエラーハンドリング

# 言語ごとにsphinx-buildを実行するループ
# for lang in ja en zh es fr hi; do
for lang in ja en; do
    sphinx-build -b html docs docs/_build/html/${lang} -D language=${lang}
done

# 必要なファイルをコピーする
cp static/index.html docs/_build/html/
cp static/robots.txt docs/_build/html/
cp static/ads.txt docs/_build/html/
cp static/style.css docs/_build/html/
cp static/cmp.js docs/_build/html/
cp static/_redirects docs/_build/html/
cp docs/_build/html/ja/sitemap.xml docs/_build/html/
