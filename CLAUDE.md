# About You (8-Bit Edition): project notes

Python generative-art project: a 50-second, 854x480, 30 fps retro/8-bit lyric video for
"About You" by The 1975. Frames are drawn with pygame and written to an MP4 with OpenCV.
The MP4 has no audio; audio is added afterwards with ffmpeg.

These notes started from reading the code. `main2.py` has since been fixed and run
successfully (see "Changes to main2.py"). `main.py` and `Raw_Lyrics.py` have not been run or
changed, so their "Known issues" are from reading, not from testing.

## Files

| File | Role |
|---|---|
| `about_you.MP3` | The song (~0.9 MB). Not read by any script. It is only used in the manual ffmpeg step. |
| `Raw_Lyrics.py` | **Lyric timing tool** (interactive). Play the song yourself, press SPACE at each line change. It prints a `RAW_LYRICS = [...]` block to paste into the renderers. |
| `main.py` | **Renderer v1**: starfield + perspective grid + floating pixel-art sprites. Headless (no window), renders as fast as possible. |
| `main2.py` | **Renderer v2** (the newer one): 8-fold animated kaleidoscope + vignette + outro card. Shows a live preview window with a progress panel. By default locked to real time (`REALTIME = True`), so a render takes as long as the video. ESC cancels. Adds the audio itself at the end. |
| `PressStart2P-Regular.ttf` | Pixel font used by both renderers (sizes 18 / 10 / 7). |
| `output/` | Created at runtime. `main2.py` writes `output/about_you_kaleido.mp4`. `main.py` still writes `output/about_you_8bit.mp4` with no audio and has to be muxed by hand. |

## Dependencies

`numpy`, `opencv-python` (`cv2`), and `pygame`. An `ffmpeg` is needed for the audio step.
There is no requirements file.

**Environment (this machine):** Python 3.14.0. The `pygame` package has no build for 3.14, so
`pip install pygame` fails. `pygame-ce` is installed instead. It is a drop-in replacement,
so `import pygame` still works. Also installed: `numpy` 2.4.1, `opencv-python` 4.13.0 and
`imageio-ffmpeg`, which bundles an `ffmpeg` binary. There is no system `ffmpeg` on PATH.

```
pip install pygame-ce numpy opencv-python imageio-ffmpeg
```

`main2.py` finds its font, audio and `output/` folder relative to the script, so it can be
run from any folder. `main.py` and `Raw_Lyrics.py` still use relative paths and need to be
run from inside this folder.

```
python "S:\About You\Raw_Lyrics.py"   # 1. get timestamps
python "S:\About You\main2.py"        # 2. render video, add audio, done
```

`main2.py` looks for `ffmpeg` on PATH, then falls back to the `imageio-ffmpeg` binary. If neither works it keeps the silent video and prints the manual command.

## Workflow / data flow

1. `Raw_Lyrics.py` holds the lyric lines. SPACE starts a wall-clock timer and stamps line 1 at 0.0. Each later SPACE ends the current line. U undoes a stamp. ESC quits and prints the results. The output is `("text", start_s, end_s),` tuples.
2. Paste that block over `RAW_LYRICS` in `main.py` / `main2.py`. Each renderer converts seconds to frames: `{"text", "start", "end"}` with `start = s * FPS`.
3. The render loop runs once per frame: find the active lyric (its index is the "scene" and picks the palette `PALETTES[scene_idx % 5]`), draw the background, draw the text, apply effects, and write the frame.

Current lyrics: 8 lines, 0.0 s to 37.1 s ("And there was something about you..." to "About you?").
The song itself is about 39 s long.

## Render pipeline (per frame, both renderers)

```
surface.fill(bg) -> background art -> title card (frame < 2s) | lyric | outro (main2 only)
  -> glitch -> scanlines (-> vignette in main2) -> progress bar -> HUD text
  -> pygame.surfarray.array3d -> transpose(1,0,2) -> RGB2BGR -> VideoWriter.write
```

OpenCV writes with the `mp4v` codec. The transpose is needed because pygame arrays are (x, y, c) and OpenCV wants (y, x, c).
In `main2.py` that file is only an intermediate: ffmpeg re-encodes it to H.264 and adds the song.

### main.py specifics
- `PALETTES`: 5 dicts with `bg / accent / text / deco`. Scene i uses palette `i % 5`.
- `STARS`: 120 twinkling stars, seeded with `random.seed(42)`.
- `draw_grid`: scrolling perspective floor under the horizon.
- Sprites are 2D 0/1 lists (`CAMERA`, `FOOTBALL`, `F1`, `CIRCUIT`, `HEART`, `STAR`), drawn at 4x scale by `draw_pixelart`. `SPRITE_MAP` maps names to bitmaps.
  The sprite themes (camera, football, F1, circuit) are personal motifs.
