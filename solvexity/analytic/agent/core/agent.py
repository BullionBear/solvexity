from abc import ABC, abstractmethod
from typing import Union, List, Any
from enum import Enum
import numpy as np

class Action(Enum):
    """
    Enum to represent possible actions in a strategy.
    """
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"

class Distribution(ABC):
    """
    Abstract base class for probability distributions.
    Subclasses must implement the required methods to support basic statistical functions.
    """

    @abstractmethod
    def mean(self) -> float:
        """Calculate the mean of the distribution."""
        pass

    @abstractmethod
    def median(self) -> float:
        """Calculate the median of the distribution."""
        pass

    @abstractmethod
    def quantile(self, q: Union[float, List[float]]) -> Union[float, List[float]]:
        """
        Calculate the quantile(s) of the distribution.
        :param q: A single quantile (float) or a list of quantiles (List[float]).
        :return: The quantile value(s).
        """
        pass

    @abstractmethod
    def variance(self) -> float:
        """Calculate the variance of the distribution."""
        pass

    @abstractmethod
    def sample(self, size: int = 1) -> np.ndarray:
        """
        Generate random samples from the distribution.
        :param size: Number of samples to generate.
        :return: An array of samples.
        """
        pass

    @abstractmethod
    def pdf(self, x: float) -> float:
        """
        Calculate the probability density function (PDF) at a given point.
        :param x: The point at which to evaluate the PDF.
        :return: The PDF value.
        """
        pass

    @abstractmethod
    def cdf(self, x: float) -> float:
        """
        Calculate the cumulative distribution function (CDF) at a given point.
        :param x: The point at which to evaluate the CDF.
        :return: The CDF value.
        """
        pass


class Strategy(ABC):
    """
    Abstract base class for strategies that operate on a probability distribution.
    Subclasses must implement the required methods to define the strategy logic.
    """

    def __init__(self, distribution: Distribution):
        """
        Initialize the strategy with a given distribution.
        :param distribution: An instance of a Distribution subclass.
        """
        self.distribution = distribution

    @abstractmethod
    def execute(self, *args, **kwargs) -> Action:
        """
        Execute the strategy logic.
        :param args: Positional arguments for the strategy.
        :param kwargs: Keyword arguments for the strategy.
        :return: The result of the strategy execution.
        """
        pass

    @abstractmethod
    def evaluate(self) -> float:
        """
        Evaluate the performance or outcome of the strategy.
        :return: A numerical value representing the evaluation result.
        """
        pass

