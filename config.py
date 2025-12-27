# config.py
# config.py
import yaml
from pathlib import Path


class Config:
    def __init__(self, config_path="config.yaml"):
        self.config_path = Path(config_path)
        self._data = self._load_yaml()

        # ---- App ----
        self.APP_NAME = self._get("app.name")
        self.DEBUG = self._get("app.debug", False)
        self.UPLOAD_FOLDER = self._get("app.upload_folder", "uploads")
        self.MAX_CONTENT_LENGTH = self._get("app.max_content_length")

        # ---- Server ----
        self.HOST = self._get("server.host", "127.0.0.1")
        self.PORT = self._get("server.port", 5000)

        # ---- Database ----
        self.DB_TYPE = self._get("database.type")
        self.DB_PATH = self._get("database.path")

        # ---- Images ----
        self.ALLOWED_EXTENSIONS = set(
            self._get("images.allowed_extensions", [])
        )

        # ---- Metadata ----
        self.METADATA_FILE = self._get("metadata.file", "image_metadata.json")

    # ---------------------
    # Internal helpers
    # ---------------------
    def _load_yaml(self):
        if not self.config_path.exists():
            raise FileNotFoundError(f"Config file not found: {self.config_path}")

        with self.config_path.open("r") as f:
            
            return yaml.safe_load(f) or {}
    def _get(self, dotted_key, default=None):
        
        keys = dotted_key.split(".")
        value = self._data

        for k in keys:
            if not isinstance(value, dict) or k not in value:
                return default
            value = value[k]

        return value
    def as_dict(self):
        return self._data
if __name__ == "__main__":
    config = Config()
    