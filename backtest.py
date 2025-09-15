# -*- coding: utf-8 -*-
"""
Backtesting Engine for the No-RSI Breakout Strategy
"""

import logging
from datetime import datetime
import pandas as pd

import config
from connectors.zerodha_connector import ZerodhaConnector
from core.risk_manager import RiskManager
from core.trade_manager import TradeManager
from strategies.no_rsi_breakout import NoRsiBreakoutStrategy
from utils.logger import CsvLogger
from utils.telegram_bot import TelegramBot

# --- Basic Setup ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def run_backtest():
    """
    Main function to run the backtest.
    """
    logging.info("--- Starting Backtest ---")

    # --- 1. Initialization ---
    # We don't need a live connector or telegram bot for backtesting.
    # We can create mock objects if needed, but for now, we'll pass `None`.
    zerodha = None # No live connection needed
    telegram = None # No alerts needed

    # We will use the CsvLogger to store trade results
    backtest_log_path = "backtest_trades.csv"
    log_header = ['timestamp', 'action', 'price', 'quantity', 'sl', 'target', 'pnl', 'reason', 'risk_r']
    logger = CsvLogger(file_path=backtest_log_path, header=log_header)

    # Initialize core components
    # The capital is set to a high value because the strategy's capital allocation
    # rule (max 50% of capital / entry price) requires it to be > 150 * NIFTY price
    # to allow even a single lot trade.
    initial_capital = 4000000
    risk_manager = RiskManager(initial_capital=initial_capital)
    strategy = NoRsiBreakoutStrategy()

    # We need a dummy trade manager that doesn't try to place real orders
    # For now, we can pass None for the connector and telegram bot
    # but let's create a simple mock telegram bot to avoid errors
    class MockTelegramBot:
        def send_message(self, message):
            pass # Do nothing

    trade_manager = TradeManager(zerodha, risk_manager, strategy, logger, MockTelegramBot())

    logging.info("Backtest components initialized.")

    # --- 2. Fetch Historical Data ---
    zerodha_live = ZerodhaConnector(config.API_KEY, config.API_SECRET, config.ACCESS_TOKEN)

    today = datetime.now()
    from_date = today.replace(year=today.year - 2, month=1, day=1)
    to_date = today.replace(year=today.year, month=12, day=31)

    try:
        logging.info(f"Attempting to fetch historical data from {from_date} to {to_date}...")
        historical_data = zerodha_live.get_historical_data(
            instrument_token=config.NIFTY_SPOT_INSTRUMENT_TOKEN,
            from_date=from_date.strftime('%Y-%m-%d'),
            to_date=to_date.strftime('%Y-%m-%d'),
            interval=config.CANDLE_TIME_FRAME
        )
        if not historical_data:
            raise Exception("No data fetched from API.")

        # Convert to DataFrame
        historical_df = pd.DataFrame(historical_data)
        historical_df['date'] = pd.to_datetime(historical_df['date'])


    except Exception as e:
        logging.warning(f"Could not fetch live historical data: {e}. Falling back to sample CSV.")
        try:
            historical_df = pd.read_csv('nifty_15min_sample.csv')
            historical_df['date'] = pd.to_datetime(historical_df['date'])
            logging.info("Successfully loaded sample data from nifty_15min_sample.csv")
        except FileNotFoundError:
            logging.error("Sample data file not found. Cannot proceed with backtest.")
            return

    historical_df.rename(columns={'date': 'timestamp'}, inplace=True)

    # --- 3. Backtesting Loop ---
    logging.info(f"Starting backtesting loop with {len(historical_df)} candles...")
    last_day = None
    for index, row in historical_df.iterrows():
        candle = row.to_dict()
        current_day = candle['timestamp'].date()

        # Check for the start of a new day to reset daily states
        if last_day and current_day != last_day:
            strategy.day_reset()
            trade_manager.day_reset()
            logging.info(f"--- New Day: {current_day.strftime('%Y-%m-%d')} ---")

        last_day = current_day

        # 1. Handle gap-down scenario for overnight positions
        if trade_manager.active_trade and candle['timestamp'].time() == pd.to_datetime("09:15:00").time():
             trade_manager.handle_gap_down(candle['open'], candle['timestamp'])

        # 2. Check for exits or manage the active trade
        trade_manager.check_and_manage_trade(candle)

        # 3. If no trade is active, check for a new entry signal
        if not trade_manager.active_trade:
            signal = strategy.process_candle(candle)
            if signal:
                trade_manager.enter_trade(signal)

    # --- 4. Generate Results ---
    logging.info("Generating backtest results...")
    generate_report(backtest_log_path, initial_capital)

    logging.info("--- Backtest Finished ---")

def generate_report(log_file_path, initial_capital):
    """
    Reads the trade log and generates a performance report.
    """
    try:
        trades_df = pd.read_csv(log_file_path)
    except FileNotFoundError:
        logging.error("Trade log file not found. No report generated.")
        return

    if trades_df.empty:
        logging.warning("No trades were made during the backtest.")
        return

    exit_trades = trades_df[trades_df['action'] == 'EXIT'].copy()

    if exit_trades.empty:
        logging.info("No trades were closed during the backtest.")
        final_capital = initial_capital
    else:
        total_pnl = exit_trades['pnl'].sum()
        final_capital = initial_capital + total_pnl

        wins = exit_trades[exit_trades['pnl'] > 0]
        losses = exit_trades[exit_trades['pnl'] <= 0]

        num_trades = len(exit_trades)
        num_wins = len(wins)
        num_losses = len(losses)

        win_rate = (num_wins / num_trades) * 100 if num_trades > 0 else 0

        gross_profit = wins['pnl'].sum()
        gross_loss = abs(losses['pnl'].sum())

        profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')

        avg_win = wins['pnl'].mean() if num_wins > 0 else 0
        avg_loss = losses['pnl'].mean() if num_losses > 0 else 0

        print("\n" + "="*50)
        print(" " * 15 + "BACKTEST RESULTS")
        print("="*50)
        print(f" Period: {trades_df['timestamp'].iloc[0]} -> {trades_df['timestamp'].iloc[-1]}")
        print(f" Initial Capital: {initial_capital:,.2f}")
        print("-" * 50)
        print(f" Final Capital:   {final_capital:,.2f}")
        print(f" Total PnL:       {total_pnl:,.2f}")
        print(f" Profit Factor:   {profit_factor:.2f}")
        print("-" * 50)
        print(f" Total Trades:    {num_trades}")
        print(f" Win Rate:        {win_rate:.2f}%")
        print(f" Winning Trades:  {num_wins}")
        print(f" Losing Trades:   {num_losses}")
        print(f" Avg. Win:        {avg_win:,.2f}")
        print(f" Avg. Loss:       {avg_loss:,.2f}")
        print("="*50 + "\n")

    print("--- DETAILED TRADE LOG ---")
    print(trades_df.to_string())


if __name__ == "__main__":
    run_backtest()
