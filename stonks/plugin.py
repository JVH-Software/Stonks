from abc import abstractmethod, ABC
from datetime import date
from functools import total_ordering
from typing import Optional

from pandas import DataFrame


@total_ordering
class Plugin(ABC):
    # temp fix for PyCharm bug: https://youtrack.jetbrains.com/issue/PY-16760
    # noinspection PyUnresolvedReferences
    """
    The base plugin class for all Stonks plugins.

    Attributes:
        priority: The priority of a plugin determines which value will be returned in case of a key conflict where the
        higher value priority wins.
    """

    priority: int = 0

    @abstractmethod
    def get(self, keys: list, start_date: date, end_date: date, exchange: str, symbol: str,
            extension: str = None) -> Optional[DataFrame]:
        """
        Args:
            keys: The kind of data requested. Plugin should ignore any unexpected keys. Ex: ["close", "open", "volume"]
            start_date: The starting date of the requested data. Inclusive. start_date <= end_date
            end_date: The ending date of the requested data. Inclusive. end_date => start_date
            exchange: The stock exchange symbol. Ex: "NYSE" from "NYSE:BRK.A".
            symbol: The stock symbol. Ex: "BRK" from "NYSE:BRK.A".
            extension: Optional. The behind-the-dot extension. Ex: "A" from "NYSE:BRK.A". Defaults to None.
        Returns:
            A DataFrame with a date index and keys as the column labels.
        """

    def __eq__(self, other):
        if issubclass(other.__class__, Plugin):
            return self.priority == other.priority
        else:
            raise TypeError(f"Expected type: Plugin. Found: {type(other)}")

    def __lt__(self, other):
        if issubclass(other.__class__, Plugin):
            return self.priority < other.priority
        else:
            raise TypeError(f"Expected type: Plugin. Found: {type(other)}")
