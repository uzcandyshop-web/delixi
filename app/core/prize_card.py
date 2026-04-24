"""Prize card PNG generator: name, cost, progress bar, balance.

Renders a 600x280 PNG card. Returns PNG bytes suitable for Telegram.
"""
from __future__ import annotations

from decimal import Decimal
from io import BytesIO
from typing import Optional

from PIL import Image, ImageDraw, ImageFont

# Card dimensions (Telegram auto-scales but native size looks best on mobile)
WIDTH = 600
HEIGHT = 280
MARGIN = 24

# Progress bar
BAR_SEGMENTS = 10
BAR_SEGMENT_W = 48
BAR_SEGMENT_H = 28
BAR_SEGMENT_GAP = 6

# Palette
BG = (18, 24, 38)           # dark navy
CARD_BG = (27, 36, 56)      # slightly lighter card
TEXT = (240, 245, 255)
MUTED = (150, 160, 185)
ACCENT = (94, 201, 108)     # green — filled segment
EMPTY = (56, 68, 92)        # dark grey — empty segment
BORDER = (42, 54, 80)
ACCENT_UNLOCKED = (255, 213, 79)  # warm yellow — "available" badge


def _load_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    """Try to load a reasonable sans-serif font; fall back to PIL default."""
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


def _fmt_num(n: Decimal) -> str:
    """Format a decimal with thousand spaces, no trailing zeros."""
    q = n.quantize(Decimal("1")) if n == n.to_integral_value() else n
    return f"{q:,}".replace(",", " ")


def make_prize_card(
    prize_name: str,
    cost: Decimal,
    balance: Decimal,
    lang: str = "ru",
) -> bytes:
    """Render a prize card PNG with a progress bar.

    progress = min(balance / cost, 1.0) — 10-segment bar (green filled / dark empty).
    If balance >= cost, shows a "available" banner instead of bar.
    """
    img = Image.new("RGB", (WIDTH, HEIGHT), BG)
    draw = ImageDraw.Draw(img)

    # Card background with rounded-ish border
    draw.rectangle(
        [(MARGIN // 2, MARGIN // 2), (WIDTH - MARGIN // 2, HEIGHT - MARGIN // 2)],
        fill=CARD_BG, outline=BORDER, width=2,
    )

    # Localized labels
    if lang == "uz":
        label_cost = "Narxi"
        label_balance = "Sizda"
        label_need_more = "yana {n} ball kerak"
        label_available = "✓ SOVG'A SIZGA OCHIQ"
        unit = "ball"
    else:
        label_cost = "Стоимость"
        label_balance = "У вас"
        label_need_more = "нужно ещё {n} баллов"
        label_available = "✓ ПРИЗ ДОСТУПЕН"
        unit = "баллов"

    # Title (prize name), truncate if too long
    f_title = _load_font(28, bold=True)
    title = prize_name
    # Rough width truncation
    max_title_w = WIDTH - 2 * MARGIN
    while draw.textlength(title, font=f_title) > max_title_w and len(title) > 4:
        title = title[:-2]
    if title != prize_name:
        title = title.rstrip() + "…"
    draw.text((MARGIN, MARGIN), title, font=f_title, fill=TEXT)

    # Cost line
    f_small = _load_font(18)
    cost_text = f"{label_cost}: {_fmt_num(cost)} {unit}"
    draw.text((MARGIN, MARGIN + 42), cost_text, font=f_small, fill=MUTED)

    # Balance line
    balance_text = f"{label_balance}: {_fmt_num(balance)} {unit}"
    draw.text((MARGIN, MARGIN + 68), balance_text, font=f_small, fill=MUTED)

    # Progress bar or "available" badge
    bar_y = MARGIN + 110

    if balance >= cost:
        # Badge
        f_badge = _load_font(24, bold=True)
        badge_w = draw.textlength(label_available, font=f_badge)
        badge_x = (WIDTH - badge_w) / 2
        badge_pad_x = 20
        badge_pad_y = 12
        badge_rect = (
            badge_x - badge_pad_x, bar_y - badge_pad_y,
            badge_x + badge_w + badge_pad_x, bar_y + 32 + badge_pad_y,
        )
        draw.rectangle(badge_rect, fill=ACCENT)
        draw.text((badge_x, bar_y), label_available, font=f_badge, fill=(15, 30, 18))
    else:
        # 10-segment bar
        ratio = float(balance) / float(cost) if cost > 0 else 0.0
        filled = int(ratio * BAR_SEGMENTS)
        # Ensure at least 1 segment if any progress
        if balance > 0 and filled == 0:
            filled = 1

        bar_total_w = BAR_SEGMENTS * BAR_SEGMENT_W + (BAR_SEGMENTS - 1) * BAR_SEGMENT_GAP
        bar_x = (WIDTH - bar_total_w) // 2

        for i in range(BAR_SEGMENTS):
            x = bar_x + i * (BAR_SEGMENT_W + BAR_SEGMENT_GAP)
            color = ACCENT if i < filled else EMPTY
            draw.rectangle(
                [(x, bar_y), (x + BAR_SEGMENT_W, bar_y + BAR_SEGMENT_H)],
                fill=color,
            )

        # Progress text below
        percent = int(ratio * 100)
        need_more = cost - balance
        f_prog = _load_font(20, bold=True)
        prog_text = f"{percent}%  —  {label_need_more.format(n=_fmt_num(need_more))}"
        prog_w = draw.textlength(prog_text, font=f_prog)
        draw.text(
            ((WIDTH - prog_w) / 2, bar_y + BAR_SEGMENT_H + 16),
            prog_text, font=f_prog, fill=TEXT,
        )

    buf = BytesIO()
    img.save(buf, format="PNG", optimize=True)
    return buf.getvalue()
