#!/usr/bin/env bash
set -euo pipefail

python -m pip install -r requirements.txt
npm install
npm run build
