#!/usr/bin/env python3
"""
小红书风格卡片生成器 —— 统一简洁布局

布局参考：米白/浅米色背景、顶部「标签 + 引号装饰」、中间大字居中文案、
底部短横线 + 左页码 / 右账号。支持多主题配色与自定义 footer 参数。

用法:
  python3 card_generator.py --theme warm --lines "周五了\n你还活着吗" --subtitle "关于活着" --page-number 1 --total-pages 6 --account "@雨夜心灯" -o card.png
  python3 card_generator.py --all-themes --demo --output-dir ./demo
"""

import os
import sys
import json
import math
import subprocess
import tempfile
import argparse
from pathlib import Path

BASE_DIR = Path(__file__).parent
CHROME_CANDIDATES = [
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
    "/usr/bin/google-chrome",
    "/usr/bin/chromium",
]

# ─── 主题配置 ──────────────────────────────────────────────────────
# 每个主题：背景、文字、点缀、装饰元素、字体
# 来源：text-to-elegant-image 仓库 18 种（其中小红书拆 A/B 两模式）+ 4 种年轻人风格 + warm 原创 = 24 种
THEMES = {
    # ── 原创风格 ──────────────────────────────────────────────
    "warm": {
        "name": "温暖哲思",
        "bg": "#F7F3ED",
        "bg_gradient": None,
        "text": "#3A3229",
        "muted": "#8C8070",
        "accent": "#C4A882",
        "accent2": "#D9C6B0",
        "font_main": "'Songti SC', 'STSong', 'SimSun', 'Noto Serif SC', serif",
        "font_tag": "'PingFang SC', 'Microsoft YaHei', sans-serif",
        "quote_color": "#C4A882",
        "deco": "warm",
        "letter_spacing": 4,
        "google_fonts": [],
    },
    # ── 年轻人风格（新增，非仓库原始） ────────────────────────
    "y2k": {
        "name": "Y2K 千禧潮酷",
        "bg": "#0B0B15",
        "bg_gradient": "linear-gradient(160deg, #1A0B2E 0%, #2D1B4E 40%, #0B3D4C 100%)",
        "text": "#FFFFFF",
        "muted": "#B8B8D1",
        "accent": "#FF00CC",
        "accent2": "#00FFFF",
        "font_main": "'PingFang SC', 'Helvetica Neue', 'Arial', 'Heiti SC', sans-serif",
        "font_tag": "'PingFang SC', 'Helvetica Neue', sans-serif",
        "quote_color": "#00FFFF",
        "deco": "stars",
        "letter_spacing": 3,
        "google_fonts": [],
    },
    "doodle": {
        "name": "手绘涂鸦",
        "bg": "#FFFEF7",
        "bg_gradient": None,
        "text": "#2C2C2C",
        "muted": "#6B6B6B",
        "accent": "#FF6B35",
        "accent2": "#FFD23F",
        "font_main": "'ZCOOL KuaiLe', 'Caveat', 'PingFang SC', 'Microsoft YaHei', cursive",
        "font_tag": "'ZCOOL KuaiLe', 'Caveat', 'PingFang SC', cursive",
        "quote_color": "#FF6B35",
        "deco": "doodles",
        "letter_spacing": 2,
        "google_fonts": ["ZCOOL KuaiLe", "Caveat:wght@400;700"],
    },
    "pop": {
        "name": "渐变波普",
        "bg": "#FFF0F5",
        "bg_gradient": "linear-gradient(135deg, #FFF0F5 0%, #E6F3FF 50%, #FFF9E6 100%)",
        "text": "#1A1A2E",
        "muted": "#5A5A6E",
        "accent": "#FF3366",
        "accent2": "#3366FF",
        "font_main": "'PingFang SC', 'Arial Black', 'Impact', 'Heiti SC', sans-serif",
        "font_tag": "'PingFang SC', 'Arial Black', sans-serif",
        "quote_color": "#FF3366",
        "deco": "dots",
        "letter_spacing": 3,
        "google_fonts": [],
    },
    "minimal": {
        "name": "极简日系",
        "bg": "#FAFAFA",
        "bg_gradient": None,
        "text": "#1A1A1A",
        "muted": "#888888",
        "accent": "#1A1A1A",
        "accent2": "#E0E0E0",
        "font_main": "'Songti SC', 'STSong', 'Noto Serif SC', serif",
        "font_tag": "'PingFang SC', sans-serif",
        "quote_color": "#CCCCCC",
        "deco": "none",
        "letter_spacing": 5,
        "google_fonts": [],
    },
    # ── text-to-elegant-image 仓库 18 种风格 ──────────────────
    # 01 赛博科技
    "cyberpunk": {
        "name": "赛博科技",
        "bg": "#050812",
        "bg_gradient": "linear-gradient(180deg, #050812 0%, #0C1220 100%)",
        "text": "#F0F4F8",
        "muted": "#7A8FA6",
        "accent": "#00F0FF",
        "accent2": "#B900FF",
        "font_main": "'PingFang SC', 'Helvetica Neue', 'Microsoft YaHei', sans-serif",
        "font_tag": "'PingFang SC', 'Helvetica Neue', sans-serif",
        "quote_color": "#00F0FF",
        "deco": "cyberpunk",
        "letter_spacing": 3,
        "google_fonts": [],
    },
    # 02 极简优雅
    "elegant": {
        "name": "极简优雅",
        "bg": "#FDFDFD",
        "bg_gradient": None,
        "text": "#2C2C2C",
        "muted": "#8E8E8E",
        "accent": "#D32F2F",
        "accent2": "#EAEAEA",
        "font_main": "'Songti SC', 'Noto Serif CJK SC', 'Source Han Serif CN', Georgia, serif",
        "font_tag": "'Songti SC', 'Noto Serif CJK SC', serif",
        "quote_color": "#D32F2F",
        "deco": "none",
        "letter_spacing": 4,
        "google_fonts": [],
    },
    # 03 Apple 质感
    "apple": {
        "name": "Apple 质感",
        "bg": "#F5F5F7",
        "bg_gradient": None,
        "text": "#1D1D1F",
        "muted": "#6E6E73",
        "accent": "#0066CC",
        "accent2": "#E8E8ED",
        "font_main": "-apple-system, 'BlinkMacSystemFont', 'PingFang SC', 'Segoe UI', Helvetica, Arial, sans-serif",
        "font_tag": "-apple-system, 'PingFang SC', sans-serif",
        "quote_color": "#0066CC",
        "deco": "none",
        "letter_spacing": 3,
        "google_fonts": [],
    },
    # 04 轻科技
    "cowork": {
        "name": "轻科技",
        "bg": "#F5F5F7",
        "bg_gradient": None,
        "text": "#1D1D1F",
        "muted": "#6E6E73",
        "accent": "#0066CC",
        "accent2": "#0077ED",
        "font_main": "-apple-system, 'SF Pro Display', 'SF Pro Text', 'PingFang SC', sans-serif",
        "font_tag": "-apple-system, 'SF Pro Text', 'PingFang SC', sans-serif",
        "quote_color": "#0066CC",
        "deco": "none",
        "letter_spacing": 3,
        "google_fonts": [],
    },
    # 05 报纸杂志
    "newspaper": {
        "name": "报纸杂志",
        "bg": "#F0EDE4",
        "bg_gradient": None,
        "text": "#1A1A1A",
        "muted": "#555550",
        "accent": "#8B1A1A",
        "accent2": "#C8C4BA",
        "font_main": "'Georgia', 'Songti SC', 'Noto Serif CJK SC', serif",
        "font_tag": "'Georgia', 'Songti SC', serif",
        "quote_color": "#8B1A1A",
        "deco": "newspaper",
        "letter_spacing": 3,
        "google_fonts": [],
    },
    # 06 Bloomberg 终端
    "bloomberg": {
        "name": "Bloomberg 终端",
        "bg": "#0A0A0A",
        "bg_gradient": None,
        "text": "#E8E8E8",
        "muted": "#777777",
        "accent": "#FF6B00",
        "accent2": "#00CC44",
        "font_main": "'Courier New', 'Courier', 'Lucida Console', monospace",
        "font_tag": "'PingFang SC', 'Microsoft YaHei', sans-serif",
        "quote_color": "#FF6B00",
        "deco": "bloomberg",
        "letter_spacing": 2,
        "google_fonts": [],
    },
    # 07 水墨卷轴
    "ink": {
        "name": "水墨卷轴",
        "bg": "#F5F0E8",
        "bg_gradient": None,
        "text": "#2A2018",
        "muted": "#7A6A50",
        "accent": "#8B1A1A",
        "accent2": "#1A1008",
        "font_main": "'Songti SC', 'Noto Serif CJK SC', 'Source Han Serif CN', 'STSong', Georgia, serif",
        "font_tag": "'Songti SC', 'STSong', serif",
        "quote_color": "#8B1A1A",
        "deco": "ink",
        "letter_spacing": 5,
        "google_fonts": [],
    },
    # 08 蒸汽朋克
    "steampunk": {
        "name": "蒸汽朋克",
        "bg": "#1A1008",
        "bg_gradient": "linear-gradient(135deg, #1E1408 0%, #150F06 50%, #1E1408 100%)",
        "text": "#E8D4A0",
        "muted": "#A08040",
        "accent": "#C8A830",
        "accent2": "#B87333",
        "font_main": "'Rye', 'Noto Serif SC', 'Songti SC', 'STSong', Georgia, serif",
        "font_tag": "'Rye', 'Noto Serif SC', 'Songti SC', serif",
        "quote_color": "#C8A830",
        "deco": "steampunk",
        "letter_spacing": 3,
        "google_fonts": ["Rye", "Noto Serif SC"],
    },
    # 09-A 小红书 · 简洁正式
    "xhs": {
        "name": "小红书·简洁",
        "bg": "#FFFFFF",
        "bg_gradient": None,
        "text": "#1A1A1A",
        "muted": "#999999",
        "accent": "#FF2442",
        "accent2": "#FF6B8A",
        "font_main": "-apple-system, 'BlinkMacSystemFont', 'PingFang SC', 'Helvetica Neue', 'Microsoft YaHei', sans-serif",
        "font_tag": "-apple-system, 'PingFang SC', sans-serif",
        "quote_color": "#FF2442",
        "deco": "xhs",
        "letter_spacing": 3,
        "google_fonts": [],
    },
    # 09-B 小红书 · 丰富活泼
    "xhs_rich": {
        "name": "小红书·丰富",
        "bg": "#FFF5F7",
        "bg_gradient": "linear-gradient(160deg, #FFF7F9 0%, #FFEFF3 55%, #FFE6EB 100%)",
        "text": "#1A1A1A",
        "muted": "#8E8E93",
        "accent": "#FF2442",
        "accent2": "#FF8FA8",
        "font_main": "-apple-system, 'BlinkMacSystemFont', 'PingFang SC', 'Helvetica Neue', 'Microsoft YaHei', sans-serif",
        "font_tag": "-apple-system, 'PingFang SC', sans-serif",
        "quote_color": "#FF2442",
        "deco": "xhs_rich",
        "letter_spacing": 3,
        "google_fonts": [],
    },
    # 10 莫兰迪灰
    "morandi": {
        "name": "莫兰迪灰",
        "bg": "#E8E4DD",
        "bg_gradient": None,
        "text": "#4A453E",
        "muted": "#94897C",
        "accent": "#7C8B7E",
        "accent2": "#9A8C82",
        "font_main": "'Inter', 'PingFang SC', 'Helvetica Neue', sans-serif",
        "font_tag": "'Inter', 'PingFang SC', sans-serif",
        "quote_color": "#7C8B7E",
        "deco": "none",
        "letter_spacing": 3,
        "google_fonts": ["Inter:wght@300;400;500;600"],
    },
    # 11 玻璃拟态
    "glass": {
        "name": "玻璃拟态",
        "bg": "#EDEBFF",
        "bg_gradient": "linear-gradient(135deg, #E6E9FF 0%, #F3E9FF 35%, #E9F7FF 70%, #FFF0F7 100%)",
        "text": "#1F2433",
        "muted": "#5B6072",
        "accent": "#6D5EF7",
        "accent2": "#4EC8E8",
        "font_main": "'Inter', 'PingFang SC', 'Helvetica Neue', sans-serif",
        "font_tag": "'Inter', 'PingFang SC', sans-serif",
        "quote_color": "#6D5EF7",
        "deco": "glass",
        "letter_spacing": 3,
        "google_fonts": ["Inter:wght@300;400;500;600"],
    },
    # 12 故宫
    "palace": {
        "name": "故宫金红",
        "bg": "#0E0604",
        "bg_gradient": "linear-gradient(180deg, #0E0604 0%, #160A06 50%, #0E0604 100%)",
        "text": "#F0E6C8",
        "muted": "#9A8060",
        "accent": "#C8A45A",
        "accent2": "#C0392B",
        "font_main": "'Ma Shan Zheng', 'ZCOOL XiaoWei', 'Noto Serif SC', 'Songti SC', 'STSong', Georgia, serif",
        "font_tag": "'ZCOOL XiaoWei', 'Songti SC', serif",
        "quote_color": "#C8A45A",
        "deco": "palace",
        "letter_spacing": 6,
        "google_fonts": ["Ma Shan Zheng", "ZCOOL XiaoWei"],
    },
    # 13 清新绿
    "fresh": {
        "name": "清新绿",
        "bg": "#F1F7F0",
        "bg_gradient": None,
        "text": "#1F3A29",
        "muted": "#6B8475",
        "accent": "#2E9E5B",
        "accent2": "#6FB98F",
        "font_main": "'Inter', 'PingFang SC', 'Helvetica Neue', sans-serif",
        "font_tag": "'Inter', 'PingFang SC', sans-serif",
        "quote_color": "#2E9E5B",
        "deco": "fresh",
        "letter_spacing": 3,
        "google_fonts": ["Inter:wght@300;400;500;600"],
    },
    # 14 大地原木
    "earthy": {
        "name": "大地原木",
        "bg": "#F3ECE1",
        "bg_gradient": None,
        "text": "#3D2E22",
        "muted": "#8A7460",
        "accent": "#B5683C",
        "accent2": "#8A8B5C",
        "font_main": "'Inter', 'PingFang SC', 'Helvetica Neue', sans-serif",
        "font_tag": "'Inter', 'PingFang SC', sans-serif",
        "quote_color": "#B5683C",
        "deco": "none",
        "letter_spacing": 3,
        "google_fonts": ["Inter:wght@300;400;500;600"],
    },
    # 15 紫梦幻
    "dreamy": {
        "name": "紫梦幻",
        "bg": "#F6F2FB",
        "bg_gradient": None,
        "text": "#2E2541",
        "muted": "#7C7295",
        "accent": "#8B5CF6",
        "accent2": "#C084FC",
        "font_main": "'Inter', 'PingFang SC', 'Helvetica Neue', sans-serif",
        "font_tag": "'Inter', 'PingFang SC', sans-serif",
        "quote_color": "#8B5CF6",
        "deco": "dreamy",
        "letter_spacing": 3,
        "google_fonts": ["Inter:wght@300;400;500;600"],
    },
    # 16 马卡龙
    "macaron": {
        "name": "马卡龙",
        "bg": "#FDF2F4",
        "bg_gradient": None,
        "text": "#4A2F38",
        "muted": "#9C7B85",
        "accent": "#EB6F8E",
        "accent2": "#F5A9C0",
        "font_main": "'Inter', 'PingFang SC', 'Helvetica Neue', sans-serif",
        "font_tag": "'Inter', 'PingFang SC', sans-serif",
        "quote_color": "#EB6F8E",
        "deco": "macaron",
        "letter_spacing": 3,
        "google_fonts": ["Inter:wght@300;400;500;600"],
    },
    # 17 暗色极简
    "carbon": {
        "name": "暗色极简",
        "bg": "#14161A",
        "bg_gradient": None,
        "text": "#D6DAE0",
        "muted": "#8A929E",
        "accent": "#4FB8C4",
        "accent2": "#6CCFA8",
        "font_main": "'Inter', 'SF Mono', 'PingFang SC', 'Helvetica Neue', sans-serif",
        "font_tag": "'Inter', 'SF Mono', 'PingFang SC', sans-serif",
        "quote_color": "#4FB8C4",
        "deco": "carbon",
        "letter_spacing": 3,
        "google_fonts": ["Inter:wght@300;400;500;600"],
    },
    # 18 活力渐变
    "vivid": {
        "name": "活力渐变",
        "bg": "#FBF9FF",
        "bg_gradient": None,
        "text": "#1E1B2E",
        "muted": "#6B6480",
        "accent": "#7C3AED",
        "accent2": "#EC4899",
        "font_main": "'Inter', 'PingFang SC', 'Helvetica Neue', sans-serif",
        "font_tag": "'Inter', 'PingFang SC', sans-serif",
        "quote_color": "#7C3AED",
        "deco": "vivid",
        "letter_spacing": 3,
        "google_fonts": ["Inter:wght@300;400;500;600"],
    },
}

