# -*- coding: utf-8 -*-
"""
Access Token Generation Helper

This script simplifies the process of generating a daily access token for the
Zerodha Kite Connect API.
"""

import logging
import re
from kiteconnect import KiteConnect
import config

logging.basicConfig(level=logging.INFO)

def generate_token():
    """
    Guides the user through the 2-step process of generating an access token.
    """
    if not config.API_KEY or config.API_KEY == "YOUR_API_KEY" or \
       not config.API_SECRET or config.API_SECRET == "YOUR_API_SECRET":
        logging.error("API_KEY or API_SECRET are not configured in config.py. Please update them first.")
        return

    # --- Step 1: Generate Login URL ---
    kite = KiteConnect(api_key=config.API_KEY)
    login_url = kite.login_url()

    print("\n" + "="*80)
    print("STEP 1: Generate a request_token by logging into Kite.")
    print("Please open the following URL in your web browser:\n")
    print(login_url)
    print("\nAfter successful login, you will be redirected to a URL that may look like:")
    print("https://your-redirect-url.com/?status=success&request_token=YOUR_REQUEST_TOKEN")
    print("="*80)

    # --- Step 2: Get request_token from user and generate access_token ---
    try:
        request_token = input("\nPlease paste the full `request_token` from the redirect URL here and press Enter: ")
    except (KeyboardInterrupt, EOFError):
        logging.info("\nOperation cancelled by user.")
        return

    if not request_token:
        logging.error("request_token cannot be empty.")
        return

    try:
        logging.info("Generating session with the provided request_token...")
        data = kite.generate_session(request_token.strip(), api_secret=config.API_SECRET)
        access_token = data.get("access_token")

        if access_token:
            # Automatically update the config file
            if update_config_file(access_token):
                print("\n" + "="*80)
                print("SUCCESS! `config.py` has been automatically updated with your new access token.")
                print("You are now ready to start the trading bot.")
                print("="*80 + "\n")
            else:
                # Fallback message if auto-update fails
                print("\n" + "="*80)
                print("ACTION REQUIRED: Could not update config file automatically.")
                print("Please copy this access_token and paste it into your `config.py` file")
                print("for the `ACCESS_TOKEN` variable.")
                print("\nACCESS TOKEN:")
                print(access_token)
                print("="*80 + "\n")
        else:
            logging.error("Could not generate access token. The response did not contain one. Full response:")
            print(data)

    except Exception as e:
        logging.error(f"Session generation failed: {e}")
        logging.error("This could be due to an invalid request_token or api_secret.")

def update_config_file(new_token):
    """
    Automatically updates the ACCESS_TOKEN in the config.py file.
    """
    try:
        with open('config.py', 'r') as f:
            content = f.read()

        # Use regex to find and replace the access token line
        # This handles cases where the token is None, empty, or an existing string
        pattern = r"ACCESS_TOKEN\s*=\s*.*"
        replacement = f"ACCESS_TOKEN = \"{new_token}\"  # This was updated automatically"

        new_content = re.sub(pattern, replacement, content, count=1)

        with open('config.py', 'w') as f:
            f.write(new_content)

        logging.info("`config.py` has been automatically updated with the new access token.")
        return True
    except Exception as e:
        logging.error(f"Failed to automatically update config.py: {e}")
        logging.error("Please update the file manually.")
        return False

if __name__ == "__main__":
    generate_token()
