import pandas as pd
import numpy as np
import math
from scipy import optimize
import scipy.stats as si
from scipy.stats import norm

def find_atm(options_df: pd.DataFrame, underlying_df: pd.DataFrame, date: pd.Timestamp, num_options: int, target_expiry: int, tol: float) -> list[tuple[str, str]]:
    """
    Finds at-the-money option couples (put and call) for a given issuer at a specific date, only works with 1 issuer, do not input csv file with more than 1 issuer
    Takes in the target days to expiry, and number of option couples as arguments.

    Args:
        options_data (str): csv file from WRDS OptionMetrics database containing options data, 
                            must include "date", "symbol", and "strike_price" columns
        underlying_data (str): csv file from WRDS CRSP database containing stocks data of the underlying stocks for the options,
                               must include "date", "PRC" data
        date (pandas.Timestamp): The date to find ATM options at
        target_expiry (int): The target days to expiry wanted, function returns the options closest to it
        num_options (int): Number of option couples to find
        tol (float): Relative tolerance for what constitutes at-the-money, for example 0.05 would consider anything +- %5 of the stock price atm

    Returns:
        list: A list of tuples of option names (put and call in no specific order as str)
    """

    # Initializing data
    options_df = options_df[options_df["date"] == date]
    options_df.reset_index(inplace=True)

    underlying_df = underlying_df[underlying_df["date"] == date]
    underlying_df.reset_index(inplace=True)
    stock_price = underlying_df["PRC"][0]

    atm_list = [] # Return value

    for i, row in options_df.iterrows():
        # Iterating over the options data for one given date
        # Iterating over different options in one date given the stock at that date
        if (math.isclose(stock_price, row["strike_price"] / 1000, rel_tol=tol)):
            # At-the-money option
            option_name = row["symbol"]
            option_reverse = reverse_option(option_name) # Couple of the option, put or call with same strike and expiration
            option_tuple = (option_name, option_reverse)
            option_tuple_reverse = (option_reverse, option_name)
            if (option_reverse in options_df["symbol"].values) and (option_tuple not in atm_list) and (option_tuple_reverse not in atm_list):
                # Checking if the option has an atm couple, adding to dict if there is
                atm_list.append(option_tuple)

    options_df = options_df.set_index("symbol")
    option_expiry_dict = {}
    expiry_set = set()
    for couple in atm_list:
        option1 = couple[0]
        option2 = couple[1]
        expiration_date = options_df.loc[option1]["exdate"]
        expiration_time_interval = (expiration_date - date).days
        expiry_set.add(expiration_time_interval)
        option_expiry_dict[couple] = expiration_time_interval
    expiry = min(expiry_set, key=lambda x: abs(x - target_expiry))
    option_expiry_dict = {key: value for key, value in option_expiry_dict.items() if value == expiry}
    
    option_volume_dict = {}
    for couple in option_expiry_dict:
        option1 = couple[0]
        option2 = couple[1]
        option1_volume = options_df.loc[option1]["volume"]
        option2_volume = options_df.loc[option2]["volume"]
        avg_volume = (option1_volume + option2_volume) / 2
        option_volume_dict[couple] = avg_volume
    
    option_volume_dict = sorted(option_volume_dict.items(), key=lambda x:x[1], reverse=True)
    options_list = [option_couple[0] for option_couple in option_volume_dict[:num_options]]

    return options_list

def find_atm_given_expiration(options_df: pd.DataFrame, underlying_df: pd.DataFrame, date: pd.Timestamp, num_options: int, tol: float, expiration: pd.Timestamp) -> list[tuple[str, str]]:
    """
    Finds at-the-money option couples (put and call) for a given issuer at a specific date, only works with 1 issuer, do not input csv file with more than 1 issuer
    Takes in the target days to expiry, and number of option couples as arguments.

    Args:
        options_data (str): csv file from WRDS OptionMetrics database containing options data, 
                            must include "date", "symbol", and "strike_price" columns
        underlying_data (str): csv file from WRDS CRSP database containing stocks data of the underlying stocks for the options,
                               must include "date", "PRC" data
        date (pandas.Timestamp): The date to find ATM options at
        target_expiry (int): The target days to expiry wanted, function returns the options closest to it
        num_options (int): Number of option couples to find
        tol (float): Relative tolerance for what constitutes at-the-money, for example 0.05 would consider anything +- %5 of the stock price atm

    Returns:
        list: A list of tuples of option names (put and call in no specific order as str)
    """

    # Initializing data
    options_df = options_df[options_df["date"] == date]
    options_df.reset_index(inplace=True)

    underlying_df = underlying_df[underlying_df["date"] == date]
    underlying_df.reset_index(inplace=True)
    stock_price = underlying_df["PRC"][0]

    atm_list = [] # Return value

    for i, row in options_df.iterrows():
        # Iterating over the options data for one given date
        # Iterating over different options in one date given the stock at that date
        if (math.isclose(stock_price, row["strike_price"] / 1000, rel_tol=tol)):
            # At-the-money option
            option_name = row["symbol"]
            option_expiration = row["exdate"]
            option_reverse = reverse_option(option_name) # Couple of the option, put or call with same strike and expiration
            option_tuple = (option_name, option_reverse)
            option_tuple_reverse = (option_reverse, option_name)
            if (option_reverse in options_df["symbol"].values) and (option_tuple not in atm_list) and (option_tuple_reverse not in atm_list) and (option_expiration == expiration):
                # Checking if the option has an atm couple, adding to dict if there is
                atm_list.append(option_tuple)
    
    options_df = options_df.set_index("symbol")
    option_volume_dict = {}
    for couple in atm_list:
        option1 = couple[0]
        option2 = couple[1]
        option1_volume = options_df.loc[option1]["volume"]
        option2_volume = options_df.loc[option2]["volume"]
        avg_volume = (option1_volume + option2_volume) / 2
        option_volume_dict[couple] = avg_volume
    
    option_volume_dict = sorted(option_volume_dict.items(), key=lambda x:x[1], reverse=True)
    options_list = [option_couple[0] for option_couple in option_volume_dict[:num_options]]

    return options_list
    

