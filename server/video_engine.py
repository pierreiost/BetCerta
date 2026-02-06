"""
BetCerta - Video Engine
Generates 1080x1920 (9:16) vertical videos with betting data overlays.
"""

import os
import uuid
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from PIL import Image, ImageDraw, ImageFont
from moviepy.editor import ColorClip

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)

WIDTH, HEIGHT = 1080, 1920
FPS = 24
DURATION = 12  # seconds (shorter = less memory)

# Colors
BG_COLOR = (11, 14, 17)        # #0B0E11
GREEN = "#00FF00"
GREEN_RGB = (0, 255, 0)
TEXT_COLOR = (229, 231, 235)    # #E5E7EB
DARK_GRAY = (30, 34, 40)

# Pre-load fonts once
_fonts = {}

def _get_fonts():
    if _fonts:
        return _fonts
    try:
        _fonts["big"] = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 68)
        _fonts["med"] = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 44)
        _fonts["sm"] = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 34)
        _fonts["mono"] = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf", 60)
        _fonts["mono_sm"] = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 38)
        _fonts["xs"] = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 22)
    except (IOError, OSError):
        default = ImageFont.load_default()
        _fonts["big"] = default
        _fonts["med"] = default
        _fonts["sm"] = default
        _fonts["mono"] = default
        _fonts["mono_sm"] = default
        _fonts["xs"] = default
    return _fonts


def _generate_chart() -> np.ndarray:
    """Generate an upward trend chart and return as RGBA numpy array."""
    fig, ax = plt.subplots(figsize=(8, 4), dpi=100)
    fig.patch.set_facecolor("#0B0E11")
    ax.set_facecolor("#0B0E11")

    np.random.seed(42)
    x = np.linspace(0, 10, 40)
    base = np.linspace(1, 8, 40)
    noise = np.random.normal(0, 0.3, 40)
    y = np.clip(base + noise, 0.5, None)

    ax.plot(x, y, color=GREEN, linewidth=3, solid_capstyle="round")
    ax.fill_between(x, y, alpha=0.15, color=GREEN)
    ax.tick_params(colors="#E5E7EB", labelsize=9)
    for spine in ax.spines.values():
        spine.set_color("#1E2228")
    ax.grid(True, alpha=0.1, color="#E5E7EB")

    fig.canvas.draw()
    w, h = fig.canvas.get_width_height()
    buf = np.frombuffer(fig.canvas.tostring_argb(), dtype=np.uint8).reshape(h, w, 4)
    # ARGB → RGBA
    rgba = np.empty_like(buf)
    rgba[:, :, 0] = buf[:, :, 1]
    rgba[:, :, 1] = buf[:, :, 2]
    rgba[:, :, 2] = buf[:, :, 3]
    rgba[:, :, 3] = buf[:, :, 0]
    plt.close(fig)
    return rgba


