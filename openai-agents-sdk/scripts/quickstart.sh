#!/bin/bash

# check if UV and nvm are installed or not
# install UV and nvm for them if they don't have it
# set default uv python version to 3.10
# run `nvm use 20`

# TODO: set up databricks auth for them
# check if databricks cli is installed or not (databricks -v doesn't error out)
# install the databricks CLI either via homebrew or curl if homebrew fails
# brew tap databricks/tap
# brew install databricks
# curl -fsSL https://raw.githubusercontent.com/databricks/setup-cli/main/install.sh | sh
# run the curl with sudo 





./setup-mlflow.sh
./start-app.sh
