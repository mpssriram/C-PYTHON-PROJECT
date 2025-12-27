import mysql.connector
import pandas as pd
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime
from config import Config
from filereader import ExifDataFrameBuilder

class ImageDBService:
    def __init__(
        self,
        config: Config | None = None,
    ):
        self.config = config or Config()
        self.host = self.config._get("database.host", "localhost")
        self.user = self.config._get("database.user", "root")
        self.password = self.config._get("database.password", "1234")  
        self.database = self.config._get("database.database", "image_gallery")
        self.table = self.config._get("database.table", "image_info")

    # -------------------------
    # Internal: connection helper
    # -------------------------
    def _connect(self):
        return mysql.connector.connect(
            host=self.host,
            user=self.user,
            password=self.password,
            database=self.database,
        )
    # -------------------------
    # INSERT: DataFrame -> MySQL
    # -------------------------
    def insert_dataframe(self, df: pd.DataFrame) -> int:
        """
        Insert rows from DataFrame into MySQL.

        Expected DataFrame columns:
          - image_filename
          - EXIF_DateTime
          - full_path
          - created_time
          - EXIF_Make
          - EXIF_Model
          - EXIF_XPKeywords

        Returns:
          number of rows inserted
        """
        conn = self._connect()
        try:
            cursor = conn.cursor()
            sql = f"""
            INSERT INTO image_info
            (image_filename, exif_datetime, full_path, created_time, exif_make, exif_model, exif_xpkeywords)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            df = df.where(pd.notnull(df), None)
            data: List[Tuple[Any, ...]] = []
            for _, row in df.iterrows():
                data.append((
                    row.get("image_filename"),
                    row.get("EXIF_DateTime"),
                    row.get("full_path"),
                    row.get("created_time"),
                    row.get("EXIF_Make"),
                    row.get("EXIF_Model"),
                    row.get("EXIF_XPKeywords"),
                ))
            if not data:
                return 0
            cursor.executemany(sql, data)
            conn.commit()
            return cursor.rowcount
        finally:
            conn.close()
# ----------- CREATE NEW DATAFRAME ------------
    def new_insert_dataframe(self,df : pd.DataFrame): 
        conn = self._connect()
        try:
            cursor = conn.cursor()

            sql = f"""
            INSERT INTO image_info
            (image_filename, exif_datetime, full_path, created_time, exif_make, exif_model, exif_xpkeywords)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            
            df = df.where(pd.notnull(df), None)
            data: List[Tuple[Any, ...]] = []
            for _, row in df.iterrows():
                data.append((
                    row.get("image_filename"),
                    row.get("EXIF_DateTime"),
                    row.get("full_path"),
                    row.get("created_time"),
                    row.get("EXIF_Make"),
                    row.get("EXIF_Model"),
                    row.get("EXIF_XPKeywords"),
                ))

            if not data:
                return 0

            cursor.executemany(sql, data)
            conn.commit()
            return cursor.rowcount

        finally:
            conn.close()
    # -------------------------
    # SEARCH: MySQL -> rows
    # -------------------------
    def search(
        self,
        exif_datetime: Optional[datetime] = None,
        image_filename: Optional[str] = None,
        exif_xpkeywords: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Search image_info by:
          - exif_datetime (exact match)
          - image_filename (exact match)

        Pass one or both. If both are None -> returns [].
        """
        if exif_datetime is None and image_filename is None and exif_xpkeywords is None:
            return []

        conn = self._connect()
        try:
            cursor = conn.cursor(dictionary=True)

            sql = f"SELECT * FROM image_info WHERE 1=1"
            params: List[Any] = []

            if exif_datetime is not None:
                sql += " AND DATE(exif_datetime) = %s"
                params.append(exif_datetime)

            if image_filename is not None:
                sql += " AND image_filename = %s"
                params.append(image_filename)

            if exif_xpkeywords:
                sql += " AND exif_xpkeywords like %s"
                params.append(f"%{exif_xpkeywords}%")
            
            
            cursor.execute(sql, params)
            return cursor.fetchall()

        finally:
            conn.close()
# ------------ GET FULL_PATH ------------
    def get_full_path(self):
        conn = self._connect()
        try:
            cursor = conn.cursor()
            command = f"SELECT full_path from {self.table} "
            
            cursor.execute(command)
            result = cursor.fetchall()
            return result
    
        except Exception as e :
            return f"{e}"
        finally:
            conn.close()       
# --------- GET ALL IMAGES ---------------
    def get_all_images(self, limit: int = 500):
        conn = self._connect()
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute(
                f"SELECT image_filename, full_path, exif_datetime, exif_make, exif_model, exif_xpkeywords "
                f"FROM {self.table} "
                f"ORDER BY exif_datetime DESC "
                f"LIMIT %s",
                (limit,),
            )
            return cursor.fetchall()
        finally:
            conn.close()
# ----------- GET TAGS ---------
    def get_tags(self, full_path: str):
        conn = self._connect()
        
        try:
            cursor = conn.cursor(dictionary = True)
            sql = (f"""
                select exif_xpkeywords from {self.table}
                where full_path = %s
                """
            )
            cursor.execute(sql, (full_path,))
            row = cursor.fetchone()
            return None if row is None else row["exif_xpkeywords"]
        finally:
            conn.close()
# -------- UPDATE TAG INFO ------------  
    def update_tag_info(self, full_path : str ,tag_value : str):
        
        conn = self._connect()
        try:
            cursor = conn.cursor()
            f = full_path
            params: List[Any] = []
            print(f)
        
            command = f"UPDATE {self.table} SET exif_xpkeywords = %s where full_path = %s"
            params.append(tag_value)
            params.append(f)
            cursor.execute(command,params)
            conn.commit()
            result = cursor.rowcount
            return result
    
        except Exception as e :
            return f"{e}"
        finally:
            conn.close()
# --------- UPDATE METADATA ------
    def update_metadata_info(self,full_path: str | None,exif_datetime: str | None,exif_make: str | None,exif_model: str | None):
        conn = self._connect()
        try:
            cursor = conn.cursor()
            sql = f"""
            UPDATE {self.table}
            SET exif_datetime = COALESCE(%s, exif_datetime),
                exif_make     = COALESCE(%s, exif_make),
                exif_model    = COALESCE(%s, exif_model)
            WHERE full_path = %s
            """
            dt = None
            if exif_datetime:
                exif_datetime = exif_datetime.strip()
                for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
                    try:
                        dt = datetime.strptime(exif_datetime, fmt)
                        break
                    except ValueError:
                        pass

            cursor.execute(sql, (dt, exif_make, exif_model, full_path))
            conn.commit()
            return cursor.rowcount
        finally:
            conn.close()
# ---------- BACKEND FOR WEBSITE -------------
if __name__ == "__main__":
    db_service = ImageDBService(Config("config.yaml"))
    builder = ExifDataFrameBuilder(Config("config.yaml"))
    df = builder.build_dataframe()
    
