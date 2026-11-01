"""Bar heights: real audio levels measured by an mpv filter, or a decorative fake."""
import math

BANDS = 14
FREQS = [40 * 350 ** (i / (BANDS - 1)) for i in range(BANDS)]  # 40 Hz to 14 kHz, evenly spaced in pitch
OCTAVES = math.log2(350) / (BANDS - 1)  # width of each band, so neighbours just touch
CHANNELS = "FC BL BR BC SL SR TFL TFC TFR TBL TBC TBR WL WR".split()  # the spare channels of a 16-channel layout

# mpv only reads stats from the main chain (amerge drops frame metadata), so each band rides along as
# an extra channel: copy the mono mix into it, band-pass it, measure every channel, then mix back to stereo
GRAPH = ",".join([
    "aformat=channel_layouts=stereo",
    "pan=hexadecagonal|FL=c0|FR=c1|" + "|".join(f"{c}=0.5*c0+0.5*c1" for c in CHANNELS),
    *(f"bandpass=f={f:.0f}:width_type=o:width={OCTAVES:.2f}:channels={c}" for f, c in zip(FREQS, CHANNELS)),
    "astats=metadata=1:reset=1:measure_overall=none:measure_perchannel=RMS_level",
    "pan=stereo|c0=c0|c1=c1",
])
LABEL = "viz"
FILTER = f"@{LABEL}:lavfi=graph=%{len(GRAPH)}%{GRAPH}"  # %n% quoting keeps mpv from parsing the graph's , | =
PROPERTY = f"af-metadata/{LABEL}"
# tuned on recordings of three Lofi Girl streams: bars average about 40% high and rarely pin at full
TILT = 2.5  # dB lift per band: music has far less energy up high, this keeps the right side alive
FLOOR, RANGE = -8.0, 22.0  # dB below the stream's loudness for an empty bar, dB span to a full one
SILENCE = -100.0
ADAPT = 0.01  # per poll (~30 a second), so the loudness reference follows over a few seconds


class Meter:
    """Bar heights from mpv's band levels, relative to the stream's own recent loudness:
    some stations are mixed 10 dB louder than others, and a fixed scale would pin them at full."""

    def __init__(self):
        self.reference = None

    def heights(self, meta):
        """0..1 per band from mpv's af-metadata, or None while no audio has gone through the filter."""
        try:  # astats channels 1 and 2 are the music itself
            dbs = [max(SILENCE, float(meta[f"lavfi.astats.{i + 3}.RMS_level"])) + TILT * i for i in range(BANDS)]
        except (KeyError, TypeError, ValueError):
            return None
        loudness = sum(dbs) / BANDS
        if loudness > SILENCE + 30:  # don't let a silent gap drag the reference down
            self.reference = loudness if self.reference is None else self.reference + (loudness - self.reference) * ADAPT
        if self.reference is None:
            return [0.0] * BANDS
        return [max(0.0, min(1.0, (db - self.reference - FLOOR) / RANGE)) for db in dbs]


def sample(bands, x):
    """Bands linearly interpolated at x in 0..1, so any number of bars can show them."""
    pos = x * (len(bands) - 1)
    i = min(int(pos), len(bands) - 2)
    return bands[i] + (bands[i + 1] - bands[i]) * (pos - i)


def wave(i, t):
    """The decorative mode: layered sines in about 0..1, fluid at any frame rate."""
    return (0.5 + 0.22 * math.sin(t * 1.3 + i * 0.45)
            + 0.16 * math.sin(t * 2.9 + i * 1.7)
            + 0.12 * math.sin(t * 4.7 + i * 2.9))
