import unittest

from synthwave import visualizer as v


class VisualizerTest(unittest.TestCase):
    def meta(self, *dbs):
        return {f"lavfi.astats.{i + 3}.RMS_level": str(db - v.TILT * i) for i, db in enumerate(dbs)}

    def test_heights_are_relative_to_the_streams_loudness(self):
        quiet, loud = v.Meter(), v.Meter()
        flat = [-30.0] * v.BANDS
        for q, l in zip(quiet.heights(self.meta(*flat)), loud.heights(self.meta(*[db + 10 for db in flat]))):
            self.assertAlmostEqual(q, l)
        peak = quiet.heights(self.meta(-30 + v.FLOOR + v.RANGE + 10, *flat[1:]))
        self.assertEqual(peak[0], 1.0)  # well above the reference clamps to a full bar
        self.assertAlmostEqual(peak[1], -v.FLOOR / v.RANGE, delta=0.05)  # at the reference sits mid-height

    def test_silence_neither_fills_nor_skews(self):
        meter = v.Meter()
        silent = {f"lavfi.astats.{i + 3}.RMS_level": "-inf" for i in range(v.BANDS)}
        self.assertEqual(meter.heights(silent), [0.0] * v.BANDS)
        self.assertIsNone(meter.reference)

    def test_no_audio_yet(self):
        self.assertIsNone(v.Meter().heights(None))
        self.assertIsNone(v.Meter().heights({}))

    def test_sample_interpolates_across_bars(self):
        bands = [0.0, 1.0, 0.0]
        self.assertEqual([v.sample(bands, x) for x in (0, 0.25, 0.5, 1)], [0.0, 0.5, 1.0, 0.0])

    def test_graph_has_one_channel_per_band(self):
        self.assertEqual(len(v.CHANNELS), v.BANDS)
        self.assertEqual(v.GRAPH.count("bandpass="), v.BANDS)


if __name__ == "__main__":
    unittest.main()
