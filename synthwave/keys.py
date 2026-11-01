"""Rebindable actions, and the key names the settings file stores for them."""
import curses

ACTIONS = (  # (action, label in the settings menu, default key)
    ("play", "play / pause", "space"),
    ("prev", "previous station", "left"),
    ("next", "next station", "right"),
    ("louder", "volume up", "up"),
    ("quieter", "volume down", "down"),
    ("mute", "mute", "m"),
    ("quote", "new quote", "n"),
    ("sleep", "sleep timer", "s"),
    ("settings", "settings", "o"),
    ("quit", "quit", "q"),
)
DEFAULTS = {action: key for action, _, key in ACTIONS}
NAMED = {"space": ord(" "), "left": curses.KEY_LEFT, "right": curses.KEY_RIGHT,
         "up": curses.KEY_UP, "down": curses.KEY_DOWN}
SYMBOLS = {"left": "←", "right": "→", "up": "↑", "down": "↓"}
ENTER, ESC = (curses.KEY_ENTER, 10, 13), 27


def name(code):
    """The name of a bindable key code, else None. Digits stay reserved for picking stations."""
    for n, c in NAMED.items():
        if c == code:
            return n
    return chr(code) if 33 <= code < 127 and not chr(code).isdigit() else None


def code(n):
    """The key code for a bindable key name, else None."""
    c = NAMED.get(n, ord(n) if isinstance(n, str) and len(n) == 1 else None)
    return c if c is not None and name(c) == n else None


def label(n):
    return SYMBOLS.get(n, n)


def bindings(keymap):
    """{key code: action} from {action: key name}."""
    return {code(key): action for action, key in keymap.items()}
