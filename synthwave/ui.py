"""Curses rendering. Each frame is redrawn from App state; curses only sends the cells that changed."""
import curses, math, textwrap, time

from .stations import STATIONS

PALETTE = (199, 205, 213, 177, 141, 105, 75, 51)  # 256-colour hot pink -> cyan
FALLBACK = (curses.COLOR_MAGENTA,) * 4 + (curses.COLOR_CYAN,) * 4  # for 8-colour terminals
QUOTE_COLOR = 183  # lavender
BLOCKS = " ▁▂▃▄▅▆▇█"
TITLE = "S Y N T H W A V E"
HELP = "space play/pause · ←/→ station · ↑/↓ volume · s sleep · m mute · q quit"
TYPE_SPEED = 40  # quote characters revealed per second
MAX_BAR_ROWS = 12


def setup():
    curses.curs_set(0)
    curses.use_default_colors()
    rich = curses.COLORS >= 256
    for i, c in enumerate(PALETTE if rich else FALLBACK):
        curses.init_pair(i + 1, c, -1)
    curses.init_pair(len(PALETTE) + 1, QUOTE_COLOR if rich else -1, -1)


def color(i):
    return curses.color_pair(i + 1)


def put(scr, y, x, s, attr=0):
    try:  # plain try is noticeably cheaper than contextlib.suppress at ~100 calls a frame
        scr.addnstr(y, x, s, max(0, scr.getmaxyx()[1] - x), attr)
    except curses.error:  # clipped by a small terminal
        pass


def wave(i, t):
    """A fake spectrum in 0..1 from layered sines, so motion stays fluid at any frame rate."""
    return (0.5 + 0.22 * math.sin(t * 1.3 + i * 0.45)
            + 0.16 * math.sin(t * 2.9 + i * 1.7)
            + 0.12 * math.sin(t * 4.7 + i * 2.9))


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

    for i, ch in enumerate(TITLE):
        put(scr, 1, 2 + i, ch, color(i * n // len(TITLE)) | bold)
    put(scr, 1, 4 + len(TITLE), "lofi girl radio", dim)
    if app.sleep_at:
        timer = f"☾ {math.ceil((app.sleep_at - now) / 60)}m"
        put(scr, 1, w - 2 - len(timer), timer, pink)

    text, who = app.quote
    lines, credit = textwrap.wrap(f"“{text}”", max(10, W)), f"— {who}"
    shown = int((now - app.quote_at) * TYPE_SPEED)  # typewriter reveal, counted down line by line
    for i, line in enumerate(lines):
        put(scr, 3 + i, (w - len(line)) // 2, line[: max(0, shown)], color(n) | curses.A_ITALIC)
        shown -= len(line)
    put(scr, 4 + len(lines), (w - len(credit)) // 2, credit[: max(0, shown)], dim)

    horizon = h - 8
    rows = max(0, min(horizon - 8, MAX_BAR_ROWS))  # stay clear of the quote
    if app.energy:
        eighths = [int(app.energy * wave(i, now) * rows * 8) for i in range(W // 2)]  # bar heights
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
    put(scr, h - 2, 2, HELP, dim)
    scr.refresh()
    return bool(app.energy) or shown < len(credit)
