# Quick Start - Digital Ocean Deployment

## 1. Create Droplet
- Ubuntu 22.04 LTS
- 1GB RAM minimum ($6/month)
- Add your SSH key

## 2. SSH and Run Setup

```bash
# SSH into server
ssh root@YOUR_IP

# Clone repository
git clone YOUR_REPO_URL /home/scraper/scraper

# Run automated setup
cd /home/scraper/scraper
chmod +x deployment/setup.sh
sudo ./deployment/setup.sh
```

## 3. Configure Environment

```bash
# Edit .env file
nano /home/scraper/scraper/.env
```

Required settings:
```env
DATABASE_URL=mysql+mysqlconnector://scraper:PASSWORD@localhost/scraper_db
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_CHAT_ID=your_chat_id_here
```

## 4. Set Up Database

### Option A: Use Digital Ocean Managed Database (Recommended)
1. Create a MySQL database in Digital Ocean dashboard
2. Note the connection string
3. Update DATABASE_URL in `.env`
4. Skip to Step 5

### Option B: Install MySQL on Droplet

```bash
# Install MySQL
sudo apt install -y mysql-server
sudo mysql_secure_installation

# Create database
sudo mysql
```

In MySQL:
```sql
CREATE DATABASE scraper_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'scraper'@'localhost' IDENTIFIED BY 'YOUR_SECURE_PASSWORD';
GRANT ALL PRIVILEGES ON scraper_db.* TO 'scraper'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

## 5. Initialize Database

```bash
su - scraper
cd scraper
source venv/bin/activate
python init_db.py
```

## 6. Add Keywords

```bash
python manage_keywords.py add "stake"
python manage_keywords.py add "shuffle"
python manage_keywords.py add "rollbit"
python manage_keywords.py add "duelbits"
# Add more...
```

## 7. Add Forums

```bash
# AskGamblers
python manage_forums.py add "askgamblers" "https://forum.askgamblers.com/" \
  '["https://forum.askgamblers.com/forum/21-online-slot-discussions/", "https://forum.askgamblers.com/forum/9-sports-betting-general-discussions/"]' \
  --type category --max-pages 1

# BitcoinTalk
python manage_forums.py add "bitcointalk" "https://bitcointalk.org/" \
  '["https://bitcointalk.org/index.php?board=56.0"]' \
  --type category --max-pages 1

# Reddit subreddits
python add_reddit_forums.py
```

## 8. Test Run

```bash
python main.py
```

Check for any errors. You should see it crawling forums and potentially finding matches.

## 9. Enable Automated Running

```bash
exit  # Exit scraper user back to root
sudo systemctl enable scraper.timer
sudo systemctl start scraper.timer
sudo systemctl status scraper.timer
```

## 10. Verify Everything Works

```bash
# Check timer is active
sudo systemctl list-timers --all | grep scraper

# View logs
sudo journalctl -u scraper.service -f

# Manually trigger a run
sudo systemctl start scraper.service
```

## Done! 🎉

The scraper will now run automatically once per day at midnight by default.

### Change Schedule (Optional)

Edit schedule in `.env`:
```bash
nano /home/scraper/scraper/.env
```

Add these lines:
```env
# Run every 12 hours instead
SCHEDULE_INTERVAL=12

# Run at 2 AM
SCHEDULE_TIME=02:00
```

Options for SCHEDULE_INTERVAL: 1, 2, 3, 4, 6, 8, 12, 24 hours

Apply changes:
```bash
su - scraper
cd scraper
./deployment/configure_schedule.sh
exit
sudo cp /home/scraper/scraper/deployment/scraper.timer /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl restart scraper.timer
```

You'll receive Telegram notifications when matches are found.

## Common Commands

```bash
# View recent logs
sudo journalctl -u scraper.service -n 100

# Check timer schedule
sudo systemctl list-timers scraper.timer

# Restart timer
sudo systemctl restart scraper.timer

# Run immediately
sudo systemctl start scraper.service

# View crawler log file
tail -f /home/scraper/scraper/crawler.log

# Update code
su - scraper
cd scraper
git pull
source venv/bin/activate
pip install -r requirements.txt
exit
sudo systemctl restart scraper.timer
```

## Costs

- **Droplet**: $6/month (1GB RAM)
- **Total**: $6/month with local MySQL

No additional costs for managed databases needed!
