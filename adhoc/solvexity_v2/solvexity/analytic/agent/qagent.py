import joblib
import numpy as np
import pandas as pd
import decimal
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import QuantileRegressor
from sklearn.preprocessing import PolynomialFeatures
from sklearn.decomposition import PCA
from .core import Agent, ConditionalDistribution


def generate_quantile_pipeline(q: decimal.Decimal) -> Pipeline:
    """
    Generate a pipeline for quantile regression.
    :param q: Quantile to be predicted (between 0 and 1).
    :return: A sklearn Pipeline object.
    """
    return Pipeline([
        ('imputer', SimpleImputer(strategy='mean')),
        ('scaler', StandardScaler()),
        ('poly', PolynomialFeatures(degree=2)),
        ('pca', PCA(n_components=0.95)),
        ('quantile', QuantileRegressor(quantile=q))
    ])


class QuantileConditionalDistribution(ConditionalDistribution):
    def __init__(self, pipelines: dict[decimal.Decimal, Pipeline], x_columns: list[str]):
        self.pipelines = pipelines
        assert len(pipelines) > 1, "At least two pipelines are required"
        self.x_columns = x_columns
    
    def mean(self, x: pd.DataFrame) -> float:
        quantiles = sorted(list(self.pipelines.keys()))
        m = 0
        for q_prev, q in zip(quantiles[:-1], quantiles[1:]):
            m += (self.quantile(x, q_prev) + self.quantile(x, q)) * (q - q_prev) / 2
        return m
    
    def quantile(self, x: pd.DataFrame, q: decimal.Decimal) -> float:
        return self.pipeline.predict(x[self.x_columns], q)


class QuantileAgent(Agent):
    def __init__(self, distribution: QuantileConditionalDistribution):
        self.distribution = distribution
        
    def act(self, x: pd.DataFrame) -> np.array:
        # Ensure the input DataFrame has the correct columns
        if not all(col in x.columns for col in self.distribution.x_columns):
            raise ValueError(f"Input DataFrame must contain the following columns: {self.distribution.x_columns}")
        # Ensure the input DataFrame has the correct shape
        if x.shape[1] != len(self.distribution.x_columns):
            raise ValueError(f"Input DataFrame must have {len(self.x_columns)} columns, got {x.shape[1]}")
        # Predict using the pipeline
        return self.pipeline.predict(x[self.x_columns])
    
    @classmethod
    def load(cls, path: str):
        pipeline = joblib.load(path)
        if not isinstance(pipeline, Pipeline):
            raise ValueError(f"Expected a sklearn Pipeline, got {type(pipeline)}")
        # Check if the pipeline has the expected steps
        expected_steps = {
            'imputer': SimpleImputer,
            'scaler': StandardScaler,
            'poly': PolynomialFeatures,
            'pca': PCA,
            'quantile': QuantileRegressor
        }
        for name, step in expected_steps.items():
            if name not in pipeline.named_steps:
                raise ValueError(f"Pipeline is missing expected step: {name}")
            if not isinstance(pipeline.named_steps[name], step):
                raise ValueError(f"Expected step '{name}' to be of type {step}, got {type(pipeline.named_steps[name])}")
        # checksum 
        test_data = pd.DataFrame({col: 1.0 for col in cls.x_columns})
        checksum = pipeline.predict(test_data)
        assert abs(checksum - 6.37927929) < 1e-9, f"Checksum failed: {checksum}"
        return cls(pipeline)