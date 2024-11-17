from .moving_average import MovingAverageSignal

class SignalFactory:
    def __init__(self, trade_context, signal_config: dict):
        self.trade_context = trade_context
        self.signal_config = signal_config

    def __getitem__(self, signal_name: str):
        return self.get_signal(signal_name)

    def get_signal(self, signal_name: str):
        if signal_name == "ma":
            return MovingAverageSignal(
                self.trade_context,
                **self.signal_config["ma"]
            )
        else:
            raise ValueError(f"Unknown signal: {signal_name}")
