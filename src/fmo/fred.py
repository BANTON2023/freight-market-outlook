"""Download economic series from the FRED API (Federal Reserve Bank of St. Louis).

Docs: https://fred.stlouisfed.org/docs/api/fred/series_observations.html
"""
import pandas as pd

from .http import get_json

URL = "https://api.stlouisfed.org/fred/series/observations"


def fetch_series(series_id: str, api_key: str) -> pd.DataFrame:
    """Return one FRED series as a table with columns `date` and `value`."""
    params = {"series_id": series_id, "api_key": api_key, "file_type": "json"}
    return to_frame(get_json(URL, params)["observations"])


def to_frame(observations: list[dict]) -> pd.DataFrame:
    """Turn FRED observations into a clean, sorted table.

    FRED marks a missing value with ".", which becomes empty and is dropped.
    """
    df = pd.DataFrame(observations, columns=["date", "value"])
    df["date"] = pd.to_datetime(df["date"])
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    return df.dropna().sort_values("date").reset_index(drop=True)
