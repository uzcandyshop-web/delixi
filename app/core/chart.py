"""Bar-chart PNG generator for revenue/transactions reports.

Renders a 600x320 PNG with vertical bars, axes, value labels.
"""
from __future__ import annotations

from datetime import date
from decimal import Decimal
from io import BytesIO
from typing import Sequence

from PIL import Image, ImageDraw, ImageFont

WIDTH = 600
HEIGHT = 320
MARGIN_LEFT = 50
MARGIN_RIGHT = 20
MARGIN_TOP = 50
MARGIN_BOTTOM = 50

# Palette
BG = (18, 24, 38)
CARD_BG = (27, 36, 56)
TEXT = (240, 245, 255)
MUTED = (150, 160, 185)
BAR = (94, 201, 108)
BAR_LIGHT = (140, 220, 150)
GRID = (56, 68, 92)
BORDER = (42, 54, 80)


def _load_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
    ]
    for path in candidates:
        try:
            return ImageFont.truetype(path, size)
        except (OSError, IOError):
            continue
    return ImageFont.load_default()


def _fmt_compact(n: Decimal | int | float) -> str:
    """Format number compactly for axis labels: 1500000 -> '1.5M'."""
    n = float(n)
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f}M".replace(".0M", "M")
    if n >= 1_000:
        return f"{n / 1_000:.0f}k"
    return f"{n:.0f}"


def make_bar_chart(
    title: str,
    subtitle: str,
    bars: Sequence[tuple[str, Decimal | int | float]],
    lang: str = "ru",
) -> bytes:
    """Render a bar chart.

    bars: list of (label, value). label is shown under the bar (short),
          value determines bar height. The largest value sets the y-axis max.
    """
    img = Image.new("RGB", (WIDTH, HEIGHT), BG)
    draw = ImageDraw.Draw(img)

    # Card background
    draw.rectangle(
        [(8, 8), (WIDTH - 8, HEIGHT - 8)],
        fill=CARD_BG, outline=BORDER, width=2,
    )

    # Title + subtitle
    f_title = _load_font(20, bold=True)
    f_sub = _load_font(14)
    draw.text((MARGIN_LEFT, 14), title, font=f_title, fill=TEXT)
    if subtitle:
        draw.text((MARGIN_LEFT, 36), subtitle, font=f_sub, fill=MUTED)

    if not bars:
        f_empty = _load_font(16)
        msg = "Нет данных" if lang == "ru" else "Ma'lumot yo'q"
        bbox = draw.textbbox((0, 0), msg, font=f_empty)
        w = bbox[2] - bbox[0]
        draw.text(((WIDTH - w) / 2, HEIGHT / 2), msg, font=f_empty, fill=MUTED)
        buf = BytesIO()
        img.save(buf, format="PNG", optimize=True)
        return buf.getvalue()

    # Determine max for scale
    values = [float(v) for _, v in bars]
    max_v = max(values) if max(values) > 0 else 1.0

    # Plot area
    plot_x0 = MARGIN_LEFT
    plot_x1 = WIDTH - MARGIN_RIGHT
    plot_y0 = MARGIN_TOP
    plot_y1 = HEIGHT - MARGIN_BOTTOM
    plot_w = plot_x1 - plot_x0
    plot_h = plot_y1 - plot_y0

    # Y-axis grid + labels (4 lines: 0, 25%, 50%, 75%, 100%)
    f_axis = _load_font(11)
    for i in range(5):
        y = plot_y1 - (i / 4) * plot_h
        draw.line([(plot_x0, y), (plot_x1, y)], fill=GRID, width=1)
        v = (i / 4) * max_v
        label = _fmt_compact(v)
        draw.text((4, y - 7), label, font=f_axis, fill=MUTED)

    # Bars
    n = len(bars)
    bar_slot = plot_w / n
    bar_w = max(4, min(40, bar_slot * 0.6))
    # Skip every Nth label when bars are dense
    label_skip = 1
    if n > 14:
        label_skip = 2
    if n > 25:
        label_skip = 3

    f_label = _load_font(10)
    f_value = _load_font(10, bold=True)

    for i, (label, value) in enumerate(bars):
        v = float(value)
        x_center = plot_x0 + bar_slot * (i + 0.5)
        bar_x0 = x_center - bar_w / 2
        bar_x1 = x_center + bar_w / 2

        if max_v > 0:
            bar_h = (v / max_v) * plot_h
        else:
            bar_h = 0
        bar_y0 = plot_y1 - bar_h
        bar_y1 = plot_y1

        if v > 0:
            draw.rectangle([(bar_x0, bar_y0), (bar_x1, bar_y1)], fill=BAR)
            # Value above bar — only when bars aren't too dense
            if n <= 14:
                value_text = _fmt_compact(v)
                bbox = draw.textbbox((0, 0), value_text, font=f_value)
                text_w = bbox[2] - bbox[0]
                draw.text(
                    (x_center - text_w / 2, max(plot_y0, bar_y0 - 14)),
                    value_text, font=f_value, fill=TEXT,
                )

        # Label under bar — show every Nth depending on density
        if i % label_skip == 0:
            bbox = draw.textbbox((0, 0), label, font=f_label)
            label_w = bbox[2] - bbox[0]
            if label_w > bar_slot * label_skip - 2 and len(label) > 4:
                label = label[:4]
                bbox = draw.textbbox((0, 0), label, font=f_label)
                label_w = bbox[2] - bbox[0]
            draw.text(
                (x_center - label_w / 2, plot_y1 + 6),
                label, font=f_label, fill=MUTED,
            )

    buf = BytesIO()
    img.save(buf, format="PNG", optimize=True)
    return buf.getvalue()


def make_daily_chart(
    title: str,
    subtitle: str,
    daily: list[tuple[date, Decimal | int]],
    lang: str = "ru",
) -> bytes:
    """Helper for daily-aggregated data: formats dates as DD.MM labels."""
    bars = [(d.strftime("%d.%m"), v) for d, v in daily]
    return make_bar_chart(title, subtitle, bars, lang=lang)
