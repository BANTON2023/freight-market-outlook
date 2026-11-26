"""Settings for the Freight Market Outlook project.

API keys are read from a `.env` file in the project folder (never committed to Git)
or from environment variables, which is how GitHub Actions passes its secrets.
"""
import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data"
OUTPUT_DIR = ROOT / "outputs"

load_dotenv(ROOT / ".env")

# --- Data series -------------------------------------------------------------
# EIA: U.S. No 2 Diesel Retail Prices, dollars per gallon, weekly (from 1994).
EIA_DIESEL_SERIES = "EMD_EPD2D_PTE_NUS_DPG"
EIA_DIESEL_ROUTE = "petroleum/pri/gnd"

# FRED: freight demand indicators, monthly, seasonally adjusted.
FRED_SERIES = {
    "TRUCKD11": "ATA truck tonnage index (2015 = 100)",
    "TSIFRGHT": "Freight Transportation Services Index (BTS, 2000 = 100)",
}

# --- Forecast settings -------------------------------------------------------
HORIZON_MONTHS = 6     # how far ahead to forecast
BACKTEST_MONTHS = 36   # recent months used to test the models (never seen when fitting)
INTERVAL = (0.10, 0.90)  # forecast range: 80% of past errors fell inside it
TRAIN_START = "2010-01-01"  # ignore older history

# --- SIJ what-if -------------------------------------------------------------
# SIJ Logistics data is fictional practice data. Only its fleet fuel economy is
# used here, to turn a real diesel price into an illustrative fuel cost per mile:
#   fuel cost per mile = diesel price per gallon / miles per gallon
SIJ_AVG_MPG = 6.45  # SIJ report, full period 2022-2024


def api_key(name: str) -> str:
    """Return an API key from the environment, with a clear message if missing."""
    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(
            f"{name} is not set. Copy .env.example to .env and paste your key after "
            f"'{name}=' (see README, 'Get your API keys')."
        )
    return value
