#!/bin/bash
# Setup script for Forum Scraper on Ubuntu server

set -e

echo "=== Forum Scraper Deployment Setup ==="
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "Please run as root (use sudo)"
    exit 1
fi

# Update system
echo "→ Updating system packages..."
apt update && apt upgrade -y

# Install dependencies
echo "→ Installing required packages..."
apt install -y python3 python3-pip python3-venv git

# Optional: Install mysql-client for manual DB access
# Uncomment the line below if you want to use mysql command-line client
# apt install -y mysql-client

# Create scraper user if doesn't exist
if ! id "scraper" &>/dev/null; then
    echo "→ Creating scraper user..."
    adduser --disabled-password --gecos "" scraper
    echo "✓ User 'scraper' created"
else
    echo "✓ User 'scraper' already exists"
fi

# Set up application directory
SCRAPER_DIR="/home/scraper/scraper"

if [ ! -d "$SCRAPER_DIR" ]; then
    echo "→ Please clone your repository to $SCRAPER_DIR manually:"
    echo "   su - scraper"
    echo "   git clone YOUR_REPO_URL scraper"
    echo "   exit"
    echo ""
    echo "Then run this script again."
    exit 0
fi

# Create virtual environment
echo "→ Setting up Python virtual environment..."
cd $SCRAPER_DIR
if [ ! -d "venv" ]; then
    sudo -u scraper python3 -m venv venv
fi

# Install Python dependencies
echo "→ Installing Python packages..."
sudo -u scraper $SCRAPER_DIR/venv/bin/pip install -r requirements.txt

# Set up .env file if doesn't exist
if [ ! -f "$SCRAPER_DIR/.env" ]; then
    echo "→ Creating .env file..."
    cp $SCRAPER_DIR/.env.example $SCRAPER_DIR/.env
    chown scraper:scraper $SCRAPER_DIR/.env
    echo ""
    echo "⚠️  IMPORTANT: Edit $SCRAPER_DIR/.env with your configuration:"
    echo "   - Database connection details"
    echo "   - Telegram bot token and chat ID"
fi

# Install systemd service and timer
echo "→ Installing systemd service..."
cp $SCRAPER_DIR/deployment/scraper.service /etc/systemd/system/
cp $SCRAPER_DIR/deployment/scraper.timer /etc/systemd/system/

# Reload systemd
systemctl daemon-reload

# Set correct permissions
echo "→ Setting permissions..."
chown -R scraper:scraper $SCRAPER_DIR

echo ""
echo "=== Setup Complete! ==="
echo ""
echo "Next steps:"
echo "1. Edit configuration: nano $SCRAPER_DIR/.env"
echo "2. Initialize database: su - scraper -c 'cd scraper && source venv/bin/activate && python init_db.py'"
echo "3. Add keywords: su - scraper -c 'cd scraper && source venv/bin/activate && python manage_keywords.py add \"keyword\"'"
echo "4. Add forums: su - scraper -c 'cd scraper && source venv/bin/activate && python manage_forums.py add ...'"
echo "5. Test run: su - scraper -c 'cd scraper && source venv/bin/activate && python main.py'"
echo "6. Enable timer: systemctl enable scraper.timer && systemctl start scraper.timer"
echo ""
echo "Check timer status: systemctl status scraper.timer"
echo "View logs: journalctl -u scraper.service -f"
