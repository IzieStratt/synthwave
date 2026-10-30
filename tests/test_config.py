import os, tempfile, unittest

from synthwave import config
from synthwave.stations import STATIONS


class ConfigTest(unittest.TestCase):
    def setUp(self):
        self.path = os.path.join(tempfile.mkdtemp(), "nested", "synthwave.json")

    def test_defaults_when_missing(self):
        self.assertEqual(config.load(self.path), (0, 100))

    def test_round_trip(self):
        config.save(3, 40, self.path)
        self.assertEqual(config.load(self.path), (3, 40))

    def test_corrupt_file_falls_back(self):
        config.save(3, 40, self.path)
        with open(self.path, "w") as f:
            f.write("{garbage")
        self.assertEqual(config.load(self.path), (0, 100))

    def test_out_of_range_values_are_clamped(self):
        os.makedirs(os.path.dirname(self.path))
        with open(self.path, "w") as f:
            f.write(f'{{"station": {len(STATIONS) + 1}, "volume": 500}}')
        self.assertEqual(config.load(self.path), (1, 100))


if __name__ == "__main__":
    unittest.main()
