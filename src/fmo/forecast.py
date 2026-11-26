"""Monthly forecasting: three candidate models, an honest backtest, and a forecast.

How the test works (rolling-origin backtest):
  Pretend it is month M in the past. Fit each model only on data up to M, forecast
  the next HORIZON months, and record how far off each forecast was. Repeat for
  every month in the backtest window. The model with the lowest average % error
  (MAPE) wins, and the spread of its past errors sets the forecast range.
"""
import warnings

import numpy as np
import pandas as pd
from statsmodels.tsa.holtwinters import ExponentialSmoothing

SEASON = 12  # months in a year


def to_monthly(df: pd.DataFrame, value_col: str) -> pd.Series:
    """Average a dated table by calendar month (month-start dates)."""
    s = df.set_index("date")[value_col].resample("MS").mean()
    return s.dropna()


# --- Candidate models: each takes past values and returns the next h values ---

def naive(history: pd.Series, h: int) -> np.ndarray:
    """Next months = the last month. The benchmark every model must beat."""
    return np.repeat(history.iloc[-1], h)


def seasonal_naive(history: pd.Series, h: int) -> np.ndarray:
    """Next months = the same months last year."""
    last_year = history.iloc[-SEASON:].to_numpy()
    return np.array([last_year[i % SEASON] for i in range(h)])


def holt_winters(history: pd.Series, h: int) -> np.ndarray:
    """Exponential smoothing with a damped trend and yearly seasonality."""
    model = ExponentialSmoothing(
        history.to_numpy(), trend="add", damped_trend=True,
        seasonal="add", seasonal_periods=SEASON,
    )
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")  # convergence chatter, checked by the backtest
        return model.fit().forecast(h)


MODELS = {"naive": naive, "seasonal_naive": seasonal_naive, "holt_winters": holt_winters}


def backtest(series: pd.Series, horizon: int, months: int) -> pd.DataFrame:
    """Forecast from every origin in the last `months` and record each error.

    Returns one row per (model, origin, step) with actual, forecast and error.
    """
    rows = []
    n = len(series)
    for origin in range(n - months, n - horizon + 1):
        history, future = series.iloc[:origin], series.iloc[origin:origin + horizon]
        for name, model in MODELS.items():
            forecast = model(history, len(future))
            for step, (date, actual) in enumerate(future.items(), start=1):
                rows.append({
                    "model": name, "origin": series.index[origin - 1], "step": step,
                    "date": date, "actual": actual, "forecast": forecast[step - 1],
                })
    out = pd.DataFrame(rows)
    out["error"] = out["actual"] - out["forecast"]
    out["pct_error"] = 100 * out["error"].abs() / out["actual"].abs()
    return out


def score(results: pd.DataFrame) -> pd.DataFrame:
    """MAPE (average % miss) and MAE (average miss in units) per model, best first."""
    table = results.groupby("model").agg(
        mape=("pct_error", "mean"), mae=("error", lambda e: e.abs().mean()),
        forecasts=("origin", "nunique"),
    )
    return table.sort_values("mape").reset_index()


def forecast(series: pd.Series, model_name: str, results: pd.DataFrame,
             horizon: int, interval: tuple[float, float]) -> pd.DataFrame:
    """Forecast the next `horizon` months with the chosen model and a range.

    The range adds the chosen model's own past errors at each step (10th and
    90th percentiles by default) to the point forecast, so it reflects how
    wrong the model has actually been, not a textbook assumption.
    """
    point = MODELS[model_name](series, horizon)
    dates = pd.date_range(series.index[-1] + pd.offsets.MonthBegin(), periods=horizon, freq="MS")
    errors = results[results["model"] == model_name].groupby("step")["error"]
    low = errors.quantile(interval[0]).reindex(range(1, horizon + 1)).to_numpy()
    high = errors.quantile(interval[1]).reindex(range(1, horizon + 1)).to_numpy()
    return pd.DataFrame({
        "date": dates, "model": model_name, "forecast": point,
        "low": point + low, "high": point + high,
    })
