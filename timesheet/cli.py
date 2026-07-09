from __future__ import annotations

from datetime import date, datetime, timedelta
from itertools import groupby

import click

from . import config as cfgmod
from . import fill as fillmod
from .harvest_client import HarvestClient
from .jira_client import JiraClient


def _load(ctx) -> dict:
    return cfgmod.load_config(ctx.obj["config_path"])


@click.group()
@click.option("--config", "config_file", default=None,
              help="Path to config.yaml (default: ~/.config/timesheet/config.yaml)")
@click.pass_context
def cli(ctx, config_file):
    """A tiny CLI for turning your week's Jira/meeting work into Harvest entries."""
    ctx.ensure_object(dict)
    ctx.obj["config_path"] = cfgmod.config_path(config_file)


# ------------------------------------------------------------------ config

@cli.group()
def config():
    """Manage timesheet config."""


@config.command("init")
@click.pass_context
def config_init(ctx):
    """Create a default config file to edit."""
    path = ctx.obj["config_path"]
    if path.exists():
        click.confirm(f"{path} already exists. Overwrite with defaults?", abort=True)
    cfgmod.save_config(cfgmod.DEFAULT_CONFIG, path)
    click.echo(f"Wrote default config to {path}")
    click.echo(
        "Edit it, then set these environment variables before running fill:\n"
        "  export JIRA_API_TOKEN=...\n"
        "  export HARVEST_ACCESS_TOKEN=..."
    )


@config.command("show")
@click.pass_context
def config_show(ctx):
    """Print the resolved config."""
    import yaml
    click.echo(yaml.safe_dump(_load(ctx), sort_keys=False))


@config.command("path")
@click.pass_context
def config_show_path(ctx):
    click.echo(str(ctx.obj["config_path"]))


# --------------------------------------------------------------- recurring

@cli.group()
def recurring():
    """Manage recurring meetings (cron-like, fixed duration)."""


@recurring.command("list")
@click.pass_context
def recurring_list(ctx):
    cfg = _load(ctx)
    items = cfg["recurring"]
    if not items:
        click.echo("No recurring meetings configured.")
        return
    for i, m in enumerate(items):
        click.echo(
            f"[{i}] {m['name']}: {','.join(m['days'])} "
            f"{m['duration_hours']}h -> project {m['harvest_project_id']} "
            f"/ task {m['harvest_task_id']}"
        )


@recurring.command("add")
@click.option("--name", required=True)
@click.option("--days", required=True,
              help="Comma-separated: mon,tue,wed,thu,fri")
@click.option("--duration-hours", required=True, type=float)
@click.option("--harvest-project-id", required=True, type=int)
@click.option("--harvest-task-id", required=True, type=int)
@click.pass_context
def recurring_add(ctx, name, days, duration_hours, harvest_project_id,
                   harvest_task_id):
    cfg = _load(ctx)
    cfg["recurring"].append({
        "name": name,
        "days": [d.strip().lower() for d in days.split(",")],
        "duration_hours": duration_hours,
        "harvest_project_id": harvest_project_id,
        "harvest_task_id": harvest_task_id,
    })
    cfgmod.save_config(cfg, ctx.obj["config_path"])
    click.echo(f"Added recurring meeting '{name}'.")


@recurring.command("remove")
@click.argument("index", type=int)
@click.pass_context
def recurring_remove(ctx, index):
    cfg = _load(ctx)
    try:
        removed = cfg["recurring"].pop(index)
    except IndexError:
        raise click.ClickException(f"No recurring meeting at index {index}.")
    cfgmod.save_config(cfg, ctx.obj["config_path"])
    click.echo(f"Removed '{removed['name']}'.")


# ------------------------------------------------------------- fill-list

@cli.group("fill-projects")
def fill_projects_grp():
    """Manage the %-based fill-list used for leftover capacity."""


@fill_projects_grp.command("list")
@click.pass_context
def fp_list(ctx):
    cfg = _load(ctx)
    items = cfg["fill_projects"]
    if not items:
        click.echo("No fill projects configured.")
        return
    total = 0
    for i, fp in enumerate(items):
        click.echo(
            f"[{i}] {fp.get('label', '')} project {fp['harvest_project_id']} "
            f"/ task {fp['harvest_task_id']}: {fp['percent']}%"
        )
        total += fp["percent"]
    click.echo(f"Total: {total}%")


@fill_projects_grp.command("add")
@click.option("--label", default="")
@click.option("--harvest-project-id", required=True, type=int)
@click.option("--harvest-task-id", required=True, type=int)
@click.option("--percent", required=True, type=float)
@click.pass_context
def fp_add(ctx, label, harvest_project_id, harvest_task_id, percent):
    cfg = _load(ctx)
    cfg["fill_projects"].append({
        "label": label,
        "harvest_project_id": harvest_project_id,
        "harvest_task_id": harvest_task_id,
        "percent": percent,
    })
    cfgmod.save_config(cfg, ctx.obj["config_path"])
    click.echo("Added fill project.")


@fill_projects_grp.command("remove")
@click.argument("index", type=int)
@click.pass_context
def fp_remove(ctx, index):
    cfg = _load(ctx)
    try:
        removed = cfg["fill_projects"].pop(index)
    except IndexError:
        raise click.ClickException(f"No fill project at index {index}.")
    cfgmod.save_config(cfg, ctx.obj["config_path"])
    click.echo(f"Removed '{removed.get('label') or removed['harvest_project_id']}'.")


# ------------------------------------------------------------------ epics

@cli.group()
def epics():
    """Inspect / edit saved epic -> Harvest project+task mappings."""


