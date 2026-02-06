"""
BetCerta - Video Engine
Generates 720x1280 (9:16) vertical videos with betting data overlays.
Uses ffmpeg directly via subprocess to minimize memory usage.
"""

import os
import uuid
import subprocess
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from PIL import Image, ImageDraw, ImageFont

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)

WIDTH, HEIGHT = 720, 1280
FPS = 15
DURATION = 10

# Colors
BG_COLOR = (11, 14, 17)
GREEN_RGB = (0, 255, 0)
TEXT_COLOR = (229, 231, 235)
DARK_GRAY = (30, 34, 40)

_fonts = {}

def _get_fonts():
    if _fonts:
        return _fonts
    try:
        _fonts["big"] = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 46)
        _fonts["med"] = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 30)
        _fonts["sm"] = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 22)
        _fonts["mono"] = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf", 40)
        _fonts["mono_sm"] = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 26)
        _fonts["xs"] = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 16)
    except (IOError, OSError):
        default = ImageFont.load_default()
        for k in ("big", "med", "sm", "mono", "mono_sm", "xs"):
            _fonts[k] = default
    return _fonts


def _generate_chart_image() -> Image.Image:
    """Generate upward trend chart as PIL Image."""
    fig, ax = plt.subplots(figsize=(6, 3), dpi=80)
    fig.patch.set_facecolor("#0B0E11")
    ax.set_facecolor("#0B0E11")

    np.random.seed(42)
    x = np.linspace(0, 10, 30)
    y = np.clip(np.linspace(1, 8, 30) + np.random.normal(0, 0.3, 30), 0.5, None)

    ax.plot(x, y, color="#00FF00", linewidth=2.5)
    ax.fill_between(x, y, alpha=0.12, color="#00FF00")
    ax.tick_params(colors="#E5E7EB", labelsize=8)
    for spine in ax.spines.values():
        spine.set_color("#1E2228")
    ax.grid(True, alpha=0.1, color="#E5E7EB")

    fig.canvas.draw()
    w, h = fig.canvas.get_width_height()
    buf = np.frombuffer(fig.canvas.buffer_rgba(), dtype=np.uint8).reshape(h, w, 4)
    chart = Image.fromarray(buf).convert("RGBA").resize((600, 270))
    plt.close(fig)
    return chart


