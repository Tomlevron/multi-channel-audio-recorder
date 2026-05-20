from __future__ import annotations

from pathlib import Path


class DirectoryManager:
    """Resolve the main + backup save directories relative to the current working dir."""

    def __init__(self, main_dir: str | Path = "data", backup_dir: str | Path = "backup") -> None:
        cwd = Path.cwd()
        self.main_save_path: Path = cwd / main_dir
        self.backup_path: Path = cwd / backup_dir
