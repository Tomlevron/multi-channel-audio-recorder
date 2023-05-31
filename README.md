![DALL·E 2023-05-31 10 20 11 - No cable2](https://github.com/Tomlevron/multi-channel-audio-recorder/assets/54799120/49134df9-8b2f-4e9d-975e-3aae71a59bf3)

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

- Python 3.6 or above
- numpy>=1.21.5
- wave
- pyaudio==0.2.11
- argparse

## Installation
1. Clone the repository:
```
git clone https://github.com/Tomlevron/multi-channel-audio-recorder.git
cd multi-channel-audio-recorder
```
2. Install requirements:
```
pip install -r requirements.txt
```
Note: You might need to use pip3 instead of pip and add --user after install if you encounter permission issues.
## Usage

1. Make sure all the dependencies are installed in your Python environment.

2. Run the script with command-line parameters:

```shell
python audio_recorder.py --main_dir data --backup_dir backup --recording_unit minutes --recording_time 1 --recording_length 60 --channels_names channel_1,channel_2 --channels 2 --suffix _channel_ 
```

The command-line arguments are:

- --main_dir: Set the primary directory for audio file storage.
- --backup_dir: Backup directory for the storage of audio file copies.
- --recording_unit: Specify the unit of recording time (the options are `seconds`, `minutes`, or `hours`).
- --recording_time: Define the total time duration for which you wish to record.
- --recording_length: Specify the duration of each individual recording in seconds.
- --channels_names: Provide a list of the names of the channels being recorded. These names will influence the filenames of the generated .wav files.
- --channels: Specify the number of audio channels to record.
- --suffix: Specify the suffix to append to the filename of the recordings.

3. Execute the script. You will be prompted to select an input device from a list printed in the console.
4. The script will record audio for the specified duration, and subsequently, save the audio data as .wav files in the designated primary and backup directories.

## To do
- [x] Add Code comments and docstrings
- [x] Add installation instructions
- [ ] Explain what can be done with it
- [ ] Add unit tests to ensure the functionality of the code.
- [ ] Add an example section demonstrating different usage scenarios
- [ ] Incorporate logging to track the progress and errors during recording.
- [ ] Provide detailed documentation on the usage of the command-line interface.
## Contact

If you have any questions, suggestions, or feedback regarding this project, please feel free to reach out to me. You can contact me at:

- Name: Tom Lev-ron
- Email: tomseaherb@gmail.com
- LinkedIn: [Tom](https://www.linkedin.com/in/tomlev-ron/)
