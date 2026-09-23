import pygame
import numpy as np
import cv2
import math
import os
import random
import time
import sys
import shutil
import subprocess

# ═══════════════════════════════════════════════════════════════
#  SETTINGS
# ═══════════════════════════════════════════════════════════════
BASE_DIR       = os.path.dirname(os.path.abspath(__file__))   # paths no longer depend on cwd
WIDTH, HEIGHT  = 854, 480
FPS            = 30
OUT_SCALE      = 3               # output = 854x480 * OUT_SCALE (whole numbers keep pixels crisp): 2 -> 1708x960, 3 -> 2562x1440
OUT_SIZE       = (WIDTH * OUT_SCALE, HEIGHT * OUT_SCALE)
FALLBACK_SECONDS = 50            # used only if the audio length can't be read
OUTRO_EXTRA    = 6               # seconds of outro held after the song ends (audio is padded with silence)
REALTIME       = True           # True = lock preview to real time; False = render as fast as possible
AUDIO_PATH     = os.path.join(BASE_DIR, "about_you.MP3")
FONT_PATH      = os.path.join(BASE_DIR, "PressStart2P-Regular.ttf")
OUT_DIR        = os.path.join(BASE_DIR, "output")
SILENT_PATH    = os.path.join(OUT_DIR, "about_you_kaleido_silent.mp4")   # own name: no clash with main.py
OUTPUT_PATH    = os.path.join(OUT_DIR, "about_you_kaleido.mp4")
PANEL_H        = 72

os.makedirs(OUT_DIR, exist_ok=True)
pygame.init()

# Video length follows the song instead of a hard-coded 50 s
try:
    pygame.mixer.init()
    TOTAL_SECONDS = int(math.ceil(pygame.mixer.Sound(AUDIO_PATH).get_length())) + OUTRO_EXTRA
except Exception as exc:
    print(f"Could not read audio length ({exc}); using {FALLBACK_SECONDS}s")
    TOTAL_SECONDS = FALLBACK_SECONDS
TOTAL_FRAMES = FPS * TOTAL_SECONDS

screen  = pygame.display.set_mode((WIDTH, HEIGHT + PANEL_H))
pygame.display.set_caption("About You - 8-Bit Renderer  |  ESC to cancel")
surface = pygame.Surface((WIDTH, HEIGHT))
clock   = pygame.time.Clock()          # ← real-time throttle

GUI_FONT  = pygame.font.SysFont("Courier New", 13, bold=True)
GUI_SMALL = pygame.font.SysFont("Courier New", 11)

# ═══════════════════════════════════════════════════════════════
#  8-BIT COLOR PALETTES
# ═══════════════════════════════════════════════════════════════
PALETTES = [
    {"bg": (4,  4,  16),  "accent": (80,  180, 255), "text": (255, 255, 200), "deco": (255, 100, 150)},
    {"bg": (10, 4,  20),  "accent": (190, 90,  255), "text": (200, 255, 210), "deco": (255, 210, 50) },
    {"bg": (3,  12, 8),   "accent": (40,  240, 140), "text": (255, 210, 100), "deco": (90,  200, 255)},
    {"bg": (16, 4,  4),   "accent": (255, 90,  50),  "text": (255, 255, 255), "deco": (255, 200, 90) },
    {"bg": (6,  10, 20),  "accent": (100, 220, 255), "text": (230, 200, 255), "deco": (255, 130, 80) },
]

# ═══════════════════════════════════════════════════════════════
#  LYRICS
# ═══════════════════════════════════════════════════════════════
RAW_LYRICS = [
    ("And there was something about you that now I can't remember", 0.0,  4.4),
    ("It's the same damn thing that made my heart surrender",        4.4,  9.6),
    ("And I'll miss you on a train, I'll miss you in the mornin'",  9.6,  15.1),
    ("I never know what to think about",                            15.1, 18.3),
    ("I think about you",                                           18.3, 23.9),
    ("About you",                                                   23.9, 29.0),
    ("Do you think I have forgotten",                               29.0, 34.1),
    ("About you?",                                                  34.1, 37.1),
]
LYRICS      = [{"text": t, "start": s * FPS, "end": e * FPS} for t, s, e in RAW_LYRICS]
OUTRO_START = int(37.1 * FPS)
TITLE_END   = 2 * FPS

