import os
import re
from dataclasses import dataclass
from typing import Literal

# Appendix B & §4 default constants
MAX_STEPS = int(os.getenv("MAX_STEPS", "40"))
MAX_PATCHES = int(os.getenv("MAX_PATCHES", "3"))
CRITIC_ROUNDS_MAX = int(os.getenv("CRITIC_ROUNDS_MAX", "2"))
RUN_TIMEOUT_S = int(os.getenv("RUN_TIMEOUT_S", "600"))
INSTALL_TIMEOUT_S = int(os.getenv("INSTALL_TIMEOUT_S", "300"))
DIAGNOSE_STEPS_MAX = int(os.getenv("DIAGNOSE_STEPS_MAX", "8"))
MAX_FILES = int(os.getenv("MAX_FILES", "5"))
MAX_CHANGED_LINES = int(os.getenv("MAX_CHANGED_LINES", "200"))
LARGE_PATCH_FILES = int(os.getenv("LARGE_PATCH_FILES", "2"))
LARGE_PATCH_LINES = int(os.getenv("LARGE_PATCH_LINES", "20"))
LOG_CAP_BYTES = int(os.getenv("LOG_CAP_BYTES", "2000000"))

# Provider settings
SOLVER_PROVIDER = os.getenv("SOLVER_PROVIDER", "gemini")
SOLVER_MODEL = os.getenv("SOLVER_MODEL", "gemini-3.1-flash-lite")
SOLVER_BASE_URL = os.getenv("SOLVER_BASE_URL", "https://generativelanguage.googleapis.com/v1beta/gemini")
SOLVER_API_KEY = os.getenv("SOLVER_API_KEY", "")

CRITIC_PROVIDER = os.getenv("CRITIC_PROVIDER", "gemini")
CRITIC_MODEL = os.getenv("CRITIC_MODEL", "gemini-3.1-flash-lite")
CRITIC_BASE_URL = os.getenv("CRITIC_BASE_URL", "https://generativelanguage.googleapis.com/v1beta/gemini")
CRITIC_API_KEY = os.getenv("CRITIC_API_KEY", "")

FALLBACK_PROVIDER = os.getenv("FALLBACK_PROVIDER", "gemini")
FALLBACK_MODEL = os.getenv("FALLBACK_MODEL", "gemini-3.1-flash-lite")
FALLBACK_BASE_URL = os.getenv("FALLBACK_BASE_URL", "https://generativelanguage.googleapis.com/v1beta/gemini")
FALLBACK_API_KEY = os.getenv("FALLBACK_API_KEY", "")

CASSETTE_DIR = os.getenv("CASSETTE_DIR", "data/cassettes")
LLM_MODE = os.getenv("LLM_MODE", "live")  # live | record | replay

SECRET_PATTERNS = [
    r"sk-[a-zA-Z0-9_\-]{20,}",
    r"ghp_[a-zA-Z0-9]{20,}",
    r"(?i)(?:api_key|apikey|secret|password|token)\s*[:=]\s*['\"]?([a-zA-Z0-9_\-\.]{8,})['\"]?"
]

def scrub_secrets(text: str) -> str:
    """Scrub potential secrets, API keys, and sensitive tokens from strings."""
    if not isinstance(text, str):
        return text
    scrubbed = text
    # Known key values in env
    keys_to_mask = [SOLVER_API_KEY, CRITIC_API_KEY, FALLBACK_API_KEY]
    for k in keys_to_mask:
        if k and len(k) > 4:
            scrubbed = scrubbed.replace(k, "[REDACTED_API_KEY]")
            
    for pat in SECRET_PATTERNS:
        scrubbed = re.sub(pat, "[REDACTED_SECRET]", scrubbed)
    return scrubbed

