"""Independently inspect the final JSON and importable PNG, not build-script intent."""
import base64
import hashlib
import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO))
sys.dont_write_bytecode = True
from scripts.package_candidate_png import chunks

BASELINE = 'f007e0c030e70c9ec90c3149c61b4343675b5b1c'
MOD = REPO / 'modules/hormone-ledger'
JSON_FILE = REPO / 'release/火影姬世界_Candidate3_v1.0.json'
PNG_FILE = REPO / 'release/火影姬世界_Candidate3_v1.0.png'
ready = json.loads((REPO/'dist/火影姬世界_worldbook-ready_v1.0.json').read_text())
raw = JSON_FILE.read_bytes()
previous = json.loads((REPO/'release/火影姬世界_Candidate2_v1.0.json').read_text())
current = json.loads(raw)
for obj in [previous, current]:
    status = [s for s in obj['data']['extensions']['tavern_helper']['scripts'] if s['name'] == '变量状态栏']
    assert len(status) == 1
    status[0]['content'] = '<only allowed card change>'
assert current == previous, 'Candidate3 must differ only in statusbar script content'
assert not subprocess.check_output(['git','diff','--name-only','35b03b6099c690819d14a53967f4437a2f427ac6','--','media','modules/hormone-ledger/integration','modules/hormone-ledger/src/runtime.js','modules/hormone-ledger/src/host.js','modules/hormone-ledger/src/schema.js'],cwd=REPO,text=True).strip()

card = json.loads(raw)
data = card['data']
book = data['character_book']
original = ready['data']['character_book']
assert len(original['entries']) == 192
assert book['entries'][:192] == original['entries']
assert {k:v for k,v in book.items() if k != 'entries'} == {k:v for k,v in original.items() if k != 'entries'}
assert len(book['entries']) == 197
scripts = data['extensions']['tavern_helper']['scripts']
names = ['MVU', 'MVU ZOD', '变量状态栏']
contents = {}
for name in names:
    found = [s for s in scripts if s['name'] == name]
    assert len(found) == 1
    s = found[0]
    assert s['type'] == 'script' and s['enabled'] is True and s['id']
    contents[name] = s['content']
assert contents['MVU'].strip() == (MOD/'integration/mvu-core-script-fragment.js').read_text().strip()
assert contents['MVU ZOD'].strip() == (MOD/'integration/schema-script-fragment.js').read_text().strip()
assert contents['变量状态栏'].strip() == (MOD/'dist/hormone-ledger.js').read_text().strip()
assert not any(word in contents['变量状态栏'] for word in ['setTimeout(', 'setInterval('])
assert 'MutationObserver' in contents['变量状态栏']
assert all('</script>' not in c.lower() for c in contents.values())
regexes = data['extensions']['regex_scripts']
for rid in ['a5d59e93-d19f-4c12-9109-bda3623c9569', 'mvu-hide-update-block', 'mvu-hide-placeholder']:
    found = [r for r in regexes if r['id'] == rid]
    assert len(found) == 1 and found[0]['disabled'] is False
comments = {e['comment']:e for e in book['entries'][192:]}
for name in ['核心规则:火影姬·每回合荷尔蒙记录强制输出','变量列表','[mvu_update]变量更新规则','[mvu_update]变量输出格式']:
    assert comments[name]['enabled'] is True
assert comments['[initvar]变量初始化勿开']['enabled'] is False
assert '角色荷尔蒙: {}' in comments['[initvar]变量初始化勿开']['content']
assert '角色活体铠甲: {}' in comments['[initvar]变量初始化勿开']['content']
assert '禁止输出第二个 hormone 块' in data['post_history_instructions']
payloads = []
for kind, value, _ in chunks(PNG_FILE.read_bytes()):
    if kind == b'tEXt' and value.split(b'\0', 1)[0] in [b'chara', b'ccv3']:
        key, encoded = value.split(b'\0', 1)
        decoded = base64.b64decode(encoded, validate=True)
        assert decoded == raw
        payloads.append(key.decode())
assert sorted(payloads) == ['ccv3','chara']
protected = ['worldbook','dist','scripts/build_worldbook.py','scripts/audit_worldbook_final.py','scripts/apply_worldbook_refinements.py']
assert not subprocess.check_output(['git','diff','--name-only',BASELINE,'--',*protected],cwd=REPO,text=True).strip()
objects = {p:subprocess.check_output(['git','rev-parse',BASELINE+':'+p],cwd=REPO,text=True).strip() for p in protected}
report = {
    'status':'PASS', 'baseline':'35b03b6099c690819d14a53967f4437a2f427ac6',
    'sealed_lore_baseline':BASELINE,
    'checks':{
        'only_statusbar_content_differs_from_candidate2':True,
        'protected_media_schema_runtime_host_integration_unchanged':True,
        'three_real_enabled_native_scripts':True, 'embedded_status_script_matches_dist':True,
        'all_nine_components_present':True, 'three_real_enabled_regexes':True,
        'hormone_contract_and_short_post_history_present':True,
        'sealed_192_entries_and_lights_unchanged':True,'sealed_book_metadata_unchanged':True,
        'final_197_is_192_lore_plus_5_integration_entries':True,
        'png_ccv3_and_chara_match_final_json_bytes':True,
        'protected_source_diff_empty':True,'no_timer_refresh_or_second_state_system':True,
    },
    'json_sha256':hashlib.sha256(raw).hexdigest(),
    'png_sha256':hashlib.sha256(PNG_FILE.read_bytes()).hexdigest(),
    'protected_git_objects':objects,
    'real_android_sillytavern_acceptance':'pending user screenshots',
}
(MOD/'qa/evidence/candidate3-integration.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(report,ensure_ascii=False,indent=2))