- `SCENE_ELEMENTS[scene_idx]` gives `(sprite_name, x, y)` positions, with a sine float animation and a label under each sprite.
- `draw_lyrics`: 0.5 s fade in/out, typewriter reveal over the first 1.5 s, blinking `_` cursor, word wrap at `WIDTH - 80`, drop shadow.

### main2.py specifics
- `draw_kaleidoscope`: N=8 segments. Each segment has 5 layers: spokes, orbiting dots, rotating diamond outlines, cross-segment connector lines, outer petal dots. There is also a 16-spoke central mandala. Everything is driven by `t = frame * 0.028` and colours come from `accent`, `deco` and darker copies. Odd and even segments spin in opposite directions.
- `SCANLINES` and `VIGNETTE` are `SRCALPHA` surfaces built once and blitted per frame.
- `draw_lyrics` adds a translucent black box behind the text (wrap width `WIDTH - 120`).
- `draw_outro`: "Thanks for listening" card that fades in from `OUTRO_START = 37.1 s` and stays until the end of the video.
- The preview window is `HEIGHT + PANEL_H` tall. The extra strip shows percent, frame count, ETA and preview fps. The panel is only on screen and is not in the video.

## Changes to main2.py

Settings are at the top of the file:

| Setting | Meaning |
|---|---|
| `OUTRO_EXTRA = 6` | Seconds of outro held after the song ends. Total video length = ceil(audio length) + `OUTRO_EXTRA`, so currently 39 + 6 = 45 s. |
| `OUT_SCALE = 3` | Output resolution = 854x480 x `OUT_SCALE`. Currently 2562x1440. The scene is still drawn at 854x480, then each frame is enlarged with nearest-neighbour (`cv2.INTER_NEAREST`) before writing, so the 8-bit pixel edges stay hard. Use whole numbers: 2 gives 1708x960, 4 gives 3416x1920. 1920x1080 would need a 2.25x enlargement and give uneven pixels. |
| `REALTIME = True` | `True` locks the preview to real time. `False` renders as fast as possible. |
| `FALLBACK_SECONDS = 50` | Only used if the MP3 length can't be read. |
| `BASE_DIR` | Directory of the script. The font, audio and output paths are built from it. |

Music reaction and colour blending (added later):
- **`analyse_audio()`** decodes the MP3 with `pygame.sndarray` (no extra dependency) and takes a 2048-sample FFT per video frame. It returns per-frame `LEVEL` (loudness), `BASS` (30-150 Hz energy), `BEAT` (a 0..1 pulse that jumps on each detected beat and decays by 0.84 per frame) and `HITS` (strong beats, at most one per second). Beats are peaks of spectral flux above the local 1-second average, with at least 7 frames between beats. If decoding fails, everything is zero and the old time-based animation and 3-second glitch are used (`AUDIO_OK = False`).
- **Kaleidoscope reaction.** `draw_kaleidoscope(surf, pal, t, sc, pulse)` takes an animation clock `t` (`ANIM_T`, a running sum whose speed grows with loudness and beats, so it never jumps), a radius scale `sc` that breathes with the bass, and a `pulse` that thickens lines and grows dots and diamonds. The background also brightens slightly on each beat, and the glitch effect fires on `HITS`.
- **Palette blending.** `blended_palette()` eases the colours (smoothstep over `BLEND_FRAMES` = 0.75 s) from the previous scene's palette to the current one at each new lyric line.
- Result on the current song: 41 beats (~64/min) and 16 glitch hits. Tuning knobs are the thresholds in `analyse_audio()` (1.35 flux ratio, 7-frame gap), the decay 0.84, and the multipliers in the `ANIM_T` line and the `draw_kaleidoscope` call in the main loop.

What was fixed:
- **Length follows the audio.** `pygame.mixer.Sound(AUDIO_PATH).get_length()` replaces the hard-coded 50 s.
- **Longer outro.** The outro lasts from 37.1 s to the end (about 8 s). The audio is padded with silence (`-af apad` plus `-shortest`) through the extra time.
- **Title card.** The fade is clamped to 0-255. It moved to the top of the screen so the first lyric, which starts at 0.0 s, is no longer hidden. The lyric and title are both drawn during the first 2 s. The outro fade is clamped too.
- **Real-time throttle** is optional (`REALTIME`).
- **Audio and codec.** At the end, ffmpeg re-encodes to H.264 (`yuv420p`, crf 18) and adds AAC audio. The silent intermediate `about_you_kaleido_silent.mp4` is deleted on success.
- **Output name** is `about_you_kaleido.mp4`, so it no longer collides with `main.py`.
- **Paths** no longer depend on the current working directory.

