# resrm Threat Model and Security Scope

`resrm` is a command-line filesystem utility. It is designed to be executed intentionally by an operator, sometimes with elevated privileges, as a safer replacement for common `rm` usage. By default it moves files and directories into a per-user trash area and records minimal JSON metadata so they can later be listed, inspected, restored, pruned, or permanently emptied.

Because of that design, `resrm`'s security model is different from that of a network service, web application, daemon, sandbox, or setuid program. `resrm` does not attempt to defend against arbitrary local compromise of the account executing it. If an attacker can control the command line, environment, current working directory, installed Python package, metadata file, trash directory, or Python runtime used by the operator, they may be able to influence what `resrm` does. That situation is considered a local trust-boundary failure outside `resrm`'s intended security model.

`resrm` is not a secure deletion tool. It moves files by default and permanently removes files only when requested or when pruning/emptying trash. It does not overwrite storage blocks, wipe free space, defeat snapshots, or guarantee that file contents cannot be recovered by other means.

## Core Assumptions

`resrm` assumes that the person running the tool understands what they are asking it to do.

In particular:

- If `resrm` is run as root, the root user is assumed to control and understand the command line, environment, current working directory, target paths, trash metadata, and installed Python package being used.
- If `--skip-trash` is used, the operator is intentionally bypassing the recoverable trash path and requesting permanent deletion.
- If `--empty` is used, the operator is intentionally permanently deleting the current user's trash contents.
- If `RESRM_TRASH_LIFE` is set, the operator is intentionally controlling the automatic trash retention period.
- The per-user `metadata.json` file and `files/` directory are trusted local state for the user that owns them.
- The operator is expected to understand the impact of running filesystem removal and restore commands as root.

## What resrm Stores

`resrm` stores trashed files and directories in a local per-user trash area.

For the current effective user, the default locations are:

```text
normal users: ~/.local/share/resrm/files
root:         /root/.local/share/resrm/files
metadata:     <trash base>/metadata.json
```

For each trashed item, metadata currently includes:

- A random UUID hex `id`.
- The resolved original path as `orig_path`.
- The deletion timestamp as `timestamp`.

The file or directory contents are moved into:

```text
<trash base>/files/<id>
```

`resrm` does not store:

- File hashes.
- A metadata schema version.
- ACLs as separate structured metadata.
- Extended attributes as separate structured metadata.
- Capabilities as separate structured metadata.
- SELinux, AppArmor, or other MAC labels as separate structured metadata.
- A cryptographic integrity record for metadata or trashed contents.
- A transaction log for crash recovery.

Some filesystem metadata may remain attached to the moved file or directory depending on the filesystem, platform, and `shutil.move()` behaviour. `resrm` does not model that metadata independently.

## What Is In Scope

`resrm` tries to protect careful users and administrators from common accidental deletion mistakes while preserving familiar `rm`-style ergonomics.

In-scope security concerns include:

- Default removal should move files and directories to trash rather than permanently deleting them.
- `--skip-trash` should be the explicit path for immediate permanent deletion.
- `--empty` and automatic pruning should operate within the current user's configured `resrm` trash directory.
- Restore should not overwrite an existing original path; it should fall back to the current directory when the original path exists.
- Non-root users should not be given a false impression that they can manage root-owned files without sudo.
- Root-owned path handling should be explicit and understandable.
- Directory removal should require `-r` unless behaviour is intentionally redesigned.
- Symlink handling should avoid surprising target deletion in permanent-delete paths.
- Metadata parsing failures should not cause arbitrary code execution.
- Shell completion should use local metadata only and should not execute metadata contents.
- `resrm` should not automatically run sudo or otherwise escalate privileges.
- Python and subprocess-free implementation paths should avoid shell injection concerns for ordinary path names.

These measures are defense-in-depth. They are intended to reduce accidental permanent deletion, unexpected overwrite, unsafe restore behaviour, and misleading privilege behaviour when `resrm` is used normally.

## What Is Out Of Scope

The following are generally out of scope and should not be reported as `resrm` vulnerabilities unless they also bypass one of `resrm`'s explicit hardening mechanisms:

- A malicious local user who can already control the invoking user's command line, shell environment, current working directory, Python environment, installed package, or filesystem permissions.
- A root user intentionally deleting dangerous paths with `--skip-trash`.
- A root user intentionally emptying root's trash with `--empty`.
- A user intentionally setting `RESRM_TRASH_LIFE` to a short retention period.
- A user relying on `resrm` as a backup system after trash has been emptied, pruned, moved, corrupted, or manually edited.
- A user relying on `resrm` for secure deletion or anti-forensic wiping.
- A user relying on `resrm` to preserve ACLs, xattrs, capabilities, MAC labels, hard-link relationships, or every filesystem-specific attribute across moves and restores.
- A user relying on `resrm` as a sandbox for untrusted local users or untrusted path names selected by an attacker.
- A compromised system where an attacker already controls the user's trash directory, metadata file, shell, Python packages, environment, or filesystem namespace.
- Reports that amount to "if root runs this tool with malicious options, root can delete or move important files."

`resrm` is a tool for users and administrators, not a sandbox for hostile local users. It cannot make unsafe local trust decisions safe if the operator's own execution environment is already attacker-controlled.

## Trusted Trash Metadata

`resrm` metadata is stored in a local JSON file named `metadata.json` under the user's trash base. This file should be treated as trusted local user state.

