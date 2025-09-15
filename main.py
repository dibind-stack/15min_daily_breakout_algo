# -*- coding: utf-8 -*-
"""
Main Application File for the Trading Bot
"""

import logging
import time
import pandas as pd
from datetime import datetime, time as dt_time

import config
from connectors.zerodha_connector import ZerodhaConnector
from core.risk_manager import RiskManager
from core.trade_manager import TradeManager
from strategies.no_rsi_breakout import NoRsiBreakoutStrategy
from utils.logger import CsvLogger
from utils.telegram_bot import TelegramBot

# --- Basic Setup ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Global Variables for Tick Data ---
# A list to store ticks for the current, unformed candle
current_interval_ticks = []

def process_candle_data(trade_manager, strategy):
    """
    Processes the collected ticks into a 15-minute candle and acts on it.
    """
    global current_interval_ticks
    if not current_interval_ticks:
        return

    # Create a DataFrame from the collected ticks
    df = pd.DataFrame(current_interval_ticks)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df.set_index('timestamp', inplace=True)

    # Resample to get the latest 15-min OHLC
    # The 'closed' and 'label' args ensure we get candles for intervals like 09:15-09:30
    ohlc = df['price'].resample('15min', closed='right', label='right').ohlc().iloc[-1]

    candle = {
        'timestamp': ohlc.name,
        'open': ohlc.open,
        'high': ohlc.high,
        'low': ohlc.low,
        'close': ohlc.close
    }

    logging.info(f"New 15-min Candle Formed: T={candle['timestamp']}, O={candle['open']}, H={candle['high']}, L={candle['low']}, C={candle['close']}")

    # --- Process the candle ---
    # 1. Check for exits or manage the active trade first
    trade_manager.check_and_manage_trade(candle)

    # 2. If no trade is active, check for a new entry signal
    if not trade_manager.active_trade:
        signal = strategy.process_candle(candle)
        if signal:
            trade_manager.enter_trade(signal)

    # Clear the ticks list for the next interval
    current_interval_ticks = []

def main():
    """
    The main function to run the trading bot.
    """
    logging.info("--- Starting Trading Bot ---")

    # --- 1. Initialization ---
    try:
        zerodha = ZerodhaConnector(api_key=config.API_KEY, api_secret=config.API_SECRET, access_token=config.ACCESS_TOKEN)
        logger = CsvLogger(file_path=config.LOG_FILE_PATH, header=['timestamp', 'action', 'price', 'quantity', 'pnl', 'reason', 'sl', 'target', 'risk_r'])
        telegram = TelegramBot(token=config.TELEGRAM_BOT_TOKEN, chat_id=config.TELEGRAM_CHAT_ID)

        # Fetch available capital from the broker
        initial_capital = zerodha.get_margins()
        if initial_capital is None:
            logging.error("Could not fetch initial capital. Exiting.")
            telegram.send_message("ALERT: Could not fetch account capital. Bot is shutting down.")
            return

        # Fetch the current NIFTY futures trading symbol
        nifty_futures_symbol = zerodha.get_current_nifty_futures_symbol()
        if nifty_futures_symbol is None:
            logging.error("Could not fetch NIFTY futures symbol. Exiting.")
            telegram.send_message("ALERT: Could not fetch NIFTY futures symbol. Bot is shutting down.")
            return
        config.NIFTY_FUTURES_TRADING_SYMBOL = nifty_futures_symbol

        risk_manager = RiskManager(initial_capital=initial_capital)
        strategy = NoRsiBreakoutStrategy()
        trade_manager = TradeManager(zerodha, risk_manager, strategy, logger, telegram)
    except Exception as e:
        logging.error(f"Failed to initialize components: {e}")
        return

    # --- 2. WebSocket and Data Handling ---
    def on_ticks(ws, ticks):
        """
        Callback to handle incoming ticks. It simply appends them to a list.
        """
        global current_interval_ticks
        for tick in ticks:
            if tick['instrument_token'] == config.NIFTY_SPOT_INSTRUMENT_TOKEN:
                current_interval_ticks.append({'timestamp': tick['timestamp'], 'price': tick['last_price']})

    zerodha.initialize_websocket(on_ticks_callback=on_ticks)
    zerodha.connect_websocket()
    zerodha.subscribe_to_instruments([config.NIFTY_SPOT_INSTRUMENT_TOKEN])

    telegram.send_message("Trading Bot is LIVE and listening for data.")
    logging.info("WebSocket connected. Waiting for ticks...")

    # --- 3. Main Loop for Candle Processing ---
    last_processed_minute = -1
    try:
        while True:
            now = datetime.now()
            # Process candles at the end of each 15-minute interval
            if now.minute % 15 == 0 and now.minute != last_processed_minute:
                # Give a few seconds for all ticks of the closing minute to arrive
                time.sleep(3)
                logging.info(f"--- 15-minute boundary ({now.minute}) reached. Processing candle. ---")
                process_candle_data(trade_manager, strategy)
                last_processed_minute = now.minute

            # Reset daily strategy state at the beginning of the day
            if now.time() >= dt_time(9, 0) and now.time() < dt_time(9, 15) and strategy.first_candle_high is not None:
                strategy.day_reset()
                trade_manager.day_reset()

            time.sleep(1) # Main loop sleeps for 1 second
    except KeyboardInterrupt:
        logging.info("--- Shutting Down Trading Bot ---")
        zerodha.stop_websocket()
        telegram.send_message("Trading Bot has been shut down.")

if __name__ == "__main__":
    main()
