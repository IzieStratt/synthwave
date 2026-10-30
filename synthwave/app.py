"""Player state, the main loop and key bindings."""
import curses, random, re, time

from . import config, ui
from .mpv import Mpv
from .quotes import QUOTES
from .stations import STATIONS, url

AUTOPLAY_DELAY = 5  # seconds to pick a station at launch before the current one starts
SLEEP_STEPS = (0, 15, 30, 60, 90)  # sleep timer presets in minutes, 0 = off
QUOTE_SECONDS = 120
FRAME_MS, IDLE_MS = 33, 500  # ~30 fps while anything moves, otherwise barely wake up
LIVE_STAMP = re.compile(r" \d{4}-\d\d-\d\d \d\d:\d\d$")  # yt-dlp appends the start time to live titles


class App:
    def __init__(self):
        now = time.monotonic()
        self.station, volume = config.load()
        self.mpv = Mpv(volume)
        self.mpv.send("loadfile", url(self.station))  # buffers while paused, so autoplay starts instantly
        self.props = {"pause": True, "volume": volume, "mute": False, "media-title": "", "core-idle": True}
        self.banner = ""  # shown instead of the stream title; None once the stream has loaded
        self.autoplay_at = now + AUTOPLAY_DELAY
        self.sleep_step, self.sleep_at = 0, None
        self.listened, self.energy, self.last = 0.0, 0.0, now
        self.drift = time.time() - now
        self.quote = None
        self.new_quote(now)

    @property
    def playing(self):
        return not self.props["pause"] and not self.props["core-idle"]

    @property
    def volume(self):
        return int(self.props["volume"])

    @property
    def title(self):
        return self.props["media-title"] if self.banner is None else self.banner

    def new_quote(self, now):
        self.quote = random.choice([q for q in QUOTES if q != self.quote])
        self.quote_at = now

    def play(self):
        self.autoplay_at = None
        self.mpv.set("pause", False)

    def pause(self):
        self.autoplay_at = None
        self.mpv.set("pause", True)

    def tune(self, station, now):
        self.station = station % len(STATIONS)
        self.mpv.send("loadfile", url(self.station))
        if self.autoplay_at:
            self.autoplay_at = now + AUTOPLAY_DELAY  # still choosing: wait for the dial to settle
        else:
            self.mpv.set("pause", False)
        config.save(self.station, self.volume)

    def tick(self, now):
        for ev in self.mpv.events():
            kind = ev.get("event")
            if kind == "property-change" and "data" in ev:
                data = ev["data"]
                self.props[ev["name"]] = LIVE_STAMP.sub("", data) if ev["name"] == "media-title" else data
            elif kind == "start-file":
                self.banner = ""
            elif kind == "file-loaded":
                self.banner = None
            elif kind == "end-file" and ev.get("reason") == "error":
                self.banner = "stream unavailable, try another station"

        # monotonic time stops while the machine sleeps, so a jump against wall time means the lid was closed
        if time.time() - now - self.drift > 5:
            self.pause()
        self.drift = time.time() - now
        if self.autoplay_at and now >= self.autoplay_at:
            self.play()
        if self.sleep_at and now >= self.sleep_at:
            self.pause()
            self.sleep_step, self.sleep_at = 0, None

        dt, self.last = now - self.last, now
        self.listened += dt * self.playing
        self.energy += (self.playing - self.energy) * min(1.0, dt * 4)  # bars ease in and out
        if self.energy < 0.001:
            self.energy = 0.0
        if now - self.quote_at > QUOTE_SECONDS:
            self.new_quote(now)

    def on_key(self, key, now):
        """Handle one key press; returns False to quit."""
        if key in (ord("q"), ord("Q")):
            return False
        if key in (ord(" "), ord("p")):
            if self.autoplay_at:
                self.play()
            else:
                self.mpv.send("cycle", "pause")
        elif key in (curses.KEY_ENTER, 10, 13):
            self.play()
        elif key == ord("m"):
            self.mpv.send("cycle", "mute")
        elif key == ord("s"):
            self.sleep_step = (self.sleep_step + 1) % len(SLEEP_STEPS)
            self.sleep_at = now + SLEEP_STEPS[self.sleep_step] * 60 if self.sleep_step else None
        elif key in (curses.KEY_UP, curses.KEY_DOWN, ord("+"), ord("="), ord("-")):
            volume = max(0, min(100, self.volume + (-5 if key in (curses.KEY_DOWN, ord("-")) else 5)))
            self.props["volume"] = volume  # update now so fast repeats don't read a stale value
            self.mpv.set("volume", volume)
            config.save(self.station, volume)
        elif key in (curses.KEY_LEFT, curses.KEY_RIGHT):
            self.tune(self.station + (1 if key == curses.KEY_RIGHT else -1), now)
        elif ord("1") <= key < ord("1") + len(STATIONS):
            self.tune(key - ord("1"), now)
        return True

    def run(self, scr):
        ui.setup()
        try:
            while self.mpv.proc.poll() is None:
                now = time.monotonic()
                self.tick(now)
                scr.timeout(FRAME_MS if ui.draw(scr, self, now) else IDLE_MS)
                if not self.on_key(scr.getch(), time.monotonic()):
                    return None
            return f"synthwave: mpv exited ({self.mpv.proc.returncode})"
        finally:
            self.mpv.close()
