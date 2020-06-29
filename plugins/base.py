import math
from typing import Optional

import dateutil
import yfinance as yf
from pytrends.request import TrendReq
from datetime import date, timedelta

from pandas import DataFrame

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
            extension: str = None) -> Optional[DataFrame]:
        # Return nothing if no specified keys apply to this plugin
        if not self.available_keys.intersection(set(keys)):
            return None

        # Get data from Yahoo Finance through yfinance
        stock = yf.Ticker(symbol)
        dataframe = stock.history(start=start_date, end=end_date + timedelta(days=1))

        return dataframe


class GoogleTrendsPlugin(Plugin):
    """
    Stonks plugin for Google Trends.

    Keys:
        Monthly Relative Interest: Google Trends Interest value relative to the past 30 days.

        Annual Relative Interest: Google Trends Interest value relative to the past 365 days.

        Monthly Relative Interest To S&P: Google Trends Interest value relative to "S&P" Interest value within the past
        30 days.

        Annual Relative Interest To S&P: Google Trends Interest value relative to "S&P" Interest value within the past
        365 days.
    """

    available_keys = {"Monthly Relative Interest", "Annual Relative Interest", "Monthly Relative Interest To S&P",
                      "Annual Relative Interest To S&P"}

    def get(self, keys: list, start_date: date, end_date: date, exchange: str, symbol: str,
            extension: str = None) -> Optional[DataFrame]:

        # Return nothing if no specified keys apply to this plugin
        if not self.available_keys.intersection(set(keys)):
            return None

        # Get data from Google Trends through pytrends
        pytrends = TrendReq(hl='en-US', tz=360)

        dataframe = DataFrame()

        day_delta = timedelta(days=1)
        month_delta = timedelta(days=30)
        year_delta = timedelta(days=365)
        keywords_no_sp = [symbol]
        keywords_with_sp = [symbol, "S&P"]

        if "Monthly Relative Interest" in keys:
            idx = start_date
            while idx <= end_date:
                pytrends.build_payload(keywords_no_sp, cat=0, timeframe=f"{idx - month_delta} {idx}", geo='US')
                trend_data = pytrends.interest_over_time()
                if not trend_data.at[idx, 'isPartial']:
                    value = trend_data.at[idx, symbol]
                    d = DataFrame(index=[idx], data={"Monthly Relative Interest": [value/100]})
                    dataframe = dataframe.combine_first(d)

                idx += day_delta
        if "Annual Relative Interest" in keys:
            idx = start_date
            while idx <= end_date:
                pytrends.build_payload(keywords_no_sp, cat=0, timeframe=f"{idx - year_delta} {idx}", geo='US')
                trend_data = pytrends.interest_over_time()
                if not trend_data.at[idx, 'isPartial']:
                    value = trend_data.at[idx, symbol]
                    d = DataFrame(index=[idx], data={"Annual Relative Interest": [value/100]})
                    dataframe = dataframe.combine_first(d)

                idx += day_delta
        if "Monthly Relative Interest To S&P" in keys:
            idx = start_date
            while idx <= end_date:
                pytrends.build_payload(keywords_with_sp, cat=0, timeframe=f"{idx - month_delta} {idx}", geo='US')
                trend_data = pytrends.interest_over_time()
                if not trend_data.at[idx, 'isPartial']:
                    relative_value = float(trend_data.at[idx, symbol]) / float(trend_data.at[idx, "S&P"])
                    d = DataFrame(index=[idx], data={"Monthly Relative Interest To S&P": [relative_value]})
                    dataframe = dataframe.combine_first(d)

                idx += day_delta
        if "Annual Relative Interest To S&P" in keys:
            idx = start_date
            while idx <= end_date:
                pytrends.build_payload(keywords_with_sp, cat=0, timeframe=f"{idx - year_delta} {idx}", geo='US')
                trend_data = pytrends.interest_over_time()
                if not trend_data.at[idx, 'isPartial']:
                    relative_value = float(trend_data.at[idx, symbol]) / float(trend_data.at[idx, "S&P"])
                    d = DataFrame(index=[idx], data={"Annual Relative Interest To S&P": [relative_value]})
                    dataframe = dataframe.combine_first(d)

                idx += day_delta

        return dataframe
