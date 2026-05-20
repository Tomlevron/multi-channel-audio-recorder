from multi_channel_audio_recorder.recorder import compute_segment_lengths


def test_no_remainder_splits_evenly():
    assert compute_segment_lengths(60, 30) == [30, 30]


def test_remainder_becomes_final_short_segment():
    assert compute_segment_lengths(90, 60) == [60, 30]


def test_total_smaller_than_segment_gives_one_short():
    assert compute_segment_lengths(10, 60) == [10]


def test_zero_total_is_empty():
    assert compute_segment_lengths(0, 60) == []


def test_exact_single_segment():
    assert compute_segment_lengths(60, 60) == [60]


def test_three_full_plus_remainder():
    assert compute_segment_lengths(125, 30) == [30, 30, 30, 30, 5]
