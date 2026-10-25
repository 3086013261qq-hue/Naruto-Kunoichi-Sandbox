#!/usr/bin/env python3
from __future__ import annotations

import copy
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SET_DIR = ROOT / "worldbook" / "settings"
CHAR_DIR = ROOT / "worldbook" / "characters"
TIMELINE_DIR = ROOT / "worldbook" / "timeline"
LOCATION_DIR = ROOT / "worldbook" / "locations"
DIST = ROOT / "dist" / "火影姬世界_完整世界书_v1.0.json"
READY = ROOT / "dist" / "火影姬世界_worldbook-ready_v1.0.json"
BASE = ROOT / "火影忍者_沙盒_纯设定基底_v0.1.json"
CHAR_BACKUP = ROOT / "火影忍者_沙盒_角色条目拆分备份_v0.1.json"
MAPPING = CHAR_DIR / "06_火影姬全库姓名映射_v1.0.md"
REPORT = ROOT / "qa" / "最终世界书逐源对照审计_v1.0.md"

RUNTIME_SETTING_FILES = {
    "00_火影姬AU核心设定_v0.3.md",
    "01_忍术与技能体系_含AU兼容修订.md",
    "02_核心规则_含AU兼容修订.md",
    "04_荷尔蒙查克拉运行细则_v0.4.md",
    "05_成人玩具忍具与通灵尾兽活体铠甲_v0.5.md",
    "06_三大圣地特殊通灵活体铠甲_v0.6.md",
    "07_特殊通灵兽活体铠甲补充_v0.7.md",
    "09_忍术荷尔蒙查克拉总则_v0.9.md",
    "10_女女相恋社会与家庭生育总则_v1.0.md",
    "11_忍阶实力阈值与瞳术进化补遗_v1.1.md",
    "12_火影姬战斗思维链_v1.0.md",
    "13_火影姬开放性话题池_v1.0.md",
}
META_SETTING_FILES = {
    "03_输出状态与记忆规则.md",
    "08_世界书灯态与激活策略_v0.8.md",
}
BATCH_FILES = [
    CHAR_DIR / "02_角色精修_Batch01_v0.1.md",
    CHAR_DIR / "03_角色精修_Batch02_v0.1.md",
    CHAR_DIR / "04_角色精修_Batch03_v0.1.md",
    CHAR_DIR / "05_角色精修_Batch04_收官_v0.1.md",
]
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
EXPECTED_CORE_RULES = {
    "核心规则:火影姬世界总则",
    "核心规则:世界观校验/过滤",
    "核心规则:金钱",
    "核心规则:任务等级说明",
    "核心规则:荷尔蒙查克拉循环",
    "核心规则:忍术与荷尔蒙查克拉总则",
    "核心规则:玩具型忍具体系",
    "核心规则:活体铠甲基础构造",
    "核心规则:通灵兽与尾兽铠化",
    "核心规则:女女相恋社会与家庭生育总则",
    "核心规则:忍阶实力阈值与身份分离",
    "核心规则:火影姬开放性话题池",
}

GENDER_REPLACEMENTS = [
    ("成为火影的男人", "成为火影"), ("火影的男人", "火影"),
    ("男朋友", "女朋友"), ("男性朋友", "女性朋友"),
    ("美少年", "美少女"), ("男孩子", "女孩子"), ("男孩", "女孩"),
    ("男童", "女童"), ("少年", "少女"), ("男人", "女人"),
    ("男性", "女性"), ("丈夫", "妻子"), ("男友", "女友"),
    ("父亲", "母亲"), ("爸爸", "妈妈"), ("祖父", "祖母"),
    ("爷爷", "奶奶"), ("兄长", "姐姐"), ("哥哥", "姐姐"),
    ("弟弟", "妹妹"), ("兄弟", "姐妹"), ("儿子", "女儿"),
    ("父辈", "母辈"), ("父权", "家族权威"), ("父系", "家系"),
    ("老爷子", "高龄女忍者"), ("老头", "高龄女忍者"),
    ("老者", "高龄女忍者"), ("山羊胡", "清晰的岁月纹与沉稳神态"),
    ("大叔", "成熟御姐"),
]
SINGLE_ALIAS_RULES = [
    (r"鼬(?!鼠)", "伊月"), (r"兜(?!帽|鍪)", "兜美"),
    (r"凯(?!旋)", "凯莉"), (r"斑(?!纹|点|驳|块|痕|马)", "斑奈"),
    (r"李(?=[，。！？、与和的在对被将是曾已正则])", "洛可"),
]

