import pygame
import numpy as np
import cv2
import math
import os

# ═══════════════════════════════════════════════
#  SETTINGS
# ═══════════════════════════════════════════════
WIDTH, HEIGHT = 854, 480
FPS = 30
TOTAL_SECONDS = 50
TOTAL_FRAMES = FPS * TOTAL_SECONDS
OUTPUT_PATH = "output/about_you_8bit.mp4"

os.makedirs("output", exist_ok=True)
pygame.init()
surface = pygame.Surface((WIDTH, HEIGHT))

# ═══════════════════════════════════════════════
#  8-BIT COLOR PALETTES  (one per scene)
# ═══════════════════════════════════════════════
PALETTES = [
    {"bg": (10, 10, 30),  "accent": (80, 180, 255),  "text": (255, 255, 200), "deco": (255, 100, 150)},
    {"bg": (25, 10, 45),  "accent": (190, 90, 255),  "text": (200, 255, 210), "deco": (255, 210, 50) },
    {"bg": (8,  28, 18),  "accent": (40, 240, 140),  "text": (255, 210, 100), "deco": (90, 200, 255) },
    {"bg": (35, 10, 10),  "accent": (255, 90,  50),  "text": (255, 255, 255), "deco": (255, 200, 90) },
    {"bg": (15, 25, 45),  "accent": (100, 220, 255), "text": (230, 200, 255), "deco": (255, 130, 80) },
]

# ═══════════════════════════════════════════════
#  ✏️  PASTE YOUR LYRICS HERE
#  Each entry: text, start second, end second
# ═══════════════════════════════════════════════
RAW_LYRICS = [
    ("And there was something about you that now I can't remember", 0.0, 4.4),
    ("It's the same damn thing that made my heart surrender", 4.4, 9.6),
    ("And I'll miss you on a train, I'll miss you in the mornin'", 9.6, 15.1),
    ("I never know what to think about", 15.1, 18.3),
    ("I think about you", 18.3, 23.9),
    ("About you", 23.9, 29.0),
    ("Do you think I have forgotten", 29.0, 34.1),
    ("About you?", 34.1, 37.1),
]

# Convert seconds → frames
LYRICS = [{"text": t, "start": s * FPS, "end": e * FPS} for t, s, e in RAW_LYRICS]

# ═══════════════════════════════════════════════
#  FONTS
# ═══════════════════════════════════════════════
FONT_LARGE = pygame.font.Font("PressStart2P-Regular.ttf", 18)
FONT_SMALL = pygame.font.Font("PressStart2P-Regular.ttf", 10)
FONT_TINY  = pygame.font.Font("PressStart2P-Regular.ttf", 7)


# ═══════════════════════════════════════════════
#  PIXEL-ART DRAWING HELPERS
# ═══════════════════════════════════════════════
def pixel_rect(surf, color, x, y, pw, ph, scale=4):
    """Draw a pixel-art block (scaled rectangle)."""
    pygame.draw.rect(surf, color, (x * scale, y * scale, pw * scale, ph * scale))

def draw_pixelart(surf, bitmap, x, y, color, scale=4):
    """
    Draw a sprite from a 2D bitmap list (1=draw, 0=skip).
    x, y = top-left in pixels (not scaled).
    """
    for row_i, row in enumerate(bitmap):
        for col_i, cell in enumerate(row):
            if cell:
                pygame.draw.rect(
                    surf, color,
                    (x + col_i * scale, y + row_i * scale, scale, scale)
                )


# ═══════════════════════════════════════════════
#  PIXEL ART SPRITES
# ═══════════════════════════════════════════════
CAMERA_SPRITE = [
    [0,1,1,1,1,1,1,0],
    [1,1,1,1,1,1,1,1],
    [1,1,0,1,1,0,1,1],
    [1,1,1,1,1,1,1,1],
    [1,1,0,1,1,0,1,1],
    [1,1,1,1,1,1,1,1],
    [0,1,1,1,1,1,1,0],
    [0,0,1,1,1,1,0,0],
]

FOOTBALL_SPRITE = [
    [0,0,1,1,1,1,0,0],
    [0,1,1,0,0,1,1,0],
    [1,1,0,1,1,0,1,1],
    [1,0,1,1,1,1,0,1],
    [1,0,1,1,1,1,0,1],
    [1,1,0,1,1,0,1,1],
    [0,1,1,0,0,1,1,0],
    [0,0,1,1,1,1,0,0],
]

