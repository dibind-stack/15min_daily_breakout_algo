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

> **Note for Interactive Environment Users:** If you are working in an interactive environment (like the one where this bot was created), the code files are already present. You can skip Step 1 and proceed directly to Step 2.

1.  **Clone the repository (if on your local machine):**
    ```bash
    # Replace YOUR_REPOSITORY_URL_HERE with the actual URL of the repository
    git clone YOUR_REPOSITORY_URL_HERE
    cd <repository_directory>
    for e.g. 
    cd ~/documents
    git clone https://github.com/dibind-stack/15min_daily_breakout_algo.git
    cd 15min_daily_breakout_algo
    ```

2.  **Install dependencies:**
    ```bash
    # Step 1: Create a virtual environment (folder name: venv)
    python3 -m venv venv

    # Step 2: Activate it
    source venv/bin/activate

    # Step 3: Install requirements inside this venv
    pip install -r requirements.txt
    ```
    ```
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
- **State Persistence:** The bot saves the state of any active trade to a `trade_state.json` file. This makes the bot resilient to restarts and crashes. If the bot is restarted while a trade is active, it will automatically load the trade's state and continue managing it correctly.
- **Dynamic Futures Symbol:** The bot automatically detects and trades the current month's NIFTY futures contract.
- **Pre-Expiry Risk Management:** The bot will automatically exit any open positions and stop entering new ones a configurable number of days before the contract expires (see `DAYS_BEFORE_EXPIRY_TO_EXIT` in `config.py`). This helps to avoid expiry-day volatility.
- **Capital Scaling:** The bot uses a trailing equity high model to calculate risk, ensuring that profits are compounded while protecting against excessive risk after losses.
- **PnL Guardrail:** It includes a daily PnL guardrail (`MAX_DAILY_DRAWDOWN_R` in `config.py`) to automatically stop trading for the day if losses exceed a specified limit in terms of 'R' (risk units).
- **Google Sheets Logging:** A placeholder for a Google Sheets logger is included in `utils/g_sheets_logger.py`.

## Go-Live Checklist

Before running this bot in a live market with real money, please review the following critical points:

1.  **Daily `access_token` Generation (Manual Step):**
    - The Zerodha `access_token` expires every morning. You **must** generate a new one via the Kite Connect login flow and update it in `config.py` before you start the bot each day. This is the only required manual step for daily operation.

2.  **Start with Paper Trading or Low Capital:**
    - It is highly recommended to first test the bot in a paper trading environment or with a very small amount of capital to ensure everything works as you expect.

3.  **Understand Market Orders & Slippage:**
    - The bot uses `MARKET` orders to ensure trades are executed quickly. In fast-moving markets, this can lead to "slippage," where the price you get is slightly different from the price at the moment the order was placed. This is a normal aspect of live trading.

4.  **Server & Uptime:**
    - For the bot to manage your trades correctly (especially the stop-loss, which is managed in-memory), it must run continuously during market hours. Deploy it on a reliable server or cloud VPS (Virtual Private Server), not on a personal computer that might shut down or lose internet connectivity.

5.  **Bot-Managed Stop-Loss:**
    - **CRITICAL:** The bot manages the stop-loss by watching the price and sending a `MARKET` order if the SL is hit. It does **not** place a pending SL-M order with the broker. If the bot crashes or stops running, your open position will **not** have a stop-loss order protecting it at the exchange. The State Persistence feature helps recover from restarts, but cannot protect against prolonged downtime.

6.  **Disclaimer:**
    - This is a complex piece of software provided for educational purposes. Trading in financial markets involves significant risk. Use this bot at your own risk.
