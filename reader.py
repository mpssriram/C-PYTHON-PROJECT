# reader.py
from pathlib import Path
from typing import List

from config import Config


class FileReader:
    def __init__(self, config: Config | None = None):
        self.config = config or Config()

        self.allowed_extensions = {
            ext.lower().lstrip(".")
            for ext in self.config.ALLOWED_EXTENSIONS
        }

    def read_images(self, folder_path: str | Path) -> List[str]:
        """
        Read all image files from a folder and its subfolders.

        Returns:
            List of relative file paths (as strings)
        """
        folder = Path(folder_path)

        if not folder.exists():
            raise FileNotFoundError(f"Folder does not exist: {folder}")

        if not folder.is_dir():
            raise NotADirectoryError(f"Not a directory: {folder}")

        images: List[str] = []

        for file in folder.rglob("*"):
            if file.is_file() and self._is_allowed(file):
                images.append(str(file.relative_to(folder)))

        return sorted(images)

    # -------------------
    # Internal helpers
    # -------------------
    def _is_allowed(self, file: Path) -> bool:
        return file.suffix.lower().lstrip(".") in self.allowed_extensions

if __name__ == "__main__":
    config = Config()
    reader = FileReader(config)
    image_files = reader.read_images(config.UPLOAD_FOLDER)
    