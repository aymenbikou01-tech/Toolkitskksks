import os
import sys
import time
import shutil
import subprocess
import re
import importlib
from pathlib import Path

# =========================================================
# COLORAMA
# =========================================================
try:
    from colorama import init, Fore, Style
    init(autoreset=True)
    BLACK   = Fore.BLACK
    RED     = Fore.RED
    GREEN   = Fore.GREEN
    CYAN    = Fore.CYAN
    YELLOW  = Fore.YELLOW
    MAGENTA = Fore.MAGENTA
    BLUE    = Fore.BLUE
    WHITE   = Fore.WHITE
    RESET   = Style.RESET_ALL
    BOLD    = Style.BRIGHT
except ImportError:
    BLACK = RED = GREEN = CYAN = YELLOW = MAGENTA = BLUE = WHITE = ""
    RESET = BOLD = ""


# =========================================================
# PATHS
# =========================================================
BASE_DIR     = Path(__file__).resolve().parent
TOOLS_DIR    = BASE_DIR / "Polli"
REQUIREMENTS = BASE_DIR / "requirements.txt"


# =========================================================
# TERMINAL HELPERS
# =========================================================
def term_width(default=80):
    try:
        return shutil.get_terminal_size((default, 24)).columns
    except Exception:
        return default


def strip_ansi(text):
    return re.sub(r"\033\[[0-9;]*m", "", text)


def visible_len(text):
    return len(strip_ansi(text))


def center_text(text, width):
    clean_len = visible_len(text)
    pad = max(0, width - clean_len)
    left = pad // 2
    right = pad - left
    return " " * left + text + " " * right


# =========================================================
# VENV DETECTION
# =========================================================
def find_venv():
    candidates = [
        BASE_DIR / "virtualEnv",
        BASE_DIR / "venv",
        BASE_DIR / ".venv",
        BASE_DIR / "env",
    ]

    if os.name == "nt":
        bin_subdir   = "Scripts"
        python_names = ["python.exe", "python3.exe"]
        pip_names    = ["pip.exe", "pip3.exe"]
    else:
        bin_subdir   = "bin"
        python_names = ["python", "python3"]
        pip_names    = ["pip", "pip3"]

    for venv_dir in candidates:
        if not venv_dir.is_dir():
            continue
        bin_dir = venv_dir / bin_subdir
        if not bin_dir.is_dir():
            continue
        python_path = next(
            (bin_dir / n for n in python_names if (bin_dir / n).is_file()),
            None
        )
        pip_path = next(
            (bin_dir / n for n in pip_names if (bin_dir / n).is_file()),
            None
        )
        if python_path:
            return venv_dir, python_path, pip_path

    return None, None, None


VENV_DIR, VENV_PYTHON, VENV_PIP = find_venv()


def venv_available():
    return VENV_DIR is not None and VENV_PYTHON is not None


# =========================================================
# REQUIREMENTS AUTO-INSTALL
# =========================================================
def _get_pip_cmd():
    if VENV_PIP and VENV_PIP.is_file():
        return [str(VENV_PYTHON), "-m", "pip"]
    return [sys.executable, "-m", "pip"]


def _parse_requirement(line):
    line = line.strip()
    if not line or line.startswith("#"):
        return None, None, None
    if " #" in line:
        line = line.split(" #")[0].strip()

    marker = None
    if ";" in line:
        line, marker = line.split(";", 1)
        line = line.strip()
        marker = marker.strip()

    match = re.match(r"^([A-Za-z0-9_\-\.]+)\s*(.*)$", line)
    if not match:
        return None, None, None
    return match.group(1), match.group(2).strip(), marker


def _marker_matches(marker):
    if not marker:
        return True
    try:
        from packaging.markers import Marker
        return Marker(marker).evaluate()
    except Exception:
        m = marker.lower()
        if "sys_platform" in m:
            if "win32" in m and os.name != "nt":
                return False
            if "linux" in m and not sys.platform.startswith("linux"):
                return False
            if "darwin" in m and sys.platform != "darwin":
                return False
        return True