def reverse_option(option_name:str) -> str:
    """
    Finds the couple of an option (put if call, call if put) with same expiration and strike, returns the couple as str

    Args:
        option_name (str): The option to find the couple, should be in WRDS OptionMetrics symbol format, for example "AAPL 190104C120000"

    Returns:
        str: Symbol of the couple of the option 
    """
    option_list = option_name.split()
    if option_list[1][6] == "C":
        reverse = option_list[0] + " " + option_list[1][:6] + "P" + option_list[1][7:]
    else:
        reverse = option_list[0] + " " + option_list[1][:6] + "C" + option_list[1][7:]
    return reverse

def get_total_delta(options_df: pd.DataFrame, underlying_df: pd.DataFrame, risk_free_df: pd.DataFrame, options_list: list[str], date: pd.Timestamp) -> float:
    """
    Gets the number of shares to buy or sell given a list of options, should be from the same issuer and have contract size 100
    
    Args:
        options_df: Pandas dataframe with WRDS options data
        options_list: List of option symbols as str
        date: The date to hedge at

    Returns:
        Number of underlying stocks to buy or sell

    """

    try:
        starting_date = date - pd.Timedelta(days=365)
        starting_dividend = underlying_df.loc[underlying_df['date'] == starting_date, 'DIVAMT'].item()
    except:
        starting_date = underlying_df.iloc[0]["date"]
    
    start_index = underlying_df.index[underlying_df['date'] == starting_date].tolist()[0]
    end_index = underlying_df.index[underlying_df['date'] == date].tolist()[0]

    volatility_df = underlying_df.iloc[start_index:end_index+1]

    cur_price = underlying_df.loc[underlying_df['date'] == date, 'PRC'].item()
    historical = volatility_df['PRC'].std() / cur_price

    total_delta = 0
    for option in options_list:
        delta = get_delta(options_df, underlying_df, risk_free_df, option, date, historical)
        total_delta += delta

    return total_delta

def get_iv(S, K, T, r, market_price, option_type, q=0, historical=None):
    
    if (option_type == "C"):
        def bs_price(sigma):
            d1 = (np.log(S/K)+(r-q+0.5*sigma**2)*T)/(sigma*np.sqrt(T))
            d2 = d1-(sigma*np.sqrt(T))
            price = S*np.exp(-q*T)*si.norm.cdf(d1,0,1)-K*np.exp(-r*T)*si.norm.cdf(d2,0,1)
            f = price - market_price
            return f
    elif (option_type == "P"):
        def bs_price(sigma):
            d1 = (np.log(S/K)+(r-q+0.5*sigma**2)*T)/(sigma*np.sqrt(T))
            d2 = d1-(sigma*np.sqrt(T))
            price = -S*np.exp(-q*T)*si.norm.cdf(-d1,0,1)+K*np.exp(-r*T)*si.norm.cdf(-d2,0,1)
            f = price - market_price
            return f
    
    try:
        return optimize.brentq(bs_price,0.000000001,10000,maxiter=2000)
    except ValueError:
        # Brent failed, trying Newton-Rhapson
        try:
            return optimize.newton(bs_price, historical)
        except RuntimeError:
            # Newton-Rhapson failed, using historical volatility
            return historical

def delta_calc(r, S, K, T, sigma, type, q=0):

    d1= (np.log(S/K)+(r-q+0.5*sigma**2)*T)/(sigma*np.sqrt(T))
    if type == "C":
        delta_calc = norm.cdf(d1, 0, 1)
    elif type == "P":
        delta_calc = -norm.cdf(-d1, 0, 1)
    return delta_calc