def _create_scanline_overlay() -> np.ndarray:
    """Create a scanline/CRT grain overlay frame."""
    overlay = np.zeros((HEIGHT, WIDTH, 4), dtype=np.uint8)
    for y in range(0, HEIGHT, 4):
        overlay[y, :, 3] = 25
    grain = np.random.randint(0, 12, (HEIGHT, WIDTH), dtype=np.uint8)
    overlay[:, :, 0] = grain
    overlay[:, :, 1] = grain
    overlay[:, :, 2] = grain
    overlay[:, :, 3] = np.clip(overlay[:, :, 3].astype(np.int16) + grain.astype(np.int16) // 2, 0, 35).astype(np.uint8)
    return overlay


def _make_frame_fn(
    home_team: str,
    away_team: str,
    odd: float,
    profit: float,
    bet_amount: float,
    unit: float,
    chart_img: np.ndarray,
    scanline: np.ndarray,
    extra_tip: str = "",
):
    """Return a function that generates frame at time t."""
    fonts = _get_fonts()
    chart_pil = Image.fromarray(chart_img).convert("RGBA").resize((900, 400))
    scanline_img = Image.fromarray(scanline)

    def make_frame(t):
        img = Image.new("RGBA", (WIDTH, HEIGHT), (*BG_COLOR, 255))
        draw = ImageDraw.Draw(img)

        # -- Header: "BETCERTA" branding --
        draw.text((WIDTH // 2, 120), "BETCERTA", fill=GREEN_RGB, font=fonts["big"], anchor="mm")
        draw.text((WIDTH // 2, 180), "GERADOR DE VÍDEOS", fill=TEXT_COLOR, font=fonts["sm"], anchor="mm")

        # -- Divider --
        draw.line([(80, 230), (WIDTH - 80, 230)], fill=GREEN_RGB, width=2)

        # -- Match --
        match_text = f"{home_team}  vs  {away_team}"
        draw.text((WIDTH // 2, 320), match_text, fill=TEXT_COLOR, font=fonts["med"], anchor="mm")

        # -- Odd badge --
        draw.rounded_rectangle([(WIDTH // 2 - 180, 380), (WIDTH // 2 + 180, 450)],
                                radius=12, fill=DARK_GRAY, outline=GREEN_RGB, width=2)
        draw.text((WIDTH // 2, 415), f"Odd: {odd:.2f}", fill=GREEN_RGB, font=fonts["sm"], anchor="mm")

        # -- Bet amount + Unit (side by side) --
        draw.rounded_rectangle([(100, 480), (520, 560)],
                                radius=12, fill=DARK_GRAY, outline=(*TEXT_COLOR, 80), width=1)
        draw.text((310, 500), "VALOR DA APOSTA", fill=(*TEXT_COLOR, 180), font=fonts["xs"], anchor="mt")
        draw.text((310, 535), f"R$ {bet_amount:,.2f}", fill=GREEN_RGB, font=fonts["mono_sm"], anchor="mm")

        draw.rounded_rectangle([(560, 480), (980, 560)],
                                radius=12, fill=DARK_GRAY, outline=(*TEXT_COLOR, 80), width=1)
        draw.text((770, 500), "UNIDADE INDICADA", fill=(*TEXT_COLOR, 180), font=fonts["xs"], anchor="mt")
        draw.text((770, 535), f"{unit:.1f}%", fill=GREEN_RGB, font=fonts["mono_sm"], anchor="mm")

        # -- Animated profit counter --
        anim_t = min(t / 4.0, 1.0)
        eased = anim_t * anim_t * (3 - 2 * anim_t)
        current_profit = profit * eased

        draw.text((WIDTH // 2, 620), "LUCRO ESTIMADO", fill=TEXT_COLOR, font=fonts["sm"], anchor="mm")
        draw.text((WIDTH // 2, 700), f"R$ {current_profit:,.2f}", fill=GREEN_RGB, font=fonts["mono"], anchor="mm")

        # -- Glow after animation --
        if t > 4.0:
            pulse = int(15 + 10 * np.sin(t * 3))
            draw.rounded_rectangle(
                [(WIDTH // 2 - 300, 660), (WIDTH // 2 + 300, 740)],
                radius=16, outline=(*GREEN_RGB, min(pulse * 5, 255)), width=3,
            )

        # -- Chart --
        if t >= 2.0:
            chart_alpha = min((t - 2.0) / 1.5, 1.0)
            c = chart_pil.copy()
            alpha_ch = c.split()[3]
            alpha_ch = alpha_ch.point(lambda p: int(p * chart_alpha))
            c.putalpha(alpha_ch)
            img.paste(c, (90, 800), c)

        # -- Extra tip --
        if extra_tip:
            draw.text((WIDTH // 2, 1280), "DICA EXTRA", fill=GREEN_RGB, font=fonts["sm"], anchor="mm")
            words = extra_tip.split()
            lines, current = [], ""
            for w in words:
                test = f"{current} {w}".strip()
                if len(test) > 35:
                    lines.append(current)
                    current = w
                else:
                    current = test
            if current:
                lines.append(current)
            for i, line in enumerate(lines[:3]):
                draw.text((WIDTH // 2, 1340 + i * 45), line, fill=TEXT_COLOR, font=fonts["sm"], anchor="mm")

        # -- Footer --
        draw.line([(80, HEIGHT - 200), (WIDTH - 80, HEIGHT - 200)], fill=GREEN_RGB, width=2)
        draw.text((WIDTH // 2, HEIGHT - 140), "betcerta.fly.dev", fill=(*TEXT_COLOR, 180), font=fonts["sm"], anchor="mm")
        draw.text((WIDTH // 2, HEIGHT - 80), "Análise gerada por IA", fill=(*TEXT_COLOR, 100), font=fonts["sm"], anchor="mm")

        # -- Scanline --
        img_out = Image.alpha_composite(img, scanline_img)
        return np.array(img_out.convert("RGB"))

    return make_frame


def generate_video(
    home_team: str,
    away_team: str,
    odd: float,
    profit: float,
    bet_amount: float = 0.0,
    unit: float = 0.0,
    extra_tip: str = "",
) -> str:
    """Generate a vertical video and return the file path."""

    chart_img = _generate_chart()
    scanline = _create_scanline_overlay()

    frame_fn = _make_frame_fn(
        home_team, away_team, odd, profit, bet_amount, unit,
        chart_img, scanline, extra_tip
    )

    video = ColorClip(size=(WIDTH, HEIGHT), color=BG_COLOR, duration=DURATION)
    video = video.set_make_frame(lambda t: frame_fn(t))
    video = video.set_fps(FPS)
    video = video.set_duration(DURATION)

    filename = f"bet_{uuid.uuid4().hex[:8]}.mp4"
    output_path = os.path.join(OUTPUT_DIR, filename)

    video.write_videofile(
        output_path,
        fps=FPS,
        codec="libx264",
        audio=False,
        preset="ultrafast",
        threads=2,
        logger=None,
    )

    return output_path
