[![License](https://img.shields.io/github/license/guardutils/resrm?style=flat)](LICENCE)
[![Language](https://img.shields.io/github/languages/top/guardutils/resrm.svg)](https://github.com/guardutils/resrm/)
![GitHub Release](https://img.shields.io/github/v/release/guardutils/resrm?display_name=release&logo=github)
![PyPI - Version](https://img.shields.io/pypi/v/resrm?logo=pypi)
[![PyPI downloads](https://img.shields.io/pypi/dm/resrm.svg)](https://pypi.org/project/resrm/)

# resrm

**resrm** is a safe, drop-in replacement for the Linux `rm` command with **undo/restore support**.
It moves files to a per-user _trash_ instead of permanently deleting them, while still allowing full `sudo` support for root-owned files.

---

## Features

- Move files and directories to a **Trash folder** instead of permanent deletion
- Restore deleted files by **short ID or exact basename**
- Empty trash safely
- Supports `-r`, `-f`, `-i`, `--skip-trash` options
- Works with `sudo` for root-owned files
- Automatically prunes Trash entries older than `$RESRM_TRASH_LIFE` days (default **7**, minimum **1**)

  > Note: if you need immediate deletion, use the `--skip-trash` flag.

---

## Configuration

To control how long trashed files are kept, add this line to your shell configuration (e.g. `~/.bashrc`):

```bash
export RESRM_TRASH_LIFE=10
```

---

## Installation

### From package manager

This is the preferred method of installation.

**Ubuntu 22.04 and 24.04**
```
sudo add-apt-repository ppa:mdaleo/resrm
sudo apt update
sudo apt install resrm
```

**Fedora 41, 42, 43**
```
sudo dnf copr enable mdaleo/resrm
sudo dnf install resrm
```

### From PyPI

**NOTE:** To use `resrm` with `sudo`, the path to `resrm` must be in the `$PATH` seen by `root`.\
Either:

 * install `resrm` as `root`, or
 * add the path to `resrm` to the `secure_path` parameter in `/etc/sudoers`. For example, where `/home/user/.local/bin` is where `resrm` is:

``` bash
Defaults secure_path="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/home/user/.local/bin"
```

Install with:

```bash
pip install resrm
```

### From this repository

```bash
git clone https://github.com/guardutils/resrm.git
cd resrm/
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
resrm --skip-trash file

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

## pre-commit
This project uses [**pre-commit**](https://pre-commit.com/) to run automatic formatting and security checks before each commit (Black, Bandit, and various safety checks).

To enable it:
```
poetry install
poetry run pre-commit install
```
This ensures consistent formatting, catches common issues early, and keeps the codebase clean.
