import datetime

from multi_channel_audio_recorder.recorder import make_filename


def test_iso_format_with_millisecond_precision():
    when = datetime.datetime(2026, 5, 20, 14, 32, 15, 123456)
    assert make_filename("left", "_channel_", when) == "left_channel_2026-05-20T14-32-15-123.wav"


def test_no_colon_in_filename_for_windows():
    when = datetime.datetime(2026, 5, 20, 14, 32, 15)
    assert ":" not in make_filename("ch", "_", when)


def test_custom_suffix_is_inserted_verbatim():
    when = datetime.datetime(2026, 1, 1, 0, 0, 0)
    assert make_filename("boom", "-take-", when).startswith("boom-take-")


def test_filenames_at_same_instant_collide_by_design():
    # Same datetime → same filename. Callers rely on this so all channels of one
    # segment share a timestamp (you can pair left/right by name lookup).
    when = datetime.datetime(2026, 5, 20, 14, 32, 15, 500000)
    assert make_filename("left", "_ch_", when) == make_filename("left", "_ch_", when)