# ─── SVG 构建 ───────────────────────────────────────────────────────

def escape(text):
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def estimate_line_width(line, font_size, letter_spacing):
    """估算单行文字在 SVG 中的像素宽度（含 letter-spacing）"""
    # 中文字符占宽约 0.95em，英文/数字/标点约 0.55em
    char_w = font_size * 0.95
    half_w = font_size * 0.55
    width = 0
    for ch in line:
        if ord(ch) > 127:
            width += char_w
        else:
            width += half_w
    # letter-spacing 加在每字之后，最后一个字符不加
    if len(line) > 1:
        width += (len(line) - 1) * letter_spacing
    # 预留 8% 安全边距（不同字体渲染差异）
    return width * 1.08


def compute_font_size(lines, width, height, theme):
    """根据行数、字数和卡片尺寸计算合适字号"""
    n = len(lines) if lines else 1
    max_chars = max(len(line) for line in lines) if lines else 4

    # 最大字号上限（行数越多，上限越低）
    max_sizes = {1: 130, 2: 120, 3: 95, 4: 78, 5: 64}
    max_size = max_sizes.get(n, 56)
    min_size = 38

    # 可用宽度：左右各留 11% 边距
    usable_width = width * 0.78
    # 可用高度：顶部标签到底部 footer 之间
    usable_height = height * 0.62

    letter_spacing = theme.get("letter_spacing", 4)

    # 先按字数给一个经验上限
    if max_chars >= 14:
        max_size = min(max_size, int(usable_width / (max_chars * 1.0)))
    elif max_chars >= 10:
        max_size = min(max_size, int(usable_width / (max_chars * 1.05)))
    elif max_chars >= 7:
        max_size = min(max_size, int(usable_width / (max_chars * 1.1)))

    # 再按高度限制
    line_height_at = lambda s: s * 1.6
    max_by_height = int(usable_height / (n * 1.6))
    max_size = min(max_size, max_by_height)

    # 从候选字号向下找，确保每行都不溢出
    for size in range(max_size, min_size - 1, -1):
        all_fit = all(
            estimate_line_width(line, size, letter_spacing) <= usable_width
            for line in lines
        )
        if all_fit:
            return max(size, min_size)
    return min_size


