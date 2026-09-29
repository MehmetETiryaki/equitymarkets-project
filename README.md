# equitymarkets-project

Team 2's project for Dr. John Miller's class "Equity Markets and Quantitative Trading" at Johns Hopkins.

We backtest options volatility strategies on US equities and ETFs using daily historical data.

## Strategies

- **Short / long straddle:** sell (or buy) at-the-money call and put pairs, with optional daily delta hedging in the underlying and optional buyback before expiry.
- **Dispersion:** sell ATM straddles on an index ETF (e.g. XLK) and buy straddles on its constituents. Positions are sized so the premiums balance.

Deltas come from Black-Scholes with implied volatility solved from market prices. The model accounts for dividend yield and uses the 10-year Treasury rate as the risk-free rate.

## Structure

```
equity.py          ATM option selection, implied volatility, delta, dispersion sizing
equity_strats.py   Backtests: short straddle, long straddle, dispersion
main.py            Example: chained short-straddle backtests on AAPL
notebooks/         Backtest experiments and plots
data/DGS10.csv     10-year Treasury yield (FRED)
```

## Data

Options data comes from WRDS OptionMetrics and stock data from WRDS CRSP. Neither is included in this repo because both are licensed. Place the CSV exports in `data/`.

## Usage

```
pip install pandas numpy scipy matplotlib pandas_market_calendars
python main.py
```
