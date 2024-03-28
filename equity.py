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
        cur_date = row["date"]
        stock_price = row["PRC"]
        for j in range(date_start, len(options_df)):
            # Iterating over different options in one date given the stock at that date
            if (options_df["date"][j] < row["date"]):
                 # If past the date for the given stock, break and iterate the stock
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
            