def _pkg_installed(pkg_name):
    aliases = {
        "pyreadline3": "pyreadline3",
        "secure-smtplib": "secure_smtplib",
        "python-dotenv": "dotenv",
        "pillow": "PIL",
        "beautifulsoup4": "bs4",
        "scikit-learn": "sklearn",
        "opencv-python": "cv2",
    }
    candidates = [
        aliases.get(pkg_name.lower(), pkg_name),
        pkg_name.replace("-", "_"),
        pkg_name,
    ]
    for name in candidates:
        try:
            importlib.import_module(name)
            return True
        except ImportError:
            continue
    return False


def ensure_requirements():
    print(f"\n{CYAN}{BOLD}[i] Checking requirements...{RESET}\n")

    if not REQUIREMENTS.is_file():
        print(f"{YELLOW}[~] requirements.txt not found — skipping.{RESET}\n")
        return True

    try:
        with open(REQUIREMENTS, "r", encoding="utf-8") as f:
            lines = f.readlines()
    except Exception as e:
        print(f"{RED}[✗] Cannot read requirements.txt: {e}{RESET}\n")
        return False

    importlib.invalidate_caches()

    missing = []
    for raw in lines:
        pkg, spec, marker = _parse_requirement(raw)
        if not pkg:
            continue
        if not _marker_matches(marker):
            continue
        if not _pkg_installed(pkg):
            missing.append((pkg, spec))

    if not missing:
        print(f"{GREEN}[✓] All requirements are installed.{RESET}\n")
        return True

    print(f"{YELLOW}[~] Missing packages ({len(missing)}):{RESET}")
    for pkg, spec in missing:
        print(f"     {RED}✗{RESET} {pkg}{spec}")
    print()

    try:
        answer = input(
            f"{CYAN}[?] Install missing packages now? [Y/n]: {RESET}"
        ).strip().lower()
    except (EOFError, KeyboardInterrupt):
        print()
        return False

    if answer and answer not in ("y", "yes"):
        print(f"{YELLOW}[~] Skipped. Tool may not work properly.{RESET}\n")
        return False

    pip_cmd = _get_pip_cmd()
    failed  = []

    for pkg, spec in missing:
        target = f"{pkg}{spec}"
        print(f"\n{CYAN}[i] Installing:{RESET} {WHITE}{target}{RESET}")
        try:
            result = subprocess.run(
                pip_cmd + ["install", target],
                check=False,
                timeout=300,
            )
            if result.returncode == 0:
                print(f"{GREEN}[✓] Installed: {pkg}{RESET}")
            else:
                print(f"{RED}[✗] Failed: {pkg}{RESET}")
                failed.append(pkg)
        except subprocess.TimeoutExpired:
            print(f"{RED}[✗] Timeout: {pkg}{RESET}")
            failed.append(pkg)
        except Exception as e:
            print(f"{RED}[✗] Error: {pkg} — {e}{RESET}")
            failed.append(pkg)

    print()
    if failed:
        print(f"{RED}{BOLD}[✗] Some packages failed:{RESET}")
        for p in failed:
            print(f"     {RED}✗{RESET} {p}")
        print(f"\n{YELLOW}Try manually:{RESET}")
        print(f"  {WHITE}{' '.join(pip_cmd)} install {' '.join(failed)}{RESET}\n")
        return False

    print(f"{GREEN}{BOLD}[✓] All requirements installed!{RESET}\n")
    return True


