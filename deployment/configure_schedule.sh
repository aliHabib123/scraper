#!/bin/bash
# Configure systemd timer based on .env settings

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
ENV_FILE="$PROJECT_DIR/.env"

# Check if .env exists
if [ ! -f "$ENV_FILE" ]; then
    echo "Error: .env file not found at $ENV_FILE"
    exit 1
fi

# Load environment variables
export $(grep -v '^#' "$ENV_FILE" | grep -v '^$' | xargs)

# Default values
SCHEDULE_INTERVAL=${SCHEDULE_INTERVAL:-24}
SCHEDULE_TIME=${SCHEDULE_TIME:-00:00}

echo "=== Configuring Scraper Schedule ==="
echo "Interval: Every $SCHEDULE_INTERVAL hours"
echo "Time: $SCHEDULE_TIME"

# Generate OnCalendar value based on interval
case $SCHEDULE_INTERVAL in
    1)
        CALENDAR_VALUE="hourly"
        DESCRIPTION="hourly"
        ;;
    2)
        CALENDAR_VALUE="*-*-* 00/2:00:00"
        DESCRIPTION="every 2 hours"
        ;;
    3)
        CALENDAR_VALUE="*-*-* 00/3:00:00"
        DESCRIPTION="every 3 hours"
        ;;
    4)
        CALENDAR_VALUE="*-*-* 00/4:00:00"
        DESCRIPTION="every 4 hours"
        ;;
    6)
        CALENDAR_VALUE="*-*-* 00/6:00:00"
        DESCRIPTION="every 6 hours"
        ;;
    8)
        CALENDAR_VALUE="*-*-* 00/8:00:00"
        DESCRIPTION="every 8 hours"
        ;;
    12)
        CALENDAR_VALUE="*-*-* 00/12:00:00"
        DESCRIPTION="every 12 hours"
        ;;
    24)
        # Use specified time or default to midnight
        if [ "$SCHEDULE_TIME" = "00:00" ]; then
            CALENDAR_VALUE="daily"
        else
            CALENDAR_VALUE="*-*-* $SCHEDULE_TIME:00"
        fi
        DESCRIPTION="daily at $SCHEDULE_TIME"
        ;;
    *)
        echo "Error: Invalid SCHEDULE_INTERVAL. Must be one of: 1, 2, 3, 4, 6, 8, 12, 24"
        exit 1
        ;;
esac

# Generate timer file
TIMER_FILE="$SCRIPT_DIR/scraper.timer"

cat > "$TIMER_FILE" << EOF
[Unit]
Description=Run Forum Scraper $DESCRIPTION
Requires=scraper.service

[Timer]
# Run $DESCRIPTION
OnCalendar=$CALENDAR_VALUE
# Run 5 minutes after boot if missed
OnBootSec=5min
# If the system was off during a scheduled run, run it when system comes back
Persistent=true

[Install]
WantedBy=timers.target
EOF

echo "✓ Timer configuration updated: $TIMER_FILE"
echo ""

# If running as root and systemd service exists, offer to reload
if [ "$EUID" -eq 0 ] && [ -f "/etc/systemd/system/scraper.timer" ]; then
    echo "Do you want to update and reload the systemd timer? (y/n)"
    read -r response
    if [[ "$response" =~ ^[Yy]$ ]]; then
        cp "$TIMER_FILE" /etc/systemd/system/scraper.timer
        systemctl daemon-reload
        if systemctl is-active --quiet scraper.timer; then
            systemctl restart scraper.timer
            echo "✓ Systemd timer reloaded and restarted"
        else
            echo "✓ Systemd timer configuration updated (not started)"
        fi
        systemctl status scraper.timer --no-pager
    fi
else
    echo "To apply changes on the server:"
    echo "  sudo cp $TIMER_FILE /etc/systemd/system/"
    echo "  sudo systemctl daemon-reload"
    echo "  sudo systemctl restart scraper.timer"
fi

echo ""
echo "Next scheduled run:"
if [ "$EUID" -eq 0 ] && [ -f "/etc/systemd/system/scraper.timer" ]; then
    systemctl list-timers scraper.timer --no-pager
else
    echo "(Install timer to see schedule)"
fi
