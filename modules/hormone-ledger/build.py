"""Deterministic dependency-free module build; never writes outside this module."""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[1]
media = json.loads((REPO / 'media/mvu/media-manifest.v1.json').read_text())
manifest = json.loads((REPO / media['lockscreen']['manifest_path']).read_text())
paths = [p for book in manifest['books'] for p in book['pages']]
assert len(paths) == len(set(paths)) == 61
assert re.fullmatch(r'[a-f0-9]{40}', media['asset_commit'])
generated = {
    'pages': [media['cdn_base'] + p for p in paths],
    'background': media['background']['cdn'],
    'css': (ROOT / 'src/style.css').read_text(),
}
(ROOT / 'src/media.js').write_text('// Generated from the authoritative manifests; do not reorder.\n' + '\n'.join(
    f'export const {key} = {json.dumps(value, ensure_ascii=False)};' for key, value in generated.items()) + '\n')
parts = []
for name in ['schema', 'runtime', 'media', 'gallery', 'ui', 'host', 'entry']:
    source = (ROOT / f'src/{name}.js').read_text()
    source = re.sub(r'^import .*?;\n', '', source, flags=re.M)
    parts.append(re.sub(r'\bexport (?=(?:const|function)\b)', '', source))
(ROOT / 'dist/hormone-ledger.js').write_text('(() => {\n"use strict";\n' + '\n'.join(parts) + '\n})();\n')
regex = {
    'id': 'a5d59e93-d19f-4c12-9109-bda3623c9569',
    'scriptName': '♡ 荷尔蒙记录 · 本回合',
    'findRegex': r'/<hormone>\s*([\s\S]*?)\s*<\/hormone>\s*/gi',
    'replaceString': '<details style="background:#17151a;color:#f1e3c8;border:1px solid #d8b36a44;border-radius:4px;padding:4px 10px"><summary style="min-height:44px;line-height:44px;cursor:pointer">♡ 荷尔蒙记录 · 本回合</summary><pre style="white-space:pre-wrap;overflow-wrap:anywhere;font:inherit">$1</pre></details>',
    'trimStrings': [], 'placement': [2], 'disabled': False,
    'markdownOnly': True, 'promptOnly': False, 'runOnEdit': True,
    'substituteRegex': 0, 'minDepth': None, 'maxDepth': None,
}
(ROOT / 'dist/regex.json').write_text(json.dumps(regex, ensure_ascii=False, indent=2) + '\n')
print('Built independent runtime + display-only regex; 61 manifest-ordered pages.')
