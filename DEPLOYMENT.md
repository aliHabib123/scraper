# Digital Ocean Deployment Guide

## Prerequisites
- Digital Ocean Droplet (Ubuntu 22.04 recommended)
- Domain/IP address
- MySQL database (can be on same droplet or managed database)

## Step 1: Set Up Your Droplet

### Create a Droplet
1. Log into Digital Ocean
2. Create a new Droplet (Ubuntu 22.04 LTS, minimum 1GB RAM)
3. Add your SSH key during creation
4. Note the IP address

### SSH into your server
```bash
ssh root@YOUR_DROPLET_IP
```

## Step 2: Initial Server Setup

```bash
# Update system
apt update && apt upgrade -y

# Install required packages
apt install -y python3 python3-pip python3-venv git

# Optional: Install mysql-client for manual database access (not needed if using managed DB)
# apt install -y mysql-client

# Create a user for the application (optional but recommended)
adduser scraper
usermod -aG sudo scraper
su - scraper
```

## Step 3: Clone and Setup Application

```bash
# Clone your repository
cd ~
git clone https://github.com/aliHabib123/scraper.git scraper
cd scraper

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## Step 4: Configure Environment

```bash
# Copy and edit environment file
cp .env.example .env
nano .env
```

Update these values in `.env`:
```
DATABASE_URL=mysql+mysqlconnector://USER:PASSWORD@localhost/scraper_db
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id
```

## Step 5: Set Up Database

### Option A: Local MySQL on Droplet
```bash
# Install MySQL
sudo apt install -y mysql-server

# Secure installation
sudo mysql_secure_installation

# Create database
sudo mysql -e "CREATE DATABASE scraper_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
sudo mysql -e "CREATE USER 'scraper'@'localhost' IDENTIFIED BY 'YOUR_PASSWORD';"
sudo mysql -e "GRANT ALL PRIVILEGES ON scraper_db.* TO 'scraper'@'localhost';"
sudo mysql -e "FLUSH PRIVILEGES;"
```

### Option B: Digital Ocean Managed Database
1. Create a MySQL database in Digital Ocean dashboard
2. Note connection details
3. Update DATABASE_URL in .env

### Initialize Database
```bash
cd ~/scraper
source venv/bin/activate
python init_db.py
```

## Step 6: Add Forums and Keywords

```bash
# Add keywords
python manage_keywords.py add "stake"
python manage_keywords.py add "shuffle"
# ... add more keywords

# Add forums
python manage_forums.py add "askgamblers" "https://forum.askgamblers.com/" \
  '["https://forum.askgamblers.com/forum/21-online-slot-discussions/", "https://forum.askgamblers.com/forum/9-sports-betting-general-discussions/"]' \
  --type category --max-pages 2

python manage_forums.py add "bitcointalk" "https://bitcointalk.org/" \
  '["https://bitcointalk.org/index.php?board=56.0"]' \
  --type category --max-pages 1

# Add Reddit subreddits
python add_reddit_forums.py
```

## Step 7: Configure Schedule (Optional)

Edit `.env` to set your preferred schedule:

```bash
nano .env
```

Add/modify these lines:
```env
# Run every 24 hours (default)
SCHEDULE_INTERVAL=24

# Run at 2 AM instead of midnight
SCHEDULE_TIME=02:00

# Other options: 1, 2, 3, 4, 6, 8, 12, 24 hours
```

Generate the timer configuration:
```bash
./deployment/configure_schedule.sh
```

## Step 8: Set Up Systemd Service (Automated Running)

```bash
# Copy service files
sudo cp deployment/scraper.service /etc/systemd/system/
sudo cp deployment/scraper.timer /etc/systemd/system/

# Enable and start the timer
sudo systemctl daemon-reload
sudo systemctl enable scraper.timer
sudo systemctl start scraper.timer

# Check status
sudo systemctl status scraper.timer
sudo systemctl list-timers --all
```

## Step 8: Manual Test Run

```bash
cd ~/scraper
source venv/bin/activate
python main.py
```

## Management Commands

### View service logs
```bash
sudo journalctl -u scraper.service -f
```

### Check timer status
```bash
sudo systemctl status scraper.timer
```

### Run manually
```bash
sudo systemctl start scraper.service
```

### Stop/Restart
```bash
sudo systemctl stop scraper.timer
sudo systemctl restart scraper.timer
```

### Update code
```bash
cd ~/scraper
git pull
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart scraper.timer
```

## Monitoring

### Check crawler logs
```bash
tail -f ~/scraper/crawler.log
```

### Check last run
```bash
sudo journalctl -u scraper.service --since "1 hour ago"
```

### Database queries
```bash
mysql -u scraper -p scraper_db

# Show recent matches
SELECT m.id, f.name as forum, k.keyword, m.thread_url, m.created_at 
FROM matches m 
JOIN forums f ON m.forum_id = f.id 
JOIN keywords k ON m.keyword_id = k.id 
ORDER BY m.created_at DESC 
LIMIT 10;
```

## Troubleshooting

### Service won't start
```bash
sudo systemctl status scraper.service
sudo journalctl -u scraper.service -n 50
```

### Database connection issues
```bash
# Test database connection
python test_db_connection.py
```

### Permissions issues
```bash
# Fix ownership
sudo chown -R scraper:scraper ~/scraper
```

## Security Best Practices

1. **Firewall**: Enable UFW
```bash
sudo ufw allow OpenSSH
sudo ufw enable
```

2. **Fail2Ban**: Protect SSH
```bash
sudo apt install fail2ban
sudo systemctl enable fail2ban
```

3. **Keep Updated**
```bash
# Set up unattended upgrades
sudo apt install unattended-upgrades
sudo dpkg-reconfigure --priority=low unattended-upgrades
```

4. **Backup Database**
```bash
# Create backup script
mkdir -p ~/backups
mysqldump -u scraper -p scraper_db > ~/backups/scraper_$(date +%Y%m%d).sql
```

## Cost Optimization

- **$6/month**: 1GB RAM droplet (sufficient for this scraper)
- **Managed DB**: $15/month (optional, can use local MySQL)
- **Total**: As low as $6/month with local MySQL
