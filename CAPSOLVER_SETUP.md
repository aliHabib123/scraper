# CapSolver Setup for Cloudflare Challenge Bypass

## What is CapSolver?

CapSolver automatically solves Cloudflare Turnstile challenges, reCAPTCHA, and other captchas using AI. This bypasses Cloudflare's "Checking your browser" challenges that block datacenter IPs.

## Installation

### 1. Install CapSolver Package

```bash
# On server
cd /home/scraper/scraper
source venv/bin/activate
pip install capsolver
```

### 2. Get API Key

1. Sign up at [capsolver.com](https://www.capsolver.com/)
2. Add credit to your account (~$0.002 per Cloudflare challenge)
3. Copy your API key from dashboard

### 3. Configure Environment Variable

```bash
# On server
nano ~/.bashrc

# Add this line at the end:
export CAPSOLVER_API_KEY="your-api-key-here"

# Save and reload
source ~/.bashrc
```

Or add to `.env` file:

```bash
cd /home/scraper/scraper
nano .env

# Add:
CAPSOLVER_API_KEY=your-api-key-here
```

## How It Works

1. **Playwright detects Cloudflare challenge** → "Checking your browser..."
2. **Extracts site key** from challenge page
3. **Sends to CapSolver API** → AI solves challenge (~5-10 seconds)
4. **Receives solution token** from CapSolver
5. **Injects token** into page → Challenge bypassed ✓

## Cost

- **Cloudflare Turnstile:** ~$0.002 per challenge (0.2 cents)
- **Budget estimate:** If you hit 100 challenges/day = $0.20/day = $6/month
- **Likely actual cost:** $1-3/month (most pages don't challenge after first success)

## Supported Challenge Types

- ✅ Cloudflare Turnstile (Managed/Non-Interactive)
- ✅ Cloudflare Challenge Page
- ✅ reCAPTCHA v2/v3
- ✅ GeeTest
- ✅ AWS WAF

## Testing

```bash
# Test CapSolver integration
cd /home/scraper/scraper
source venv/bin/activate
export CAPSOLVER_API_KEY="your-key"
python3 test_advanced_bypass.py
```

**Expected output:**
- "CapSolver enabled for automatic Cloudflare challenge solving"
- "Attempting to solve Cloudflare challenge with CapSolver..."
- "✓ Cloudflare challenge solved with CapSolver"

## Fallback

If CapSolver is not available or API key not set:
- Falls back to manual completion (30s wait for non-headless mode)
- Logs warning: "CapSolver not available"

## Monitoring Balance

Check your CapSolver balance:

```python
import capsolver
capsolver.api_key = "your-key"
print(capsolver.balance())
```

## Troubleshooting

**"CapSolver not available"**
- Run: `pip install capsolver`

**"CAPSOLVER_API_KEY not set"**
- Check: `echo $CAPSOLVER_API_KEY`
- Make sure you ran `source ~/.bashrc`

**"Could not extract Cloudflare site key"**
- Challenge page format may have changed
- Check logs for actual challenge type

**"Challenge still present after token injection"**
- Token may be expired/invalid
- Try refreshing the page or checking CapSolver balance
