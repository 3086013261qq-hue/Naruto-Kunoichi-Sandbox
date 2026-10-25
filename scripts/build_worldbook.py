#!/usr/bin/env python3
from __future__ import annotations

import copy
import json
import re
from pathlib import Path
from typing import Dict, List, Tuple, Any

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "dist"
QA_DIR = ROOT / "qa"

BASE_CARD = ROOT / "火影忍者_沙盒_纯设定基底_v0.1.json"
CHAR_BACKUP = ROOT / "火影忍者_沙盒_角色条目拆分备份_v0.1.json"
CHAR_DIR = ROOT / "worldbook" / "characters"
SET_DIR = ROOT / "worldbook" / "settings"
TIMELINE_DIR = ROOT / "worldbook" / "timeline"
LOCATION_DIR = ROOT / "worldbook" / "locations"

BATCH_FILES = [
    CHAR_DIR / "02_角色精修_Batch01_v0.1.md",
    CHAR_DIR / "03_角色精修_Batch02_v0.1.md",
    CHAR_DIR / "04_角色精修_Batch03_v0.1.md",
    CHAR_DIR / "05_角色精修_Batch04_收官_v0.1.md",
]
MAPPING_FILE = CHAR_DIR / "06_火影姬全库姓名映射_v1.0.md"

BLUE_TITLES = {
    "火影姬世界总则",
    "荷尔蒙查克拉循环",
    "玩具型忍具体系",
    "活体铠甲基础构造",
    "通灵兽与尾兽铠化",
    "忍术与荷尔蒙查克拉总则",
    "女女相恋社会与家庭生育总则",
    "忍阶实力阈值与身份分离",
}

BLUE_ORDER = {
    "火影姬世界总则": 449,
    "世界观校验/过滤": 448,
    "金钱": 447,
    "任务等级说明": 446,
    "荷尔蒙查克拉循环": 445,
    "忍术与荷尔蒙查克拉总则": 444,
    "玩具型忍具体系": 443,
    "活体铠甲基础构造": 442,
    "通灵兽与尾兽铠化": 441,
    "女女相恋社会与家庭生育总则": 440,
    "忍阶实力阈值与身份分离": 439,
    "火影姬开放性话题池": 405,
}

GENDER_REPLACEMENTS = [
    ("成为火影的男人", "成为火影"),
    ("火影的男人", "火影"),
    ("男朋友", "女朋友"),
    ("男性朋友", "女性朋友"),
    ("美少年", "美少女"),
    ("男孩子", "女孩子"),
    ("男孩", "女孩"),
    ("男童", "女童"),
    ("少年", "少女"),
    ("男人", "女人"),
    ("男性", "女性"),
    ("丈夫", "妻子"),
    ("男友", "女友"),
    ("父亲", "母亲"),
    ("爸爸", "妈妈"),
    ("祖父", "祖母"),
    ("爷爷", "奶奶"),
    ("兄长", "姐姐"),
    ("哥哥", "姐姐"),
    ("弟弟", "妹妹"),
    ("兄弟", "姐妹"),
    ("儿子", "女儿"),
    ("父辈", "母辈"),
    ("父权", "家族权威"),
    ("父系", "家系"),
    ("老爷子", "高龄女忍者"),
    ("老头", "高龄女忍者"),
    ("老者", "高龄女忍者"),
    ("山羊胡", "清晰的岁月纹与沉稳神态"),
    ("大叔", "成熟御姐"),
]

SAFE_SINGLE_ALIAS_MAP = {}

SINGLE_ALIAS_RULES = [
    (r"鼬(?!鼠)", "伊月"),
    (r"兜(?!帽|鍪)", "兜美"),
    (r"凯(?!旋)", "凯莉"),
    (r"斑(?!纹|点|驳|块|痕|马)", "斑奈"),
    (r"李(?=[，。！？、与和的在对被将是曾已正则])", "洛可"),
]


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def load_json(path: Path) -> Any:
    return json.loads(read_text(path))


def card_entries(card: dict) -> list:
    if "data" in card and "character_book" in card["data"]:
        return card["data"]["character_book"]["entries"]
    if "character_book" in card:
        return card["character_book"]["entries"]
    raise KeyError("character_book.entries not found")


