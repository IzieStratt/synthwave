# synthwave

A tiny, vibey terminal radio for [Lofi Girl](https://www.youtube.com/@LofiGirl)'s live streams.
One small Python package, no dependencies beyond the standard library, about 20 MB of memory
and around 1% CPU while it animates.

```
  S Y N T H W A V E  lofi girl radio                                       ☾ 30m

              “Not all those who wander are lost.”  — J.R.R. Tolkien

                      ▂           ▅ ▆ ▃                   ▇ ▄
          ▄ ▆ ▂     ▃ █ ▆       ▂ █ █ █ ▅               ▃ █ █ ▅
        ▂ █ █ █ ▇ ▅ █ █ █ ▃   ▄ █ █ █ █ █ ▆ ▁         ▆ █ █ █ █ ▂
  ▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔

  ▶  synthwave radio 🌌 beats to chill/game to
  synthwave   lofi   sleep   jazz   house   rainy   ambient   dark

  vol ━━━━━━━━━━━━━━━━━━──────── 75%                              01:24:09
  space play/pause · ←/→ station · ↑/↓ volume · s sleep · m mute · q quit
```

## Features

- Eight Lofi Girl stations: synthwave, lofi, sleep, jazz, house, rainy, ambient and dark
- Five seconds to pick a station at launch, then your last one starts on its own
- Sleep timer (15, 30, 60 or 90 minutes)
- Pauses when your laptop sleeps, so music doesn't blast when you open the lid
- Remembers your station and volume
- A new quote every couple of minutes

## Install

You need [mpv](https://mpv.io) and [yt-dlp](https://github.com/yt-dlp/yt-dlp) on your PATH, and Python 3.9+.
It runs on macOS and Linux.

```sh
brew install mpv yt-dlp        # or your distro's package manager
uv tool install git+https://github.com/JosTheDude/synthwave   # or: pipx install git+https://github.com/JosTheDude/synthwave
synthwave
```

From a clone: `uv tool install --editable .`, or run it in place with `python3 -m synthwave`.

## Keys

| Key | Action |
| --- | --- |
| `space` / `p` | play or pause |
| `enter` | play now (skips the launch countdown) |
| `←` `→` / `1`–`8` | switch station |
| `↑` `↓` / `+` `-` | volume |
| `s` | cycle the sleep timer |
| `m` | mute |
| `q` | quit |

## How it works

synthwave runs a headless `mpv` and controls it over mpv's
[JSON IPC socket](https://mpv.io/manual/stable/#json-ipc). The bars are decorative, not a real
spectrum, so the app never touches the audio itself. Settings live in
`$XDG_CONFIG_HOME/synthwave.json` (by default `~/.config/synthwave.json`).

| File | What it does |
| --- | --- |
| `synthwave/app.py` | player state, main loop, key bindings |
| `synthwave/ui.py` | all drawing |
| `synthwave/mpv.py` | mpv process and IPC client |
| `synthwave/stations.py` | station list |
| `synthwave/quotes.py` | quote list |
| `synthwave/config.py` | saved settings |

## Contributing

Run the tests with `python3 -m unittest`.

Lofi Girl sometimes restarts a stream, which changes its YouTube ID. If a station says
"stream unavailable", update its ID in `synthwave/stations.py` from
[Lofi Girl's live streams](https://www.youtube.com/@LofiGirl/streams). New quotes go in
`synthwave/quotes.py`; keep them short enough to fit on one line.

## License

[MIT](LICENSE). Not affiliated with Lofi Girl; all music streams belong to their owners.
