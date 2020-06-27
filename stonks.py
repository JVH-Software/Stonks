import collections
import os
from datetime import date
from typing import Union

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

        # Create cache
        if self.cache_path:
            os.mkdir(self.cache_path)
            raise NotImplementedError

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
            extension: str = None) -> dict:
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
        # Convert the optional string type into a single item list
        if type(keys) == str:
            keys = [keys]

        # Run get method on each plugin
        stock_data = {}
        for plugin in self.plugins:
            try:
                update_dict(stock_data, plugin.get(keys, start_date, end_date, exchange, symbol, extension))
            except Exception as e:
                print(e)
        return stock_data