# =========================================================
# BANNER — كيتكيّف مع الشاشة
# =========================================================
def banner():
    W = term_width()

    print()

    # ─── Termux / شاشة صغيرة ───
    if W < 55:
        print(f"""{BOLD}{RED}
   ╔═══════════════════════════╗
   ║  ⠙⢷⣶⣄    ⣰⣿⡿        ║
   ║  ⣸⣿⣿⣿⣦  ⣿⣿⡿        ║
   ║  ⠈⠻⣿⣿⣿  ⠉⠻⠁        ║
   ║  ⢀⣿⣿⣿⣿  ⢀⡄          ║
   ║  ⠈⠻⣿⣿⣷⣾⣷⡾ ⣤⣄      ║
   ║   ⠘⣿⣿⣿⣿⣿⣿⠛        ║
   ╚═══════════════════════════╝
   {BLACK}    Phone ToolKits{RED}
{RESET}""")
        return

    # ─── PC / شاشة كبيرة ───
    print(f"""{BOLD}{RED}
⠙⢷⣶⣄⡀⠀⠀⠀⠀⠀⢀⣀⣀⣀⡀⠀⢀⡀⣰⣿⡿
⠀⣸⣿⣿⣿⣦⠀⠀⠀⠀⠀⠉⠿⠿⣿⣶⣿⣿⡿⠛⠁
⠀⠈⠻⣿⣿⣿⡇⠀⠀⠀⠀⠀⠀⠀⠈⠈⠉⠻⠁⠀⠀
⠀⠀⢀⣿⣿⣿⣿⠀⢀⡄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠈⠻⣿⣿⣷⣾⣷⡾⠀⣀⣤⣶⣶⣶⣶⣤⣄⠀
⠀⠀⠀⠀⠀⠘⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡿⠛⠋⠑
⠀⠀⠀⠀⠀⠀⢹⠟⠛⠉⠉⠙⠻⡟⠁⠀⠈⠁⠀⠀⠀
                  {BLACK}Welcom{RED}⠀⠀⠀⠀
           {BLACK}Simpel Phone ToolKits{RED}
{RESET}""")


# =========================================================
# CLEAR
# =========================================================
def clear_screen():
    os.system("cls" if os.name == "nt" else "clear")


# =========================================================
# PROMPT
# =========================================================
def get_prompt():
    if venv_available():
        return (
            f"{GREEN}{BOLD}ven{RESET}"
            f"{WHITE}({GREEN}{BOLD}Selver{RESET}{WHITE})"
            f"{GREEN} > {RESET}"
        )
    return f"{GREEN}{BOLD}Selver{RESET}{GREEN} > {RESET}"


# =========================================================
# OPTIONS
# =========================================================
OPTIONS = {
    "1": ("Auto save Email message Html", "AUto_save_HTML_phishing.py"),
    "2": ("Pro server Phishing",          "server.py"),
    "3": ("wifi password Generator",      "71sta.py"),
    "4": ("Bob ControleX2",               "c2.py"),
    "5": ("I Forget My Info Crack",       "Info_Secret.py"),
}


# =========================================================
# MENU — ذكي: بلا box فـ Termux، box فـ PC
# =========================================================
def print_menu():
    banner()

    items = [
        ("1", "Auto save Email message Html"),
        ("2", "Pro server Phishing"),
        ("3", "wifi password Generator"),
        ("4", "Bob ControleX2"),
        ("5", "I Forget My Info Crack"),
        ("0", "Exit"),
    ]

    def option_text(key, desc):
        if key == "0":
            return f"{BLUE}{BOLD}[0]{RESET} {WHITE}{desc}{RESET}"
        return f"{CYAN}[{key}]{RESET} {WHITE}{desc}{RESET}"

    W = term_width()

    # ─── Termux / شاشة صغيرة: list عادي بلا box ───
    if W < 60:
        print()
        for key, desc in items:
            print(f"   {option_text(key, desc)}")
        print()
        return

    # ─── PC / شاشة كبيرة: box ديناميكي ───
    lines = [option_text(k, d) for k, d in items]
    max_content = max(visible_len(l) for l in lines)
    inner = min(max_content + 2, W - 6)
    inner = max(inner, 30)

    print(f"{RED}{BOLD}╭{'─' * inner}╮{RESET}")
    for line in lines:
        pad = max(0, inner - visible_len(line) - 2)
        print(f"{RED}│{RESET} {line}{' ' * pad} {RED}│{RESET}")
    print(f"{RED}{BOLD}╰{'─' * inner}╯{RESET}")


