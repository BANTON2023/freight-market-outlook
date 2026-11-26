"""Forecasting and the SIJ what-if, checked on small made-up series."""
import numpy as np
import pandas as pd
import pytest

from fmo import forecast, whatif


def monthly(values, start="2015-01-01"):
    return pd.Series(values, index=pd.date_range(start, periods=len(values), freq="MS"), dtype=float)


def test_weekly_prices_average_by_month():
    df = pd.DataFrame({"date": pd.to_datetime(["2026-01-05", "2026-01-12", "2026-02-02"]),
                       "price": [3.0, 4.0, 5.0]})
    s = forecast.to_monthly(df, "price")
    assert s.tolist() == [3.5, 5.0]
    assert s.index[0] == pd.Timestamp("2026-01-01")


def test_naive_and_seasonal_naive():
    s = monthly(range(1, 25))  # 24 months: 1..24
    assert forecast.naive(s, 3).tolist() == [24, 24, 24]
    assert forecast.seasonal_naive(s, 3).tolist() == [13, 14, 15]


def test_backtest_never_uses_the_future():
    s = monthly(np.arange(60.0))
    results = forecast.backtest(s, horizon=3, months=12)
    assert (results["date"] > results["origin"]).all()
    assert results["step"].max() == 3
    assert results.groupby("model")["origin"].nunique().eq(10).all()  # 12 - 3 + 1


def test_holt_winters_learns_a_seasonal_pattern():
    t = np.arange(96)
    s = monthly(100 + 0.5 * t + 10 * np.sin(2 * np.pi * t / 12))
    scores = forecast.score(forecast.backtest(s, horizon=6, months=24))
    assert scores["model"].iat[0] == "holt_winters"
    assert scores["mape"].iat[0] < 1.0


def test_forecast_range_contains_the_point():
    s = monthly(100 + np.random.default_rng(0).normal(0, 2, 72).cumsum())
    results = forecast.backtest(s, horizon=6, months=24)
    fc = forecast.forecast(s, "naive", results, horizon=6, interval=(0.1, 0.9))
    assert len(fc) == 6
    assert fc["date"].iat[0] == s.index[-1] + pd.offsets.MonthBegin()
    assert (fc["low"] <= fc["forecast"]).all() and (fc["forecast"] <= fc["high"]).all()


def test_sij_fuel_cost_per_mile():
    fc = pd.DataFrame({"date": pd.to_datetime(["2027-01-01"]), "forecast": [3.87],
                       "low": [3.60], "high": [4.20]})
    out = whatif.fuel_cost_per_mile(fc, mpg=6.45)
    assert out["fuel_cost_per_mile"].iat[0] == pytest.approx(0.6)
    assert out["fuel_cost_per_mile_low"].iat[0] < out["fuel_cost_per_mile_high"].iat[0]
