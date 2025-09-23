import mlflow
from mlflow.genai.scorers import RelevanceToQuery, Safety
from agent import predict 


eval_dataset = [
    {
        "inputs": {
            "request": {
                "input": [{"role": "user", "content": "Calculate the 15th Fibonacci number"}]
            }
        },
        "expected_response": "The 15th Fibonacci number is 610.",
    }
]


results = mlflow.genai.evaluate(
    data=eval_dataset,
    predict_fn=predict,  # pass your agent's @invoke function directly
    scorers=[RelevanceToQuery(), Safety()],
)
print(results)
print("✅ MLflow evaluation completed")