@epics.command("list")
@click.pass_context
def epics_list(ctx):
    cfg = _load(ctx)
    mapping = cfg["epic_mapping"]
    if not mapping:
        click.echo("No epic mappings saved yet.")
        return
    for key, m in mapping.items():
        click.echo(f"{key} -> project {m['harvest_project_id']} / task {m['harvest_task_id']}")


@epics.command("unset")
@click.argument("epic_key")
@click.pass_context
def epics_unset(ctx, epic_key):
    cfg = _load(ctx)
    if epic_key in cfg["epic_mapping"]:
        del cfg["epic_mapping"][epic_key]
        cfgmod.save_config(cfg, ctx.obj["config_path"])
        click.echo(f"Removed mapping for {epic_key}.")
    else:
        click.echo(f"No mapping for {epic_key}.")


# -------------------------------------------------------------------- fill

def _prompt_for_epic_mapping(cfg, harvest, epic_key, epic_name):
    click.echo(f"\nNo Harvest mapping yet for epic {epic_key} ({epic_name}).")
    projects = harvest.list_active_projects()
    for i, p in enumerate(projects):
        code = f" [{p.code}]" if p.code else ""
        click.echo(f"  [{i}] {p.name}{code}")
    idx = click.prompt("Pick the Harvest project number", type=int)
    project = projects[idx]
    tasks = harvest.list_project_tasks(project.id)
    if not tasks:
        raise click.ClickException(f"Project {project.name} has no tasks assigned.")
    for i, t in enumerate(tasks):
        click.echo(f"  [{i}] {t.name}")
    tidx = click.prompt("Pick the Harvest task number", type=int)
    task = tasks[tidx]
    cfg["epic_mapping"][epic_key] = {
        "harvest_project_id": project.id,
        "harvest_task_id": task.id,
    }
    return cfg["epic_mapping"][epic_key]


@cli.command()
@click.option("--week-start", required=True,
              help="Monday of the target week, YYYY-MM-DD")
@click.option("--yes", is_flag=True, help="Skip the confirmation prompt.")
@click.option("--dry-run", is_flag=True, help="Never write to Harvest, just preview.")
@click.pass_context
def fill(ctx, week_start, yes, dry_run):
    """Compute the week's plan (meetings + Jira epics + %-fill) and push it
    to Harvest."""
    cfg = _load(ctx)
    path = ctx.obj["config_path"]
    week_start_date = datetime.strptime(week_start, "%Y-%m-%d").date()
    if week_start_date.weekday() != 0:
        click.echo(
            f"Note: {week_start_date} is a {week_start_date.strftime('%A')}, "
            f"not a Monday -- using it as given anyway."
        )

    days = fillmod.week_dates(week_start_date, cfg["work_days"])
    week_end_date = days[-1]

    # --- meetings ---
    meeting_entries = fillmod.build_meeting_entries(cfg["recurring"], days)

    # --- jira ---
    jira_token = cfgmod.get_secret("jira_api_token")
    jira = JiraClient(
        base_url=cfg["jira"]["base_url"],
        email=cfg["jira"]["email"],
        api_token=jira_token,
        story_points_field=cfg["jira"]["story_points_field"],
        epic_link_field=cfg["jira"]["epic_link_field"],
    )
    jql = cfg["jira"]["jql"].format(
        start=week_start_date.isoformat(), end=week_end_date.isoformat()
    )
    click.echo(f"Querying Jira: {jql}")
    issues = jira.search_issues(jql)
    click.echo(f"Found {len(issues)} issue(s).")
    epic_groups = fillmod.group_by_epic(issues)

    # --- harvest (needed for prompting new epic mappings too) ---
    harvest_token = cfgmod.get_secret("harvest_access_token")
    harvest = HarvestClient(cfg["harvest"]["account_id"], harvest_token)

    for key, eg in epic_groups.items():
        if eg.total_points <= 0:
            continue
        if key not in cfg["epic_mapping"]:
            _prompt_for_epic_mapping(cfg, harvest, key, eg.epic_name)
            cfgmod.save_config(cfg, path)  # persist immediately

    entries, warnings = fillmod.build_plan(
        days=days,
        hours_per_day=cfg["hours_per_day"],
        meeting_entries=meeting_entries,
        epic_groups=epic_groups,
        epic_mapping=cfg["epic_mapping"],
        points_to_hours_ratio=cfg["points_to_hours_ratio"],
        fill_projects=cfg["fill_projects"],
    )

    _print_preview(entries, warnings)

    if not entries:
        click.echo("Nothing to submit.")
        return

    if dry_run:
        click.echo("\n(dry run -- nothing written to Harvest)")
        return

    if not yes:
        click.confirm(
            f"\nSubmit {len(entries)} time entries to Harvest?", abort=True
        )

    for e in entries:
        harvest.create_time_entry(
            project_id=e.harvest_project_id,
            task_id=e.harvest_task_id,
            spent_date=e.day.isoformat(),
            hours=e.hours,
            notes=e.label,
        )
    click.echo(f"Submitted {len(entries)} entries to Harvest.")


def _print_preview(entries, warnings):
    if not entries:
        click.echo("\nNo entries to show.")
    else:
        click.echo("\nPlan preview:")
        entries_sorted = sorted(entries, key=lambda e: (e.day, e.source))
        for day, group in groupby(entries_sorted, key=lambda e: e.day):
            click.echo(f"\n{day.isoformat()} ({day.strftime('%A')})")
            day_total = 0.0
            for e in group:
                click.echo(f"  [{e.source:7s}] {e.hours:5.2f}h  {e.label}")
                day_total += e.hours
            click.echo(f"  {'':7s}  {day_total:5.2f}h  (total)")
    if warnings:
        click.echo("\nWarnings:")
        for w in warnings:
            click.echo(f"  - {w}")


def main():
    cli(obj={})


if __name__ == "__main__":
    main()