def set_card_entries(card: dict, entries: list) -> None:
    if "data" in card and "character_book" in card["data"]:
        card["data"]["character_book"]["entries"] = entries
    elif "character_book" in card:
        card["character_book"]["entries"] = entries
    else:
        raise KeyError("character_book.entries not found")


def get_character_book(card: dict) -> dict:
    if "data" in card and "character_book" in card["data"]:
        return card["data"]["character_book"]
    return card["character_book"]


def parse_name_mapping() -> Tuple[Dict[str, str], List[str]]:
    text = read_text(MAPPING_FILE)
    mapping: Dict[str, str] = {}
    changed_formal_names: List[str] = []
    for line in text.splitlines():
        if not line.startswith("|") or line.startswith("|---"):
            continue
        cols = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cols) < 4 or cols[0].startswith("源文本姓名"):
            continue
        source_cell, formal, short_cell = cols[:3]
        source_aliases = [x.strip() for x in source_cell.split(" / ") if x.strip()]
        formal_aliases = [x.strip() for x in short_cell.split(" / ") if x.strip()]
        if not source_aliases or not formal:
            continue
        old_formal = source_aliases[0]
        if old_formal != formal:
            mapping[old_formal] = formal
            changed_formal_names.append(old_formal)
        preferred_short = next((x for x in formal_aliases if x != formal and "火影" not in x and "仙人" not in x and x not in {"佩恩", "阿飞", "赤砂之蝎"}), formal_aliases[0] if formal_aliases else formal)
        for old in source_aliases[1:]:
            if old == formal or old == preferred_short:
                continue
            if len(old) >= 2:
                mapping[old] = preferred_short
            elif old in SAFE_SINGLE_ALIAS_MAP:
                mapping[old] = SAFE_SINGLE_ALIAS_MAP[old]
    return mapping, sorted(set(changed_formal_names), key=len, reverse=True)


def replace_names(text: str, mapping: Dict[str, str]) -> str:
    for old in sorted(mapping, key=len, reverse=True):
        new = mapping[old]
        if old != new:
            text = text.replace(old, new)
    return text


def replace_single_aliases(text: str) -> str:
    for pattern, repl in SINGLE_ALIAS_RULES:
        text = re.sub(pattern, repl, text)
    return text


def feminize_text(text: str) -> str:
    protected = {
        "其他人": "__PROTECT_OTHER_PEOPLE__",
        "其他": "__PROTECT_OTHER__",
        "他人": "__PROTECT_OTHERS__",
    }
    for src, mark in protected.items():
        text = text.replace(src, mark)
    text = text.replace("他们", "她们")
    for old, new in GENDER_REPLACEMENTS:
        text = text.replace(old, new)
    text = text.replace("他", "她")
    for src, mark in protected.items():
        text = text.replace(mark, src)
    text = text.replace("父母", "双亲")
    return text


def parse_character_patches() -> Dict[int, dict]:
    patches: Dict[int, dict] = {}
    section_re = re.compile(
        r"^## (?P<name>[^\n]+)\n(?P<body>.*?)(?=^---\s*$|\Z)",
        re.M | re.S,
    )
    for path in BATCH_FILES:
        text = read_text(path)
        for m in section_re.finditer(text):
            name = m.group("name").strip()
            body = m.group("body")
            src_m = re.search(r"源条目：\s*(\d+)(?:\s*[–—-]\s*(\d+))?", body)
            if not src_m:
                continue
            start = int(src_m.group(1))
            end = int(src_m.group(2) or start)
            key_m = re.search(r"正式关键词：`([^`]+)`", body)
            beast_m = re.search(r"兽化特征:\s*\n((?:- [^\n]+\n?){4})", body)
            if not key_m or not beast_m:
                raise RuntimeError(f"Patch parse failed for {name} in {path.name}")
            beast = "兽化特征:\n" + beast_m.group(1).rstrip()
            patch = {
                "name": name,
                "key": key_m.group(1),
                "beast": beast,
            }
            for source_id in range(start, end + 1):
                if source_id in patches:
                    raise RuntimeError(f"duplicate character patch for source id {source_id}")
                patches[source_id] = patch
    return patches


