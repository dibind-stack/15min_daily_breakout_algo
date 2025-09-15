# -*- coding: utf-8 -*-
"""
Risk and Capital Management

This module provides a class to manage risk and calculate position size
based on the strategy's rules, including trailing equity for compounding.
"""

import math
import logging
import config

class RiskManager:
    """
    Calculates trade quantity based on risk and capital parameters.
    Uses a trailing equity high model for capital scaling.
    """
    def __init__(self, initial_capital):
        """
        Initializes the RiskManager.

        :param initial_capital: The starting trading capital.
        """
        self.current_capital = initial_capital
        self.trailing_equity_high = initial_capital
        logging.info(f"RiskManager initialized with Capital: {self.current_capital}, Trailing Equity High: {self.trailing_equity_high}")

    def update_capital(self, new_capital):
        """
        Updates the current capital and the trailing equity high.
        The trailing equity high only increases, never decreases.
        """
        self.current_capital = new_capital
        if self.current_capital > self.trailing_equity_high:
            self.trailing_equity_high = self.current_capital
            logging.info(f"Capital updated. New Current: {self.current_capital:.2f}, New Trailing High: {self.trailing_equity_high:.2f}")
        else:
            logging.info(f"Capital updated. New Current: {self.current_capital:.2f}, Trailing High remains: {self.trailing_equity_high:.2f}")

    def calculate_quantity(self, entry_price, sl_price):
        """
        Calculates the quantity to trade based on the defined risk rules,
        using the trailing equity high for risk calculation.

        :param entry_price: The intended entry price of the trade.
        :param sl_price: The stop-loss price for the trade.
        :return: The calculated quantity (integer), rounded down to the lot size.
        """
        if entry_price <= sl_price:
            logging.error("Entry price must be <= SL price for a long trade.")
            return 0

        # Use trailing equity high for risk calculation
        capital_for_risk = self.trailing_equity_high

        # 1. Calculate Risk Amount
        risk_amount_per_trade = capital_for_risk * (config.RISK_PER_TRADE_PERCENT / 100.0)

        # 2. Calculate SL Distance
        sl_distance_per_share = entry_price - sl_price
        if sl_distance_per_share <= 0:
            return 0

        # 3. Calculate Initial Quantity based on risk
        quantity_by_risk = risk_amount_per_trade / sl_distance_per_share

        # 4. Calculate Quantity Cap based on capital allocation (using current capital)
        max_capital_for_trade = self.current_capital * (config.MAX_CAPITAL_ALLOCATION_PERCENT / 100.0)
        quantity_by_capital = max_capital_for_trade / entry_price

        # 5. Determine final quantity
        final_quantity = min(quantity_by_risk, quantity_by_capital)

        # 6. Round down to the nearest lot size
        lot_size = config.NIFTY_LOT_SIZE
        calculated_quantity = math.floor(final_quantity / lot_size) * lot_size if lot_size > 0 else 0

        logging.info("Quantity Calculation:")
        logging.info(f"  - Capital for Risk (Trailing High): {capital_for_risk:.2f}")
        logging.info(f"  - Risk Amount: {risk_amount_per_trade:.2f}")
        logging.info(f"  - SL Distance: {sl_distance_per_share:.2f}")
        logging.info(f"  - Qty by Risk: {quantity_by_risk:.2f}")
        logging.info(f"  - Qty by Capital: {quantity_by_capital:.2f}")
        logging.info(f"  - Final Raw Qty: {final_quantity:.2f}")
        logging.info(f"  - Rounded Qty (Lot Size {lot_size}): {calculated_quantity}")

        return int(calculated_quantity)

# Example Usage
if __name__ == '__main__':
    config.NIFTY_LOT_SIZE = 50
    capital = 100000
    risk_manager = RiskManager(initial_capital=capital)

    # Profitable trade
    risk_manager.update_capital(105000) # PnL = +5000
    qty = risk_manager.calculate_quantity(22050, 22000)
    print(f"Calculated Qty after profit: {qty}") # Should use 105k for risk
    assert risk_manager.trailing_equity_high == 105000

    # Losing trade
    risk_manager.update_capital(102000) # PnL = -3000
    qty = risk_manager.calculate_quantity(22150, 22100)
    print(f"Calculated Qty after loss: {qty}") # Should still use 105k for risk
    assert risk_manager.trailing_equity_high == 105000
    assert risk_manager.current_capital == 102000
