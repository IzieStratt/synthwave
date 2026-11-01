"""Settings, saved in $XDG_CONFIG_HOME/synthwave.json."""
import json, os

from . import keys
from .stations import STATIONS

PATH = os.path.join(os.environ.get("XDG_CONFIG_HOME") or os.path.expanduser("~/.config"), "synthwave.json")
CHOICES = {  # settings the menu cycles through, in menu order
    "visualizer": ("audio", "decorative", "off"),
    "quote_minutes": (1, 2, 5, 10, 0),  # 0 = keep the same quote
    "countdown": (0, 3, 5, 10),  # seconds to pick a station at launch, 0 = play right away
}


def defaults():
    return {"station": 0, "volume": 100, "visualizer": "audio", "quote_minutes": 2, "countdown": 5,
            "keys": dict(keys.DEFAULTS)}


def clean(field, value):
    """The value if it's valid for that setting (clamped where that makes sense); raises otherwise."""
    if field == "station":
        return int(value) % len(STATIONS)
    if field == "volume":
        return max(0, min(100, int(value)))
    if field == "keys":
        keymap = dict(keys.DEFAULTS, **{a: k for a, k in value.items() if a in keys.DEFAULTS and keys.code(k)})
        if len(set(keymap.values())) < len(keymap):
            raise ValueError("two actions share a key")
        return keymap
    if value in CHOICES[field]:
        return value
    raise ValueError(value)


def load(path=None):
    """Saved settings over the defaults; anything missing or invalid keeps its default."""
    settings = defaults()
    try:
        with open(path or PATH) as f:
            saved = json.load(f)
        for field, value in saved.items():
            try:
                settings[field] = clean(field, value)
            except (AttributeError, KeyError, TypeError, ValueError):
                pass
    except (OSError, ValueError, AttributeError):  # missing, corrupt, or not a JSON object
        pass
    return settings


def save(settings, path=None):
    path = path or PATH
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path + ".tmp", "w") as f:
        json.dump(settings, f, indent=2)
    os.replace(path + ".tmp", path)  # atomic, so a crash never leaves a half-written file
