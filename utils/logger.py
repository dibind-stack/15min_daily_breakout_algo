# -*- coding: utf-8 -*-
"""
Logger Utility

This module provides a CSV logger for recording trade activities.
"""

import csv
import os
import logging

class CsvLogger:
    """
    A simple logger to write trade data to a CSV file.
    """
    def __init__(self, file_path, header):
        """
        Initializes the logger.

        :param file_path: Path to the CSV log file.
        :param header: A list of strings representing the CSV header.
        """
        self.file_path = file_path
        self.header = header
        self._initialize_file()

    def _initialize_file(self):
        """
        Creates the log file and writes the header if it doesn't exist.
        """
        if not os.path.exists(self.file_path):
            try:
                with open(self.file_path, 'w', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow(self.header)
                logging.info(f"Log file created at {self.file_path}")
            except IOError as e:
                logging.error(f"Could not create log file: {e}")

    def log(self, data_dict):
        """
        Logs a dictionary of data as a new row in the CSV file.

        :param data_dict: A dictionary where keys match the header.
        """
        try:
            with open(self.file_path, 'a', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=self.header)
                writer.writerow(data_dict)
        except IOError as e:
            logging.error(f"Could not write to log file: {e}")
        except ValueError as e:
            logging.error(f"Data dictionary does not match header: {e}")

# Example Usage (for testing)
if __name__ == '__main__':
    log_header = ['timestamp', 'symbol', 'action', 'price', 'quantity', 'pnl']
    logger = CsvLogger('test_log.csv', log_header)

    logger.log({'timestamp': '2024-09-14 10:00:00', 'symbol': 'NIFTYFUT', 'action': 'BUY', 'price': 22000, 'quantity': 50, 'pnl': 0})
    logger.log({'timestamp': '2024-09-14 11:00:00', 'symbol': 'NIFTYFUT', 'action': 'SELL', 'price': 22100, 'quantity': 50, 'pnl': 5000})

    print("Test log entries written to test_log.csv")