Metadata can contain filesystem paths and deletion timestamps. It does not contain a complete copy of filesystem metadata, but it can still reveal sensitive operational details such as filenames, directory layouts, and deletion times.

Before running restore, especially as root, the operator should be confident that the selected trash metadata is the intended local state and has not been tampered with.

`resrm` does not treat an arbitrary attacker-supplied `metadata.json` as untrusted input to be safely enforced. If an attacker can edit metadata, they may be able to influence restore destinations or make restore fail.

## Default Trash Mode

Default removal moves an existing path to a UUID-named location under the selected trash directory and appends a metadata entry.

```bash
resrm file
resrm -r directory
```

For root-owned paths, a non-root process prints a permission message and refuses the default trash operation:

```text
resrm: permission denied: 'path' (root-owned file, try sudo)
```

When possible, default trash mode chooses the trash base from the file owner's home directory. This is intended to support sudo workflows where root removes a user-owned file but the file remains associated with that user's `resrm` trash.

This is convenience behaviour, not a privilege boundary. Operators should still understand which user owns the file, which effective user is running the process, and which trash area will receive the moved object.

## Permanent Deletion Paths

`resrm` has three permanent deletion mechanisms:

```text
resrm --skip-trash PATH     immediate permanent deletion
resrm --empty               permanently remove current user's trash contents
automatic pruning           remove entries older than RESRM_TRASH_LIFE days
```

These operations are not recoverable by `resrm`.

`--skip-trash` uses `shutil.rmtree()` for directories and `Path.unlink()` for non-directories and symlinks. It is the operator's responsibility to use this only when immediate deletion is intended.

`--empty` removes entries inside the current user's trash file directory and clears current metadata.

Automatic pruning runs at the start of every `resrm` invocation. The retention period defaults to 7 days, falls back to 7 for invalid values, and has a minimum of 1 day.

## Restore Behaviour

Restore uses trusted metadata to find the trashed object and original path.

```bash
resrm --restore <id-or-basename>
```

Candidate lookup works as follows:

```text
1. exact basename match against the stored original path
2. id prefix match against the stored UUID
```

If multiple candidates match, `resrm` prompts for a selection.

Restore starts with the stored original path. If that path already exists, `resrm` restores to the current working directory using the original basename instead. This avoids direct overwrite of the original path.

Restore creates parent directories for the selected destination. Because restore destinations come from trusted metadata, metadata tampering is considered a local trust failure rather than something `resrm` promises to sandbox.

## Symlinks And Filesystem Races

`resrm` operates on a live filesystem. Concurrent filesystem changes can affect what exists at the moment a remove, restore, empty, or prune operation runs.

Current symlink behaviour is operation-specific:

- Default trash mode uses `shutil.move()`, which normally moves the symlink itself when the path argument is a symlink.
- `--skip-trash` deletes symlink path entries with `Path.unlink()` rather than recursively deleting their targets.
- `--inspect` uses `lstat()` and displays symlink targets with `os.readlink()`.
- Some ownership checks use `stat()` and therefore follow symlinks.

Reports that identify concrete symlink target deletion, unintended overwrite, or privilege-impacting time-of-check/time-of-use behaviour in normal `resrm` operations are useful. Reports that require the operator's account or root environment to already be attacker-controlled are usually out of scope.

## Local Compromise

`resrm` includes guardrails against some dangerous local mistakes because it handles deletion-like operations. For example, default removal uses trash instead of immediate deletion, directories require `-r`, restore avoids overwriting an existing original path, and `resrm` does not automatically escalate privileges.

However, local compromise cannot be ruled out completely for a CLI filesystem tool. If an attacker can influence the user's shell, environment, metadata file, trash directory, Python packages, current working directory, or command-line arguments, they may be able to influence `resrm`'s behaviour.

Such scenarios are treated as local compromise or operator trust failures, not as vulnerabilities in `resrm` by themselves.

## Security Report Guidance

Useful vulnerability reports include issues where `resrm` behaves unsafely despite the documented trust model. Examples include:

- Default `resrm PATH` permanently deletes a file instead of moving it to trash under normal conditions.
- `--skip-trash` on a symlink deletes the target rather than the symlink path itself.
- Restore overwrites an existing original path without explicit operator approval.
- `--empty` removes files outside the current user's `resrm` trash directory.
- Automatic pruning removes files outside the current user's `resrm` trash directory.
- A non-root user can use normal `resrm` behaviour to move or delete root-owned files without appropriate filesystem permissions.
- Shell completion or metadata parsing executes code from metadata.
- Ordinary path names cause shell injection or command execution.
- A failed safety check is silently ignored and `resrm` proceeds with a dangerous permanent deletion.

Less useful reports, and normally out of scope, include:

- "Root can delete important files with `--skip-trash`."
- "A user can empty their own trash with `--empty`."
- "A user can set `RESRM_TRASH_LIFE=1` and old trash is pruned."
- "A user can manually delete or corrupt their own trash directory."
- "A malicious local user can compromise `resrm` after already controlling the invoking user's environment, Python packages, or filesystem permissions."
- "`resrm` does not securely wipe deleted file contents from disk."
- "`resrm` does not guarantee backup-grade recovery after pruning, emptying, metadata tampering, or filesystem failure."

Reports about concrete bypasses of `resrm`'s guardrails are welcome. The project does not treat intentional administrator-controlled execution as a vulnerability by itself.