def build_svg(theme, width, height, content, options):
    """生成统一布局的 SVG"""
    t = THEMES[theme]
    tag = content.get("tag", "人生随笔")
    lines = content.get("lines", ["未命名卡片"])
    subtitle = content.get("subtitle", "")
    page_number = content.get("page_number", 1)
    total_pages = content.get("total_pages", 1)
    account = content.get("account", "")

    show_tag = options.get("show_tag", True)
    show_subtitle = options.get("show_subtitle", True)
    show_page = options.get("show_page_number", True)
    show_account = options.get("show_account", True)

    # 动态计算字号：按文字量自动缩放，确保不溢出
    font_size = compute_font_size(lines, width, height, t)
    letter_spacing = t.get("letter_spacing", 4)

    line_height = font_size * 1.6
    text_block_h = len(lines) * line_height
    start_y = (height - text_block_h) / 2 - 20

    # 背景（渐变由 build_html 的 CSS 处理，SVG 侧用纯色）
    bg_style = f"fill: {t['bg']}"
    bg_rect = f'<rect width="{width}" height="{height}" style="{bg_style}"/>'

    # 装饰元素
    decorations = build_decorations(theme, width, height, t)

    # 顶部标签
    tag_y = 130
    tag_parts = []
    if show_tag and tag:
        quote_left = f'<text x="{width/2 - 70}" y="{tag_y}" text-anchor="end" font-size="28" fill="{t['quote_color']}" font-family="{t['font_tag']}">"</text>'
        tag_text = f'<text x="{width/2}" y="{tag_y}" text-anchor="middle" font-size="24" fill="{t['muted']}" font-family="{t['font_tag']}" letter-spacing="6">{escape(tag)}</text>'
        quote_right = f'<text x="{width/2 + 70}" y="{tag_y}" text-anchor="start" font-size="28" fill="{t['quote_color']}" font-family="{t['font_tag']}">"</text>'
        tag_parts = [quote_left, tag_text, quote_right]

    # 主文案
    text_parts = []
    for i, line in enumerate(lines):
        y = start_y + i * line_height + font_size * 0.85
        # 如果只有一行，可以稍微粗一点
        weight = "500" if len(lines) <= 2 else "400"
        text_parts.append(
            f'<text x="{width/2}" y="{y}" text-anchor="middle" font-size="{font_size}" '
            f'fill="{t['text']}" font-family="{t['font_main']}" font-weight="{weight}" '
            f'letter-spacing="{letter_spacing}">{escape(line)}</text>'
        )

    # 副标题
    subtitle_y = start_y + text_block_h + 70
    subtitle_parts = []
    if show_subtitle and subtitle:
        subtitle_parts.append(
            f'<text x="{width/2}" y="{subtitle_y}" text-anchor="middle" font-size="26" '
            f'fill="{t['muted']}" font-family="{t['font_tag']}" letter-spacing="3">— {escape(subtitle)} —</text>'
        )

    # 底部分隔线
    footer_y = height - 130
    footer_parts = [
        f'<line x1="{width * 0.1}" y1="{footer_y - 30}" x2="{width * 0.9}" y2="{footer_y - 30}" '
        f'stroke="{t['accent2']}" stroke-width="1"/>'
    ]

    # 页码
    if show_page:
        page_text = f"No.{page_number:02d} / {total_pages:02d}"
        footer_parts.append(
            f'<text x="{width * 0.1}" y="{footer_y + 18}" text-anchor="start" font-size="22" '
            f'fill="{t['muted']}" font-family="{t['font_tag']}" letter-spacing="1">{page_text}</text>'
        )

    # 账号
    if show_account and account:
        footer_parts.append(
            f'<text x="{width * 0.9}" y="{footer_y + 18}" text-anchor="end" font-size="22" '
            f'fill="{t['muted']}" font-family="{t['font_tag']}" letter-spacing="1">{escape(account)}</text>'
        )

    # 组合
    svg_parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        bg_rect,
    ]
    svg_parts.extend(decorations)
    svg_parts.extend(tag_parts)
    svg_parts.extend(text_parts)
    svg_parts.extend(subtitle_parts)
    svg_parts.extend(footer_parts)
    svg_parts.append('</svg>')

    return "\n".join(svg_parts)


