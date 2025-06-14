import os
import base64
import re
from pathlib import Path
from typing import Dict, Optional

from ecies import decrypt

_PREFIX = "encrypted:"


def _private_key_name(path: str) -> str:
    name = Path(path).name
    if name == ".env":
        return "DOTENV_PRIVATE_KEY"
    if name.startswith(".env."):
        env = name.split(".", 1)[1]
        return f"DOTENV_PRIVATE_KEY_{env.upper()}"
    return "DOTENV_PRIVATE_KEY"


def _find_private_key(env_path: str, keys_path: Optional[str]) -> Optional[str]:
    key_name = _private_key_name(env_path)
    if os.getenv(key_name):
        return os.getenv(key_name)

    keys_file = Path(keys_path) if keys_path else Path(env_path).with_name(".env.keys")
    if keys_file.exists():
        pattern = re.compile(rf"^\s*{re.escape(key_name)}\s*=\s*(.+)")
        for line in keys_file.read_text().splitlines():
            m = pattern.match(line)
            if m:
                return m.group(1).strip()
    return None


def _decrypt(value: str, private_key: str) -> str:
    if not value.startswith(_PREFIX):
        return value
    data = base64.b64decode(value[len(_PREFIX) :])
    secret = bytes.fromhex(private_key)
    return decrypt(secret, data).decode()


def load(path: str = ".env", *, override: bool = False, keys_path: Optional[str] = None) -> Dict[str, str]:
    env_path = Path(path)
    if not env_path.exists():
        raise FileNotFoundError(env_path)
    private_key = _find_private_key(str(env_path), keys_path)

    loaded: Dict[str, str] = {}
    for line in env_path.read_text().splitlines():
        if line.strip().startswith("#") or "=" not in line:
            continue
        key, val = line.split("=", 1)
        key = key.strip()
        val = val.strip()
        if private_key:
            try:
                val = _decrypt(val, private_key)
            except Exception:
                pass
        if key in os.environ and not override:
            loaded[key] = os.environ[key]
            continue
        os.environ[key] = val
        loaded[key] = val
    return loaded

