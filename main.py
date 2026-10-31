import asyncio
import random
import string
import sys
import os
import aiohttp
from datetime import datetime, timedelta
import sqlite3
from colorama import init, Fore, Style

init(autoreset=True)

DB_FILE = "checked.db"
CONFIG_FILE = "Data.txt"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS checked_names (
            name TEXT PRIMARY KEY,
            timestamp TEXT
        )
    """)
    conn.commit()
    conn.close()

def is_recently_checked(name):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT timestamp FROM checked_names WHERE name = ?", (name,))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        checked_time = datetime.fromisoformat(row[0])
        if datetime.now() - checked_time < timedelta(weeks=1):
            return True
    return False

def mark_as_checked(name):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO checked_names (name, timestamp) VALUES (?, ?)", 
                   (name, datetime.now().isoformat()))
    conn.commit()
    conn.close()

def load_config():
    config = {
        "interval_min": 1.0,
        "interval_max": 3.0,
        "webhook_url": "",
        "webhook_format": "{username}",
        "concurrent_workers": 3
    }
    
    if not os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            f.write("interval_min = 1.0\n")
            f.write("interval_max = 3.0\n")
            f.write("webhook_url = \n")
            f.write("webhook_format = {username}\n")
            f.write("concurrent_workers = 3\n")
        return config

    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                key, val = line.split("=", 1)
                key = key.strip()
                val = val.strip()
                if key == "interval_min":
                    try: config["interval_min"] = float(val)
                    except: pass
                elif key == "interval_max":
                    try: config["interval_max"] = float(val)
                    except: pass
                elif key == "webhook_url":
                    config["webhook_url"] = val
                elif key == "webhook_format":
                    config["webhook_format"] = val
                elif key == "concurrent_workers":
                    try: config["concurrent_workers"] = int(val)
                    except: pass
    return config

async def send_webhook(config, username):
    webhook_url = config["webhook_url"]
    if not webhook_url:
        return
    
    content = config["webhook_format"].replace("{username}", username)
    payload = {"content": content}
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(webhook_url, json=payload) as resp:
                pass
        except Exception:
            pass

def generate_username(mode, wordlist):
    if mode == "1": 
        chars = string.ascii_lowercase + string.digits
        return "".join(random.choices(chars, k=4))
    elif mode == "2": 
        chars = string.ascii_lowercase
        return "".join(random.choices(chars, k=5))
    elif mode == "3":
        chars = string.digits
        return "".join(random.choices(chars, k=5))
    elif mode == "4": 
        if wordlist:
            return random.choice(wordlist).strip()
        else:
            return "".join(random.choices(string.ascii_lowercase, k=5))
    return "".join(random.choices(string.ascii_lowercase, k=5))

async def worker(token_queue, config, mode, wordlist):
    min_wait = config["interval_min"]
    max_wait = config["interval_max"]
    
    async with aiohttp.ClientSession() as session:
        while True:
            await asyncio.sleep(random.uniform(min_wait, max_wait))

            token = await token_queue.get()
            
            username = generate_username(mode, wordlist)
            
            if is_recently_checked(username):
                token_queue.put_nowait(token) 
                continue
                
            try:
                payload = {"username": username}
                async with session.post("https://discord.com/api/v9/users/@me/pomelo-attempt", headers={"Authorization": token}, json=payload) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        taken = data.get("taken", True)
                        
                        if not taken:
                            print(f"{Fore.GREEN}[AVAILABLE] @{username}{Style.RESET_ALL}")
                            with open("success.txt", "a", encoding="utf-8") as f:
                                f.write(f"{username}\n")
                            mark_as_checked(username)
                            await send_webhook(config, username)
                        else:
                            print(f"{Fore.RED}[TAKEN] @{username}{Style.RESET_ALL}")
                            mark_as_checked(username)
                    elif resp.status == 429:
                        print(f"{Fore.YELLOW}[RATE LIMIT] @{username}{Style.RESET_ALL}")
                        await asyncio.sleep(5)
                    else:
                        print(f"{Fore.YELLOW}[ERROR/STATUS {resp.status}] @{username}{Style.RESET_ALL}")
            except Exception as e:
                print(f"{Fore.YELLOW}[EXCEPTION] @{username} - {e}{Style.RESET_ALL}")
            finally:
                token_queue.put_nowait(token)

async def main():
    init_db()
    
    config = load_config()
    print(f"{Fore.CYAN}Config loaded successfully (Interval: {config['interval_min']}~{config['interval_max']}s){Style.RESET_ALL}")
    
    if not os.path.exists("tokens.txt"):
        print(f"{Fore.RED}tokens.txt not found.{Style.RESET_ALL}")
        return
        
    with open("tokens.txt", "r", encoding="utf-8") as f:
        tokens = [line.strip() for line in f if line.strip()]
        
    if not tokens:
        print(f"{Fore.RED}No valid tokens found in tokens.txt{Style.RESET_ALL}")
        return

    print(f"{Fore.GREEN}Loaded tokens: {len(tokens)}{Style.RESET_ALL}")
    
    print("\n--- Select Generation Mode ---")
    print("1: 4-letterAlphanumeric")
    print("2: 5-letterAlphabetic")
    print("3: 5-letterNumeric")
    print("4: file")
    mode = input("Select (1-4): ").strip()
    
    wordlist = []
    if mode == "4":
        if os.path.exists("wordlist.txt"):
            with open("wordlist.txt", "r", encoding="utf-8") as f:
                wordlist = [line.strip() for line in f if line.strip()]
        else:
            print(f"{Fore.RED}wordlist.txt not found. Falling back to default (3: 5-letter Numeric).{Style.RESET_ALL}")
            mode = "3"

    print(f"\n{Fore.CYAN}Starting checker... (Press Ctrl+C to stop){Style.RESET_ALL}\n")

    token_queue = asyncio.Queue()
    for token in tokens:
        await token_queue.put(token)
    
    worker_count = min(config["concurrent_workers"], len(tokens))
    
    tasks = []
    for _ in range(worker_count):
        task = asyncio.create_task(worker(token_queue, config, mode, wordlist))
        tasks.append(task)
        
    await asyncio.gather(*tasks)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}Checker stopped by user.{Style.RESET_ALL}")
