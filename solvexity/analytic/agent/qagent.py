import joblib
import numpy as np
import pandas as pd
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import QuantileRegressor
from sklearn.preprocessing import PolynomialFeatures
from sklearn.decomposition import PCA

def generate_quantile_pipeline(q: float) -> Pipeline:
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


class QuantileAgent:
    def __init__(self, pipeline: Pipeline):
        self.pipeline = pipeline
        self.x_columns = ['returns_1m_30', 'volatility_1m_30', 'mdd_1m_30',
            'skewness_1m_30', 'kurtosis_1m_30', 'returns_1m_180',
            'volatility_1m_180', 'mdd_1m_180', 'skewness_1m_180', 'kurtosis_1m_180',
            'returns_5m_30', 'volatility_5m_30', 'mdd_5m_30', 'skewness_5m_30',
            'kurtosis_5m_30', 'returns_5m_180', 'volatility_5m_180', 'mdd_5m_180',
            'skewness_5m_180', 'kurtosis_5m_180', 'returns_15m_30',
            'volatility_15m_30', 'mdd_15m_30', 'skewness_15m_30', 'kurtosis_15m_30',
            'returns_15m_180', 'volatility_15m_180', 'mdd_15m_180',
            'skewness_15m_180', 'kurtosis_15m_180', 'returns_1h_30',
            'volatility_1h_30', 'mdd_1h_30', 'skewness_1h_30', 'kurtosis_1h_30',
            'returns_1h_180', 'volatility_1h_180', 'mdd_1h_180', 'skewness_1h_180',
            'kurtosis_1h_180']
        
    def predict(self, x: pd.DataFrame) -> np.array:
        # Ensure the input DataFrame has the correct columns
        if not all(col in x.columns for col in self.x_columns):
            raise ValueError(f"Input DataFrame must contain the following columns: {self.x_columns}")
        # Ensure the input DataFrame has the correct shape
        if x.shape[1] != len(self.x_columns):
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