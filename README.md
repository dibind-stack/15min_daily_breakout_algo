# No-RSI 15-Minute Breakout Trading Bot

This project is a Python-based automated trading bot that implements the "NoRSI_15Breakout_5R_AdvancedTrailing" strategy for the NIFTY Spot Index and executes trades on NIFTY Monthly Futures.

## Strategy Overview

- **Signal Instrument:** NIFTY Spot Index (15-min candles)
- **Execution Instrument:** NIFTY Monthly Futures
- **Entry:** Go long if a 15-min candle closes above the high of the first 15-min candle of the day (09:15 - 09:30 IST).
- **Exit:**
    - **Initial SL:** Low of the breakout candle.
    - **Target:** 5R (Risk:Reward = 1:5).
    - **Trailing SL:** Once the 5R target is hit, the SL is trailed to the low of each new 15-min candle.
- **Risk Management:**
    - **Risk per Trade:** 2% of capital.
    - **Max Capital Allocation:** 50% of capital per trade.
    - **Quantity:** Rounded down to the nearest lot size.

## Project Structure

The project is organized into the following directories:

- `connectors/`: Handles connection to the broker's API (Zerodha Kite Connect).
- `core/`: Contains the main logic for trade management and risk management.
- `strategies/`: Implements the trading strategy logic.
- `utils/`: Provides utility functions for logging and notifications (Telegram).
- `main.py`: The main entry point to run the bot.
- `config.py`: Configuration file for API keys, strategy parameters, etc.
- `requirements.txt`: Lists the Python dependencies.

## How to Set Up and Run

1.  **Clone the repository:**
    ```bash
    git clone <repository_url>
    cd <repository_directory>
    ```

2.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Configure the bot:**
    - Open `config.py` and fill in your details:
        - Zerodha `API_KEY`, `API_SECRET`, and `ACCESS_TOKEN`.
        - The correct `NIFTY_SPOT_INSTRUMENT_TOKEN` and `NIFTY_FUTURES_TRADING_SYMBOL`.
        - Your `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID`.
        - Adjust `NIFTY_LOT_SIZE` if it has changed.

4.  **Run the Live Trading Bot:**
    ```bash
    python main.py
    ```

## Backtesting

To backtest the strategy on historical data, use the `backtest.py` script.

**Running with Your Own Data:**

You can run the backtest on your own historical data file by using the `--data` command-line argument.

1.  **Prepare your data file:**
    - The CSV file must contain the following columns: `date`, `open`, `high`, `low`, `close`.
    - The `date` column should have timestamps in a format that pandas can recognize (e.g., `YYYY-MM-DD HH:MM:SS`).

2.  **Run the backtest script:**
    ```bash
    python backtest.py --data /path/to/your/data.csv
    ```

If you don't provide a data file, it will automatically run on the included `nifty_15min_sample.csv` file.

The bot will initialize, connect to the Zerodha WebSocket, and start listening for NIFTY Spot ticks. It will automatically form 15-minute candles and apply the strategy rules to manage trades.

## Additional Features

- **Dynamic Capital:** At startup, the bot automatically fetches your available capital from your Zerodha account.
- **Dynamic Futures Symbol:** The bot automatically detects and trades the current month's NIFTY futures contract. You no longer need to change the symbol in `config.py` every month.
- **Capital Scaling:** The bot uses a trailing equity high model to calculate risk, ensuring that profits are compounded while protecting against excessive risk after losses.
- **PnL Guardrail:** It includes a daily PnL guardrail (`MAX_DAILY_DRAWDOWN_R` in `config.py`) to automatically stop trading for the day if losses exceed a specified limit in terms of 'R' (risk units).
- **Google Sheets Logging:** A placeholder for a Google Sheets logger is included in `utils/g_sheets_logger.py`.

## Important Notes for a Fully Automated Run

- **The `access_token` is the ONLY manual step:** For the bot to be fully automated, one piece requires daily manual intervention. The Zerodha `ACCESS_TOKEN` expires each day. You must generate a new one and update it in `config.py` before starting the bot for the day.
- **Live Trading Enabled:** The bot is now configured to place live orders with Zerodha. Please ensure your API keys in `config.py` are correct and you have sufficient funds before running `main.py`.
- **Bot-Managed Stop-Loss:** It is critical to understand that this bot manages the stop-loss internally. It does **not** place a Stop-Loss (SL-M) order with the broker. Instead, it monitors the price and places a MARKET order if the stop-loss level is breached. This means you must have the bot running for your stop-loss to be active.
- **Disclaimer:** This is a sample implementation for educational purposes. Trading in financial markets involves significant risk. Use this bot at your own risk.
