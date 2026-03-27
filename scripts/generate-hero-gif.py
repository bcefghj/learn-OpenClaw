#!/usr/bin/env python3
"""生成 README 顶部展示的轻量循环 GIF（GitHub 会正常播放动画）。"""
from __future__ import annotations

import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "assets" / "hero-openclaw-flow.gif"
W, H = 720, 200
FRAMES = 36
BG = (13, 17, 23)  # 接近 GitHub dark
ACCENT = (255, 107, 53)
ACCENT2 = (247, 197, 159)
TEXT = (230, 237, 243)


def try_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for name in (
        "PingFang SC",
        "Heiti SC",
        "STHeiti",
        "Arial Unicode MS",
        "Helvetica",
    ):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


def main() -> None:
    font_sm = try_font(15)
    font_md = try_font(18)
    font_lg = try_font(22)

    nodes = [
        (60, "用户消息"),
        (210, "Gateway"),
        (380, "Agent Runner"),
        (540, "ReAct + Tools"),
    ]
    box_w, box_h = 130, 44

    images: list[Image.Image] = []
    for fi in range(FRAMES):
        phase = (fi / FRAMES) * 2 * 3.14159
        img = Image.new("RGB", (W, H), BG)
        d = ImageDraw.Draw(img)

        title = "OpenClaw 消息链路（循环示意）"
        d.text((W // 2, 22), title, fill=TEXT, font=font_lg, anchor="mm")

        # 节点框
        y0 = 70
        for x, label in nodes:
            d.rounded_rectangle(
                (x, y0, x + box_w, y0 + box_h),
                radius=8,
                outline=ACCENT,
                width=2,
            )
            d.text(
                (x + box_w // 2, y0 + box_h // 2),
                label,
                fill=TEXT,
                font=font_sm,
                anchor="mm",
            )

        # 流动光点（沿连接线）
        seg_len = [150, 170, 160]  # approx gaps between box centers
        starts = [60 + box_w, 210 + box_w, 380 + box_w]
        cy = y0 + box_h // 2
        total = sum(seg_len)
        dist = (fi / FRAMES) * total
        acc = 0.0
        for i, L in enumerate(seg_len):
            if dist <= acc + L:
                t = (dist - acc) / L
                x1 = starts[i] - 20
                x2 = starts[i] + int(L * 0.85)
                px = int(x1 + t * (x2 - x1))
                r = 5 + int(2 * abs(math.sin(phase)))
                d.ellipse((px - r, cy - r, px + r, cy + r), fill=ACCENT2)
                break
            acc += L

        d.text(
            (W // 2, H - 18),
            "learn-openclaw-for-interview · 零基础 → 面试通关",
            fill=(139, 148, 158),
            font=font_md,
            anchor="mm",
        )

        images.append(img)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    images[0].save(
        OUT,
        save_all=True,
        append_images=images[1:],
        duration=60,
        loop=0,
        optimize=True,
    )
    print(f"Wrote {OUT} ({len(images)} frames)")


if __name__ == "__main__":
    main()
