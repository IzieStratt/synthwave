# synthwave

A tiny, vibey terminal radio for [Lofi Girl](https://www.youtube.com/@LofiGirl)'s live streams.
One small Python package with no dependencies beyond the standard library (plus curses on Windows). The app itself uses
about 20 MB of memory and around 1% CPU while it animates.

```
  ◓ synthwave                                                ☾ 30m   ↻ new quote

              “Not all those who wander are lost.”  — J.R.R. Tolkien

                      ▂           ▅ ▆ ▃                   ▇ ▄
          ▄ ▆ ▂     ▃ █ ▆       ▂ █ █ █ ▅               ▃ █ █ ▅
        ▂ █ █ █ ▇ ▅ █ █ █ ▃   ▄ █ █ █ █ █ ▆ ▁         ▆ █ █ █ █ ▂
  ▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔

  ▶  synthwave radio 🌌 beats to chill/game to
  synthwave   lofi   sleep   jazz   house   rainy   ambient   dark

  vol ━━━━━━━━━━━━━━━━━━──────── 75%                              01:24:09
  space play · ←/→ station · ↑/↓ vol · s sleep · m mute · o settings · q quit
```

## Features

- Eight Lofi Girl stations: synthwave, lofi, sleep, jazz, house, rainy, ambient and dark
- A visualizer that follows the real audio (or a decorative one, or none)
- A few seconds to pick a station at launch, then your last one starts on its own
- Sleep timer (15, 30, 60 or 90 minutes)
- Pauses when your laptop sleeps, so music doesn't blast when you open the lid
- A settings menu for the visualizer, quotes, launch countdown and every key
- Remembers your station, volume and settings
- A new quote every couple of minutes, or whenever you click for one

## Install

You need [mpv](https://mpv.io), [yt-dlp](https://github.com/yt-dlp/yt-dlp) and Python 3.9+, with
`mpv` and `yt-dlp` on your PATH. It runs on macOS, Linux and Windows. Install those first, then
synthwave itself with [uv](https://docs.astral.sh/uv/) or [pipx](https://pipx.pypa.io):

```sh
uv tool install git+https://github.com/JosTheDude/synthwave
# or: pipx install git+https://github.com/JosTheDude/synthwave
synthwave
```

From a clone: `uv tool install --editable .`, or run it in place with `python3 -m synthwave`.

### macOS

```sh
brew install mpv yt-dlp uv
```

### Linux

YouTube changes often, and distro `yt-dlp` packages (Debian and Ubuntu especially) can lag far
enough behind to stop working. If a station says "stream unavailable", install yt-dlp with
`uv tool install yt-dlp` (or `pipx install yt-dlp`) instead and keep it fresh with
`uv tool upgrade yt-dlp`.

```sh
# Debian, Ubuntu, Mint, Pop!_OS
sudo apt install mpv pipx && pipx install yt-dlp

# Fedora
sudo dnf install mpv yt-dlp pipx

# Arch, Manjaro, EndeavourOS
sudo pacman -S mpv yt-dlp uv

# openSUSE
sudo zypper install mpv yt-dlp python3-pipx
```

On any distro, `curl -LsSf https://astral.sh/uv/install.sh | sh` installs uv. With pipx, run
`pipx ensurepath` once so `synthwave` lands on your PATH.

### Windows

With [Scoop](https://scoop.sh):

```powershell
scoop bucket add extras
scoop install python mpv yt-dlp uv
uv tool install git+https://github.com/JosTheDude/synthwave
synthwave
```

On Windows synthwave also installs [windows-curses](https://pypi.org/project/windows-curses/),
since Windows Python has no curses of its own. Use Windows Terminal for colors and the visualizer's
block characters. Clicking the new-quote button doesn't work there; press `n` instead.

## Keys

These are the defaults; every one of them can be changed in settings.

| Key | Action |
| --- | --- |
| `space` | play or pause |
| `←` `→` | previous or next station |
| `↑` `↓` | volume |
| `n` | new quote (or click `↻ new quote`) |
| `s` | cycle the sleep timer |
| `m` | mute |
| `o` | settings |
| `q` | quit |

`enter` (play now, skipping the countdown) and `1`–`8` (jump to a station) always work and
can't be rebound. Clicking needs mouse reporting, which most terminals have on (not on Windows). In Warp it's a
setting. While synthwave is open, hold Shift (Option in iTerm2) to select text.

## Settings

Press `o`. Use `↑` `↓` to pick a row, `←` `→` or `enter` to change it, and `esc` to close.
Changes save as you make them.

| Setting | Choices |
| --- | --- |
| visualizer | **real audio** (default), **decorative** or **off** |
| new quote | every 1, 2 (default), 5 or 10 minutes, or never |
| launch countdown | off, 3, 5 (default) or 10 seconds |
| keys | select an action, press `enter`, then press the new key. If another action had that key, the two swap. `esc` cancels. |

**real audio** bars show the music that's actually playing, split into 14 bands from deep bass
on the left to treble on the right. Heights are measured against each stream's own recent
loudness, so loud and quiet stations both fill the space. Measuring adds about 6% of one CPU
core to mpv. **decorative** bars are layered sine waves that only follow play and pause, and
they cost almost nothing.

## How it works

synthwave runs a headless `mpv` and controls it over mpv's
[JSON IPC socket](https://mpv.io/manual/stable/#json-ipc).

For the real-audio visualizer, it adds an ffmpeg filter to mpv's audio chain. The filter copies
the music into 14 extra channels, band-passes each one to its own frequency band, measures every
channel's loudness, then mixes back down to plain stereo, so what you hear doesn't change. The
app reads the levels about 30 times a second. Switching to decorative or off removes the filter.

Settings live in `$XDG_CONFIG_HOME/synthwave.json` (by default `~/.config/synthwave.json`). You
can edit the file by hand too. Anything invalid falls back to its default.

| File | What it does |
| --- | --- |
| `synthwave/app.py` | player state, main loop, actions |
| `synthwave/ui.py` | all drawing, including the settings panel, and mouse clicks |
| `synthwave/settings.py` | settings menu rows and how keys change them |
| `synthwave/keys.py` | rebindable actions and key names |
| `synthwave/visualizer.py` | the audio filter, level meter and decorative wave |
| `synthwave/mpv.py` | mpv process and IPC client |
| `synthwave/config.py` | settings file: defaults, validation, saving |
| `synthwave/stations.py` | station list |
| `synthwave/quotes.py` | quote list |

## Contributing

Run the tests with `python3 -m unittest`.

Lofi Girl sometimes restarts a stream, which changes its YouTube ID. If a station says
"stream unavailable", update its ID in `synthwave/stations.py` from
[Lofi Girl's live streams](https://www.youtube.com/@LofiGirl/streams). New quotes go in
`synthwave/quotes.py`; keep them short enough to fit on one line.

## License

[MIT](LICENSE). Not affiliated with Lofi Girl; all music streams belong to their owners.
