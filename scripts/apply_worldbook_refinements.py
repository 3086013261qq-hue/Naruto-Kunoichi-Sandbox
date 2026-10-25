#!/usr/bin/env python3
from __future__ import annotations

import copy
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BOOK_PATH = ROOT / "dist" / "火影姬世界_完整世界书_v1.0.json"
READY_PATH = ROOT / "dist" / "火影姬世界_worldbook-ready_v1.0.json"
MANIFEST_PATH = ROOT / "dist" / "火影姬世界_世界书条目清单_v1.0.json"
LIGHT_PATH = ROOT / "worldbook" / "settings" / "14_世界书蓝绿灯返工裁决_v1.0.json"
HAIR_PATH = ROOT / "worldbook" / "characters" / "07_原男性角色女性化发型补丁_v1.0.json"
QA_PATH = ROOT / "qa" / "世界书返工审计_v1.0.json"

HAIR_MARKERS = (
    "短发", "长发", "乱发", "头发", "发型", "刘海", "马尾", "双马尾", "辫",
    "发髻", "刺猬头", "西瓜头", "扫把头", "发尾", "卷发", "直发",
    "银发", "白发", "金发", "黑发", "红发", "棕发", "灰发", "紫发", "蓝发", "褐发",
)
HAIR_FALSE_POSITIVES = ("发白", "发育", "爆发", "出发", "发生", "发作", "发情")


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def dump_json(path: Path, obj) -> None:
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def index_of(entries: list[dict], comment: str) -> int:
    hits = [i for i, e in enumerate(entries) if e.get("comment") == comment]
    if len(hits) != 1:
        raise RuntimeError(f"expected exactly one entry {comment!r}, got {len(hits)}")
    return hits[0]


def set_blue(entry: dict, title: str, order: int) -> dict:
    out = copy.deepcopy(entry)
    out["comment"] = f"核心规则:{title}"
    out["enabled"] = True
    out["constant"] = True
    out["selective"] = False
    out["insertion_order"] = order
    out["position"] = "after_char"
    out["keys"] = []
    out["secondary_keys"] = []
    out["use_regex"] = False
    ex = out.setdefault("extensions", {})
    ex["position"] = 1
    ex["depth"] = 4
    ex["probability"] = 100
    ex["useProbability"] = True
    ex["exclude_recursion"] = False
    ex["prevent_recursion"] = False
    ex["delay_until_recursion"] = False
    ex["selectiveLogic"] = 0
    ex["scan_depth"] = 5
    return out


def promote_global_rules(entries: list[dict], policy: dict) -> list[dict]:
    entries = copy.deepcopy(entries)
    promoted: list[dict] = []
    for item in policy["promote_to_blue"]:
        title = item["title"]
        green_comment = f"核心设定:{title}"
        blue_comment = f"核心规则:{title}"
        green_hits = [i for i, e in enumerate(entries) if e.get("comment") == green_comment]
        blue_hits = [i for i, e in enumerate(entries) if e.get("comment") == blue_comment]
        if len(green_hits) == 1 and not blue_hits:
            src = entries.pop(green_hits[0])
        elif len(blue_hits) == 1 and not green_hits:
            src = entries.pop(blue_hits[0])
        else:
            raise RuntimeError(f"cannot uniquely promote {title}: green={len(green_hits)} blue={len(blue_hits)}")
        promoted.append(set_blue(src, title, int(item["order"])))

    start = index_of(entries, "【核心规则:起始】")
    end = index_of(entries, "【核心规则:结尾】")
    rules = entries[start + 1:end] + promoted
    rules.sort(key=lambda e: e.get("insertion_order", 0), reverse=True)
    entries[start + 1:end] = rules
    return entries


def is_hair_token(token: str) -> bool:
    if any(x in token for x in HAIR_FALSE_POSITIVES):
        return False
    return any(x in token for x in HAIR_MARKERS)


def rewrite_speedsketch_hair(content: str, hairstyle: str) -> tuple[str, bool]:
    lines = content.splitlines()
    for i, line in enumerate(lines):
        if not line.startswith("速写:"):
            continue
        body = line[len("速写:"):]
        tokens = [x.strip() for x in re.split(r"[;,，；]", body) if x.strip()]
        rewritten: list[str] = []
        inserted = False
        for token in tokens:
            if is_hair_token(token):
                if not inserted:
                    rewritten.append(hairstyle)
                    inserted = True
                continue
            rewritten.append(token)
        if not inserted:
            insert_at = 2 if len(rewritten) >= 2 else len(rewritten)
            rewritten.insert(insert_at, hairstyle)
        lines[i] = "速写:" + ",".join(rewritten)
        return "\n".join(lines), True

    marker = "性别:女"
    if marker in content:
        return content.replace(marker, marker + "\n发型:" + hairstyle, 1), True
    return content, False


