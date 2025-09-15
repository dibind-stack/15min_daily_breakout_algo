# -*- coding: utf-8 -*-
"""
NoRSI_15Breakout_5R_AdvancedTrailing Strategy

This module contains the core logic for the breakout strategy.
"""

import logging
import pandas as pd
from datetime import time

class NoRsiBreakoutStrategy:
    """
    Implements the logic for the No-RSI 15-min Breakout strategy.
    """
    def __init__(self):
        self.first_candle_high = None
        self.trade_active = False
        self.day_reset()
        logging.info("NoRsiBreakoutStrategy initialized.")

    def day_reset(self):
        """
        Resets the state for a new trading day.
        """
        self.first_candle_high = None
        logging.info("Strategy state reset for a new day.")

    def process_candle(self, candle):
        """
        Processes a new 15-minute candle to check for entry signals.

        :param candle: A dictionary or object with 'timestamp', 'open', 'high', 'low', 'close'.
        :return: A dictionary with signal info if a trade should be initiated, otherwise None.
        """
        candle_time = candle['timestamp'].time()

        # Reset at the start of a new day
        if candle_time < time(9, 15):
            self.day_reset()
            return None

        # 1. Identify and store the high of the first 15-min candle of the day
        if self.first_candle_high is None:
            # The first candle processed after the daily reset is considered the first candle.
            # The main loop ensures a day_reset() happens before 9:15.
            # We confirm it's the 9:30 candle to be safe.
            if candle_time == time(9, 30):
                self.first_candle_high = candle['high']
                logging.info(f"First 15-min candle of the day processed. High: {self.first_candle_high}")
                return None
            else:
                # Ignore candles before the official first candle is set
                return None

        # 2. Check for entry signal if the first candle is set and no trade is active
        if self.first_candle_high is not None and not self.trade_active:
            if candle['close'] > self.first_candle_high:
                logging.info(f"--- ENTRY SIGNAL ---")
                logging.info(f"Breakout detected at {candle['timestamp']}.")
                logging.info(f"Close ({candle['close']}) > First Candle High ({self.first_candle_high})")

                self.trade_active = True # Mark that a trade is now active

                return {
                    'signal': 'LONG',
                    'entry_price': candle['close'],
                    'sl_price': candle['low'],
                    'timestamp': candle['timestamp']
                }

        return None

    def on_trade_exit(self):
        """
        Callback to be called when an active trade is exited.
        This allows the strategy to look for new trades.
        """
        self.trade_active = False
        logging.info("Strategy state updated: Trade exited. Ready for new signals.")

# Example Usage (for testing)
if __name__ == '__main__':
    strategy = NoRsiBreakoutStrategy()

    # Simulate a trading day
    mock_candles = [
        {'timestamp': pd.to_datetime('2024-09-14 09:30:00'), 'open': 22000, 'high': 22050, 'low': 21980, 'close': 22040},
        {'timestamp': pd.to_datetime('2024-09-14 09:45:00'), 'open': 22040, 'high': 22060, 'low': 22030, 'close': 22055},
        {'timestamp': pd.to_datetime('2024-09-14 10:00:00'), 'open': 22055, 'high': 22080, 'low': 22050, 'close': 22075},
    ]

    print("--- Simulating Day 1 ---")
    # Process first candle
    signal = strategy.process_candle(mock_candles[0])
    assert signal is None
    print(f"First candle high set to: {strategy.first_candle_high}")

    # Process second candle (breakout)
    signal = strategy.process_candle(mock_candles[1])
    if signal:
        print(f"Trade signal generated: {signal}")
        assert signal['signal'] == 'LONG'
        assert strategy.trade_active is True
    else:
        print("No signal.")

    # Process third candle (should do nothing as trade is active)
    signal = strategy.process_candle(mock_candles[2])
    print(f"Signal on 3rd candle: {signal}")
    assert signal is None

    # Simulate trade exit
    strategy.on_trade_exit()
    print("Trade exited. Strategy is now looking for new signals.")
    assert strategy.trade_active is False

    # Process third candle again (should trigger now)
    signal = strategy.process_candle(mock_candles[2])
    if signal:
        print(f"New trade signal generated after exit: {signal}")
        assert signal['signal'] == 'LONG'
    else:
        print("No signal.")
