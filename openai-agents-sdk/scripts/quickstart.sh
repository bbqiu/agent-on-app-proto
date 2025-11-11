#!/bin/bash

# check if UV and nvm are installed or not
# optimally, use brew
#    - [`uv` installation docs](https://docs.astral.sh/uv/getting-started/installation/)
#    - [`nvm` installation](https://github.com/nvm-sh/nvm?tab=readme-ov-file#installing-and-updating)
#    - [`databricks CLI` installation](https://docs.databricks.com/aws/en/dev-tools/cli/install)
# install UV and nvm for them if they don't have it
# set default uv python version to 3.10
# run `nvm use 20`

# TODO: set up databricks auth for them - https://docs.databricks.com/aws/en/dev-tools/cli/install
# check if databricks cli is installed or not (databricks -v doesn't error out)
# install the databricks CLI either via homebrew or curl if homebrew fails
# brew tap databricks/tap
# brew install databricks
# curl -fsSL https://raw.githubusercontent.com/databricks/setup-cli/main/install.sh | sh
# run the curl with sudo if this fails


set -e
echo "Setting up configuration files..."

# Copy .env.example to .env.local if it doesn't exist
if [ ! -f ".env.local" ]; then
    echo "Copying .env.example to .env.local..."
    cp .env.example .env.local
    echo
else
    echo ".env.local already exists, skipping copy..."
fi

# run databricks auth login and wait for the user to finish
# if the user cancels, exit the script
# from the output of databricks auth login, get the profile name
# set the DATABRICKS_CONFIG_PROFILE environment variable to the profile name in .env.local

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


./start-app.sh
