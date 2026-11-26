# Changelog

All notable changes to this project are recorded here.
The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the
project uses [Semantic Versioning](https://semver.org/).

## [Unreleased]

## [0.1.0] - 2026-11-26

### Added

- EIA client for weekly U.S. diesel prices, with paging, retries and hidden keys.
- FRED client for the ATA truck tonnage index and the BTS Freight Transportation
  Services Index.
- Forecasting: naive, seasonal naive and Holt-Winters models, a 36-month rolling
  backtest, and 6-month forecasts with ranges from past errors.
- SIJ Logistics what-if: fuel cost per mile under the diesel forecast.
- Unit tests that need no network or keys, and GitHub Actions workflows for tests
  and a weekly data refresh.