# =========================================================
# CHECK SCRIPT
# =========================================================
def check_script(script_path):
    if not script_path.exists():
        print(f"\n{RED}{BOLD}[✗] Script not found:{RESET}")
        print(f"{YELLOW}{script_path}{RESET}")
        return False
    return True


# =========================================================
# RUN SCRIPT
# =========================================================
def run_script(script_name):
    clear_screen()
    banner()

    script_path = TOOLS_DIR / script_name

    if not check_script(script_path):
        input(f"\n{MAGENTA}Press Enter to return...{RESET}")
        return

    try:
        # BASH
        if script_path.suffix.lower() == ".sh":
            if not shutil.which("bash"):
                print(f"{RED}[✗] bash not found on this system.{RESET}")
                input(f"\n{MAGENTA}Press Enter to return...{RESET}")
                return
            command = ["bash", str(script_path)]
            interpreter = "Bash"

        # PYTHON
        elif script_path.suffix.lower() == ".py":
            if venv_available():
                command = [str(VENV_PYTHON), str(script_path)]
                interpreter = f"virtualEnv ({VENV_DIR.name}) / Python"
            else:
                command = [sys.executable, str(script_path)]
                interpreter = "System Python"

        # EXECUTABLE
        else:
            command = [str(script_path)]
            interpreter = "Executable"

        print(f"{GREEN}[+] Interpreter : {WHITE}{interpreter}{RESET}")
        print(f"{GREEN}[+] File        : {WHITE}{script_path.name}{RESET}")
        print()

        time.sleep(0.5)

        subprocess.run(
            command,
            cwd=str(TOOLS_DIR),
            check=False
        )

    except KeyboardInterrupt:
        print(f"\n\n{YELLOW}[!] Interrupted by user.{RESET}")

    except Exception as error:
        print(f"\n{RED}[✗] Error:{RESET} {error}")

    input(f"\n{CYAN}{BOLD}Press Enter to return to menu...{RESET}")


# =========================================================
# MAIN
# =========================================================
def main():
    if not BASE_DIR.is_dir():
        print(f"{RED}{BOLD}[✗] TOOLKITS directory not found!{RESET}")
        print(BASE_DIR)
        sys.exit(1)

    if not TOOLS_DIR.is_dir():
        print(f"{RED}{BOLD}[✗] .Scripts directory not found!{RESET}")
        print(TOOLS_DIR)
        sys.exit(1)

    # ✅ فحص requirements قبل الـ menu
    clear_screen()
    banner()
    ensure_requirements()
    input(f"{MAGENTA}Press Enter to continue...{RESET}")

    # =========================================
    # MENU LOOP
    # =========================================
    while True:
        clear_screen()
        print_menu()

        try:
            choice = input(f"\n{get_prompt()}").strip()
        except (EOFError, KeyboardInterrupt):
            print(f"\n\n{YELLOW}[!] Interrupted.{RESET}")
            break

        # EXIT
        if choice == "0":
            clear_screen()
            W = term_width()
            box_w = min(W - 4, 38)

            print(f"\n{RED}{BOLD}╔{'═' * box_w}╗{RESET}")
            print(f"{RED}{BOLD}║{RESET}{'Goodbye, void bear!'.center(box_w)}{RED}{BOLD}║{RESET}")
            print(f"{RED}{BOLD}╚{'═' * box_w}╝{RESET}\n")
            break

        # INVALID
        if choice not in OPTIONS:
            print(f"\n{RED}[✗] Invalid option.{RESET}")
            time.sleep(1)
            continue

        # RUN
        description, script_name = OPTIONS[choice]
        run_script(script_name)


# =========================================================
# START
# =========================================================
if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n{YELLOW}[!] Interrupted.{RESET}")
        sys.exit(0)