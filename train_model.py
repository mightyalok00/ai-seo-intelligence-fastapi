from pathlib import Path

import pandas as pd
from joblib import dump
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score


BASE_DIR = Path(__file__).resolve().parent
DATA_PATH = BASE_DIR / "data" / "search_intent_keywords.csv"
MODEL_PATH = BASE_DIR / "model" / "intent_model.pkl"


def train():
    """Train and save a small search-intent text-classification model."""
    df = pd.read_csv(DATA_PATH)

    X_train, X_test, y_train, y_test = train_test_split(
        df["keyword"],
        df["intent"],
        test_size=0.25,
        random_state=42,
        stratify=df["intent"],
    )

    model = Pipeline(
        steps=[
            ("tfidf", TfidfVectorizer(ngram_range=(1, 2), lowercase=True)),
            (
                "classifier",
                LogisticRegression(
                    max_iter=1000,
                    random_state=42,
                    solver="liblinear",
                ),
            ),
        ]
    )

    model.fit(X_train, y_train)
    predictions = model.predict(X_test)

    print(f"Accuracy: {accuracy_score(y_test, predictions):.3f}")
    print(classification_report(y_test, predictions))

    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    dump(model, MODEL_PATH)
    print(f"Model saved to: {MODEL_PATH}")


if __name__ == "__main__":
    train()