def build_decorations(theme, width, height, t):
    """根据主题添加装饰元素"""
    decos = []
    deco = t.get("deco", "none")

    if deco == "stars" or theme == "y2k":
        # Y2K 星星和十字装饰
        decos.append(f'<polygon points="{width-120},80 {width-115},95 {width-100},100 {width-115},105 {width-120},120 {width-125},105 {width-140},100 {width-125},95" fill="{t['accent2']}" opacity="0.8"/>')
        decos.append(f'<polygon points="120,180 125,195 140,200 125,205 120,220 115,205 100,200 115,195" fill="{t['accent']}" opacity="0.7"/>')
        decos.append(f'<text x="{width-90}" y="{height-160}" font-size="48" fill="{t['accent']}" opacity="0.5">✦</text>')
        decos.append(f'<text x="90" y="{height-140}" font-size="36" fill="{t['accent2']}" opacity="0.5">✦</text>')
    elif deco == "doodles" or theme == "doodle":
        decos.append(f'<path d="M {width-140},70 Q {width-120},90 {width-140},110 Q {width-160},90 {width-140},70" fill="none" stroke="{t['accent']}" stroke-width="3" stroke-linecap="round"/>')
        decos.append(f'<path d="M 110,120 L 130,140 M 130,120 L 110,140" stroke="{t['accent2']}" stroke-width="4" stroke-linecap="round"/>')
        decos.append(f'<circle cx="{width-100}" cy="{height-140}" r="8" fill="none" stroke="{t['accent']}" stroke-width="3"/>')
        decos.append(f'<path d="M 90,{height-130} Q 110,{height-150} 130,{height-130}" fill="none" stroke="{t['accent2']}" stroke-width="3" stroke-linecap="round"/>')
    elif deco == "dots" or theme == "pop":
        for cx, cy, r, color in [
            (width - 100, 100, 18, t["accent"]),
            (width - 70, 140, 10, t["accent2"]),
            (100, height - 120, 14, t["accent"]),
            (140, height - 90, 8, t["accent2"]),
            (width - 130, height - 100, 12, t["accent"]),
        ]:
            decos.append(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{color}" opacity="0.85"/>')
    elif deco == "warm" or theme == "warm":
        decos.append(f'<circle cx="{width-90}" cy="90" r="3" fill="{t['accent']}" opacity="0.5"/>')
        decos.append(f'<circle cx="{width-110}" cy="110" r="2" fill="{t['accent']}" opacity="0.4"/>')
        decos.append(f'<circle cx="90" cy="{height-100}" r="3" fill="{t['accent']}" opacity="0.5"/>')
    elif deco == "palace" or theme == "palace":
        seal_x, seal_y, seal_r = width - 100, 100, 28
        decos.append(f'<rect x="{seal_x - seal_r}" y="{seal_y - seal_r}" width="{seal_r * 2}" height="{seal_r * 2}" fill="{t['accent2']}" opacity="0.85" rx="3"/>')
        decos.append(f'<text x="{seal_x}" y="{seal_y + 8}" text-anchor="middle" font-size="22" fill="{t['accent']}" font-family="{t['font_main']}">印</text>')
        decos.append(f'<path d="M 40,40 L 80,40 M 40,40 L 40,80" stroke="{t['accent']}" stroke-width="2" opacity="0.6"/>')
        decos.append(f'<path d="M {width-40},40 L {width-80},40 M {width-40},40 L {width-40},80" stroke="{t['accent']}" stroke-width="2" opacity="0.6"/>')
        decos.append(f'<path d="M 40,{height-40} L 80,{height-40} M 40,{height-40} L 40,{height-80}" stroke="{t['accent']}" stroke-width="2" opacity="0.6"/>')
        decos.append(f'<path d="M {width-40},{height-40} L {width-80},{height-40} M {width-40},{height-40} L {width-40},{height-80}" stroke="{t['accent']}" stroke-width="2" opacity="0.6"/>')
    elif deco == "cyberpunk" or theme == "cyberpunk":
        # 网格线 + 发光点
        for i in range(0, width, 60):
            decos.append(f'<line x1="{i}" y1="0" x2="{i}" y2="{height}" stroke="{t["accent"]}" stroke-width="0.5" opacity="0.06"/>')
        for j in range(0, height, 60):
            decos.append(f'<line x1="0" y1="{j}" x2="{width}" y2="{j}" stroke="{t["accent"]}" stroke-width="0.5" opacity="0.06"/>')
        decos.append(f'<circle cx="{width-80}" cy="80" r="4" fill="{t["accent"]}" opacity="0.8"/>')
        decos.append(f'<circle cx="{width-100}" cy="100" r="2" fill="{t["accent2"]}" opacity="0.6"/>')
        decos.append(f'<circle cx="80" cy="{height-80}" r="3" fill="{t["accent"]}" opacity="0.7"/>')
    elif deco == "newspaper" or theme == "newspaper":
        # 双线边框
        decos.append(f'<rect x="30" y="30" width="{width-60}" height="{height-60}" fill="none" stroke="{t["accent2"]}" stroke-width="1"/>')
        decos.append(f'<rect x="36" y="36" width="{width-72}" height="{height-72}" fill="none" stroke="{t["accent2"]}" stroke-width="0.5"/>')
    elif deco == "bloomberg" or theme == "bloomberg":
        # 扫描线
        for j in range(0, height, 4):
            decos.append(f'<line x1="0" y1="{j}" x2="{width}" y2="{j}" stroke="{t["accent"]}" stroke-width="0.3" opacity="0.04"/>')
        decos.append(f'<rect x="0" y="0" width="4" height="{height}" fill="{t["accent"]}" opacity="0.6"/>')
    elif deco == "ink" or theme == "ink":
        # 水墨晕圈
        decos.append(f'<ellipse cx="{width-100}" cy="100" rx="60" ry="40" fill="{t["accent2"]}" opacity="0.04"/>')
        decos.append(f'<ellipse cx="100" cy="{height-100}" rx="50" ry="35" fill="{t["accent"]}" opacity="0.05"/>')
        # 印章
        decos.append(f'<rect x="{width-80}" y="{height-80}" width="40" height="40" fill="{t["accent"]}" opacity="0.8" rx="2"/>')
        decos.append(f'<text x="{width-60}" y="{height-55}" text-anchor="middle" font-size="18" fill="{t["bg"]}" font-family="{t["font_main"]}">墨</text>')
    elif deco == "steampunk" or theme == "steampunk":
        # 齿轮装饰
        cx, cy, r = width - 90, 90, 25
        gear = f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{t["accent"]}" stroke-width="2" opacity="0.5"/>'
        for a in range(0, 360, 45):
            rad = math.radians(a)
            x1 = cx + math.cos(rad) * r
            y1 = cy + math.sin(rad) * r
            x2 = cx + math.cos(rad) * (r + 8)
            y2 = cy + math.sin(rad) * (r + 8)
            gear += f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{t["accent"]}" stroke-width="3" opacity="0.5"/>'
        decos.append(gear)
        decos.append(f'<circle cx="{cx}" cy="{cy}" r="8" fill="{t["accent2"]}" opacity="0.4"/>')
        # 铜管装饰
        decos.append(f'<rect x="60" y="{height-60}" width="80" height="6" fill="{t["accent2"]}" opacity="0.3" rx="3"/>')
    elif deco == "xhs" or theme == "xhs":
        # 小红书·简洁：45°极淡斜纹（纸张质感）+ 少量小圆点，保持呼吸感
        stripes = []
        step = 26
        x = -height
        while x < width + height:
            stripes.append(
                f'<line x1="{x}" y1="0" x2="{x + height}" y2="{height}" '
                f'stroke="{t["accent"]}" stroke-width="1" opacity="0.035"/>'
            )
            x += step
        decos.append("".join(stripes))
        decos.append(f'<circle cx="{width-70}" cy="70" r="6" fill="{t["accent"]}" opacity="0.15"/>')
        decos.append(f'<circle cx="{width-90}" cy="90" r="4" fill="{t["accent2"]}" opacity="0.2"/>')
        decos.append(f'<circle cx="70" cy="{height-70}" r="5" fill="{t["accent"]}" opacity="0.15"/>')
    elif deco == "xhs_rich" or theme == "xhs_rich":
        # 小红书·丰富：手账圆点纹 + 毛玻璃光晕 + 三段渐变波浪线
        dots = []
        gap = 46
        y = gap
        while y < height:
            x = gap
            while x < width:
                dots.append(
                    f'<circle cx="{x}" cy="{y}" r="2.2" fill="{t["accent"]}" opacity="0.10"/>'
                )
                x += gap
            y += gap
        decos.append("".join(dots))
        # 毛玻璃光晕
        decos.append(f'<circle cx="{width-110}" cy="150" r="90" fill="{t["accent2"]}" opacity="0.13"/>')
        decos.append(f'<circle cx="90" cy="{height-180}" r="110" fill="{t["accent"]}" opacity="0.07"/>')
        # 顶部三段渐变波浪线（模式B 标志性装饰）
        wx = width // 2 - 26
        wy = 150
        decos.append(f'<rect x="{wx}" y="{wy}" width="28" height="5" rx="2.5" fill="{t["accent"]}" opacity="0.9"/>')
        decos.append(f'<rect x="{wx+32}" y="{wy}" width="14" height="5" rx="2.5" fill="{t["accent"]}" opacity="0.5"/>')
        decos.append(f'<rect x="{wx+50}" y="{wy}" width="7" height="5" rx="2.5" fill="{t["accent"]}" opacity="0.25"/>')
    elif deco == "glass" or theme == "glass":
        # 模糊光斑
        decos.append(f'<circle cx="{width-120}" cy="120" r="40" fill="{t["accent"]}" opacity="0.08"/>')
        decos.append(f'<circle cx="120" cy="{height-120}" r="50" fill="{t["accent2"]}" opacity="0.08"/>')
        decos.append(f'<circle cx="{width-80}" cy="{height-200}" r="30" fill="{t["accent"]}" opacity="0.06"/>')
    elif deco == "fresh" or theme == "fresh":
        # 叶子装饰
        decos.append(f'<ellipse cx="{width-80}" cy="80" rx="12" ry="6" fill="{t["accent"]}" opacity="0.2" transform="rotate(-30 {width-80} 80)"/>')
        decos.append(f'<ellipse cx="80" cy="{height-80}" rx="10" ry="5" fill="{t["accent2"]}" opacity="0.25" transform="rotate(30 80 {height-80})"/>')
    elif deco == "dreamy" or theme == "dreamy":
        # 闪烁星点
        decos.append(f'<circle cx="{width-90}" cy="90" r="3" fill="{t["accent"]}" opacity="0.4"/>')
        decos.append(f'<circle cx="{width-110}" cy="70" r="2" fill="{t["accent2"]}" opacity="0.5"/>')
        decos.append(f'<circle cx="90" cy="{height-90}" r="2" fill="{t["accent"]}" opacity="0.4"/>')
        decos.append(f'<circle cx="70" cy="{height-110}" r="3" fill="{t["accent2"]}" opacity="0.3"/>')
    elif deco == "macaron" or theme == "macaron":
        # 甜美小圆点
        for cx, cy, r in [
            (width - 80, 80, 10), (width - 100, 100, 6),
            (80, height - 80, 8), (100, height - 100, 5),
        ]:
            decos.append(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{t["accent2"]}" opacity="0.3"/>')
    elif deco == "carbon" or theme == "carbon":
        # 代码风格小方块
        decos.append(f'<rect x="{width-90}" y="70" width="6" height="6" fill="{t["accent"]}" opacity="0.4"/>')
        decos.append(f'<rect x="{width-78}" y="70" width="6" height="6" fill="{t["accent2"]}" opacity="0.3"/>')
        decos.append(f'<rect x="{width-66}" y="70" width="6" height="6" fill="{t["accent"]}" opacity="0.2"/>')
        decos.append(f'<rect x="70" y="{height-80}" width="6" height="6" fill="{t["accent2"]}" opacity="0.3"/>')
    elif deco == "vivid" or theme == "vivid":
        # 渐变光斑
        decos.append(f'<circle cx="{width-100}" cy="100" r="25" fill="{t["accent"]}" opacity="0.1"/>')
        decos.append(f'<circle cx="100" cy="{height-100}" r="20" fill="{t["accent2"]}" opacity="0.1"/>')
        decos.append(f'<circle cx="{width-60}" cy="{height-180}" r="15" fill="{t["accent2"]}" opacity="0.08"/>')
    # none / morandi / apple / cowork / earthy / elegant 无装饰
    return decos


def build_html(theme, width, height, content, options):
    """把 SVG 包装成 HTML 供 Chrome 渲染"""
    t = THEMES[theme]
    svg = build_svg(theme, width, height, content, options)

    # 如果主题有渐变背景，用 CSS 实现更稳
    bg_css = f"background: {t['bg']};"
    if t["bg_gradient"]:
        bg_css = f"background: {t['bg_gradient']};"

    # Google Fonts CDN 加载：多镜像 fallback，确保国内可用
    # 策略：同时加载 Google 原始 CDN + 国内镜像，谁先到用谁
    # 镜像列表按优先级排序：国内镜像优先（Chrome headless 在国内访问 Google 不稳定）
    google_fonts = t.get("google_fonts", [])
    fonts_links = []
    if google_fonts:
        families = "&".join(f"family={f.replace(' ', '+')}" for f in google_fonts)
        # 多镜像：<link> 标签并行加载，浏览器自动用最先返回的 CSS
        # 1. fonts.loli.net — 国内社区镜像，API 完全兼容
        # 2. fonts.googleapis.cn — Google 官方中国镜像
        # 3. fonts.googleapis.com — Google 原始（海外 fallback）
        mirrors = [
            ("fonts.loli.net", "https://fonts.loli.net"),
            ("fonts.googleapis.cn", "https://fonts.googleapis.cn"),
            ("fonts.googleapis.com", "https://fonts.googleapis.com"),
        ]
        for domain, base_url in mirrors:
            fonts_links.append(
                f'<link href="{base_url}/css2?{families}&display=swap" rel="stylesheet">'
            )

        # 额外保险：JS 检测字体是否加载成功，失败则动态注入镜像 CSS
        font_names_js = json.dumps([f.split(":")[0].strip() for f in google_fonts])
        fonts_js = f'''<script>
(function() {{
    var fontNames = {font_names_js};
    var mirrors = [
        'https://fonts.loli.net/css2?{families}&display=swap',
        'https://fonts.googleapis.cn/css2?{families}&display=swap'
    ];
    // 等 3 秒后检查字体是否加载成功
    setTimeout(function() {{
        fontNames.forEach(function(name) {{
            try {{
                var loaded = document.fonts.check('16px "' + name + '"');
                if (!loaded) {{
                    console.log('Font not loaded: ' + name + ', injecting mirror');
                    var link = document.createElement('link');
                    link.rel = 'stylesheet';
                    link.href = mirrors[0];
                    document.head.appendChild(link);
                }}
            }} catch(e) {{}}
        }});
    }}, 3000);
}})();
</script>'''

    fonts_link = "\n    ".join(fonts_links)

    html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>card</title>
    {fonts_link}
    {fonts_js if google_fonts else ""}
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            width: {width}px;
            height: {height}px;
            {bg_css}
            display: flex;
            align-items: center;
            justify-content: center;
            overflow: hidden;
        }}
        svg {{
            width: {width}px;
            height: {height}px;
            display: block;
        }}
    </style>