# ═══════════════════════════════════════════════════════════════
#  PIXEL FONTS
# ═══════════════════════════════════════════════════════════════
FONT_LARGE = pygame.font.Font(FONT_PATH, 18)
FONT_SMALL = pygame.font.Font(FONT_PATH, 10)
FONT_TINY  = pygame.font.Font(FONT_PATH, 7)

# ═══════════════════════════════════════════════════════════════
#  PRE-COMPUTED OVERLAY SURFACES
# ═══════════════════════════════════════════════════════════════
random.seed(42)

SCANLINES = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
for _y in range(0, HEIGHT, 4):
    pygame.draw.line(SCANLINES, (0, 0, 0, 65), (0, _y), (WIDTH, _y))

VIGNETTE = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
for _i in range(90):
    _a = int(210 * (1 - _i / 90) ** 1.8)
    pygame.draw.rect(VIGNETTE, (0, 0, 0, _a), (0, _i,              WIDTH, 1))
    pygame.draw.rect(VIGNETTE, (0, 0, 0, _a), (0, HEIGHT - 1 - _i, WIDTH, 1))
for _i in range(55):
    _a = int(130 * (1 - _i / 55) ** 2)
    pygame.draw.rect(VIGNETTE, (0, 0, 0, _a), (_i,             0, 1, HEIGHT))
    pygame.draw.rect(VIGNETTE, (0, 0, 0, _a), (WIDTH - 1 - _i, 0, 1, HEIGHT))


