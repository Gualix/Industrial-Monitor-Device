#!/usr/bin/env bash
set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SERVICE_FILE="/etc/systemd/system/industrial-monitor-device.service"

sudo tee "$SERVICE_FILE" >/dev/null <<SERVICE
[Unit]
Description=Industrial Monitor Device
After=network.target

[Service]
WorkingDirectory=$PROJECT_ROOT/backend
ExecStart=$PROJECT_ROOT/backend/.venv/bin/python $PROJECT_ROOT/backend/run.py
Restart=always
RestartSec=3
User=titanio

[Install]
WantedBy=multi-user.target
SERVICE

sudo systemctl daemon-reload
sudo systemctl enable industrial-monitor-device.service
sudo systemctl restart industrial-monitor-device.service

echo "Service installed and started."
