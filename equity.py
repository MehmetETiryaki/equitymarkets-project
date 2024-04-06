import pandas as pd
import numpy as np
import math

def find_atm(options_data: str, underlying_data: str, date: pd.Timestamp, num_options: int, target_expiry: int, tol: float) -> list[tuple[str, str]]:
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
    options_df = pd.read_csv(options_data, parse_dates = ["exdate", "date"])
    options_df = options_df[options_df["date"] == date]
    options_df.reset_index(inplace=True)

    underlying_df = pd.read_csv(underlying_data, parse_dates = ["date"])
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
            if (option_reverse in options_df["symbol"].values):
                # Checking if the option has an atm couple, adding to dict if there is
                atm_list.append(option_tuple)

    options_df = options_df.set_index("symbol")
    option_expiry_dict = {}
    expiry_set = set()
    for couple in atm_list:
        option1 = couple[0]
        option2 = couple[0]
        expiration_date = options_df.loc[option1]["exdate"]
        delta1 = options_df.loc[option1]["delta"]
        delta2 = options_df.loc[option2]["delta"]
        expiration_time_interval = (expiration_date - date).days
        if (delta1 != np.nan and delta2 != np.nan):
            # TODO: Remove this after delta functionality
            option_expiry_dict[couple] = expiration_time_interval
            expiry_set.add(expiration_time_interval)
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
            
# TODO: Mid market vs worst
# N bid offer spread at closing options
def short_straddle(options_data: str, underlying_data: str, options_dict: dict[tuple[str, str], pd.Timestamp]):

    options_df = pd.read_csv(options_data, parse_dates = ["date"])
    underlying_df = pd.read_csv(underlying_data, parse_dates = ["date"])
    returns_list = [0 for i in options_dict]

    i = 0
    for option_couple in options_dict:

        if (option_couple[0][11] == "C"):
            call_index = 0
            put_index = 1
        else:
            call_index = 1
            put_index = 0

        given_option_df = options_df[options_df['symbol'] == option_couple[call_index]]
        given_option_atm_date_df = given_option_df[given_option_df["date"] == options_dict[option_couple]]
        call_option_atm_series = given_option_atm_date_df

        given_option_df = options_df[options_df['symbol'] == option_couple[put_index]]
        given_option_atm_date_df = given_option_df[given_option_df["date"] == options_dict[option_couple]]
        put_option_atm_series = given_option_atm_date_df

        exec_date = options_dict[option_couple]
        strike_price = int(option_couple[0][12:]) / 1000
        contract_size = call_option_atm_series["contract_size"].item()
        spot_at_expiration = underlying_df[underlying_df["date"] == exec_date]["PRC"].item()

        best_bid_call = call_option_atm_series["best_bid"].item() * 100
        best_bid_put = put_option_atm_series["best_bid"].item() * 100

        if (not math.isclose(best_bid_call, 0) and not math.isclose(best_bid_put, 0)):

            # Selling options
            returns_list[i] += best_bid_call
            returns_list[i] += best_bid_put

            if spot_at_expiration > strike_price or spot_at_expiration < strike_price:
                # One of the options is exercised
                returns_list[i] -= abs((spot_at_expiration - strike_price) * contract_size)

        i += 1

    return returns_list

def long_straddle(options_data: str, underlying_data: str, options_dict: dict[tuple[str, str], pd.Timestamp]):

    options_df = pd.read_csv(options_data, parse_dates = ["date"])
    underlying_df = pd.read_csv(underlying_data, parse_dates = ["date"])
    returns_list = [0 for i in options_dict]

    i = 0
    for option_couple in options_dict:

        if (option_couple[0][11] == "C"):
            call_index = 0
            put_index = 1
        else:
            call_index = 1
            put_index = 0

        given_option_df = options_df[options_df['symbol'] == option_couple[call_index]]
        given_option_atm_date_df = given_option_df[given_option_df["date"] == options_dict[option_couple]]
        call_option_atm_series = given_option_atm_date_df

        given_option_df = options_df[options_df['symbol'] == option_couple[put_index]]
        given_option_atm_date_df = given_option_df[given_option_df["date"] == options_dict[option_couple]]
        put_option_atm_series = given_option_atm_date_df

        exec_date = options_dict[option_couple]
        strike_price = int(option_couple[0][12:]) / 1000
        contract_size = call_option_atm_series["contract_size"].item()
        spot_at_expiration = underlying_df[underlying_df["date"] == exec_date]["PRC"].item()

        best_ask_call = call_option_atm_series["best_offer"].item() * 100
        best_ask_put = put_option_atm_series["best_offer"].item() * 100

        if (not math.isclose(best_ask_call, 0) and not math.isclose(best_ask_put, 0)):

            # Selling options
            returns_list[i] -= best_ask_call
            returns_list[i] -= best_ask_put

            if spot_at_expiration > strike_price or spot_at_expiration < strike_price:
                # One of the options is exercised
                returns_list[i] += abs((spot_at_expiration - strike_price) * contract_size)

        i += 1

    return returns_list


    """
    Gets the number of shares to buy or sell given a list of options, should be from the same issuer and have contract size 100
    
    Args:
        options_df: Pandas dataframe with WRDS options data
        options_list: List of option symbols as str
        date: The date to hedge at

    Returns:
        Number of underlying stocks to buy or sell

    """
def get_hedge_count(options_df: pd.DataFrame, options_list: list[str], date: pd.Timestamp) -> int:

    total_delta = 0
    for option in options_list:
        specific_option_series = options_df[options_df["symbol"] == option]
        option_at_given_time = specific_option_series[options_df["date"] == date]
        option_at_given_time.reset_index(inplace=True)
        delta = option_at_given_time["delta"][0]
        if delta == np.nan:
            # TODO: IMPLEMENT
            pass
        total_delta += delta

    return int(-1 * round(total_delta, 2)  * 100) # TODO: Assumes contract size = 100, ensure this