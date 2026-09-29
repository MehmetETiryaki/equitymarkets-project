import equity_strats as eq_strats
import pandas as pd

if __name__ == "__main__":
    AAPL_options_csv = 'data/apple_options.csv'
    AAPL_underlying_csv = 'data/apple_stocks.csv'
    AAPL_options = pd.read_csv(AAPL_options_csv, parse_dates = ["exdate", "date"])
    AAPL_underlying = pd.read_csv(AAPL_underlying_csv, parse_dates = ["date"])
    risk_free = pd.read_csv("data/DGS10.csv", parse_dates = ["DATE"])

    start_date = pd.Timestamp(2018,1,4)
    daily_returns = []
    for i in range(8):
        results = eq_strats.backtest_short_straddle_with_premium_change(AAPL_options, AAPL_underlying, risk_free, start_date, 10, 180, 0)
        daily_returns.append(results)
        start_date = results["date"].iloc[-1]
