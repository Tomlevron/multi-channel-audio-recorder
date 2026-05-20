"""Record audio from multiple input channels and save each to its own WAV file."""

from __future__ import annotations

from multi_channel_audio_recorder.paths import DirectoryManager
from multi_channel_audio_recorder.recorder import Recorder

__version__ = "0.2.0"
__all__ = ["DirectoryManager", "Recorder", "__version__"]
