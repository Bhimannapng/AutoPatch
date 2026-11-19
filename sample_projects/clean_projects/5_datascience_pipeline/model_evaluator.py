from typing import List, Dict
import math

class ModelEvaluator:
    """Computes regression evaluation metrics without nested loops or excessive heap memory."""

    @staticmethod
    def calculate_metrics(y_true: List[float], y_pred: List[float]) -> Dict[str, float]:
        if not y_true or not y_pred or len(y_true) != len(y_pred):
            return {"mse": 0.0, "mae": 0.0, "rmse": 0.0}

        n = len(y_true)
        # Linear O(N) evaluation using generator expressions
        sq_errors = ((yt - yp) ** 2 for yt, yp in zip(y_true, y_pred))
        abs_errors = (abs(yt - yp) for yt, yp in zip(y_true, y_pred))

        mse = sum(sq_errors) / n
        mae = sum(abs_errors) / n
        rmse = math.sqrt(mse)

        return {
            "sample_count": n,
            "mse": round(mse, 4),
            "mae": round(mae, 4),
            "rmse": round(rmse, 4)
        }