def patch_character_entry(entry: dict, patch: dict, name_map: Dict[str, str]) -> dict:
    out = copy.deepcopy(entry)
    original_content = out.get("content", "")
    was_male = bool(re.search(r"性别\s*:\s*男", original_content))
    content = replace_single_aliases(replace_names(original_content, name_map))
    comment = replace_single_aliases(replace_names(out.get("comment", ""), name_map))
    if was_male:
        content = feminize_text(content)
        content = re.sub(r"性别\s*:\s*男", "性别:女", content)
    else:
        content = re.sub(r"性别\s*:\s*女", "性别:女", content)

    new_name = patch["name"]
    content = re.sub(r"^名字\s*:[^\n]*", f"名字:{new_name}", content, count=1, flags=re.M)
    content = re.sub(r"<[^/<>\n]+character>", f"<{new_name}character>", content, count=1)
    content = re.sub(r"</[^<>\n]+character>", f"</{new_name}character>", content, count=1)

    if "兽化特征:" not in content:
        close_tag = f"</{new_name}character>"
        if close_tag in content:
            content = content.replace(close_tag, "\n\n" + patch["beast"] + "\n" + close_tag, 1)
        else:
            content = content.rstrip() + "\n\n" + patch["beast"] + "\n"

    if new_name == "猿飞日和":
        content = content.replace("矮小的高龄女忍者", "体态利落的高龄女火影")
        content = content.replace("矮小高龄女忍者", "体态利落的高龄女火影")
    if new_name == "漩涡鸣子":
        content = content.replace("成为火影的女人", "成为火影")

    out["comment"] = comment
    out["content"] = content
    out["keys"] = [patch["key"]]
    out["constant"] = False
    out["selective"] = True
    out["enabled"] = True
    out["position"] = "after_char"
    out["use_regex"] = True
    ex = out.setdefault("extensions", {})
    ex["position"] = 1
    ex["depth"] = 4
    ex["probability"] = 100
    ex["useProbability"] = True
    ex["exclude_recursion"] = True
    ex["prevent_recursion"] = True
    return out


def extract_tag_blocks(text: str, namespaces=("核心设定", "技能")) -> Dict[str, str]:
    ns = "|".join(re.escape(x) for x in namespaces)
    pat = re.compile(rf"<(?P<tag>(?:{ns}):[^>]+)>[\s\S]*?</(?P=tag)>")
    out = {}
    for m in pat.finditer(text):
        full = m.group(0).strip()
        tag = re.match(r"<([^>]+)>", full).group(1)
        title = tag.split(":", 1)[1]
        out[title] = full
    return out


def extract_code_fence(text: str) -> str:
    m = re.search(r"```(?:text)?\s*\n([\s\S]*?)\n```", text)
    if not m:
        raise RuntimeError("code fence not found")
    return m.group(1).strip()


def extract_section(text: str, heading: str) -> str:
    pat = re.compile(rf"^## {re.escape(heading)}\s*$\n(?P<body>[\s\S]*?)(?=^---\s*$|^## |\Z)", re.M)
    m = pat.search(text)
    return m.group("body").strip() if m else ""


def parse_skill_entries() -> Dict[str, dict]:
    text = read_text(SET_DIR / "01_忍术与技能体系_含AU兼容修订.md")
    blocks = extract_tag_blocks(text, namespaces=("技能",))
    result = {}
    for title, content in blocks.items():
        km = re.search(r"【未来绿灯关键词】\s*\n`([^`]+)`", content)
        terms = [x.strip() for x in (km.group(1).split("|") if km else [title]) if x.strip()]
        # settings/08 final trigger anti-explosion rules override broad candidates.
        if title == "八门遁甲":
            terms = [x for x in terms if x != "开门"]
        if title == "轮回眼":
            terms = [x for x in terms if x != "外道"]
        result[title] = {"content": content, "terms": terms}

    s11 = read_text(SET_DIR / "11_忍阶实力阈值与瞳术进化补遗_v1.1.md")
    eye_patch = extract_section(s11, "原卡补遗:写轮眼进化条件")
    byakugan_patch = extract_section(s11, "原卡补遗:白眼与转生眼进化条件")
    for skill, patch in (("写轮眼", eye_patch), ("白眼", byakugan_patch)):
        if skill in result and patch:
            closing = f"</技能:{skill}>"
            result[skill]["content"] = result[skill]["content"].replace(
                closing,
                "\n\n【正式进化补遗】\n" + patch + "\n" + closing,
                1,
            )
    return result


