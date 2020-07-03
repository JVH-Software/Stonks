import math
import re
from typing import Optional

from bs4 import BeautifulSoup
import dateutil
import requests
import yfinance as yf
from pytrends.request import TrendReq
from datetime import date, timedelta, datetime

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


class MacrotrendsPlugin(Plugin):
    """
    Stonks plugin for Macrotrends historical finance data.

    Keys:
        Shares: Number of shares outstanding

        EPS: Earnings per share.

        D/E: Debt / equity ratio

        FCFPS: Free cash flow per share

        Current Ratio: Current ratio

        Quick Ratio: Quick ratio

        ROE: Return on equity

        ROA: Return on assets

        ROI: Return on investments

    """

    available_keys = {"Shares", "EPS", "D/E", "FCFPS", "Current Ratio", "Quick Ratio", "ROE", "ROA", "ROI"}

    def get(self, keys: list, start_date: date, end_date: date, exchange: str, symbol: str,
            extension: str = None) -> Optional[DataFrame]:
        # Return nothing if no specified keys apply to this plugin
        if not self.available_keys.intersection(set(keys)):
            return None

        # Get URL
        url = f"https://www.macrotrends.net/stocks/charts/{symbol}/"
        response = requests.get(url, allow_redirects=False)
        if response.status_code == 301:
            url = response.headers["Location"]

        dataframe = DataFrame()

        if "Shares" in keys:
            response = requests.get(url + "shares-outstanding")
            if response:
                soup = BeautifulSoup(response.text, "lxml")
                table = soup.findAll("table", class_="historical_data_table table")[1]
                dataframe = dataframe.combine_first(self._convert_table_to_dataframe(table, "Shares"))

        if "EPS" in keys:
            response = requests.get(url + "eps-earnings-per-share-diluted")
            if response:
                soup = BeautifulSoup(response.text, "lxml")
                table = soup.findAll("table", class_="historical_data_table table")[1]
                dataframe = dataframe.combine_first(self._convert_table_to_dataframe(table, "EPS"))

        if "D/E" in keys:
            response = requests.get(url + "debt-equity-ratio")
            if response:
                soup = BeautifulSoup(response.text, "lxml")
                table = soup.findAll("table")[0]
                dataframe = dataframe.combine_first(self._convert_table_to_dataframe(table, "D/E", 3))

        if "FCFPS" in keys:
            response = requests.get(url + "price-fcf")
            if response:
                soup = BeautifulSoup(response.text, "lxml")
                table = soup.findAll("table")[0]
                dataframe = dataframe.combine_first(self._convert_table_to_dataframe(table, "FCFPS", 2))

        if "Current Ratio" in keys:
            response = requests.get(url + "current-ratio")
            if response:
                soup = BeautifulSoup(response.text, "lxml")
                table = soup.findAll("table")[0]
                dataframe = dataframe.combine_first(self._convert_table_to_dataframe(table, "Current Ratio", 3))

        if "Quick Ratio" in keys:
            response = requests.get(url + "quick-ratio")
            if response:
                soup = BeautifulSoup(response.text, "lxml")
                table = soup.findAll("table")[0]
                dataframe = dataframe.combine_first(self._convert_table_to_dataframe(table, "Quick Ratio", 3))

        if "ROE" in keys:
            response = requests.get(url + "roe")
            if response:
                soup = BeautifulSoup(response.text, "lxml")
                table = soup.findAll("table")[0]
                dataframe = dataframe.combine_first(self._convert_table_to_dataframe(table, "ROE", 3))

        if "ROA" in keys:
            response = requests.get(url + "roa")
            if response:
                soup = BeautifulSoup(response.text, "lxml")
                table = soup.findAll("table")[0]
                dataframe = dataframe.combine_first(self._convert_table_to_dataframe(table, "ROA", 3))

        if "ROI" in keys:
            response = requests.get(url + "roi")
            if response:
                soup = BeautifulSoup(response.text, "lxml")
                table = soup.findAll("table")[0]
                dataframe = dataframe.combine_first(self._convert_table_to_dataframe(table, "ROI", 3))

        return dataframe

    @staticmethod
    def _convert_table_to_dataframe(table, column_name: str, cell_idx: int = 1) -> DataFrame:
        data = {column_name: []}
        index = []
        for row in table.tbody.find_all("tr"):
            cells = row.find_all("td")
            if cells is not None:

                cell_str = cells[cell_idx].text
                try:
                    cell_float = float(cell_str.replace("$", "").replace("%", "").strip())
                except ValueError:
                    print(f"Failed to convert {cell_str} to float from {cells}.")
                    continue

                index.append(datetime.strptime(cells[0].text, "%Y-%m-%d").date())
                if "%" in cell_str:
                    cell_float = cell_float / 100
                data[column_name].append(cell_float)

        return DataFrame(index=index, data=data)
