#!/usr/bin/env python3
"""
resrm: drop-in replacement for rm with undo/restore built-in (single script)

Basic usage:
  resrm file1 file2           # move to trash (safe)
  resrm -r dir                # recursive remove (moves dir to trash)
  resrm -f file               # ignore nonexistent, no prompt
  resrm -i file               # interactive prompt before removal
  resrm --skip-trash file     # permanent delete (bypass trash)
  resrm -l                    # list trash entries (neat table)
  resrm --restore <id|name>   # restore by short-id (8 chars) or exact basename
  resrm --empty               # empty trash entries (permanent)
"""

from __future__ import annotations
import argparse
import json
import os
import shutil
import sys
import uuid
import datetime
import textwrap
from pathlib import Path
from typing import List, Dict, Optional

# Config
def get_trash_base_for_user(uid: int) -> Path:
    """Return the trash base path depending on whether user is root or normal."""
    if uid == 0:
        return Path("/root/.local/share/resrm")
    else:
        try:
            import pwd
            user_info = pwd.getpwuid(uid)
            home_dir = Path(user_info.pw_dir)
        except Exception:
            home_dir = Path.home()
        return home_dir / ".local" / "share" / "resrm"


def get_trash_paths() -> tuple[Path, Path]:
    """Return (trash_dir, meta_file) for the current user."""
    base = get_trash_base_for_user(os.geteuid())
    trash = base / "files"
    meta = base / "metadata.json"
    trash.mkdir(parents=True, exist_ok=True)
    meta.parent.mkdir(parents=True, exist_ok=True)
    return trash, meta


TRASH_DIR, META_FILE = get_trash_paths()
DATEFMT = "%Y-%m-%d %H:%M"