def _render_frame(t, fonts, chart, home_team, away_team, odd, profit, bet_amount, unit, extra_tip):
    """Render a single frame at time t, returns RGB PIL Image."""
    img = Image.new("RGB", (WIDTH, HEIGHT), BG_COLOR)
    draw = ImageDraw.Draw(img)

    # Header
    draw.text((WIDTH // 2, 80), "BETCERTA", fill=GREEN_RGB, font=fonts["big"], anchor="mm")
    draw.text((WIDTH // 2, 120), "GERADOR DE VÍDEOS", fill=TEXT_COLOR, font=fonts["xs"], anchor="mm")
    draw.line([(50, 150), (WIDTH - 50, 150)], fill=GREEN_RGB, width=2)

    # Match
    draw.text((WIDTH // 2, 200), f"{home_team}  vs  {away_team}", fill=TEXT_COLOR, font=fonts["med"], anchor="mm")

    # Odd badge
    draw.rounded_rectangle([(WIDTH // 2 - 120, 240), (WIDTH // 2 + 120, 290)],
                            radius=10, fill=DARK_GRAY, outline=GREEN_RGB, width=2)
    draw.text((WIDTH // 2, 265), f"Odd: {odd:.2f}", fill=GREEN_RGB, font=fonts["sm"], anchor="mm")

    # Bet + Unit cards
    draw.rounded_rectangle([(60, 310), (345, 380)], radius=10, fill=DARK_GRAY, outline=(*TEXT_COLOR, 60), width=1)
    draw.text((202, 325), "VALOR DA APOSTA", fill=(*TEXT_COLOR, 150), font=fonts["xs"], anchor="mt")
    draw.text((202, 355), f"R$ {bet_amount:,.2f}", fill=GREEN_RGB, font=fonts["mono_sm"], anchor="mm")

    draw.rounded_rectangle([(375, 310), (660, 380)], radius=10, fill=DARK_GRAY, outline=(*TEXT_COLOR, 60), width=1)
    draw.text((517, 325), "UNIDADE INDICADA", fill=(*TEXT_COLOR, 150), font=fonts["xs"], anchor="mt")
    draw.text((517, 355), f"{unit:.1f}%", fill=GREEN_RGB, font=fonts["mono_sm"], anchor="mm")

    # Animated profit
    anim_t = min(t / 3.5, 1.0)
    eased = anim_t * anim_t * (3 - 2 * anim_t)
    current_profit = profit * eased

    draw.text((WIDTH // 2, 420), "LUCRO ESTIMADO", fill=TEXT_COLOR, font=fonts["sm"], anchor="mm")
    draw.text((WIDTH // 2, 470), f"R$ {current_profit:,.2f}", fill=GREEN_RGB, font=fonts["mono"], anchor="mm")

    # Glow pulse after counter done
    if t > 3.5:
        pulse = int(15 + 10 * np.sin(t * 3))
        draw.rounded_rectangle(
            [(WIDTH // 2 - 200, 445), (WIDTH // 2 + 200, 495)],
            radius=12, outline=(*GREEN_RGB, min(pulse * 5, 255)), width=2,
        )

    # Chart fade in
    if t >= 1.5:
        alpha = min((t - 1.5) / 1.0, 1.0)
        c = chart.copy()
        a = c.split()[3].point(lambda p: int(p * alpha))
        c.putalpha(a)
        temp = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
        temp.paste(c, (60, 520), c)
        img = Image.composite(temp.convert("RGB"), img, temp.split()[3])
        draw = ImageDraw.Draw(img)

    # Extra tip
    if extra_tip:
        draw.text((WIDTH // 2, 850), "DICA EXTRA", fill=GREEN_RGB, font=fonts["sm"], anchor="mm")
        words = extra_tip.split()
        lines, cur = [], ""
        for w in words:
            test = f"{cur} {w}".strip()
            if len(test) > 40:
                lines.append(cur)
                cur = w
            else:
                cur = test
        if cur:
            lines.append(cur)
        for i, line in enumerate(lines[:3]):
            draw.text((WIDTH // 2, 885 + i * 30), line, fill=TEXT_COLOR, font=fonts["sm"], anchor="mm")

    # Footer
    draw.line([(50, HEIGHT - 130), (WIDTH - 50, HEIGHT - 130)], fill=GREEN_RGB, width=2)
    draw.text((WIDTH // 2, HEIGHT - 90), "betcerta.fly.dev", fill=(*TEXT_COLOR, 150), font=fonts["sm"], anchor="mm")
    draw.text((WIDTH // 2, HEIGHT - 55), "Análise gerada por IA", fill=(*TEXT_COLOR, 100), font=fonts["xs"], anchor="mm")

    # Simple scanline effect (draw directly, no overlay)
    for sy in range(0, HEIGHT, 4):
        draw.line([(0, sy), (WIDTH, sy)], fill=(0, 0, 0), width=1)

    return img


def generate_video(
    home_team: str,
    away_team: str,
    odd: float,
    profit: float,
    bet_amount: float = 0.0,
    unit: float = 0.0,
    extra_tip: str = "",
) -> str:
    """Generate a vertical video by piping frames to ffmpeg."""
    fonts = _get_fonts()
    chart = _generate_chart_image()

    filename = f"bet_{uuid.uuid4().hex[:8]}.mp4"
    output_path = os.path.join(OUTPUT_DIR, filename)

    total_frames = FPS * DURATION

    # Pipe raw frames to ffmpeg
    cmd = [
        "ffmpeg", "-y",
        "-f", "rawvideo",
        "-vcodec", "rawvideo",
        "-s", f"{WIDTH}x{HEIGHT}",
        "-pix_fmt", "rgb24",
        "-r", str(FPS),
        "-i", "-",
        "-c:v", "libx264",
        "-preset", "ultrafast",
        "-pix_fmt", "yuv420p",
        "-an",
        output_path,
    ]

    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    for frame_idx in range(total_frames):
        t = frame_idx / FPS
        img = _render_frame(t, fonts, chart, home_team, away_team, odd, profit, bet_amount, unit, extra_tip)
        proc.stdin.write(img.tobytes())

    proc.stdin.close()
    proc.wait()

    return output_path
