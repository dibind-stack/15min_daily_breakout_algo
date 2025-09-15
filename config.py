# -*- coding: utf-8 -*-
"""
Configuration file for the NoRSI_15Breakout_5R_AdvancedTrailing trading bot.

Store all your sensitive information and strategy parameters here.
"""

# Zerodha API Credentials
API_KEY = "YOUR_API_KEY"
API_SECRET = "YOUR_API_SECRET"
ACCESS_TOKEN = "YOUR_ACCESS_TOKEN"  # Generate this daily or store it securely

# Zerodha Instrument Identifiers
# You can get these from the Kite Connect instruments API call
NIFTY_SPOT_INSTRUMENT_TOKEN = 256265  # Example for NIFTY 50
NIFTY_FUTURES_TRADING_SYMBOL = "NIFTY24SEPFUT"  # Example, should be updated to current month

# Strategy Parameters
RISK_PER_TRADE_PERCENT = 2.0  # 2% of capital at risk per trade
MAX_CAPITAL_ALLOCATION_PERCENT = 50.0  # Use max 50% of capital for a trade
TARGET_RISK_REWARD_RATIO = 5.0  # 5R target

# NIFTY Futures Contract Details
NIFTY_LOT_SIZE = 50  # As of my last update, but verify this

# Telegram Bot for Alerts
TELEGRAM_BOT_TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"
TELEGRAM_CHAT_ID = "YOUR_TELEGRAM_CHAT_ID"

# Logging Configuration
LOG_FILE_PATH = "trading_log.csv"
GOOGLE_SHEET_NAME = "Trading_PnL"  # Optional: for Google Sheets logging

# System Settings
HEARTBEAT_INTERVAL = 30  # In seconds, for checking WebSocket connection
CANDLE_TIME_FRAME = "15minute"
EXCHANGE = "NFO"  # National Stock Exchange of India - Futures and Options
PRODUCT_TYPE = "NRML"  # Normal Margin, for holding positions overnight
ORDER_VARIETY = "REGULAR"  # Regular order

# PnL Guardrail (Optional)
MAX_DAILY_DRAWDOWN_R = -2.5  # Stop trading for the day if loss exceeds -2.5R
