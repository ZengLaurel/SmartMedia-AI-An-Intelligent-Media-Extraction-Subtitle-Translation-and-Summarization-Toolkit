"""Configuration and API key management.

API keys are read from environment variables, optionally supplemented by a
local `.env` file (version-control excluded, per IFR-06 / C4 / NFR-07).
"""

import os

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass


def _get(name: str, default: str | None = None) -> str | None:
    value = os.environ.get(name, default)
    if value is not None:
        value = value.strip()
        if value == "":
            value = default
    return value


ASR_API_KEY = _get("ASR_API_KEY")
ASR_API_BASE = _get("ASR_API_BASE")

TRANSLATION_API_KEY = _get("TRANSLATION_API_KEY")
TRANSLATION_API_BASE = _get("TRANSLATION_API_BASE")

SUMMARIZATION_API_KEY = _get("SUMMARIZATION_API_KEY")
SUMMARIZATION_API_BASE = _get("SUMMARIZATION_API_BASE")

# A single shared key is also accepted for convenience.
GENERIC_API_KEY = _get("SMARTMEDIA_API_KEY")

OUTPUT_DIR = _get("OUTPUT_DIR", "output")
TEMP_DIR = _get("TEMP_DIR", "temp")

MAX_AUDIO_SEGMENT_SECONDS = int(_get("MAX_AUDIO_SEGMENT_SECONDS", "1800"))
MAX_CONCURRENT_DOWNLOADS = int(_get("MAX_CONCURRENT_DOWNLOADS", "3"))


def require_api_key(name: str) -> str:
    """Return the API key for the given service, or raise a clear error."""
    candidates = {
        "asr": [ASR_API_KEY, GENERIC_API_KEY],
        "translation": [TRANSLATION_API_KEY, GENERIC_API_KEY],
        "summarization": [SUMMARIZATION_API_KEY, GENERIC_API_KEY],
    }
    for key in candidates.get(name.lower(), []):
        if key:
            return key
    raise ValueError(
        f"API key for '{name}' is not configured. "
        f"Set the corresponding environment variable or add it to your .env file."
    )
