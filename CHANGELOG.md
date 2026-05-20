# Changelog

All notable changes to this project are documented in this file. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] — 2026-05-20

### Added

- **Installable package** via `pyproject.toml`. `pip install .` now provides a `multi-channel-record` console command, and `python -m multi_channel_audio_recorder ...` also works.
- **`src/multi_channel_audio_recorder/` package** split into `cli.py` (argparse + `main()`), `recorder.py` (the `Recorder` class plus pure helpers `compute_segment_lengths` and `make_filename`), `paths.py` (`DirectoryManager`), and `__main__.py`. Re-exports + `__version__` live in `__init__.py`.
- **`--list-devices`** flag — print every input-capable device with its id, channel count, sample rate, and name; exit cleanly.
- **`--device-id N`** flag — record from a specific device without the interactive prompt. The script is now fully non-interactive when given all required flags.
- **`--sample-rate`** and **`--bit-depth`** flags. Bit depth supports 16, 24, and 32, replacing the old hard-coded 16-bit-only behaviour. De-interleaving now runs on raw bytes (`np.frombuffer(data, dtype=np.uint8).reshape(-1, channels, sample_width)`) rather than int16-specific slicing — that's what makes 24-bit work, since `paInt24` has no native numpy dtype.
- **Dash-style flag aliases** (`--main-dir`, `--recording-time`, `--channels-names`, …) alongside the original underscore forms. Both resolve to the same argparse `dest`.
- **`Ctrl+C` flush.** Pressing Ctrl+C during a segment now writes the audio captured up to that point to WAV before exiting (130), instead of dropping it.
- **Final shorter segment** when `--recording-time` doesn't divide evenly into `--recording-length`. Previously the tail was silently discarded.
- **Argparse-time validation**: `--channels` must match `len(--channels-names)`, and `--recording-time` / `--recording-length` must be `> 0`.
- **Channel-count guard** at `Recorder` construction: if you ask for more channels than the device supports, you get `Device id=X (Name) supports max N input channels, but M were requested. Run with --list-devices to see options.` instead of a cryptic PyAudio error.
- **pytest test suite** (17 tests) covering the segment math, ISO filename format, argparse validation, and dash/underscore flag aliasing.
- **`CHANGELOG.md`** (this file).

### Changed

- **Filenames switched** from `<name><suffix><epoch-with-dots-stripped>.wav` to ISO-8601 with millisecond precision, e.g. `boom1_channel_2026-05-20T19-51-19-966.wav`. Sortable, human-readable, and `:` is replaced with `-` so the names are valid on Windows.
- **Error handling**: `main()` now catches `KeyboardInterrupt` (exit 130) and `(ValueError, RuntimeError, OSError)` (exit 1) with a one-line message instead of letting tracebacks reach the terminal.
- **Path handling** uses `pathlib.Path` throughout. `DirectoryManager` returns `Path` objects; `Recorder.save_wav` accepts a `Path` and creates parents with `mkdir(parents=True, exist_ok=True)`.
- **Type hints** on all public APIs (`Recorder`, `DirectoryManager`, `main`, `build_parser`, helpers).
- **Python version** floor raised to 3.9 (EOL Oct 2025 — still supported, and required for the modern type-hint syntax used in the package).
- **`pyaudio` unpinned** from `==0.2.11` to `>=0.2.14`. The newer version ships prebuilt wheels for Windows and macOS, so `pip install` no longer needs PortAudio system headers + a C compiler on those platforms.

### Removed

- **`audio_recorder.py`** at the repo root — replaced by the `src/multi_channel_audio_recorder/` package. Use `multi-channel-record` (console script) or `python -m multi_channel_audio_recorder` (module entry) instead.
- **Dead interactive directory prompts** in the old `__main__` block (they collected `main_dir_input` / `backup_dir_input` and then discarded them in favour of `args.main_dir` / `args.backup_dir`).
- **`wave` and `argparse` from `requirements.txt`** — both are in the Python standard library and were never real dependencies.
- **`sample_format` constructor argument** on `Recorder` — replaced by the higher-level `bit_depth` (16/24/32).
