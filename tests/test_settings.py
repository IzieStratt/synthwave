import curses, unittest

from synthwave import config, keys
from synthwave.settings import ROWS, Menu


def menu_at(kind, field):
    menu = Menu(config.defaults())
    menu.row = ROWS.index(next(r for r in ROWS if r[:2] == (kind, field)))
    return menu


class MenuTest(unittest.TestCase):
    def test_cycles_choices_both_ways(self):
        menu = menu_at("choice", "visualizer")
        self.assertEqual(menu.on_key(curses.KEY_RIGHT), "visualizer")
        self.assertEqual(menu.settings["visualizer"], "decorative")
        menu.on_key(curses.KEY_LEFT)
        menu.on_key(curses.KEY_LEFT)
        self.assertEqual(menu.settings["visualizer"], "off")

    def test_rebind_swaps_with_the_old_owner(self):
        menu = menu_at("key", "quote")
        menu.on_key(10)  # enter: wait for a key
        self.assertIsNone(menu.on_key(ord("1")))  # digits are reserved, still waiting
        self.assertEqual(menu.on_key(ord("m")), "keys")
        self.assertEqual((menu.settings["keys"]["quote"], menu.settings["keys"]["mute"]), ("m", "n"))
        self.assertFalse(menu.capturing)

    def test_esc_cancels_a_rebind_then_closes(self):
        menu = menu_at("key", "quit")
        menu.on_key(10)
        self.assertIsNone(menu.on_key(keys.ESC))
        self.assertEqual(menu.settings["keys"], keys.DEFAULTS)
        self.assertTrue(menu.open)
        menu.on_key(keys.ESC)
        self.assertFalse(menu.open)

    def test_reset_and_wraparound(self):
        menu = menu_at("reset", "keys")
        menu.settings["keys"]["quit"] = "x"
        self.assertEqual(menu.on_key(10), "keys")
        self.assertEqual(menu.settings["keys"], keys.DEFAULTS)
        menu.on_key(curses.KEY_DOWN)
        self.assertEqual(menu.row, 0)


if __name__ == "__main__":
    unittest.main()
