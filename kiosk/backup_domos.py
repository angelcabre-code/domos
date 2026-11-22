#!/usr/bin/env python3
"""
DOMOS Automatic Backup & Restore Utility
- Archives all /opt/domoskiosk/*.json, *.py, *.sh, static UI, audio assets, and systemd unit files.
- Saves to /opt/domoskiosk/backups/ AND mirrors to SD card /media/storage/domos_backups/.
- Retention: keeps last 7 daily backups + last 4 Sunday weekly backups.
- Supports 1-command restore: python3 /opt/domoskiosk/backup_domos.py --restore <archive.tar.gz>
"""
import argparse
import json
import os
import shutil
import sys
import tarfile
from datetime import datetime
from pathlib import Path

BASE_DIR = Path("/opt/domoskiosk")
LOCAL_BACKUP_DIR = BASE_DIR / "backups"
SD_BACKUP_DIR = Path("/media/storage/domos_backups")
STATUS_FILE = LOCAL_BACKUP_DIR / "backup_status.json"
SYSTEMD_DIR = Path("/etc/systemd/system")


def _prune_dir(bdir: Path, keep_daily: int = 7, keep_weekly: int = 4):
    if not bdir.exists():
        return
    files = sorted(bdir.glob("domos_backup_*.tar.gz"), key=lambda p: p.stat().st_mtime, reverse=True)
    if len(files) <= keep_daily:
        return
    kept = set(files[:keep_daily])
    weekly_kept = 0
    for f in files[keep_daily:]:
        # Filename format: domos_backup_YYYY-MM-DD_HHMMSS.tar.gz
        try:
            date_part = f.name.split("_")[2]
            dt = datetime.strptime(date_part, "%Y-%m-%d")
            if dt.weekday() == 6 and weekly_kept < keep_weekly:  # Sunday
                kept.add(f)
                weekly_kept += 1
        except Exception:
            pass
    for f in files:
        if f not in kept:
            try:
                f.unlink()
            except Exception:
                pass


def create_backup(reason: str = "scheduled") -> dict:
    LOCAL_BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    now = datetime.now()
    ts_str = now.strftime("%Y-%m-%d_%H%M%S")
    archive_name = f"domos_backup_{ts_str}.tar.gz"
    local_archive = LOCAL_BACKUP_DIR / archive_name

    included_files = []
    with tarfile.open(local_archive, "w:gz") as tar:
        # 1. All JSON configs & histories, Python scripts, shell scripts, and doorbell WAV
        for pattern in ("*.json", "*.py", "*.sh", "doorbell_chime.wav"):
            for p in sorted(BASE_DIR.glob(pattern)):
                if p.is_file():
                    tar.add(p, arcname=f"domoskiosk/{p.name}")
                    included_files.append(p.name)

        # 2. Static UI files (index.html, app.js, style.css, icons/logos)
        static_dir = BASE_DIR / "static"
        if static_dir.exists():
            for p in sorted(static_dir.rglob("*")):
                if p.is_file() and p.stat().st_size < 15 * 1024 * 1024:
                    rel = p.relative_to(BASE_DIR)
                    tar.add(p, arcname=f"domoskiosk/{rel}")
                    included_files.append(str(rel))

        # 3. Systemd unit files snapshot
        if SYSTEMD_DIR.exists():
            for p in sorted(SYSTEMD_DIR.glob("domoskiosk-*")):
                if p.is_file():
                    try:
                        tar.add(p, arcname=f"systemd/{p.name}")
                        included_files.append(f"systemd/{p.name}")
                    except Exception:
                        pass

    size_bytes = local_archive.stat().st_size

    # Mirror to SD card if mounted & writable
    sd_mirrored = False
    sd_error = None
    if Path("/media/storage").is_mount():
        try:
            SD_BACKUP_DIR.mkdir(parents=True, exist_ok=True)
            shutil.copy2(local_archive, SD_BACKUP_DIR / archive_name)
            _prune_dir(SD_BACKUP_DIR)
            sd_mirrored = True
        except Exception as e:
            sd_error = str(e)

    _prune_dir(LOCAL_BACKUP_DIR)

    info = {
        "success": True,
        "filename": archive_name,
        "timestamp": now.strftime("%Y-%m-%d %H:%M:%S"),
        "reason": reason,
        "size_bytes": size_bytes,
        "size_kb": round(size_bytes / 1024.0, 1),
        "files_count": len(included_files),
        "local_path": str(local_archive),
        "sd_mirrored": sd_mirrored,
        "sd_path": str(SD_BACKUP_DIR / archive_name) if sd_mirrored else None,
        "sd_error": sd_error,
    }
    try:
        STATUS_FILE.write_text(json.dumps(info, indent=2, ensure_ascii=False))
    except Exception:
        pass
    return info


def list_backups() -> dict:
    LOCAL_BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    items = []
    for p in sorted(LOCAL_BACKUP_DIR.glob("domos_backup_*.tar.gz"), key=lambda x: x.stat().st_mtime, reverse=True):
        st = p.stat()
        sd_exists = (SD_BACKUP_DIR / p.name).exists()
        items.append({
            "filename": p.name,
            "date": datetime.fromtimestamp(st.st_mtime).strftime("%Y-%m-%d %H:%M"),
            "size_kb": round(st.st_size / 1024.0, 1),
            "sd_mirrored": sd_exists,
        })
    last_status = None
    if STATUS_FILE.exists():
        try:
            last_status = json.loads(STATUS_FILE.read_text())
        except Exception:
            pass
    return {
        "backups": items,
        "count": len(items),
        "sd_mounted": Path("/media/storage").is_mount(),
        "sd_dir": str(SD_BACKUP_DIR),
        "local_dir": str(LOCAL_BACKUP_DIR),
        "schedule": "Diario 04:00 (retiene 7 diarios + 4 semanales)",
        "last_status": last_status,
    }


def restore_backup(archive_path: str, configs_only: bool = False):
    p = Path(archive_path)
    if not p.exists():
        print(f"ERROR: Archive not found: {p}", file=sys.stderr)
        sys.exit(1)
    with tarfile.open(p, "r:gz") as tar:
        for member in tar.getmembers():
            if not member.isfile():
                continue
            if member.name.startswith("domoskiosk/"):
                rel = member.name[len("domoskiosk/"):]
                if configs_only and not rel.endswith(".json"):
                    continue
                target = BASE_DIR / rel
                target.parent.mkdir(parents=True, exist_ok=True)
                with tar.extractfile(member) as src, open(target, "wb") as dst:
                    shutil.copyfileobj(src, dst)
                print(f"Restored: {target}")
    print("Restore complete! Run: sudo systemctl restart domoskiosk-server domoskiosk-cage")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="DOMOS Backup & Restore")
    parser.add_argument("--reason", default="manual", help="Reason label (scheduled/manual)")
    parser.add_argument("--restore", help="Path to domos_backup_*.tar.gz to restore")
    parser.add_argument("--configs-only", action="store_true", help="When restoring, only restore *.json files")
    parser.add_argument("--list", action="store_true", help="List backups as JSON")
    args = parser.parse_args()

    if args.restore:
        restore_backup(args.restore, configs_only=args.configs_only)
    elif args.list:
        print(json.dumps(list_backups(), indent=2, ensure_ascii=False))
    else:
        res = create_backup(reason=args.reason)
        print(json.dumps(res, indent=2, ensure_ascii=False))
