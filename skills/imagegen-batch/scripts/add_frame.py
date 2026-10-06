#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""给插图加「相框感」：白边 + 细线框（装裱效果）。

模型基本不遵守 prompt 里的「四周留白」，相框感必须后期加。结构：

    图像 → 白隙 gap → 细线框 line → 外侧白边 pad

用法：
    python3 add_frame.py in.png out.png                          # 默认加框（白边 + 细线）
    python3 add_frame.py in.png out.png --line 0                 # 只留白边，不画线（更柔和）
    python3 add_frame.py in.png out.png --crop-bottom 80         # 先裁底部 80px（去水印）
    python3 add_frame.py in.png out.png --ratio 2.35             # 裁到含边恰为 2.35:1（头条封面）
    python3 add_frame.py in.png out.png --ratio 1 --line 0       # 方形次条封面，无边白框
    python3 add_frame.py in.png out.png --no-frame               # 只裁切，不加边

依赖：Pillow（`python3 -m pip install Pillow`）。

参数说明：
    --pad    外侧白边宽度，取短边的比例，默认 0.06（5%~6% 观感最好）
    --gap    图像与线框之间的白隙，默认 11px；--line 0 时它就是图像到外沿的留白
    --line   线框粗细，默认 3px；**传 0 则只留白边不画线**（2026-09-26 用户偏好）
    --ink    线框颜色，默认 #1e1e1e（纯黑太硬）
"""
import argparse
from PIL import Image, ImageDraw

PAPER = (255, 255, 255)
INK = (30, 30, 30)


def frame_geoms(w, h, pad_ratio, line, gap):
    """返回 (pad, F)：pad 是外侧白边，F 是图像距外框的总边距。"""
    pad = int(min(w, h) * pad_ratio)
    return pad, pad + line + gap


def add_frame(im, pad_ratio=0.06, gap=11, line=3, ink=INK, paper=PAPER):
    w, h = im.size
    pad, F = frame_geoms(w, h, pad_ratio, line, gap)
    canvas = Image.new("RGB", (w + 2 * F, h + 2 * F), paper)
    canvas.paste(im, (F, F))
    if line > 0:
        dr = ImageDraw.Draw(canvas)
        for i in range(line):
            dr.rectangle(
                [pad - i, pad - i, w + 2 * F - 1 - pad + i, h + 2 * F - 1 - pad + i],
                outline=ink,
            )
    return canvas


def inner_h_for_ratio(w, target, pad_ratio=0.06, gap=11, line=3):
    """二分求内部高度，使「加框后」的整体宽高比恰为 target。

    注意：pad 依赖短边，短边随内部高度变化 → 不能手算，必须迭代。
    """
    lo, hi = 50, w * 4
    for _ in range(64):
        mid = (lo + hi) // 2
        _, F = frame_geoms(w, mid, pad_ratio, line, gap)
        r = (w + 2 * F) / (mid + 2 * F)
        if r > target:      # 太高，需要更大的高度
            lo = mid
        else:
            hi = mid
    return hi


def fit_ratio(im, target, pad_ratio=0.06, gap=11, line=3, top_bias=0.72):
    """裁切图像，使「加框后」整体比例恰为 target。宽高比够就裁高度，否则裁宽度。"""
    w, h = im.size
    th = inner_h_for_ratio(w, target, pad_ratio, gap, line)
    if th <= h:                                   # 目标更扁 → 裁高度
        cut = h - th
        top = int(cut * top_bias)
        return im.crop((0, top, w, top + th))
    # 目标更方/更高 → 高度不够，改裁宽度（F 以高度为短边估）
    _, F = frame_geoms(h, h, pad_ratio, line, gap)
    tw = max(1, min(w, int(target * (h + 2 * F) - 2 * F)))
    left = (w - tw) // 2
    return im.crop((left, 0, left + tw, h))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("dst")
    ap.add_argument("--crop-bottom", type=int, default=0, help="先裁掉底部像素（去水印）")
    ap.add_argument("--ratio", type=float, default=None, help="含框后的目标宽高比，如 2.35 / 1")
    ap.add_argument("--top-bias", type=float, default=0.72, help="按比例裁切时，从上方多裁的比重")
    ap.add_argument("--pad", type=float, default=0.06)
    ap.add_argument("--gap", type=int, default=11)
    ap.add_argument("--line", type=int, default=3)
    ap.add_argument("--no-frame", action="store_true")
    a = ap.parse_args()

    im = Image.open(a.src).convert("RGB")
    ow, oh = im.size

    if a.crop_bottom:
        im = im.crop((0, 0, im.size[0], im.size[1] - a.crop_bottom))

    if a.ratio:
        im = fit_ratio(im, a.ratio, a.pad, a.gap, a.line, a.top_bias)

    out = im if a.no_frame else add_frame(im, a.pad, a.gap, a.line)
    out.save(a.dst)
    ratio = out.size[0] / out.size[1]
    print("%s %dx%d -> %s %dx%d  比例 %.4f" % (
        a.src.split("/")[-1], ow, oh, a.dst.split("/")[-1], out.size[0], out.size[1], ratio))


if __name__ == "__main__":
    main()
