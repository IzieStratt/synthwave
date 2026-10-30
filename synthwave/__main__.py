"""Entry point for `synthwave` and `python -m synthwave`."""
import contextlib, curses, shutil, signal, sys

from .app import App


def main():
    missing = [tool for tool in ("mpv", "yt-dlp") if not shutil.which(tool)]
    if missing:
        sys.exit(f"synthwave needs {' and '.join(missing)} on your PATH (e.g. brew install {' '.join(missing)})")
    for sig in (signal.SIGHUP, signal.SIGTERM):  # closing the terminal still stops mpv
        signal.signal(sig, lambda *_: sys.exit())
    with contextlib.suppress(KeyboardInterrupt):
        sys.exit(curses.wrapper(lambda scr: App().run(scr)))


if __name__ == "__main__":
    main()
