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

    available_keys = {"Open", "High", "Low", "Close", "Volume", "Dividends", "Stock Splits",
                      "Open Change", "High Change", "Low Change", "Close Change", "Volume Change"}

    def get(self, keys: list, start_date: date, end_date: date, exchange: str, symbol: str,
            extension: str = None) -> Optional[DataFrame]:
        # Return nothing if no specified keys apply to this plugin
        if not self.available_keys.intersection(set(keys)):
            return None

        # Require base value column if change column requested
        open_change = False
        high_change = False
        low_change = False
        close_change = False
        volume_change = False
        if "Open Change" in keys:
            open_change = True
            if "Open" not in keys:
                keys.append("Open")
        if "High Change" in keys and "High" not in keys:
            high_change = True
            if "High" not in keys:
                keys.append("High")
        if "Low Change" in keys and "Low" not in keys:
            low_change = True
            if "Low" not in keys:
                keys.append("Low")
        if "Close Change" in keys and "Close" not in keys:
            close_change = True
            if "Close" not in keys:
                keys.append("Close")
        if "Volume Change" in keys and "Volume" not in keys:
            volume_change = True
            if "Volume" not in keys:
                keys.append("Volume")

        # Get data from Yahoo Finance through yfinance
        stock = yf.Ticker(symbol)
        dataframe = stock.history(start=start_date - timedelta(days=1), end=end_date + timedelta(days=1))

        delta = timedelta(days=1)
        if open_change or high_change or low_change or close_change or volume_change:
            idx = start_date
            while idx <= end_date:
                if open_change:
                    try:
                        prev_value = dataframe.at[idx-delta, "Open"]
                        value = dataframe.at[idx, "Open"]
                        d = DataFrame(index=[idx], data={"Open Change": [value / prev_value]})
                        dataframe = dataframe.combine_first(d)
                    except KeyError:
                        pass
                if high_change:
                    try:
                        prev_value = dataframe.at[idx-delta, "High"]
                        value = dataframe.at[idx, "High"]
                        d = DataFrame(index=[idx], data={"High Change": [value / prev_value]})
                        dataframe = dataframe.combine_first(d)
                    except KeyError:
                        pass
                if low_change:
                    try:
                        prev_value = dataframe.at[idx-delta, "Low"]
                        value = dataframe.at[idx, "Low"]
                        d = DataFrame(index=[idx], data={"Low Change": [value / prev_value]})
                        dataframe = dataframe.combine_first(d)
                    except KeyError:
                        pass
                if close_change:
                    try:
                        prev_value = dataframe.at[idx-delta, "Close"]
                        value = dataframe.at[idx, "Close"]
                        d = DataFrame(index=[idx], data={"Close Change": [value / prev_value]})
                        dataframe = dataframe.combine_first(d)
                    except KeyError:
                        pass
                if volume_change:
                    try:
                        prev_value = dataframe.at[idx-delta, "Volume"]
                        value = dataframe.at[idx, "Volume"]
                        d = DataFrame(index=[idx], data={"Volume Change": [value / prev_value]})
                        dataframe = dataframe.combine_first(d)
                    except KeyError:
                        pass

                idx += delta

        return dataframe


class GoogleTrendsPlugin(Plugin):
    """
    Stonks plugin for Google Trends.

    Keys:
        Monthly Relative Interest

        Annual Relative Interest

        Monthly Relative Interest To S&P

        Annual Relative Interest To S&P
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