def derive_terms(title: str) -> List[str]:
    explicit = {
        "兽耳兽尾与御姐化": ["兽耳", "兽尾", "兽化", "御姐化"],
        "查克拉体态再塑": ["体态再塑", "体态重塑", "再发育", "第二性征"],
        "查克拉等级与多次再发育": ["多次再发育", "再发育", "身体阶段", "实力阈值"],
        "成人玩具忍具名录": ["玩具忍具", "成人玩具忍具", "刺激忍具", "查克拉忍具"],
        "通灵兽活体铠甲": ["通灵兽活体铠甲", "通灵铠甲", "通灵兽铠化"],
        "发情期三阶段": ["发情期", "升温期", "高峰期", "回落期"],
        "兽种差异与周期特征": ["兽种差异", "周期特征", "兽化周期"],
        "活体铠甲同步等级": ["活体铠甲同步", "同步率", "完全铠化"],
        "忍村荷尔蒙查克拉训练流派": ["荷尔蒙查克拉训练", "训练流派", "忍村训练"],
        "高活性后的恢复与泄压": ["高活性", "恢复与泄压", "荷尔蒙过载", "感官过载"],
        "忍者学校": ["忍者学校", "忍校", "毕业班", "班级", "学校课程"],
    }
    if title in explicit:
        return explicit[title]
    if "活体铠甲" in title:
        subject = title.replace("活体铠甲群", "").replace("活体铠甲", "").strip()
        terms = [title]
        if subject:
            terms.append(subject)
            terms.append(subject + "铠甲")
        m = re.match(r"([一二三四五六七八九]尾)(.+)", subject)
        if m:
            terms.extend([m.group(1) + m.group(2), m.group(2)])
        return list(dict.fromkeys(t for t in terms if len(t) >= 2))
    parts = [p.strip() for p in re.split(r"与|和|及|·|—|/", title) if len(p.strip()) >= 2]
    return list(dict.fromkeys([title] + parts))


def regex_key(terms: List[str], wrapped_story_scene: bool = True) -> str:
    clean = [re.escape(x) for x in terms if x]
    group = "|".join(clean) if clean else r"(?!)"
    if wrapped_story_scene:
        return rf"/<story_scene>.*?(?:{group}).*?<\/story_scene>/s"
    return rf"/(?:{group})/"


def mk_entry(template: dict, *, comment: str, content: str, order: float,
             enabled: bool = True, constant: bool = True, selective: bool = False,
             position: str = "after_char", depth: int = 4,
             keys: List[str] | None = None, secondary_keys: List[str] | None = None,
             use_regex: bool = False, exclude_recursion: bool = False) -> dict:
    e = copy.deepcopy(template)
    e["keys"] = keys or []
    e["secondary_keys"] = secondary_keys or []
    e["comment"] = comment
    e["content"] = content
    e["constant"] = constant
    e["selective"] = selective
    e["insertion_order"] = order
    e["enabled"] = enabled
    e["position"] = position
    e["use_regex"] = use_regex
    ex = e.setdefault("extensions", {})
    ex["position"] = 0 if position == "before_char" else 4 if position == "at_depth" else 1
    ex["depth"] = depth
    ex["probability"] = 100
    ex["useProbability"] = True
    ex["exclude_recursion"] = exclude_recursion
    ex["prevent_recursion"] = exclude_recursion
    ex["delay_until_recursion"] = False
    ex["selectiveLogic"] = 0
    ex["scan_depth"] = 5
    return e


def parse_special_core_rules() -> Tuple[List[dict], dict]:
    text = read_text(SET_DIR / "02_核心规则_含AU兼容修订.md")
    blocks = {}
    for tag, title in (
        ("money_rules", "金钱"),
        ("班级座位", "忍者学校"),
        ("任务等级说明", "任务等级说明"),
        ("Worldview_Boundary_and_Filter", "世界观校验/过滤"),
    ):
        m = re.search(rf"<{re.escape(tag)}>[\s\S]*?</{re.escape(tag)}>", text)
        if not m:
            raise RuntimeError(f"missing core rule block: {tag}")
        blocks[title] = m.group(0).strip()
    return [
        {"title": "金钱", "content": blocks["金钱"], "order": BLUE_ORDER["金钱"]},
        {"title": "任务等级说明", "content": blocks["任务等级说明"], "order": BLUE_ORDER["任务等级说明"]},
        {"title": "世界观校验/过滤", "content": blocks["世界观校验/过滤"], "order": BLUE_ORDER["世界观校验/过滤"]},
    ], {"title": "忍者学校", "content": blocks["忍者学校"], "terms": derive_terms("忍者学校")}


