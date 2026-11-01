"""Curses rendering. Each frame is redrawn from App state; curses only sends the cells that changed."""
import curses, math, re, sys, textwrap, time

from . import keys, settings
from .stations import STATIONS
from .visualizer import sample, wave

PALETTE = (199, 205, 213, 177, 141, 105, 75, 51)  # 256-colour hot pink -> cyan
FALLBACK = (curses.COLOR_MAGENTA,) * 4 + (curses.COLOR_CYAN,) * 4  # for 8-colour terminals
QUOTE_COLOR = 183  # lavender
BLOCKS = " ▁▂▃▄▅▆▇█"
LOGO, TITLE = "◓", "synthwave"  # a sun setting on the horizon
BUTTON = "↻ new quote"  # top right, clickable
CLICK = re.compile(r"\[<0;(\d+);(\d+)M")  # SGR left-button press, 1-based column;row
TYPE_SPEED = 40  # quote characters revealed per second
MAX_BAR_ROWS = 12
VISUALIZER_TEXT = {"audio": "real audio", "decorative": "decorative", "off": "off"}
MENU_WIDTH = 46


def setup():
    curses.curs_set(0)
    curses.use_default_colors()
    rich = curses.COLORS >= 256
    for i, c in enumerate(PALETTE if rich else FALLBACK):
        curses.init_pair(i + 1, c, -1)
    curses.init_pair(len(PALETTE) + 1, QUOTE_COLOR if rich else -1, -1)
    curses.set_escdelay(25)  # a bare Esc shouldn't take a second to register
    mouse(True)


def mouse(on):
    # SGR clicks (1006), parsed by on_button: the system curses on macOS only understands the old X10
    # format, which some terminals (Warp) don't send and which breaks past column 223
    sys.stdout.write(f"\x1b[?1000;1006{'h' if on else 'l'}")
    sys.stdout.flush()


def read_escape(scr):
    """After an ESC key code, the rest of the escape sequence; empty for a bare Esc key press."""
    seq = ""
    scr.nodelay(True)  # the terminal sends the whole sequence at once; the main loop resets the timeout
    while len(seq) < 16 and not seq.endswith(("M", "m")):
        k = scr.getch()
        if k == -1:
            break
        seq += chr(k)
    return seq


def on_button(seq, width):
    """True if the escape sequence is a left click on the new-quote button."""
    m = CLICK.fullmatch(seq)
    if not m:
        return False
    x, y, left = int(m[1]) - 1, int(m[2]) - 1, width - 2 - len(BUTTON)
    return y == 1 and left <= x < left + len(BUTTON)


def color(i):
    return curses.color_pair(i + 1)


def put(scr, y, x, s, attr=0):
    try:  # plain try is noticeably cheaper than contextlib.suppress at ~100 calls a frame
        scr.addnstr(y, x, s, max(0, scr.getmaxyx()[1] - x), attr)
    except curses.error:  # clipped by a small terminal
        pass


def help_line(keymap):
    """Fits 80 columns with the default keys; the quote key lives on the button and in settings."""
    k = {action: keys.label(key) for action, key in keymap.items()}
    return (f"{k['play']} play · {k['prev']}/{k['next']} station · {k['louder']}/{k['quieter']} vol · "
            f"{k['sleep']} sleep · {k['mute']} mute · {k['settings']} settings · {k['quit']} quit")


def setting_text(field, value):
    if field == "visualizer":
        return VISUALIZER_TEXT[value]
    if field == "quote_minutes":
        return f"every {value} min" if value else "never"
    return f"{value} s" if value else "off"  # countdown


def status(app, now):
    """(icon, text, right-aligned label) for the now-playing line."""
    if app.autoplay_at:
        return "◌", f"{STATIONS[app.station][0]} starts in {math.ceil(app.autoplay_at - now)}…", "enter to play now"
    if app.props["pause"]:
        return "❚❚", app.title, "paused"
    if app.playing:
        return "▶", app.title, ""
    return "◌", app.title, "" if app.banner else "tuning in…"


