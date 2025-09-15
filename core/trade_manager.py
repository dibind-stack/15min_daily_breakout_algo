# -*- coding: utf-8 -*-
"""
Trade Execution and Management

This module provides a class to manage the lifecycle of a trade, from
entry to exit, including stop loss and target management, and PnL guardrails.
"""

import logging
import pandas as pd
import config
from connectors.zerodha_connector import (TRANSACTION_TYPE_BUY, TRANSACTION_TYPE_SELL,
                                          ORDER_TYPE_MARKET)

class TradeManager:
    """
    Manages the execution and lifecycle of a single trade at a time.
    """
    def __init__(self, zerodha_connector, risk_manager, strategy, logger, telegram_bot):
        self.zerodha = zerodha_connector
        self.risk_manager = risk_manager
        self.strategy = strategy
        self.logger = logger
        self.telegram = telegram_bot

        self.day_reset()
        logging.info("TradeManager initialized.")

    def day_reset(self):
        """Resets daily counters and flags."""
        self.active_trade = None
        self.trailing_sl_activated = False
        self.daily_r_pnl = 0.0
        self.trading_stopped_for_day = False
        logging.info("TradeManager state has been reset for the new day.")

    def enter_trade(self, signal):
        """
        Enters a new trade based on a signal from the strategy.
        """
        if self.active_trade:
            logging.warning("Cannot enter a new trade, another is active.")
            return

        if self.trading_stopped_for_day:
            logging.warning(f"Cannot enter new trade, daily loss limit of {config.MAX_DAILY_DRAWDOWN_R}R reached.")
            return

        entry_price = signal['entry_price']
        sl_price = signal['sl_price']

        quantity = self.risk_manager.calculate_quantity(entry_price, sl_price)
        if quantity == 0:
            logging.warning("Calculated quantity is 0. Skipping trade.")
            self.strategy.on_trade_exit() # Reset strategy state
            return

        # --- Place Live Entry Order ---
        try:
            logging.info("Placing live entry order...")
            order_id = self.zerodha.place_order(
                tradingsymbol=config.NIFTY_FUTURES_TRADING_SYMBOL,
                exchange=config.EXCHANGE,
                transaction_type=TRANSACTION_TYPE_BUY,
                quantity=quantity,
                product=config.PRODUCT_TYPE,
                order_type=ORDER_TYPE_MARKET
            )
            logging.info(f"Live entry order placed successfully. Order ID: {order_id}")
        except Exception as e:
            logging.error(f"Failed to place live entry order: {e}")
            self.telegram.send_message(f"ALERT: Failed to place entry order: {e}")
            self.strategy.on_trade_exit() # Reset strategy state
            return

        initial_risk_per_share = entry_price - sl_price
        target_price = entry_price + (initial_risk_per_share * config.TARGET_RISK_REWARD_RATIO)

        self.active_trade = {
            'order_id': order_id,
            'entry_price': entry_price,
            'initial_sl': sl_price,
            'current_sl': sl_price,
            'target_price': target_price,
            'quantity': quantity,
            'initial_risk_per_share': initial_risk_per_share,
            'timestamp': signal['timestamp']
        }
        self.trailing_sl_activated = False

        msg = (f"--- NEW TRADE INITIATED ---\n"
               f"Symbol: {config.NIFTY_FUTURES_TRADING_SYMBOL}\n"
               f"Entry: {entry_price:.2f}\n"
               f"SL: {sl_price:.2f}\n"
               f"Target (5R): {target_price:.2f}\n"
               f"Quantity: {quantity}")
        self.telegram.send_message(msg)
        self.logger.log({'timestamp': signal['timestamp'], 'action': 'ENTER', 'price': entry_price, 'quantity': quantity, 'sl': sl_price, 'target': target_price})

    def check_and_manage_trade(self, current_candle):
        """
        Checks the active trade against the latest candle data for exit conditions.
        """
        if not self.active_trade:
            return

        low_price = current_candle['low']
        high_price = current_candle['high']

        # 1. Check for SL hit
        if low_price <= self.active_trade['current_sl']:
            self.exit_trade(current_candle['timestamp'], self.active_trade['current_sl'], "SL_HIT")
            return

        # 2. Check for Trailing SL activation
        if not self.trailing_sl_activated and high_price >= self.active_trade['target_price']:
            self.trailing_sl_activated = True
            msg = f"--- 5R TARGET HIT --- \nTrade is now in Trailing SL mode. Target was {self.active_trade['target_price']:.2f}"
            self.telegram.send_message(msg)
            logging.info(msg)

        # 3. Manage Trailing SL
        if self.trailing_sl_activated:
            new_sl = low_price
            if new_sl > self.active_trade['current_sl']:
                self.active_trade['current_sl'] = new_sl
                msg = f"--- TSL UPDATED --- \nNew SL is {new_sl:.2f}"
                self.telegram.send_message(msg)
                self.logger.log({'timestamp': current_candle['timestamp'], 'action': 'TSL_UPDATE', 'price': new_sl})
                logging.info(msg)

    def exit_trade(self, timestamp, exit_price, reason):
        """
        Exits the active trade and updates capital and PnL.
        """
        if not self.active_trade:
            return

        # --- Place Live Exit Order ---
        try:
            logging.info(f"Placing live exit order for reason: {reason}")
            exit_order_id = self.zerodha.place_order(
                tradingsymbol=config.NIFTY_FUTURES_TRADING_SYMBOL,
                exchange=config.EXCHANGE,
                transaction_type=TRANSACTION_TYPE_SELL,
                quantity=self.active_trade['quantity'],
                product=config.PRODUCT_TYPE,
                order_type=ORDER_TYPE_MARKET
            )
            logging.info(f"Live exit order placed successfully. Order ID: {exit_order_id}")
        except Exception as e:
            logging.error(f"CRITICAL: Failed to place live exit order: {e}")
            self.telegram.send_message(f"CRITICAL ALERT: FAILED TO EXIT TRADE! REASON: {e}. MANUAL INTERVENTION REQUIRED.")
            # Don't reset state here, so we can try to exit again on the next candle
            return

        pnl = (exit_price - self.active_trade['entry_price']) * self.active_trade['quantity']
        # Calculate PnL in terms of R
        r_pnl = pnl / (self.active_trade['initial_risk_per_share'] * self.active_trade['quantity'])
        self.daily_r_pnl += r_pnl

        msg = (f"--- TRADE EXITED ({reason}) ---\n"
               f"Exit Price: {exit_price:.2f}\n"
               f"PnL: {pnl:.2f} ({r_pnl:.2f}R)\n"
               f"Daily PnL: {self.daily_r_pnl:.2f}R")
        self.telegram.send_message(msg)
        self.logger.log({'timestamp': timestamp, 'action': 'EXIT', 'price': exit_price, 'quantity': self.active_trade['quantity'], 'pnl': pnl, 'reason': reason, 'risk_r': r_pnl})

        # Update capital
        new_capital = self.risk_manager.current_capital + pnl
        self.risk_manager.update_capital(new_capital)

        # Check PnL Guardrail
        if self.daily_r_pnl <= config.MAX_DAILY_DRAWDOWN_R:
            self.trading_stopped_for_day = True
            stop_msg = f"--- TRADING STOPPED --- \nDaily loss limit of {config.MAX_DAILY_DRAWDOWN_R}R reached. No new trades will be taken today."
            self.telegram.send_message(stop_msg)
            logging.warning(stop_msg)

        # Reset state
        self.active_trade = None
        self.trailing_sl_activated = False
        self.strategy.on_trade_exit()

    def handle_gap_down(self, opening_price, timestamp):
        """
        Handles gap-down scenario at market open.
        """
        if self.active_trade and opening_price < self.active_trade['current_sl']:
            logging.warning(f"GAP-DOWN DETECTED! Market open ({opening_price}) is below SL ({self.active_trade['current_sl']}). Exiting at open.")
            self.exit_trade(timestamp, opening_price, "GAP_DOWN_EXIT")
