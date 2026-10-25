#!/usr/bin/env python3
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "dist" / "火影姬世界_worldbook-ready_v1.0.json"
MOD = ROOT / "modules" / "hormone-ledger"
OUT_DIR = ROOT / "release"
OUT_JSON = OUT_DIR / "火影姬世界_Candidate2_v1.0.json"
OUT_QA = OUT_DIR / "火影姬世界_Candidate2_v1.0_QA.json"


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def script_obj(name: str, sid: str, content: str, info: str):
    return {
        "type": "script",
        "enabled": True,
        "name": name,
        "id": sid,
        "content": content.strip() + "\n",
        "info": info,
        "button": {"enabled": False, "buttons": []},
        "data": {},
        "export_with": {"data": True, "button": False},
    }


def wb_ext(position_num: int, depth: int = 4):
    return {
        "selectiveLogic": 0,
        "position": position_num,
        "depth": depth,
        "role": 0,
        "match_whole_words": True,
        "probability": 100,
        "useProbability": True,
        "sticky": 0,
        "cooldown": 0,
        "delay": 0,
        "exclude_recursion": True,
        "prevent_recursion": True,
        "delay_until_recursion": False,
        "group": "",
        "group_override": False,
        "group_weight": 100,
        "use_group_scoring": False,
        "scan_depth": 2,
        "case_sensitive": False,
        "automation_id": "",
        "vectorized": False,
        "display_index": 0,
        "outlet_name": "",
        "match_persona_description": False,
        "match_character_description": False,
        "match_character_personality": False,
        "match_character_depth_prompt": False,
        "match_scenario": False,
        "match_creator_notes": False,
        "triggers": [],
        "ignore_budget": False,
    }


def wb_entry(eid: int, comment: str, content: str, order: int, enabled: bool, position: str, depth: int = 4):
    pos_num = 4 if position == "at_depth" else (0 if position == "before_char" else 1)
    ext = wb_ext(pos_num, 0 if position == "at_depth" else depth)
    return {
        "id": eid,
        "keys": [],
        "secondary_keys": [],
        "comment": comment,
        "content": content.rstrip() + "\n",
        "constant": True,
        "selective": False,
        "insertion_order": order,
        "enabled": enabled,
        "position": position,
        "use_regex": True,
        "extensions": ext,
    }


def upsert_by_name(items: list[dict], obj: dict, key: str = "name"):
    items[:] = [x for x in items if x.get(key) != obj.get(key)]
    items.append(obj)


def upsert_by_comment(items: list[dict], obj: dict):
    items[:] = [x for x in items if x.get("comment") != obj.get("comment")]
    items.append(obj)


