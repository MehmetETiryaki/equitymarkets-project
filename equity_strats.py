import pandas as pd
import pandas_market_calendars as mcal
import matplotlib.pyplot as plt
import math as math
from equity import find_atm
import equity as eq


def backtest_short_straddle_with_premium_change(options_df, underlying_df, risk_free_df, start_date, number_of_options, expiration_time, buyback_period, hedging=True, file=None):
    portfolio = {'options': [], 'underlying': 0, 'premium_costs': 0, "stock_costs": 0}
    results_dict = {"date": [], "cost of selling options": [], "number of stocks eod": [], "delta eod": [], "costs of stocks after": [], "pnl of premiums": [], "pnl of stocks": [], "unrealized pnl": [], "daily pnl": [], \
                    "number of stocks before": [], "delta before": [], "costs of stocks daily": []}
    daily_returns = []
    nyse_calendar = mcal.get_calendar('NYSE')
    buyback_period = pd.Timedelta(days=buyback_period)
 

    atm_options = find_atm(options_df, underlying_df, start_date, 1,expiration_time, 0.1)
    option_couple = atm_options[0]
    for i in range(number_of_options - 1):
        atm_options.append(option_couple)
    print(atm_options)
    for option_couple in atm_options:
        option1 = option_couple[0]
        option2 = option_couple[1]
        option1_data = options_df.loc[options_df['symbol'] == option1].iloc[0]
        option2_data = options_df.loc[options_df['symbol'] == option1].iloc[0]
        portfolio['options'].append({'data': option1_data, 'symbol': option1})
        portfolio['options'].append({'data': option2_data, 'symbol': option2})

    for option in portfolio["options"]:
        option_data_latest = options_df[options_df["date"] == start_date]
        option_data_latest= option_data_latest[option_data_latest["symbol"] == option["symbol"]]
        premium = ((option_data_latest['best_bid'].values[0] + option_data_latest['best_offer'].values[0]) / 2) * option["data"]['contract_size']
        portfolio['premium_costs'] += premium

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
        if len(portfolio["options"]) == 0:
            break
        print(current_date)
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
            buyback_date = exdate - buyback_period

            if exdate == current_date:
                # Calculate and realize P&L from option expiration
                contract_size = option["data"]['contract_size']
                option_type = option["symbol"].split()[1][6]
                pnl = min(spot_price - (option["data"]["strike_price"]/1000), 0) if 'P' == option_type else min(-spot_price + (option["data"]["strike_price"]/1000), 0)
                pnl *= option["data"]['contract_size']
                portfolio['premium_costs'] += pnl
                options_to_remove.append(option)
            elif buyback_date == current_date and buyback_date != exdate:
                current_premium = ((option_data_latest['best_bid'].values[0] + option_data_latest['best_offer'].values[0]) / 2) * option["data"]['contract_size']
                daily_unrealized_pnl -= current_premium 
                options_to_remove.append(option)
            else:
                # Calculate unrealized P&L for non-expiring options using the most recent premium information
                current_premium = ((option_data_latest['best_bid'].values[0] + option_data_latest['best_offer'].values[0]) / 2) * option["data"]['contract_size']
                daily_unrealized_pnl -= current_premium 

        # Remove expired options
        for option in options_to_remove:
            portfolio['options'].remove(option)

        results_dict["pnl of premiums"].append(daily_unrealized_pnl)
        daily_unrealized_pnl += spot_price * portfolio["underlying"]
        results_dict["pnl of stocks"].append(spot_price * portfolio["underlying"])


        # Daily rebalance based on delta
        portfolio_option_symbols = [option['symbol'] for option in portfolio['options']]
        daily_pnl = daily_unrealized_pnl + portfolio["premium_costs"] + portfolio["stock_costs"] # Update to include cash change

        #print("Number of stocks before hedge:", portfolio["underlying"])
        
        if hedging:
            contract_size = 100 # TODO: Fix this
            delta = eq.get_total_delta(options_df, underlying_df, risk_free_df, portfolio_option_symbols, current_date) - (portfolio["underlying"] * (1/contract_size))
            results_dict["number of stocks before"].append(portfolio["underlying"])
            results_dict["delta before"].append(delta)
            #print("Delta before hedge:", delta)
            #print(current_date)
            #print("Delta before hedging", delta_with_stocks)
            hedge_count = 0
            if current_date != trading_day_index:
                if (abs(delta) > 0.1):
                    hedge_count = int(round(delta * contract_size))
                    #print("Hedge count:", hedge_count)
                    portfolio["stock_costs"] -= hedge_count * spot_price
                    portfolio["underlying"] += hedge_count

            delta = eq.get_total_delta(options_df, underlying_df, risk_free_df, portfolio_option_symbols, current_date) - (portfolio["underlying"] * (1/contract_size))
            results_dict["number of stocks eod"].append(portfolio["underlying"])
            results_dict["delta eod"].append(delta)

            #print("Delta after hedge:", delta)
        #print("Number of stocks after hedge:", portfolio["underlying"])

        results_dict["costs of stocks daily"].append(hedge_count * spot_price)
        results_dict["date"].append(current_date)
        results_dict["cost of selling options"].append(portfolio["premium_costs"])
        results_dict["costs of stocks after"].append(portfolio["stock_costs"])
        results_dict["unrealized pnl"].append(daily_unrealized_pnl)
        results_dict["daily pnl"].append(daily_pnl)

        
        #print("Delta after hedging", delta_with_stocks)
        # Add daily unrealized P&L from options to daily returns
        # Calculate and include real cash changes in daily P&L
    
        daily_returns.append(daily_pnl)

        if file is not None:
            file.write(f"{current_date} {daily_pnl}\n")

    return pd.DataFrame(results_dict)


