#!/usr/bin/env python3
"""
Test Telegram bot configuration.

Usage:
    python test_telegram.py
"""

from notifier import TelegramNotifier
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

print("=" * 60)
print("TELEGRAM BOT TEST")
print("=" * 60)
print()

notifier = TelegramNotifier()
notifier.test_connection()

print()
print("=" * 60)
