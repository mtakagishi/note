import os
import sys
from translate_po.main import run
import asyncio

def clean_path(path_str):
    """ダブルクォートやシングルクォートを取り除いて正規化"""
    return os.path.normpath(path_str.strip('"').strip("'"))

def main():
    from_lang = "ja"
    to_lang = "en"

    # コマンドライン引数 or 対話入力
    if len(sys.argv) >= 2:
        untranslated = clean_path(" ".join(sys.argv[1:]))
    else:
        untranslated = clean_path(input("翻訳対象の .po ファイルのパスを入力してください: "))

    # 存在チェック
    if not os.path.exists(untranslated):
        print(f"エラー: ファイルが存在しません: {untranslated}")
        sys.exit(1)

    # 拡張子チェック
    if not untranslated.lower().endswith(".po"):
        print(f"エラー: .po ファイルではありません: {untranslated}")
        sys.exit(1)

    translated = untranslated  # 上書き翻訳

    asyncio.run(run(fro=from_lang, to=to_lang, src=untranslated, dest=translated))

if __name__ == "__main__":
    main()
