"""Entry point for `synthwave` and `python -m synthwave`."""
import contextlib, curses, shutil, signal, sys

from .app import App


def main():
    missing = [tool for tool in ("mpv", "yt-dlp") if not shutil.which(tool)]
    if missing:
        sys.exit(f"synthwave needs {' and '.join(missing)} on your PATH (see Install in the README)")
    for sig in ("SIGHUP", "SIGTERM"):  # closing the terminal still stops mpv; Windows has no SIGHUP
        if hasattr(signal, sig):
            signal.signal(getattr(signal, sig), lambda *_: sys.exit())
    with contextlib.suppress(KeyboardInterrupt):
        sys.exit(curses.wrapper(lambda scr: App().run(scr)))


if __name__ == "__main__":
    main()
