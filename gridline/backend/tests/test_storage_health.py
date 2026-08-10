"""The storage writability probe.

Regression cover for a failure that only appeared under Docker: a named volume
mounted over a path that does not exist in the image is created root-owned, so a
non-root container hits PermissionError on the first photo write. The user saw
only "internal server error" — the probe makes it visible in /health instead.
"""

from __future__ import annotations

import os

import pytest

from app.services import storage


@pytest.fixture(autouse=True)
def _reset():
    storage.reset_backend()
    yield
    storage.reset_backend()


def test_reports_local_when_the_directory_is_writable(monkeypatch, tmp_path):
    from app.config import settings

    monkeypatch.setattr(settings, "local_storage_dir", str(tmp_path / "photos"))
    assert storage.storage_status() == "local"


def test_reports_unwritable_when_permissions_deny_writes(monkeypatch, tmp_path):
    if os.geteuid() == 0:
        pytest.skip("root ignores directory permissions")

    locked = tmp_path / "locked"
    locked.mkdir()
    locked.chmod(0o500)  # r-x: the exact shape of a root-owned volume mount

    from app.config import settings

    monkeypatch.setattr(settings, "local_storage_dir", str(locked))
    status = storage.storage_status()
    assert status.startswith("unwritable")
    assert "PermissionError" in status


def test_probe_leaves_no_file_behind(monkeypatch, tmp_path):
    from app.config import settings

    root = tmp_path / "photos"
    monkeypatch.setattr(settings, "local_storage_dir", str(root))
    storage.storage_status()
    assert list(root.iterdir()) == []
