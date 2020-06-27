import yfinance as yf
from datetime import date, timedelta

from plugin import Plugin


class YahooFinancePlugin(Plugin):
    """
    Stonks plugin for Yahoo Finance Data.

    Keys:
        Open: Opening price

        High: Highest price

        Low: Lowest price

        Close: Closing price

        Volume: Trading volume

        Dividends: Dividends paid

        Stock Splits: Stock splits
    """

    available_keys = {"Open", "High", "Low", "Close", "Volume", "Dividends", "Stock Splits"}

    def get(self, keys: list, start_date: date, end_date: date, exchange: str, symbol: str,
            extension: str = None) -> dict:

        # Return nothing if no specified keys apply to this plugin
        if not self.available_keys.intersection(set(keys)):
            return {}

        # Get data from Yahoo Finance through yfinance
        stock = yf.Ticker(symbol)
        dataframe = stock.history(start=start_date, end=end_date + timedelta(days=1))

        # Convert index to default date string format
        idx_list = dataframe.index.tolist()
        for i in range(len(idx_list)):
            idx_list[i] = str(idx_list[i].date())
        dataframe.index = idx_list

        # Drop any columns that were not specified in the request
        drop_labels = (set(keys) ^ self.available_keys) & self.available_keys
        dataframe = dataframe.drop(columns=drop_labels)

        # Convert to expected dictionary format
        return dataframe.T.to_dict()
