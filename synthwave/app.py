"""Player state, the main loop and key bindings."""
import curses, random, re, sys, time

from . import config, keys, settings, ui, visualizer
from .mpv import Mpv
from .quotes import QUOTES
from .stations import STATIONS, url

SLEEP_STEPS = (0, 15, 30, 60, 90)  # sleep timer presets in minutes, 0 = off
FRAME_MS, IDLE_MS = 33, 500  # ~30 fps while anything moves, otherwise barely wake up
LIVE_STAMP = re.compile(r" \d{4}-\d\d-\d\d \d\d:\d\d$")  # yt-dlp appends the start time to live titles
LEVELS = 1  # request id for visualizer level polls


class App:
    def __init__(self):
        now = time.monotonic()
        self.settings = config.load()
        self.station, volume = self.settings["station"], self.settings["volume"]
        self.bindings = keys.bindings(self.settings["keys"])
        self.menu = None
        self.mpv = Mpv(volume)
        if self.settings["visualizer"] == "audio":
            self.mpv.send("af", "add", visualizer.FILTER)
        self.mpv.send("loadfile", url(self.station))  # buffers while paused, so autoplay starts instantly
        self.props = {"pause": True, "volume": volume, "mute": False, "media-title": "", "core-idle": True}
        self.banner = ""  # shown instead of the stream title; None once the stream has loaded
        self.autoplay_at = now + self.settings["countdown"]
        self.sleep_step, self.sleep_at = 0, None
        self.listened, self.energy, self.last = 0.0, 0.0, now
        self.meter = visualizer.Meter()
        self.bands = self.target = [0.0] * visualizer.BANDS  # shown and latest measured audio levels
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

    def save(self):
        config.save(dict(self.settings, station=self.station, volume=self.volume))

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
            self.autoplay_at = now + self.settings["countdown"]  # still choosing: wait for the dial to settle
        else:
            self.mpv.set("pause", False)
        self.save()

    def changed(self, setting):
        """Apply a setting the menu just changed, then save."""
        if setting == "visualizer":
            self.mpv.send("af", "remove", "@" + visualizer.LABEL)  # no-op when it isn't there
            if self.settings["visualizer"] == "audio":
                self.mpv.send("af", "add", visualizer.FILTER)
        elif setting == "keys":
            self.bindings = keys.bindings(self.settings["keys"])
        self.save()

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
            elif ev.get("request_id") == LEVELS:
                self.target = self.meter.heights(ev.get("data")) or [0.0] * visualizer.BANDS

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
        if self.settings["visualizer"] == "audio" and self.playing:
            self.mpv.send("get_property", visualizer.PROPERTY, request_id=LEVELS)
        rise, fall = min(1.0, dt * 25), min(1.0, dt * 6)  # snap up on a beat, settle down gently
        self.bands = [b + (t - b) * (rise if t > b else fall) for b, t in zip(self.bands, self.target)]
        minutes = self.settings["quote_minutes"]
        if minutes and now - self.quote_at > minutes * 60:
            self.new_quote(now)

    def on_key(self, key, now):
        """Handle one key press; returns False to quit."""
        if self.menu:
            changed = self.menu.on_key(key)
            if changed:
                self.changed(changed)
            if not self.menu.open:
                self.menu = None
            return True
        action = self.bindings.get(key)
        if action == "quit":
            return False
        if action == "play":
            if self.autoplay_at:
                self.play()
            else:
                self.mpv.send("cycle", "pause")
        elif key in keys.ENTER:
            self.play()
        elif action == "mute":
            self.mpv.send("cycle", "mute")
        elif action == "quote":
            self.new_quote(now)
        elif action == "sleep":
            self.sleep_step = (self.sleep_step + 1) % len(SLEEP_STEPS)
            self.sleep_at = now + SLEEP_STEPS[self.sleep_step] * 60 if self.sleep_step else None
        elif action in ("louder", "quieter"):
            volume = max(0, min(100, self.volume + (5 if action == "louder" else -5)))
            self.props["volume"] = volume  # update now so fast repeats don't read a stale value
            self.mpv.set("volume", volume)
            self.save()
        elif action in ("prev", "next"):
            self.tune(self.station + (1 if action == "next" else -1), now)
        elif action == "settings":
            self.menu = settings.Menu(self.settings)
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
                key, now = scr.getch(), time.monotonic()
                if key == curses.KEY_RESIZE and sys.platform == "win32":
                    curses.resize_term(0, 0)  # PDCurses only takes the new size when asked
                if key == keys.ESC:
                    seq = ui.read_escape(scr)
                    if seq:  # a mouse report, not the Esc key
                        if ui.on_button(seq, scr.getmaxyx()[1]):
                            self.new_quote(now)
                        continue
                if not self.on_key(key, now):
                    return None
            return f"synthwave: mpv exited ({self.mpv.proc.returncode})"
        finally:
            ui.mouse(False)
            self.mpv.close()
