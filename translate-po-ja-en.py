import os
from translate_po.main import run

from_lang = "ja"
to_lang = "en"
untranslated = "docs\locale\en\LC_MESSAGES\index.po"
translated = untranslated

run(fro=from_lang, to=to_lang, src=untranslated,
    dest=translated)
