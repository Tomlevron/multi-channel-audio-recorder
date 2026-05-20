from __future__ import annotations

import argparse
import sys

from multi_channel_audio_recorder.paths import DirectoryManager
from multi_channel_audio_recorder.recorder import Recorder, list_input_devices


def build_parser() -> argparse.ArgumentParser:
    """Construct the argparse parser. Dash and underscore aliases coexist for back-compat."""
    parser = argparse.ArgumentParser(
        prog="multi-channel-record",
        description="Multi-channel audio recorder",
    )
    parser.add_argument(
        "--list-devices",
        action="store_true",
        help="List input-capable audio devices and exit.",
    )
    parser.add_argument(
        "--device-id",
        type=int,
        default=None,
        help="Input device id to record from. If omitted, you will be prompted.",
    )
    # Each of the following accepts both --foo-bar (new) and --foo_bar (legacy).
    parser.add_argument(
        "--main-dir", "--main_dir",
        dest="main_dir", default="data",
        help="Main directory for saving recordings",
    )
    parser.add_argument(
        "--backup-dir", "--backup_dir",
        dest="backup_dir", default="backup",
        help="Backup directory for saving recordings",
    )
    parser.add_argument(
        "--recording-unit", "--recording_unit",
        dest="recording_unit", default="minutes",
        choices=["seconds", "minutes", "hours"],
        help="Unit of --recording-time",
    )
    parser.add_argument(
        "--recording-time", "--recording_time",
        dest="recording_time", type=int, default=1,
        help="Total recording duration, expressed in --recording-unit",
    )
    parser.add_argument(
        "--recording-length", "--recording_length",
        dest="recording_length", type=int, default=60,
        help="Length of each individual WAV file, in seconds",
    )
    parser.add_argument(
        "--channels-names", "--channels_names",
        dest="channels_names", default="channel_1,channel_2",
        help="Comma-separated channel names (count must match --channels)",
    )
    parser.add_argument(
        "--channels",
        type=int, default=2,
        help="Number of audio channels to record",
    )
    parser.add_argument(
        "--sample-rate",
        type=int, default=None,
        help="Sample rate in Hz. If omitted, uses the device default.",
    )
    parser.add_argument(
        "--bit-depth",
        type=int, default=16, choices=[16, 24, 32],
        help="Bit depth per sample (default 16).",
    )
    parser.add_argument(
        "--suffix",
        default="_channel_",
        help="Suffix appended to the per-channel filename",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.list_devices:
        list_input_devices()
        return 0

    if args.recording_time <= 0:
        parser.error("--recording-time must be > 0")
    if args.recording_length <= 0:
        parser.error("--recording-length must be > 0")

    channels_names = args.channels_names.split(",")
    if len(channels_names) != args.channels:
        parser.error(
            f"--channels={args.channels} but --channels-names has {len(channels_names)} "
            f"name(s): {channels_names}. They must match."
        )

    dir_manager = DirectoryManager(main_dir=args.main_dir, backup_dir=args.backup_dir)
    print(f"Main save path:   {dir_manager.main_save_path}")
    print(f"Backup save path: {dir_manager.backup_path}")

    try:
        recorder = Recorder(
            channels=args.channels,
            device_id=args.device_id,
            sample_rate=args.sample_rate,
            bit_depth=args.bit_depth,
            main_save_path=dir_manager.main_save_path,
            backup_path=dir_manager.backup_path,
            suffix=args.suffix,
        )
        recorder.start_recording(
            args.recording_time,
            args.recording_length,
            channels_names,
            time_unit=args.recording_unit,
        )
    except KeyboardInterrupt:
        print("\nStopped by user.")
        return 130
    except (ValueError, RuntimeError, OSError) as e:
        print(f"Error: {e}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