def apply_hairstyles(entries: list[dict], patches: dict[str, str]) -> tuple[list[dict], dict[str, int]]:
    entries = copy.deepcopy(entries)
    touched = {name: 0 for name in patches}
    for entry in entries:
        content = entry.get("content", "")
        m = re.search(r"^名字\s*:\s*([^\n]+)", content, re.M)
        if not m:
            continue
        name = m.group(1).strip()
        if name not in patches:
            continue
        new_content, ok = rewrite_speedsketch_hair(content, patches[name])
        if not ok:
            raise RuntimeError(f"could not install hairstyle for {name}: {entry.get('comment')}")
        entry["content"] = new_content
        touched[name] += 1
    missing = [name for name, count in touched.items() if count == 0]
    if missing:
        raise RuntimeError("hairstyle patch names not found: " + ", ".join(missing))
    return entries, touched


def normalize_ids(entries: list[dict]) -> None:
    for i, entry in enumerate(entries):
        entry["id"] = i
        entry.setdefault("extensions", {})["display_index"] = i


def make_manifest(entries: list[dict]) -> list[dict]:
    return [
        {
            "index": i,
            "id": e.get("id"),
            "comment": e.get("comment"),
            "enabled": e.get("enabled"),
            "constant": e.get("constant"),
            "selective": e.get("selective"),
            "position": e.get("position"),
            "depth": e.get("extensions", {}).get("depth"),
            "order": e.get("insertion_order"),
            "use_regex": e.get("use_regex"),
            "keys": e.get("keys", []),
        }
        for i, e in enumerate(entries)
    ]


def main() -> None:
    book = load_json(BOOK_PATH)
    ready = load_json(READY_PATH)
    policy = load_json(LIGHT_PATH)
    hair_cfg = load_json(HAIR_PATH)
    hairstyle_patches: dict[str, str] = hair_cfg["patches"]

    original_entries = copy.deepcopy(book["entries"])
    original_total = len(original_entries)

    entries = promote_global_rules(original_entries, policy)
    entries, touched = apply_hairstyles(entries, hairstyle_patches)
    normalize_ids(entries)

    worldbook_name = policy["worldbook_name"]
    book["name"] = worldbook_name
    book["entries"] = entries

    ready.setdefault("data", {})["character_book"] = copy.deepcopy(book)
    ready["data"].setdefault("extensions", {})["world"] = worldbook_name
    if "character_book" in ready:
        ready["character_book"] = copy.deepcopy(book)

    dump_json(BOOK_PATH, book)
    dump_json(READY_PATH, ready)
    dump_json(MANIFEST_PATH, make_manifest(entries))

    rule_start = index_of(entries, "【核心规则:起始】")
    rule_end = index_of(entries, "【核心规则:结尾】")
    rule_comments = {e.get("comment") for e in entries[rule_start + 1:rule_end]}
    checks: dict[str, bool] = {
        "entry_count_unchanged": len(entries) == original_total,
        "worldbook_name_exact": book.get("name") == "火影姬世界书" and ready.get("data", {}).get("character_book", {}).get("name") == "火影姬世界书",
        "ready_world_extension_exact": ready.get("data", {}).get("extensions", {}).get("world") == "火影姬世界书",
        "hair_patch_name_count_29": len(hairstyle_patches) == 29,
        "hair_patch_all_names_found": set(touched) == set(hairstyle_patches) and all(v > 0 for v in touched.values()),
    }

    for item in policy["promote_to_blue"]:
        title = item["title"]
        comment = f"核心规则:{title}"
        hit = [e for e in entries if e.get("comment") == comment]
        checks[f"blue_{title}"] = (
            len(hit) == 1
            and comment in rule_comments
            and hit[0].get("constant") is True
            and hit[0].get("selective") is False
            and hit[0].get("enabled") is True
            and hit[0].get("insertion_order") == int(item["order"])
            and not hit[0].get("keys")
            and hit[0].get("use_regex") is False
        )
        checks[f"green_removed_{title}"] = not any(e.get("comment") == f"核心设定:{title}" for e in entries)

    for name, hairstyle in hairstyle_patches.items():
        matching = [e for e in entries if re.search(rf"^名字\s*:\s*{re.escape(name)}$", e.get("content", ""), re.M)]
        checks[f"hair_{name}"] = bool(matching) and all(hairstyle in e.get("content", "") for e in matching)

    qa = {
        "status": "PASS" if all(checks.values()) else "FAIL",
        "worldbook_name": worldbook_name,
        "entry_count_before": original_total,
        "entry_count_after": len(entries),
        "promoted_blue": [x["title"] for x in policy["promote_to_blue"]],
        "hairstyle_patch_names": list(hairstyle_patches.keys()),
        "hairstyle_body_counts": touched,
        "checks": checks,
        "scope": "只修改世界书显示名、4条全局设定灯态、29名原男性角色女性化发型；不读取或修改 modules/hormone-ledger。"
    }
    dump_json(QA_PATH, qa)
    print(json.dumps(qa, ensure_ascii=False, indent=2))
    if qa["status"] != "PASS":
        raise SystemExit(2)


if __name__ == "__main__":
    main()
