from __future__ import annotations

import os
from pathlib import Path


def load_env(env_dir: str = "env", filename: str = ".env") -> None:
    """Load simple KEY=VALUE pairs from an env file into os.environ if not already set.

    Looks for <cwd>/env/.env by default. Silently returns if file not found.
    """
    env_path = Path.cwd() / env_dir / filename
    if not env_path.exists():
        return

    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, val = line.split("=", 1)
        key = key.strip()
        val = val.strip().strip('"').strip("'")
        # Only set if not already in the environment
        if key and key not in os.environ:
            os.environ[key] = val
