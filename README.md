# timesheet-cli

A small personal CLI that turns a week of Jira work + recurring meetings
into Harvest time entries.

## How it works

For a given week it builds a plan in three layers, in this order:

1. **Recurring meetings** — fixed, defined by you (`timesheet recurring add`),
   e.g. "Daily standup, mon-fri, 0.25h".
2. **Jira epics** — it runs a JQL query to find issues you touched that
   week, groups them by epic, and converts story points to hours using
   `points_to_hours_ratio` from config. The first time it sees a new epic
   it asks which Harvest project + task it maps to, then remembers that
   choice forever (saved to config). Epic hours are poured into whatever
   daily capacity is left after meetings, day by day.
3. **Fill-list** — whatever capacity is left after meetings + epics is
   split across your `fill-projects` list by percentage.

> **Note on story points:** Jira has no worklogs in this setup, so there's
> no per-day breakdown for epic work — this tool estimates total hours
> per epic for the week (points × ratio) and spreads it across the
> week's remaining capacity. Always check the preview table before
> confirming; nothing is written to Harvest without your OK (or `--yes`).

## Install

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

## Credentials (never stored in the config file)

```bash
export JIRA_API_TOKEN=...       # https://id.atlassian.com/manage-profile/security/api-tokens
export HARVEST_ACCESS_TOKEN=... # https://id.getharvest.com/developers
```

## Setup

```bash
timesheet config init
# edit ~/.config/timesheet/config.yaml:
#   - jira.base_url, jira.email
#   - jira.story_points_field  (custom field id for story points, e.g. customfield_10016)
#   - harvest.account_id
#   - points_to_hours_ratio    (e.g. 1 point = 2 hours -> 2.0)
#   - hours_per_day / work_days

timesheet recurring add --name "Daily standup" --days mon,tue,wed,thu,fri \
    --duration-hours 0.25 --harvest-project-id 111 --harvest-task-id 222

timesheet fill-projects add --label "Internal tooling" \
    --harvest-project-id 333 --harvest-task-id 444 --percent 60
timesheet fill-projects add --label "Support" \
    --harvest-project-id 555 --harvest-task-id 666 --percent 40
```

## Weekly use

```bash
timesheet fill --week-start 2026-07-06        # prompts for new epic mappings, shows preview, asks to confirm
timesheet fill --week-start 2026-07-06 --dry-run   # preview only, never writes to Harvest
timesheet fill --week-start 2026-07-06 --yes       # skip the confirmation prompt
```

## Other commands

```bash
timesheet config show
timesheet recurring list / remove <index>
timesheet fill-projects list / remove <index>
timesheet epics list             # see saved epic -> Harvest mappings
timesheet epics unset <EPIC-KEY> # forget a mapping, will re-prompt next fill
```

## Customizing the Jira query

`jira.jql` in the config supports `{start}` and `{end}` (YYYY-MM-DD) for
the target week and defaults to issues assigned to you, updated in that
window. Adjust it to match your workflow (e.g. filter by project, status,
or sprint) — it's plain JQL.

## Notes / things you may want to tweak

- The epic-detection logic checks `parent` first (team-managed projects,
  where an Epic issue type is the parent) and falls back to the classic
  "Epic Link" custom field (`jira.epic_link_field`) for company-managed
  projects. If neither matches, the issue is grouped as its own
  pseudo-epic and prompted for individually.
- If fill-list percentages don't add up to 100%, the tool applies them
  as given (so <100% intentionally leaves capacity unfilled, and a
  warning is printed either way if it's not exactly 100%).
- `harvest.account_id` and Harvest project/task IDs are numeric — find
  them via `timesheet fill` (it lists projects/tasks interactively when
  prompting for a new epic mapping) or in the Harvest web UI.
