"""Read-only integrity QA of authoritative manifest order and image bytes."""
import hashlib
import json
import subprocess
from pathlib import Path
from PIL import Image

MODULE = Path(__file__).resolve().parents[1]
REPO = MODULE.parents[1]
media = json.loads((REPO/'media/mvu/media-manifest.v1.json').read_text())
manifest = json.loads((REPO/media['lockscreen']['manifest_path']).read_text())
pages = [p for b in manifest['books'] for p in b['pages']]
assert [len(b['pages']) for b in manifest['books']] == [28,33]
assert len(pages) == len(set(pages)) == 61
hashes = set()
for path in pages + [media['background']['path']]:
    full = REPO/path
    with Image.open(full) as im:
        assert im.format == 'WEBP'
        im.load()
        assert im.width > 0 and im.height > 0
    subprocess.run(['git','cat-file','-e',media['asset_commit']+':'+path],cwd=REPO,check=True)
    if path in pages:
        hashes.add(hashlib.sha256(full.read_bytes()).hexdigest())
assert len(hashes) == 61, 'Duplicate page bytes'
subprocess.run(['git','cat-file','-e',media['asset_commit']+':'+media['lockscreen']['manifest_path']],cwd=REPO,check=True)
print('PASS: 28 + 33 = 61 unique manifest-ordered pages decode; background decodes; all exist at pinned commit.')