issues: list[str] = []
stats: dict[str, int] = {}


def fail(msg: str) -> None:
    issues.append(msg)


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def load(path: Path):
    return json.loads(read(path))


def card_entries(card: dict) -> list:
    if "data" in card:
        return card["data"]["character_book"]["entries"]
    return card["character_book"]["entries"]


def parse_name_mapping() -> tuple[dict[str, str], list[str]]:
    mapping: dict[str, str] = {}
    changed: list[str] = []
    for line in read(MAPPING).splitlines():
        if not line.startswith("|") or line.startswith("|---"):
            continue
        cols = [x.strip() for x in line.strip().strip("|").split("|")]
        if len(cols) < 4 or cols[0].startswith("源文本姓名"):
            continue
        source, formal, shorts = cols[:3]
        old_aliases = [x.strip() for x in source.split(" / ") if x.strip()]
        formal_aliases = [x.strip() for x in shorts.split(" / ") if x.strip()]
        if not old_aliases or not formal:
            continue
        old_formal = old_aliases[0]
        if old_formal != formal:
            mapping[old_formal] = formal
            changed.append(old_formal)
        preferred = next((x for x in formal_aliases if x != formal and "火影" not in x and "仙人" not in x and x not in {"佩恩", "阿飞", "赤砂之蝎"}), formal_aliases[0] if formal_aliases else formal)
        for old in old_aliases[1:]:
            if old in {formal, preferred}:
                continue
            if len(old) >= 2:
                mapping[old] = preferred
    return mapping, sorted(set(changed), key=len, reverse=True)


def replace_names(text: str, mapping: dict[str, str]) -> str:
    for old in sorted(mapping, key=len, reverse=True):
        if old != mapping[old]:
            text = text.replace(old, mapping[old])
    return text


def replace_single_aliases(text: str) -> str:
    for pat, repl in SINGLE_ALIAS_RULES:
        text = re.sub(pat, repl, text)
    return text


def feminize(text: str) -> str:
    protected = {"其他人": "__OTHER_PEOPLE__", "其他": "__OTHER__", "他人": "__OTHERS__"}
    for src, mark in protected.items():
        text = text.replace(src, mark)
    text = text.replace("他们", "她们")
    for old, new in GENDER_REPLACEMENTS:
        text = text.replace(old, new)
    text = text.replace("他", "她")
    for src, mark in protected.items():
        text = text.replace(mark, src)
    return text.replace("父母", "双亲")


def extract_tag_blocks(text: str, namespace: str) -> dict[str, str]:
    pat = re.compile(rf"<(?P<tag>{re.escape(namespace)}:[^>]+)>[\s\S]*?</(?P=tag)>")
    out: dict[str, str] = {}
    for m in pat.finditer(text):
        block = m.group(0).strip()
        tag = re.match(r"<([^>]+)>", block).group(1)
        title = tag.split(":", 1)[1]
        if title in out:
            fail(f"设定源重复标题: {namespace}:{title}")
        out[title] = block
    return out


def extract_code_fence(text: str) -> str:
    m = re.search(r"```(?:text)?\s*\n([\s\S]*?)\n```", text)
    return m.group(1).strip() if m else ""


def extract_section(text: str, heading: str) -> str:
    pat = re.compile(rf"^## {re.escape(heading)}\s*$\n(?P<body>[\s\S]*?)(?=^---\s*$|^## |\Z)", re.M)
    m = pat.search(text)
    return m.group("body").strip() if m else ""


