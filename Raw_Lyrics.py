import pygame
import sys
import time

# ═══════════════════════════════════════════════
#  LYRICS — edit these lines freely
# ═══════════════════════════════════════════════
LYRICS = [
    "And there was something about you that now I can't remember",
    "It's the same damn thing that made my heart surrender",
    "And I'll miss you on a train, I'll miss you in the mornin'",
    "I never know what to think about",
    "I think about you",
    "About you",
    "Do you think I have forgotten",
    "About you?",
]

# ═══════════════════════════════════════════════
#  SETUP
# ═══════════════════════════════════════════════
WIDTH, HEIGHT = 900, 520
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("🎮 Lyric Timer — About You | The 1975")

FONT_TITLE  = pygame.font.SysFont("Courier New", 13, bold=True)
FONT_DONE   = pygame.font.SysFont("Courier New", 14)
FONT_ACTIVE = pygame.font.SysFont("Courier New", 20, bold=True)
FONT_NEXT   = pygame.font.SysFont("Courier New", 14)
FONT_TIMER  = pygame.font.SysFont("Courier New", 36, bold=True)
FONT_HINT   = pygame.font.SysFont("Courier New", 12)
FONT_OUT    = pygame.font.SysFont("Courier New", 13)

# Colors
BG         = (10,  10,  26)
DONE_COL   = (74,  222, 128)   # green
ACTIVE_COL = (250, 204, 21)    # yellow
NEXT_COL   = (80,  80,  110)   # muted
TIMER_COL  = (167, 139, 250)   # purple
ACCENT_COL = (100, 180, 255)   # blue
GRAY       = (60,  60,  80)
WHITE      = (220, 220, 220)
BAR_BG     = (30,  30,  50)


# ═══════════════════════════════════════════════
#  STATE
# ═══════════════════════════════════════════════
timestamps = []     # list of floats: one per SPACE press
start_time = None   # set on first SPACE
state      = "waiting"   # waiting | running | done


def format_time(secs):
    m = int(secs) // 60
    s = secs % 60
    return f"{m:02d}:{s:05.2f}"


def wrap_text(text, font, max_w):
    """Word-wrap text into lines that fit max_w pixels."""
    words  = text.split()
    lines  = []
    line   = ""
    for word in words:
        test = (line + " " + word).strip()
        if font.size(test)[0] <= max_w:
            line = test
        else:
            if line:
                lines.append(line)
            line = word
    if line:
        lines.append(line)
    return lines


def draw_text(surf, text, font, color, x, y, center=False):
    img = font.render(text, True, color)
    r   = img.get_rect(center=(x, y)) if center else img.get_rect(topleft=(x, y))
    surf.blit(img, r)
    return r.height


