![Git banner PyAudio Multi-Channel Recorder](https://github.com/Tomlevron/multi-channel-audio-recorder/assets/54799120/c2264de4-dc82-4eb6-af07-34d728ff7d03)

# PyAudio Multi-Channel Recorder

Welcome to the PyAudio Multi-Channel Recorder repository. This utility is designed to record audio from multiple channels simultaneously using the PyAudio library. It comes with the ability to save backup recordings, define recording durations, and a command-line interface to customize various parameters. Moreover, you can break the total recording time into smaller recording durations.
This simple code is versatile and can be used with different recorders connected to a computer via USB. In the past, I've personally used this with a ZOOM H5n recorder, which worked well.
## Features

- Detection and selection of the input device.
- Audio recording in manageable chunks for a user-defined duration.
- Splitting of the incoming data into distinct channels.
- Storing each channel's audio data in individual .wav files in a primary directory and a backup directory.
- Comprehensive file naming based on the channel name, current time, and date.
- Organization of files in date-specific folders within both primary and backup directories.
- Command-line interface for customizing various parameters.

## Requirements

- Python 3.9 or above
- [pyaudio](https://pypi.org/project/PyAudio/) ≥ 0.2.14 (ships prebuilt wheels for Windows and macOS — no C compiler needed)
- [numpy](https://pypi.org/project/numpy/) ≥ 1.21

## Installation

```shell
git clone https://github.com/Tomlevron/multi-channel-audio-recorder.git
cd multi-channel-audio-recorder
pip install .
```

This installs a `multi-channel-record` console command you can invoke from anywhere. You can also run the package directly with `python -m multi_channel_audio_recorder ...`.

> On Linux, PyAudio still requires the PortAudio system library first: `sudo apt install portaudio19-dev` (or equivalent). Windows and macOS users normally don't need any system packages because pyaudio 0.2.14+ ships prebuilt wheels.

### Development install

```shell
pip install -e .[dev]
pytest
```

Editable mode reflects code changes immediately. The `[dev]` extra pulls in pytest for the test suite under `tests/`.

## Usage

1. Plug in your audio interface or USB recorder.

2. List the input devices your computer can see:

```shell
multi-channel-record --list-devices
# equivalently:
python -m multi_channel_audio_recorder --list-devices
```

Output looks like:
```
  id= 0  channels= 2  rate=44100  name=Microsoft Sound Mapper - Input
  id= 5  channels= 4  rate=48000  name=ZOOM H6
```
Note the `id` of your recorder and the number of input channels it exposes.

3. Run a recording. Example: 2 minutes from device 5, 4 channels, 30-second files, 24-bit / 48 kHz:

```shell
multi-channel-record \
  --device-id 5 \
  --channels 4 \
  --channels-names boom1,boom2,boom3,boom4 \
  --sample-rate 48000 \
  --bit-depth 24 \
  --recording-unit minutes \
  --recording-time 2 \
  --recording-length 30
```

Press Ctrl+C at any time — audio captured so far in the current segment is flushed to disk before the program exits.

Files are named `boom1_channel_2026-05-20T19-51-19-966.wav` (ISO-8601 timestamp, millisecond precision) and placed under a date-named subfolder inside both `--main-dir` and `--backup-dir`.

### Command-line flags

| Flag | Purpose |
|------|---------|
| `--list-devices` | Print all input devices and exit. Use this first to find your `--device-id`. |
| `--device-id N` | Record from device N. If omitted, you will be prompted interactively. |
| `--channels N` | Number of channels to record. Must be ≤ the device's max input channels. |
| `--channels-names a,b,c` | Comma-separated channel names. Count must equal `--channels`. |
| `--sample-rate HZ` | Sample rate in Hz (e.g. `48000`). Defaults to the device's reported rate. |
| `--bit-depth {16,24,32}` | Sample width in bits. Defaults to 16. |
| `--recording-unit {seconds,minutes,hours}` | Unit for `--recording-time`. Defaults to `minutes`. |
| `--recording-time N` | Total duration in `--recording-unit`. |
| `--recording-length N` | Length of each individual WAV file in seconds. If totals don't divide evenly, a final shorter file is recorded instead of dropping the remainder. |
| `--main-dir DIR` | Primary save directory (default `data`). |
| `--backup-dir DIR` | Backup directory; every file is written here too (default `backup`). |
| `--suffix STR` | Suffix inserted between channel name and timestamp (default `_channel_`). |

> The legacy underscore-style flags (`--main_dir`, `--recording_time`, `--channels_names`, …) are still accepted for back-compatibility with older invocations.

## Recipes

The right `--channels` value depends on **how your device exposes itself to the computer over USB**, not on how many physical inputs the device has. Many portable field recorders (e.g. **Zoom H4n**, **Zoom H5**) only present a 2-channel stereo stream in USB Audio Interface mode regardless of how many XLR inputs they have — for true multi-channel recording on those, record to SD card instead. Always run `--list-devices` first to confirm what your device actually advertises.

**Stereo USB recorder (Zoom H4n / H5 / consumer USB mic):**
```shell
multi-channel-record --device-id <id> --channels 2 --channels-names left,right \
  --sample-rate 48000 --bit-depth 24 --recording-unit minutes --recording-time 10
```

**4-channel recorder (Zoom H6 in multi-track USB mode, Tascam DR-680 mkII):**
```shell
multi-channel-record --device-id <id> --channels 4 \
  --channels-names xlr1,xlr2,xlr3,xlr4 \
  --sample-rate 48000 --bit-depth 24 --recording-unit minutes --recording-time 30
```

**USB mixer or interface with 8+ inputs (Behringer XR18, Focusrite Scarlett 18i20, MOTU 828):**
```shell
multi-channel-record --device-id <id> --channels 8 \
  --channels-names ch1,ch2,ch3,ch4,ch5,ch6,ch7,ch8 \
  --sample-rate 48000 --bit-depth 24 --recording-unit minutes --recording-time 60
```

If you request more channels than the device supports, you'll get a clear error telling you the maximum.

## Project layout

```
src/multi_channel_audio_recorder/
├── __init__.py     # re-exports Recorder, DirectoryManager, __version__
├── __main__.py     # entry point for `python -m multi_channel_audio_recorder`
├── cli.py          # argparse + main()
├── recorder.py     # Recorder class, list_input_devices(), pure helpers
└── paths.py        # DirectoryManager
tests/              # pytest unit tests (no audio hardware required)
```

## To do
- [x] Add Code comments and docstrings
- [x] Add installation instructions
- [x] Explain what can be done with it
- [x] Add unit tests to ensure the functionality of the code.
- [x] Add an example section demonstrating different usage scenarios
- [ ] Incorporate logging to track the progress and errors during recording.
- [x] Provide detailed documentation on the usage of the command-line interface.
## Contact

If you have any questions, suggestions, or feedback regarding this project, please feel free to reach out to me. You can contact me at:

- Name: Tom Lev-ron
- Email: tomseaherb@gmail.com
- LinkedIn: [Tom](https://www.linkedin.com/in/tomlev-ron/)
