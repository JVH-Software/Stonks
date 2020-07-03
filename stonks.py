import collections
import json
import os
from datetime import date, timedelta
from typing import Union, Optional

import numpy
from pandas import read_pickle, DataFrame, date_range

from plugin import Plugin
from plugins import *  # This is required to load all plugins dynamically


def update_dict(d, u):
    """
    A utility function that recursively updates a dictionary.

    Args:
        d: dictionary to update
        u: new/updated data

    Returns:
        The updated dictionary
    """
    for k, v in u.items():
        if isinstance(v, collections.abc.Mapping):
            d[k] = update_dict(d.get(k, {}), v)
        else:
            d[k] = v
    return d


class Stonks:
    """
    A python package for accessing historical stock data.

    Args:
        cache_path: Optional. File path to cache directory. Will not cache data if set to None. Defaults to None.
        specified_plugins: Optional. Specifies which plugins to specifically include/exclude if set. Defaults to None.
        whitelist: Specifies whether the plugins argument is to be used as a whitelist (include), or a blacklist
        (exclude). Defaults to False.

    Attributes:
        cache_path: File path to cache directory.
        plugins: Active plugins to use.
    """

    def __init__(self, cache_path: str = None, specified_plugins: list = [], whitelist: bool = False):
        self.cache_path = cache_path

        # Load plugins
        self.plugins = []
        for plugin in Plugin.__subclasses__():
            print(plugin.__name__)
            if whitelist and plugin.__name__ in specified_plugins:
                self.plugins.append(plugin())
            elif not whitelist and plugin.__name__ not in specified_plugins:
                self.plugins.append(plugin())
        self.plugins.sort()

    def get(self, keys: Union[list, str], start_date: date, end_date: date, exchange: str, symbol: str,
            extension: str = None) -> Optional[DataFrame]:
        """
        Args:
            keys: The kind of data requested. Ex: ["close", "open", "volume"]
            start_date: The starting date of the requested data. Inclusive. start_date <= end_date
            end_date: The ending date of the requested data. Inclusive. end_date => start_date
            exchange: The stock exchange symbol. Ex: "NYSE" from "NYSE:BRK.A".
            symbol: The stock symbol. Ex: "BRK" from "NYSE:BRK.A".
            extension: Optional. The behind-the-dot extension. Ex: "A" from "NYSE:BRK.A". Defaults to None.
        Returns:
            A nested dictionary containing the requested data in the form {"YYYY-MM-DD": {"KEY": "VALUE"}}.
        """
        stock_data = DataFrame()

        # Convert the optional string type into a single item list
        if type(keys) == str:
            keys = [keys]

        # Load cache or create path it if it doesn't exist
        file_path = None
        if self.cache_path:
            if extension:
                file_path = os.path.join(self.cache_path, exchange, symbol + "." + extension)
            else:
                file_path = os.path.join(self.cache_path, exchange, symbol)
            if os.path.exists(file_path):
                stock_data = read_pickle(file_path)
                stock_data = conform_dataframe_rows(stock_data, start_date, end_date)
            elif not os.path.exists(os.path.dirname(file_path)):
                os.makedirs(os.path.dirname(file_path))

        print(stock_data.columns)
        print(stock_data)

        # Determine if cache is missing any keys
        missing_keys = []
        idx = start_date
        delta = timedelta(days=1)
        # Check for missing dates (all keys missing)
        while idx <= end_date:
            if numpy.datetime64(idx) not in stock_data.index:
                print(f"Missing date {idx}.")
                missing_keys = keys.copy()
                break
            idx += delta
        # Check for null values in the columns
        for null_column in stock_data.columns[stock_data.isna().any()]:
            if null_column not in missing_keys and null_column in keys:
                print(f"Null values in {null_column}.")
                missing_keys.append(null_column)
        # Check for missing columns
        for key in keys:
            if key not in stock_data.columns and key not in missing_keys:
                print(f"Column {key} does not exist.")
                missing_keys.append(key)

        # Run get method on each plugin
        if missing_keys is not None:
            print(f"Missing keys: {missing_keys}")
            for plugin in self.plugins:
                print(f"Executing plugin {plugin.__class__.__name__}")
                new_data = None
                try:
                    new_data = plugin.get(missing_keys, start_date, end_date, exchange, symbol, extension)
                except Exception as e:
                    print(type(e))
                    print(e)
                if new_data is not None:
                    print(f"New Data: {new_data}")
                    stock_data = stock_data.combine_first(new_data)

        # Store data in cache
        if file_path:
            stock_data.to_pickle(file_path)

        # Remove any unrequested columns or rows
        stock_data = conform_dataframe(stock_data, keys, start_date, end_date)

        return stock_data


def conform_dataframe_columns(dataframe: DataFrame, keys: list) -> DataFrame:
    # Drop any columns that were not specified in the request
    drop_keys = set(dataframe.columns.values) - set(keys)
    return dataframe.drop(columns=drop_keys)


def conform_dataframe_rows(dataframe: DataFrame, start_date: date, end_date: date) -> DataFrame:
    # Get only rows that are within the time range
    mask = (dataframe.index >= numpy.datetime64(start_date)) & (dataframe.index <= numpy.datetime64(end_date))
    return dataframe.loc[mask]


def conform_dataframe(dataframe: DataFrame, keys: list, start_date: date, end_date: date) -> DataFrame:
    return conform_dataframe_columns(conform_dataframe_rows(dataframe, start_date, end_date), keys)