def build_settings(template: dict, name_map: Dict[str, str]) -> Tuple[List[dict], List[dict]]:
    blue: Dict[str, str] = {}
    green: Dict[str, dict] = {}

    source_files = [
        "00_火影姬AU核心设定_v0.3.md",
        "04_荷尔蒙查克拉运行细则_v0.4.md",
        "05_成人玩具忍具与通灵尾兽活体铠甲_v0.5.md",
        "06_三大圣地特殊通灵活体铠甲_v0.6.md",
        "07_特殊通灵兽活体铠甲补充_v0.7.md",
        "09_忍术荷尔蒙查克拉总则_v0.9.md",
        "10_女女相恋社会与家庭生育总则_v1.0.md",
        "11_忍阶实力阈值与瞳术进化补遗_v1.1.md",
    ]
    for fn in source_files:
        blocks = extract_tag_blocks(read_text(SET_DIR / fn), namespaces=("核心设定",))
        for title, content in blocks.items():
            content = replace_names(content, name_map)
            if title in BLUE_TITLES:
                blue[title] = content
            else:
                green[title] = {"content": content, "terms": derive_terms(title)}

    special_blue, ninja_school = parse_special_core_rules()
    for item in special_blue:
        blue[item["title"]] = replace_names(item["content"], name_map)
    green[ninja_school["title"]] = {
        "content": replace_names(ninja_school["content"], name_map),
        "terms": ninja_school["terms"],
    }

    for title, item in parse_skill_entries().items():
        green[f"技能:{title}"] = {
            "content": replace_names(item["content"], name_map),
            "terms": item["terms"],
        }

    blue_entries: List[dict] = []
    for title in sorted(blue, key=lambda x: BLUE_ORDER.get(x, 438), reverse=True):
        if title not in BLUE_ORDER:
            raise RuntimeError(f"blue title has no fixed order: {title}")
        blue_entries.append(mk_entry(
            template,
            comment=f"核心规则:{title}",
            content=blue[title],
            order=BLUE_ORDER[title],
            constant=True,
            selective=False,
            use_regex=False,
        ))

    topic = extract_code_fence(read_text(SET_DIR / "13_火影姬开放性话题池_v1.0.md"))
    blue_entries.append(mk_entry(
        template,
        comment="核心规则:火影姬开放性话题池",
        content=topic,
        order=BLUE_ORDER["火影姬开放性话题池"],
        constant=True,
        selective=False,
    ))
    blue_entries.sort(key=lambda e: e["insertion_order"], reverse=True)

    ordered_green_titles = sorted(green, key=lambda x: (0 if x.startswith("技能:") else 1, x))
    if len(ordered_green_titles) > 98:
        raise RuntimeError(f"too many core setting entries for 400..301: {len(ordered_green_titles)}")
    green_entries: List[dict] = []
    order = 399
    for title in ordered_green_titles:
        item = green[title]
        green_entries.append(mk_entry(
            template,
            comment=(title if title.startswith("技能:") else f"核心设定:{title}"),
            content=item["content"],
            order=order,
            enabled=True,
            constant=False,
            selective=True,
            position="after_char",
            depth=4,
            keys=[regex_key(item["terms"], wrapped_story_scene=True)],
            use_regex=True,
            exclude_recursion=True,
        ))
        order -= 1
    return blue_entries, green_entries


def parse_location(path: Path) -> dict:
    text = read_text(path)
    title_m = re.search(r"^# 地点:(.+)$", text, re.M)
    if not title_m:
        raise RuntimeError(f"location title missing: {path}")
    name = title_m.group(1).strip()
    body_m = re.search(r"(<地点_[^>]+>[\s\S]*?</地点_[^>]+>)", text)
    if not body_m:
        raise RuntimeError(f"location body missing: {path}")
    body = body_m.group(1).strip()
    key_m = re.search(r"<!-- keys: (\[.*?\]) -->", text)
    original_keys = json.loads(key_m.group(1)) if key_m else []
    aliases = [name]
    if original_keys:
        gm = re.search(r"\(([^()]+\|[^()]+)\)", original_keys[0])
        if gm:
            aliases.extend(x for x in gm.group(1).split("|") if x and "\\" not in x)
    fallback = regex_key(list(dict.fromkeys(aliases)), wrapped_story_scene=False)
    keys = original_keys + ([fallback] if fallback not in original_keys else [])
    return {"name": name, "body": body, "keys": keys}


