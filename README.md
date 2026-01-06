# Forum Crawler

A minimal, production-ready Python crawler for monitoring public forums for keyword mentions. Built for extensibility and background execution.

## Features

- **Lightweight**: Pure Python with httpx + BeautifulSoup (no Scrapy, no Selenium)
- **Database-driven**: Dynamic forums and keywords loaded from PostgreSQL
- **Smart storage**: Saves matches only when keywords are found
- **Pagination support**: Configurable max pages per forum
- **Rate limiting**: Built-in request throttling
- **Error isolation**: Per-forum failure handling without crashing
- **Extensible**: Easy to add new forum parsers

## Requirements

- Python 3.11+
- MySQL 5.7+ (or PostgreSQL 12+)

## Quick Start

### 1. Install Dependencies

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install packages
pip install -r requirements.txt
```

### 2. Configure Database

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your database credentials
# MySQL: DATABASE_URL=mysql+mysqlconnector://user:password@localhost:3306/forum_crawler
# PostgreSQL: DATABASE_URL=postgresql://user:password@localhost:5432/forum_crawler
```

Or set environment variable directly:
```bash
# For MySQL:
export DATABASE_URL='mysql+mysqlconnector://root:password@localhost:3306/forum_crawler'

# For PostgreSQL:
export DATABASE_URL='postgresql://postgres:postgres@localhost:5432/forum_crawler'
```

### 3. Initialize Database

```bash
# Create tables
python init_db.py

# Or create tables with sample data
python init_db.py --sample-data
```

### 4. Run Crawler

```bash
# Run with default settings (2s rate limit)
python main.py

# Run with custom rate limit
python main.py --rate-limit 3.0

# Verbose logging
python main.py --verbose
```

## Project Structure

```
scraper/
├── models/              # SQLAlchemy models
│   ├── __init__.py
│   ├── base.py         # Database configuration
│   ├── forum.py        # Forum model
│   ├── keyword.py      # Keyword model
│   └── match.py        # Match model
├── crawler/            # Crawler logic
│   ├── __init__.py
│   ├── base_crawler.py # HTTP client with rate limiting
│   └── forum_crawler.py # Main crawler orchestration
├── parsers/            # Forum-specific parsers
│   ├── __init__.py
│   ├── base_parser.py  # Abstract parser interface
│   └── casino_guru_parser.py # casino.guru implementation
├── main.py             # CLI entrypoint
├── init_db.py          # Database initialization
└── requirements.txt
```

## Database Schema

### Forums Table
- `name`: Forum identifier (e.g., "casino.guru")
- `base_url`: Forum base URL
- `type`: "category" or "search"
- `start_urls`: JSON array of starting URLs
- `pagination_type`: Pagination strategy
- `max_pages`: Maximum pages to crawl per start URL
- `enabled`: Active status

### Keywords Table
- `keyword`: Search term
- `enabled`: Active status

### Matches Table
- `forum_id`: Foreign key to forums
- `keyword_id`: Foreign key to keywords
- `page_url`: URL where match was found
- `snippet`: Text excerpt containing keyword
- `created_at`: Timestamp
- **Unique constraint**: (forum_id, keyword_id, page_url) - prevents duplicates

## Usage Examples

### Add a Forum

```python
from models import Forum
from models.base import get_session_maker

SessionMaker = get_session_maker()
session = SessionMaker()

forum = Forum(
    name='casino.guru',
    base_url='https://casino.guru',
    type='category',
    start_urls=[
        'https://casino.guru/forum/casinos',
        'https://casino.guru/forum/complaints'
    ],
    pagination_type='page_number',
    max_pages=10,
    enabled=True
)

session.add(forum)
session.commit()
session.close()
```

### Add Keywords

