from data_loader import DataLoader
from model_evaluator import ModelEvaluator

SAMPLE_DATA = """feature_1,feature_2,target
1.2,3.4,12.5
2.1,1.8,14.2
3.0,4.1,18.9
4.5,2.9,22.1
5.2,5.0,28.4
"""

def run_pipeline():
    # Stream dataset via generator
    dataset = list(DataLoader.stream_dataset(SAMPLE_DATA))
    
    # Linear model prediction: y_pred = 3.0 * f1 + 2.0 * f2
    y_true = [row["target"] for row in dataset]
    y_pred = [3.0 * row["feature_1"] + 2.0 * row["feature_2"] for row in dataset]

    metrics = ModelEvaluator.calculate_metrics(y_true, y_pred)
    print("Pipeline Execution Completed Successfully.")
    print(f"Evaluated {metrics['sample_count']} samples:")
    print(f"  MSE: {metrics['mse']}")
    print(f"  MAE: {metrics['mae']}")
    print(f"  RMSE: {metrics['rmse']}")
    return metrics

if __name__ == "__main__":
    run_pipeline()