F1_SPRITE = [
    [0,0,0,1,1,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,1,1,1,1,1,1,1,1,1,1,0,0,0,0],
    [0,1,1,0,1,1,1,1,1,1,1,1,1,0,0,0],
    [1,1,1,1,1,1,1,1,1,1,1,1,1,1,0,0],
    [1,0,1,1,1,1,1,1,1,1,1,1,1,0,1,0],
    [0,0,1,1,0,0,1,1,1,1,0,0,1,1,0,0],
    [0,0,0,1,1,1,0,0,0,0,1,1,1,0,0,0],
]

CIRCUIT_SPRITE = [
    [1,1,0,0,1,1,0,1,1,0,0,1],
    [0,1,0,0,1,0,0,1,0,0,0,1],
    [0,1,1,1,1,0,0,1,1,1,1,1],
    [0,0,0,0,1,0,0,0,0,0,0,1],
    [1,1,1,1,1,0,1,1,1,0,0,1],
    [1,0,0,0,0,0,1,0,1,1,1,1],
    [1,0,1,1,1,1,1,0,0,0,0,1],
    [1,0,0,0,0,0,0,0,1,1,1,1],
]

HEART_SPRITE = [
    [0,1,1,0,1,1,0],
    [1,1,1,1,1,1,1],
    [1,1,1,1,1,1,1],
    [0,1,1,1,1,1,0],
    [0,0,1,1,1,0,0],
    [0,0,0,1,0,0,0],
]

STAR_SPRITE = [
    [0,0,0,1,0,0,0],
    [0,1,1,1,1,1,0],
    [1,1,1,1,1,1,1],
    [0,1,1,1,1,1,0],
    [0,1,0,0,0,1,0],
    [1,0,0,0,0,0,1],
]


# ═══════════════════════════════════════════════
#  SCENE ELEMENT LAYOUT
#  Maps lyric index → which sprites to show + positions
# ═══════════════════════════════════════════════
SCENE_ELEMENTS = [
    [("heart",   50,  80), ("star",  700, 80)],   # scene 0
    [("camera", 60, 320), ("star",  720, 50)],    # scene 1
    [("circuit", 30, 60), ("football", 680, 280)],# scene 2
    [("f1",     100, 200), ("heart", 650, 100)],  # scene 3
    [("football",50,100), ("camera", 660, 280)],  # scene 4
    [("star",    40, 300), ("circuit", 650,180)], # scene 5
    [("heart",   60, 200), ("f1",     450, 300)], # scene 6
    [("camera",  50,  50), ("football",680,180)], # scene 7
    [("circuit", 30,250), ("star",   700, 250)],  # scene 8
    [("f1",      80, 300), ("heart",  620,  80)], # scene 9
    [("star",    50, 180), ("camera", 650, 180)], # scene 10
    [("heart",  300, 380), ("star",  400,  30)],  # scene 11
]

SPRITE_MAP = {
    "camera":   CAMERA_SPRITE,
    "football": FOOTBALL_SPRITE,
    "f1":       F1_SPRITE,
    "circuit":  CIRCUIT_SPRITE,
    "heart":    HEART_SPRITE,
    "star":     STAR_SPRITE,
}


# ═══════════════════════════════════════════════
#  STARFIELD BACKGROUND
# ═══════════════════════════════════════════════
import random
random.seed(42)
STARS = [(random.randint(0, WIDTH), random.randint(0, HEIGHT),
          random.randint(1, 3), random.random() * 2 * math.pi)
         for _ in range(120)]

def draw_stars(surf, frame, color):
    for sx, sy, size, phase in STARS:
        brightness = int(128 + 127 * math.sin(frame * 0.05 + phase))
        c = tuple(min(255, int(ch * brightness / 255)) for ch in color)
        pygame.draw.rect(surf, c, (sx, sy, size, size))


# ═══════════════════════════════════════════════
#  SCANLINE OVERLAY  (CRT 8-bit effect)
# ═══════════════════════════════════════════════
def draw_scanlines(surf):
    for y in range(0, HEIGHT, 4):
        pygame.draw.line(surf, (0, 0, 0, 60), (0, y), (WIDTH, y))


