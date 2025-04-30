# note.mtakagishi

[![MIT license](https://img.shields.io/badge/License-MIT-blue.svg)](https://lbesson.mit-license.org/) [![Netlify Status](https://api.netlify.com/api/v1/badges/cf669616-af9c-424e-bd66-d00fe89e9420/deploy-status)](https://app.netlify.com/sites/jolly-brown-b98547/deploys)

## URL

- "https://mtakagishi.com"
- "https://jolly-brown-b98547.netlify.app/"

## サイト趣旨

- IT関連の技術の記録

## localhostでの参照方法
```bash
git clone https://github.com/mtakagishi/note.git
cd note
poetry install
poetry run poe doc
python simple_http_server.py -p {port} --open-browser
```
port:デフォは8000。
ビルド済みなら、`run_simple_http_server.bat`

## サイト維持メモ
### 英語化
- poファイル生成
`poegry run poe gettext`
- Google翻訳
`poetry run python .\translate-po-ja-en.py` {ファイルPATH}
- 手作業翻訳
  - 画面を目視確認。
  - 翻訳漏れを発見したら `docs/locale/en/LC_MESSAGES` 配下を更新

## その他Tips
### VSCODE のターミナルを git bash へ
`terminal.integrated.shell.windows` に "C:\\Program Files\\Git\\bin\\bash.exe" を設定

### pip in proxy
```ini:$HOME/pip/pip.ini
 [global]
proxy = [user:passwd@]http://proxy:port
```
### shell in proxy
```bash
export HTTP_PROXY="http://proxy:port"
export HTTPS_PROXY="http://proxy:port"
```
### git in proxy
```bash
git config --global http.proxy http://proxy:port
git config --global https.proxy http://proxy:port
```