def build_timeline_entries(template: dict, name_map: Dict[str, str]) -> List[dict]:
    paths = [
        TIMELINE_DIR / "01_前传.md",
        TIMELINE_DIR / "02_第一部.md",
        TIMELINE_DIR / "03_疾风传.md",
        TIMELINE_DIR / "04_博乃传.md",
    ]
    entries = []
    for path in paths:
        text = read_text(path)
        title = re.search(r"^# (.+)$", text, re.M).group(1).strip()
        body = re.search(r"<world_timeline>[\s\S]*?</world_timeline>", text).group(0).strip()
        body = replace_names(body, name_map)
        enabled = "第一部" in title
        entries.append(mk_entry(
            template,
            comment=title,
            content=body,
            order=454,
            enabled=enabled,
            constant=True,
            selective=False,
            position="after_char",
            depth=4,
        ))
    return entries


def find_default_status(base_entries: list) -> str:
    for e in base_entries:
        if e.get("comment") == "状态栏-默认":
            return e.get("content", "")
    for e in base_entries:
        if str(e.get("comment", "")).startswith("状态栏") and e.get("enabled"):
            return e.get("content", "")
    return ""


def section_marker(template: dict, name: str, order: int) -> dict:
    return mk_entry(
        template,
        comment=f"【{name}】",
        content="",
        order=order,
        enabled=True,
        constant=True,
        selective=True,
        position="after_char",
    )


