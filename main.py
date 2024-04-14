import equity as eq
import equity_strats as eq_strats
import pandas as pd
import matplotlib.pyplot as plt
import math as math
import statistics

if __name__ == "__main__":
    #options_dict = eq.find_atm("apple_options.csv", "apple_stocks.csv", 1000, 0.01)
    #returns = eq.short_straddle("apple_options.csv", "apple_stocks.csv", options_dict)
    #print(sum(returns))
    #returns2 = eq.long_straddle("apple_options.csv", "apple_stocks.csv", options_dict)
    #print(sum(returns2))
    #print(eq.find_atm("apple_options.csv", "apple_stocks.csv", pd.Timestamp(2019, 1, 2), 1, 60, 0.05))

    AAPL_options_csv = 'apple_options.csv'
    AAPL_underlying_csv = 'apple_stocks.csv'
    AAPL_options = pd.read_csv(AAPL_options_csv, parse_dates = ["exdate", "date"])
    AAPL_underlying = pd.read_csv(AAPL_underlying_csv, parse_dates = ["date"])
    risk_free = pd.read_csv("DGS10.csv", parse_dates = ["DATE"])
    #print(eq.find_atm(AAPL_options_csv, AAPL_underlying_csv, pd.Timestamp(2022, 2, 28), 5, 90, 0.1))

    daily_returns1 = eq_strats.backtest_short_straddle_with_premium_change(AAPL_options_csv, AAPL_underlying_csv, AAPL_options, AAPL_underlying, risk_free, pd.Timestamp(2018,1,4), 10, 180)
    end_date1 = daily_returns1.index[-1]
    daily_returns2 = eq_strats.backtest_short_straddle_with_premium_change(AAPL_options_csv, AAPL_underlying_csv, AAPL_options, AAPL_underlying, risk_free, end_date1, 10, 180)
    end_date2 = daily_returns2.index[-1]
    daily_returns3 = eq_strats.backtest_short_straddle_with_premium_change(AAPL_options_csv, AAPL_underlying_csv, AAPL_options, AAPL_underlying, risk_free, end_date2, 10, 180)
    end_date3 = daily_returns3.index[-1]
    daily_returns4 = eq_strats.backtest_short_straddle_with_premium_change(AAPL_options_csv, AAPL_underlying_csv, AAPL_options, AAPL_underlying, risk_free, end_date3, 10, 180)
    end_date4 = daily_returns4.index[-1]
    daily_returns5 = eq_strats.backtest_short_straddle_with_premium_change(AAPL_options_csv, AAPL_underlying_csv, AAPL_options, AAPL_underlying, risk_free, end_date4, 10, 180)
    end_date5 = daily_returns5.index[-1]
    daily_returns6 = eq_strats.backtest_short_straddle_with_premium_change(AAPL_options_csv, AAPL_underlying_csv, AAPL_options, AAPL_underlying, risk_free, end_date5, 10, 180)
    end_date6 = daily_returns6.index[-1]
    daily_returns7 = eq_strats.backtest_short_straddle_with_premium_change(AAPL_options_csv, AAPL_underlying_csv, AAPL_options, AAPL_underlying, risk_free, end_date6, 10, 180)
    end_date7 = daily_returns7.index[-1]
    daily_returns8 = eq_strats.backtest_short_straddle_with_premium_change(AAPL_options_csv, AAPL_underlying_csv, AAPL_options, AAPL_underlying, risk_free, end_date7, 10, 180)

    #print(statistics.stdev(daily_returns))

    #daily_returns2 = eq_strats.backtest_short_straddle_with_premium_change(AAPL_options_csv, AAPL_underlying_csv, AAPL_options, AAPL_underlying, risk_free, pd.Timestamp(2021,1,4), 10, 180)
