"""The settings menu: what it lists and how keys change it. Drawing lives in ui.py."""
import curses

from . import config, keys

ROWS = (  # (kind, setting or action, label)
    ("choice", "visualizer", "visualizer"),
    ("choice", "quote_minutes", "new quote"),
    ("choice", "countdown", "launch countdown"),
    *(("key", action, label) for action, label, _ in keys.ACTIONS),
    ("reset", "keys", "reset keys to defaults"),
)


class Menu:
    """↑/↓ pick a row, ←/→ or enter change it, esc closes. Edits the settings dict in place."""

    def __init__(self, settings):
        self.settings, self.row, self.capturing, self.open = settings, 0, False, True

    def on_key(self, key):
        """Handle one key; returns the name of the setting it changed, if any."""
        kind, field, _ = ROWS[self.row]
        if self.capturing:
            return self.bind(field, key)
        if key in (curses.KEY_UP, curses.KEY_DOWN):
            self.row = (self.row + (1 if key == curses.KEY_DOWN else -1)) % len(ROWS)
        elif kind == "choice" and key in (curses.KEY_LEFT, curses.KEY_RIGHT, *keys.ENTER):
            options = config.CHOICES[field]
            step = -1 if key == curses.KEY_LEFT else 1
            self.settings[field] = options[(options.index(self.settings[field]) + step) % len(options)]
            return field
        elif kind == "key" and key in keys.ENTER:
            self.capturing = True
        elif kind == "reset" and key in keys.ENTER:
            self.settings["keys"] = dict(keys.DEFAULTS)
            return "keys"
        elif key == keys.ESC or keys.name(key) in (self.settings["keys"]["settings"], self.settings["keys"]["quit"]):
            self.open = False
        return None

    def bind(self, action, key):
        """Give the action the pressed key, swapping with whichever action had it. Esc cancels."""
        new = keys.name(key)
        if key != keys.ESC and new is None:
            return None  # not bindable: keep waiting
        self.capturing = False
        if key == keys.ESC:
            return None
        keymap = self.settings["keys"]
        for other, old in keymap.items():
            if old == new:
                keymap[other] = keymap[action]
        keymap[action] = new
        return "keys"
