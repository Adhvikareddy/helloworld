"""
Q-SENTINEL Attack Harness Configuration.

Centralises API target, default parameters, and experiment constants
so every attack scenario uses the same source of truth.
"""
import os

API_URL = os.getenv("QSENTINEL_API_URL", "http://qsentinel-api:8000")
DB_PATH = os.getenv("QSENTINEL_DB_PATH", "/app/data/ledger.db")

DEFAULT_SHOTS = int(os.getenv("QSENTINEL_DEFAULT_SHOTS", "1024"))
DEFAULT_SEED = int(os.getenv("QSENTINEL_DEFAULT_SEED", "42"))

# Channel disturbance presets — documented numerical sweep
DISTURBANCE_LEVELS = {
    "low":    0.10,
    "medium": 0.25,
    "high":   0.50,
}

# Valid-path forgery experiment — predeclared population size
FORGERY_B_POPULATION = int(os.getenv("QSENTINEL_FORGERY_B_POPULATION", "20"))

# Replay / impersonation repeat count
DEFAULT_REPEAT_COUNT = int(os.getenv("QSENTINEL_REPEAT_COUNT", "5"))
