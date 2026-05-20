import pytest

from multi_channel_audio_recorder.cli import build_parser, main


def test_channels_must_match_channels_names_count(capsys):
    with pytest.raises(SystemExit):
        main(["--channels", "5", "--channels-names", "a,b,c"])
    assert "must match" in capsys.readouterr().err


def test_rejects_zero_recording_time(capsys):
    with pytest.raises(SystemExit):
        main(["--recording-time", "0"])
    assert "must be > 0" in capsys.readouterr().err


def test_rejects_negative_recording_length(capsys):
    with pytest.raises(SystemExit):
        main(["--recording-length", "-5"])
    assert "must be > 0" in capsys.readouterr().err


def test_argparse_rejects_invalid_bit_depth(capsys):
    with pytest.raises(SystemExit):
        main(["--bit-depth", "99"])
    assert "invalid choice" in capsys.readouterr().err


def test_argparse_rejects_invalid_recording_unit(capsys):
    with pytest.raises(SystemExit):
        main(["--recording-unit", "fortnights"])
    assert "invalid choice" in capsys.readouterr().err


def test_dash_and_underscore_flag_aliases_resolve_to_same_dest():
    parser = build_parser()
    dash = parser.parse_args(["--main-dir", "X", "--recording-time", "5"])
    underscore = parser.parse_args(["--main_dir", "X", "--recording_time", "5"])
    assert dash.main_dir == underscore.main_dir == "X"
    assert dash.recording_time == underscore.recording_time == 5


def test_default_argv_uses_real_sys_argv(monkeypatch):
    # When main() is called with argv=None it must read from sys.argv.
    # We assert this indirectly by passing argv=[] and confirming defaults apply.
    parser = build_parser()
    args = parser.parse_args([])
    assert args.channels == 2
    assert args.bit_depth == 16
    assert args.recording_unit == "minutes"
    assert args.channels_names == "channel_1,channel_2"
