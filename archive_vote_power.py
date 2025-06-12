import os
import json
import time
import shutil
import datetime

THRESHOLD_DAYS = 30

BASE_DIR = "current_vote_power"
DOCS_DIR = os.path.join("docs", "current_vote_power")


def archive_old_files(base_dir=BASE_DIR, docs_dir=DOCS_DIR, days=THRESHOLD_DAYS):
    """Move files older than ``days`` into month-based archive folders."""
    now = time.time()
    cutoff = now - days * 86400
    moved = {}

    for name in os.listdir(base_dir):
        path = os.path.join(base_dir, name)
        if not os.path.isfile(path):
            continue
        mtime = os.path.getmtime(path)
        if mtime > cutoff:
            continue
        ts = datetime.datetime.utcfromtimestamp(mtime)
        sub = os.path.join("archive", ts.strftime("%Y-%m"))

        os.makedirs(os.path.join(base_dir, sub), exist_ok=True)
        os.makedirs(os.path.join(docs_dir, sub), exist_ok=True)

        shutil.move(path, os.path.join(base_dir, sub, name))

        docs_src = os.path.join(docs_dir, name)
        if os.path.exists(docs_src):
            shutil.move(docs_src, os.path.join(docs_dir, sub, name))
        moved[name] = f"{sub}/{name}"

    if moved:
        manifest_path = os.path.join(docs_dir, "manifest.json")
        if os.path.exists(manifest_path):
            with open(manifest_path) as f:
                manifest = json.load(f)
        else:
            manifest = {"flare": [], "songbird": []}

        for network, files in manifest.items():
            manifest[network] = [moved.get(fname, fname) for fname in files]

        with open(manifest_path, "w") as f:
            json.dump(manifest, f, indent=2)


if __name__ == "__main__":
    archive_old_files()
