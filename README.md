# Freight Market Outlook

Forecasts of U.S. diesel prices and freight demand, built from two public APIs, with
an illustrative what-if for **SIJ Logistics & Analytics**, the fictional trucking
company from [SIJ-Logistics-Analytics](https://github.com/BANTON2023/SIJ-Logistics-Analytics).

> **Status:** in progress (v0.1.0): data pipeline, backtested forecasts and SIJ what-if.
> Power BI page and PostgreSQL storage come next (see [Roadmap](#roadmap)).

## Questions it answers

1. Where are U.S. diesel prices heading over the next 6 months, and how sure can we be?
2. Is U.S. freight demand rising or falling?
3. If diesel follows the forecast, what would SIJ's fuel cost per mile be?

## How it works

```
EIA API  ──► weekly diesel price ──┐
                                   ├─► monthly series ─► backtest 3 models ─► best model
FRED API ──► truck tonnage,       ─┘                     (last 36 months)     forecasts 6 months
             freight services index                                           with a range
                                                                                   │
                                                  SIJ what-if: price ÷ 6.45 MPG ◄──┘
```

- **Data:** [EIA API v2](https://www.eia.gov/opendata/documentation.php) series
  `EMD_EPD2D_PTE_NUS_DPG` (U.S. No 2 diesel retail price, weekly) and
  [FRED](https://fred.stlouisfed.org/docs/api/fred/) series `TRUCKD11` (ATA truck
  tonnage) and `TSIFRGHT` (BTS Freight Transportation Services Index), both monthly.
- **Models:** naive (next month = this month), seasonal naive (same month last year)
  and Holt-Winters exponential smoothing with a damped trend.
- **Honest testing:** a rolling-origin backtest. For each of the last 36 months, each
  model is fitted only on data before that month and forecasts the next 6. The model
  with the lowest MAPE (average % miss) is used. Every model must beat the naive one
  to be worth anything.
- **Forecast range:** the 10th to 90th percentile of the chosen model's own past
  errors at each step ahead, so 80% of past forecasts landed inside a range this wide.
- **SIJ what-if:** SIJ's data is fictional, so no model is fitted to it. Only its
  fleet fuel economy (6.45 MPG) is used: fuel cost per mile = diesel price ÷ MPG.

## Run it yourself

Needs Python 3.11 or later.

1. **Get your API keys** (free): EIA at [eia.gov/opendata](https://www.eia.gov/opendata/)
   and FRED at [fred.stlouisfed.org/docs/api/api_key.html](https://fred.stlouisfed.org/docs/api/api_key.html).
2. **Set up** in a terminal in this folder:

   ```bash
   python -m venv .venv
   .venv\Scripts\activate        # Windows; on Mac/Linux: source .venv/bin/activate
   pip install -r requirements.txt
   copy .env.example .env        # then paste your two keys into .env
   ```

3. **Run the pipeline:**

   ```bash
   python scripts/fetch_data.py     # download the data into data/
   python scripts/run_forecast.py   # test the models, forecast, write outputs/
   pytest                           # run the tests (no keys needed)
   ```

Your keys stay in `.env`, which Git ignores. They are never written to code or output.

## Outputs

| File | Contents |
| --- | --- |
| `data/diesel_weekly.csv`, `data/fred_*.csv` | Raw downloads |
| `data/fetch_log.csv` | When each download ran, rows and latest date |
| `outputs/model_scores.csv` | MAPE and MAE per model and series |
| `outputs/backtest.csv` | Every past test forecast with its error |
| `outputs/forecast.csv` | The next 6 months per series, with low and high |
| `outputs/history.csv` | Monthly actuals |
| `outputs/sij_whatif.csv` | SIJ fuel cost per mile under the diesel forecast |
| `outputs/*.png` | One chart per series |

## Project structure

```
src/fmo/        config.py   settings, series IDs, API keys from .env
                http.py     API calls with timeouts, retries, hidden keys
                eia.py      EIA client (pages through results)
                fred.py     FRED client
                forecast.py models, backtest, scoring, forecast range
                whatif.py   SIJ fuel cost per mile
scripts/        fetch_data.py, run_forecast.py
tests/          unit tests with saved sample responses (no network)
.github/        checks.yml (tests on every pull request), refresh.yml (weekly update)
```

## Automation

- **checks:** runs the tests on every pull request.
- **refresh:** every Tuesday it downloads new data, re-forecasts and commits the
  results. It needs the repository secrets `EIA_API_KEY` and `FRED_API_KEY`. It
  commits straight to `main`, so a branch protection rule must allow
  `github-actions[bot]` to push.

## Roadmap

- [x] Pull diesel and freight data from the EIA and FRED APIs
- [x] Baseline and Holt-Winters forecasts with a rolling backtest
- [x] SIJ fuel cost per mile what-if
- [ ] Machine-learning model (XGBoost with lag features) to compare against Holt-Winters
- [ ] Store the data in PostgreSQL
- [ ] Power BI page: actuals, forecast range and the SIJ what-if
- [ ] Turn on the weekly refresh with repository secrets

## Contributing

Changes go through pull requests: branch from `main`, use
[Conventional Commits](https://www.conventionalcommits.org/), and the checks must pass.

## License

[MIT](LICENSE). Data: U.S. Energy Information Administration and Federal Reserve
Bank of St. Louis (FRED), both public. This project is not affiliated with either.
