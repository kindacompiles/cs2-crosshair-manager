import copy
import json
import platform
from pathlib import Path

CONFIG_FILE = Path(__file__).parent / "config.json"

DEFAULT_CONFIG = {
    "cs2_cfg_path": "",
    "crosshairs": {},
    "cycle_letters": [],
    "cycle_bind": "",
}

_CS2_SUBPATH = "steamapps/common/Counter-Strike Global Offensive/game/csgo/cfg"

_SEARCH_PATHS = {
    "linux": [
        Path.home() / ".local/share/Steam" / _CS2_SUBPATH,
        Path.home() / "Steam" / _CS2_SUBPATH,
        Path.home() / ".steam/steam" / _CS2_SUBPATH,
    ],
    "windows": [
        Path("C:/Program Files (x86)/Steam") / _CS2_SUBPATH,
        Path("C:/Program Files/Steam") / _CS2_SUBPATH,
    ],
    "darwin": [
        Path.home() / "Library/Application Support/Steam" / _CS2_SUBPATH,
    ],
}


class ConfigError(Exception):
    pass


def default_config():
    return copy.deepcopy(DEFAULT_CONFIG)


def load():
    if not CONFIG_FILE.exists():
        return default_config()

    try:
        data = json.loads(CONFIG_FILE.read_text())
    except json.JSONDecodeError as exc:
        broken = CONFIG_FILE.with_suffix(".json.broken")
        CONFIG_FILE.replace(broken)
        raise ConfigError(f"config.json was invalid, so it was moved to {broken.name}.") from exc

    if not isinstance(data, dict):
        raise ConfigError("config.json must contain a JSON object.")

    config = default_config()
    config.update(data)
    if not isinstance(config.get("crosshairs"), dict):
        config["crosshairs"] = {}
    if not isinstance(config.get("cycle_letters"), list):
        config["cycle_letters"] = []
    return config


def save(config):
    CONFIG_FILE.write_text(json.dumps(config, indent=2) + "\n")


def detect_cs2_path():
    system = platform.system().lower()
    for path in _SEARCH_PATHS.get(system, []):
        if path.exists():
            return str(path)
    return ""
