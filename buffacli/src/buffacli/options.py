import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Annotated, Any, Dict, List, Optional, Union

from buffacli import export
from buffacli.exceptions import InvalidArgsException
from buffacli.formatters import FormatOptions
from buffacli.render import RenderOptions, make_renderable
from dateutil.relativedelta import relativedelta
from pydantic import BaseModel, BeforeValidator, Field, field_validator, model_validator

RISK_LEVEL_MAP = {
    "NO RISK": 0,
    "LOW": 1,
    "MEDIUM": 4,
    "HIGH": 8,
}
ALLOWED_RISK_LEVELS_INT = list(range(0, 9))


def risk_level_to_int(value: Union[str, int, None]) -> Optional[int]:
    """Converts a string risk level (HIGH, LOW) to an integer score."""
    if value is None:
        return None
    if isinstance(value, str):
        normalized_value = value.upper()  # .replace(" ", "_")
        if normalized_value in RISK_LEVEL_MAP:
            return RISK_LEVEL_MAP[normalized_value]

        # If the string is a number, try converting it
        try:
            int_value = int(value)
            if int_value in ALLOWED_RISK_LEVELS_INT:
                return int_value
        except ValueError:
            pass

    if isinstance(value, int) and (1 <= value <= 8):
        return value

    raise InvalidArgsException(f"Risk score must be an integer between 0-8 or one of {', '.join(RISK_LEVEL_MAP.keys())}. Got {value}.")


def generate_start_and_end_date(since) -> tuple[datetime, datetime]:
    """
    Generates a start date and end date using `since` parameter

    Parses a `self.since` if available and calculates the start date by subtracting the
    duration from the current timestamp (the end date).
    """
    match = re.match(r"^(\d+)([HMdm])$", since.strip())
    if not match:
        raise InvalidArgsException(f"Invalid format: '{since}'. Expected format is <number><unit>, where unit is M, H, d, or m.")

    quantity = int(match.group(1))
    unit = match.group(2)

    # Set the end_date to the current timestamp
    end_date = datetime.now()
    start_date = end_date

    # Handle time deltas
    if unit == "M":
        start_date = end_date - timedelta(minutes=quantity)
    elif unit == "H":
        start_date = end_date - timedelta(hours=quantity)
    elif unit == "d":
        start_date = end_date - timedelta(days=quantity)
    elif unit == "m":
        start_date = end_date - relativedelta(months=quantity)
    return start_date, end_date


RISK_SCORE_TYPE = Annotated[int, str, BeforeValidator(risk_level_to_int)]


class QueryOptions(BaseModel):
    mode: Optional[RenderOptions] = Field(default=None)
    page_size: Optional[int] = Field(default=None)
    output_file: Optional[Path] = Field(default=None)
    limit: Optional[int] = Field(default=None, description="Maximum number of items to return.")
    formatter: Optional[FormatOptions] = Field(default=FormatOptions.table, description="Output format.")
    omit: Optional[str] = Field(default=None, description="Comma or space-separated fields to omit.")
    mappings: Optional[Dict[str, str]] = Field(default=None, description="Field:alias mapping.")
    since: Optional[str] = Field(default=None, description="Time delta string (e.g., '1h', '1d', '1M').")

    @field_validator("mappings", mode="before")
    @classmethod
    def process_mappings(cls, value: Optional[str]) -> Optional[Dict[str, str]]:
        """Converts a space-separated string of 'field:alias' to a dictionary."""
        if value:
            try:
                return dict(mapstr.split(":") for mapstr in value.split())
            except ValueError:
                raise InvalidArgsException("Mappings must follow the format 'field1:alias1 field2:alias2'")
        return None

    @model_validator(mode="after")
    def perform_post_validations(self):

        # Instantiate export and format option object
        exporter = None
        if self.output_file:
            exporter = export.get_exporter(self.output_file)
        self.formatter = make_renderable(self.formatter, mode=self.mode, page_size=self.page_size, exporter=exporter)
        return self


class AlertQueryOptions(BaseModel):
    fields: Optional[List[str]] = Field(default=None, description="Query fields to display.")
    start_date: Optional[datetime] = Field(default=None)
    end_date: Optional[datetime] = Field(default=None)
    name: Optional[str] = Field(default=None)
    ip: Optional[str] = Field(default=None)
    country: Optional[str] = Field(default=None)
    is_vip: Optional[bool] = Field(default=None)
    notified: Optional[bool] = Field(default=None)
    min_risk_score: Optional[RISK_SCORE_TYPE] = Field(default=None, description="Exclude alerts below risk score.")
    max_risk_score: Optional[RISK_SCORE_TYPE] = Field(default=None, description="Exclude alerts above risk score.")
    risk_score: Optional[RISK_SCORE_TYPE] = Field(default=None, description="Include alerts with specific risk score.")
    login_start_time: Optional[datetime] = Field(default=None)
    login_end_time: Optional[datetime] = Field(default=None)
    user_agent: Optional[str] = Field(default=None)
    since: Optional[str] = Field(default=None, description="Time delta string (e.g., '1h', '1d', '1M').")
    limit: Optional[int] = Field(default=None, description="Maximum number of items to return.")

    @model_validator(mode="after")
    def validate_alert_dates(self) -> "AlertQueryOptions":
        """Ensures start date and end date pairs are sequentially correct."""
        if self.since:
            # Check if dates were explicitly set by the user (as in the CLI)
            if self.start_date or self.end_date:
                raise InvalidArgsException("Cannot specify start_date/end_date when using 'since'.")
            self.start_date, self.end_date = generate_start_and_end_date(self.since)

        if self.start_date and self.end_date and self.start_date > self.end_date:
            raise InvalidArgsException(f"Alert End date cannot be earlier than start date. End date: {self.end_date}, Start date: {self.start_date}")

        if self.login_start_time and self.login_end_time and self.login_start_time > self.login_end_time:
            raise InvalidArgsException(
                f"Login end date cannot be earlier than login start date. End date: {self.login_end_time}, Start date: {self.login_start_time}"
            )
        return self


class LoginQueryOptions(BaseModel):
    fields: Optional[list[str]] = Field(default=None)
    username: Optional[str] = Field(default=None)
    ip: Optional[str] = Field(default=None)
    index: Optional[str] = Field(default=None)
    country: Optional[str] = Field(default=None)
    login_start_time: Optional[datetime] = Field(default=None)
    login_end_time: Optional[datetime] = Field(default=None)
    user_agent: Optional[str] = Field(default=None)
    since: Optional[str] = Field(default=None)
    limit: Optional[int] = Field(default=None)

    @model_validator(mode="after")
    def validate_login_dates(self) -> "AlertQueryOptions":
        """Ensures start date and end date pairs are sequentially correct."""
        if self.since:
            # Check if dates were explicitly set by the user (as in the CLI)
            if self.login_start_time or self.login_end_time:
                raise InvalidArgsException("Cannot specify start_time/end_time when using 'since'.")
            self.login_start_time, self.login_end_time = generate_start_and_end_date(self.since)

        if self.login_start_time and self.login_end_time and self.login_start_time > self.login_end_time:
            raise InvalidArgsException(
                f"Login end date cannot be earlier than login start date. End date: {self.login_end_time}, Start date: {self.login_start_time}"
            )
        return self