def draw(scr, app, now):
    """Draw one frame; returns True while something is still animating."""
    h, w = scr.getmaxyx()
    W, n = max(0, w - 4), len(PALETTE)
    pink, cyan, dim, bold = color(0), color(n - 1), curses.A_DIM, curses.A_BOLD
    scr.erase()

    put(scr, 1, 2, LOGO, pink | bold)
    put(scr, 1, 4, TITLE, bold)
    left = w - 2 - len(BUTTON)
    put(scr, 1, left, BUTTON[0], color(n) | bold)
    put(scr, 1, left + 1, BUTTON[1:], dim)
    if app.sleep_at:
        timer = f"☾ {math.ceil((app.sleep_at - now) / 60)}m"
        put(scr, 1, left - 3 - len(timer), timer, pink)

    text, who = app.quote
    lines, credit = textwrap.wrap(f"“{text}”", max(10, W)), f"— {who}"
    shown = int((now - app.quote_at) * TYPE_SPEED)  # typewriter reveal, counted down line by line
    for i, line in enumerate(lines):
        put(scr, 3 + i, (w - len(line)) // 2, line[: max(0, shown)], color(n) | curses.A_ITALIC)
        shown -= len(line)
    put(scr, 4 + len(lines), (w - len(credit)) // 2, credit[: max(0, shown)], dim)

    horizon = h - 8
    rows = max(0, min(horizon - 8, MAX_BAR_ROWS))  # stay clear of the quote
    mode, count = app.settings["visualizer"], W // 2
    if mode != "off" and app.energy:
        if mode == "audio":
            heights = [sample(app.bands, i / max(1, count - 1)) for i in range(count)]
        else:
            heights = [wave(i, now) for i in range(count)]
        eighths = [int(app.energy * height * rows * 8) for height in heights]
        for r in range(rows):  # bottom row first
            line = " ".join([BLOCKS[max(0, min(8, e - r * 8))] for e in eighths])
            for c in range(n):  # one write per colour band keeps redraws cheap
                a, b = c * W // n, (c + 1) * W // n
                put(scr, horizon - 1 - r, 2 + a, line[a:b], color(c))
    put(scr, horizon, 2, "▔" * W, dim)

    icon, text, label = status(app, now)
    put(scr, h - 6, 2, icon, pink | bold)
    put(scr, h - 6, 5, text[: W - 6 - len(label)])  # spare columns for wide emoji
    put(scr, h - 6, w - 2 - len(label), label, dim)

    x = 2
    for i, (name, _) in enumerate(STATIONS):
        put(scr, h - 5, x, name, cyan | bold if i == app.station else dim)
        x += len(name) + 3

    mute = app.props["mute"]
    bar = max(0, min(24, W - 30))
    filled = round(app.volume / 100 * bar)
    put(scr, h - 3, 2, "vol", dim)
    put(scr, h - 3, 6, "━" * filled, dim if mute else cyan)
    put(scr, h - 3, 6 + filled, "─" * (bar - filled), dim)
    put(scr, h - 3, 7 + bar, "muted" if mute else f"{app.volume}%", dim if mute else cyan)
    clock = time.strftime("%H:%M:%S", time.gmtime(app.listened))
    put(scr, h - 3, w - 2 - len(clock), clock, pink)
    put(scr, h - 2, 2, help_line(app.settings["keys"]), dim)
    if app.menu:
        draw_menu(scr, app.menu, h, w)
    scr.refresh()
    return (mode != "off" and bool(app.energy)) or shown < len(credit)


def draw_menu(scr, menu, h, w):
    """The settings panel, centred over everything else."""
    n = len(PALETTE)
    pink, cyan, dim, bold = color(0), color(n - 1), curses.A_DIM, curses.A_BOLD
    bw, bh = min(MENU_WIDTH, w), len(settings.ROWS) + 7
    top, left = max(0, (h - bh) // 2), (w - bw) // 2
    for y in range(bh):
        ends, fill = ("╭╮", "─") if y == 0 else ("╰╯", "─") if y == bh - 1 else ("││", " ")
        put(scr, top + y, left, ends[0] + fill * (bw - 2) + ends[1], dim)
    put(scr, top, left + 2, " settings ", pink | bold)

    y = top + 2
    for i, (kind, field, label) in enumerate(settings.ROWS):
        if kind == "key" and settings.ROWS[i - 1][0] != "key":
            put(scr, y + 1, left + 4, "keys", dim)
            y += 2
        selected = i == menu.row
        if kind == "choice":
            value = setting_text(field, menu.settings[field])
            value = f"‹ {value} ›" if selected else value
        elif kind == "key":
            value = "press a key…" if selected and menu.capturing else keys.label(menu.settings["keys"][field])
        else:
            value = ""
        put(scr, y, left + 2, "›" if selected else " ", pink | bold)
        put(scr, y, left + 4, label, 0 if selected else dim)
        put(scr, y, left + bw - 3 - len(value), value, (pink if menu.capturing else cyan) | bold if selected else 0)
        y += 1

    hint = "esc cancel" if menu.capturing else "↑↓ move · ←→ change · enter set · esc close"
    put(scr, top + bh - 2, left + (bw - len(hint)) // 2, hint, dim)
