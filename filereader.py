# exif_reader.py
from __future__ import annotations

from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional

import pandas as pd
from PIL import Image, ExifTags

from config import Config
from reader import FileReader


class ExifDataFrameBuilder:
    def __init__(self, config: Config | None = None):
        self.config = config or Config()
        self.reader = FileReader(self.config)

        # Map EXIF numeric tag -> human-readable name
        self._exif_tag_map = {k: v for k, v in ExifTags.TAGS.items()}

    def build_dataframe(self, folder_path: str | Path | None = None) -> pd.DataFrame:
        """
        Reads images (including subfolders), extracts:
          - full_path
          - created_time (ISO)
          - all EXIF tags as columns

          
        Returns:
          pandas.DataFrame
        """
        base_folder = Path(folder_path) if folder_path else Path(self.config.UPLOAD_FOLDER)

        rel_files = self.reader.read_images(base_folder)
        rows: List[Dict[str, Any]] = []

        for rel in rel_files:
            full_path = (base_folder / rel).resolve()
            row: Dict[str, Any] = {
                "full_path": str(full_path),
                "created_time": self._file_created_time_iso(full_path),
            }

            exif = self._read_exif_dict(full_path)
            row.update(exif)  # each EXIF tag becomes a column

            rows.append(row)

        df = pd.DataFrame(rows)

    

        df["image_filename"] = df["full_path"].apply(lambda p: Path(p).name)


        # Optional: put the key columns first
        key_cols = ["full_path", "created_time"]
        other_cols = [c for c in df.columns if c not in key_cols]
        df = df[key_cols + sorted(other_cols)]
        df = df[["full_path","created_time","EXIF_Make","EXIF_Model","EXIF_DateTime","image_filename","EXIF_XPKeywords"]]

        return df

    # -----------------------------
    # Internal helpers
    # -----------------------------
    def _file_created_time_iso(self, path: Path) -> str:
        """
        Windows: st_ctime is creation time.
        Linux: st_ctime is metadata change time (not true creation).
        Still useful as a "created-ish" timestamp.
        """
        ts = path.stat().st_ctime
        return datetime.fromtimestamp(ts).isoformat(timespec="seconds")

    def _read_exif_dict(self, path: Path) -> Dict[str, Any]:
        """
        Returns EXIF tags as { "EXIF_<TagName>": value }.
        If no EXIF or not readable, returns {}.
        """
        try:
            with Image.open(path) as im:
                exif_raw = im.getexif()
                #print("tets run",exif_raw)
                if not exif_raw:
                    return {}

                out: Dict[str, Any] = {}
                for tag_id, value in exif_raw.items():
                    tag_name = self._exif_tag_map.get(tag_id, str(tag_id))
                    col = f"EXIF_{tag_name}"

                    out[col] = self._normalize_exif_value(value)
                    print("\t\t--",tag_name,"\t---> ", out[col])

                return out

        except Exception:
            # Some images (png/gif/heic) may have no EXIF or Pillow may not read it.
            return {}

    def _normalize_exif_value(self, value: Any) -> Any:
        """
        Make EXIF values safe for DataFrame + DB insertion.
        """
        # bytes -> decode if possible
        if isinstance(value, (bytes, bytearray)):
            try:
                return value.decode("utf-16le", errors="replace")
            except Exception:
                return str(value)

        # Pillow IFDRational / tuples -> stringify to keep DB-friendly
        if isinstance(value, (tuple, list)):
            return str(value)

        # dict-like -> stringify
        if isinstance(value, dict):
            return str(value)

        return value

if __name__ == "__main__":
    cfg = Config("config.yaml")
    builder = ExifDataFrameBuilder(cfg)
    df = builder.build_dataframe()
'''
full_path,created_time,EXIF_Make,EXIF_Model,EXIF_DateTime,
'''

