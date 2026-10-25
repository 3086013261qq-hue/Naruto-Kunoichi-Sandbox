#!/usr/bin/env python3
"""Replace metadata payloads only; retain every non-card PNG chunk byte-for-byte."""
from __future__ import annotations
import argparse
import base64
import hashlib
import json
import struct
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CARD = ROOT / 'release/火影姬世界_Candidate3_v1.0.json'
OUTPUT = ROOT / 'release/火影姬世界_Candidate3_v1.0.png'
REPORT = ROOT / 'release/火影姬世界_Candidate3_v1.0_PNG_QA.json'
SIGNATURE = b'\x89PNG\r\n\x1a\n'

def chunks(data):
    assert data[:8] == SIGNATURE, 'not a PNG'
    offset = 8
    while offset < len(data):
        length = struct.unpack_from('>I', data, offset)[0]
        kind = data[offset+4:offset+8]
        content = data[offset+8:offset+8+length]
        raw = data[offset:offset+length+12]
        assert len(raw) == length + 12, 'truncated PNG'
        assert struct.unpack('>I', raw[-4:])[0] == zlib.crc32(kind + content), 'PNG CRC mismatch'
        yield kind, content, raw
        offset += length + 12
        if kind == b'IEND':
            assert offset == len(data), 'trailing PNG bytes'
            break

def card_chunk(kind, content):
    return kind in (b'tEXt', b'iTXt', b'zTXt') and content.split(b'\0', 1)[0] in (b'chara', b'ccv3')

def text_chunk(keyword, content):
    body = keyword + b'\0' + base64.b64encode(content)
    return struct.pack('>I', len(body)) + b'tEXt' + body + struct.pack('>I', zlib.crc32(b'tEXt' + body))

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--cover', type=Path, default=ROOT / 'release/火影姬世界_Candidate2_v1.0.png',
                        help='Existing imported PNG; default repacks committed Candidate3 itself')
    args = parser.parse_args()
    card_bytes = CARD.read_bytes()
    card = json.loads(card_bytes)
    assert card.get('spec') == 'chara_card_v3'
    original = list(chunks(args.cover.read_bytes()))
    image_chunks = [raw for kind, value, raw in original if not card_chunk(kind, value)]
    assert image_chunks and original[-1][0] == b'IEND'
    packed = SIGNATURE + b''.join(image_chunks[:-1]) + text_chunk(b'chara', card_bytes) + text_chunk(b'ccv3', card_bytes) + image_chunks[-1]
    recovered = {}
    final_chunks = list(chunks(packed))
    for kind, value, raw in final_chunks:
        if card_chunk(kind, value):
            key, encoded = value.split(b'\0', 1)
            assert key not in recovered, 'duplicate payload keyword'
            recovered[key] = base64.b64decode(encoded, validate=True)
    assert set(recovered) == {b'chara', b'ccv3'}
    assert recovered[b'ccv3'] == recovered[b'chara'] == card_bytes
    assert [raw for kind, value, raw in final_chunks if not card_chunk(kind, value)] == image_chunks
    OUTPUT.write_bytes(packed)
    report = {
        'status': 'PASS', 'json': CARD.name, 'png': OUTPUT.name,
        'json_sha256': hashlib.sha256(card_bytes).hexdigest(),
        'png_sha256': hashlib.sha256(packed).hexdigest(),
        'ccv3_payload_exact_json_bytes': True, 'chara_payload_exact_json_bytes': True,
        'all_png_chunk_crcs_valid': True, 'existing_cover_chunks_unchanged': True,
        'cover_chunks_sha256': hashlib.sha256(b''.join(image_chunks)).hexdigest(),
        'note': 'Metadata packaging QA only; real Android/SillyTavern acceptance is pending.',
    }
    REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n')
    print(json.dumps(report, ensure_ascii=False, indent=2))

if __name__ == '__main__':
    main()