def main():
    card = load_json(BASE)
    if card.get("spec") != "chara_card_v3":
        raise SystemExit("base is not chara_card_v3")

    data = card.setdefault("data", {})
    book = data.setdefault("character_book", {}).setdefault("entries", [])
    original_entries = copy.deepcopy(book)
    original_count = len(book)
    if original_count != 192:
        raise SystemExit("expected sealed 192-entry worldbook; refusing lore rebuild")

    integration = load_json(MOD / "integration" / "integration-manifest.json")
    if integration.get("status") != "fragments-only-not-installed":
        raise SystemExit("unexpected integration manifest status")

    core_js = (MOD / "integration" / "mvu-core-script-fragment.js").read_text(encoding="utf-8")
    zod_js = (MOD / "integration" / "schema-script-fragment.js").read_text(encoding="utf-8")
    status_js = (MOD / "dist" / "hormone-ledger.js").read_text(encoding="utf-8")
    rule_md = (MOD / "integration" / "worldbook-rule-fragment.md").read_text(encoding="utf-8")
    var_list = (MOD / "integration" / "variable-list-fragment.txt").read_text(encoding="utf-8")
    initvar = (MOD / "integration" / "initvar-fragment.yaml").read_text(encoding="utf-8")
    post_history = (MOD / "integration" / "post-history-fragment.txt").read_text(encoding="utf-8").strip()
    hormone_regex = load_json(MOD / "dist" / "regex.json")
    cleanup_regexes = load_json(MOD / "integration" / "regex-cleanup-fragment.json")
    update_rule = (MOD / "integration" / "variable-update-rule-fragment.yaml").read_text(encoding="utf-8")
    output_format = (MOD / "integration" / "variable-output-format-fragment.yaml").read_text(encoding="utf-8")

    data["name"] = "火影姬世界"
    data["description"] = "《火影忍者》全员姬化沙盒 · 荷尔蒙档案 MVU"
    data["avatar"] = "none"
    data["character_version"] = "1.0.0"
    data["creator_notes"] = (data.get("creator_notes", "") + "\n\n火影姬世界 v1.0.0：以封版 worldbook-ready v1.0 为正文基线，仅装配独立 hormone-ledger MVU、强制 <hormone> 快照契约与显示正则；世界书既有正文不改。媒体由固定 GitHub/jsDelivr 清单云加载。真实 Android/SillyTavern 以本 PNG 导入验收为准。").strip()
    tags = list(dict.fromkeys((data.get("tags") or []) + ["火影姬世界", "咩咩制卡·全栈1.0.0", "MVU", "荷尔蒙档案"]))
    data["tags"] = tags
    # Preserve the sealed book's name, entries, order and light states verbatim.

    for k in ("name", "description", "personality", "scenario", "first_mes", "mes_example", "creator_notes"):
        if k in card:
            card[k] = data.get(k, card[k])

    ext = data.setdefault("extensions", {})
    th = ext.setdefault("tavern_helper", {})
    scripts = th.setdefault("scripts", [])
    th.setdefault("variables", {})
    upsert_by_name(scripts, script_obj("MVU", "mvu-core", core_js, "MagVarUpdate 变量系统底座，勿删。"))
    upsert_by_name(scripts, script_obj("MVU ZOD", "mvu-zod-schema", zod_js, "仅定义角色荷尔蒙与角色活体铠甲两个 Record。"))
    upsert_by_name(scripts, script_obj("变量状态栏", "hormone-ledger-statusbar", status_js, "火影姬·荷尔蒙档案：仅最新正常 AI 楼单实例面板。"))

    regexes = ext.setdefault("regex_scripts", [])
    regexes[:] = [r for r in regexes if r.get("scriptName") != hormone_regex.get("scriptName") and r.get("id") != hormone_regex.get("id")]
    regexes.append(hormone_regex)
    for regex in cleanup_regexes:
        regexes[:] = [r for r in regexes if r.get("id") != regex["id"]]
        regexes.append(regex)

    old_phi = (data.get("post_history_instructions") or "").strip()
    data["post_history_instructions"] = (old_phi + ("\n\n" if old_phi else "") + post_history).strip()

    max_id = max((int(e.get("id", -1)) for e in book), default=-1)
    entries_to_add = [
        wb_entry(max_id + 1, "核心规则:火影姬·每回合荷尔蒙记录强制输出", rule_md, 549, True, "after_char"),
        wb_entry(max_id + 2, "变量列表", var_list, 900, True, "at_depth"),
        wb_entry(max_id + 3, "[initvar]变量初始化勿开", initvar, 899, False, "after_char"),
        wb_entry(max_id + 4, "[mvu_update]变量输出格式", output_format, 901, True, "at_depth"),
        wb_entry(max_id + 5, "[mvu_update]变量更新规则", update_rule, 902, True, "at_depth"),
    ]
    for e in entries_to_add:
        upsert_by_comment(book, e)

    original_unchanged = book[:original_count] == original_entries
    comments = [e.get("comment") for e in book]
    script_names = [s.get("name") for s in scripts]
    adult_gate = any(
        "对明确成年角色" in (e.get("content") or "") and "对未成年角色不使用乳腺/性化反馈" in (e.get("content") or "")
        for e in original_entries
    )
    lock_manifest = load_json(ROOT / "media" / "mvu" / "lockscreen" / "manifest.json")
    lock_pages = [ROOT / p for b in lock_manifest["books"] for p in b["pages"]]
    checks = {
        "spec_is_ccv3": card.get("spec") == "chara_card_v3" and card.get("spec_version") == "3.0",
        "worldbook_original_entries_byte_semantics_unchanged": original_unchanged,
        "worldbook_entry_count_expected": len(book) == original_count + 5,
        "sealed_book_name_preserved": data["character_book"]["name"] == "火影姬世界书",
        "adult_gate_preserved_from_existing_worldbook": adult_gate,
        "mvu_scripts_exact_three_present": all(n in script_names for n in ["MVU", "MVU ZOD", "变量状态栏"]),
        "mvu_scripts_enabled_and_native": all(
            len([s for s in scripts if s.get("name") == n and s.get("enabled") is True and
                 s.get("type") == "script" and s.get("content", "").strip()]) == 1
            for n in ["MVU", "MVU ZOD", "变量状态栏"]
        ),
        "native_variable_update_rule_present": "[mvu_update]变量更新规则" in comments,
        "native_variable_output_format_present": "[mvu_update]变量输出格式" in comments,
        "schema_exact_two_records": "角色荷尔蒙" in zod_js and "角色活体铠甲" in zod_js and "z.record" in zod_js,
        "hormone_rule_present": "核心规则:火影姬·每回合荷尔蒙记录强制输出" in comments,
        "variable_list_present": "变量列表" in comments,
        "initvar_present_disabled": any(e.get("comment") == "[initvar]变量初始化勿开" and not e.get("enabled") for e in book),
        "post_history_has_single_block_contract": "必须输出一个完整的 <hormone>...</hormone>" in data.get("post_history_instructions", ""),
        "display_regex_present": any(r.get("scriptName") == "♡ 荷尔蒙记录 · 本回合" for r in regexes),
        "native_cleanup_regexes_enabled": all(any(r.get("id") == x["id"] and r.get("disabled") is False for r in regexes) for x in cleanup_regexes),
        "no_polling_in_statusbar": all(x not in status_js for x in ["setInterval(", "setTimeout("]),
        "lockscreen_has_61_pages": len(lock_pages) == 61,
        "module_media_commit_pinned": integration.get("media_commit") == "b4b11c5efbbc99e1b7d92d79f32b937cfabd2f27",
    }

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    text = json.dumps(card, ensure_ascii=False, separators=(",", ":"))
    OUT_JSON.write_text(text, encoding="utf-8")
    qa = {
        "status": "PASS" if all(checks.values()) else "FAIL",
        "checks": checks,
        "base": str(BASE.relative_to(ROOT)),
        "base_worldbook_entries": original_count,
        "final_worldbook_entries": len(book),
        "lockscreen_pages": len(lock_pages),
        "integration_media_commit": integration.get("media_commit"),
        "final_json_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
        "note": "本报告是静态/自动化组装 QA；真实 Android/SillyTavern 仍需导入最终 PNG 实机验收。",
    }
    OUT_QA.write_text(json.dumps(qa, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(qa, ensure_ascii=False, indent=2))
    if qa["status"] != "PASS":
        raise SystemExit(2)


if __name__ == "__main__":
    main()
