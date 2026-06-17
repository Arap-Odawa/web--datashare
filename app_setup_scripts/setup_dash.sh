#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

echo "--- Updating System Packages ---"
sudo apt-get update -y
sudo apt-get upgrade -y

echo "--- Installing Python and Virtual Environment Tools ---"
sudo apt-get install -y python3 python3-pip python3-venv build-essential


# Define the target path
TARGET_DIR="$HOME/dmaritim/Music/archive"

echo "--- Checking for Project Directory ---"
if [ -d "$TARGET_DIR" ]; then
    echo "Directory $TARGET_DIR found. Proceeding..."
    cd $TARGET_DIR
else
    echo "ERROR: The folder 'dash_app' was not found in $HOME/Music."
    echo "Please ensure the folder exists before running this script."
    mkdir -p $TARGET_DIR
    cd $TARGET_DIR
    
fi


echo "--- Setting up Virtual Environment ---"
python3 -m venv venv
#source /home/dmaritim/Music/archive/venv/bin/activate
pip install gunicorn

echo "--- Installing Required Modules ---"
# Upgrading pip first
pip install --upgrade pip
# Installing specific versions for stability
pip install polars dash plotly pandas

echo "--- Environment Setup Complete ---"

# Check if the python script exists, if not, create a placeholder
if [ ! -f "app.py" ]; then
    echo "Note: Please ensure your python script is saved as 'app.py' in $(pwd)"
fi

echo "--- Instructions ---"
echo "1. Place your 'processed_dhis2_data.csv' in $(pwd)"
echo "2. Run 'source venv/bin/activate'"
echo "3. Run 'python app.py'"
