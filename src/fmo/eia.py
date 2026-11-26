"""Download weekly U.S. diesel prices from the EIA API (v2).

Docs: https://www.eia.gov/opendata/documentation.php
"""
import pandas as pd

from . import config
from .http import get_json

BASE_URL = "https://api.eia.gov/v2"
PAGE_SIZE = 5000  # the most rows EIA returns per JSON request


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
            "start": start,
            "sort[0][column]": "period",
            "sort[0][direction]": "asc",
            "offset": offset,
            "length": PAGE_SIZE,
        }
        body = get_json(url, params)["response"]
        page = body["data"]
        rows.extend(page)
        offset += len(page)
        if not page or offset >= int(body["total"]):
            break
    return to_frame(rows)


def to_frame(rows: list[dict]) -> pd.DataFrame:
    """Turn EIA JSON rows into a clean, sorted table."""
    df = pd.DataFrame(rows, columns=["period", "value"])
    df = df.rename(columns={"period": "date", "value": "price"})
    df["date"] = pd.to_datetime(df["date"])
    df["price"] = pd.to_numeric(df["price"], errors="coerce")
    return df.dropna().drop_duplicates("date").sort_values("date").reset_index(drop=True)
