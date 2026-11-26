"""Translate the diesel forecast into SIJ Logistics terms (illustrative only).

SIJ's data is fictional practice data, so nothing here is fitted to it. The what-if
uses one SIJ figure, its fleet fuel economy, and the standard trucking formula:

    fuel cost per mile = diesel price per gallon / miles per gallon
"""
import pandas as pd

from . import config


def fuel_cost_per_mile(diesel_forecast: pd.DataFrame, mpg: float = config.SIJ_AVG_MPG) -> pd.DataFrame:
    """Add SIJ fuel cost per mile (point, low, high) to a diesel price forecast."""
    out = diesel_forecast[["date", "forecast", "low", "high"]].copy()
    out = out.rename(columns={"forecast": "diesel_price", "low": "diesel_low", "high": "diesel_high"})
    out["mpg"] = mpg
    for col in ["price", "low", "high"]:
        source = "diesel_price" if col == "price" else f"diesel_{col}"
        name = "fuel_cost_per_mile" if col == "price" else f"fuel_cost_per_mile_{col}"
        out[name] = (out[source] / mpg).round(4)
    return out
