import pandas as pd

class Pattern:

    @staticmethod
    def recognize(method: str, df: pd.DataFrame) -> dict[str, float]:
        return {method: Pattern._recognize(method, df)}

    @staticmethod
    def _recognize(method: str, df: pd.DataFrame) -> float:
        if method == "support":
            return Pattern.support(df)
        elif method == "resistance":
            return Pattern.resistance(df)
        else:
            raise ValueError(f"Method {method} not supported")
        
    @staticmethod
    def support(df: pd.DataFrame) -> float:

        pass

    @staticmethod
    def resistance(df: pd.DataFrame) -> float:
        pass