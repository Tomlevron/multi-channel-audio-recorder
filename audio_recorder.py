import os
import wave
import pyaudio
import numpy as np
import time
import datetime
import argparse

class Recorder:
    def __init__(self, sample_format=pyaudio.paInt16, channels=1, chunk=1024, choice=False, main_save_path=None, backup_path=None, suffix='_channel_'):
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
        self.record_audio(rec_length)
        current_time = str(time.time())
        date_today = datetime.datetime.now()
        date_str = str(date_today.date())

        for i, name in enumerate(rooms_names):
            self.save_wav(name +  self.suffix, self.frames[i], date_str, current_time, self.main_save_path)
            self.save_wav(name +  self.suffix, self.frames[i], date_str, current_time, self.backup_path)
        
    def start_recording(self, num_rec, recording_length, rooms_names, time_unit="seconds"):
        # Convert num_rec to the appropriate time unit
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
    def __init__(self, main_dir="data", backup_dir="backup"):
        self.current_directory = os.getcwd()
        self.main_save_path = self.construct_path(main_dir)
        self.backup_path = self.construct_path(backup_dir)

    def construct_path(self, dir_name):
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

    recorder = Recorder(args.channels, choice=True, main_save_path=dir_manager.main_save_path, backup_path=dir_manager.backup_path, suffix=args.suffix)
    try:
        recorder.start_recording(args.recording_time, args.recording_length, channels_names, time_unit=args.recording_unit)
    except Exception as e:
        print(f"An error of type {type(e).__name__} occurred: {e}")