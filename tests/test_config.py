"""Tests for config.py — API key loading from environment / .env."""

import importlib

import config


def test_missing_key_raises(monkeypatch):
    monkeypatch.delenv("ASR_API_KEY", raising=False)
    monkeypatch.delenv("SMARTMEDIA_API_KEY", raising=False)
    importlib.reload(config)
    try:
        try:
            config.require_api_key("asr")
            raised = False
        except ValueError:
            raised = True
        assert raised
    finally:
        importlib.reload(config)


def test_env_key_is_picked_up(monkeypatch):
    monkeypatch.setenv("ASR_API_KEY", "test-key-123")
    importlib.reload(config)
    try:
        assert config.require_api_key("asr") == "test-key-123"
    finally:
        importlib.reload(config)
