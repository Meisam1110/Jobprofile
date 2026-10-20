#!/usr/bin/env python3
"""Build the offline Windows installer bundle (runs on Linux, macOS or Windows).

Produces dist-windows/JobProfile-Windows-Setup.zip containing:
  Install.bat + README.txt           the double-click installer
  payload/python/                    embeddable Python 3.11 for Windows, with every
                                     dependency pre-extracted (no pip, no internet)
  payload/jpms/                      backend, built frontend, master workbook
  payload/seed/jobprofile.db         database pre-loaded with all job profiles
  payload/*.bat|vbs|ps1|ico          launcher, shortcuts, uninstaller

Requirements on the build machine: Python 3.11+ with pip, Node 20+ and internet.
Usage:  python packaging/build_windows_bundle.py
"""
from __future__ import annotations

import os
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PKG = ROOT / "packaging"
OUT = ROOT / "dist-windows"
CACHE = OUT / "cache"

PY_VERSION = "3.11.9"  # last 3.11 release that ships Windows binaries
PY_EMBED_URL = f"https://www.python.org/ftp/python/{PY_VERSION}/python-{PY_VERSION}-embed-amd64.zip"
PTH_NAME = "python311._pth"

TEXT_SUFFIXES = {".bat", ".vbs", ".ps1", ".txt"}


def log(msg: str) -> None:
    print(f"==> {msg}", flush=True)


def run(cmd: list[str], **kwargs) -> None:
    subprocess.run(cmd, check=True, **kwargs)


def download(url: str, dest: Path) -> Path:
    if dest.exists() and dest.stat().st_size > 0:
        return dest
    dest.parent.mkdir(parents=True, exist_ok=True)
    log(f"Downloading {url}")
    with urllib.request.urlopen(url, timeout=120) as response, open(dest, "wb") as handle:
        shutil.copyfileobj(response, handle)
    return dest


def copy_text_crlf(src: Path, dest: Path) -> None:
    """Batch/VBS/PowerShell files must be ASCII with CRLF line endings."""
    text = src.read_text(encoding="utf-8")
    try:
        text.encode("ascii")
    except UnicodeEncodeError as exc:
        raise SystemExit(f"{src} contains non-ASCII characters: {exc}")
    text = text.replace("\r\n", "\n").replace("\n", "\r\n")
    dest.write_bytes(text.encode("ascii"))


def build_python_runtime(payload: Path) -> None:
    py_dir = payload / "python"
    embed = download(PY_EMBED_URL, CACHE / f"python-{PY_VERSION}-embed-amd64.zip")
    with zipfile.ZipFile(embed) as zf:
        zf.extractall(py_dir)

    wheels = CACHE / "wheels"
    if wheels.exists():
        shutil.rmtree(wheels)
    wheels.mkdir(parents=True)
    log("Downloading Windows wheels (cp311, win_amd64)")
    run([
        sys.executable, "-m", "pip", "download", "-q",
        "-r", str(PKG / "requirements-windows.txt"),
        "-d", str(wheels),
        "--platform", "win_amd64",
        "--python-version", "3.11",
        "--implementation", "cp",
        "--abi", "cp311",
        "--only-binary=:all:",
    ])

    site = py_dir / "Lib" / "site-packages"
    site.mkdir(parents=True)
    names = []
    for wheel in sorted(wheels.glob("*.whl")):
        names.append(wheel.name)
        with zipfile.ZipFile(wheel) as zf:
            zf.extractall(site)
    (payload / "wheels-manifest.txt").write_text("\r\n".join(names) + "\r\n")
    log(f"Extracted {len(names)} wheels")

    # Embedded Python ignores PYTHONPATH; everything it can import is listed here.
    # Paths are relative to this file (python\), so ..\jpms\backend is the app.
    (py_dir / PTH_NAME).write_text(
        "python311.zip\r\n.\r\nLib\\site-packages\r\n..\\jpms\\backend\r\nimport site\r\n"
    )


def build_frontend() -> Path:
    frontend = ROOT / "frontend"
    log("Building the frontend")
    npm = "npm.cmd" if os.name == "nt" else "npm"
    if not (frontend / "node_modules").exists():
        run([npm, "install", "--no-audit", "--no-fund"], cwd=frontend)
    run([npm, "run", "build"], cwd=frontend)
    return frontend / "dist"


def copy_app(payload: Path, dist: Path) -> None:
    jpms = payload / "jpms"
    ignore = shutil.ignore_patterns("__pycache__", "*.pyc", ".env", "*.db", "*.db-*")
    shutil.copytree(ROOT / "backend" / "app", jpms / "backend" / "app", ignore=ignore)
    data = jpms / "data"
    data.mkdir(parents=True)
    shutil.copy2(ROOT / "data" / "job_profiles_master.xlsm", data)
    shutil.copy2(ROOT / "data" / "job_profile_template.docx", data)
    shutil.copytree(dist, jpms / "frontend" / "dist")


def build_seed_db(payload: Path) -> None:
    log("Pre-loading the database from the master workbook")
    seed_dir = payload / "seed"
    seed_dir.mkdir(parents=True)
    db_path = seed_dir / "jobprofile.db"
    env = {**os.environ, "JPMS_DATABASE_URL": f"sqlite:///{db_path.as_posix()}"}
    run([sys.executable, str(ROOT / "scripts" / "import_excel.py")], env=env)
    con = sqlite3.connect(db_path)
    con.execute("PRAGMA wal_checkpoint(TRUNCATE)")
    con.execute("PRAGMA journal_mode=DELETE")
    con.execute("VACUUM")
    con.close()
    for extra in seed_dir.glob("jobprofile.db-*"):
        extra.unlink()


def make_icon(dest: Path) -> None:
    from PIL import Image, ImageDraw, ImageFont

    size = 256
    image = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((8, 8, size - 8, size - 8), radius=52, fill=(255, 203, 5, 255))
    font = None
    for candidate in (
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "C:/Windows/Fonts/arialbd.ttf",
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
    ):
        if Path(candidate).exists():
            font = ImageFont.truetype(candidate, 128)
            break
    if font is None:
        font = ImageFont.load_default(size=128)
    draw.text((size / 2, size / 2), "JP", fill=(26, 26, 26, 255), font=font, anchor="mm")
    image.save(dest, format="ICO", sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])


def main() -> None:
    if OUT.exists():
        shutil.rmtree(OUT / "JobProfile-Setup", ignore_errors=True)
    stage = OUT / "JobProfile-Setup"
    payload = stage / "payload"
    payload.mkdir(parents=True)

    build_python_runtime(payload)
    copy_app(payload, build_frontend())
    build_seed_db(payload)
    make_icon(payload / "jobprofile.ico")

    log("Adding launcher scripts")
    src = PKG / "windows"
    for item in sorted(src.iterdir()):
        if item.name in ("Install.bat", "README.txt"):
            copy_text_crlf(item, stage / item.name)
        else:
            copy_text_crlf(item, payload / item.name)

    zip_path = OUT / "JobProfile-Windows-Setup.zip"
    zip_path.unlink(missing_ok=True)
    log(f"Creating {zip_path}")
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for path in sorted(stage.rglob("*")):
            if path.is_file():
                zf.write(path, Path("JobProfile-Setup") / path.relative_to(stage))
    size_mb = zip_path.stat().st_size / 1_048_576
    log(f"Done: {zip_path} ({size_mb:.0f} MB)")


if __name__ == "__main__":
    main()
