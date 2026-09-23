# About You: 8-Bit Lyric Video

A retro lyric video for **"About You" by The 1975**, drawn frame by frame in Python with
[pygame](https://www.pygame.org/) and written to MP4 with OpenCV. An animated 8-fold
kaleidoscope reacts to the music (beats, bass and loudness), the colours glide between
lyric lines, and the lyrics appear with a typewriter effect in a pixel font.

The finished video is in [`output/about_you_kaleido.mp4`](output/about_you_kaleido.mp4)
(2562x1440, 45 s, with audio).

## Features

- **Music-reactive visuals:** the song is analysed with an FFT. Beats thicken the lines and
  grow the dots, bass makes the pattern breathe, loudness speeds up the spin, and strong
  beats trigger a glitch effect.
- **Smooth palette changes:** colours ease from one lyric's palette to the next.
- **8-bit look:** Press Start 2P font, scanlines, vignette and hard pixel edges. The scene is
  drawn at 854x480 and enlarged with nearest-neighbour scaling (`OUT_SCALE`).
- **Live preview window** with progress, ETA and frame counter while rendering. ESC cancels.
- **Automatic audio:** at the end the video is re-encoded to H.264 and the song is added.
- **Lyric timing helper** (`Raw_Lyrics.py`) for stamping when each line starts.

## Files

| File | What it does |
|---|---|
| `main2.py` | Main renderer: kaleidoscope, music reaction, audio mux. **Use this one.** |
| `main.py` | First version: starfield, grid floor and floating pixel-art sprites. No audio step. |
| `Raw_Lyrics.py` | Interactive tool: press SPACE at each line change and it prints a `RAW_LYRICS` list. |
| `about_you.MP3` | The song. |
| `PressStart2P-Regular.ttf` | Pixel font. |
| `output/` | Rendered video. |
| `CLAUDE.md` | Detailed developer notes: how the code works, known issues, ideas. |

## Setup

Python 3.10 or newer. On very new Python versions (for example 3.14) `pygame` may not
install; `pygame-ce` is a drop-in replacement.

```
pip install pygame-ce numpy opencv-python imageio-ffmpeg
```

`imageio-ffmpeg` bundles an `ffmpeg` binary. It is not needed if `ffmpeg` is already on your PATH.

## Usage

```
python main2.py
```

It renders the video and writes `output/about_you_kaleido.mp4`, taking the length of the song
plus a few seconds of outro. `main2.py` finds its files relative to the script, so it can be
run from any folder.

### Settings (top of `main2.py`)

| Setting | Meaning |
|---|---|
| `OUT_SCALE` | Output size = 854x480 x this number. `3` gives 2562x1440, `2` gives 1708x960. Use whole numbers to keep pixels crisp. |
| `OUTRO_EXTRA` | Seconds of "Thanks for listening" held after the song ends. |
| `REALTIME` | `True` plays the preview at real time. `False` renders as fast as possible. |

### Timing your own lyrics

Run `python Raw_Lyrics.py`, start the song yourself, and press SPACE the moment each line
begins (U undoes the last stamp, ESC finishes). Paste the printed `RAW_LYRICS` block into
`main2.py`. `Raw_Lyrics.py` and `main.py` use relative paths, so run them from inside this folder.

## Copyright

The song and its lyrics belong to their owners (The 1975 and their publishers). They are
included here as part of a fan project for personal and educational use only. The code is
free to reuse, but no license file has been chosen yet.
