# -*- coding: utf-8 -*-
"""
Zerodha Connector

This module provides a class to connect to Zerodha's Kite Connect API and
handle real-time data streams via WebSocket.
"""

import logging
from kiteconnect import KiteConnect, KiteTicker
import config

logging.basicConfig(level=logging.INFO)

class ZerodhaConnector:
    """
    Handles all interactions with Zerodha Kite Connect API.
    """
    def __init__(self, api_key, api_secret, access_token):
        """
        Initializes the KiteConnect client.
        """
        self.kite = KiteConnect(api_key=api_key)
        self.kite.set_access_token(access_token)
        self.ticker = None
        logging.info("KiteConnect client initialized.")

    def initialize_websocket(self, on_ticks_callback, on_connect_callback=None, on_close_callback=None):
        """
        Initializes the KiteTicker WebSocket client.
        """
        self.ticker = KiteTicker(config.API_KEY, self.kite.access_token)

        # Assign callbacks
        self.ticker.on_ticks = on_ticks_callback
        self.ticker.on_connect = on_connect_callback if on_connect_callback else self._on_connect
        self.ticker.on_close = on_close_callback if on_close_callback else self._on_close

        logging.info("KiteTicker WebSocket client initialized.")

    def connect_websocket(self):
        """
        Starts the WebSocket connection.
        """
        if self.ticker:
            self.ticker.connect(threaded=True)
            logging.info("WebSocket connection started.")
        else:
            logging.error("WebSocket not initialized. Call initialize_websocket() first.")

    def subscribe_to_instruments(self, instrument_tokens):
        """
        Subscribes to a list of instrument tokens.
        """
        if self.ticker:
            self.ticker.subscribe(instrument_tokens)
            self.ticker.set_mode(self.ticker.MODE_FULL, instrument_tokens)
            logging.info(f"Subscribed to instruments: {instrument_tokens}")
        else:
            logging.error("WebSocket not initialized. Call initialize_websocket() first.")

    def place_order(self, tradingsymbol, exchange, transaction_type, quantity, product, order_type, price=None, trigger_price=None):
        """
        Places an order.
        """
        try:
            order_id = self.kite.place_order(
                variety=config.ORDER_VARIETY,
                exchange=exchange,
                tradingsymbol=tradingsymbol,
                transaction_type=transaction_type,
                quantity=quantity,
                product=product,
                order_type=order_type,
                price=price,
                trigger_price=trigger_price
            )
            logging.info(f"Order placed successfully. Order ID: {order_id}")
            return order_id
        except Exception as e:
            logging.error(f"Error placing order: {e}")
            return None

    def get_historical_data(self, instrument_token, from_date, to_date, interval):
        """
        Fetches historical candle data.
        """
        try:
            records = self.kite.historical_data(instrument_token, from_date, to_date, interval)
            return records
        except Exception as e:
            logging.error(f"Error fetching historical data: {e}")
            return []

    # --- Private WebSocket Callback Handlers ---
    def _on_connect(self, ws, response):
        """
        Default on_connect callback.
        """
        logging.info("WebSocket connected.")
        # You might want to re-subscribe to instruments here if connection drops
        # For simplicity, we assume a stable connection initially.

    def _on_close(self, ws, code, reason):
        """
        Default on_close callback.
        """
        logging.info(f"WebSocket connection closed. Code: {code}, Reason: {reason}")

    def stop_websocket(self):
        """
        Stops the WebSocket connection.
        """
        if self.ticker:
            self.ticker.stop()
            logging.info("WebSocket connection stopped.")
