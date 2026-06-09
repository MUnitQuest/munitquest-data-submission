#!/bin/bash
PIPLOG="/app/output/environment.log"

# installs dependencies
printf "Setting up environment (BIDS-Validator & MUniverse)...\n"
python3 -m venv .submission
source .submission/bin/activate

python3 -m pip install --upgrade pip --quiet --quiet --log $PIPLOG
python3 -m pip install bids-validator-deno --quiet --quiet --log $PIPLOG
# install MUniverse
git clone https://github.com/dfarinagroup/muniverse.git &>> $PIPLOG
cd muniverse
python3 -m pip install -e . --quiet --quiet --log $PIPLOG
cd ..

printf "Building scoring program...\n"
python3 -m pip install -e . --quiet --quiet --log $PIPLOG

# run the program
printf "\nRunning scoring program...\n"
python3 main.py /app/input/res /app/output/