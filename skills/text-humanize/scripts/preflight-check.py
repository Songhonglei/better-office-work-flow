#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
text-humanize / scripts/preflight-check.py

中文文本「机械检查层」。审计前跑一次定基线，改写后再跑一次做验收。

用法:
    python3 preflight-check.py draft.md
    python3 preflight-check.py draft.md --tier short|long|literary   # 默认 long
    python3 preflight-check.py draft.md --lyrical
    python3 preflight-check.py draft.md --para-max 70 --strict
    python3 preflight-check.py 定稿.md --cut '## 本轮改动'
    python3 preflight-check.py draft.md --json

结果分三级:
    FAIL  机器残留，必须归零（半角引号 / 编号小标题 / 标点空格 / 破折号形态）
    WARN  文风项，只报数字供判断（超长段 / 同位语密度 / 词库命中）
    INFO  仅记录（段落数、人称计数）

退出码: 0 = 无 FAIL; 1 = 有 FAIL。加 --strict 时 WARN 也计入。

语言护栏（--lang，默认 auto）:
    本脚本的标点层规则是**中文专属**的 —— 半角引号、`...`、`--` 在英文里本来就是正确写法，
    拿英文稿跑会得到一堆假 FAIL。所以 auto 模式下先算 CJK 占比（口径同 SKILL.md 的
    Language Auto-Detection：CJK > 50% 才算中文模式），不足 50% 就把标点层降级为 INFO、
    不参与退出码，并在开头打出警告。需要覆盖时显式传 --lang zh。
