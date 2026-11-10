"""Register this model with an MLflow tracking server."""

import mlflow, pickle

with open("model/model.pkl", "rb") as fh:
    model = pickle.load(fh)

with mlflow.start_run(run_name="avaloka-0ee49c7e6145"):
    mlflow.sklearn.log_model(model, "model", registered_model_name="high_compute_route")
    mlflow.log_metric("roc_auc", 0.9560400845533548)
