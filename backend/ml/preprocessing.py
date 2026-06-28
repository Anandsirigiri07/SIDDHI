# backend/ml/preprocessing.py
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer

class MLPreprocessor:
    def __init__(self):
        self.imputer = SimpleImputer(strategy="median")
        self.scaler = StandardScaler()
        
    def fit(self, X):
        self.imputer.fit(X)
        X_imputed = self.imputer.transform(X)
        self.scaler.fit(X_imputed)
        return self
        
    def transform(self, X):
        X_imputed = self.imputer.transform(X)
        X_scaled = self.scaler.transform(X_imputed)
        if isinstance(X, pd.DataFrame):
            return pd.DataFrame(X_scaled, columns=X.columns, index=X.index)
        return X_scaled
        
    def fit_transform(self, X):
        self.fit(X)
        return self.transform(X)