Last run: rendered 1350 frames (45 s) at ~29.9 fps and produced `output/about_you_kaleido.mp4` (2562x1440, ~45 MB, H.264 + audio; the ~15 MB figure was before the `OUT_SCALE` change). I did not view the video, so the look and lyric sync are unchecked.

## Known issues / rough edges (worth fixing when continuing)

Items marked **[fixed in main2.py]** are resolved there but still apply to `main.py` / `Raw_Lyrics.py`.

1. **Lyrics are duplicated** in `Raw_Lyrics.py` (plain list), `main.py` and `main2.py` (timed tuples). A retiming means editing in 2-3 places. Better: one shared `lyrics.py` / JSON file that all scripts import.
2. **Constants and helpers are copy-pasted** between `main.py` and `main2.py` (settings, palettes, fonts, `draw_lyrics`, title, progress, glitch). Better: a shared module, with each visual style as a pluggable "background" function.
3. **Length mismatch** **[fixed in main2.py]**: `main.py` still has `TOTAL_SECONDS = 50` although the lyrics end at 37.1 s and the song is about 39 s, so it shows only the background for the last ~13 s. It also does not read the MP3 length.
4. **`SCENE_ELEMENTS` in `main.py` has 12 entries but only 8 lyrics** exist. The last 4 are unused.
5. **Scanlines in `main.py`** call `pygame.draw.line` with an RGBA colour on a plain `Surface`. The alpha is ignored, so the lines are opaque black. `main2.py` does this correctly with an `SRCALPHA` overlay.
6. **Title fade** **[fixed in main2.py]**: `main.py` still uses `255 - (frame - 50) * 12`, which exceeds 255 between frames 32 and 50. The card is shown for frames 0-59, and the first lyric starts at 0.0 s but is hidden behind it until 2 s.
7. **Background is not audio-reactive.** Everything is a function of the frame number. There is no beat detection, so no visual reacts to the music.
8. `main2.py` real-time throttle **[fixed]**: set `REALTIME = False` for fast renders.
9. **In `main.py`, `draw_elements` finds the sprite index with `elements.index((name, bx, by))`**, which is O(n) but harmless at this size.
10. **Timing accuracy in `Raw_Lyrics.py`** is limited by human reaction time (0.1-0.3 s). It also doesn't play the audio itself, so the user has to start the MP3 at the same moment as their first SPACE.
11. `Raw_Lyrics.py` shows non-ASCII glyphs (`✓ ▶ ✅ …`) in a Courier New system font. These may render as boxes on some systems.
12. Codec **[fixed in main2.py]**: OpenCV writes `mp4v` (MPEG-4 Part 2), which is large and poorly supported. `main2.py` re-encodes to H.264 automatically. `main.py` output is still `mp4v` and has no audio.
13. **Relative paths and output name in `main.py` / `Raw_Lyrics.py`** are not fixed. They need to be run from inside this folder, and `main.py` writes `output/about_you_8bit.mp4`.

## Ideas for continuing

- Have `Raw_Lyrics.py` play `about_you.MP3` via `pygame.mixer` so stamps line up with the audio, and make it load lyrics from the shared file.
- Detect beats/energy (numpy FFT or `librosa`) and drive kaleidoscope radius, spin speed and glitch triggers from them.
- Give `main.py` the same fixes `main2.py` got (audio mux, path handling, length from audio, clamped fades).
- Add a `--style kaleido|starfield` option and a CLI for width, height and fps. Use one entry point instead of two near-duplicate scripts.
- Mix sprites into the kaleidoscope scene, or cross-fade between the two styles per verse.
- Use per-line palettes with smooth colour interpolation instead of a hard switch at each lyric.
- Word-level timing so the typewriter effect follows the actual singing.

## Conventions in the existing code

- Banner comments with `═══` box-drawing lines separate sections.
- Colours are RGB tuples in a palette dict. Pixel text uses `render(..., False, ...)` (no anti-aliasing) to keep the 8-bit look.
- Times are authored in seconds and converted to frames once, up front.
- `random.seed(42)` keeps starfields and glitches reproducible between runs.
