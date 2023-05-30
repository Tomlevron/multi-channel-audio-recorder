import os
import wave
import pyaudio
import numpy as np
import time
import datetime
import argparse

class Recorder:
    """Audio recorder utility.

    Args:
        sample_format (int, optional): The sample format for audio recording. Defaults to pyaudio.paInt16.
        channels (int, optional): The number of audio channels to record. Defaults to 2.
        chunk (int, optional): The chunk size for audio recording. Defaults to 1024.
        choice (bool, optional): Flag indicating whether to prompt for input device selection. Defaults to False.
        main_save_path (str, optional): The main directory path for saving audio recordings. Defaults to None.
        backup_path (str, optional): The backup directory path for saving audio recordings. Defaults to None.
        suffix (str, optional): The suffix to append to the filename of the recordings. Defaults to '_channel_'.

    Raises:
        Exception: If the input device ID is invalid.

    Attributes:
        sample_format (int): The sample format for audio recording.
        channels (int): The number of audio channels to record.
        chunk (int): The chunk size for audio recording.
        frames (list): A list to store audio frames for each channel.
        p (pyaudio.PyAudio): The PyAudio instance.
        choice (bool): Flag indicating whether to prompt for input device selection.
        input_device_index (int): The index of the selected input device.
        fs (int): The sample rate of the input device.
        main_save_path (str): The main directory path for saving audio recordings.
        backup_path (str): The backup directory path for saving audio recordings.
        suffix (str): The suffix to append to the filename of the recordings.

    Methods:
        get_input_device_index(): Prompt the user to select an input device and return its index.
        validate_device_index(index): Validate if the provided device index is valid.
        get_device_sample_rate(): Get the sample rate of the selected input device.
        record_audio(rec_length): Record audio for the specified length of time.
        save_wav(filename, frames, date_as_string, time_as_string, directory_path): Save audio frames as a WAV file.
        record_and_save(rec_length, rooms_names): Record audio and save the WAV files for each room.
        start_recording(num_rec, recording_length, rooms_names, time_unit): Start recording audio for the specified duration.

    """
    def __init__(self, sample_format=pyaudio.paInt16, channels=2, chunk=1024, choice=False, main_save_path=None, backup_path=None, suffix='_channel_'):
        # Initialize 
        self.sample_format = sample_format
        self.channels = channels
        self.chunk = chunk
        self.frames = [[] for _ in range(channels)]
        self.p = pyaudio.PyAudio()
        self.choice = choice
        self.input_device_index = self.get_input_device_index()
        # Check if device index is valid
        if not self.validate_device_index(self.input_device_index):
            raise Exception(f'Invalid device ID: {self.input_device_index}')
        self.fs = self.get_device_sample_rate()
        self.main_save_path = main_save_path
        self.backup_path = backup_path
        self.suffix = suffix  # Added suffix
        
    def get_input_device_index(self):
        """Prompt the user to select an input device and return its index.

        Returns:
            int: The index of the selected input device.

        Raises:
            Exception: If no input devices are found or the selected device ID is invalid.

        """
        valid_indexes = []
        for i in range(self.p.get_device_count()):
            device_info = self.p.get_device_info_by_index(i)
            if (device_info["maxInputChannels"]) > 0:
                valid_indexes.append(i)
                print("Input Device id ", i, " - ", device_info["name"])
                print(f"Input Device id {i} - {device_info['name']} - Channels: {device_info['maxInputChannels']}")

        if not valid_indexes:
            raise Exception('No device found')
        
        if self.choice:
            while True:
                choice = input("Enter the ID of the preferred input device: ")
                if choice.isdigit() and int(choice) in valid_indexes:
                    return int(choice)
                print(f'Invalid device ID: {choice}. Please try again.')
        else:
            return valid_indexes[0]  # Return the first valid index
        
    def validate_device_index(self, index):
        """Validate if the provided device index is valid.

        Args:
            index (int): The device index to validate.

        Returns:
            bool: True if the device index is valid, False otherwise.

        """
        try:
            self.p.get_device_info_by_index(index)
            return True
        except Exception:
            return False

    def get_device_sample_rate(self):
        device_info = self.p.get_device_info_by_index(self.input_device_index)
        print(int(device_info['defaultSampleRate']))
        return int(device_info['defaultSampleRate'])


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
    # Set up argument parser
    parser = argparse.ArgumentParser(description="Audio Recorder")
    parser.add_argument('--main_dir', default='data', help='Main directory for saving recordings')
    parser.add_argument('--backup_dir', default='backup', help='Backup directory for saving recordings')
    parser.add_argument('--recording_unit', default='minutes', help='Unit of recording time')
    parser.add_argument('--recording_time', type=int, default=1, help='Recording time')
    parser.add_argument('--recording_length', type=int, default=60, help='Length of each individual recording')
    parser.add_argument('--channels_names', default='channel_1,channel_2', help='Names of the channels')
    parser.add_argument('--channels', type=int, default=2, help='Number of audio channels to record')
    parser.add_argument('--suffix', default='_channel_', help='Suffix to append to the filename of the recordings')
    args = parser.parse_args()

    channels_names = args.channels_names.split(',')

    # Ask for directory paths
    main_dir_input = input("Enter the directory for the main data (leave blank for default): ")
    if not main_dir_input:
        main_dir_input = args.main_dir

    backup_dir_input = input("Enter the directory for the backup data (leave blank for default): ")
    if not backup_dir_input:
        backup_dir_input = args.backup_dir

    dir_manager = DirectoryManager(main_dir=args.main_dir, backup_dir=args.backup_dir)
    print(dir_manager.main_save_path)  # Outputs the main directory path
    print(dir_manager.backup_path)  # Outputs the backup directory path

    recorder = Recorder(channels=args.channels, choice=True, main_save_path=dir_manager.main_save_path, backup_path=dir_manager.backup_path, suffix=args.suffix)
    try:
        recorder.start_recording(args.recording_time, args.recording_length, channels_names, time_unit=args.recording_unit)
    except Exception as e:
        print(f"An error of type {type(e).__name__} occurred: {e}")