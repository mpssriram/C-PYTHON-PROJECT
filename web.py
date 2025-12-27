from flask import Flask, render_template, send_from_directory, abort, request, redirect, url_for

from pathlib import Path
from datetime import datetime

from config import Config
from database import ImageDBService   # <-- your uploaded database.py
from tagmanager import TagManager
from filereader import ExifDataFrameBuilder

cfg = Config("config.yaml")
web = Flask(__name__)

db = ImageDBService(cfg)
tagm = TagManager(cfg)
file_r = ExifDataFrameBuilder(cfg)

BASE_DIR = Path(cfg.UPLOAD_FOLDER).resolve()

@web.route("/uploads/<path:relpath>")
def uploads(relpath):
    # block path traversal
    target = (BASE_DIR / relpath).resolve()
    if not str(target).startswith(str(BASE_DIR)):
        abort(403)
    return send_from_directory(str(BASE_DIR), relpath)
# ---------- WEB ROUTE FOR VIEWING GALLERY --------
@web.route("/gallery")
def gallery():
    q = (request.args.get("q") or "").strip()
    d = (request.args.get("date") or "").strip()
    g = (request.args.get("g") or "").strip()
    

    exif_date = None
    if d:
        exif_date = datetime.strptime(d, "%Y-%m-%d").date()

    image_filename = q if q else None
    tag_file = g if g else None

    # Show ALL images if nothing entered
    if exif_date is None and image_filename is None and tag_file is None:
        rows = db.get_all_images(limit=500)
    else:
        rows = db.search(exif_datetime=exif_date, image_filename=image_filename,exif_xpkeywords = tag_file)

    images = []
    for r in rows:
        full_path = r.get("full_path")
        if not full_path:
            continue

        p = Path(full_path).resolve()

        try:
            rel = p.relative_to(BASE_DIR)
        except Exception:
            continue

        images.append({
            "image_filename": r.get("image_filename"),
            "relpath": str(rel).replace("\\", "/"),
            "exif_datetime": r.get("exif_datetime"),
            "exif_make": r.get("exif_make"),
            "exif_model": r.get("exif_model"),
            "exif_xpkeywords": r.get("exif_xpkeywords"),
        })

    return render_template("gallery.html", images=images, q=q, date=d,g = g)
#--------- ROUTE FOR GALLERY IN THE WEBSITE ----------
@web.route("/")
def home():
    return '<a href="/gallery">Open Gallery</a>'

# ---------- API FOR UPDATING TAGS -----------
def update_tag(file_path: str, tag_value: str):
    tags = tag_value.split(",")
    try:
        existing = db.get_tags(file_path)
        print("EXISTING FROM DB:", repr(existing))

        new_tags = tagm.merge_tags(existing, tags)
        print("NEW_TAGS COMPUTED:", repr(new_tags))

        rc = db.update_tag_info(file_path, new_tags)
        print("ROWCOUNT:", rc)

        # verify immediately (same run)
        after = db.get_tags(file_path)
        print("AFTER FROM DB:", repr(after))

        return f"SUCCESS: tags='{new_tags}', rows_updated={rc}"

    except Exception as e:
        return f"FAILED: {e}"
# --------- API FOR DELETING TAGS --------
def delete_tags(file_path: str, tag_value: str):
    tags = tag_value.split(",")
    try:
        existing = db.get_tags(file_path)
        print("EXISTING FROM DB:", repr(existing))

        new_tags = tagm.delete_tags(existing, tags)
        print("NEW_TAGS COMPUTED:", repr(new_tags))

        rc = db.update_tag_info(file_path, new_tags)
        print("ROWCOUNT:", rc)

        # verify immediately (same run)
        after = db.get_tags(file_path)
        print("AFTER FROM DB:", repr(after))

        return f"SUCCESS: tags='{new_tags}', rows_updated={rc}"

    except Exception as e:
        return f"FAILED: {e}"
# ---------- API FOR EDITING THE DATABSE INFO ---------
def edit_database():

    data = db.get_full_path()
    df = file_r.build_dataframe()
    edited_data = {
        Path(row[0]).resolve().as_posix().lower()
        for row in data
    }
    for i in range(len(df["full_path"])):
        df_path = Path(df["full_path"][i]).resolve().as_posix().lower()

        if df_path not in edited_data:
            db.new_insert_dataframe(df.iloc[[i]])
            print("sucessful added the data")
        else:
            pass
            print("not added data")

# --------- FOR EDITING TAGS ROUTE ------------
@web.route("/edit", methods=["POST"])
def edit_tags():
    mode = (request.form.get("mode") or "tags").strip()   # "tags" or "meta"

    r = (request.form.get("r") or "").strip()
    file = (request.form.get("file") or "").strip()
    edit = (request.form.get("edit") or "").strip()

    full_path = (BASE_DIR / file).resolve()
    if not str(full_path).startswith(str(BASE_DIR)):
        return "Invalid path", 403

    # ---------- TAGS ----------
    if mode == "tags":
        if edit == "delete":
            delete_tags(str(full_path), r)
        else:
            update_tag(str(full_path), r)

        return redirect(url_for("gallery"))

    # ---------- METADATA ----------
    elif mode == "meta":
        exif_datetime = (request.form.get("exif_datetime") or "").strip()
        exif_make = (request.form.get("exif_make") or "").strip()
        exif_model = (request.form.get("exif_model") or "").strip()

        # empty => keep old value (COALESCE)
        exif_datetime = exif_datetime or None
        exif_make = exif_make or None
        exif_model = exif_model or None

        rc = db.update_metadata_info(str(full_path), exif_datetime, exif_make, exif_model)
        print("UPDATED META ROWS:", rc)

        return redirect(url_for("gallery"))

    return "Invalid mode", 400
# ------ to run the website --------
if __name__ == "__main__":
    web.run(debug=cfg.DEBUG, host=cfg.HOST, port=cfg.PORT)
    #update_tag(r'C:\2 WEEK PROJECT\sample_images\TIJV0077.JPG',"sunrise,mountains,himalayas")
    #db.update_tag_info(
    # "C:\\2 WEEK PROJECT\\sample_images\\IMG_1688.HEIC",
    # "FORCE_TEST")
    #print(edit_metadata(r'C:\2 WEEK PROJECT\sample_images\IMG_9938.jpg',"2020-11-13 00:00:00,APPLE"))
    #print(edit_database())