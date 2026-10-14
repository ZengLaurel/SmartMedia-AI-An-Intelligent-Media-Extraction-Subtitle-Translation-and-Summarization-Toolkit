"""Smoke tests — verifies the package scaffolding imports cleanly."""

import cli_main
import config
import downloader
import media_processor
import ai_engine
import subtitle_generator
import summarizer
import utils


def test_modules_importable():
    assert config is not None
    assert downloader is not None
    assert media_processor is not None
    assert ai_engine is not None
    assert subtitle_generator is not None
    assert summarizer is not None
    assert utils is not None


def test_cli_requires_input():
    try:
        cli_main.main([])
        asserted = False
    except SystemExit:
        asserted = True
    assert asserted
