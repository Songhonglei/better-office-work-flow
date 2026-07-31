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
import subprocess
import tempfile
import argparse
from pathlib import Path

BASE_DIR = Path(__file__).parent
NODE_BIN = "/Users/songhonglei/.workbuddy/binaries/node/versions/22.22.2/bin/node"
NODE_PATH = "/Users/songhonglei/.workbuddy/binaries/node/workspace/node_modules"
CHROME_CANDIDATES = [
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
    "/usr/bin/google-chrome",
    "/usr/bin/chromium",
]

# ─── 主题配置 ──────────────────────────────────────────────────────
# 每个主题：背景、文字、点缀、装饰元素、字体
THEMES = {
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
        "deco": "none",
        "letter_spacing": 4,
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
        "font_main": "'Caveat', 'Permanent Marker', 'Chalkduster', 'Bradley Hand', 'Marker Felt', 'Kaiti SC', cursive",
        "font_tag": "'Caveat', 'Chalkduster', 'Bradley Hand', 'Marker Felt', 'PingFang SC', cursive",
        "quote_color": "#FF6B35",
        "deco": "doodles",
        "letter_spacing": 2,
        "google_fonts": ["Caveat:wght@400;700", "Permanent Marker"],
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
    "palace": {
        "name": "故宫金红",
        "bg": "#1A0A05",
        "bg_gradient": "linear-gradient(180deg, #1A0A05 0%, #2D1108 50%, #1A0A05 100%)",
        "text": "#D4A843",
        "muted": "#8B6914",
        "accent": "#C9A961",
        "accent2": "#8B0000",
        "font_main": "'Ma Shan Zheng', 'ZCOOL XiaoWei', 'Songti SC', serif",
        "font_tag": "'ZCOOL XiaoWei', 'Songti SC', serif",
        "quote_color": "#C9A961",
        "deco": "palace",
        "letter_spacing": 6,
        "google_fonts": ["Ma Shan Zheng", "ZCOOL XiaoWei"],
    },
    "morandi": {
        "name": "莫兰迪灰",
        "bg": "#E8E4E0",
        "bg_gradient": None,
        "text": "#5D5754",
        "muted": "#9E9690",
        "accent": "#A89B94",
        "accent2": "#C4BBB5",
        "font_main": "'Inter', 'PingFang SC', 'Helvetica Neue', sans-serif",
        "font_tag": "'Inter', 'PingFang SC', sans-serif",
        "quote_color": "#A89B94",
        "deco": "none",
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

    # 背景
    bg_style = f"fill: {t['bg']}"
    bg_rect = f'<rect width="{width}" height="{height}" style="{bg_style}"/>'
    gradient_defs = ""
    if t["bg_gradient"]:
        gradient_id = "bgGrad"
        # 简化为直接用 CSS gradient on rect
        bg_rect = f'<rect width="{width}" height="{height}" style="fill: {t['bg']}"/>'

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
        f'<defs>{gradient_defs}</defs>',
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
    if theme == "y2k":
        # 星星和十字装饰
        decos.append(f'<polygon points="{width-120},80 {width-115},95 {width-100},100 {width-115},105 {width-120},120 {width-125},105 {width-140},100 {width-125},95" fill="{t['accent2']}" opacity="0.8"/>')
        decos.append(f'<polygon points="120,180 125,195 140,200 125,205 120,220 115,205 100,200 115,195" fill="{t['accent']}" opacity="0.7"/>')
        decos.append(f'<text x="{width-90}" y="{height-160}" font-size="48" fill="{t['accent']}" opacity="0.5">✦</text>')
        decos.append(f'<text x="90" y="{height-140}" font-size="36" fill="{t['accent2']}" opacity="0.5">✦</text>')
    elif theme == "doodle":
        # 手绘风星星和线条
        decos.append(f'<path d="M {width-140},70 Q {width-120},90 {width-140},110 Q {width-160},90 {width-140},70" fill="none" stroke="{t['accent']}" stroke-width="3" stroke-linecap="round"/>')
        decos.append(f'<path d="M 110,120 L 130,140 M 130,120 L 110,140" stroke="{t['accent2']}" stroke-width="4" stroke-linecap="round"/>')
        decos.append(f'<circle cx="{width-100}" cy="{height-140}" r="8" fill="none" stroke="{t['accent']}" stroke-width="3"/>')
        decos.append(f'<path d="M 90,{height-130} Q 110,{height-150} 130,{height-130}" fill="none" stroke="{t['accent2']}" stroke-width="3" stroke-linecap="round"/>')
    elif theme == "pop":
        # 波普圆点
        for cx, cy, r, color in [
            (width - 100, 100, 18, t["accent"]),
            (width - 70, 140, 10, t["accent2"]),
            (100, height - 120, 14, t["accent"]),
            (140, height - 90, 8, t["accent2"]),
            (width - 130, height - 100, 12, t["accent"]),
        ]:
            decos.append(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{color}" opacity="0.85"/>')
    elif theme == "warm":
        # 淡淡的角落装饰
        decos.append(f'<circle cx="{width-90}" cy="90" r="3" fill="{t['accent']}" opacity="0.5"/>')
        decos.append(f'<circle cx="{width-110}" cy="110" r="2" fill="{t['accent']}" opacity="0.4"/>')
        decos.append(f'<circle cx="90" cy="{height-100}" r="3" fill="{t['accent']}" opacity="0.5"/>')
    elif theme == "palace":
        # 金色印章 + 角花装饰
        seal_x, seal_y, seal_r = width - 100, 100, 28
        decos.append(f'<rect x="{seal_x - seal_r}" y="{seal_y - seal_r}" width="{seal_r * 2}" height="{seal_r * 2}" fill="{t['accent2']}" opacity="0.85" rx="3"/>')
        decos.append(f'<text x="{seal_x}" y="{seal_y + 8}" text-anchor="middle" font-size="22" fill="{t['accent']}" font-family="{t['font_main']}">印</text>')
        # 顶部角花
        decos.append(f'<path d="M 40,40 L 80,40 M 40,40 L 40,80" stroke="{t['accent']}" stroke-width="2" opacity="0.6"/>')
        decos.append(f'<path d="M {width-40},40 L {width-80},40 M {width-40},40 L {width-40},80" stroke="{t['accent']}" stroke-width="2" opacity="0.6"/>')
        # 底部角花
        decos.append(f'<path d="M 40,{height-40} L 80,{height-40} M 40,{height-40} L 40,{height-80}" stroke="{t['accent']}" stroke-width="2" opacity="0.6"/>')
        decos.append(f'<path d="M {width-40},{height-40} L {width-80},{height-40} M {width-40},{height-40} L {width-40},{height-80}" stroke="{t['accent']}" stroke-width="2" opacity="0.6"/>')
    # minimal / morandi 无装饰
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
    os.unlink(tmp_html.name)

    if result.returncode != 0:
        print(f"[ERROR] 渲染失败: {result.stderr}", file=sys.stderr)
        return False

    return True


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
    parser.add_argument("--demo", action="store_true", help="使用示例内容")
    parser.add_argument("--content", help="JSON 文件路径")
    parser.add_argument("--tag", help="顶部标签")
    parser.add_argument("--lines", help="主文案，用 \\n 分隔")
    parser.add_argument("--subtitle", help="副标题")
    parser.add_argument("--page-number", type=int, help="当前页码")
    parser.add_argument("--total-pages", type=int, help="总页数")
    parser.add_argument("--account", help="账号名")
    parser.add_argument("--show-tag", action="store_true", default=True, help="显示顶部标签")
    parser.add_argument("--hide-tag", action="store_true", help="隐藏顶部标签")
    parser.add_argument("--show-subtitle", action="store_true", default=True, help="显示副标题")
    parser.add_argument("--hide-subtitle", action="store_true", help="隐藏副标题")
    parser.add_argument("--show-page-number", action="store_true", default=True, help="显示页码")
    parser.add_argument("--hide-page-number", action="store_true", help="隐藏页码")
    parser.add_argument("--show-account", action="store_true", default=True, help="显示账号")
    parser.add_argument("--hide-account", action="store_true", help="隐藏账号")
    parser.add_argument("--width", type=int, default=1080, help="输出宽度")
    parser.add_argument("--height", type=int, default=1440, help="输出高度")
    parser.add_argument("--output", "-o", help="输出 PNG 路径")
    parser.add_argument("--output-dir", default="output", help="all-themes 输出目录")
    args = parser.parse_args()

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

    # 显示选项
    options = {
        "show_tag": not args.hide_tag if args.hide_tag else args.show_tag,
        "show_subtitle": not args.hide_subtitle if args.hide_subtitle else args.show_subtitle,
        "show_page_number": not args.hide_page_number if args.hide_page_number else args.show_page_number,
        "show_account": not args.hide_account if args.hide_account else args.show_account,
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
