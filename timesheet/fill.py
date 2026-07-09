"""Builds the week's time-entry plan:

  1. Recurring meetings (fixed, from config, per weekday).
  2. Epic work, sized from Jira story points * points_to_hours_ratio,
     poured into whatever capacity is left each day after meetings.
  3. Fill-list projects (by %), poured into whatever capacity remains
     after meetings + epic work.

This is a heuristic, not a source of truth -- Jira has no per-day worklogs
here, so epic hours are spread across the week's remaining capacity in
day order. Always review the preview table before confirming.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, timedelta

DAY_NAMES = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]


@dataclass
class PlanEntry:
    day: date
    source: str  # "meeting" | "epic" | "fill"
    label: str
    hours: float
    harvest_project_id: int
    harvest_task_id: int


@dataclass
class EpicGroup:
    epic_key: str
    epic_name: str
    total_points: float
    issue_keys: list[str] = field(default_factory=list)


def week_dates(week_start: date, work_days: list[str]) -> list[date]:
    idxs = [DAY_NAMES.index(d.lower()) for d in work_days]
    return [week_start + timedelta(days=i) for i in idxs]


def group_by_epic(issues) -> dict[str, EpicGroup]:
    groups: dict[str, EpicGroup] = {}
    for issue in issues:
        key = issue.epic_key or f"__no_epic__:{issue.key}"
        name = issue.epic_name or f"(no epic) {issue.key}"
        if key not in groups:
            groups[key] = EpicGroup(epic_key=key, epic_name=name, total_points=0.0)
        groups[key].total_points += issue.story_points or 0.0
        groups[key].issue_keys.append(issue.key)
    return groups


def build_meeting_entries(recurring: list[dict], days: list[date]) -> list[PlanEntry]:
    entries = []
    for d in days:
        day_name = DAY_NAMES[d.weekday()]
        for m in recurring:
            if day_name in [x.lower() for x in m.get("days", [])]:
                entries.append(PlanEntry(
                    day=d,
                    source="meeting",
                    label=m["name"],
                    hours=float(m["duration_hours"]),
                    harvest_project_id=m["harvest_project_id"],
                    harvest_task_id=m["harvest_task_id"],
                ))
    return entries


def build_plan(
    days: list[date],
    hours_per_day: float,
    meeting_entries: list[PlanEntry],
    epic_groups: dict[str, EpicGroup],
    epic_mapping: dict[str, dict],
    points_to_hours_ratio: float,
    fill_projects: list[dict],
) -> tuple[list[PlanEntry], list[str]]:
    """Returns (entries, warnings)."""
    warnings: list[str] = []
    entries: list[PlanEntry] = list(meeting_entries)

    capacity = {}
    for d in days:
        used = sum(e.hours for e in meeting_entries if e.day == d)
        capacity[d] = max(0.0, hours_per_day - used)

    # --- epic work, poured into remaining capacity day by day ---
    epic_queue = []
    for eg in epic_groups.values():
        hrs = eg.total_points * points_to_hours_ratio
        if hrs <= 0:
            continue
        mapping = epic_mapping.get(eg.epic_key)
        if not mapping:
            warnings.append(
                f"Epic {eg.epic_key} ({eg.epic_name}) has no Harvest mapping "
                f"-- skipped {hrs:.2f}h."
            )
            continue
        epic_queue.append((eg, hrs, mapping))

    for eg, hrs, mapping in epic_queue:
        remaining = hrs
        for d in days:
            if remaining <= 0:
                break
            avail = capacity[d]
            if avail <= 0:
                continue
            take = min(avail, remaining)
            entries.append(PlanEntry(
                day=d,
                source="epic",
                label=f"{eg.epic_key} {eg.epic_name}",
                hours=take,
                harvest_project_id=mapping["harvest_project_id"],
                harvest_task_id=mapping["harvest_task_id"],
            ))
            capacity[d] -= take
            remaining -= take
        if remaining > 0.001:
            warnings.append(
                f"Epic {eg.epic_key} ({eg.epic_name}) had {hrs:.2f}h of work "
                f"but only {hrs - remaining:.2f}h of capacity was available "
                f"this week -- {remaining:.2f}h left unassigned."
            )

    # --- fill-list, by % of whatever capacity remains, per day ---
    total_pct = sum(fp["percent"] for fp in fill_projects) if fill_projects else 0
    if fill_projects and abs(total_pct - 100.0) > 0.01:
        warnings.append(
            f"Fill-list percentages add up to {total_pct}%, not 100% -- "
            f"they'll be applied as-is (i.e. proportionally, or leaving gaps "
            f"if <100%)."
        )

    for d in days:
        avail = capacity[d]
        if avail <= 0 or not fill_projects:
            continue
        for fp in fill_projects:
            take = avail * (fp["percent"] / 100.0)
            if take <= 0:
                continue
            entries.append(PlanEntry(
                day=d,
                source="fill",
                label=fp.get("label", f"project {fp['harvest_project_id']}"),
                hours=take,
                harvest_project_id=fp["harvest_project_id"],
                harvest_task_id=fp["harvest_task_id"],
            ))

    return entries, warnings
