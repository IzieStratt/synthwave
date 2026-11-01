import unittest

from synthwave import ui


class Screen:
    """Just enough of a curses window: queued key codes."""
    def __init__(self, keys):
        self.keys = [ord(c) for c in keys]

    def getch(self):
        return self.keys.pop(0) if self.keys else -1

    def nodelay(self, flag):
        pass


class Mouse(unittest.TestCase):
    def test_click_on_button(self):  # button spans columns 87..97 (0-based) at width 100, row 1
        self.assertTrue(ui.on_button("[<0;88;2M", 100))
        self.assertTrue(ui.on_button("[<0;98;2M", 100))

    def test_misses(self):
        self.assertFalse(ui.on_button("[<0;87;2M", 100))  # just left of it
        self.assertFalse(ui.on_button("[<0;90;3M", 100))  # row below
        self.assertFalse(ui.on_button("[<0;90;2m", 100))  # release
        self.assertFalse(ui.on_button("[<2;90;2M", 100))  # right button
        self.assertFalse(ui.on_button("", 100))  # a bare Esc key

    def test_read_escape_stops_at_the_end_of_the_sequence(self):
        scr = Screen("[<0;90;2Mq")
        self.assertEqual(ui.read_escape(scr), "[<0;90;2M")
        self.assertEqual(scr.getch(), ord("q"))
        self.assertEqual(ui.read_escape(Screen("")), "")


if __name__ == "__main__":
    unittest.main()
