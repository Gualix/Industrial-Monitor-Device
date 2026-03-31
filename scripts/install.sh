#!/usr/bin/env bash
set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

sudo raspi-config nonint do_i2c 0
sudo raspi-config nonint do_onewire 0

sudo apt update
sudo apt install -y python3-venv python3-pip git

cd "$PROJECT_ROOT/backend"
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

echo
echo "Installation complete."
echo "Run with:"
echo "cd $PROJECT_ROOT/backend && source .venv/bin/activate && python run.py"
