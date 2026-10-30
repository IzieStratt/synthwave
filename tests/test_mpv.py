import unittest

from synthwave.mpv import parse


class ParseTest(unittest.TestCase):
    def test_keeps_partial_line_for_next_read(self):
        msgs, rest = parse(b'{"event":"pause"}\n{"data":1}\n{"par')
        self.assertEqual(msgs, [{"event": "pause"}, {"data": 1}])
        self.assertEqual(rest, b'{"par')
        self.assertEqual(parse(rest + b'tial":true}\n'), ([{"partial": True}], b""))

    def test_empty(self):
        self.assertEqual(parse(b""), ([], b""))


if __name__ == "__main__":
    unittest.main()
