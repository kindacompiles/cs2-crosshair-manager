import re

from csxhair import Crosshair

_SHARE_CODE_RE = re.compile(r"CSGO-[A-Za-z0-9]{5}(?:-[A-Za-z0-9]{5}){4}")
_CVAR_RE = re.compile(r"^cl_crosshair[A-Za-z0-9_]*$")

BOOL_CVARS = {
    "cl_crosshairusealpha",
    "cl_crosshair_drawoutline",
    "cl_crosshair_recoil",
    "cl_crosshairdot",
    "cl_crosshair_t",
    "cl_crosshairgap_useweaponvalue",
}


def _parse_number(raw):
    try:
        return int(raw)
    except ValueError:
        return float(raw)


def _parse_bool(raw):
    raw = raw.lower()
    if raw in {"true", "1"}:
        return 1
    if raw in {"false", "0"}:
        return 0
    raise ValueError(raw)


def find_share_code(text):
    match = _SHARE_CODE_RE.search(text.strip())
    return match.group(0) if match else ""


def _parse_command_lines(lines):
    result = {}

    for line in lines:
        line = line.strip()
        if line.startswith("[Console]"):
            line = line[len("[Console]") :].strip()

        parts = line.split()
        if len(parts) < 2:
            continue

        cvar_name = parts[0]
        if not _CVAR_RE.fullmatch(cvar_name):
            continue

        raw_val = parts[1].strip('"')
        try:
            if raw_val.lower() in {"true", "false"} or cvar_name in BOOL_CVARS:
                result[cvar_name] = _parse_bool(raw_val)
            else:
                result[cvar_name] = _parse_number(raw_val)
        except ValueError:
            continue

    return result


def parse(text):
    return _parse_command_lines(text.splitlines())


def decode_share_code(code):
    commands = Crosshair.decode(code).cs2_commands
    return _parse_command_lines(commands)


def is_valid(data):
    required = {"cl_crosshairstyle", "cl_crosshairsize", "cl_crosshairgap"}
    return required.issubset(data.keys())
