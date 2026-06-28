# backend/ml/models/crime_classifier.py
import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.neighbors import KNeighborsClassifier
from sklearn.preprocessing import LabelEncoder
from backend.ml.utils.serialization import save_model_artifact
from backend.ml.model_registry import register_model

FEATURES = ["BriefFacts"]
TARGETS = ["crime_head", "crime_subhead"]

def train_crime_classifier(X_train, y_train_head, y_train_sub, X_val, y_val_head, y_val_sub, X_test, y_test_head, y_test_sub, test_df):
    print("Training Crime Classifier models (TF-IDF + KNN)...")
    
    # 1. Fill missing values
    X_train_clean = X_train.fillna("No incident details available.")
    X_val_clean = X_val.fillna("No incident details available.")
    X_test_clean = X_test.fillna("No incident details available.")
    
    # 2. Extract TF-IDF embeddings
    vectorizer = TfidfVectorizer(max_features=2000, stop_words="english", ngram_range=(1, 2))
    X_train_tfidf = vectorizer.fit_transform(X_train_clean)
    X_val_tfidf = vectorizer.transform(X_val_clean)
    X_test_tfidf = vectorizer.transform(X_test_clean)
    
    # 3. Label encode targets
    le_head = LabelEncoder()
    y_train_head_enc = le_head.fit_transform(y_train_head)
    y_val_head_enc = le_head.transform(y_val_head)
    y_test_head_enc = le_head.transform(y_test_head)
    
    le_sub = LabelEncoder()
    y_train_sub_enc = le_sub.fit_transform(y_train_sub)
    
    # Handle unseen labels in val/test safely
    def transform_safe(le, labels):
        classes = set(le.classes_)
        # map unseen to first class index (usually 0)
        return np.array([le.transform([l])[0] if l in classes else 0 for l in labels])
        
    y_val_sub_enc = transform_safe(le_sub, y_val_sub)
    y_test_sub_enc = transform_safe(le_sub, y_test_sub)
    
    # 4. Train KNN classifiers
    knn_head = KNeighborsClassifier(n_neighbors=5, weights="distance")
    knn_head.fit(X_train_tfidf, y_train_head_enc)
    
    knn_sub = KNeighborsClassifier(n_neighbors=5, weights="distance")
    knn_sub.fit(X_train_tfidf, y_train_sub_enc)
    
    # 5. Evaluate accuracies
    # Top-1 Accuracy
    preds_test_head_enc = knn_head.predict(X_test_tfidf)
    acc_top1 = float(np.mean(preds_test_head_enc == y_test_head_enc))
    
    # Top-3 Accuracy
    probs_test_head = knn_head.predict_proba(X_test_tfidf)
    top3_correct = 0
    for idx, row_prob in enumerate(probs_test_head):
        top3_classes = np.argsort(row_prob)[-3:]
        if y_test_head_enc[idx] in top3_classes:
            top3_correct += 1
    acc_top3 = float(top3_correct / len(y_test_head_enc)) if len(y_test_head_enc) > 0 else 1.0
    
    print(f"Crime Head Classifier Test metrics: Top-1 Accuracy={acc_top1:.4f}, Top-3 Accuracy={acc_top3:.4f}")
    
    # Store the actual mapping of acts/sections for suggestion fallback
    # Group by head to get most common acts/sections
    suggestion_db = {}
    for head in le_head.classes_:
        sub_df = test_df[test_df["crime_head"] == head]
        if not sub_df.empty:
            acts = sub_df["suggested_acts"].dropna().mode()
            secs = sub_df["suggested_sections"].dropna().mode()
            suggestion_db[head] = {
                "acts": acts.iloc[0] if not acts.empty else "Indian Penal Code",
                "sections": secs.iloc[0] if not secs.empty else "Section 379 IPC"
            }
        else:
            suggestion_db[head] = {
                "acts": "Indian Penal Code",
                "sections": "Section 379 IPC"
            }
            
    # 6. Save model pack
    model_pack = {
        "vectorizer": vectorizer,
        "knn_head": knn_head,
        "knn_sub": knn_sub,
        "le_head": le_head,
        "le_sub": le_sub,
        "suggestion_db": suggestion_db,
        "algorithm": "TFIDF + KNN"
    }
    
    metadata = {
        "algorithm": "TFIDF + KNN",
        "features": FEATURES,
        "targets": TARGETS,
        "train_size": len(X_train),
        "val_size": len(X_val),
        "test_size": len(X_test),
        "metrics": {
            "test": {
                "top_1_accuracy": acc_top1,
                "top_3_accuracy": acc_top3
            }
        }
    }
    
    save_model_artifact(model_pack, "crime_classifier", metadata)
    register_model("crime_classifier", metadata)
    
    return "TFIDF + KNN", metadata["metrics"]["test"]
