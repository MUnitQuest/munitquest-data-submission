#!/bin/bash
ENVLOG="/app/output/environment.log"

# installs dependencies
echo "Setting up environment (BIDS-Validator & MUniverse)..." | tee -a $ENVLOG
python3 -m venv .submission
source .submission/bin/activate
python3 -m pip install --upgrade pip >> $ENVLOG 2>&1
python3 -m pip install muniverse-emg bids-validator-deno >> $ENVLOG 2>&1

echo "Building scoring program..." | tee -a $ENVLOG
python3 -m pip install -e . >> $ENVLOG 2>&1

# run the program
echo "Running scoring program..."
python3 main.py /app/input/res /app/output/