def load_meta() -> List[Dict]:
    if META_FILE.exists():
        try:
            with META_FILE.open("r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []

def save_meta(meta: List[Dict]):
    with META_FILE.open("w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2, ensure_ascii=False)

meta = load_meta()

def short_id(fullid: str) -> str:
    return fullid[:8]

def human_time(ts: str) -> str:
    """
    Convert ISO timestamp string from metadata to a human-readable format.
    """
    try:
        dt = datetime.datetime.fromisoformat(ts)
        return dt.strftime(DATEFMT)
    except Exception:
        # Fallback: just return the raw string
        return ts

def entry_display(entry: Dict, width: int = 80) -> str:
    id8 = short_id(entry["id"])
    ts = human_time(entry["timestamp"])
    path = entry["orig_path"]
    wrapped = textwrap.fill(path, width=width-32)
    return f"{id8:<8} {ts:<19} {wrapped}"

def list_trash():
    if not meta:
        print("Trash empty.")
        return

    header = f"{'ID':<8} {'Deleted at':<19} {'Original path'}"
    print(header)
    print('-' * len(header))
    for entry in meta:
        id8 = short_id(entry["id"])
        ts = human_time(entry["timestamp"])
        path = entry["orig_path"]
        max_path_len = 80
        if len(path) > max_path_len:
            path = "…" + path[-(max_path_len - 1):]
        print(f"{id8:<8} {ts:<19} {path}")

def find_candidates(identifier: str) -> List[Dict]:
    # exact basename match first
    exact = [m for m in meta if Path(m["orig_path"]).name == identifier]
    if exact:
        return exact
    # then id prefix match
    id_matches = [m for m in meta if m["id"].startswith(identifier)]
    if id_matches:
        return id_matches

def restore_many(identifiers: List[str]):
    """Restore multiple files, prompting when needed."""
    for identifier in identifiers:
        candidates = find_candidates(identifier)

        if not candidates:
            print(f"No match found for '{identifier}'")
            continue

        # Only one match - restore immediately
        if len(candidates) == 1:
            restore_one(candidates[0])
            continue

        # Multiple matches - prompt user
        print(f"Multiple matches for '{identifier}':")
        for i, entry in enumerate(candidates, start=1):
            print(f"{i}) {short_id(entry['id'])}  {entry['orig_path']}  ({entry['timestamp']})")

        try:
            choice = input("Choose number to restore (or skip): ").strip()
        except KeyboardInterrupt:
            print("\nAborted.")
            return

        if not choice.isdigit():
            print("Skipped.")
            continue

        idx = int(choice) - 1
        if 0 <= idx < len(candidates):
            restore_one(candidates[idx])
        else:
            print("Invalid selection. Skipped.")

def restore_one(entry: Dict) -> bool:
    src = TRASH_DIR / entry["id"]
    dest = Path(entry["orig_path"])
    # If dest exists, restore to current dir with original basename
    if dest.exists():
        dest = Path.cwd() / dest.name
    dest.parent.mkdir(parents=True, exist_ok=True)
    try:
        shutil.move(str(src), str(dest))
    except Exception as e:
        print(f"Failed to restore: {e}")
        return False
    # remove meta entry
    try:
        meta.remove(entry)
        save_meta(meta)
    except ValueError:
        pass
    print(f"Restored to: {dest}")
    return True

def restore(identifier: str):
    candidates = find_candidates(identifier)
    if not candidates:
        print(f"No match found for '{identifier}'")
        return
    if len(candidates) == 1:
        restore_one(candidates[0])
        return
    # multiple candidates -> show list and ask
    print("Multiple matches:")
    for i, e in enumerate(candidates, start=1):
        print(f"{i}) {short_id(e['id'])}  {e['orig_path']}  ({e['timestamp']})")
    try:
        choice = input("Choose number to restore (or abort): ").strip()
    except KeyboardInterrupt:
        print("\nAborted.")
        return
    if not choice.isdigit():
        print("Aborted.")
        return
    idx = int(choice) - 1
    if idx < 0 or idx >= len(candidates):
        print("Invalid selection.")
        return
    restore_one(candidates[idx])

def empty_trash():
    """Permanently remove all trashed files and clear metadata."""
    count = 0
    for entry in list(meta):
        f = TRASH_DIR / entry["id"]
        try:
            if f.exists():
                if f.is_dir():
                    shutil.rmtree(f, ignore_errors=True)
                else:
                    f.unlink(missing_ok=True)
            meta.remove(entry)
            count += 1
        except Exception as e:
            print(f"Failed to remove {f}: {e}")
    save_meta(meta)
    print(f"Trash emptied ({count} entries removed).")

def move_to_trash(path: Path, interactive: bool, force: bool, recursive: bool, skip_trash: bool):
    if not path.exists():
        if force:
            return
        print(f"resrm: cannot remove '{path}': No such file or directory")
        return

    # Interactive prompt
    if interactive:
        try:
            yn = input(f"remove '{path}'? [y/N] ").strip().lower()
        except KeyboardInterrupt:
            print()
            return
        if yn != "y":
            return

    # Permanent delete path
    if skip_trash:
        try:
            if path.is_dir() and not path.is_symlink():
                shutil.rmtree(path)
            else:
                path.unlink()
        except Exception as e:
            print(f"Failed permanent delete: {e}")
        return

    # Prevent non-root user deleting root-owned files
    try:
        st = path.stat()
        if st.st_uid == 0 and os.geteuid() != 0:
            print(f"resrm: permission denied: '{path}' (root-owned file, try sudo)")
            return
    except Exception:
        pass

    # Detect which trash to use (based on file owner)
    try:
        import pwd
        owner_uid = path.stat().st_uid
        owner_info = pwd.getpwuid(owner_uid)
        owner_home = Path(owner_info.pw_dir)
        trash_base = owner_home / ".local" / "share" / "resrm"
    except Exception:
        # fallback if we can't resolve owner
        trash_base = TRASH_DIR.parent

    trash_dir = trash_base / "files"
    meta_file = trash_base / "metadata.json"
    trash_dir.mkdir(parents=True, exist_ok=True)
    meta_file.parent.mkdir(parents=True, exist_ok=True)

    # Try to move file
    uid = uuid.uuid4().hex
    dest = trash_dir / uid
    try:
        shutil.move(str(path), str(dest))
    except Exception as e:
        print(f"Failed to move to trash: {e}")
        return

    # Update metadata (per-owner)
    try:
        if meta_file.exists():
            with meta_file.open("r", encoding="utf-8") as f:
                owner_meta = json.load(f)
        else:
            owner_meta = []
    except Exception:
        owner_meta = []

    entry = {
        "id": uid,
        "orig_path": str(path.resolve()),
        "timestamp": datetime.datetime.now().isoformat()
    }
    owner_meta.append(entry)
    with meta_file.open("w", encoding="utf-8") as f:
        json.dump(owner_meta, f, indent=2, ensure_ascii=False)

    print(f"Removed '{path}' -> trash id {short_id(uid)}")

def main(argv: Optional[List[str]] = None):
    if argv is None:
        argv = sys.argv[1:]
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("paths", nargs="*", help="files to remove")
    parser.add_argument("-r", action="store_true", help="recursive")
    parser.add_argument("-f", "--force", action="store_true", help="force")
    parser.add_argument("-i", action="store_true", help="interactive")
    parser.add_argument("--skip-trash", action="store_true", help="permanent delete")
    parser.add_argument("--restore", nargs="+", help="restore by id or basename")
    parser.add_argument("-l", action="store_true", help="list trash")
    parser.add_argument("--empty", action="store_true", help="empty the trash permanently")
    parser.add_argument("-h", "--help", action="store_true", help="show help")
    args = parser.parse_args(argv)

    # Always print docstring if --help or no args
    if args.help or not argv:
        print(__doc__)
        return

    if args.l:
        list_trash()
        return

    if args.empty:
        empty_trash()
        return

    if args.restore:
        restore_many(args.restore)
        return

    if not args.paths:
        parser.print_help()
        return

    # Process removals
    for p in args.paths:
        pth = Path(p)
        # simplistic recursive handling: if -r not given and it's a directory, mimic rm behavior: error unless -r
        if pth.is_dir() and not args.r:
            if args.f:
                continue
            print(f"resrm: cannot remove '{pth}': Is a directory")
            continue
        move_to_trash(pth, interactive=args.i, force=args.force, recursive=args.r, skip_trash=args.skip_trash)
