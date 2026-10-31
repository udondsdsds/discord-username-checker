# Discord Multi-Token Username Checker
An asynchronous Discord username availability checker written in Python, designed to work with multiple user tokens and custom generation options.
# ⚠️ Disclaimer (Important)
USE AT YOUR OWN RISK.
This tool is provided for educational and experimental purposes only. Using user tokens (self-bots) to automate requests against the Discord API violates Discord's Terms of Service (ToS). The authors and contributors are not responsible for any account suspensions, bans, or other damages caused by using this software.
Features
Multi-Token Support: Rotate and utilize multiple user tokens seamlessly.
Duplicate Prevention: SQLite-based caching prevents checking the same username for 1 week.
Smart Error Handling: Rate limits (429) and connection errors automatically skip marking usernames as checked so they can be retried later.
Customizable Configuration: Manage intervals, worker counts, and webhook settings easily via Data.txt.
Discord Webhook Notifications: Real-time alerts when an available username is found.
Auto-save: Successfully found available usernames are automatically saved to success.txt.
Random Generation Options:
4-letter alphanumeric
5-letter alphabetic
5-letter numeric
Custom wordlist from file (wordlist.txt)
Setup & Installation
1. Prerequisites
Ensure you have Python 3.8+ installed on your system.
2. Install Dependencies
Run the following command in your terminal to install the required libraries:
pip install aiohttp colorama

# 3. File Setup
Create the following files in your project directory:
main.py (Paste the checker script here)
tokens.txt (Put your Discord user tokens, one per line)
wordlist.txt (Optional) (Put custom words/names, one per line, if you select option 4)
Configuration (Data.txt)
Upon first run, a Data.txt configuration file will be automatically generated. You can modify it to suit your needs without touching the source code:
# Checker Configuration
interval_min = 1.0
interval_max = 3.0
webhook_url = webhook_url
webhook_format = {username}
concurrent_workers = 3

interval_min / interval_max: Random delay range (in seconds) between requests.
webhook_url: Your Discord Webhook URL for success notifications.
webhook_format: Custom message format for webhooks (use {username} as a placeholder).
concurrent_workers: Number of concurrent workers (tokens) running at the same time.
How to Run
Make sure your tokens are listed in tokens.txt (one per line).
Execute the script:
python main.py

Choose your desired username generation mode from the interactive menu:
1: 4-letter Alphanumeric
2: 5-letter Alphabetic
3: 5-letter Numeric
4: file 

The tool will start checking automatically. Press Ctrl + C to stop at any time.