def get_delta(options_df, underlying_df, risk_free_df, option, date, historical):
    option_df = options_df[options_df["date"] == date]
    option_df = option_df[option_df["symbol"] == option]
    spot = underlying_df.loc[underlying_df['date'] == date, 'PRC'].item()
    strike = option_df["strike_price"].item() / 1000
    time_to_maturity = (option_df["exdate"].item() - date).days / 365
    price = (option_df["best_bid"].item() + option_df["best_offer"].item()) / 2
    type = option.split()[1][6]
    try:
        risk_free_rate = risk_free_df.loc[risk_free_df['DATE'] == date, 'DGS10'].item()
        if (risk_free_rate == "."):
            risk_free_rate = risk_free_df.loc[risk_free_df['DATE'] == (date - pd.Timedelta(days=1)), 'DGS10'].item()
    except ValueError:
        i = 1
        while (True):
            try:
                risk_free_rate = risk_free_df.loc[risk_free_df['DATE'] == (date - pd.Timedelta(days=i)), 'DGS10'].item()
                if (risk_free_rate != "."):
                    break
            except ValueError:
                pass
            i += 1
            
    risk_free_rate = float(risk_free_rate) / 100
    try:
        starting_date = date - pd.Timedelta(days=365)
        starting_dividend = underlying_df.loc[underlying_df['date'] == starting_date, 'DIVAMT'].item()
    except:
        starting_date = underlying_df.iloc[0]["date"]

    running_date = starting_date

    total_dividends = 0
    while(running_date < date):
        try:
            dividend = underlying_df.loc[underlying_df['date'] == running_date, 'DIVAMT'].item()
        except:
            running_date += pd.Timedelta(days=1)
            continue
        if  not math.isnan(dividend):
            total_dividends += dividend
        running_date += pd.Timedelta(days=1)

    dividend_yield = total_dividends / spot

    iv = get_iv(S=spot, K=strike, T=time_to_maturity, r=risk_free_rate, market_price=price, option_type=type, q = dividend_yield, historical=historical)
    delta = delta_calc(S=spot, K=strike, T=time_to_maturity, r=risk_free_rate, sigma=iv, type=type, q = dividend_yield)

    return delta    

def calculate_allocation_premium_neutral(
        num_options: int, 
        etf_options_df: pd.DataFrame,
        etf_underlying_df: pd.DataFrame,
        stock_options_dataframes: dict[str, pd.DataFrame],
        stock_underlying_dataframes: dict[str, pd.DataFrame],
        date: pd.Timestamp, 
        target_expiry: int,
        tol: float,
        etf_weightings: dict[str, float]) -> dict[str, float]:
    # Calculate ATM options for ETF
    etf_atm_options = find_atm(etf_options_df, etf_underlying_df, date, 1, target_expiry, tol)

    # Current etf_weightings don't sum to 1, so we scale them
    scaled_etf_weightings = {stock: etf_weightings[stock] / sum(etf_weightings.values()) for stock in etf_weightings}
    
    # Calculate total ETF premium from ATM options
    total_etf_premium = 0
    for call_id, put_id in etf_atm_options:
        call_data = etf_options_df.loc[etf_options_df['symbol'] == call_id].iloc[0]
        put_data = etf_options_df.loc[etf_options_df['symbol'] == put_id].iloc[0]
        call_premium = ((call_data['best_bid'] + call_data['best_offer']) / 2) * call_data['contract_size']
        put_premium = ((put_data['best_bid'] + put_data['best_offer']) / 2) * put_data['contract_size']
        total_etf_premium += call_premium + put_premium # Plus because selling options on index

    total_etf_premium *= num_options  # Adjust for the number of options we buy/sell

    # Calculate total premium for each stock
    stock_premiums = {}
    total_weighted_premiums = 0
    for stock, stock_options_df in stock_options_dataframes.items():
        stock_underlying_df = stock_underlying_dataframes[stock]
        stock_atm_options = find_atm(stock_options_df, stock_underlying_df, date, 1, target_expiry, tol)
        
        total_stock_premium = 0
        for call_id, put_id in stock_atm_options:
            call_data = stock_options_df.loc[stock_options_df['symbol'] == call_id].iloc[0]
            put_data = stock_options_df.loc[stock_options_df['symbol'] == put_id].iloc[0]
            call_premium = ((call_data['best_bid'] + call_data['best_offer']) / 2) * call_data['contract_size']
            put_premium = ((put_data['best_bid'] + put_data['best_offer']) / 2) * put_data['contract_size']
            total_stock_premium += call_premium + put_premium
        
        stock_premiums[stock] = total_stock_premium
        total_weighted_premiums += total_stock_premium * scaled_etf_weightings[stock]

    print(stock_premiums)

    c = total_etf_premium / total_weighted_premiums    

    # Get the number of straddles for each stock by C * scaled_weighting.
    allocation_results = {stock: int(round(c * scaled_etf_weightings[stock] * num_options)) for stock in stock_premiums}

    return allocation_results