def parse_patches() -> dict[int, dict]:
    out: dict[int, dict] = {}
    sec = re.compile(r"^## (?P<name>[^\n]+)\n(?P<body>.*?)(?=^---\s*$|\Z)", re.M | re.S)
    for path in BATCH_FILES:
        for m in sec.finditer(read(path)):
            name, body = m.group("name").strip(), m.group("body")
            sm = re.search(r"源条目：\s*(\d+)(?:\s*[–—-]\s*(\d+))?", body)
            if not sm:
                continue
            km = re.search(r"正式关键词：`([^`]+)`", body)
            bm = re.search(r"兽化特征:\s*\n((?:- [^\n]+\n?){4})", body)
            if not km or not bm:
                fail(f"角色补丁解析失败: {path.name}/{name}")
                continue
            patch = {"name": name, "key": km.group(1), "beast": "兽化特征:\n" + bm.group(1).rstrip()}
            for sid in range(int(sm.group(1)), int(sm.group(2) or sm.group(1)) + 1):
                if sid in out:
                    fail(f"角色补丁 source_id 重复: {sid}")
                out[sid] = patch
    return out


def expected_character(entry: dict, patch: dict, mapping: dict[str, str]) -> tuple[str, str]:
    original = entry.get("content", "")
    was_male = bool(re.search(r"性别\s*:\s*男", original))
    content = replace_single_aliases(replace_names(original, mapping))
    comment = replace_single_aliases(replace_names(entry.get("comment", ""), mapping))
    if was_male:
        content = feminize(content)
        content = re.sub(r"性别\s*:\s*男", "性别:女", content)
    else:
        content = re.sub(r"性别\s*:\s*女", "性别:女", content)
    name = patch["name"]
    content = re.sub(r"^名字\s*:[^\n]*", f"名字:{name}", content, count=1, flags=re.M)
    content = re.sub(r"<[^/<>\n]+character>", f"<{name}character>", content, count=1)
    content = re.sub(r"</[^<>\n]+character>", f"</{name}character>", content, count=1)
    if "兽化特征:" not in content:
        close = f"</{name}character>"
        if close in content:
            content = content.replace(close, "\n\n" + patch["beast"] + "\n" + close, 1)
        else:
            content = content.rstrip() + "\n\n" + patch["beast"] + "\n"
    if name == "猿飞日和":
        content = content.replace("矮小的高龄女忍者", "体态利落的高龄女火影")
        content = content.replace("矮小高龄女忍者", "体态利落的高龄女火影")
    if name == "漩涡鸣子":
        content = content.replace("成为火影的女人", "成为火影")
    return comment, content


def between(entries: list[dict], start: str, end: str) -> list[dict]:
    comments = [e.get("comment", "") for e in entries]
    try:
        a, b = comments.index(start), comments.index(end)
    except ValueError:
        fail(f"分区缺失: {start} / {end}")
        return []
    if a >= b:
        fail(f"分区顺序错误: {start} 在 {end} 之后")
        return []
    return entries[a + 1:b]


def compile_key(key: str):
    if not (key.startswith("/") and key.endswith("/s")):
        raise ValueError(key)
    return re.compile(key[1:-2], re.S)