```python
from models import Keyword
from models.base import get_session_maker

SessionMaker = get_session_maker()
session = SessionMaker()

keywords = ['bonus', 'scam', 'withdrawal', 'jackpot']
for kw in keywords:
    keyword = Keyword(keyword=kw, enabled=True)
    session.add(keyword)

session.commit()
session.close()
```

### Query Matches

```python
from models import Match
from models.base import get_session_maker

SessionMaker = get_session_maker()
session = SessionMaker()

# Get all matches
matches = session.query(Match).all()

# Get matches for specific keyword
from models import Keyword
keyword = session.query(Keyword).filter_by(keyword='bonus').first()
matches = session.query(Match).filter_by(keyword_id=keyword.id).all()

for match in matches:
    print(f"Found '{match.keyword.keyword}' at {match.page_url}")
    print(f"Snippet: {match.snippet[:100]}...")
    print()

session.close()
```

## CLI Management Tools

The project includes CLI tools for managing keywords and forums without writing Python code.

### Keyword Management

```bash
# List all keywords
python manage_keywords.py list

# Add a new keyword
python manage_keywords.py add "jackpot"
python manage_keywords.py add "rigged" --disabled

# Remove a keyword (with confirmation)
python manage_keywords.py remove 4

# Enable/disable a keyword
python manage_keywords.py toggle 1
```

**Example Output:**
```
$ python manage_keywords.py list

ID    Keyword                        Enabled   
--------------------------------------------------
1     bonus                          ✓ Yes     
2     scam                           ✓ Yes     
3     withdrawal                     ✓ Yes     
4     jackpot                        ✓ Yes     
```

### Forum Management

```bash
# List all forums
python manage_forums.py list

# Add a new forum
python manage_forums.py add "bitcointalk" \
  "https://bitcointalk.org" \
  "https://bitcointalk.org/index.php?board=56.0" \
  --max-pages 5

# Multiple start URLs (comma-separated)
python manage_forums.py add "reddit" \
  "https://reddit.com" \
  "https://reddit.com/r/gambling,https://reddit.com/r/casino" \
  --max-pages 10

# Update forum settings
python manage_forums.py update 1 --max-pages 20
python manage_forums.py update 2 --name "BitcoinTalk Forum"

# Remove a forum (with confirmation)
python manage_forums.py remove 2

# Enable/disable a forum
python manage_forums.py toggle 1
```

**Example Output:**
```
$ python manage_forums.py list

ID: 1
Name: casino.guru
Status: ✓ Enabled
Type: category
Max Pages: 10
Start URLs (4):
  - https://casino.guru/forum/casinos
  - https://casino.guru/forum/bonuses-and-promotions
  - https://casino.guru/forum/complaints-discussion
  - https://casino.guru/forum/general-gambling-discussion
------------------------------------------------------------

ID: 2
Name: bitcointalk
Status: ✓ Enabled
Type: category
Max Pages: 5
Start URLs (1):
  - https://bitcointalk.org/index.php?board=56.0
------------------------------------------------------------
```

### Check Matches

```bash
# View matches in database
python check_matches.py
```

**Example Output:**
```
Total matches found: 56

Matches by keyword:
  bonus: 26
  scam: 11
  withdrawal: 19

Sample matches:

Keyword: scam
URL: https://casino.guru/forum/casinos/beware--scam-casinos...
Snippet: [Post #1 by XDaniel] beware, scam casinos on the rise!...
```

## Adding New Forum Parsers

1. Create a new parser in `parsers/`:

```python
from parsers.base_parser import BaseParser
from bs4 import BeautifulSoup
from typing import List, Dict, Optional

class MyForumParser(BaseParser):
    def get_paginated_url(self, base_url: str, page_num: int) -> str:
        # Implement pagination logic
        return f"{base_url}?page={page_num}"
    
    def extract_thread_urls(self, soup: BeautifulSoup, base_url: str) -> List[str]:
        # Extract thread URLs from listing page
        urls = []
        for link in soup.select('.thread-link'):
            urls.append(link['href'])
        return urls
    
    def extract_thread_content(self, soup: BeautifulSoup) -> Optional[Dict[str, str]]:
        # Extract title and first post
        title = soup.select_one('h1.title').get_text(strip=True)
        content = soup.select_one('.first-post').get_text(strip=True)
        return {'title': title, 'content': content}
```

