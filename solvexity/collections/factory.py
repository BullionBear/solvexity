from typing import Type
from solvexity.strategy.strategy import Strategy

class StrategyFactory:
    STRATEGIES = {}
    @classmethod
    def register(cls, name: str, strategy: Type[Strategy]):
        cls.STRATEGIES[name] = strategy

    @classmethod
    def create(cls, name: str) -> Strategy:
        return cls.STRATEGIES[name]