# -*- coding: utf-8 -*-
"""
Telegram Bot Utility

This module provides a simple interface for sending messages via a Telegram bot.
"""

import telegram
import logging
import config

class TelegramBot:
    """
    A simple wrapper for the python-telegram-bot library to send messages.
    """
    def __init__(self, token, chat_id):
        """
        Initializes the Telegram bot.

        :param token: Your Telegram Bot token.
        :param chat_id: The chat ID to send messages to.
        """
        self.bot = telegram.Bot(token=token)
        self.chat_id = chat_id
        logging.info("TelegramBot initialized.")

    def send_message(self, message):
        """
        Sends a message to the configured chat ID.

        :param message: The text message to send.
        """
        try:
            self.bot.send_message(chat_id=self.chat_id, text=message)
            logging.info(f"Telegram message sent: {message}")
        except Exception as e:
            logging.error(f"Failed to send Telegram message: {e}")

# Example Usage (for testing)
if __name__ == '__main__':
    # Make sure to replace with your actual token and chat_id in config.py for this to work
    if config.TELEGRAM_BOT_TOKEN != "YOUR_TELEGRAM_BOT_TOKEN" and config.TELEGRAM_CHAT_ID != "YOUR_TELEGRAM_CHAT_ID":
        tg_bot = TelegramBot(token=config.TELEGRAM_BOT_TOKEN, chat_id=config.TELEGRAM_CHAT_ID)
        tg_bot.send_message("Hello from your trading bot! System is starting up.")
        print("Test message sent. Check your Telegram.")
    else:
        print("Please configure your Telegram token and chat ID in config.py to test.")
