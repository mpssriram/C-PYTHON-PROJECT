# config.py
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional

import yaml


class Config:
    def __init__(self, config_path: str = "config.yaml"):
        self.config_path = Path(config_path)
        self._data: Dict[str, Any] = self._load_yaml()

        # ----- App -----
        self.APP_NAME = self._get("app.name")
        self.DEBUG = self._get("app.debug", False)

        # ----- Server -----
        self.HOST = self._get("server.host", "127.0.0.1")
        self.PORT = self._get("server.port", 5000)

        # ----- Database -----
        self.DB_TYPE = self._get("database.type")

        # Keep DB_PATH for compatibility (used for sqlite-style setups)
        self.DB_PATH = self._get("database.path")

        # ----- CSV -----
        self.CSV_DELIMITER = self._get("csv.delimiter", ",")
        self.CSV_HAS_HEADER = self._get("csv.has_header", True)
        self.CSV_ENCODING = self._get("csv.encoding", "utf-8")

        # ----- Files -----
        self.ALLOWED_EXTENSIONS = set(self._get("files.allowed_extensions", ["csv"]))

        # ----- Metadata -----
        self.METADATA_FILE = self._get("metadata.file", "csv_metadata.json")

    def _load_yaml(self) -> Dict[str, Any]:
        if not self.config_path.exists():
            raise FileNotFoundError(f"Config file does not exist: {self.config_path}")

        with open(self.config_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
            return data or {}

    def _get(self, dotted_key: str, default: Any = None) -> Any:
        """
        Reads nested config using dot notation:
          _get("database.host") -> self._data["database"]["host"]

        Returns default if any key is missing.
        """
        keys = dotted_key.split(".")
        value: Any = self._data

        for k in keys:
            if not isinstance(value, dict) or k not in value:
                return default
            value = value[k]

        return value

    