# -*- coding: utf-8 -*-
"""
State Manager Utility

This module provides functions to save and load the bot's state to/from a JSON file,
ensuring that the bot can recover its state after a restart.
"""

import json
import logging
import os
import pandas as pd

STATE_FILE_PATH = "trade_state.json"

class DateTimeEncoder(json.JSONEncoder):
    """
    A custom JSON encoder to handle datetime objects, which are not
    natively serializable.
    """
    def default(self, obj):
        if isinstance(obj, (pd.Timestamp, pd.Timedelta)):
            return obj.isoformat()
        if isinstance(obj, (pd.NaT.__class__)):
            return None
        return json.JSONEncoder.default(self, obj)

def save_state(state):
    """
    Saves the given state dictionary to the JSON state file.

    :param state: The dictionary representing the current state (e.g., the active trade).
                  If None, the state file is deleted.
    """
    if state is None:
        if os.path.exists(STATE_FILE_PATH):
            try:
                os.remove(STATE_FILE_PATH)
                logging.info("State file removed, trade is closed.")
            except OSError as e:
                logging.error(f"Error removing state file: {e}")
        return

    try:
        with open(STATE_FILE_PATH, 'w') as f:
            json.dump(state, f, indent=4, cls=DateTimeEncoder)
        logging.info(f"Successfully saved state to {STATE_FILE_PATH}")
    except (IOError, TypeError) as e:
        logging.error(f"Failed to save state: {e}")

def load_state():
    """
    Loads the state dictionary from the JSON state file.

    :return: The state dictionary if the file exists, otherwise None.
    """
    if not os.path.exists(STATE_FILE_PATH):
        logging.info("No state file found. Starting with a clean state.")
        return None

    try:
        with open(STATE_FILE_PATH, 'r') as f:
            state = json.load(f)
            # Convert timestamp strings back to datetime objects
            if state and 'timestamp' in state:
                state['timestamp'] = pd.to_datetime(state['timestamp'])
            logging.info(f"Successfully loaded state from {STATE_FILE_PATH}")
            return state
    except (IOError, json.JSONDecodeError) as e:
        logging.error(f"Failed to load state, starting fresh: {e}")
        return None

# Example Usage (for testing)
if __name__ == '__main__':
    # Test saving a state
    test_trade = {
        'order_id': 'test_order_123',
        'entry_price': 22000,
        'current_sl': 21950,
        'quantity': 75,
        'timestamp': pd.to_datetime('now')
    }
    save_state(test_trade)

    # Test loading the state
    loaded_trade = load_state()
    print("Loaded State:")
    print(loaded_trade)
    assert loaded_trade['order_id'] == 'test_order_123'
    assert isinstance(loaded_trade['timestamp'], pd.Timestamp)

    # Test clearing the state
    save_state(None)
    assert load_state() is None
    print("\nState cleared and verified.")
