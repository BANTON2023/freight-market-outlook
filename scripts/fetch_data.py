"""Step 1 of the pipeline: download the latest data from the EIA and FRED APIs.

Run from the project folder:
    python scripts/fetch_data.py

Writes:
    data/diesel_weekly.csv       weekly U.S. diesel price, $/gallon
    data/fred_<SERIES>.csv       one file per FRED series in config.FRED_SERIES
    data/fetch_log.csv           one row per run: when, what, how many rows, latest date
"""
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import pandas as pd  # noqa: E402

from fmo import config, eia, fred  # noqa: E402


def save(df: pd.DataFrame, name: str, log: list) -> None:
    path = config.DATA_DIR / f"{name}.csv"
    df.to_csv(path, index=False, date_format="%Y-%m-%d")
    latest = df["date"].max().date()
    log.append({"fetched_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                "file": path.name, "rows": len(df), "latest_date": latest})
    print(f"  {path.name}: {len(df):,} rows, latest {latest}")


def main() -> None:
    config.DATA_DIR.mkdir(exist_ok=True)
    log = []

    print("EIA diesel prices...")
    save(eia.fetch_diesel(config.api_key("EIA_API_KEY")), "diesel_weekly", log)

    fred_key = config.api_key("FRED_API_KEY")
    for series_id, label in config.FRED_SERIES.items():
        print(f"FRED {series_id} ({label})...")
        save(fred.fetch_series(series_id, fred_key), f"fred_{series_id}", log)

    log_path = config.DATA_DIR / "fetch_log.csv"
    pd.DataFrame(log).to_csv(log_path, mode="a", header=not log_path.exists(), index=False)
    print("Done.")


if __name__ == "__main__":
    main()
