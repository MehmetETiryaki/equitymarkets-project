import pandas as pd
import math

def find_atm(options_data: str, underlying_data: str , num_options: int, tol: float) -> dict[tuple[str, str], pd.Timestamp]:
    """
    Finds at-the-money option couples (put and call) for a given issuer, only works with 1 issuer, do not input csv file with more than 1 issuer

    Args:
        options_data (str): csv file from WRDS OptionMetrics database containing options data, 
                            must include "date", "symbol", and "strike_price" columns
        underlying_data (str): csv file from WRDS CRSP database containing stocks data of the underlying stocks for the options,
                               must include "date", "PRC" data
        num_options (int): Number of option couples to find
        tol (float): Relative tolerance for what constitutes at-the-money, for example 0.05 would consider anything +- %5 of the stock price atm

    Returns:
        dict: A dictionary of tuples of option names (put and call in no specific order as str) that maps to the date when they are at-the-money
    """

    # Initializing data
    options_df = pd.read_csv(options_data, parse_dates = ["date"])
    underlying_df = pd.read_csv(underlying_data, parse_dates = ["date"])
    date_start = 0
    atm_dict = {} # Return value
    atm_list = [] # Keeping track of already picked options

    for i, row in underlying_df.iterrows():

        # Iterating over the underlying data date by date
        if (len(atm_dict) >= num_options):
            break
        
        cur_date = row["date"]
        stock_price = row["PRC"]

        for j in range(date_start, len(options_df)):
            # Iterating over different options in one date given the stock at that date
            if (options_df["date"][j] > row["date"]):
                 # If past the date for the given stock, break inner loop and iterate the stock
                 break
            elif (options_df["date"][j] == cur_date):
                # The options to iterate over
                if (math.isclose(stock_price, options_df["strike_price"][j] / 1000, rel_tol=tol)):
                    # At-the-money option
                    option_name = options_df["symbol"][j]
                    option_reverse = reverse_option(option_name) # Couple of the option, put or call with same strike and expiration
                    option_tuple = (option_name, option_reverse)
                    if (option_reverse in options_df["symbol"].values) and (option_tuple not in atm_list):
                        # Checking if the option has an atm couple, adding to dict if there is
                        atm_dict[option_tuple] = cur_date
                        atm_list.append(option_tuple)
                    if (len(atm_dict) >= num_options):
                        break
                date_start += 1 
            else:
                date_start += 1

    return atm_dict

def reverse_option(option_name:str) -> str:
    """
    Finds the couple of an option (put if call, call if put) with same expiration and strike, returns the couple as str

    Args:
        option_name (str): The option to find the couple, should be in WRDS OptionMetrics symbol format, for example "AAPL 190104C120000"

    Returns:
        str: Symbol of the couple of the option 
    """
    if option_name[11] == "C":
        reverse = option_name[:11] + "P" + option_name[12:]
    else:
        reverse = option_name[:11] + "C" + option_name[12:]
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
