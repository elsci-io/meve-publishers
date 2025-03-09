from datetime import datetime, timezone

import pytz
from dateutil.parser import isoparser

isoparser = isoparser()


def at_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        raise ValueError(
            "Can't turn a datetime w/o timezone into a UTC time. Ensure that you create a datetime that has"
            " timezone information. Otherwise it doesn't represent any particular instant and therefore it's not"
            " possible to calculate the UTC time.")
    # Signals API has a bug - it silently drops the timezone info considering all dates as if those were
    # UTC0 dates. So we need to change the time to UTC0 to be compatible.
    return dt.astimezone(timezone.utc)


def parse_ord_time(t: str) -> datetime | None:
    if not t:
        return None
    if "/" in t:
        return datetime.strptime(t, '%m/%d/%Y').replace(tzinfo=pytz.UTC)
    return at_utc(isoparser.isoparse(t))
