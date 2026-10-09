from __future__ import annotations

import datetime
import json
from pathlib import Path

import pytest

from resrm import core


def _entry(id_, orig_path, timestamp="2026-01-01T00:00:00"):
    return {"id": id_, "orig_path": str(orig_path), "timestamp": timestamp}


def _iso_days_ago(days):
    moment = datetime.datetime.now() - datetime.timedelta(days=days)
    return moment.isoformat()


def test_trash_base_for_root_is_fixed_path():
    assert core.get_trash_base_for_user(0) == Path("/root/.local/share/resrm")


def test_trash_base_uses_user_home(isolated_trash):
    base = core.get_trash_base_for_user(12345)
    assert base == isolated_trash.home / ".local" / "share" / "resrm"


def test_load_meta_missing_file_returns_empty(isolated_trash):
    assert not isolated_trash.meta_file.exists()
    assert core.load_meta() == []


def test_load_meta_malformed_file_returns_empty(isolated_trash):
    isolated_trash.meta_file.write_text("{not json", encoding="utf-8")
    assert core.load_meta() == []


def test_find_candidates_prefers_exact_basename(isolated_trash):
    by_name = _entry("deadbeef" + "0" * 24, "/x/report.txt")
    by_prefix = _entry("report.txt-extra", "/x/notes.md")
    core.meta = [by_prefix, by_name]
    assert core.find_candidates("report.txt") == [by_name]


def test_find_candidates_matches_id_prefix(isolated_trash):
    first = _entry("abcd1234" + "0" * 24, "/x/a")
    second = _entry("abcd9999" + "0" * 24, "/x/b")
    core.meta = [first, second]
    assert core.find_candidates("abcd12") == [first]
    assert core.find_candidates("abcd") == [first, second]
    assert core.find_candidates("zzz") == []


def test_move_to_trash_moves_file_and_writes_metadata(
    isolated_trash, tmp_path
):
    src = tmp_path / "keep.txt"
    src.write_text("data", encoding="utf-8")

    core.move_to_trash(src, interactive=False, force=False, skip_trash=False)

    assert not src.exists()
    stored = list(isolated_trash.trash_dir.iterdir())
    assert len(stored) == 1
    saved = json.loads(isolated_trash.meta_file.read_text(encoding="utf-8"))
    assert saved[0]["orig_path"] == str(src.resolve())
    assert saved[0]["id"] == stored[0].name


def test_skip_trash_deletes_file_permanently(isolated_trash, tmp_path):
    src = tmp_path / "gone.txt"
    src.write_text("x", encoding="utf-8")

    core.move_to_trash(src, interactive=False, force=False, skip_trash=True)

    assert not src.exists()
    assert list(isolated_trash.trash_dir.iterdir()) == []
    assert core.load_meta() == []


def test_skip_trash_removes_symlink_not_target(isolated_trash, tmp_path):
    target = tmp_path / "target.txt"
    target.write_text("data", encoding="utf-8")
    link = tmp_path / "link.txt"
    link.symlink_to(target)

    core.move_to_trash(link, interactive=False, force=False, skip_trash=True)

    assert not link.exists()
    assert target.exists()


def test_missing_path_without_force_reports_error(
    isolated_trash, tmp_path, capsys
):
    missing = tmp_path / "nope.txt"
    core.move_to_trash(
        missing, interactive=False, force=False, skip_trash=False
    )
    assert "No such file or directory" in capsys.readouterr().out


def test_missing_path_with_force_is_silent(isolated_trash, tmp_path, capsys):
    missing = tmp_path / "nope.txt"
    core.move_to_trash(
        missing, interactive=False, force=True, skip_trash=False
    )
    assert capsys.readouterr().out == ""


def test_directory_without_recursive_is_rejected(
    isolated_trash, tmp_path, capsys
):
    directory = tmp_path / "adir"
    directory.mkdir()

    core.main([str(directory)])

    assert "Is a directory" in capsys.readouterr().out
    assert directory.is_dir()


def test_restore_one_returns_to_original_path(isolated_trash, tmp_path):
    original = tmp_path / "restored.txt"
    stored = isolated_trash.trash_dir / ("a" * 32)
    stored.write_text("data", encoding="utf-8")
    entry = _entry("a" * 32, original)
    core.meta = [entry]

    assert core.restore_one(entry) is True

    assert original.read_text(encoding="utf-8") == "data"
    assert not stored.exists()
    assert core.meta == []
    assert core.load_meta() == []


def test_restore_one_falls_back_to_cwd_when_original_exists(
    isolated_trash, tmp_path
):
    (tmp_path / "sub").mkdir()
    original = tmp_path / "sub" / "taken.txt"
    original.write_text("original", encoding="utf-8")
    stored = isolated_trash.trash_dir / ("b" * 32)
    stored.write_text("trashed", encoding="utf-8")
    entry = _entry("b" * 32, original)
    core.meta = [entry]

    assert core.restore_one(entry) is True

    fallback = tmp_path / "taken.txt"
    assert fallback.read_text(encoding="utf-8") == "trashed"
    assert original.read_text(encoding="utf-8") == "original"


@pytest.mark.parametrize(
    "life, days_old, expect_pruned",
    [
        ("7", 10, True),
        ("7", 1, False),
        ("not-a-number", 10, True),
        ("0", 2, True),
    ],
)
def test_prune_old_trash_retention(
    isolated_trash, monkeypatch, life, days_old, expect_pruned
):
    monkeypatch.setenv("RESRM_TRASH_LIFE", life)
    old = isolated_trash.trash_dir / ("c" * 32)
    old.write_text("old", encoding="utf-8")
    entry = _entry("c" * 32, "/x/old.txt", timestamp=_iso_days_ago(days_old))
    core.meta = [entry]

    core.prune_old_trash()

    if expect_pruned:
        assert not old.exists()
        assert core.meta == []
    else:
        assert old.exists()
        assert core.meta == [entry]


def test_empty_trash_clears_files_and_metadata(isolated_trash):
    file_entry = isolated_trash.trash_dir / ("d" * 32)
    file_entry.write_text("1", encoding="utf-8")
    dir_entry = isolated_trash.trash_dir / ("e" * 32)
    dir_entry.mkdir()
    (dir_entry / "inner").write_text("2", encoding="utf-8")
    core.meta = [_entry("d" * 32, "/x/1"), _entry("e" * 32, "/x/2")]

    core.empty_trash()

    assert list(isolated_trash.trash_dir.iterdir()) == []
    assert core.meta == []
    saved = json.loads(isolated_trash.meta_file.read_text(encoding="utf-8"))
    assert saved == []
