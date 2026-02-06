"""
GreenScreen Bet Generator - Video Engine
Generates 1080x1920 (9:16) vertical videos with betting data overlays.
"""

import os
import uuid
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from PIL import Image, ImageDraw, ImageFont
from moviepy.editor import (
    ColorClip,
    ImageClip,
    TextClip,
    CompositeVideoClip,
    concatenate_videoclips,
)

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)

WIDTH, HEIGHT = 1080, 1920
FPS = 30
DURATION = 15  # seconds

# Colors
BG_COLOR = (11, 14, 17)        # #0B0E11
GREEN = "#00FF00"
GREEN_RGB = (0, 255, 0)
TEXT_COLOR = (229, 231, 235)    # #E5E7EB
DARK_GRAY = (30, 34, 40)


def _generate_chart(stats_label: str, stats_value: str) -> str:
    """Generate an upward trend chart with Matplotlib and return path to PNG."""
    fig, ax = plt.subplots(figsize=(8, 4), dpi=150)
    fig.patch.set_facecolor("#0B0E11")
    ax.set_facecolor("#0B0E11")

    np.random.seed(42)
    x = np.linspace(0, 10, 50)
    base = np.linspace(1, 8, 50)
    noise = np.random.normal(0, 0.3, 50)
    y = base + noise
    y = np.clip(y, 0.5, None)

    ax.plot(x, y, color=GREEN, linewidth=3, solid_capstyle="round")
    ax.fill_between(x, y, alpha=0.15, color=GREEN)

    ax.set_xlabel(stats_label if stats_label else "Performance", color="#E5E7EB", fontsize=14)
    ax.set_ylabel(stats_value if stats_value else "", color="#E5E7EB", fontsize=14)
    ax.tick_params(colors="#E5E7EB", labelsize=10)
    for spine in ax.spines.values():
        spine.set_color("#1E2228")

    ax.grid(True, alpha=0.1, color="#E5E7EB")

    chart_path = os.path.join(OUTPUT_DIR, f"chart_{uuid.uuid4().hex[:8]}.png")
    fig.savefig(chart_path, bbox_inches="tight", transparent=True)
    plt.close(fig)
    return chart_path


