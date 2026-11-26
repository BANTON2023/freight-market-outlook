"""Step 2 of the pipeline: test the models, forecast, and apply the SIJ what-if.

Run from the project folder, after scripts/fetch_data.py:
    python scripts/run_forecast.py

Writes to outputs/:
    model_scores.csv     each model's average error per series (lower is better)
    backtest.csv         every past test forecast, for charts in Power BI
    forecast.csv         the next months for each series, with a low-high range
    history.csv          the monthly actuals the forecasts start from
    sij_whatif.csv       SIJ fuel cost per mile if diesel follows the forecast
    <series>.png         a chart per series
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import matplotlib  # noqa: E402

matplotlib.use("Agg")  # draw charts to files, no window
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

from fmo import config, forecast, whatif  # noqa: E402


def load_series() -> dict[str, tuple[str, pd.Series]]:
    """Read the downloaded files as monthly series: {key: (label, series)}."""
    out = {}
    diesel = pd.read_csv(config.DATA_DIR / "diesel_weekly.csv", parse_dates=["date"])
    out["diesel"] = ("U.S. diesel price ($/gallon)", forecast.to_monthly(diesel, "price"))
    for series_id, label in config.FRED_SERIES.items():
        df = pd.read_csv(config.DATA_DIR / f"fred_{series_id}.csv", parse_dates=["date"])
        out[series_id] = (label, forecast.to_monthly(df, "value"))
    return {k: (label, s[s.index >= config.TRAIN_START]) for k, (label, s) in out.items()}


def chart(key: str, label: str, series: pd.Series, fc: pd.DataFrame) -> None:
    recent = series.iloc[-60:]
    fig, ax = plt.subplots(figsize=(9, 4))
    ax.plot(recent.index, recent.values, color="#1f4e79", label="Actual (monthly average)")
    ax.plot(fc["date"], fc["forecast"], color="#c55a11", linestyle="--",
            label=f"Forecast ({fc['model'].iat[0].replace('_', ' ')})")
    ax.fill_between(fc["date"], fc["low"], fc["high"], color="#c55a11", alpha=0.15,
                    label="Range (80% of past errors)")
    ax.set_title(label)
    ax.legend(frameon=False, loc="upper left")
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(config.OUTPUT_DIR / f"{key}.png", dpi=150)
    plt.close(fig)


def main() -> None:
    config.OUTPUT_DIR.mkdir(exist_ok=True)
    scores, tests, forecasts, history = [], [], [], []
    for key, (label, series) in load_series().items():
        print(f"{label}: {len(series)} months, {series.index[0]:%Y-%m} to {series.index[-1]:%Y-%m}")
        results = forecast.backtest(series, config.HORIZON_MONTHS, config.BACKTEST_MONTHS)
        table = forecast.score(results)
        print(table.to_string(index=False, float_format=lambda v: f"{v:,.3f}"))
        best = table["model"].iat[0]
        fc = forecast.forecast(series, best, results, config.HORIZON_MONTHS, config.INTERVAL)
        chart(key, label, series, fc)
        print(f"  best: {best}; next month {fc['forecast'].iat[0]:,.3f}\n")

        scores.append(table.assign(series=key))
        tests.append(results.assign(series=key))
        forecasts.append(fc.assign(series=key))
        history.append(series.rename("value").rename_axis("date").reset_index().assign(series=key))
        if key == "diesel":
            whatif.fuel_cost_per_mile(fc).to_csv(config.OUTPUT_DIR / "sij_whatif.csv", index=False)

    for name, frames in [("model_scores", scores), ("backtest", tests),
                         ("forecast", forecasts), ("history", history)]:
        pd.concat(frames).to_csv(config.OUTPUT_DIR / f"{name}.csv", index=False,
                                 float_format="%.4f", date_format="%Y-%m-%d")
    print(f"Outputs written to {config.OUTPUT_DIR}")


if __name__ == "__main__":
    main()
