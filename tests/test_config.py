import json, os, tempfile, unittest

from synthwave import config, keys
from synthwave.stations import STATIONS


class ConfigTest(unittest.TestCase):
    def setUp(self):
        self.path = os.path.join(tempfile.mkdtemp(), "nested", "synthwave.json")

    def write(self, text):
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        with open(self.path, "w") as f:
            f.write(text)

    def test_defaults_when_missing(self):
        self.assertEqual(config.load(self.path), config.defaults())

    def test_round_trip(self):
        settings = dict(config.defaults(), station=3, volume=40, visualizer="off", countdown=0)
        settings["keys"]["quit"] = "x"
        config.save(settings, self.path)
        self.assertEqual(config.load(self.path), settings)

    def test_corrupt_file_falls_back(self):
        self.write("{garbage")
        self.assertEqual(config.load(self.path), config.defaults())
        self.write("[1, 2]")
        self.assertEqual(config.load(self.path), config.defaults())

    def test_out_of_range_values_are_clamped(self):
        self.write(f'{{"station": {len(STATIONS) + 1}, "volume": 500}}')
        self.assertEqual((config.load(self.path)["station"], config.load(self.path)["volume"]), (1, 100))

    def test_bad_values_keep_their_default_only(self):
        self.write(json.dumps({"volume": 30, "visualizer": "lasers", "quote_minutes": "soon", "keys": 5}))
        settings = config.load(self.path)
        self.assertEqual(settings, dict(config.defaults(), volume=30))

    def test_keys_merge_over_defaults_and_reject_clashes(self):
        self.write(json.dumps({"keys": {"quit": "x", "nonsense": "y", "mute": "5"}}))
        self.assertEqual(config.load(self.path)["keys"], dict(keys.DEFAULTS, quit="x"))
        self.write(json.dumps({"keys": {"quit": "m"}}))  # m is already mute
        self.assertEqual(config.load(self.path)["keys"], keys.DEFAULTS)


if __name__ == "__main__":
    unittest.main()
