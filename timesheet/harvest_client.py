"""Minimal Harvest v2 REST client."""
from __future__ import annotations

from dataclasses import dataclass

import requests

API_BASE = "https://api.harvestapp.com/v2"


@dataclass
class HarvestProject:
    id: int
    name: str
    code: str | None


@dataclass
class HarvestTask:
    id: int
    name: str


class HarvestClient:
    def __init__(self, account_id: str, access_token: str):
        self.session = requests.Session()
        self.session.headers.update({
            "Harvest-Account-Id": str(account_id),
            "Authorization": f"Bearer {access_token}",
            "User-Agent": "timesheet-cli (personal use)",
        })

    def list_active_projects(self) -> list[HarvestProject]:
        projects: list[HarvestProject] = []
        url = f"{API_BASE}/projects"
        params = {"is_active": "true", "per_page": 100}
        while url:
            resp = self.session.get(url, params=params)
            resp.raise_for_status()
            data = resp.json()
            for p in data.get("projects", []):
                projects.append(
                    HarvestProject(id=p["id"], name=p["name"], code=p.get("code"))
                )
            url = data.get("links", {}).get("next")
            params = None
        return projects

    def list_project_tasks(self, project_id: int) -> list[HarvestTask]:
        tasks: list[HarvestTask] = []
        url = f"{API_BASE}/projects/{project_id}/task_assignments"
        params = {"per_page": 100}
        while url:
            resp = self.session.get(url, params=params)
            resp.raise_for_status()
            data = resp.json()
            for ta in data.get("task_assignments", []):
                t = ta["task"]
                tasks.append(HarvestTask(id=t["id"], name=t["name"]))
            url = data.get("links", {}).get("next")
            params = None
        return tasks

    def create_time_entry(self, project_id: int, task_id: int, spent_date: str,
                           hours: float, notes: str = "") -> dict:
        resp = self.session.post(
            f"{API_BASE}/time_entries",
            json={
                "project_id": project_id,
                "task_id": task_id,
                "spent_date": spent_date,
                "hours": round(hours, 2),
                "notes": notes,
            },
        )
        resp.raise_for_status()
        return resp.json()
