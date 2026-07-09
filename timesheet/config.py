"""Config file handling.

Config lives at ~/.config/timesheet/config.yaml by default (override with
--config / TIMESHEET_CONFIG env var). Secrets (API tokens) are NOT stored in
this file -- they're read from environment variables. Everything else
(recurring meetings, epic->Harvest mappings, fill-list, ratios) lives here
and is edited by the CLI as you go.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml

from dotenv import load_dotenv

load_dotenv()


CREDENTIAL_ENV_VARS = {
    "jira_api_token": "JIRA_API_TOKEN",
    "jira_base_url": "JIRA_BASE_URL",
    "jira_email": "JIRA_EMAIL",
    "harvest_access_token": "HARVEST_ACCESS_TOKEN",
    "harvest_account_id": "HARVEST_ACCOUNT_ID",
}


def config_path(override: str | None = None) -> Path:
    return Path(override) if override else DEFAULT_CONFIG_PATH


def load_config(path: Path | None = None) -> dict[str, Any]:
    path = path or DEFAULT_CONFIG_PATH
    if not path.exists():
        raise FileNotFoundError(
            f"No config found at {path}. Run `timesheet config init` first."
        )
    with open(path) as f:
        data = yaml.safe_load(f) or {}
    return _deep_merge(DEFAULT_CONFIG, data)


def save_config(cfg: dict[str, Any], path: Path | None = None) -> None:
    path = path or DEFAULT_CONFIG_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        yaml.safe_dump(cfg, f, sort_keys=False, default_flow_style=False)


def _deep_merge(base: dict, override: dict) -> dict:
    result = dict(base)
    for k, v in override.items():
        if isinstance(v, dict) and isinstance(result.get(k), dict):
            result[k] = _deep_merge(result[k], v)
        else:
            result[k] = v
    return result


def get_secret(name: str) -> str:
    """name is one of CREDENTIAL_ENV_VARS keys, e.g. 'jira_api_token'."""
    env_var = CREDENTIAL_ENV_VARS[name]
    val = os.environ.get(env_var)
    if not val:
        raise RuntimeError(
            f"Missing required environment variable {env_var}. "
            f"Export it before running timesheet (e.g. in your shell rc file)."
        )
    return val


DEFAULT_CONFIG_PATH = Path(
    os.environ.get(
        "TIMESHEET_CONFIG",
        str(Path.home() / ".config" / "timesheet" / "config.yaml"),
    )
)

DEFAULT_CONFIG: dict[str, Any] = {
    "jira": {
        "base_url": get_secret(name="jira_base_url"),
        "email": get_secret(name="jira_email"),
        # JQL used to find issues you worked on in the target week.
        # {start} / {end} are substituted as YYYY-MM-DD.
        "jql": (
            "status CHANGED by currentUser() DURING ({start}, {end})"
        ),
        # Custom field id holding story points, e.g. "customfield_10016".
        "story_points_field": "customfield_10016",
        # Custom field id for the classic "Epic Link" field. Only used as a
        # fallback if the issue has no `parent` (team-managed projects use
        # `parent` directly for epics).
        "epic_link_field": "customfield_10014",
    },
    "harvest": {
        "account_id": get_secret(name="harvest_account_id"),
    },
    "points_to_hours_ratio": 12,
    "hours_per_day": 7.5,
    "work_days": ["mon", "tue", "wed", "thu", "fri"],
    "recurring": [],
    "epic_mapping": {},
    "fill_projects": [],
}
