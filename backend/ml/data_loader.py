# backend/ml/data_loader.py
import os
import pandas as pd

DATASETS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "datasets"))

def load_task_dataset(task_name, features, target_col):
    """
    Loads train, val, and test splits for a specific ML task.
    """
    csv_path = os.path.join(DATASETS_DIR, f"{task_name}.csv")
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"Dataset for task '{task_name}' not found at {csv_path}")
        
    df = pd.read_csv(csv_path)
    
    # Split by temporal designation
    train_df = df[df["split"] == "train"]
    val_df = df[df["split"] == "val"]
    test_df = df[df["split"] == "test"]
    
    # Fallback to index-based splits if temporal splits are empty (e.g. for small dataset / hotspots)
    if len(train_df) == 0:
        train_df = df.iloc[:int(len(df)*0.7)]
        val_df = df.iloc[int(len(df)*0.7):int(len(df)*0.85)]
        test_df = df.iloc[int(len(df)*0.85):]
        
    # Extract features and targets
    X_train = train_df[features].copy()
    y_train = train_df[target_col].copy()
    
    X_val = val_df[features].copy()
    y_val = val_df[target_col].copy()
    
    X_test = test_df[features].copy()
    y_test = test_df[target_col].copy()
    
    return X_train, y_train, X_val, y_val, X_test, y_test
