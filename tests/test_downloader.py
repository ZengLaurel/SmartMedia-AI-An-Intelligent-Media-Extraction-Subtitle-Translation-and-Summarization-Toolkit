"""Tests for downloader.py — roadmap Phase 1, Step 1 (local file import)."""

from pathlib import Path

import pytest

from downloader import InputValidationError, import_local_file


def test_import_local_file(tmp_path):
    media_file = tmp_path / "sample.mp4"
    media_file.write_bytes(b"fake video bytes")

    result = import_local_file(str(media_file))

    assert result == media_file
    assert isinstance(result, Path)


def test_validate_url_and_file_input_missing_file(tmp_path):
    missing = tmp_path / "does_not_exist.mp4"

    with pytest.raises(InputValidationError):
        import_local_file(str(missing))


def test_validate_url_and_file_input_unsupported_extension(tmp_path):
    bad_file = tmp_path / "notes.txt"
    bad_file.write_text("not media")

    with pytest.raises(InputValidationError):
        import_local_file(str(bad_file))


def test_validate_url_and_file_input_directory_rejected(tmp_path):
    with pytest.raises(InputValidationError):
        import_local_file(str(tmp_path))
