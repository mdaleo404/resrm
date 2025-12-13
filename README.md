[![Licence](https://img.shields.io/badge/GPL--3.0-orange?label=Licence)](https://git.sysmd.uk/guardutils/resrm/src/branch/main/LICENCE)
[![Gitea Release](https://img.shields.io/gitea/v/release/guardutils/resrm?gitea_url=https%3A%2F%2Fgit.sysmd.uk%2F&style=flat&color=orange&logo=gitea)](https://git.sysmd.uk/guardutils/resrm/releases)
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-blue?logo=pre-commit&style=flat)](https://git.sysmd.uk/guardutils/resrm/src/branch/main/.pre-commit-config.yaml)

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


## Installation

### From GuardUtils package repo

This is the preferred method of installation.

### Debian/Ubuntu

#### 1) Import the GPG key

```bash
sudo mkdir -p /usr/share/keyrings
curl -fsSL https://repo.sysmd.uk/guardutils/guardutils.gpg | sudo gpg --dearmor -o /usr/share/keyrings/guardutils.gpg
```

The GPG fingerprint is `0032C71FA6A11EF9567D4434C5C06BD4603C28B1`.

#### 2) Add the APT source

```bash
echo "deb [arch=amd64 signed-by=/usr/share/keyrings/guardutils.gpg] https://repo.sysmd.uk/guardutils/debian stable main" | sudo tee /etc/apt/sources.list.d/guardutils.list
```

#### 3) Update and install

```
sudo apt update
sudo apt install resrm
```

### Fedora/RHEL

#### 1) Import the GPG key

```
sudo rpm --import https://repo.sysmd.uk/guardutils/guardutils.gpg
```

#### 2) Add the repository configuration

```
sudo tee /etc/yum.repos.d/guardutils.repo > /dev/null << 'EOF'
[guardutils]
name=GuardUtils Repository
baseurl=https://repo.sysmd.uk/guardutils/rpm/$basearch
enabled=1
gpgcheck=1
repo_gpgcheck=1
gpgkey=https://repo.sysmd.uk/guardutils/guardutils.gpg
EOF
```

#### 4) Update and install

```
sudo dnf upgrade --refresh
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
git clone https://git.sysmd.uk/guardutils/resrm.git
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

# Show full details of trashed item
resrm --inspect <id|name>

# Empty the trash permanently
resrm --empty
```


## Trash Location

Normal users: `~/.local/share/resrm/files`

Root user: `/root/.local/share/resrm/files`

## Configuration

To control how long trashed files are kept, add this line to your shell configuration (e.g. `~/.bashrc`):

```bash
export RESRM_TRASH_LIFE=10
```

### TAB completion
Add this to your `.bashrc`
```
eval "$(register-python-argcomplete resrm)"
```
And then
```
source ~/.bashrc
```

## pre-commit
This project uses [**pre-commit**](https://pre-commit.com/) to run automatic formatting and security checks before each commit (Black, Bandit, and various safety checks).

To enable it:
```
poetry install
poetry run pre-commit install
```
This ensures consistent formatting, catches common issues early, and keeps the codebase clean.