2. Register parser in `main.py`:

```python
def get_parser_for_forum(forum_name: str):
    parsers = {
        'casino.guru': CasinoGuruParser,
        'my_forum': MyForumParser,  # Add here
    }
    # ...
```

## Casino.guru Parser Details

The included `CasinoGuruParser`:
- Crawls category pages for thread listings
- Uses `?page=N` pagination format
- Extracts thread URLs using multiple fallback strategies
- Searches thread title + first post content for keywords
- Creates contextual snippets (±200 chars around keyword)

## Configuration

### Rate Limiting
Control request frequency to be respectful:
```bash
python main.py --rate-limit 3.0  # 3 seconds between requests
```

### Max Pages
Set per-forum in database:
```python
forum.max_pages = 20  # Crawl up to 20 pages per start URL
```

### Enable/Disable
Toggle forums or keywords without deleting:
```python
forum.enabled = False
keyword.enabled = False
```

## Background Execution

### Cron (Unix/Linux/Mac)
```bash
# Edit crontab
crontab -e

# Run every 6 hours
0 */6 * * * cd /path/to/scraper && ./venv/bin/python main.py >> cron.log 2>&1
```

### systemd (Linux)
Create `/etc/systemd/system/forum-crawler.service`:
```ini
[Unit]
Description=Forum Crawler
After=network.target postgresql.service

[Service]
Type=oneshot
User=youruser
WorkingDirectory=/path/to/scraper
Environment="DATABASE_URL=postgresql://..."
ExecStart=/path/to/scraper/venv/bin/python main.py

[Install]
WantedBy=multi-user.target
```

Then create a timer at `/etc/systemd/system/forum-crawler.timer`:
```ini
[Unit]
Description=Run Forum Crawler every 6 hours

[Timer]
OnBootSec=15min
OnUnitActiveSec=6h

[Install]
WantedBy=timers.target
```

Enable:
```bash
sudo systemctl enable forum-crawler.timer
sudo systemctl start forum-crawler.timer
```

## Logging

Logs are written to:
- **stdout**: Console output
- **crawler.log**: File in project directory

Use `--verbose` for debug-level logging.

## Error Handling

- Per-forum isolation: One forum failure doesn't stop others
- Automatic retry logic via rate limiting
- Duplicate prevention: Unique constraint on (forum, keyword, URL)
- Graceful degradation: Multiple parsing strategies

## Production Tips

1. **Database Connection Pooling**: Already configured (5-10 connections)
2. **Rate Limiting**: Start conservative (2-3s), adjust based on forum
3. **Max Pages**: Limit to prevent infinite crawls
4. **Monitoring**: Check `crawler.log` for errors
5. **Backups**: Regular PostgreSQL backups recommended
6. **Proxies**: Add proxy support in `base_crawler.py` if needed

## Troubleshooting

### Database Connection Errors
```bash
# For MySQL - Check if running:
mysqladmin ping

# Verify credentials:
mysql -h localhost -u root -p forum_crawler

# For PostgreSQL:
pg_isready
psql $DATABASE_URL
```

### No Matches Found
- Check keywords are enabled: `SELECT * FROM keywords WHERE enabled = true;`
- Check forums are enabled: `SELECT * FROM forums WHERE enabled = true;`
- Verify start_urls are accessible
- Use `--verbose` to see parsing details

### Parser Issues
- Forum structure may have changed
- Add debug logging to parser
- Test with `beautifulsoup4` in Python REPL

## License

This project is provided as-is for educational and monitoring purposes. Respect forum terms of service and robots.txt when crawling.
