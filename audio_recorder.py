import os
import sys
import wave
import pyaudio
import numpy as np
import time
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
        sample_format: PyAudio sample format. Defaults to pyaudio.paInt16.
        channels: Number of audio channels to record. Must be <= the device's maxInputChannels.
        chunk: Frames-per-buffer for the PyAudio stream read.
        device_id: Input device index. If None, the user is prompted interactively.
        main_save_path: Primary directory for saving WAV files.
        backup_path: Backup directory; each recording is also written here.
        suffix: Suffix appended after each channel name in the filename.

    Raises:
        ValueError: If device_id is invalid or supports fewer channels than requested.
        RuntimeError: If no input devices are present (interactive path only).
    """
    def __init__(self, sample_format=pyaudio.paInt16, channels=2, chunk=1024, device_id=None, main_save_path=None, backup_path=None, suffix='_channel_'):
        # Initialize
        self.sample_format = sample_format
        self.channels = channels
        self.chunk = chunk
        self.frames = [[] for _ in range(channels)]
        self.p = pyaudio.PyAudio()
        if device_id is None:
            self.input_device_index = self.prompt_for_input_device()
        else:
            self.input_device_index = device_id
        # Check that the device exists and can supply the requested channel count.
        device_info = self.get_device_info(self.input_device_index)
        max_in = int(device_info["maxInputChannels"])
        if max_in < self.channels:
            raise ValueError(
                f"Device id={self.input_device_index} ({device_info['name']}) "
                f"supports max {max_in} input channels, but {self.channels} were requested. "
                f"Run with --list-devices to see options."
            )
        self.fs = int(device_info["defaultSampleRate"])
        print(f"Using device id={self.input_device_index} ({device_info['name']}) "
              f"at {self.fs} Hz, {self.channels} channel(s).")
        self.main_save_path = main_save_path
        self.backup_path = backup_path
        self.suffix = suffix  # Added suffix
        
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
        """Record audio for the specified length of time.

        Args:
            rec_length (int): The length of time to record in seconds.

        Raises:
            Exception: If the number of channels is invalid.

        """
        if self.channels < 1:
            raise Exception(f'Invalid number of channels: {self.channels}')
        print('Recording')
        self.frames = [[] for _ in range(self.channels)]  # Clear frames
        stream = self.p.open(format=self.sample_format,
                            channels=self.channels,
                            rate=self.fs,
                            input_device_index=self.input_device_index,
                            frames_per_buffer=self.chunk,
                            input=True)

        for i in range(0, int(self.fs / self.chunk * rec_length)):
            data = stream.read(self.chunk)
            data_array = np.frombuffer(data, dtype='int16')  # Use frombuffer instead of fromstring
            for j in range(self.channels):
                channel = data_array[j::self.channels]
                data_str = channel.tobytes()  # Use tobytes instead of tostring
                self.frames[j].append(data_str)

        stream.stop_stream()
        stream.close()
        print('Finished recording')


    def save_wav(self, filename, frames, date_as_string, time_as_string, directory_path):
        """Save audio frames as a WAV file.

        Args:
            filename (str): The base filename for the WAV file.
            frames (list): The audio frames to be saved.
            date_as_string (str): The current date as a string.
            time_as_string (str): The current time as a string.
            directory_path (str): The directory path for saving the WAV file.

        """
        name_of_file = filename + time_as_string.replace('.', '') + '.wav'
        directory = directory_path + date_as_string
        if not os.path.isdir(directory):
            os.makedirs(directory)

        complete_name = os.path.join(directory, name_of_file)

        wf = wave.open(complete_name, 'wb')
        wf.setnchannels(1)
        wf.setsampwidth(self.p.get_sample_size(self.sample_format))
        wf.setframerate(self.fs)
        wf.writeframes(b''.join(frames))
        wf.close()

    def record_and_save(self, rec_length, rooms_names):
        """Record audio and save the WAV files for each room.

        Args:
            rec_length (int): The length of time to record in seconds.
            rooms_names (list): The names of the rooms to record.

        """

        self.record_audio(rec_length)
        current_time = str(time.time())
        date_today = datetime.datetime.now()
        date_str = str(date_today.date())

        for i, name in enumerate(rooms_names):
            self.save_wav(name +  self.suffix, self.frames[i], date_str, current_time, self.main_save_path)
            self.save_wav(name +  self.suffix, self.frames[i], date_str, current_time, self.backup_path)
        
    def start_recording(self, num_rec, recording_length, rooms_names, time_unit="seconds"):
        """Start recording audio for the specified duration and convert num_rec to the appropriate time unit.

        Args:
            num_rec (int): The total number of recordings to perform.
            recording_length (int): The length of each individual recording.
            rooms_names (list): The names of the rooms to record.
            time_unit (str): The unit of recording time (default: "seconds").

        """
        if time_unit == "minutes":
            num_rec *= 60
        elif time_unit == "hours":
            num_rec *= 3600

        num_loops = num_rec // recording_length  # Calculate the number of loops needed
        for k in range(num_loops):
            print('This is recording number :', k + 1)
            self.record_and_save(rec_length=recording_length, rooms_names=rooms_names)
        self.p.terminate()  # Terminate PyAudio session after loop

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
    parser.add_argument('--suffix', default='_channel_',
                        help='Suffix appended to the per-channel filename')
    args = parser.parse_args()

    if args.list_devices:
        list_input_devices()
        sys.exit(0)

    channels_names = args.channels_names.split(',')
    if len(channels_names) != args.channels:
        parser.error(
            f"--channels={args.channels} but --channels_names has {len(channels_names)} "
            f"name(s): {channels_names}. They must match."
        )

    dir_manager = DirectoryManager(main_dir=args.main_dir, backup_dir=args.backup_dir)
    print(f"Main save path:   {dir_manager.main_save_path}")
    print(f"Backup save path: {dir_manager.backup_path}")

    recorder = Recorder(
        channels=args.channels,
        device_id=args.device_id,
        main_save_path=dir_manager.main_save_path,
        backup_path=dir_manager.backup_path,
        suffix=args.suffix,
    )
    try:
        recorder.start_recording(args.recording_time, args.recording_length, channels_names,
                                 time_unit=args.recording_unit)
    except Exception as e:
        print(f"An error of type {type(e).__name__} occurred: {e}")