</head>
<body>
{svg}
</body>
</html>'''
    return html


# ─── PNG 渲染 ──────────────────────────────────────────────────────

def find_chrome():
    for p in CHROME_CANDIDATES:
        if os.path.exists(p):
            return p
    return None


def render_png(html_content, output_path, width=1080, height=1440):
    """用 Chrome headless 将 HTML 渲染为 PNG"""
    tmp_html = tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8")
    tmp_html.write(html_content)
    tmp_html.close()

    try:
        chrome = find_chrome()
        if not chrome:
            print("[ERROR] 未找到 Chrome/Chromium", file=sys.stderr)
            return False

        # 直接用 Chrome screenshot
        cmd = [
            chrome,
            "--headless",
            "--disable-gpu",
            "--no-sandbox",
            "--hide-scrollbars",
            "--force-device-scale-factor=1",
            "--virtual-time-budget=10000",
            f"--window-size={width},{height}",
            "--screenshot=" + os.path.abspath(output_path),
            "file://" + tmp_html.name,
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            print(f"[ERROR] 渲染失败: {result.stderr}", file=sys.stderr)
            return False

        return True
    finally:
        os.unlink(tmp_html.name)


# ─── Demo 内容 ─────────────────────────────────────────────────────

DEMO_CONTENT = {
    "tag": "人生随笔",
    "lines": [
        "我们花了太多时间",
        "去理解世界",
        "却太少时间去理解自己"
    ],
    "subtitle": "关于自省",
    "page_number": 5,
    "total_pages": 6,
    "account": "@雨夜心灯",
}

# ─── CLI ───────────────────────────────────────────────────────────

def parse_lines(value):
    if value is None:
        return []
    return [line.strip() for line in value.replace("\\n", "\n").split("\n") if line.strip()]


def main():
    parser = argparse.ArgumentParser(description="小红书风格统一卡片生成器")
    parser.add_argument("--theme", default="warm", help=f"主题 ({'/'.join(THEMES.keys())})")
    parser.add_argument("--all-themes", action="store_true", help="生成全部主题示例")
    parser.add_argument("--list-themes", action="store_true", help="打印全部主题清单后退出")
    parser.add_argument("--demo", action="store_true", help="使用示例内容")
    parser.add_argument("--content", help="JSON 文件路径")
    parser.add_argument("--tag", help="顶部标签")
    parser.add_argument("--lines", help="主文案，用 \\n 分隔")
    parser.add_argument("--subtitle", help="副标题")
    parser.add_argument("--page-number", type=int, help="当前页码")
    parser.add_argument("--total-pages", type=int, help="总页数")
    parser.add_argument("--account", help="账号名")
    parser.add_argument("--hide-tag", action="store_true", help="隐藏顶部标签")
    parser.add_argument("--hide-subtitle", action="store_true", help="隐藏副标题")
    parser.add_argument("--hide-page-number", action="store_true", help="隐藏页码")
    parser.add_argument("--hide-account", action="store_true", help="隐藏账号")
    parser.add_argument("--width", type=int, default=1080, help="输出宽度")
    parser.add_argument("--height", type=int, default=1440, help="输出高度")
    parser.add_argument("--output", "-o", help="输出 PNG 路径")
    parser.add_argument("--output-dir", default="output", help="all-themes 输出目录")
    args = parser.parse_args()

    if args.list_themes:
        print(f"共 {len(THEMES)} 种主题：")
        for key, cfg in THEMES.items():
            print(f"  {key:<12} {cfg['name']}")
        return

    # 内容
    if args.content:
        with open(args.content, "r", encoding="utf-8") as f:
            content = json.load(f)
    elif args.demo:
        content = DEMO_CONTENT.copy()
    else:
        content = {}
        if args.tag: content["tag"] = args.tag
        if args.lines: content["lines"] = parse_lines(args.lines)
        if args.subtitle: content["subtitle"] = args.subtitle
        if args.page_number is not None: content["page_number"] = args.page_number
        if args.total_pages is not None: content["total_pages"] = args.total_pages
        if args.account: content["account"] = args.account

    # 默认值
    content.setdefault("tag", "人生随笔")
    content.setdefault("lines", ["未命名卡片"])
    content.setdefault("subtitle", "")
    content.setdefault("page_number", 1)
    content.setdefault("total_pages", 1)
    content.setdefault("account", "")

    # 显示选项（默认全显示，--hide-* 隐藏）
    options = {
        "show_tag": not args.hide_tag,
        "show_subtitle": not args.hide_subtitle,
        "show_page_number": not args.hide_page_number,
        "show_account": not args.hide_account,
    }

    if args.all_themes:
        out_dir = Path(args.output_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        results = []
        for theme in THEMES:
            out_path = str(out_dir / f"{theme}.png")
            print(f"生成 {theme} ...")
            html = build_html(theme, args.width, args.height, content, options)
            if render_png(html, out_path, args.width, args.height):
                results.append((theme, out_path))
        print(f"\n完成！共生成 {len(results)} 张")
        for theme, path in results:
            print(f"  {theme:10s} → {path}")
    else:
        if args.theme not in THEMES:
            print(f"未知主题: {args.theme}")
            print(f"可用: {', '.join(THEMES.keys())}")
            sys.exit(1)

        out_path = args.output or f"output/{args.theme}.png"
        Path(out_path).parent.mkdir(parents=True, exist_ok=True)

        html = build_html(args.theme, args.width, args.height, content, options)
        if render_png(html, out_path, args.width, args.height):
            print(f"输出: {out_path}")


if __name__ == "__main__":
    main()
