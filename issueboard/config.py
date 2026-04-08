import json
import time
from pathlib import Path

CONFIG_PATH = Path.home() / ".issueboard" / "config.json"
CACHE_PATH  = Path.home() / ".issueboard" / "cache.json"
STATE_PATH  = Path.home() / ".issueboard" / "state.json"
CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)


def load_config() -> dict:
    if CONFIG_PATH.exists():
        try:
            return json.loads(CONFIG_PATH.read_text())
        except Exception:
            pass
    return {}


def save_config(cfg: dict):
    CONFIG_PATH.write_text(json.dumps(cfg, indent=2))


CACHE_TTL = 300


def load_cache() -> tuple[list[dict], float]:
    if CACHE_PATH.exists():
        try:
            data = json.loads(CACHE_PATH.read_text())
            return data.get("issues", []), data.get("ts", 0.0)
        except Exception:
            pass
    return [], 0.0


def save_cache(issues: list[dict]):
    data = {"ts": time.time(), "issues": issues}
    CACHE_PATH.write_text(json.dumps(data, indent=2))


def cache_is_fresh(ts: float) -> bool:
    return (time.time() - ts) < CACHE_TTL


def load_state() -> dict:
    if STATE_PATH.exists():
        try:
            return json.loads(STATE_PATH.read_text())
        except Exception:
            pass
    return {"wip_ids": [], "closed_ids": []}


def save_state(wip_ids: set, closed_ids: set):
    data = {
        "wip_ids":    list(wip_ids),
        "closed_ids": list(closed_ids),
    }
    STATE_PATH.write_text(json.dumps(data, indent=2))
