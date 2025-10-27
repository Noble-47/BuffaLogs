from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Annotated, Optional

import typer
from buffacli import requests
from buffacli.formatters import FormatOptions
from buffacli.models import AlertQuery, LoginQuery
from buffacli.options import AlertQueryOptions, LoginQueryOptions, QueryOptions
from buffacli.render import RenderOptions, make_renderable

app = typer.Typer(help="Query users and alerts record")


@app.callback()
def callback(
    ctx: typer.Context,
    formatter: Annotated[FormatOptions, typer.Option("-f", "--format")] = "table",
    limit: Annotated[int, typer.Option(help="Prints only the first n items")] = None,
    since: Annotated[str, typer.Option(help="Query the most recent from the given timestamp")] = "",
    mode: Annotated[RenderOptions, typer.Option(help="Select how long output are displayed")] = "",
    page_size: Annotated[int, typer.Option(help="Number of items in a page")] = None,
    output_file: Annotated[Path, typer.Option("-o", "--output", help="Output file for query export")] = None,
    omit: Annotated[list[str], typer.Option(help="Omit fields from query results")] = None,
    mappings: Annotated[str, typer.Option(help="Alias name for fields. Follows the format fieldname:alias")] = None,
):
    ctx.obj = QueryOptions(
        limit=limit,
        formatter=formatter,  # make_renderable(formatter, mode=mode, page_size=page_size, exporter=exporter),
        omit=omit,
        mappings=mappings,
        mode=mode,
        page_size=page_size,
        output_file=output_file,
        since=since,
    )


@app.command(help="Query alert data")
def alerts(
    ctx: typer.Context,
    fields: Annotated[list[str], typer.Argument(help="Query fields to display")] = None,
    start_date: Annotated[datetime, typer.Option(help="Filter alerts from the date")] = None,
    end_date: Annotated[datetime, typer.Option(help="Filter alerts up to date")] = None,
    name: Annotated[str, typer.Option("--alert-type", help="Filter by alert type")] = None,
    username: Annotated[str, typer.Option(help="Filter by username")] = None,
    ip: Annotated[str, typer.Option(help="Filter by IP address")] = None,
    country: Annotated[str, typer.Option(help="Filter by login country code")] = None,
    is_vip: Annotated[bool, typer.Option("--is-vip", help="Filter by VIP status")] = None,
    notified: Annotated[bool, typer.Option("--is-notified", help="Filter by notification status")] = None,
    min_risk_score: Annotated[str, int, typer.Option(help="Exclude alerts below risk score")] = None,
    max_risk_score: Annotated[str, int, typer.Option(help="Exclude alerts above risk score")] = None,
    risk_score: Annotated[str, int, typer.Option(help="Include alerts with risk score")] = None,
    login_start_time: Annotated[datetime, typer.Option(help="Filter by login date starting from date.")] = None,
    login_end_time: Annotated[datetime, typer.Option(help="Filter by login date up to date.")] = None,
    user_agent: Annotated[str, typer.Option(help="Filter by login agent.")] = None,
):

    # Performs validations of command option
    query_options = AlertQueryOptions(
        start_date=start_date,
        end_date=end_date,
        name=name,
        username=username,
        ip=ip,
        country=country,
        is_vip=is_vip,
        notified=notified,
        min_risk_score=min_risk_score,
        max_risk_score=max_risk_score,
        risk_score=risk_score,
        login_start_time=login_start_time,
        login_end_time=login_end_time,
        user_agent=user_agent,
        limit=ctx.obj.limit,
        since=ctx.obj.since,
    )
    data = requests.get_alerts(query_options.model_dump())
    formatter = ctx.obj.formatter
    alert_model = AlertQuery(data, omit=ctx.obj.omit, fields=fields, mappings=ctx.obj.mappings)
    formatter.print(alert_model, title="Alerts")


@app.command(help="Query login data")
def logins(
    ctx: typer.Context,
    fields: Annotated[list[str], typer.Argument(help="Query fields to display")] = None,
    username: Annotated[str, typer.Option(help="Filter by username")] = None,
    ip: Annotated[str, typer.Option(help="Filter by IP address")] = None,
    index: Annotated[str, typer.Option(help="Filter by login index")] = None,
    country: Annotated[str, typer.Option(help="Filter by login country")] = None,
    login_start_time: Annotated[datetime, typer.Option(help="Filter by login date starting from date.")] = None,
    login_end_time: Annotated[datetime, typer.Option(help="Filter by login date up to date.")] = None,
    user_agent: Annotated[str, typer.Option(help="Filter by login agent.")] = None,
):

    query_options = LoginQueryOptions(
        username=username,
        ip=ip,
        country=country,
        login_start_time=login_start_time,
        login_end_time=login_end_time,
        user_agent=user_agent,
        index=index,
        limit=ctx.obj.limit,
        since=ctx.obj.since,
    )
    data = requests.get_logins(query_options.model_dump())
    formatter = ctx.obj.formatter
    login = LoginQuery(data, omit=ctx.obj.omit, fields=fields, mappings=ctx.obj.mappings)
    formatter.print(login, title="Logins")