def build() -> Tuple[dict, dict, str]:
    name_map, changed_formal_names = parse_name_mapping()
    base_card = load_json(BASE_CARD)
    base_entries = card_entries(base_card)
    template = copy.deepcopy(base_entries[0])

    char_backup = load_json(CHAR_BACKUP)
    chars = char_backup["character_entries"]
    patches = parse_character_patches()
    expected_ids = set(range(10, 49)) | set(range(51, 104))
    if set(patches) != expected_ids:
        missing = sorted(expected_ids - set(patches))
        extra = sorted(set(patches) - expected_ids)
        raise RuntimeError(f"character patch coverage mismatch missing={missing} extra={extra}")
    by_id = {int(e["id"]): e for e in chars}
    if set(by_id) != expected_ids:
        raise RuntimeError("character backup is not exactly 92 body entries")

    patched_chars = {sid: patch_character_entry(by_id[sid], patches[sid], name_map) for sid in sorted(expected_ids)}

    core_rule_entries, core_setting_entries = build_settings(template, name_map)
    timeline_entries = build_timeline_entries(template, name_map)
    combat = extract_code_fence(read_text(SET_DIR / "12_火影姬战斗思维链_v1.0.md"))
    combat_entry = mk_entry(
        template,
        comment="战斗思维链",
        content=combat,
        order=453,
        enabled=True,
        constant=True,
        selective=False,
        position="at_depth",
        depth=0,
    )
    status_content = replace_single_aliases(replace_names(find_default_status(base_entries), name_map))
    status_entry = mk_entry(
        template,
        comment="状态栏-默认（MVU待替换）",
        content=status_content,
        order=452,
        enabled=False,
        constant=True,
        selective=False,
        position="at_depth",
        depth=0,
    )

    entries: List[dict] = []
    entries.append(mk_entry(
        template,
        comment="🗑️清空局部变量(别关)",
        content="\n".join([
            "{{setvar::combat_driver::}}",
            "{{setvar::status_format::}}",
            "{{setvar::世界书重大记忆存储::}}",
            "{{setvar::世界书日常记忆存储::}}",
            "{{setvar::世界书玩家身世背景::}}",
        ]),
        order=556,
        enabled=True,
        constant=True,
        selective=False,
        position="before_char",
        depth=4,
    ))

    entries.append(mk_entry(template, comment="【记忆相关:起始】", content="", order=555, constant=True, selective=False))
    entries.append(mk_entry(template, comment="日常记忆存储", content="{{setvar::世界书日常记忆存储::}}", order=554, enabled=False, constant=True))
    entries.append(mk_entry(template, comment="重大记忆存储", content="{{setvar::世界书重大记忆存储::}}", order=553, enabled=False, constant=True))
    entries.append(mk_entry(template, comment="玩家身世背景", content="{{setvar::世界书玩家身世背景::}}", order=552, enabled=False, constant=True))
    entries.append(mk_entry(template, comment="【记忆相关:结尾】", content="", order=551, constant=True, selective=False))

    entries.append(section_marker(template, "输出规则:起始", 550))
    entries.extend(timeline_entries)
    entries.append(combat_entry)
    entries.append(status_entry)
    entries.append(section_marker(template, "输出规则:结尾", 451))

    entries.append(section_marker(template, "核心规则:起始", 450))
    entries.extend(core_rule_entries)
    entries.append(section_marker(template, "核心规则:结尾", 401))

    entries.append(section_marker(template, "核心设定:起始", 400))
    entries.extend(core_setting_entries)
    entries.append(section_marker(template, "核心设定:结尾", 301))

    entries.append(section_marker(template, "主要角色:起始", 300))
    order = 299
    for sid in range(51, 104):
        e = patched_chars[sid]
        e["insertion_order"] = order
        entries.append(e)
        order -= 1
    entries.append(section_marker(template, "主要角色:结尾", 201))

    entries.append(section_marker(template, "其他角色:起始", 200))
    order = 199
    for sid in range(10, 49):
        e = patched_chars[sid]
        e["insertion_order"] = order
        entries.append(e)
        order -= 1
    entries.append(section_marker(template, "其他角色:结尾", 101))

    entries.append(section_marker(template, "地点:起始", 100))
    location_paths = sorted(p for p in LOCATION_DIR.glob("[0-9][0-9]_*.md"))
    if len(location_paths) != 9:
        raise RuntimeError(f"expected 9 location files, got {len(location_paths)}")
    order = 99
    for path in location_paths:
        loc = parse_location(path)
        entries.append(mk_entry(
            template,
            comment=f"地点:{loc['name']}",
            content=replace_names(loc["body"], name_map),
            order=order,
            enabled=True,
            constant=False,
            selective=True,
            position="after_char",
            depth=4,
            keys=loc["keys"],
            use_regex=True,
            exclude_recursion=True,
        ))
        order -= 1
    entries.append(section_marker(template, "地点:结尾", 1))

    for i, e in enumerate(entries):
        e["id"] = i
        e.setdefault("extensions", {})["display_index"] = i

    comments = [e.get("comment", "") for e in entries]
    section_names = ["记忆相关", "输出规则", "核心规则", "核心设定", "主要角色", "其他角色", "地点"]
    for section in section_names:
        for side in ("起始", "结尾"):
            marker = f"【{section}:{side}】"
            if comments.count(marker) != 1:
                raise RuntimeError(f"marker count not 1: {marker}")

    if sum(1 for e in entries if str(e.get("comment", "")).startswith("时间线-")) != 4:
        raise RuntimeError("timeline count != 4")
    if sum(1 for e in timeline_entries if e["enabled"]) != 1:
        raise RuntimeError("timeline enabled count != 1")
    if len(patched_chars) != 92 or set(patched_chars) != expected_ids:
        raise RuntimeError("character source-id coverage != 92")
    if len([e for e in entries if str(e.get("comment", "")).startswith("地点:")]) != 9:
        raise RuntimeError("location count != 9")
    if len(core_setting_entries) < 20:
        raise RuntimeError("core settings unexpectedly small")

    broad_trigger_hits = []
    for e in core_setting_entries:
        for key in e.get("keys", []):
            if e.get("comment") == "技能:八门遁甲" and ("|开门|" in key or "(?:开门|" in key or "|开门)" in key):
                broad_trigger_hits.append("八门遁甲:开门")
            if e.get("comment") == "技能:轮回眼" and ("|外道|" in key or "(?:外道|" in key or "|外道)" in key):
                broad_trigger_hits.append("轮回眼:外道")
    if broad_trigger_hits:
        raise RuntimeError("broad trigger regression: " + ", ".join(broad_trigger_hits))

    for sid, e in patched_chars.items():
        if "兽化特征:" not in e.get("content", ""):
            raise RuntimeError(f"character lacks beast module: source_id={sid} comment={e.get('comment')}")

    runtime_blob = "\n".join(
        [e.get("comment", "") + "\n" + e.get("content", "") + "\n" + "\n".join(e.get("keys", [])) for e in entries]
    )
    leaked = []
    leak_context = []
    for name in changed_formal_names:
        new_name = name_map.get(name, "")
        probe = runtime_blob.replace(new_name, "") if new_name else runtime_blob
        if name in probe:
            leaked.append(name)
            idx = probe.find(name)
            leak_context.append(probe[max(0, idx-80):idx+120].replace("\n", " "))
    if leaked:
        raise RuntimeError("old formal names leaked: " + ", ".join(leaked) + " | contexts: " + " || ".join(leak_context))

    banned = ["超级赛亚人", "白金之星", "幻想杀手法则", "二阶堂红丸", "草薙流古武术"]
    banned_hit = [x for x in banned if x in runtime_blob]
    if banned_hit:
        raise RuntimeError("external-module contamination: " + ", ".join(banned_hit))

    expected_top = [556, 555, 554, 553, 552, 551, 550]
    if [entries[i]["insertion_order"] for i in range(7)] != expected_top:
        raise RuntimeError("top mother-template order mismatch")

    book = copy.deepcopy(get_character_book(base_card))
    book["entries"] = entries
    card = copy.deepcopy(base_card)
    set_card_entries(card, entries)

    counts = {
        "total_entries": len(entries),
        "timelines": 4,
        "core_rules": len(core_rule_entries),
        "core_settings": len(core_setting_entries),
        "main_character_bodies": 53,
        "other_character_bodies": 39,
        "character_bodies_total": 92,
        "locations": 9,
        "mvu_runtime_entries_pending": 4,
    }
    qa = [
        "# 《火影姬世界》最终世界书自动组装审计 v1.0",
        "",
        "## 基线",
        "- 咩咩全栈世界书段位：556 → 1",
        "- 世界书静态正文：本次完成",
        "- MVU 四件（变量输出格式 / 变量列表 / 变量更新规则 / initvar）：按施工边界保留给静静，不在本构建器伪造",
        "",
        "## 数量",
    ]
    qa.extend(f"- {k}: {v}" for k, v in counts.items())
    qa += [
        "",
        "## 硬验收",
        "- PASS：7组正式分区起始/结尾各且仅各1。",
        "- PASS：4条时间线完整存在，仅第一部默认 enabled=true，其余关闭。",
        "- PASS：战斗思维链为453；旧文字状态栏仅保留452关闭占位，等待MVU替换。",
        "- PASS：核心规则蓝灯与核心设定绿灯分段。",
        "- PASS：92/92角色母本完成正式名、性别转写、兽化特征合并；未复制第二套心理模型。",
        "- PASS：主要角色53条 / 其他角色39条，沿用原卡真实分区。",
        "- PASS：9/9地点，保留旧<status>触发并新增地点名普通后备触发。",
        "- PASS：全库映射中发生改名的旧正式姓名在最终运行时条目中无残留。",
        "- PASS：龙珠 / JOJO / 幻想杀手 / 草薙流古武术 / 二阶堂红丸未进入最终运行时。",
        "- PASS：开放性话题池采用当前仓库正式版本，不额外添加世界观业务规则。",
        "- PASS：宽泛触发词防爆：八门不使用裸开门，轮回眼不使用裸外道。",
        "",
        "## 产物",
        "- `dist/火影姬世界_完整世界书_v1.0.json`：独立 character_book 对象。",
        "- `dist/火影姬世界_worldbook-ready_v1.0.json`：保留原卡其他字段、仅替换为最终完整世界书的 CCv3 JSON；供后续 MVU 装配。",
        "- `dist/火影姬世界_世界书条目清单_v1.0.json`：轻量条目清单与灯态/order，便于人工复核。",
    ]
    return book, card, "\n".join(qa) + "\n"


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    QA_DIR.mkdir(parents=True, exist_ok=True)
    book, card, qa = build()
    entries = book["entries"]
    (OUT / "火影姬世界_完整世界书_v1.0.json").write_text(
        json.dumps(book, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (OUT / "火影姬世界_worldbook-ready_v1.0.json").write_text(
        json.dumps(card, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    manifest = [
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
    (OUT / "火影姬世界_世界书条目清单_v1.0.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (QA_DIR / "最终世界书自动组装审计_v1.0.md").write_text(qa, encoding="utf-8")
    print(qa)


if __name__ == "__main__":
    main()
