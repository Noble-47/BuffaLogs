from datetime import datetime
from typing import Dict, Optional

from pydantic import BaseModel, Field


class UserInfo(BaseModel):
    username: str
    risk_score: str
    login_count: int
    alert_count: int
    last_login: datetime
    is_vip: bool
    is_ignored_user: bool
    last_triggered_alert: Optional[str]


class LoginInfo(BaseModel):
    no_of_logins_today: int
    avg_daily_logins: int
    login_count_per_week: Dict[str, int]
    login_count_per_month: Dict[str, int]
    time_of_login_today: datetime
    first_login_time_recorded: datetime
    last_login_time_recorded: datetime


class CountryInfo(BaseModel):
    last_login_country_logged: str
    total_no_of_countries_logged: int
    alert_count_per_country: Dict[str, int]
    logs_count_per_country: Dict[str, int]
    country_logged_per_month: Dict[str, list[str]] = Field(help="Countries logged per month in the last 12 months")


class AlertInfo(BaseModel):
    filters: Optional[list[str]]
    total_no_of_alerts_triggered: int
    percent_of_alerts_notified: float
    percent_of_alerts_filtered: float
    trigger_count_per_alert: Dict[str, int]


class DeviceInfo(BaseModel):
    most_recent_device: str
    most_used_device: str
    total_number_of_devices_logged: int
    log_count_per_device: Dict[str, int]
    alert_count_per_device: Dict[str, int]


class Profile(BaseModel):
    user_info: UserInfo
    country_info: CountryInfo
    alert_info: AlertInfo
    login_info: LoginInfo