def _create_scanline_overlay() -> np.ndarray:
    """Create a scanline/CRT grain overlay frame."""
    overlay = np.zeros((HEIGHT, WIDTH, 4), dtype=np.uint8)
    # Horizontal scanlines every 4 pixels
    for y in range(0, HEIGHT, 4):
        overlay[y, :, 3] = 25  # subtle alpha
    # Random grain noise
    grain = np.random.randint(0, 15, (HEIGHT, WIDTH), dtype=np.uint8)
    overlay[:, :, 0] = grain
    overlay[:, :, 1] = grain
    overlay[:, :, 2] = grain
    overlay[:, :, 3] = np.clip(overlay[:, :, 3].astype(int) + grain.astype(int) // 2, 0, 40).astype(np.uint8)
    return overlay


def _make_frame_with_counter(
    home_team: str,
    away_team: str,
    odd: float,
    profit: float,
    chart_img: np.ndarray,
    scanline: np.ndarray,
    extra_tip: str = "",
):
    """Return a function that generates frame at time t with animated counter."""

    def make_frame(t):
        # Create base image
        img = Image.new("RGBA", (WIDTH, HEIGHT), (*BG_COLOR, 255))
        draw = ImageDraw.Draw(img)

        # Try to load fonts, fall back to default
        try:
            font_big = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 72)
            font_med = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 48)
            font_sm = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 36)
            font_mono = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 64)
        except (IOError, OSError):
            font_big = ImageFont.load_default()
            font_med = ImageFont.load_default()
            font_sm = ImageFont.load_default()
            font_mono = ImageFont.load_default()

        # -- Header: "GREENSCREEN" branding --
        draw.text((WIDTH // 2, 120), "GREENSCREEN", fill=GREEN_RGB, font=font_big, anchor="mm")
        draw.text((WIDTH // 2, 180), "BET GENERATOR", fill=TEXT_COLOR, font=font_sm, anchor="mm")

        # -- Divider line --
        draw.line([(80, 230), (WIDTH - 80, 230)], fill=GREEN_RGB, width=2)

        # -- Match info --
        match_text = f"{home_team}  vs  {away_team}"
        draw.text((WIDTH // 2, 320), match_text, fill=TEXT_COLOR, font=font_med, anchor="mm")

        # -- Odd badge --
        odd_text = f"Odd: {odd:.2f}"
        draw.rounded_rectangle([(WIDTH // 2 - 180, 380), (WIDTH // 2 + 180, 450)],
                                radius=12, fill=DARK_GRAY, outline=GREEN_RGB, width=2)
        draw.text((WIDTH // 2, 415), odd_text, fill=GREEN_RGB, font=font_sm, anchor="mm")

        # -- Animated profit counter --
        # Ease-in-out animation over first 4 seconds
        anim_t = min(t / 4.0, 1.0)
        eased = anim_t * anim_t * (3 - 2 * anim_t)  # smoothstep
        current_profit = profit * eased

        draw.text((WIDTH // 2, 540), "LUCRO ESTIMADO", fill=TEXT_COLOR, font=font_sm, anchor="mm")
        profit_str = f"R$ {current_profit:,.2f}"
        draw.text((WIDTH // 2, 630), profit_str, fill=GREEN_RGB, font=font_mono, anchor="mm")

        # -- Green glow rectangle behind profit --
        if t > 4.0:
            pulse = int(15 + 10 * np.sin(t * 3))
            draw.rounded_rectangle(
                [(WIDTH // 2 - 300, 580), (WIDTH // 2 + 300, 670)],
                radius=16,
                outline=(*GREEN_RGB, pulse * 5),
                width=3,
            )

        # -- Chart overlay --
        chart_pil = Image.fromarray(chart_img).convert("RGBA")
        chart_pil = chart_pil.resize((900, 450))
        # Fade in chart after 2 seconds
        if t >= 2.0:
            chart_alpha = min((t - 2.0) / 1.5, 1.0)
            alpha_channel = chart_pil.split()[3]
            alpha_channel = alpha_channel.point(lambda p: int(p * chart_alpha))
            chart_pil.putalpha(alpha_channel)
            img.paste(chart_pil, (90, 750), chart_pil)

        # -- Extra tip --
        if extra_tip:
            draw.text((WIDTH // 2, 1280), "DICA EXTRA", fill=GREEN_RGB, font=font_sm, anchor="mm")
            # Word wrap the tip
            words = extra_tip.split()
            lines = []
            current = ""
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
                draw.text((WIDTH // 2, 1340 + i * 45), line, fill=TEXT_COLOR, font=font_sm, anchor="mm")

        # -- Footer --
        draw.line([(80, HEIGHT - 200), (WIDTH - 80, HEIGHT - 200)], fill=GREEN_RGB, width=2)
        draw.text((WIDTH // 2, HEIGHT - 140), "greenscreen.bet", fill=(*TEXT_COLOR, 180), font=font_sm, anchor="mm")
        draw.text((WIDTH // 2, HEIGHT - 80), "Análise gerada por IA", fill=(*TEXT_COLOR, 100), font=font_sm, anchor="mm")

        # -- Apply scanline overlay --
        scanline_img = Image.fromarray(scanline)
        img = Image.alpha_composite(img, scanline_img)

        return np.array(img.convert("RGB"))

    return make_frame


def generate_video(
    home_team: str,
    away_team: str,
    odd: float,
    profit: float,
    stats_label: str = "Performance",
    stats_value: str = "",
    extra_tip: str = "",
) -> str:
    """Generate a 15-second vertical video and return the file path."""

    # Generate chart
    chart_path = _generate_chart(stats_label, stats_value)
    chart_img = np.array(Image.open(chart_path).convert("RGBA"))

    # Generate scanline overlay (static)
    scanline = _create_scanline_overlay()

    # Build video using make_frame
    frame_fn = _make_frame_with_counter(
        home_team, away_team, odd, profit, chart_img, scanline, extra_tip
    )

    video = ColorClip(size=(WIDTH, HEIGHT), color=BG_COLOR, duration=DURATION)
    video = video.set_make_frame(lambda t: frame_fn(t))
    video = video.set_fps(FPS)
    video = video.set_duration(DURATION)

    # Output
    filename = f"bet_{uuid.uuid4().hex[:8]}.mp4"
    output_path = os.path.join(OUTPUT_DIR, filename)

    video.write_videofile(
        output_path,
        fps=FPS,
        codec="libx264",
        audio=False,
        preset="ultrafast",
        logger=None,
    )

    # Cleanup chart
    if os.path.exists(chart_path):
        os.remove(chart_path)

    return output_path
