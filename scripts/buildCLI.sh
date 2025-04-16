#!/usr/bin/env bash

# Delete previous build files
if [ -d ./build/ ]; then
  rm -rf ./build/
fi
if [ -d ./dist/ ]; then
  rm -rf ./dist/
fi

# Actual building!
# Install requirements.
python3 -m pip install -U -r requirements.txt

# We embed all of our files into a single executable.
pyinstaller client.py --onefile
