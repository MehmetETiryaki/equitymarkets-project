import pandas as pd
import pandas_market_calendars as mcal
import matplotlib.pyplot as plt
import math as math
from equity import find_atm
import equity as eq


def backtest_short_straddle_with_premium_change(options_csv, underlying_csv, options_df, underlying_df, risk_free_df, start_date, number_of_options, expiration_time, hedging=True):
    portfolio = {'options': [], 'underlying': 0, 'premium_costs': 0, "stock_costs": 0}
    daily_returns = []
    nyse_calendar = mcal.get_calendar('NYSE')

    atm_options = find_atm(options_csv, underlying_csv, start_date, number_of_options,expiration_time, 0.1)
    print(atm_options)
    for call_id, put_id in atm_options:
        call_data = options_df.loc[options_df['symbol'] == call_id].iloc[0]
        put_data = options_df.loc[options_df['symbol'] == put_id].iloc[0]
        call_premium = ((call_data['best_bid'] + call_data['best_offer']) / 2) * call_data['contract_size']
        put_premium = ((put_data['best_bid'] + put_data['best_offer']) / 2) * put_data['contract_size']
        portfolio['options'].append({'data': call_data, 'symbol': call_id, 'premium_received': call_premium})
        portfolio['options'].append({'data': put_data, 'symbol': put_id, 'premium_received': put_premium})
        portfolio['premium_costs'] += call_premium + put_premium

    expiry_date_list = []
    for option in portfolio["options"]:
        expiry_date_list.append(option["data"]["exdate"])
    expiry_date_set = set(expiry_date_list)
    max_expiry = max(expiry_date_set)

    trading_days = nyse_calendar.schedule(start_date, max_expiry)
    trading_day_index = mcal.date_range(trading_days, frequency='1D')
    # Change all dates to timestamps, with time 00:00:00
    trading_day_index = [pd.Timestamp(date.date()) for date in trading_day_index]

    for current_date in trading_day_index:
        spot_price = underlying_df.loc[underlying_df['date'] == current_date, 'PRC'].item()
        daily_unrealized_pnl = 0  # Initialize daily unrealized profit/loss from options
        # Process options expiring today
        options_to_remove = []
        for option in portfolio['options']:
            option_data_latest = options_df[options_df["date"] == current_date]
            option_data_latest= option_data_latest[option_data_latest["symbol"] == option["symbol"]]
            # Fetch the option data that is most current as of the current_date
            #option_data_latest = options_df.loc[(options_df['symbol'] == option['symbol']) & (options_df['date'] <= current_date)].sort_values(by='date').iloc[-1]
            exdate = option['data']['exdate']

            if exdate == current_date:
                # Calculate and realize P&L from option expiration
                option_type = option["symbol"].split()[1][6]
                pnl = min(spot_price - (option["data"]["strike_price"]/1000), 0) if 'P' == option_type else min(-spot_price + (option["data"]["strike_price"]/1000), 0)
                pnl *= option["data"]['contract_size']
                contract_size = option["data"]['contract_size']
                portfolio['premium_costs'] += pnl
                options_to_remove.append(option)
            else:
                # Calculate unrealized P&L for non-expiring options using the most recent premium information
                current_premium = ((option_data_latest['best_bid'].values[0] + option_data_latest['best_offer'].values[0]) / 2) * option["data"]['contract_size']
                daily_unrealized_pnl -= current_premium 

        #print(current_date)
        #print("Premium pnl:", daily_unrealized_pnl)
        #print("Premium costs:", portfolio["premium_costs"])
        daily_unrealized_pnl += spot_price * portfolio["underlying"]
        #print("Number of stocks:", portfolio["underlying"])
        #print("Stock pnl:", spot_price * portfolio["underlying"])
        #print("Stock costs:", portfolio["stock_costs"])
        #print("Total pnl:", daily_unrealized_pnl)
        #print("Total costs:", portfolio['premium_costs'] + portfolio["stock_costs"])
        #print("Total real pnl:", daily_unrealized_pnl + portfolio['premium_costs'] + portfolio["stock_costs"])
        #print("Spot price:", spot_price)
        # Remove expired options
        for option in options_to_remove:
            portfolio['options'].remove(option)

        # Daily rebalance based on delta
        portfolio_option_symbols = [option['symbol'] for option in portfolio['options']]
        daily_pnl = daily_unrealized_pnl + portfolio["premium_costs"] + portfolio["stock_costs"] # Update to include cash change

        #print("Number of stocks before hedge:", portfolio["underlying"])
        
        if hedging:
            contract_size = 100 # TODO: Fix this
            delta_without_stocks = eq.get_total_delta(options_df, underlying_df, risk_free_df, portfolio_option_symbols, current_date)
            delta_with_stocks = delta_without_stocks - (portfolio["underlying"] * (1/contract_size))
            #print("Delta before hedge:", delta_with_stocks)
            #print(current_date)
            #print("Delta before hedging", delta_with_stocks)
            if current_date != trading_day_index:
                if (abs(delta_with_stocks) > 0.1):
                    hedge_count = -int(round(delta_with_stocks * contract_size))
                    portfolio["stock_costs"] += hedge_count * spot_price
                    portfolio["underlying"] -= hedge_count

            delta_without_stocks = eq.get_total_delta(options_df, underlying_df, risk_free_df, portfolio_option_symbols, current_date)
            delta_with_stocks = delta_without_stocks - (portfolio["underlying"] * (1/contract_size))

        #print("Delta after hedge:", delta_with_stocks)
        #print("Number of stocks after hedge:", portfolio["underlying"])

        
        #print("Delta after hedging", delta_with_stocks)
        # Add daily unrealized P&L from options to daily returns
        # Calculate and include real cash changes in daily P&L
    
        daily_returns.append(daily_pnl)

    return pd.Series(daily_returns, index=trading_day_index)