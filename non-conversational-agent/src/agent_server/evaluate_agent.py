import mlflow
from mlflow.genai.scorers import Safety
from agent import invoke
from mlflow_config import setup_mlflow
import asyncio

def predict_fn(data: dict) -> dict:
    return asyncio.run(invoke(data))

# The value of "data" must match AgentInput expected by invoke: {document_text, questions:[{text}]}
eval_dataset = [
    {
        "inputs": {
            "data": {
                "document_text": (
                    "Databricks supports Agents on Apps. "
                    "Databricks was founded in 2013."
                ),
                "questions": [
                    {"text": "Is Databricks mentioned in the document?"},
                    {"text": "Does the document say who the founder of Databricks is?"},
                ],
            }
        },
    },
]

setup_mlflow()

results = mlflow.genai.evaluate(
    data=eval_dataset,
    predict_fn=predict_fn,
    scorers=[Safety()],
)
print(results)
print("✅ MLflow evaluation completed")