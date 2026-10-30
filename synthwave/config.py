"""Remembers the last station and volume in $XDG_CONFIG_HOME/synthwave.json."""
import json, os

from .stations import STATIONS

PATH = os.path.join(os.environ.get("XDG_CONFIG_HOME") or os.path.expanduser("~/.config"), "synthwave.json")


def load(path=None):
    """Return (station, volume), falling back to defaults if the file is missing or corrupt."""
    try:
        with open(path or PATH) as f:
            s = json.load(f)
        return int(s["station"]) % len(STATIONS), max(0, min(100, int(s["volume"])))
    except (OSError, ValueError, KeyError, TypeError):
        return 0, 100


def save(station, volume, path=None):
    path = path or PATH
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path + ".tmp", "w") as f:
        json.dump({"station": station, "volume": volume}, f)
    os.replace(path + ".tmp", path)  # atomic, so a crash never leaves a half-written file
