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
python3 -m pip install -r requirements.txt

# Build the macOS bundle.
python3 setupMac.py py2app -O2
