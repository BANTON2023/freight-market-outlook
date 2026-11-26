"""Download weekly U.S. diesel prices from the EIA API (v2).

Docs: https://www.eia.gov/opendata/documentation.php
"""
import pandas as pd

from . import config
from .http import get_json

BASE_URL = "https://api.eia.gov/v2"
PAGE_SIZE = 5000  # the most rows EIA returns per JSON request; diesel has ~1,700, so one page


def fetch_diesel(api_key: str, start: str = "1994-01-01") -> pd.DataFrame:
    """Return weekly diesel prices as a table with columns `date` and `price`."""
    url = f"{BASE_URL}/{config.EIA_DIESEL_ROUTE}/data/"
    rows, offset = [], 0
    while True:
        params = {
            "api_key": api_key,
            "frequency": "weekly",
            "data[0]": "value",
            "facets[series][]": config.EIA_DIESEL_SERIES,
            # Newest first, no "start" filter, one big page: EIA times out (HTTP 504)
            # on oldest-first sorting, date filters and offsets, so we filter here.
            "sort[0][column]": "period",
            "sort[0][direction]": "desc",
            "offset": offset,
            "length": PAGE_SIZE,
        }
        body = get_json(url, params, retries=6)["response"]
        page = body["data"]
        rows.extend(page)
        offset += len(page)
        if not page or offset >= int(body["total"]):
            break
    df = to_frame(rows)
    return df[df["date"] >= pd.Timestamp(start)].reset_index(drop=True)


def to_frame(rows: list[dict]) -> pd.DataFrame:
    """Turn EIA JSON rows into a clean, sorted table."""
    df = pd.DataFrame(rows, columns=["period", "value"])
    df = df.rename(columns={"period": "date", "value": "price"})
    df["date"] = pd.to_datetime(df["date"])
    df["price"] = pd.to_numeric(df["price"], errors="coerce")
    return df.dropna().drop_duplicates("date").sort_values("date").reset_index(drop=True)
