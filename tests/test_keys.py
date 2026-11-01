import curses, unittest

from synthwave import keys


class KeysTest(unittest.TestCase):
    def test_names_round_trip(self):
        for name in ("space", "left", "up", "q", "?", "Z"):
            self.assertEqual(keys.name(keys.code(name)), name)

    def test_unbindable(self):
        for code in (10, 13, curses.KEY_ENTER, 27, ord("1"), ord("\t"), 300):
            self.assertIsNone(keys.name(code))
        for name in ("3", "enter", "", "qq", None, 5):
            self.assertIsNone(keys.code(name))

    def test_defaults_are_distinct_and_bindable(self):
        self.assertEqual(len(set(keys.DEFAULTS.values())), len(keys.DEFAULTS))
        self.assertTrue(all(keys.code(k) for k in keys.DEFAULTS.values()))
        self.assertEqual(keys.bindings(keys.DEFAULTS)[ord(" ")], "play")


if __name__ == "__main__":
    unittest.main()