# ═══════════════════════════════════════════════
#  GRID FLOOR
# ═══════════════════════════════════════════════
def draw_grid(surf, color, frame):
    offset = frame % 32
    for x in range(-32, WIDTH + 32, 32):
        pygame.draw.line(surf, color, (x + offset, HEIGHT // 2), (x - 60, HEIGHT), 1)
    for d in range(0, HEIGHT - HEIGHT // 2, 20):
        alpha = int(255 * (1 - d / (HEIGHT - HEIGHT // 2)))
        c = tuple(min(255, int(ch * alpha / 255)) for ch in color)
        pygame.draw.line(surf, c, (0, HEIGHT // 2 + d), (WIDTH, HEIGHT // 2 + d), 1)


# ═══════════════════════════════════════════════
#  LYRIC TEXT RENDERER  (with pixel shadow)
# ═══════════════════════════════════════════════
def draw_lyrics(surf, text, frame, start_frame, end_frame, text_color, accent):
    """Render centered lyric with fade-in/out and typewriter effect."""
    total = end_frame - start_frame
    elapsed = frame - start_frame
    fade_frames = FPS // 2  # 0.5s fade

    # Fade alpha (0-255)
    if elapsed < fade_frames:
        alpha = int(255 * elapsed / fade_frames)
    elif elapsed > total - fade_frames:
        alpha = int(255 * (total - elapsed) / fade_frames)
    else:
        alpha = 255

    # Typewriter: reveal characters over first 1.5s
    reveal_frames = min(int(FPS * 1.5), total // 2)
    if elapsed < reveal_frames:
        chars = max(1, int(len(text) * elapsed / reveal_frames))
        display = text[:chars]
    else:
        display = text

    # Word-wrap if too long
    words = display.split()
    lines = []
    line = ""
    for word in words:
        test = (line + " " + word).strip()
        if FONT_LARGE.size(test)[0] > WIDTH - 80:
            lines.append(line)
            line = word
        else:
            line = test
    if line:
        lines.append(line)

    total_h = len(lines) * 30
    start_y = HEIGHT // 2 - total_h // 2 + 20

    for i, ln in enumerate(lines):
        # Shadow
        shadow = FONT_LARGE.render(ln, False, (0, 0, 0))
        shadow.set_alpha(alpha)
        sr = shadow.get_rect(center=(WIDTH // 2 + 3, start_y + i * 34 + 3))
        surf.blit(shadow, sr)

        # Main text
        txt_surf = FONT_LARGE.render(ln, False, text_color)
        txt_surf.set_alpha(alpha)
        tr = txt_surf.get_rect(center=(WIDTH // 2, start_y + i * 34))
        surf.blit(txt_surf, tr)

    # Blinking cursor at end of typewriter
    if elapsed < reveal_frames + 10:
        if (frame // 8) % 2 == 0:
            cursor = FONT_LARGE.render("_", False, accent)
            cursor.set_alpha(alpha)
            last_line = FONT_LARGE.render(lines[-1] if lines else "", False, text_color)
            cx = WIDTH // 2 + last_line.get_width() // 2 + 4
            cy = start_y + (len(lines) - 1) * 34
            surf.blit(cursor, (cx, cy))


# ═══════════════════════════════════════════════
#  DECORATIVE ELEMENTS RENDERER
# ═══════════════════════════════════════════════
def draw_elements(surf, scene_idx, frame, deco_color, accent):
    elements = SCENE_ELEMENTS[min(scene_idx, len(SCENE_ELEMENTS) - 1)]
    for (name, bx, by) in elements:
        bitmap = SPRITE_MAP.get(name)
        if not bitmap:
            continue

        # Subtle floating animation
        phase = (scene_idx * 1.3) + (["camera","football","f1","circuit","heart","star"].index(name) * 0.7)
        float_y = int(6 * math.sin(frame * 0.06 + phase))

        # Alternate deco / accent per element
        color = deco_color if elements.index((name, bx, by)) % 2 == 0 else accent
        draw_pixelart(surf, bitmap, bx, by + float_y, color, scale=4)

        # Label
        label = FONT_TINY.render(name.upper(), False, color)
        lx = bx + (len(bitmap[0]) * 4) // 2 - label.get_width() // 2
        surf.blit(label, (lx, by + float_y + len(bitmap) * 4 + 4))


# ═══════════════════════════════════════════════
#  TITLE CARD  (first 2 seconds)
# ═══════════════════════════════════════════════
def draw_title(surf, frame, pal):
    alpha = min(255, frame * 8) if frame < 32 else max(0, 255 - (frame - 50) * 12)
    t1 = FONT_LARGE.render("ABOUT YOU", False, pal["text"])
    t2 = FONT_SMALL.render("The 1975", False, pal["accent"])
    t3 = FONT_TINY.render("8-BIT EDITION", False, pal["deco"])
    for surf_txt, y in [(t1, HEIGHT//2 - 40), (t2, HEIGHT//2), (t3, HEIGHT//2 + 30)]:
        surf_txt.set_alpha(alpha)
        r = surf_txt.get_rect(center=(WIDTH // 2, y))
        surf.blit(surf_txt, r)


# ═══════════════════════════════════════════════
#  PROGRESS BAR
# ═══════════════════════════════════════════════
def draw_progress(surf, frame, color):
    bar_w = int(WIDTH * frame / TOTAL_FRAMES)
    pygame.draw.rect(surf, color, (0, HEIGHT - 6, WIDTH, 6))
    pygame.draw.rect(surf, (255, 255, 255), (0, HEIGHT - 6, bar_w, 6))


# ═══════════════════════════════════════════════
#  PIXEL NOISE / GLITCH  (occasional flicker)
# ═══════════════════════════════════════════════
def draw_glitch(surf, frame, accent):
    if frame % 90 == 0:  # glitch every ~3s
        for _ in range(3):
            gx = random.randint(0, WIDTH - 60)
            gy = random.randint(0, HEIGHT - 8)
            pygame.draw.rect(surf, accent, (gx, gy, random.randint(20, 80), 4))


# ═══════════════════════════════════════════════
#  MAIN RENDER LOOP
# ═══════════════════════════════════════════════
TITLE_END_FRAME = 2 * FPS  # 2 second title card

fourcc = cv2.VideoWriter_fourcc(*"mp4v")
writer = cv2.VideoWriter(OUTPUT_PATH, fourcc, FPS, (WIDTH, HEIGHT))

print(f"🎮 Rendering {TOTAL_FRAMES} frames at {FPS}fps...")

for frame in range(TOTAL_FRAMES):

    # ── Determine current scene ──────────────────
    scene_idx = 0
    current_lyric = None
    for i, lyric in enumerate(LYRICS):
        if lyric["start"] <= frame < lyric["end"]:
            current_lyric = lyric
            scene_idx = i
            break
        elif frame >= lyric["start"]:
            scene_idx = i

    pal = PALETTES[scene_idx % len(PALETTES)]

    # ── Background ───────────────────────────────
    surface.fill(pal["bg"])
    draw_stars(surface, frame, pal["accent"])
    draw_grid(surface, tuple(max(0, c - 160) for c in pal["accent"]), frame)

    # ── Decorative pixel art ─────────────────────
    draw_elements(surface, scene_idx, frame, pal["deco"], pal["accent"])

    # ── Title card (first 2 seconds) ─────────────
    if frame < TITLE_END_FRAME:
        draw_title(surface, frame, pal)
    elif current_lyric:
        draw_lyrics(
            surface,
            current_lyric["text"],
            frame,
            current_lyric["start"],
            current_lyric["end"],
            pal["text"],
            pal["accent"],
        )

    # ── Effects ──────────────────────────────────
    draw_glitch(surface, frame, pal["accent"])
    draw_scanlines(surface)
    draw_progress(surface, frame, pal["deco"])

    # ── HUD: song title (top-left) ───────────────
    hud = FONT_TINY.render("ABOUT YOU - THE 1975", False, pal["deco"])
    surface.blit(hud, (10, 10))

    # ── Convert pygame surface → OpenCV frame ────
    frame_arr = pygame.surfarray.array3d(surface)
    frame_arr = np.transpose(frame_arr, (1, 0, 2))  # pygame → numpy layout
    frame_bgr = cv2.cvtColor(frame_arr, cv2.COLOR_RGB2BGR)
    writer.write(frame_bgr)

    if frame % (FPS * 5) == 0:
        print(f"  ⏳ {frame // FPS}s / {TOTAL_SECONDS}s complete...")

writer.release()
pygame.quit()
print(f"\n✅ Done! Video saved to: {OUTPUT_PATH}")
print("💡 Tip: Open with VLC or merge audio using FFmpeg:")
print(f"   ffmpeg -i {OUTPUT_PATH} -i your_audio.mp3 -shortest output_final.mp4")