def backtest_dispersion(options_df_dict, underlying_df_dict, index_options_df, index_underlying_df, risk_free_df, options_weights_dict, start_date, target_expiry, etf_num, hedge = True):
    portfolio = {'companies': {}, 'underlying': {}, 'premium_costs': 0, "stock_costs": 0}
    daily_returns = []
    nyse_calendar = mcal.get_calendar('NYSE')

    for company in options_weights_dict:
        company_dict = {}
        atm_couple = find_atm(options_df_dict[company], underlying_df_dict[company], start_date, 1, 90, 0.05)[0]
        company_df = options_df_dict[company]
        option1_df = company_df[company_df["symbol"] == atm_couple[0]]
        option2_df = company_df[company_df["symbol"] == atm_couple[1]]
        company_dict["option1_df"] =  option1_df
        company_dict["option2_df"] =  option2_df
        company_dict["options_df"] =  company_df[company_df["symbol"].isin(list(atm_couple))]
        company_dict["options_df"]
        company_dict["couple"] = atm_couple
        company_dict["holdings"] = options_weights_dict[company]
        company_dict["exdate"] = option1_df[option1_df["date"] == start_date]["exdate"].iloc[0]
        company_dict["contract_size"] = option1_df[option1_df["date"] == start_date]["contract_size"].iloc[0]
        company_dict["company"] = company
        portfolio["companies"][company] = company_dict
        portfolio["underlying"][company] = 0
        print(atm_couple)

    etf_couple = eq.find_atm(index_options_df, index_underlying_df, start_date, 1, target_expiry, 0.05)[0]
    print(etf_couple)
    etf1_df = index_options_df[index_options_df["symbol"] == etf_couple[0]]
    etf1_df_start = etf1_df[etf1_df["date"] == start_date]
    etf2_df = index_options_df[index_options_df["symbol"] == etf_couple[1]]
    etf2_df_start = etf1_df[etf1_df["date"] == start_date]
    etf_expiration = etf1_df_start["exdate"].iloc[0]
    portfolio["underlying"]["etf"] = 0

    trading_days = nyse_calendar.schedule(start_date, etf_expiration)
    trading_day_index = mcal.date_range(trading_days, frequency='1D')
    # Change all dates to timestamps, with time 00:00:00
    trading_day_index = [pd.Timestamp(date.date()) for date in trading_day_index]

    etf1_start_premium = (etf1_df_start["best_bid"].iloc[0] + etf1_df_start["best_offer"].iloc[0]) / 2
    etf2_start_premium = (etf2_df_start["best_bid"].iloc[0] + etf2_df_start["best_offer"].iloc[0]) / 2
    total_etf_premium = (etf1_start_premium + etf2_start_premium) * etf_num
    etf_contract_size = etf1_df_start["contract_size"].iloc[0]
    portfolio["premium_costs"] += total_etf_premium * etf_contract_size

    total_company_premium = 0
    for company_dict in portfolio["companies"].values():
        total_premium = 0
        starting_df1 = company_dict["option1_df"][company_dict["option1_df"]["date"] == start_date]
        starting_df2 = company_dict["option2_df"][company_dict["option2_df"]["date"] == start_date] 
        starting_premium1 = (starting_df1["best_bid"].iloc[0] + starting_df1["best_offer"].iloc[0]) / 2
        starting_premium2 = (starting_df2["best_bid"].iloc[0] + starting_df2["best_offer"].iloc[0]) / 2
        total_premium = (starting_premium1 + starting_premium2) * company_dict["holdings"]
        total_company_premium += total_premium * company_dict["contract_size"]

    portfolio["premium_costs"] -= total_company_premium

    for current_date in trading_day_index:
        print(current_date)
        companies_to_remove = []
        daily_premiums = 0
        for company_dict in portfolio["companies"].values():   

            company_name = company_dict["company"]
            option1_df = company_dict["option1_df"][company_dict["option1_df"]["date"] == current_date]
            option2_df = company_dict["option2_df"][company_dict["option2_df"]["date"] == current_date]
            option_list = [company_dict["couple"][0], company_dict["couple"][1]]

            if (current_date != company_dict["exdate"]):

                underlying_df = underlying_df_dict[company_name]
                underlying_df_cur = underlying_df[underlying_df["date"] == current_date]
                spot_price = underlying_df_cur["PRC"].iloc[0]

                premium1 = (option1_df["best_bid"].iloc[0] + option1_df["best_offer"].iloc[0]) / 2
                premium2 = (option2_df["best_bid"].iloc[0] + option2_df["best_offer"].iloc[0]) / 2

                total_premium = (premium1 + premium2) * company_dict["contract_size"] * company_dict["holdings"]
                daily_premiums += total_premium

                delta = (eq.get_total_delta(company_dict["options_df"], underlying_df_dict[company_name], risk_free_df, option_list, current_date)  * company_dict["holdings"])  + ((1/company_dict["contract_size"]) * portfolio["underlying"][company_name])
                hedge_count = -int(round(delta * company_dict["contract_size"]))
                portfolio["underlying"][company_name] += hedge_count
                portfolio["stock_costs"] -= hedge_count * spot_price

            else:
                companies_to_remove.append(company_name)

                option_expired1 = company_dict["couple"][0]
                option_expired2 = company_dict["couple"][1]

                underlying_df = underlying_df_dict[company_name]
                underlying_df_expiration = underlying_df[underlying_df["date"] == current_date]
                spot_price = underlying_df_expiration["PRC"].iloc[0]

                option_1_type = option_expired1[6]
                option_2_type = option_expired2[6]

                strike_price1 = option1_df["strike_price"].iloc[0] / 1000
                strike_price2 = option2_df["strike_price"].iloc[0] / 1000

                pnl1 = max((-spot_price + strike_price1), 0) if 'P' == option_1_type else max((spot_price - strike_price1), 0)
                pnl2 = max((-spot_price + strike_price1), 0) if 'P' == option_2_type else max((spot_price - strike_price2), 0)

                total_pnl = pnl1 + pnl2

                portfolio["premium_costs"] += total_pnl
            
        for company in companies_to_remove:
            portfolio["companies"].pop(company)

        etf_option1_df = etf1_df[etf1_df["date"] == current_date]
        etf_option2_df = etf2_df[etf2_df["date"] == current_date]

        if (current_date != etf_expiration):

            etf1_premium = (etf_option1_df["best_bid"].iloc[0] + etf_option1_df["best_offer"].iloc[0]) / 2
            etf2_premium = (etf_option2_df["best_bid"].iloc[0] + etf_option2_df["best_offer"].iloc[0]) / 2
            etf_premium_total = (etf1_premium + etf2_premium) * etf_num * etf_contract_size

            daily_premiums -= etf_premium_total

        else:
            option_expired1 = etf_couple[0]
            option_expired2 = etf_couple[1]

            underlying_df = index_underlying_df
            underlying_df_expiration = underlying_df[underlying_df["date"] == current_date]
            spot_price = underlying_df_expiration["PRC"].iloc[0]

            option_1_type = option_expired1[6]
            option_2_type = option_expired2[6]

            strike_price1 = etf_option1_df["strike_price"].iloc[0] / 1000
            strike_price2 = etf_option2_df["strike_price"].iloc[0] / 1000

            pnl1 = -max((-spot_price + strike_price1), 0) if 'P' == option_1_type else -max((spot_price - strike_price1), 0)
            pnl1 = -max((-spot_price + strike_price1), 0) if 'P' == option_1_type else -max((spot_price - strike_price1), 0)

            total_pnl = pnl1 + pnl2

            portfolio["premium_costs"] += total_pnl

        daily_pnl = daily_premiums + portfolio["premium_costs"]

        daily_returns.append(daily_pnl)

    return pd.Series(daily_returns, index=trading_day_index)



    