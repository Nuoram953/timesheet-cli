"""Minimal Jira Cloud REST client -- just enough to find issues worked on
in a given week, and their epic + story points.

No worklogs are used (per user's setup, worklogs aren't tracked); instead
we look at assigned/updated issues and read story points off a custom
field.
"""
from __future__ import annotations

import base64
from dataclasses import dataclass

import requests


@dataclass
class Issue:
    key: str
    summary: str
    story_points: float | None
    epic_key: str | None
    epic_name: str | None


class JiraClient:
    def __init__(self, base_url: str, email: str, api_token: str,
                 story_points_field: str, epic_link_field: str):
        self.base_url = base_url.rstrip("/")
        self.story_points_field = story_points_field
        self.epic_link_field = epic_link_field
        token = base64.b64encode(f"{email}:{api_token}".encode()).decode()
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Basic {token}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        })

    def search_issues(self, jql: str) -> list[Issue]:
        fields = ["summary", "parent", self.story_points_field,
                  self.epic_link_field]
        issues: list[Issue] = []
        next_token = None
        while True:
            body = {
                "jql": jql,
                "fields": fields,
                "maxResults": 100,
            }
            if next_token:
                body["nextPageToken"] = next_token
            resp = self.session.post(
                f"{self.base_url}/rest/api/3/search/jql", json=body
            )
            if resp.status_code == 404:
                # Older Jira Cloud instances: fall back to /rest/api/3/search
                resp = self.session.post(
                    f"{self.base_url}/rest/api/3/search", json=body
                )
            resp.raise_for_status()
            data = resp.json()
            for raw in data.get("issues", []):
                issues.append(self._parse_issue(raw))
            next_token = data.get("nextPageToken")
            if not next_token or not data.get("issues"):
                break
        return issues

    def _parse_issue(self, raw: dict) -> Issue:
        f = raw.get("fields", {})
        sp = f.get(self.story_points_field)
        parent = f.get("parent")
        epic_key = None
        epic_name = None
        if parent and parent.get("fields", {}).get("issuetype", {}).get(
            "name"
        ) == "Epic":
            epic_key = parent.get("key")
            epic_name = parent.get("fields", {}).get("summary")
        elif parent:
            # parent exists but isn't an epic (e.g. subtask) -- ignore
            pass
        else:
            epic_key = f.get(self.epic_link_field)
            epic_name = epic_key
        return Issue(
            key=raw["key"],
            summary=f.get("summary", ""),
            story_points=float(sp) if sp is not None else None,
            epic_key=epic_key,
            epic_name=epic_name,
        )
