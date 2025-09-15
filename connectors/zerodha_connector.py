# -*- coding: utf-8 -*-
"""
Zerodha Connector

This module provides a class to connect to Zerodha's Kite Connect API and
handle real-time data streams via WebSocket.
"""

import logging
from kiteconnect import KiteConnect, KiteTicker
from kiteconnect.exceptions import (TokenException, InputException, OrderException,
                                    NetworkException, GeneralException)
from kiteconnect.connect import (TRANSACTION_TYPE_BUY, TRANSACTION_TYPE_SELL,
                                 ORDER_TYPE_MARKET, PRODUCT_NRML, EXCHANGE_NFO,
                                 VARIETY_REGULAR)
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
        except (TokenException, GeneralException) as e:
            logging.error(f"Order placement failed due to an API error: {e}")
            raise  # Re-raise the exception to be handled by the TradeManager
        except (InputException, OrderException) as e:
            logging.error(f"Order placement failed due to invalid input or order rules: {e}")
            raise
        except NetworkException as e:
            logging.error(f"Order placement failed due to a network issue: {e}")
            raise

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

    def get_margins(self):
        """
        Fetches the available capital from the user's account.
        Specifically retrieves the 'net' cash available in the equity segment.
        """
        try:
            margins = self.kite.margins()
            equity_margins = margins.get("equity")
            if equity_margins and 'net' in equity_margins:
                net_cash = equity_margins['net']
                logging.info(f"Successfully fetched account margins. Net cash available: {net_cash}")
                return net_cash
            else:
                logging.error("Could not find 'equity' segment or 'net' cash in margins response.")
                return None
        except (TokenException, GeneralException, NetworkException) as e:
            logging.error(f"Error fetching account margins: {e}")
            return None

    def get_current_nifty_futures_contract(self):
        """
        Fetches the details for the current month's NIFTY futures contract.
        Returns a dictionary with 'tradingsymbol' and 'expiry'.
        """
        try:
            instruments = self.kite.instruments('NFO')
            nifty_futures = [
                ins for ins in instruments
                if ins['name'] == 'NIFTY'
                and ins['instrument_type'] == 'FUT'
            ]

            nifty_futures.sort(key=lambda x: x['expiry'])

            from datetime import date
            today = date.today()
            for future in nifty_futures:
                if future['expiry'] >= today:
                    contract = {
                        'tradingsymbol': future['tradingsymbol'],
                        'expiry': future['expiry']
                    }
                    logging.info(f"Dynamically determined NIFTY futures contract: {contract}")
                    return contract

            logging.error("Could not find an active NIFTY futures contract.")
            return None
        except (TokenException, GeneralException, NetworkException) as e:
            logging.error(f"Error fetching NIFTY futures contract details: {e}")
            return None

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
