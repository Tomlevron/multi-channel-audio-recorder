from __future__ import annotations

import datetime
import wave
from pathlib import Path

import numpy as np
import pyaudio


def list_input_devices() -> None:
    """Print every input-capable device and its channel count."""
    p = pyaudio.PyAudio()
    try:
        found = False
        for i in range(p.get_device_count()):
            info = p.get_device_info_by_index(i)
            if info["maxInputChannels"] > 0:
                found = True
                print(
                    f"  id={i:>2}  channels={int(info['maxInputChannels']):>2}  "
                    f"rate={int(info['defaultSampleRate'])}  name={info['name']}"
                )
        if not found:
            print("No input-capable devices detected.")
    finally:
        p.terminate()


def compute_segment_lengths(total_seconds: int, segment_length: int) -> list[int]:
    """Split total_seconds into segments of segment_length, plus a final remainder.

    A short tail segment is returned instead of being silently dropped — this is the
    behavior callers should rely on to record every requested second of audio.
    """
    full, remainder = divmod(total_seconds, segment_length)
    segments = [segment_length] * full
    if remainder:
        segments.append(remainder)
    return segments


def make_filename(channel_name: str, suffix: str, when: datetime.datetime) -> str:
    """Build an ISO-8601 timestamped WAV filename safe on Windows (no ':' in the name)."""
    timestamp = when.strftime("%Y-%m-%dT%H-%M-%S-%f")[:-3]
    return f"{channel_name}{suffix}{timestamp}.wav"


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

    def __init__(
        self,
        channels: int = 2,
        chunk: int = 1024,
        device_id: int | None = None,
        sample_rate: int | None = None,
        bit_depth: int = 16,
        main_save_path: str | Path | None = None,
        backup_path: str | Path | None = None,
        suffix: str = "_channel_",
    ) -> None:
        if bit_depth not in self._BIT_DEPTH_FORMATS:
            raise ValueError(
                f"Unsupported bit_depth={bit_depth}; choose from {sorted(self._BIT_DEPTH_FORMATS)}"
            )
        self.sample_format: int = self._BIT_DEPTH_FORMATS[bit_depth]
        self.bit_depth: int = bit_depth
        self.channels: int = channels
        self.chunk: int = chunk
        self.frames: list[list[bytes]] = [[] for _ in range(channels)]
        self.interrupted: bool = False
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
        self.fs: int = (
            sample_rate if sample_rate is not None else int(device_info["defaultSampleRate"])
        )
        print(
            f"Using device id={self.input_device_index} ({device_info['name']}) "
            f"at {self.fs} Hz, {self.channels} channel(s), {self.bit_depth}-bit."
        )
        self.main_save_path: Path | None = Path(main_save_path) if main_save_path else None
        self.backup_path: Path | None = Path(backup_path) if backup_path else None
        self.suffix: str = suffix

    def prompt_for_input_device(self) -> int:
        """List input devices and prompt the user to pick one."""
        valid_indexes: list[int] = []
        for i in range(self.p.get_device_count()):
            info = self.p.get_device_info_by_index(i)
            if info["maxInputChannels"] > 0:
                valid_indexes.append(i)
                print(
                    f"  id={i:>2}  channels={int(info['maxInputChannels']):>2}  "
                    f"rate={int(info['defaultSampleRate'])}  name={info['name']}"
                )

        if not valid_indexes:
            raise RuntimeError("No input-capable audio devices found.")

        while True:
            choice = input("Enter the ID of the preferred input device: ")
            if choice.isdigit() and int(choice) in valid_indexes:
                return int(choice)
            print(f"Invalid device ID: {choice}. Please try again.")

    def get_device_info(self, index: int) -> dict:
        try:
            return self.p.get_device_info_by_index(index)
        except OSError as exc:
            raise ValueError(
                f"Invalid device id={index}. Run with --list-devices to see valid ids."
            ) from exc

    def record_audio(self, rec_length: int) -> None:
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

    def save_wav(self, filename: str, frames: list[bytes], directory: Path) -> None:
        """Write a single mono WAV file under `directory` (created if missing)."""
        directory.mkdir(parents=True, exist_ok=True)
        path = directory / filename
        with wave.open(str(path), "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(self.p.get_sample_size(self.sample_format))
            wf.setframerate(self.fs)
            wf.writeframes(b"".join(frames))

    def record_and_save(self, rec_length: int, channel_names: list[str]) -> None:
        """Record one segment and write each channel to the main + backup dirs."""
        self.record_audio(rec_length)
        now = datetime.datetime.now()
        date_folder = now.strftime("%Y-%m-%d")
        for i, name in enumerate(channel_names):
            filename = make_filename(name, self.suffix, now)
            for save_root in (self.main_save_path, self.backup_path):
                if save_root is None:
                    continue
                self.save_wav(filename, self.frames[i], save_root / date_folder)

    def start_recording(
        self,
        num_rec: int,
        recording_length: int,
        channel_names: list[str],
        time_unit: str = "seconds",
    ) -> None:
        """Record `num_rec` units of audio split into `recording_length`-second segments.

        A final shorter segment is recorded if `num_rec` doesn't divide evenly.
        """
        if time_unit == "minutes":
            num_rec *= 60
        elif time_unit == "hours":
            num_rec *= 3600

        segment_lengths = compute_segment_lengths(num_rec, recording_length)
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
