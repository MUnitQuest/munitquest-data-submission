#!/bin/bash
echo "Executing scoring program..."
# installs dependencies
python3 -m pip install bids-validator-deno
python3 -m pip install -e .

# run the program
python3 main.py /app/input/res /app/output/