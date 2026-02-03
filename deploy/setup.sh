#!/usr/bin/env bash
set -e

APP_DIR="/opt/labelprinter"
REPO="https://github.com/colbyc21/LabelPrinter.git"

echo "=== Shipping Label Printer - Pi Setup ==="

# Install system dependencies
sudo apt-get update
sudo apt-get install -y python3 python3-venv python3-dev gcc unixodbc-dev

# Clone or pull repo
if [ -d "$APP_DIR/.git" ]; then
    echo "Updating existing install..."
    cd "$APP_DIR"
    git pull
else
    echo "Cloning repo..."
    sudo mkdir -p "$APP_DIR"
    sudo chown "$USER:$USER" "$APP_DIR"
    git clone "$REPO" "$APP_DIR"
    cd "$APP_DIR"
fi

# Python venv + deps
if [ ! -d "$APP_DIR/venv" ]; then
    python3 -m venv "$APP_DIR/venv"
fi
"$APP_DIR/venv/bin/pip" install --upgrade pip
"$APP_DIR/venv/bin/pip" install -r "$APP_DIR/requirements.txt"

# Create .env if missing
if [ ! -f "$APP_DIR/.env" ]; then
    cat > "$APP_DIR/.env" <<'ENVEOF'
DB2_SYSTEM=172.17.29.10
DB2_UID=DACCOLBY
DB2_PWD=DACCOLBY
SECRET_KEY=change-me-to-random-string
ADMIN_PASSWORD=admin
ENVEOF
    echo "Created .env - edit with your settings."
fi

# Create printers.json if missing
if [ ! -f "$APP_DIR/printers.json" ]; then
    echo '[]' > "$APP_DIR/printers.json"
    echo "Created empty printers.json - add printers via admin panel."
fi

# Install systemd service
sudo cp "$APP_DIR/deploy/labelprinter.service" /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable labelprinter
sudo systemctl restart labelprinter

echo ""
echo "=== Done! ==="
echo "App running at http://$(hostname -I | awk '{print $1}'):8080"
echo "Check status: sudo systemctl status labelprinter"
echo "View logs:    sudo journalctl -u labelprinter -f"
