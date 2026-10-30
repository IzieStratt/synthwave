"""Lofi Girl live streams as (tab name, YouTube video ID).

Lofi Girl restarts streams now and then, which changes their IDs. When a station shows
"stream unavailable", grab the new ID from https://www.youtube.com/@LofiGirl/streams.
"""

STATIONS = (
    ("synthwave", "4xDzrJKXOOY"),
    ("lofi", "rFZHOHl-L8A"),
    ("sleep", "JD-kMIpDfnY"),
    ("jazz", "E2vONfzoyRI"),
    ("house", "3PFJ9SETS4M"),
    ("rainy", "CwPCy1GLS38"),
    ("ambient", "GSfT7H87zq4"),
    ("dark", "S_MOd40zlYU"),
)


def url(station):
    return f"https://www.youtube.com/watch?v={STATIONS[station][1]}"