def report() -> None:
    status = "PASS" if not issues else "FAIL"
    lines = [
        "# 《火影姬世界》最终世界书逐源对照审计 v1.0", "",
        f"## 结论：{status}", "",
        "本审计独立读取冻结源文件、只读角色母本与最终 dist，不以构建器自身的 PASS 作为内容正确性的证明。", "",
        "## 覆盖", "",
    ]
    for k, v in stats.items():
        lines.append(f"- {k}: {v}")
    lines += ["", "## 检查项", ""]
    if issues:
        lines += [f"- FAIL: {x}" for x in issues]
    else:
        lines += [
            "- PASS：完整世界书与 worldbook-ready 内嵌 entries 完全一致。",
            "- PASS：worldbook-ready 除 character_book 外完全继承原卡容器字段。",
            "- PASS：settings 所有运行时源文件均已分类；无新增未装配数字源文件。",
            "- PASS：蓝灯、绿灯、19术系、战斗链、开放话题池逐源正文一致。",
            "- PASS：92/92 角色逐条正文与母本+确定性补丁完全一致；secondary_keys 未丢失。",
            "- PASS：四卷时间线逐段一致，九地点逐段一致。",
            "- PASS：角色/地点 insertion_order 遵守母版低位起排并保持原相对顺序。",
            "- PASS：月读/无限月读、八门门名、轮回眼外道关键词完成语义触发测试。",
            "- PASS：旧正式姓名与外部污染未进入最终运行时。",
        ]
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    mapping, changed_names = parse_name_mapping()
    book = load(DIST)
    ready = load(READY)
    base = load(BASE)
    entries = book["entries"]
    ready_entries = card_entries(ready)
    stats["total_entries"] = len(entries)

    if entries != ready_entries:
        fail("完整世界书 entries 与 worldbook-ready 内嵌 entries 不一致")
    base_cmp = copy.deepcopy(base)
    ready_cmp = copy.deepcopy(ready)
    if "data" in base_cmp:
        base_cmp["data"].pop("character_book", None)
        ready_cmp["data"].pop("character_book", None)
    else:
        base_cmp.pop("character_book", None)
        ready_cmp.pop("character_book", None)
    if base_cmp != ready_cmp:
        fail("worldbook-ready 修改了 character_book 之外的原卡字段")

    ids = [e.get("id") for e in entries]
    if ids != list(range(len(entries))):
        fail("最终 entries id 不是连续 0..N-1")
    for i, e in enumerate(entries):
        if e.get("extensions", {}).get("display_index") != i:
            fail(f"display_index 错位: id={i}")
            break

    numeric = {p.name for p in SET_DIR.glob("[0-9][0-9]_*.md")}
    unclassified = numeric - RUNTIME_SETTING_FILES - META_SETTING_FILES
    missing_files = RUNTIME_SETTING_FILES - numeric
    if unclassified:
        fail("settings 存在未分类/可能漏装源文件: " + ", ".join(sorted(unclassified)))
    if missing_files:
        fail("settings 正式运行时源文件缺失: " + ", ".join(sorted(missing_files)))
    stats["runtime_setting_files"] = len(RUNTIME_SETTING_FILES)

    marker_pairs = ["记忆相关", "输出规则", "核心规则", "核心设定", "主要角色", "其他角色", "地点"]
    comments = [e.get("comment", "") for e in entries]
    for name in marker_pairs:
        for side in ("起始", "结尾"):
            m = f"【{name}:{side}】"
            if comments.count(m) != 1:
                fail(f"分区标记数量错误: {m}={comments.count(m)}")

    # Output and fixed skeleton.
    fixed = {
        "🗑️清空局部变量(别关)": 556, "【记忆相关:起始】": 555,
        "日常记忆存储": 554, "重大记忆存储": 553, "玩家身世背景": 552,
        "【记忆相关:结尾】": 551, "【输出规则:起始】": 550,
        "战斗思维链": 453, "状态栏-默认（MVU待替换）": 452,
        "【输出规则:结尾】": 451, "【核心规则:起始】": 450,
        "【核心规则:结尾】": 401, "【核心设定:起始】": 400,
        "【核心设定:结尾】": 301, "【主要角色:起始】": 300,
        "【主要角色:结尾】": 201, "【其他角色:起始】": 200,
        "【其他角色:结尾】": 101, "【地点:起始】": 100, "【地点:结尾】": 1,
    }
    by_comment = {e.get("comment", ""): e for e in entries}
    for c, order in fixed.items():
        if c not in by_comment or by_comment[c].get("insertion_order") != order:
            fail(f"固定段位错误: {c} 应为 {order}")

    # Settings content coverage.
    core_blocks: dict[str, str] = {}
    for fn in [
        "00_火影姬AU核心设定_v0.3.md", "04_荷尔蒙查克拉运行细则_v0.4.md",
        "05_成人玩具忍具与通灵尾兽活体铠甲_v0.5.md", "06_三大圣地特殊通灵活体铠甲_v0.6.md",
        "07_特殊通灵兽活体铠甲补充_v0.7.md", "09_忍术荷尔蒙查克拉总则_v0.9.md",
        "10_女女相恋社会与家庭生育总则_v1.0.md", "11_忍阶实力阈值与瞳术进化补遗_v1.1.md",
    ]:
        for title, block in extract_tag_blocks(read(SET_DIR / fn), "核心设定").items():
            if title in core_blocks:
                fail(f"跨 settings 文件重复核心设定标题: {title}")
            core_blocks[title] = replace_names(block, mapping)

    special = read(SET_DIR / "02_核心规则_含AU兼容修订.md")
    tags = {"money_rules": "核心规则:金钱", "任务等级说明": "核心规则:任务等级说明", "Worldview_Boundary_and_Filter": "核心规则:世界观校验/过滤", "班级座位": "核心设定:忍者学校"}
    expected_content: dict[str, str] = {}
    for tag, comment in tags.items():
        m = re.search(rf"<{re.escape(tag)}>[\s\S]*?</{re.escape(tag)}>", special)
        if not m:
            fail(f"核心规则源块缺失: {tag}")
        else:
            expected_content[comment] = replace_names(m.group(0).strip(), mapping)

    for title, block in core_blocks.items():
        comment = ("核心规则:" if title in BLUE_TITLES else "核心设定:") + title
        expected_content[comment] = block

    skills = extract_tag_blocks(read(SET_DIR / "01_忍术与技能体系_含AU兼容修订.md"), "技能")
    stats["skill_systems"] = len(skills)
    if len(skills) != 19:
        fail(f"正式术系应为19，实际源文件为 {len(skills)}")
    s11 = read(SET_DIR / "11_忍阶实力阈值与瞳术进化补遗_v1.1.md")
    patches = {"写轮眼": extract_section(s11, "原卡补遗:写轮眼进化条件"), "白眼": extract_section(s11, "原卡补遗:白眼与转生眼进化条件")}
    for title, block in skills.items():
        if title in patches and patches[title]:
            close = f"</技能:{title}>"
            block = block.replace(close, "\n\n【正式进化补遗】\n" + patches[title] + "\n" + close, 1)
        expected_content[f"技能:{title}"] = replace_names(block, mapping)

    expected_content["核心规则:火影姬开放性话题池"] = extract_code_fence(read(SET_DIR / "13_火影姬开放性话题池_v1.0.md"))
    expected_content["战斗思维链"] = extract_code_fence(read(SET_DIR / "12_火影姬战斗思维链_v1.0.md"))

    generated_runtime = {e.get("comment", ""): e for e in entries}
    for comment, content in expected_content.items():
        if comment not in generated_runtime:
            fail(f"源条目漏装: {comment}")
        elif generated_runtime[comment].get("content", "") != content:
            fail(f"源正文被更改/错装: {comment}")

    actual_core_rules = {e.get("comment") for e in between(entries, "【核心规则:起始】", "【核心规则:结尾】")}
    if actual_core_rules != EXPECTED_CORE_RULES:
        fail("核心规则条目集合不符: missing=" + str(sorted(EXPECTED_CORE_RULES - actual_core_rules)) + " extra=" + str(sorted(actual_core_rules - EXPECTED_CORE_RULES)))
    stats["core_rules"] = len(actual_core_rules)

    expected_green = {k for k in expected_content if k.startswith("核心设定:") or k.startswith("技能:")}
    actual_green = {e.get("comment") for e in between(entries, "【核心设定:起始】", "【核心设定:结尾】")}
    if expected_green != actual_green:
        fail("核心设定条目集合不符: missing=" + str(sorted(expected_green - actual_green)) + " extra=" + str(sorted(actual_green - expected_green)))
    stats["core_settings"] = len(actual_green)

    # Timeline exact comparison.
    tpaths = [TIMELINE_DIR / "01_前传.md", TIMELINE_DIR / "02_第一部.md", TIMELINE_DIR / "03_疾风传.md", TIMELINE_DIR / "04_博乃传.md"]
    timeline_entries = [e for e in between(entries, "【输出规则:起始】", "【输出规则:结尾】") if str(e.get("comment", "")).startswith("时间线-")]
    if len(timeline_entries) != 4:
        fail(f"时间线条目数错误: {len(timeline_entries)}")
    else:
        for path, ent in zip(tpaths, timeline_entries):
            text = read(path)
            title = re.search(r"^# (.+)$", text, re.M).group(1).strip()
            body = replace_names(re.search(r"<world_timeline>[\s\S]*?</world_timeline>", text).group(0).strip(), mapping)
            if ent.get("comment") != title or ent.get("content") != body:
                fail(f"时间线正文/标题不一致: {path.name}")
            if ent.get("insertion_order") != 454:
                fail(f"时间线段位不是454: {title}")
        if sum(bool(e.get("enabled")) for e in timeline_entries) != 1 or not next((e.get("enabled") for e in timeline_entries if "第一部" in e.get("comment", "")), False):
            fail("时间线多选一灯态错误")
    stats["timelines"] = len(timeline_entries)

    # Characters: full-text equality after only sanctioned deterministic transformations.
    backup = load(CHAR_BACKUP)
    source_chars = {int(e["id"]): e for e in backup["character_entries"]}
    patch_map = parse_patches()
    expected_ids = set(range(10, 49)) | set(range(51, 104))
    if set(source_chars) != expected_ids:
        fail("只读角色母本不是预期 92 source ids")
    if set(patch_map) != expected_ids:
        fail("四批角色补丁未覆盖完整 92 source ids")

    main_chars = between(entries, "【主要角色:起始】", "【主要角色:结尾】")
    other_chars = between(entries, "【其他角色:起始】", "【其他角色:结尾】")
    stats["main_character_bodies"] = len(main_chars)
    stats["other_character_bodies"] = len(other_chars)
    if len(main_chars) != 53 or len(other_chars) != 39:
        fail(f"角色分区数量错误: main={len(main_chars)} other={len(other_chars)}")
    if [e.get("insertion_order") for e in main_chars] != list(range(202, 255)):
        fail("主要角色 insertion_order 未按母版 202..254 保留源相对顺序")
    if [e.get("insertion_order") for e in other_chars] != list(range(102, 141)):
        fail("其他角色 insertion_order 未按母版 102..140 保留源相对顺序")

    for sid, ent in list(zip(range(51, 104), main_chars)) + list(zip(range(10, 49), other_chars)):
        if sid not in source_chars or sid not in patch_map:
            continue
        exp_comment, exp_content = expected_character(source_chars[sid], patch_map[sid], mapping)
        if ent.get("comment") != exp_comment:
            fail(f"角色 comment 被误改: source_id={sid}")
        if ent.get("content") != exp_content:
            fail(f"角色正文与母本+确定性补丁不一致: source_id={sid} {patch_map[sid]['name']}")
        if ent.get("keys") != [patch_map[sid]["key"]]:
            fail(f"角色正式关键词错装: source_id={sid} {patch_map[sid]['name']}")
        if ent.get("secondary_keys", []) != source_chars[sid].get("secondary_keys", []):
            fail(f"角色二级时间条件丢失/更改: source_id={sid} {patch_map[sid]['name']}")
        ex = ent.get("extensions", {})
        if ent.get("constant") or not ent.get("selective") or not ent.get("enabled") or not ent.get("use_regex") or ex.get("probability") != 100 or not ex.get("exclude_recursion") or not ex.get("prevent_recursion"):
            fail(f"角色灯态/递归配置错误: source_id={sid} {patch_map[sid]['name']}")

    # Locations exact body + source key preservation + low-order layout.
    loc_entries = between(entries, "【地点:起始】", "【地点:结尾】")
    lpaths = sorted(LOCATION_DIR.glob("[0-9][0-9]_*.md"))
    stats["locations"] = len(loc_entries)
    if len(lpaths) != 9 or len(loc_entries) != 9:
        fail(f"地点应为9: source={len(lpaths)} final={len(loc_entries)}")
    if [e.get("insertion_order") for e in loc_entries] != list(range(2, 11)):
        fail("地点 insertion_order 未按母版 2..10 保留源相对顺序")
    for path, ent in zip(lpaths, loc_entries):
        text = read(path)
        name = re.search(r"^# 地点:(.+)$", text, re.M).group(1).strip()
        body = replace_names(re.search(r"(<地点_[^>]+>[\s\S]*?</地点_[^>]+>)", text).group(1).strip(), mapping)
        if ent.get("comment") != f"地点:{name}" or ent.get("content") != body:
            fail(f"地点正文/标题被更改: {path.name}")
        km = re.search(r"<!-- keys: (\[.*?\]) -->", text)
        original_keys = json.loads(km.group(1)) if km else []
        if any(k not in ent.get("keys", []) for k in original_keys):
            fail(f"地点原 <status> 触发丢失: {name}")
        if len(ent.get("keys", [])) < len(original_keys) + 1:
            fail(f"地点缺少 MVU 普通名称后备触发: {name}")
        if ent.get("constant") or not ent.get("selective") or not ent.get("use_regex"):
            fail(f"地点灯态错误: {name}")

    # Regex semantic tests for known collision points.
    def key_for(comment: str):
        e = generated_runtime.get(comment)
        if not e or len(e.get("keys", [])) != 1:
            fail(f"关键词条目缺失/非单 key: {comment}")
            return None
        try:
            return compile_key(e["keys"][0])
        except Exception as exc:
            fail(f"正则不可编译: {comment}: {exc}")
            return None

    rx = key_for("技能:写轮眼")
    if rx:
        if not rx.search("<story_scene>伊月发动月读</story_scene>"):
            fail("写轮眼 key 无法触发普通月读")
        if rx.search("<story_scene>无限月读覆盖世界</story_scene>"):
            fail("无限月读错误触发写轮眼条目")
    rx = key_for("技能:八门遁甲")
    if rx:
        if not rx.search("<story_scene>开启第七门·惊门</story_scene>") or not rx.search("<story_scene>八门遁甲</story_scene>"):
            fail("八门 key 无法触发完整门名/八门遁甲")
        if rx.search("<story_scene>她推开门走出房间</story_scene>") or rx.search("<story_scene>休门</story_scene>"):
            fail("八门 key 仍被裸开门/裸门名误触发")
    rx = key_for("技能:轮回眼")
    if rx:
        if not rx.search("<story_scene>召唤外道魔像</story_scene>"):
            fail("轮回眼 key 无法触发外道魔像")
        if rx.search("<story_scene>外道</story_scene>"):
            fail("轮回眼 key 仍使用裸外道")

    # Runtime old-name and contamination checks.
    runtime_blob = "\n".join(str(e.get("comment", "")) + "\n" + str(e.get("content", "")) + "\n" + "\n".join(e.get("keys", [])) for e in entries)
    leaked = []
    for old in changed_names:
        new = mapping.get(old, "")
        probe = runtime_blob.replace(new, "") if new else runtime_blob
        if old in probe:
            leaked.append(old)
    if leaked:
        fail("最终运行时残留已改名旧正式名: " + ", ".join(leaked))
    banned = ["超级赛亚人", "白金之星", "幻想杀手法则", "二阶堂红丸", "草薙流古武术"]
    hits = [x for x in banned if x in runtime_blob]
    if hits:
        fail("最终运行时混入外部体系: " + ", ".join(hits))

    report()
    if issues:
        print("FINAL AUDIT FAIL")
        for x in issues:
            print("-", x)
        raise SystemExit(1)
    print("FINAL AUDIT PASS")
    for k, v in stats.items():
        print(f"{k}={v}")


if __name__ == "__main__":
    main()
