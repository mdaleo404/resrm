# resrm

**resrm** is a safe, drop-in replacement for the Linux `rm` command with **undo/restore support**.  
It moves files to a per-user _trash_ instead of permanently deleting them, while still allowing full `sudo` support for root-owned files.

---

## Features

- Move files and directories to a **trash folder** instead of permanent deletion  
- Restore deleted files by **short ID or exact basename**  
- Empty trash safely  
- Supports `-r`, `-f`, `-i`, `--perma` options  
- Works with `sudo` for root-owned files  

---

## Installation

**NOTE:** To use `resrm` with `sudo`, the path to `resrm` must be in the `$PATH` seen by `root`.\
Either install `resrm` as `root` (_preferred_), use `sudo -E resrm`, or add the `$PATH` to `/etc/sudoers` using its `Defaults secure_path` parameter.

Install via PyPI (_preferred_):

```bash
pip install resrm
```

Or clone the repo and install locally:

```bash
git clone https://github.com/mdaleo404/resrm.git
cd resrm/resrm
poetry install
```

## Usage

```bash
# Move files to trash
resrm file1 file2

# Recursive remove of a directory
resrm -r mydir

# Force remove (ignore nonexistent)
resrm -f file

# Interactive remove
resrm -i file

# Permanent delete (bypass trash)
resrm --perma file

# List trash entries
resrm -l

# Restore a file by ID or basename
resrm --restore <id|name>

# Empty the trash permanently
resrm --empty
```

## Trash Location

Normal users: `~/.local/share/resrm/files`

Root user: `/root/.local/share/resrm/files`