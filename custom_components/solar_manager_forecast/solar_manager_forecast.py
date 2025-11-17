"""Asynchronous client and data model for Solar Manager PV forecast."""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from aiohttp import ClientSession, BasicAuth


class SolarManagerForecastError(Exception):
    """Generic error raised for Solar Manager forecast issues."""

def _timed_value(
    at: dt.datetime,
    data: Dict[dt.datetime, int],
) -> Optional[int]:
    """Return the value for a specific time from a time-ordered dict.

    - If the time is before the first timestamp, the first value is used.
    - If the time is between timestamps, the last known value at or before
      the given time is used.
    - If the time is after all timestamps, the last value is used.
    """
    if not data:
        return None

    # The dict is insertion-ordered; we filled it in sorted order before
    iterator = iter(data.items())
    first_ts, first_val = next(iterator)

    # Case 1: time is before or exactly at the first forecast point
    if at <= first_ts:
        return first_val

    # Case 2: time is within the known range → keep last known value
    value: Optional[int] = first_val
    for timestamp, cur_value in iterator:
        if timestamp > at:
            return value
        value = cur_value

    # Case 3: time is after all known points → return last value
    return value

def _interval_value_sum(
    start: dt.datetime,
    end: dt.datetime,
    data: Dict[dt.datetime, int],
) -> int:
    """Sum all values between start (exclusive) and end (inclusive)."""
    total = 0
    for timestamp, value in data.items():
        if start < timestamp <= end:
            total += value
    return total


@dataclass
class Estimate:
    """Forecast estimate built from Solar Manager API data."""

    timezone: dt.tzinfo
    watts: Dict[dt.datetime, int]
    wh_period: Dict[dt.datetime, int]
    wh_hours: Dict[dt.datetime, int]

    @classmethod
    def from_solar_manager_data(
        cls,
        entries: List[Dict[str, Any]],
        timezone: dt.tzinfo,
        default_interval: dt.timedelta = dt.timedelta(minutes=15),
    ) -> "Estimate":
        """Build an Estimate from Solar Manager forecast JSON."""
        sorted_entries = sorted(
            (e for e in entries if "t" in e),
            key=lambda e: e["t"],
        )

        watts: Dict[dt.datetime, int] = {}
        wh_period: Dict[dt.datetime, int] = {}
        wh_hours_acc: Dict[dt.datetime, float] = {}
        timestamps_local: List[dt.datetime] = []

        for entry in sorted_entries:
            t_str = entry.get("t")
            if not t_str:
                continue

            t_utc = dt.datetime.fromisoformat(t_str.replace("Z", "+00:00"))
            t_local = t_utc.astimezone(timezone)

            power_w = int(entry.get("pW") or 0)

            timestamps_local.append(t_local)
            watts[t_local] = power_w

        for idx, t_start in enumerate(timestamps_local):
            power_w = watts[t_start]

            if idx + 1 < len(timestamps_local):
                t_end = timestamps_local[idx + 1]
            else:
                t_end = t_start + default_interval

            delta_hours = (t_end - t_start).total_seconds() / 3600.0
            if delta_hours <= 0:
                continue

            wh = power_w * delta_hours
            wh_period[t_start] = int(round(wh))

            hour_start = t_start.replace(minute=0, second=0, microsecond=0)
            wh_hours_acc[hour_start] = wh_hours_acc.get(hour_start, 0.0) + wh

        wh_hours: Dict[dt.datetime, int] = {
            ts: int(round(val)) for ts, val in wh_hours_acc.items()
        }

        return cls(
            timezone=timezone,
            watts=watts,
            wh_period=wh_period,
            wh_hours=wh_hours,
        )

    def now(self) -> dt.datetime:
        """Return current datetime in the forecast's timezone."""
        return dt.datetime.now(self.timezone)

    @property
    def power_production_now(self) -> int:
        """Return estimated power production right now (in W)."""
        return self.power_production_at_time(self.now())

    def power_production_at_time(self, at: dt.datetime) -> int:
        """Return estimated power production at a specific time (in W)."""
        if at.tzinfo is None:
            at = at.replace(tzinfo=self.timezone)
        else:
            at = at.astimezone(self.timezone)

        return _timed_value(at, self.watts) or 0

    def sum_energy_production(self, period_hours: int) -> int:
        """Return sum of energy production in the upcoming 'period_hours' hours (Wh)."""
        now = self.now().replace(minute=59, second=59, microsecond=999)
        until = now + dt.timedelta(hours=period_hours)
        return _interval_value_sum(now, until, self.wh_hours)


class SolarManagerSolarForecast:
    """Client class to fetch and build Solar Manager PV forecast estimates."""

    def __init__(
        self,
        session: ClientSession,
        base_url: Optional[str] = None,
        smart_manager_id: Optional[str] = None,
        timezone: Optional[dt.tzinfo] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
    ) -> None:
        """Initialize the client."""
        self._session = session
        self._smart_manager_id = smart_manager_id
        self._timezone = timezone or dt.timezone.utc

        if base_url:
            self._base_url = base_url
        elif smart_manager_id:
            self._base_url = (
                f"https://cloud.solar-manager.ch/"
                f"v3/users/{smart_manager_id}/data/forecast"
            )
        else:
            self._base_url = None

        # Prepare Basic Auth if username/password are provided
        if username and password:
            self._auth: Optional[BasicAuth] = BasicAuth(username, password)
        else:
            self._auth = None

    async def estimate(self) -> Estimate:
        """Fetch forecast data from Solar Manager and return an Estimate."""
        if not self._base_url:
            raise SolarManagerForecastError(
                "No base URL or Smart Manager ID configured."
            )

        try:
            async with self._session.get(
                self._base_url,
                timeout=20,
                auth=self._auth,
            ) as resp:
                resp.raise_for_status()
                payload: Any = await resp.json()
        except Exception as err:  # noqa: BLE001
            raise SolarManagerForecastError(
                f"Error fetching Solar Manager forecast: {err}"
            ) from err

        data = payload.get("data")
        if not isinstance(data, list):
            raise SolarManagerForecastError(
                "Unexpected response format: 'data' field missing or not a list."
            )

        return Estimate.from_solar_manager_data(
            entries=data,
            timezone=self._timezone,
        )
