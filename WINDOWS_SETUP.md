# Windows Setup Guide

Complete guide for setting up the Forum Scraper on a Windows laptop.

---

## Migration from MySQL to SQLite

**If you're currently using MySQL on your Mac and want to use SQLite on Windows, follow these steps first:**

### On Your Mac (Export MySQL Data)

1. Ensure your virtual environment is activated:
   ```bash
   cd ~/projects/scraper
   source venv/bin/activate
   ```

2. Run the export script:
   ```bash
   python export_mysql.py
   ```

3. This will create `mysql_export.json` containing all your data (forums, keywords, matches)

4. **Copy these files to Windows:**
   - Entire `scraper` project folder
   - `mysql_export.json` file

### On Windows (Import to SQLite)

After completing the setup steps below (1-4), you'll import the data in step 6.

**Skip to [Section 1](#1-install-prerequisites) to begin Windows setup.**

---

## 1. Install Prerequisites

### Python 3.10+

1. Download Python from [python.org](https://www.python.org/downloads/)
2. **IMPORTANT:** During installation, check ✅ **"Add Python to PATH"**
3. Complete the installation
4. Verify installation:
   ```cmd
   python --version
   ```
   Should show: `Python 3.10.x` or higher

### Git (Optional - for cloning repository)

- Download from [git-scm.com](https://git-scm.com/download/win)
- Use default installation options

---

## 2. Transfer Project Files

### Option A: Using Git

```cmd
git clone <your-repo-url>
cd scraper
```

### Option B: Manual Transfer

1. Copy entire scraper project folder from Mac
2. Place in: `C:\Users\YourName\scraper`

---

## 3. Set Up Python Environment

Open **Command Prompt** and run:

```cmd
cd C:\Users\YourName\scraper
python -m venv venv
venv\Scripts\activate
```

Your prompt should now show `(venv)`.

---

## 4. Install Dependencies

```cmd
pip install -r requirements.txt
playwright install chromium
```

This will install:
- Database libraries (SQLAlchemy)
- HTTP client (httpx)
- HTML parsing (BeautifulSoup4)
- Browser automation (Playwright)
- And all other required packages

---

## 5. Configure Environment Variables

Create a `.env` file in the project root (`C:\Users\YourName\scraper\.env`):

```env
# Database
DATABASE_URL=sqlite:///scraper.db

# Telegram Notifications (optional but recommended)
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_CHAT_ID=your_chat_id_here

# LCB.org Extraction Mode
# 'comprehensive' (default): Extract all thread links including sidebar/widgets (slower, more thorough)
# 'targeted': Extract only main thread list (faster, less coverage)
LCB_EXTRACTION_MODE=comprehensive

# Playwright Browser Settings
# Set to 'false' to see browser window during scraping (useful for debugging)
# Set to 'true' for headless mode (default, recommended for automation)
PLAYWRIGHT_HEADLESS=true
```

**Configuration Options:**

- **LCB_EXTRACTION_MODE:**
  - `comprehensive` (default): Extracts ~100+ threads per page including sidebar links, trending topics, and news. More thorough but slower (3-4 hours for full crawl).
  - `targeted`: Extracts only main thread list (~40 threads per page). Faster (1-2 hours) but may miss some trending/popular threads.

- **PLAYWRIGHT_HEADLESS:**
  - `true` (default): Browser runs in background (invisible)
  - `false`: Shows browser window (useful for debugging)

### How to Get Telegram Chat ID

#### Method 1: Using @userinfobot (Easiest)

1. Add your bot to your Telegram group
2. Add **@userinfobot** to the same group
3. @userinfobot will automatically send the group's Chat ID
4. Copy the Chat ID (looks like `-1001234567890`)
5. Remove @userinfobot from the group (optional)
6. Update `.env` with the Chat ID

#### Method 2: Using Bot API

1. Add your bot to your Telegram group
2. Send any message in the group (e.g., "test")
3. Open PowerShell and run:
   ```powershell
   Invoke-WebRequest "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates"
   ```
   Replace `<YOUR_BOT_TOKEN>` with your actual bot token

4. Look for this in the output:
   ```json
   "chat": {
     "id": -1001234567890,
     "title": "Your Group Name",
     "type": "supergroup"
   }
   ```

5. Copy the `id` value (the negative number)
6. Update `.env` with the Chat ID

**Notes:**
- Group IDs are always **negative** (e.g., `-1001234567890`)
- Private chat IDs are **positive** (e.g., `123456789`)
- Ensure your bot has permission to send messages in the group

---

## 6. Initialize Database

### Option A: Import from MySQL Export (Migrating from Mac)

**If you exported data from MySQL on your Mac:**

1. Ensure `mysql_export.json` is in the project folder
2. With the virtual environment activated, run:
   ```cmd
   python import_sqlite.py
   ```

This will:
- Create the SQLite database
- Import all forums, keywords, and matches from MySQL
- Verify data integrity

**Skip to [Section 7](#7-test-the-scraper) after import completes.**

### Option B: Fresh Database Setup

**If starting fresh without MySQL data:**

With the virtual environment activated:

```cmd
python add_forums.py
python add_keywords.py
```

This will:
- Create the SQLite database
- Add all configured forums
- Add all keywords to monitor

---

## 7. Test the Scraper

Run a test crawl:

```cmd
python main.py
```

The scraper will:
- Process all enabled forums
- Automatically handle rate limiting
- Retry blocked forums after 30 minutes
- Send Telegram notifications when matches are found

**Expected Output:**
```
Starting crawl: 8 forums, 150 keywords
Processing forum: casino.guru
...
Detected 1 forum(s) with rate limiting
Waiting 30 minutes before retry...
...
CRAWL SUMMARY
============================================================
Total matches: 5
Total pages: 120
Total threads: 85
```

---

## 8. Set Up Automated Scheduling

### Option A: Windows Task Scheduler (Recommended)

#### Open Task Scheduler

1. Press `Win + R`
2. Type: `taskschd.msc`
3. Press Enter

#### Create Basic Task

1. Click **"Create Basic Task"** (right sidebar)
2. Name: `Forum Scraper`
3. Description: `Automated forum monitoring for keywords`
4. Click **"Next"**

#### Set Trigger

1. Select: **"Daily"**
2. Click **"Next"**
3. Start time: Choose when to run (e.g., `8:00 AM`)
4. Recur every: `1 days`
5. Click **"Next"**

#### Set Action

1. Select: **"Start a program"**
2. Click **"Next"**
3. Configure program:
   - **Program/script:** 
     ```
     C:\Users\YourName\Desktop\scraper\scraper\venv\Scripts\python.exe
     ```
     *(Replace `YourName` with your actual username)*
   
   - **Add arguments:**
     ```
     main.py
     ```
   
   - **Start in:**
     ```
     C:\Users\YourName\Desktop\scraper\scraper
     ```
     *(Replace `YourName` with your actual username)*

4. Click **"Next"** then **"Finish"**

#### Configure Advanced Settings

1. Find your task in Task Scheduler Library
2. Right-click → **"Properties"**

   **General Tab:**
   - ✅ "Run whether user is logged on or not"
   - Select: "Run with highest privileges" (optional)

   **Triggers Tab:**
   - Click **"Edit"**
   - Check: ✅ "Repeat task every: **6 hours**"
   - For duration of: **1 day**
   - ✅ "Enabled"
   - Click **"OK"**

   **Conditions Tab:**
   - ❌ Uncheck "Start the task only if the computer is on AC power"

   **Settings Tab:**
   - ✅ "Allow task to be run on demand"
   - ✅ "Run task as soon as possible after a scheduled start is missed"
   - ✅ "If the task fails, restart every: **10 minutes**"
   - Attempt to restart up to: **3 times**
   - If running task does not end when requested: "Stop the existing instance"

3. Click **"OK"**
4. Enter your Windows password if prompted

#### Test the Scheduled Task

1. Right-click on your task in Task Scheduler
2. Click **"Run"**
3. Check `crawler.log` file or Telegram for results
4. Verify task ran successfully in "Last Run Result" column

---

### Option B: Simple Batch Script

Create a file named `run_scraper.bat` in your project folder:

```batch
@echo off
cd C:\Users\YourName\Desktop\scraper\scraper
call venv\Scripts\activate
python main.py
pause
```

**To use:**
- Double-click `run_scraper.bat` to run manually
- Or schedule this `.bat` file in Task Scheduler instead of python.exe

**Benefits:**
- Easier to test (just double-click)
- Shows output window
- Can see errors immediately

---

## 9. Troubleshooting

### Python Not Found

If `python` command is not recognized:
- Reinstall Python and check **"Add Python to PATH"**
- Or use full path: `C:\Users\YourName\AppData\Local\Programs\Python\Python310\python.exe`

### Permission Errors

Run Command Prompt as **Administrator**:
- Right-click on Command Prompt
- Select **"Run as administrator"**

### Playwright Installation Issues

If Playwright browser installation fails:
```cmd
playwright install --force chromium
```

### Database Locked Errors

- Ensure no other instance of the scraper is running
- Close any database browser tools (DB Browser for SQLite, etc.)

### Telegram Not Working

Test your Telegram connection:
```cmd
python test_telegram.py
```

Check:
- Bot token is correct in `.env`
- Chat ID is correct (negative number for groups)
- Bot is added to the group
- Bot has permission to send messages

---

## 10. Monitoring and Logs

### View Logs

The scraper logs to console. To save logs to a file, run:

```cmd
python main.py >> scraper.log 2>&1
```

Or in Task Scheduler, add output redirection to the arguments:
- Arguments: `main.py >> C:\Users\YourName\scraper\logs\scraper.log 2>&1`

### Check Database

Use **DB Browser for SQLite** to view the database:
1. Download from [sqlitebrowser.org](https://sqlitebrowser.org/)
2. Open `scraper.db`
3. Browse tables: `forums`, `keywords`, `matches`, `threads`

---

## 11. Automated Features

The scraper includes automatic handling for:

✅ **Rate Limit Detection**
- Stops after 3 consecutive failures
- Marks forum for retry

✅ **Automatic Forum Rotation**
- Moves to next forum when rate-limited
- No wasted time on blocked forums

✅ **Retry After 30 Minutes**
- Automatically retries rate-limited forums
- Merges results from original + retry runs
- Up to 2 retry attempts per forum

✅ **Zero Manual Intervention**
- Perfect for cron/scheduled tasks
- Handles Reddit 403 errors gracefully
- Completes fully automatically

---

## 12. Configuration Tips

### Adjust Rate Limits

Edit `main.py` if you need to adjust rate limits:

```python
if is_reddit:
    rate_limit = 12.0  # Reddit: 12 seconds between requests
elif is_casinomeister or is_askgamblers:
    rate_limit = 3.0   # Forums with bot protection: 3 seconds
else:
    rate_limit = 2.0   # Standard forums: 2 seconds
```

### Disable Headless Mode (for debugging)

To see the browser window during scraping (useful for troubleshooting):

In `.env`:
```env
PLAYWRIGHT_HEADLESS=false
```

**Note:** Headless mode is recommended for scheduled tasks (no visible browser window).

### Add/Remove Forums

Edit database using `add_forums.py` or manually update via DB Browser for SQLite.

### Add/Remove Keywords

Edit `add_keywords.py` and run:
```cmd
python add_keywords.py
```

---

## Support

If you encounter issues:

1. Check logs for error messages
2. Verify `.env` configuration
3. Test Telegram connection with `python test_telegram.py`
4. Ensure all dependencies are installed: `pip install -r requirements.txt`
5. Try running with verbose logging: `python main.py --verbose`

---

**Setup Complete!** Your scraper will now run automatically and handle all rate limiting intelligently.