"""

import argparse
import json
import pathlib
import re
import sys

BQ = chr(96)                 # 反引号，避免在源码里写字面量三连反引号
FENCE = BQ + BQ + BQ

CLICHE_METAPHOR = ["信使", "信笺", "叹息", "诗篇", "守望者", "耳语", "序章", "独白", "回响"]
FILLER_ADJ = ["温柔", "沉默", "浪漫", "治愈", "漫长", "细碎"]

FAIL, WARN, INFO = "FAIL", "WARN", "INFO"


def is_cjk(ch):
    o = ord(ch)
    return 0x4E00 <= o <= 0x9FFF or 0x3400 <= o <= 0x4DBF or 0xF900 <= o <= 0xFAFF


def cjk_len(s):
    return sum(1 for c in s if is_cjk(c))


def cjk_ratio(text):
    """CJK 占「CJK + 拉丁字母」的比例；口径同 SKILL.md Language Auto-Detection。"""
    cjk = cjk_len(text)
    latin = len(re.findall(r"[A-Za-z]", text))
    total = cjk + latin
    return (cjk / total) if total else 0.0


def strip_code(text):
    """去掉围栏代码块与行内代码，代码不算中文文本。"""
    text = re.sub(re.escape(FENCE) + r".*?" + re.escape(FENCE), "", text, flags=re.S)
    text = re.sub(BQ + "[^" + BQ + "\n]*" + BQ, "", text)
    return text


def body_paragraphs(text):
    """正文段落：排除标题、引用、表格、列表、分隔线。"""
    out = []
    for line in text.split("\n"):
        s = line.strip()
        if not s or s == "---" or s[0] in "#>|" or s[:2] in ("- ", "* "):
            continue
        out.append(s)
    return out


def collect(text, tier, para_max, lyrical):
    rows = []

    def add(level, scope, name, value, limit=None):
        rows.append({"level": level, "scope": scope, "name": name, "value": value, "limit": limit})

    # ---------- 标点层：FAIL ----------
    add(FAIL, "标点层", '半角双引号 "', text.count('"'), 0)
    add(FAIL, "标点层", "半角单引号 '", text.count("'"), 0)
    add(FAIL, "标点层", "中文后半角逗号/句点", len(re.findall(r"[\u4e00-\u9fff][,.]", text)), 0)
    add(FAIL, "标点层", "三点省略号 ...", text.count("..."), 0)
    # 注意左右负向断言：否则 markdown 的 --- 分隔线会被当成 -- 误报
    add(FAIL, "标点层", "非规范破折号 -- / 单 —",
        len(re.findall(r"(?<!-)--(?!-)", text)) + len(re.findall(r"(?<!—)—(?!—)", text)), 0)
    add(FAIL, "标点层", "破折号前后带空格", len(re.findall(r"[ \t]——|——[ \t]", text)), 0)
    add(FAIL, "标点层", "标点周边空格",
        len(re.findall(r"[，。！？；：、）】”’][ \t]|[ \t][（【“‘]", text)), 0)

    # ---------- 标点层：INFO ----------
    em = text.count("——")
    add(INFO, "标点层", "标准破折号 ——(总量)", em)
    add(INFO, "标点层", "中文省略号 ……", text.count("……"))
    if tier == "short":
        add(FAIL, "标点层", "破折号 [短文本应删]", em, 0)

    # ---------- 排版 ----------
    add(FAIL, "排版", "编号式小标题",
        len(re.findall(r"^\s{0,6}(?:[0-9]{1,2}[、.．)）]|[一二三四五六七八九十]+[、.．]|0[0-9]\s)", text, re.M)), 0)

    paras = body_paragraphs(text)
    lens = [cjk_len(p) for p in paras] or [0]
    add(WARN, "排版", "超 %d 字段落数" % para_max, sum(1 for n in lens if n > para_max), 0)
    add(INFO, "排版", "最长段落(字)", max(lens))
    add(INFO, "排版", "段落总数", len(paras))

    # ---------- 人称 ----------
    add(INFO, "人称", "「我们」", text.count("我们"))
    add(INFO, "人称", "「我」(不含我们)", len(re.findall(r"我(?!们)", text)))

    # ---------- R 类（抒情 / 文学）----------
    if lyrical or tier == "literary":
        sents = [s for s in re.split(r"[。！？!?\n]", text) if cjk_len(s) >= 4]
        appo = run = longest = 0
        for s in sents:
            if re.search(r"[，,][^，。！？；：\n]{2,14}的[^，。！？；：\n]{2,10}", s):
                appo += 1
                run += 1
                longest = max(longest, run)
            else:
                run = 0
        add(INFO, "R类", "同位语形态 X，Y的Z(粗计)", appo)
        add(WARN, "R类", "同位语最长连续句数", longest, 2)
        add(WARN, "R类", "陈腐喻体词库命中", sum(text.count(w) for w in CLICHE_METAPHOR), 0)
        add(WARN, "R类", "万能形容词词库命中", sum(text.count(w) for w in FILLER_ADJ), 2)
        detail = {w: text.count(w) for w in CLICHE_METAPHOR + FILLER_ADJ if text.count(w)}
        if detail:
            add(INFO, "R类", "词库命中明细", detail)

    return rows


def demote_punctuation(rows):
    """非中文模式：标点层规则不适用，FAIL 降级为 INFO（保留数字，不参与退出码）。"""
    for r in rows:
        if r["scope"] == "标点层":
            r["level"] = INFO
            r["limit"] = None
    return rows


def grade(row):
    """返回 OK / FAIL / warn / ok / - ，以及是否算失败。"""
    lv, val, lim = row["level"], row["value"], row["limit"]
    if lv == INFO or lim is None:
        return "-", False
    if isinstance(val, dict):
        return "-", False
    bad = val != lim if lim == 0 else val > lim
    if lv == FAIL:
        return ("FAIL" if bad else "OK"), bad
    return ("warn" if bad else "ok"), False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("path")
    ap.add_argument("--tier", choices=["short", "long", "literary"], default="long")
    ap.add_argument("--lyrical", action="store_true")
    ap.add_argument("--para-max", type=int, default=70)
    ap.add_argument("--strict", action="store_true", help="WARN 也计入退出码")
    ap.add_argument("--cut", default=None, help="在此标记处截断（丢弃尾注），只测正文")
    ap.add_argument("--lang", choices=["auto", "zh", "en"], default="auto",
                    help="auto（默认）按 CJK 占比判定；zh 强制按中文模式；en 强制不判标点层")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()

    raw = pathlib.Path(a.path).read_text(encoding="utf-8")
    if a.cut and a.cut in raw:
        raw = raw.split(a.cut)[0]
    text = strip_code(raw)

    ratio = cjk_ratio(text)
    if a.lang == "zh":
        zh_mode = True
    elif a.lang == "en":
        zh_mode = False
    else:
        zh_mode = ratio >= 0.5

    rows = collect(text, a.tier, a.para_max, a.lyrical)
    if not zh_mode:
        rows = demote_punctuation(rows)
    graded = [(r, *grade(r)) for r in rows]
    fails = [r for r, mark, bad in graded if mark == "FAIL"]
    warns = [r for r, mark, bad in graded if mark == "warn"]

    lang_note = None
    if not zh_mode:
        lang_note = ("非中文文本（中文占比 %.0f%% < 50%%），标点层规则不适用，已降级为 INFO。"
                     "本脚本只覆盖中文文本；确需强制判定请传 --lang zh。" % (ratio * 100))

    if a.json:
        out = {
            "file": a.path, "tier": a.tier, "cjk": cjk_len(text),
            "cjk_ratio": round(ratio, 3), "zh_mode": zh_mode,
            "rows": [{"level": r["level"], "scope": r["scope"], "name": r["name"],
                      "value": r["value"], "limit": r["limit"], "mark": m} for r, m, _ in graded],
            "fail": len(fails), "warn": len(warns),
        }
        if lang_note:
            out["lang_note"] = lang_note
        print(json.dumps(out, ensure_ascii=False, indent=2))
        return 1 if (fails or (a.strict and warns)) else 0

    print("文件: %s" % a.path)
    print("档位: %s    中文字数: %d" % (a.tier, cjk_len(text)))
    if lang_note:
        print("!! %s" % lang_note)
    print("-" * 66)
    scope = None
    for r, mark, bad in graded:
        if r["scope"] != scope:
            print("[%s]" % r["scope"])
            scope = r["scope"]
        val = r["value"] if not isinstance(r["value"], dict) else json.dumps(r["value"], ensure_ascii=False)
        lim = "" if r["level"] == INFO or r["limit"] is None else "  (限 %s)" % r["limit"]
        print("  %-4s %-28s %8s%s" % (mark, r["name"], val, lim))
    print("-" * 66)
    if fails:
        print("结论: FAIL %d 项 -> 修完重跑，不归零不交付" % len(fails))
        for r in fails:
            print("   x %s = %s (限 %s)" % (r["name"], r["value"], r["limit"]))
    elif warns:
        print("结论: 无 FAIL，WARN %d 项（文风取舍，交作者判断）" % len(warns))
    else:
        print("结论: 全部达标")
    return 1 if (fails or (a.strict and warns)) else 0


if __name__ == "__main__":
    sys.exit(main())
