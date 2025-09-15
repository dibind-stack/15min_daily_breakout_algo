# -*- coding: utf-8 -*-
"""
Backtesting Engine for the No-RSI Breakout Strategy
"""

import logging
from datetime import datetime
import pandas as pd
import argparse

import config
from connectors.zerodha_connector import ZerodhaConnector
from core.risk_manager import RiskManager
from core.trade_manager import TradeManager
from strategies.no_rsi_breakout import NoRsiBreakoutStrategy
from utils.logger import CsvLogger

# --- Basic Setup ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def run_backtest(data_file_path):
    """
    Main function to run the backtest.
    :param data_file_path: Path to the historical data CSV file.
    """
    logging.info("--- Starting Backtest ---")

    # --- 1. Initialization ---
    zerodha = None # No live connection needed
    class MockTelegramBot:
        def send_message(self, message): pass # Do nothing

    backtest_log_path = "backtest_trades.csv"
    log_header = ['timestamp', 'action', 'price', 'quantity', 'sl', 'target', 'pnl', 'reason', 'risk_r']
    logger = CsvLogger(file_path=backtest_log_path, header=log_header)

    initial_capital = 1200000
    risk_manager = RiskManager(initial_capital=initial_capital)
    strategy = NoRsiBreakoutStrategy()
    from datetime import date, timedelta
    dummy_expiry_date = date.today() + timedelta(days=365)
    trade_manager = TradeManager(zerodha, risk_manager, strategy, logger, MockTelegramBot(),
                                 expiry_date=dummy_expiry_date, backtest_mode=True)

    logging.info("Backtest components initialized.")

    # --- 2. Load Historical Data ---
    try:
        logging.info(f"Loading historical data from: {data_file_path}")
        historical_df = pd.read_csv(data_file_path)
        # Assuming the CSV has columns: 'date', 'open', 'high', 'low', 'close'
        historical_df['date'] = pd.to_datetime(historical_df['date'])
        historical_df.rename(columns={'date': 'timestamp'}, inplace=True)
        logging.info(f"Successfully loaded {len(historical_df)} candles.")
    except FileNotFoundError:
        logging.error(f"Data file not found at '{data_file_path}'. Please check the path.")
        return
    except Exception as e:
        logging.error(f"Error loading data file: {e}")
        return

    # --- 3. Backtesting Loop ---
    logging.info("Starting backtesting loop...")
    last_day = None
    for index, row in historical_df.iterrows():
        candle = row.to_dict()
        current_day = candle['timestamp'].date()

        if last_day and current_day != last_day:
            strategy.day_reset()
            trade_manager.day_reset()
            logging.info(f"--- New Day: {current_day.strftime('%Y-%m-%d')} ---")

        last_day = current_day

        if trade_manager.active_trade and candle['timestamp'].time() == pd.to_datetime("09:15:00").time():
             trade_manager.handle_gap_down(candle['open'], candle['timestamp'])

        trade_manager.check_and_manage_trade(candle)

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
    parser = argparse.ArgumentParser(description="Backtest the No-RSI Breakout Strategy.")
    parser.add_argument(
        '--data',
        type=str,
        help="Path to the historical data CSV file.",
        default='nifty_15min_sample.csv' # Default to sample file
    )
    args = parser.parse_args()

    run_backtest(data_file_path=args.data)