# ═══════════════════════════════════════════════════════════════
#  AUDIO ANALYSIS  — per-frame loudness, bass and beat pulses
# ═══════════════════════════════════════════════════════════════
def analyse_audio():
    """Returns (level, bass, beat, hits, ok), one value per video frame.
      level, bass : 0..1, smoothed loudness / low-frequency energy
      beat        : 0..1, jumps to ~1 on each detected beat then decays
      hits        : bool, True on the frame of a strong beat (drives the glitch effect)
    If the audio can't be decoded, everything is zero and ok is False."""
    zeros = np.zeros(TOTAL_FRAMES)
    try:
        sr  = pygame.mixer.get_init()[0]
        arr = pygame.sndarray.array(pygame.mixer.Sound(AUDIO_PATH)).astype(np.float32) / 32768.0
        mono = arr.mean(axis=1) if arr.ndim == 2 else arr
    except Exception as exc:
        print(f"Audio analysis unavailable ({exc}); using time-based animation only")
        return zeros, zeros, zeros, np.zeros(TOTAL_FRAMES, bool), False

    WIN     = 2048
    window  = np.hanning(WIN)
    freqs   = np.fft.rfftfreq(WIN, 1 / sr)
    bass_bins = (freqs >= 30) & (freqs <= 150)
    flux_bins = freqs <= 4000

    rms, bass, flux = np.zeros(TOTAL_FRAMES), np.zeros(TOTAL_FRAMES), np.zeros(TOTAL_FRAMES)
    prev = np.zeros(flux_bins.sum())
    for f in range(TOTAL_FRAMES):
        centre = int(f / FPS * sr)
        seg = mono[max(0, centre - WIN // 2): centre + WIN // 2]
        if len(seg) < WIN:                                    # before start / past the end
            seg = np.pad(seg, (0, WIN - len(seg)))
        mag = np.abs(np.fft.rfft(seg * window))
        rms[f]  = math.sqrt(float(np.mean(seg ** 2)))
        bass[f] = float(mag[bass_bins].sum())
        cur = np.log1p(mag[flux_bins] * 10)
        flux[f] = float(np.maximum(cur - prev, 0).sum())      # spectral flux = "something new happened"
        prev = cur

    def norm_smooth(x, a):
        x = np.clip(x / max(np.percentile(x, 95), 1e-9), 0, 1)
        out = np.zeros_like(x)
        for i in range(len(x)):
            out[i] = x[i] if i == 0 else max(x[i], out[i - 1] * a)   # instant attack, slow release
        return out

    level, bass = norm_smooth(rms, 0.90), norm_smooth(bass, 0.85)

    # Beat picking: flux peaks that rise above their local (~1 s) average, at most ~4 per second
    beat, hits = np.zeros(TOTAL_FRAMES), np.zeros(TOTAL_FRAMES, bool)
    last_beat, last_hit, count = -99, -99, 0
    for f in range(TOTAL_FRAMES):
        lo, hi = max(0, f - FPS // 2), min(TOTAL_FRAMES, f + FPS // 2 + 1)
        local = flux[lo:hi]
        peak  = flux[f] >= local.max() and flux[f] > 1.35 * local.mean() + 1e-6
        if peak and f - last_beat >= 7 and rms[f] > 0.01:
            strength = float(np.clip(flux[f] / (2.2 * local.mean() + 1e-9), 0.55, 1.0))
            beat[f] = strength
            last_beat, count = f, count + 1
            if strength > 0.85 and f - last_hit >= FPS:       # glitch at most once a second
                hits[f], last_hit = True, f
        elif f:
            beat[f] = beat[f - 1] * 0.84                      # decay between beats
    print(f"Audio analysis: {count} beats (~{count / (len(mono) / sr) * 60:.0f}/min), "
          f"{int(hits.sum())} glitch hits")
    return level, bass, beat, hits, True


# ═══════════════════════════════════════════════════════════════
#  PALETTE BLENDING  — colours glide between lyric lines
# ═══════════════════════════════════════════════════════════════
BLEND_FRAMES = int(0.75 * FPS)

def lerp_color(a, b, k):
    return tuple(int(round(x + (y - x) * k)) for x, y in zip(a, b))

def blended_palette(frame, scene_idx):
    """Palette for this frame: eases from the previous scene's palette to the current one
    during the first BLEND_FRAMES of each new lyric line."""
    cur = PALETTES[scene_idx % len(PALETTES)]
    if scene_idx == 0:
        return cur
    prev = PALETTES[(scene_idx - 1) % len(PALETTES)]
    k = (frame - LYRICS[scene_idx]["start"]) / BLEND_FRAMES
    if k >= 1:
        return cur
    k = max(0.0, k)
    k = k * k * (3 - 2 * k)                                   # smoothstep ease in/out
    return {key: lerp_color(prev[key], cur[key], k) for key in cur}


# ═══════════════════════════════════════════════════════════════
#  KALEIDOSCOPE  — 8-fold symmetric animated mandala
# ═══════════════════════════════════════════════════════════════
def draw_kaleidoscope(surf, pal, t, sc, pulse):
    """t = animation clock (speeds up with the music), sc = radius scale (breathes with the
    bass), pulse = 0..1 beat strength (thickens lines / grows dots and diamonds)."""
    cx, cy = WIDTH // 2, HEIGHT // 2
    N  = 8
    lw = 2 + int(round(2 * pulse))      # thick line width

    ca = pal["accent"]
    cd = pal["deco"]
    c  = [
        ca,
        cd,
        tuple(max(0, v - 80) for v in ca),
        tuple(max(0, v - 80) for v in cd),
    ]

    for seg in range(N):
        theta = seg * (2 * math.pi / N)
        spin  = t * (0.38 if seg % 2 == 0 else -0.38)

        # Layer 1 — animated spokes
        for k in range(6):
            r0  = (22 + k * 30) * sc
            r1  = r0 + (24 + 9 * math.sin(t * 1.4 + k * 0.85 + seg * 0.6)) * sc
            ang = theta + spin + k * 0.065 * math.sin(t * 0.75 + seg)
            pygame.draw.line(surf, c[k % 4],
                (cx + int(r0 * math.cos(ang)), cy + int(r0 * math.sin(ang))),
                (cx + int(r1 * math.cos(ang)), cy + int(r1 * math.sin(ang))), lw)

        # Layer 2 — orbiting dots
        for k in range(5):
            r   = (40 + k * 40 + 13 * math.sin(t * 0.85 + k * 1.25)) * sc
            ang = theta + t * (0.5 + k * 0.08) * (-1 if seg % 2 else 1)
            rad = max(2, int((4 + 3 * abs(math.sin(t * 2.2 + k * 1.75 + seg))) * (1 + 0.8 * pulse)))
            pygame.draw.circle(surf, c[(k + 1) % 4],
                (cx + int(r * math.cos(ang)), cy + int(r * math.sin(ang))), rad)

        # Layer 3 — rotating diamonds
        for k in range(3):
            r   = (62 + k * 56) * sc
            ang = theta + math.pi / N + t * (-0.27 - k * 0.04) * (1 if seg % 2 else -1)
            px  = cx + int(r * math.cos(ang))
            py  = cy + int(r * math.sin(ang))
            sz  = max(3, int((8 + 5 * math.sin(t * 1.65 + k * 2.1)) * (1 + 0.5 * pulse)))
            pygame.draw.polygon(surf, c[(k + 2) % 4],
                [(px, py - sz), (px + sz, py), (px, py + sz), (px - sz, py)], 1)

        # Layer 4 — cross-segment connectors
        for k in range(3):
            r  = (82 + k * 52) * sc
            a1 = theta + t * 0.31 + k * 0.22
            a2 = theta + math.pi / N - t * 0.17 + k * 0.16
            pygame.draw.line(surf, c[(k + seg) % 4],
                (cx + int(r * math.cos(a1)), cy + int(r * math.sin(a1))),
                (cx + int(r * math.cos(a2)), cy + int(r * math.sin(a2))), 1)

        # Layer 5 — outer petal dots
        for k in range(2):
            r   = (160 + k * 40 + 18 * math.sin(t * 0.6 + k + seg)) * sc
            ang = theta + t * 0.2 * (1 if k == 0 else -1) + seg * 0.1
            px  = cx + int(r * math.cos(ang))
            py  = cy + int(r * math.sin(ang))
            pygame.draw.circle(surf, c[k % 4], (px, py),
                               max(2, int(3 + 2 * math.sin(t + k))))

    # Central mandala
    for k in range(16):
        ang = k * (2 * math.pi / 16) + t * 0.52
        r1  = (5  + 4  * math.sin(t * 3.0  + k)) * sc
        r2  = (22 + 11 * math.sin(t * 1.75 + k * 0.75)) * (sc + 0.5 * pulse)
        pygame.draw.line(surf, c[k % 4],
            (cx + int(r1 * math.cos(ang)), cy + int(r1 * math.sin(ang))),
            (cx + int(r2 * math.cos(ang)), cy + int(r2 * math.sin(ang))), lw)


# ═══════════════════════════════════════════════════════════════
#  LYRIC TEXT RENDERER
# ═══════════════════════════════════════════════════════════════
def draw_lyrics(surf, text, frame, start_frame, end_frame, text_color, accent):
    total   = end_frame - start_frame
    elapsed = frame - start_frame
    fade_f  = FPS // 2

    if elapsed < fade_f:
        alpha = int(255 * elapsed / fade_f)
    elif elapsed > total - fade_f:
        alpha = int(255 * (total - elapsed) / fade_f)
    else:
        alpha = 255

    reveal_f = min(int(FPS * 1.5), total // 2)
    display  = text[:max(1, int(len(text) * elapsed / reveal_f))] if elapsed < reveal_f else text

    words, lines, line = display.split(), [], ""
    for word in words:
        test = (line + " " + word).strip()
        if FONT_LARGE.size(test)[0] > WIDTH - 120:
            lines.append(line); line = word
        else:
            line = test
    if line:
        lines.append(line)

    box_h = len(lines) * 38 + 24
    box_y = HEIGHT // 2 - box_h // 2 + 10
    box   = pygame.Surface((WIDTH - 80, box_h), pygame.SRCALPHA)
    box.fill((0, 0, 0, int(145 * alpha / 255)))
    surf.blit(box, (40, box_y))

    start_y = box_y + 12
    for i, ln in enumerate(lines):
        shadow = FONT_LARGE.render(ln, False, (0, 0, 0))
        shadow.set_alpha(alpha)
        surf.blit(shadow, shadow.get_rect(center=(WIDTH // 2 + 3, start_y + i * 38 + 3)))
        txt = FONT_LARGE.render(ln, False, text_color)
        txt.set_alpha(alpha)
        surf.blit(txt, txt.get_rect(center=(WIDTH // 2, start_y + i * 38)))

    if elapsed < reveal_f + 10 and (frame // 8) % 2 == 0:
        cur = FONT_LARGE.render("_", False, accent)
        cur.set_alpha(alpha)
        lw  = FONT_LARGE.size(lines[-1] if lines else "")[0]
        surf.blit(cur, (WIDTH // 2 + lw // 2 + 4, start_y + (len(lines) - 1) * 38))


# ═══════════════════════════════════════════════════════════════
#  TITLE CARD
# ═══════════════════════════════════════════════════════════════
def draw_title_card(surf, frame, pal):
    # fade in 0-32, hold to 50, fade out to TITLE_END; always clamped to 0-255
    if frame < 32:
        a = frame * 8
    else:
        a = 255 - max(0, frame - 50) * 12
    a = max(0, min(255, a))
    # Sits near the top so the first lyric (starts at 0.0 s) stays visible
    for txt, y in [
        (FONT_LARGE.render("ABOUT YOU",    False, pal["text"]),   50),
        (FONT_SMALL.render("The 1975",     False, pal["accent"]),  78),
        (FONT_TINY.render("8-BIT EDITION", False, pal["deco"]),    98),
    ]:
        txt.set_alpha(a)
        surf.blit(txt, txt.get_rect(center=(WIDTH // 2, y)))


# ═══════════════════════════════════════════════════════════════
#  OUTRO CARD
# ═══════════════════════════════════════════════════════════════
def draw_outro(surf, frame, pal):
    a = max(0, min(255, int((frame - OUTRO_START) * 5)))
    box = pygame.Surface((WIDTH - 80, 70), pygame.SRCALPHA)
    box.fill((0, 0, 0, int(130 * a / 255)))
    surf.blit(box, (40, HEIGHT // 2 - 35))
    for txt, y in [
        (FONT_SMALL.render("Thanks for listening", False, pal["accent"]),                    HEIGHT // 2 - 18),
        (FONT_TINY.render("ABOUT YOU  .  THE 1975  .  8-BIT EDITION", False, pal["deco"]),  HEIGHT // 2 + 16),
    ]:
        txt.set_alpha(a)
        surf.blit(txt, txt.get_rect(center=(WIDTH // 2, y)))


# ═══════════════════════════════════════════════════════════════
#  IN-VIDEO PROGRESS BAR
# ═══════════════════════════════════════════════════════════════
def draw_progress(surf, frame, color):
    bw = int(WIDTH * frame / TOTAL_FRAMES)
    pygame.draw.rect(surf, tuple(max(0, c // 5) for c in color), (0, HEIGHT - 5, WIDTH, 5))
    pygame.draw.rect(surf, (255, 255, 255), (0, HEIGHT - 5, bw, 5))


# ═══════════════════════════════════════════════════════════════
#  GLITCH EFFECT
# ═══════════════════════════════════════════════════════════════
def draw_glitch(surf, trigger, accent):
    if trigger:
        for _ in range(3):
            pygame.draw.rect(surf, accent,
                (random.randint(0, WIDTH - 60), random.randint(0, HEIGHT - 6),
                 random.randint(20, 80), 3))


# ═══════════════════════════════════════════════════════════════
#  GUI PANEL  (below the preview)
# ═══════════════════════════════════════════════════════════════
PANEL_Y  = HEIGHT
PANEL_BG = (5, 5, 15)

def draw_panel(win, frame, fps_r, elapsed_wall):
    pygame.draw.rect(win, PANEL_BG, (0, PANEL_Y, WIDTH, PANEL_H))
    pygame.draw.line(win, (25, 25, 55), (0, PANEL_Y), (WIDTH, PANEL_Y), 1)

    pct   = frame / TOTAL_FRAMES
    bar_w = int((WIDTH - 40) * pct)
    pygame.draw.rect(win, (16, 16, 36),    (20, PANEL_Y + 10, WIDTH - 40, 8), border_radius=4)
    if bar_w > 0:
        pygame.draw.rect(win, (70, 170, 255), (20, PANEL_Y + 10, bar_w,      8), border_radius=4)

    eta = (TOTAL_FRAMES - frame) / fps_r if fps_r > 0.1 else 0

    infos = [
        ("ABOUT YOU - 8-BIT RENDERER",                  20,  PANEL_Y + 28, (70, 130, 210), GUI_FONT ),
        (f"{pct * 100:5.1f}%",                          20,  PANEL_Y + 50, (70, 170, 255), GUI_FONT ),
        (f"frame {frame:04d} / {TOTAL_FRAMES}",        105,  PANEL_Y + 50, (130,130, 185), GUI_FONT ),
        (f"{frame // FPS:02d}s / {TOTAL_SECONDS}s",   395,  PANEL_Y + 50, (130,130, 185), GUI_FONT ),
        (f"preview: {fps_r:.1f} fps   ETA {eta:.0f}s",500,  PANEL_Y + 50, (90, 90,  155), GUI_FONT ),
        ("ESC = cancel",                               748,  PANEL_Y + 50, (45, 45,  80),  GUI_SMALL),
    ]
    for txt, x, y, col, font in infos:
        win.blit(font.render(txt, True, col), (x, y))


# ═══════════════════════════════════════════════════════════════
#  MAIN RENDER LOOP
# ═══════════════════════════════════════════════════════════════
fourcc       = cv2.VideoWriter_fourcc(*"mp4v")
writer       = cv2.VideoWriter(SILENT_PATH, fourcc, FPS, OUT_SIZE)
render_start = time.time()
fps_render   = float(FPS)

print(f"Rendering {TOTAL_FRAMES} frames at {FPS} fps")
print(("Preview plays in real time" if REALTIME else "Rendering as fast as possible")
      + f" — {TOTAL_SECONDS}s of video")
print(f"Output: {OUTPUT_PATH}\n")

# Music analysis -> animation clock. Speed = base + loudness + beat kick, accumulated so it never jumps.
LEVEL, BASS, BEAT, HITS, AUDIO_OK = analyse_audio()
ANIM_T = np.cumsum(0.028 * (1 + 1.5 * LEVEL + 1.2 * BEAT))

for frame in range(TOTAL_FRAMES):

    # ── Clock tick — locks preview to real time (optional) ──
    if REALTIME:
        clock.tick(FPS)

    # ── Window events ────────────────────────────
    for event in pygame.event.get():
        if event.type == pygame.QUIT or (
            event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
            writer.release()
            pygame.quit()
            print("\nCancelled by user.")
            sys.exit()

    # ── Determine scene & active lyric ──────────
    scene_idx, current_lyric = 0, None
    for i, lyric in enumerate(LYRICS):
        if lyric["start"] <= frame < lyric["end"]:
            current_lyric = lyric; scene_idx = i; break
        elif frame >= lyric["start"]:
            scene_idx = i

    pal = blended_palette(frame, scene_idx)

    # ── Draw to off-screen surface ───────────────
    beat  = float(BEAT[frame])
    pulse = max(beat, 0.6 * float(BASS[frame]))
    surface.fill(tuple(min(255, v + int(14 * beat)) for v in pal["bg"]))     # background flashes on the beat
    draw_kaleidoscope(surface, pal, float(ANIM_T[frame]), 1 + 0.09 * float(BASS[frame]) + 0.08 * beat, pulse)

    if current_lyric:
        draw_lyrics(surface, current_lyric["text"], frame,
                    int(current_lyric["start"]), int(current_lyric["end"]),
                    pal["text"], pal["accent"])
    elif frame >= OUTRO_START:
        draw_outro(surface, frame, pal)
    if frame < TITLE_END:
        draw_title_card(surface, frame, pal)

    draw_glitch(surface, bool(HITS[frame]) if AUDIO_OK else frame % 90 == 0, pal["accent"])
    surface.blit(SCANLINES, (0, 0))
    surface.blit(VIGNETTE,  (0, 0))
    draw_progress(surface, frame, pal["deco"])

    hud = FONT_TINY.render("ABOUT YOU - THE 1975", False, pal["deco"])
    surface.blit(hud, (10, 10))

    # ── Write frame to video file ─────────────────
    arr = pygame.surfarray.array3d(surface)
    arr = np.transpose(arr, (1, 0, 2))
    bgr = cv2.cvtColor(arr, cv2.COLOR_RGB2BGR)
    if OUT_SCALE != 1:   # nearest-neighbour keeps the hard 8-bit pixel edges
        bgr = cv2.resize(bgr, OUT_SIZE, interpolation=cv2.INTER_NEAREST)
    writer.write(bgr)

    # ── Update live preview window ────────────────
    screen.blit(surface, (0, 0))
    elapsed = time.time() - render_start
    fps_render = (frame + 1) / max(0.001, elapsed)
    draw_panel(screen, frame, fps_render, elapsed)
    pygame.display.flip()

    if frame % (FPS * 5) == 0:
        print(f"  {frame // FPS:02d}s / {TOTAL_SECONDS}s  —  {fps_render:.1f} fps")

# ── Done ──────────────────────────────────────────
writer.release()
pygame.quit()
total = time.time() - render_start
print(f"\nRendered in {total:.1f}s")

# ── Re-encode to H.264 and mux the song in ────────
FFMPEG = shutil.which("ffmpeg")
if not FFMPEG:
    try:
        import imageio_ffmpeg                      # bundled binary, if installed
        FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        pass

if FFMPEG and os.path.exists(AUDIO_PATH):
    result = subprocess.run(
        [FFMPEG, "-y", "-i", SILENT_PATH, "-i", AUDIO_PATH,
         "-af", "apad",                            # pad audio with silence through the extended outro
         "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18",
         "-c:a", "aac", "-b:a", "192k", "-shortest", OUTPUT_PATH],
        capture_output=True, text=True)
    if result.returncode == 0:
        os.remove(SILENT_PATH)
        print(f"Final video with audio -> {OUTPUT_PATH}")
    else:
        print("ffmpeg failed; silent video kept at", SILENT_PATH)
        print(result.stderr[-500:])
else:
    print(f"ffmpeg or audio not found; silent video at {SILENT_PATH}")
    print(f'Add audio: ffmpeg -i "{SILENT_PATH}" -i "{AUDIO_PATH}" -af apad -c:v libx264 -pix_fmt yuv420p -shortest "{OUTPUT_PATH}"')