from __future__ import annotations

from types import SimpleNamespace

import pytest

from resrm import core


@pytest.fixture(autouse=True)
def isolated_trash(tmp_path, monkeypatch):
    """Redirect all trash state into a temporary tree.

    resrm resolves the trash base from the file owner's home directory and
    loads metadata once at import time, so both are redirected here.
    Without this fixture a test that moved a file would write into the
    real ``~/.local/share/resrm``.
    """
    home = tmp_path / "home"
    base = home / ".local" / "share" / "resrm"
    trash_dir = base / "files"
    meta_file = base / "metadata.json"
    trash_dir.mkdir(parents=True, exist_ok=True)

    monkeypatch.setattr(core, "TRASH_DIR", trash_dir)
    monkeypatch.setattr(core, "META_FILE", meta_file)
    monkeypatch.setattr(core, "meta", [])

    # move_to_trash() and get_trash_base_for_user() import pwd locally and
    # resolve the owner's home, so patch the module attribute rather than
    # core's namespace.
    monkeypatch.setattr(
        "pwd.getpwuid", lambda uid: SimpleNamespace(pw_dir=str(home))
    )

    monkeypatch.chdir(tmp_path)
    return SimpleNamespace(home=home, trash_dir=trash_dir, meta_file=meta_file)