def draw_screen(elapsed):
    screen.fill(BG)
    current_idx = len(timestamps)

    # ── Header ──────────────────────────────────
    draw_text(screen, "LYRIC TIMING HELPER", FONT_TITLE, ACCENT_COL, 40, 20)
    draw_text(screen, "ABOUT YOU · THE 1975", FONT_TITLE, GRAY, 40, 38)

    # ── Big timer ───────────────────────────────
    timer_str = format_time(elapsed) if start_time else "00:00.00"
    draw_text(screen, timer_str, FONT_TIMER, TIMER_COL, WIDTH - 230, 20)

    # ── Progress bar ────────────────────────────
    total  = len(LYRICS)
    prog_w = int((WIDTH - 80) * current_idx / total)
    pygame.draw.rect(screen, BAR_BG,     (40, 70, WIDTH - 80, 6), border_radius=3)
    pygame.draw.rect(screen, DONE_COL,   (40, 70, prog_w, 6),     border_radius=3)
    draw_text(screen, f"{current_idx}/{total} lines stamped", FONT_HINT, GRAY, 40, 80)

    # ── Divider ─────────────────────────────────
    pygame.draw.line(screen, GRAY, (40, 100), (WIDTH - 40, 100), 1)

    # ── Done lines ──────────────────────────────
    y = 115
    visible_done = timestamps[-4:] if len(timestamps) > 4 else timestamps
    start_vis    = max(0, len(timestamps) - 4)

    for i, ts in enumerate(visible_done):
        idx  = start_vis + i
        line = LYRICS[idx]
        # shorten if needed
        short = (line[:46] + "…") if len(line) > 46 else line
        s_str = format_time(timestamps[idx - 1]) if idx > 0 else "00:00.00"
        e_str = format_time(ts)
        draw_text(screen, f"✓  {short}", FONT_DONE, DONE_COL, 50, y)
        draw_text(screen, f"{s_str} → {e_str}", FONT_DONE, DONE_COL, WIDTH - 240, y)
        y += 26

    # ── Separator before active ──────────────────
    if timestamps:
        pygame.draw.line(screen, GRAY, (40, y + 5), (WIDTH - 40, y + 5), 1)
        y += 18

    # ── Active line ─────────────────────────────
    if state == "running" and current_idx < len(LYRICS):
        active = LYRICS[current_idx]
        pygame.draw.rect(screen, (40, 35, 10), (40, y - 4, WIDTH - 80, 34), border_radius=4)
        pygame.draw.rect(screen, ACTIVE_COL,   (40, y - 4, 4,           34))
        lines = wrap_text(active, FONT_ACTIVE, WIDTH - 120)
        for ln in lines:
            draw_text(screen, ln, FONT_ACTIVE, ACTIVE_COL, 55, y)
            y += 26

        # Next preview
        if current_idx + 1 < len(LYRICS):
            y += 10
            draw_text(screen, "next ›", FONT_HINT, GRAY, 55, y)
            draw_text(screen, LYRICS[current_idx + 1], FONT_NEXT, NEXT_COL, 110, y)

    elif state == "waiting":
        draw_text(screen, "▶  Press SPACE to start the timer & stamp line 1",
                  FONT_ACTIVE, ACTIVE_COL, 50, y)

    elif state == "done":
        draw_text(screen, "✅  All lines stamped! Check your terminal for RAW_LYRICS.",
                  FONT_ACTIVE, DONE_COL, 50, y)

    # ── Spacebar hint ───────────────────────────
    hint_y = HEIGHT - 70
    pygame.draw.line(screen, GRAY, (40, hint_y - 10), (WIDTH - 40, hint_y - 10), 1)

    pygame.draw.rect(screen, (30, 30, 50), (40, hint_y, 160, 32), border_radius=6)
    pygame.draw.rect(screen, GRAY,         (40, hint_y, 160, 32), 1, border_radius=6)
    draw_text(screen, "SPACE", FONT_ACTIVE, WHITE, 120, hint_y + 8, center=True)

    if state == "waiting":
        hint_msg = "→  start timer + stamp line 1"
    elif state == "running" and current_idx < len(LYRICS):
        hint_msg = f"→  end '{LYRICS[current_idx][:30]}…' & move to next"
    else:
        hint_msg = "→  all done!"
    draw_text(screen, hint_msg, FONT_HINT, GRAY, 215, hint_y + 10)

    # ── Undo hint ───────────────────────────────
    draw_text(screen, "U = undo last stamp    ESC = quit & print results",
              FONT_HINT, GRAY, 40, HEIGHT - 30)

    pygame.display.flip()


def generate_output():
    """Build the RAW_LYRICS list string from recorded timestamps."""
    lines = ["", "RAW_LYRICS = ["]
    for i, lyric in enumerate(LYRICS):
        safe = lyric.replace('"', '\\"')
        s = round(timestamps[i],     1) if i     < len(timestamps) else 0.0
        e = round(timestamps[i + 1], 1) if i + 1 < len(timestamps) else round(timestamps[-1] + 3.0, 1)
        lines.append(f'    ("{safe}", {s:.1f}, {e:.1f}),')
    lines.append("]")
    lines.append("")
    return "\n".join(lines)


# ═══════════════════════════════════════════════
#  MAIN LOOP
# ═══════════════════════════════════════════════
clock = pygame.time.Clock()

while True:
    elapsed = (time.time() - start_time) if start_time else 0.0
    current_idx = len(timestamps)

    for event in pygame.event.get():

        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

        if event.type == pygame.KEYDOWN:

            # ── SPACE: stamp ─────────────────────
            if event.key == pygame.K_SPACE:

                if state == "waiting":
                    start_time = time.time()
                    timestamps.append(0.0)   # line 0 starts at 0
                    state = "running"

                elif state == "running":
                    now = time.time() - start_time
                    timestamps.append(round(now, 2))
                    # After stamping end of last line → done
                    if len(timestamps) > len(LYRICS):
                        state = "done"
                        print(generate_output())

            # ── U: undo last stamp ───────────────
            elif event.key == pygame.K_u:
                if state == "done":
                    state = "running"
                if len(timestamps) > 1:
                    timestamps.pop()
                elif len(timestamps) == 1:
                    timestamps.pop()
                    start_time = None
                    state = "waiting"

            # ── ESC: quit & print ────────────────
            elif event.key == pygame.K_ESCAPE:
                if timestamps:
                    print(generate_output())
                pygame.quit()
                sys.exit()

    draw_screen(elapsed)
    clock.tick(30)