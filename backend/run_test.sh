#!/bin/bash
# Activate the virtual environment
source ./venv/bin/activate

# Run the test script
python test_mcp_connector.py

# Deactivate the virtual environment
deactivate 