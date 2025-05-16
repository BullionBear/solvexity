from abc import ABC, abstractmethod
from typing import Union
from enum import Enum
import pandas as pd
import numpy as np

class Action(Enum):
    """
    Enum to represent possible actions in a strategy.
    """
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"

class ConditionalDistribution(ABC):
    """
    Abstract base class for probability distributions.
    Subclasses must implement the required methods to support basic statistical functions.
    """
    def __init__(self, x_columns: list[str]):
        """
        Initialize the distribution with a list of x_columns.
        :param x_columns: List of feature names (x_columns).
        """
        self.x_columns = x_columns

    @property
    def x_columns(self) -> list[str]:
        """
        Get the list of x_columns.
        :return: List of x_columns.
        """
        return self.x_columns

    @abstractmethod
    def mean(self, x: Union[pd.DataFrame, np.array]) -> float:
        """Calculate the mean of the distribution."""
        pass


    @abstractmethod
    def quantile(self, x: Union[pd.DataFrame, np.array], q: float) -> Union[pd.DataFrame, np.array]:
        """
        Calculate the quantile(s) of the distribution.
        :param q: A single quantile (float) or a list of quantiles (List[float]).
        :return: The quantile value(s).
        """
        pass


class Agent(ABC):
    """
    Abstract base class for strategies that operate on a probability distribution.
    Subclasses must implement the required methods to define the strategy logic.
    """

    def __init__(self, distribution: ConditionalDistribution):
        """
        Initialize the strategy with a given distribution.
        :param distribution: An instance of a Distribution subclass.
        """
        self.distribution: ConditionalDistribution = distribution

    @property
    def x_columns(self) -> list[str]:
        """
        Get the list of x_columns from the distribution.
        :return: List of x_columns.
        """
        return self.distribution.x_columns

    @abstractmethod
    def act(self, x: Union[pd.DataFrame, np.array]) -> Action:
        """
        Execute the strategy logic.
        :param args: Positional arguments for the strategy.
        :param kwargs: Keyword arguments for the strategy.
        :return: The result of the strategy execution.
        """
        pass


