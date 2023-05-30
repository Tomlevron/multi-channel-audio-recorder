# PyAudio Multi-Channel Recorder with Backup

The provided repository is a an audio recording utility, designed to record audio from multiple channels simultaneously, leveraging the PyAudio library. The tool offers features such as saving backup recordings, user-defined recording durations, and command-line interface for customizing various parameters.

### Features

- Detection and selection of the input device.
- Audio recording in manageable chunks for a user-defined duration.
- Splitting of the incoming data into distinct channels.
- Storing each channel's audio data in individual .wav files in a primary directory and a backup directory.
- Comprehensive file naming based on the channel name, current time, and date.
- Organization of files in date-specific folders within both primary and backup directories.
- Command-line interface for customizing various parameters.

### Requirements

- Python 3.6 or above
- numpy
- wave
- pyaudio
- argparse

### Usage

1. Make sure all the dependencies are installed in your Python environment.

2. Run the script with command-line parameters:

```shell
python audio_recorder.py --main_dir data --backup_dir backup --recording_unit minutes --recording_time 1 --recording_length 60 --channels_names channel_1,channel_2 --channels 2 --suffix _channel_ 
```

The command-line arguments are:

--main_dir: Set the primary directory for audio file storage.
--backup_dir: Designate a backup directory for the storage of audio file copies.
--recording_unit: Specify the unit of recording time (seconds, minutes, or hours).
--recording_time: Define the total time duration for which you wish to record.
--recording_length: Specify the duration of each individual recording in seconds.
--channels_names: Provide a list of the names of the channels being recorded. These names will influence the filenames of the generated .wav files.
--channels: Specify the number of audio channels to record.
--suffix: Specify the suffix to append to the filename of the recordings.

3. Execute the script. You will be prompted to select an input device from a list printed in the console.
4. The script will record audio for the specified duration, and subsequently, save the audio data as .wav files in the designated primary and backup directories.