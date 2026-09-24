from pathlib import Path
import joblib


MODEL_PATH = Path(__file__).resolve().parents[2] / "model" / "intent_model.pkl"


class IntentPredictor:
    """Loads the trained scikit-learn pipeline once and serves predictions."""

    def __init__(self):
        self.model = None

    def load(self):
        if not MODEL_PATH.exists():
            raise FileNotFoundError(
                "Intent model is missing. Run: python train_model.py"
            )
        self.model = joblib.load(MODEL_PATH)

    def predict(self, keyword: str):
        if self.model is None:
            self.load()

        prediction = self.model.predict([keyword])[0]
        confidence = 0.0

        if hasattr(self.model, "predict_proba"):
            confidence = float(self.model.predict_proba([keyword]).max())

        return str(prediction), round(confidence, 4)


intent_predictor = IntentPredictor()
