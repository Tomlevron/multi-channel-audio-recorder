import os
import sys
import wave
import pyaudio
import numpy as np
import datetime
import argparse


def list_input_devices():
    """Print every input-capable device and its channel count, then return."""
    p = pyaudio.PyAudio()
    try:
        found = False
        for i in range(p.get_device_count()):
            info = p.get_device_info_by_index(i)
            if info["maxInputChannels"] > 0:
                found = True
                print(f"  id={i:>2}  channels={int(info['maxInputChannels']):>2}  "
                      f"rate={int(info['defaultSampleRate'])}  name={info['name']}")
        if not found:
            print("No input-capable devices detected.")
    finally:
        p.terminate()


class Recorder:
    """Records a multi-channel input stream and writes each channel to its own mono WAV file.

    Args:
        channels: Number of audio channels to record. Must be <= the device's maxInputChannels.
        chunk: Frames-per-buffer for the PyAudio stream read.
        device_id: Input device index. If None, the user is prompted interactively.
        sample_rate: Sample rate in Hz. If None, uses the device's default rate.
        bit_depth: Sample width in bits — 16, 24, or 32. Defaults to 16.
        main_save_path: Primary directory for saving WAV files.
        backup_path: Backup directory; each recording is also written here.
        suffix: Suffix appended after each channel name in the filename.

    Raises:
        ValueError: If device_id is invalid, bit_depth is unsupported, or the device
            supports fewer channels than requested.
        RuntimeError: If no input devices are present (interactive path only).
    """

    _BIT_DEPTH_FORMATS = {16: pyaudio.paInt16, 24: pyaudio.paInt24, 32: pyaudio.paInt32}

    def __init__(self, channels=2, chunk=1024, device_id=None, sample_rate=None, bit_depth=16,
                 main_save_path=None, backup_path=None, suffix='_channel_'):
        if bit_depth not in self._BIT_DEPTH_FORMATS:
            raise ValueError(
                f"Unsupported bit_depth={bit_depth}; choose from {sorted(self._BIT_DEPTH_FORMATS)}"
            )
        self.sample_format = self._BIT_DEPTH_FORMATS[bit_depth]
        self.bit_depth = bit_depth
        self.channels = channels
        self.chunk = chunk
        self.frames = [[] for _ in range(channels)]
        self.interrupted = False
        self.p = pyaudio.PyAudio()
        if device_id is None:
            self.input_device_index = self.prompt_for_input_device()
        else:
            self.input_device_index = device_id
        device_info = self.get_device_info(self.input_device_index)
        max_in = int(device_info["maxInputChannels"])
        if max_in < self.channels:
            raise ValueError(
                f"Device id={self.input_device_index} ({device_info['name']}) "
                f"supports max {max_in} input channels, but {self.channels} were requested. "
                f"Run with --list-devices to see options."
            )
        self.fs = sample_rate if sample_rate is not None else int(device_info["defaultSampleRate"])
        print(f"Using device id={self.input_device_index} ({device_info['name']}) "
              f"at {self.fs} Hz, {self.channels} channel(s), {self.bit_depth}-bit.")
        self.main_save_path = main_save_path
        self.backup_path = backup_path
        self.suffix = suffix
        
    def prompt_for_input_device(self):
        """List input devices and prompt the user to pick one. Returns the chosen device index."""
        valid_indexes = []
        for i in range(self.p.get_device_count()):
            info = self.p.get_device_info_by_index(i)
            if info["maxInputChannels"] > 0:
                valid_indexes.append(i)
                print(f"  id={i:>2}  channels={int(info['maxInputChannels']):>2}  "
                      f"rate={int(info['defaultSampleRate'])}  name={info['name']}")

        if not valid_indexes:
            raise RuntimeError("No input-capable audio devices found.")

        while True:
            choice = input("Enter the ID of the preferred input device: ")
            if choice.isdigit() and int(choice) in valid_indexes:
                return int(choice)
            print(f"Invalid device ID: {choice}. Please try again.")

    def get_device_info(self, index):
        try:
            return self.p.get_device_info_by_index(index)
        except OSError as exc:
            raise ValueError(
                f"Invalid device id={index}. Run with --list-devices to see valid ids."
            ) from exc


    def record_audio(self, rec_length):
        """Record `rec_length` seconds into self.frames (one byte-buffer list per channel).

        On Ctrl+C, captures whatever was read so far, sets self.interrupted, and returns
        without re-raising — callers should check self.interrupted to stop the outer loop.
        """
        if self.channels < 1:
            raise ValueError(f"Invalid number of channels: {self.channels}")
        print(f"Recording {rec_length}s...")
        self.frames = [[] for _ in range(self.channels)]
        sample_width = self.p.get_sample_size(self.sample_format)
        stream = self.p.open(
            format=self.sample_format,
            channels=self.channels,
            rate=self.fs,
            input_device_index=self.input_device_index,
            frames_per_buffer=self.chunk,
            input=True,
        )
        try:
            for _ in range(int(self.fs / self.chunk * rec_length)):
                data = stream.read(self.chunk)
                # De-interleave by byte stride so this works for any sample width (16/24/32).
                frame = np.frombuffer(data, dtype=np.uint8).reshape(-1, self.channels, sample_width)
                for j in range(self.channels):
                    self.frames[j].append(frame[:, j, :].tobytes())
        except KeyboardInterrupt:
            print("\nInterrupted — flushing captured audio so far...")
            self.interrupted = True
        finally:
            stream.stop_stream()
            stream.close()
        print("Finished recording")


    def save_wav(self, filename, frames, directory):
        """Write a single mono WAV file under `directory` (created if missing)."""
        os.makedirs(directory, exist_ok=True)
        path = os.path.join(directory, filename)
        with wave.open(path, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(self.p.get_sample_size(self.sample_format))
            wf.setframerate(self.fs)
            wf.writeframes(b"".join(frames))

    def record_and_save(self, rec_length, channel_names):
        """Record one segment and write each channel to the main + backup dirs."""
        self.record_audio(rec_length)
        now = datetime.datetime.now()
        date_folder = now.strftime("%Y-%m-%d")
        # ISO-8601-ish, ms precision, ':' avoided so the name is valid on Windows.
        timestamp = now.strftime("%Y-%m-%dT%H-%M-%S-%f")[:-3]
        for i, name in enumerate(channel_names):
            filename = f"{name}{self.suffix}{timestamp}.wav"
            for save_root in (self.main_save_path, self.backup_path):
                self.save_wav(filename, self.frames[i], os.path.join(save_root, date_folder))

    def start_recording(self, num_rec, recording_length, channel_names, time_unit="seconds"):
        """Record `num_rec` units of audio split into `recording_length`-second segments.

        A final shorter segment is recorded if `num_rec` doesn't divide evenly, instead
        of silently dropping the remainder.
        """
        if time_unit == "minutes":
            num_rec *= 60
        elif time_unit == "hours":
            num_rec *= 3600

        full_segments, remainder = divmod(num_rec, recording_length)
        segment_lengths = [recording_length] * full_segments
        if remainder:
            segment_lengths.append(remainder)

        if not segment_lengths:
            print("Total recording time is 0; nothing to record.")
            self.p.terminate()
            return

        try:
            total = len(segment_lengths)
            for k, length in enumerate(segment_lengths, 1):
                print(f"Recording segment {k}/{total} ({length}s)")
                self.record_and_save(rec_length=length, channel_names=channel_names)
                if self.interrupted:
                    print(f"Stopped after segment {k}/{total}.")
                    break
        finally:
            self.p.terminate()

class DirectoryManager:
    """Utility class for managing directory paths.

    Args:
        main_dir (str, optional): The main directory name. Defaults to "data".
        backup_dir (str, optional): The backup directory name. Defaults to "backup".

    Attributes:
        current_directory (str): The current working directory.
        main_save_path (str): The full path to the main directory.
        backup_path (str): The full path to the backup directory.

    Methods:
        construct_path(dir_name): Construct the full path for a directory.

    """
    def __init__(self, main_dir="data", backup_dir="backup"):
        self.current_directory = os.getcwd()
        self.main_save_path = self.construct_path(main_dir)
        self.backup_path = self.construct_path(backup_dir)

    def construct_path(self, dir_name):
        """Construct the full path for a directory.

        Args:
            dir_name (str): The name of the directory.

        Returns:
            str: The full path to the directory.

        """
        return os.path.join(self.current_directory, dir_name, '')
    
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Multi-channel audio recorder")
    parser.add_argument('--list-devices', action='store_true',
                        help='List input-capable audio devices and exit.')
    parser.add_argument('--device-id', type=int, default=None,
                        help='Input device id to record from. If omitted, you will be prompted.')
    parser.add_argument('--main_dir', default='data', help='Main directory for saving recordings')
    parser.add_argument('--backup_dir', default='backup', help='Backup directory for saving recordings')
    parser.add_argument('--recording_unit', default='minutes',
                        choices=['seconds', 'minutes', 'hours'],
                        help='Unit of --recording_time')
    parser.add_argument('--recording_time', type=int, default=1,
                        help='Total recording duration, expressed in --recording_unit')
    parser.add_argument('--recording_length', type=int, default=60,
                        help='Length of each individual WAV file, in seconds')
    parser.add_argument('--channels_names', default='channel_1,channel_2',
                        help='Comma-separated channel names (count must match --channels)')
    parser.add_argument('--channels', type=int, default=2,
                        help='Number of audio channels to record')
    parser.add_argument('--sample-rate', type=int, default=None,
                        help='Sample rate in Hz. If omitted, uses the device default.')
    parser.add_argument('--bit-depth', type=int, default=16, choices=[16, 24, 32],
                        help='Bit depth per sample (default 16).')
    parser.add_argument('--suffix', default='_channel_',
                        help='Suffix appended to the per-channel filename')
    args = parser.parse_args()

    if args.list_devices:
        list_input_devices()
        sys.exit(0)

    if args.recording_time <= 0:
        parser.error("--recording_time must be > 0")
    if args.recording_length <= 0:
        parser.error("--recording_length must be > 0")

    channels_names = args.channels_names.split(',')
    if len(channels_names) != args.channels:
        parser.error(
            f"--channels={args.channels} but --channels_names has {len(channels_names)} "
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
        recorder.start_recording(args.recording_time, args.recording_length, channels_names,
                                 time_unit=args.recording_unit)
    except KeyboardInterrupt:
        print("\nStopped by user.")
        sys.exit(130)
    except (ValueError, RuntimeError, OSError) as e:
        print(f"Error: {e}")
        sys.exit(1)