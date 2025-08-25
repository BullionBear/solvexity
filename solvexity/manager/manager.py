from solvexity.agent.agent import Agent
from solvexity.strategy.strategy import Strategy

class StrategyManager:
    def __init__(self, strategy: Strategy, agent: Agent):
        self.strategy: Strategy = strategy
        self.agent: Agent = agent

    def run(self):
        self.strategy.run()
        self.agent.run()