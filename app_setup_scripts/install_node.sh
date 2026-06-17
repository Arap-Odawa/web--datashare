#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

echo "--- 1. Prerequisite Checks ---"
# Check if running as root or with sudo
if [ "$EUID" -ne 0 ]; then 
  echo "Please run as root or use sudo."
  exit 1
fi

echo "--- 2. Updating System & Installing Curl ---"
apt-get update -y
apt-get install -y curl build-essential

echo "--- 3. Adding Node.js LTS Repository ---"
# Downloads the setup script for the current LTS version (e.g., v20/v22)
# This prevents installing the very old versions often found in default Ubuntu repos
curl -fsSL https://deb.nodesource.com/setup_lts.x | bash -

echo "--- 4. Installing Node.js ---"
apt-get install -y nodejs

echo "--- 5. Installing Yarn ---"
# The most reliable way to install Yarn on modern Node systems is via npm
npm install -g yarn

echo "--- 6. Verifying Installation ---"
NODE_VERSION=$(node -v)
NPM_VERSION=$(npm -v)
YARN_VERSION=$(yarn -v)

echo "Success! The following versions are installed:"
echo "Node.js: $NODE_VERSION"
echo "NPM:     $NPM_VERSION"
echo "Yarn:    $YARN_VERSION"

echo "--- Instructions ---"
echo "You can now run 'yarn build' or 'd2 app scripts' in your project directory."
