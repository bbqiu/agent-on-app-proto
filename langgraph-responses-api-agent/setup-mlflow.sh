#!/bin/bash
set -e

echo "Setting up MLflow experiment and configuration files..."

# Copy .env.example to .env.local
echo "Copying .env.example to .env.local..."
cp .env.example .env.local
echo

# Get current Databricks username
echo "Getting Databricks username..."
DATABRICKS_USERNAME=$(databricks current-user me | jq -r .userName)
echo "Username: $DATABRICKS_USERNAME"
echo

# Create MLflow experiment and capture the experiment ID
echo "Creating MLflow experiment..."
EXPERIMENT_NAME="/Users/$DATABRICKS_USERNAME/agents-on-apps"

# Try to create the experiment with the default name first
if EXPERIMENT_RESPONSE=$(databricks experiments create-experiment $EXPERIMENT_NAME 2>/dev/null); then
    EXPERIMENT_ID=$(echo $EXPERIMENT_RESPONSE | jq -r .experiment_id)
    echo "Created experiment '$EXPERIMENT_NAME' with ID: $EXPERIMENT_ID"
else
    echo "Experiment name already exists, creating with random suffix..."
    RANDOM_SUFFIX=$(openssl rand -hex 4)
    EXPERIMENT_NAME="/Users/$DATABRICKS_USERNAME/agents-on-apps-$RANDOM_SUFFIX"
    EXPERIMENT_RESPONSE=$(databricks experiments create-experiment $EXPERIMENT_NAME)
    EXPERIMENT_ID=$(echo $EXPERIMENT_RESPONSE | jq -r .experiment_id)
    echo "Created experiment '$EXPERIMENT_NAME' with ID: $EXPERIMENT_ID"
fi
echo

# Update .env.local with the experiment ID
echo "Updating .env.local with experiment ID..."
sed -i '' "s/MLFLOW_EXPERIMENT_ID=.*/MLFLOW_EXPERIMENT_ID=$EXPERIMENT_ID/" .env.local
echo

# Update app.yaml with the experiment ID
echo "Updating app.yaml with experiment ID..."
sed -i '' "s/value: \"[0-9]*\"/value: \"$EXPERIMENT_ID\"/" app.yaml
echo

echo "Setup complete!"
echo "- .env.local created with experiment ID: $EXPERIMENT_ID"
echo "- app.yaml updated with experiment ID: $EXPERIMENT_ID"
echo "- MLflow experiment created at: /Users/$DATABRICKS_USERNAME/agents-on-apps"

