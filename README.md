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

4.  **Run the bot:**
    ```bash
    python main.py
    ```

The bot will initialize, connect to the Zerodha WebSocket, and start listening for NIFTY Spot ticks. It will automatically form 15-minute candles and apply the strategy rules to manage trades.

## Important Notes

- **Access Token:** The Zerodha `ACCESS_TOKEN` needs to be generated daily. You will need to update it in `config.py` before running the bot each day.
- **Simulation:** The current implementation simulates order placement. To make it live, you will need to uncomment the `place_order` calls in `core/trade_manager.py` and ensure your Zerodha account has the necessary permissions and funds.
## Additional Features

- **Capital Scaling:** The bot uses a trailing equity high model to calculate risk, ensuring that profits are compounded while protecting against excessive risk after losses.
- **PnL Guardrail:** It includes a daily PnL guardrail (`MAX_DAILY_DRAWDOWN_R` in `config.py`) to automatically stop trading for the day if losses exceed a specified limit in terms of 'R' (risk units).
- **Google Sheets Logging:** A placeholder for a Google Sheets logger is included in `utils/g_sheets_logger.py`. This can be implemented to provide cloud-based logging of trades.

## Important Notes

- **Access Token:** The Zerodha `ACCESS_TOKEN` needs to be generated daily. You will need to update it in `config.py` before running the bot each day.
- **Live Trading:** The order placement in `core/trade_manager.py` is **simulated**. To enable live trading, you must implement the call to your broker's API for placing orders.
- **Disclaimer:** This is a sample implementation for educational purposes. Trading in financial markets involves significant risk. Use this bot at your own risk.
