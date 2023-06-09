#!/bin/bash
SCRIPT_NAME="lambda_function"
SCRIPT_PATH="$(dirname "${BASH_SOURCE[0]}")/$SCRIPT_NAME.py"
ZIP_NAME="$SCRIPT_NAME.zip"

echo "Zipping $SCRIPT_NAME"

zip -v $ZIP_NAME $SCRIPT_PATH
