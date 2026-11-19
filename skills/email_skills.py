"""
Email & Gmail Skills for S.H.I.V.A.
Supports:
1. Reading unread or recent emails via IMAP (imap.gmail.com:993)
2. Sending emails directly via SMTP (smtp.gmail.com:587)
3. Opening Gmail / pre-filling Compose in Google Chrome when App Password is not yet set
"""

import os
import imaplib
import smtplib
import email
from email.header import decode_header
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import urllib.parse
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv
from config import BASE_DIR
from skills.system_skills import open_in_chrome

load_dotenv(BASE_DIR / ".env")

GMAIL_USER = os.getenv("GMAIL_USER", "shivamjais2106@gmail.com")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD", "").strip()


def _decode_mime_words(raw_header: Optional[str]) -> str:
    """Decodes MIME encoded words (like UTF-8 base64 subjects)."""
    if not raw_header:
        return ""
    decoded_fragments = decode_header(raw_header)
    parts = []
    for content, encoding in decoded_fragments:
        if isinstance(content, bytes):
            try:
                parts.append(content.decode(encoding or "utf-8", errors="replace"))
            except Exception:
                parts.append(content.decode("latin1", errors="replace"))
        else:
            parts.append(str(content))
    return "".join(parts)


def open_gmail(folder: str = "inbox") -> str:
    """Opens Boss's Gmail inbox or specific folder in Google Chrome."""
    clean_folder = folder.lower().strip()
    target_url = f"https://mail.google.com/mail/u/0/#{clean_folder}"
    return open_in_chrome(target_url)


def compose_email_in_browser(to_email: str = "", subject: str = "", body: str = "") -> str:
    """
    Opens Google Chrome with a new Gmail compose window pre-filled with recipient, subject, and body.
    Zero configuration needed!
    """
    encoded_to = urllib.parse.quote(to_email.strip())
    encoded_su = urllib.parse.quote(subject.strip())
    encoded_body = urllib.parse.quote(body.strip())
    compose_url = f"https://mail.google.com/mail/?view=cm&fs=1&to={encoded_to}&su={encoded_su}&body={encoded_body}"
    open_in_chrome(compose_url)
    return (
        f"Boss, maine Gmail compose window Chrome mein open kar di hai. "
        f"Recipient '{to_email or 'recipient'}' aur subject '{subject or 'No Subject'}' pre-fill kar diya hai! ✉️"
    )


def build_conversational_recent_emails(emails_list: List[Dict[str, Any]]) -> str:
    """Builds a human conversational summary of recent emails."""
    if not emails_list:
        return "Boss, inbox mein koi naya email nahi hai. Sab kuch up to date hai! ✨"

    parts = [f"Boss, aapke latest {len(emails_list)} emails maine check kar liye hain."]
    for idx, em in enumerate(emails_list[:3]):
        sender = em.get('from', '').split('<')[0].replace('"', '').strip()
        sub = em.get('subject', '').strip()
        if idx == 0:
            parts.append(f"Pehla email {sender} ki taraf se hai: '{sub}'.")
        elif idx == 1:
            parts.append(f"Doosra email {sender} se hai: '{sub}'.")
        elif idx == 2:
            parts.append(f"Teesra email {sender} se hai: '{sub}'.")

    if len(emails_list) > 3:
        parts.append(f"Baki {len(emails_list) - 3} aur emails inbox mein hain.")

    parts.append("Kya main inme se koi email Chrome mein open karoon, Boss?")
    return " ".join(parts)


def build_conversational_email_briefing(
    timeframe_hours: int,
    total_count: int,
    urgent_emails: List[Dict[str, Any]],
    work_emails: List[Dict[str, Any]],
    general_count: int,
) -> str:
    """Builds a sharp, fluent, natural conversational executive briefing without robotic bullets."""
    if total_count == 0:
        return f"Boss, pichhle {timeframe_hours} ghante mein koi naya email nahi aaya hai. Aapka inbox bilkul up to date hai! ✨"

    parts = [f"Boss, pichhle {timeframe_hours} ghante mein aapke inbox mein total {total_count} emails aaye hain."]

    if urgent_emails:
        first_urgent = urgent_emails[0]
        sender = first_urgent.get("from", "").split("<")[0].replace('"', '').strip()
        sub = first_urgent.get("subject", "").strip()
        parts.append(f"Sabse zaroori email {sender} ki taraf se hai, subject hai '{sub}'.")
        if len(urgent_emails) > 1:
            parts.append(f"Iske alava {len(urgent_emails) - 1} aur priority alerts hain.")

    if work_emails:
        first_work = work_emails[0]
        work_sender = first_work.get("from", "").split("<")[0].replace('"', '').strip()
        work_sub = first_work.get("subject", "").strip()
        parts.append(f"Work aur development se related {len(work_emails)} updates hain, jaise {work_sender} se '{work_sub}'.")

    if general_count > 0:
        if urgent_emails or work_emails:
            parts.append(f"Baki {general_count} emails regular promotions aur newsletters hain.")
        else:
            parts.append(f"Sabhi {general_count} emails regular newsletters aur promotional updates hain, koi urgent alert nahi hai.")

    if urgent_emails:
        parts.append("Kya aap urgent email ko Chrome browser mein open karke dekhna chahte hain, Boss?")
    else:
        parts.append("Kya aap koi specific email open karna chahte hain, Boss?")

    return " ".join(parts)


def read_emails(limit: int = 5, unread_only: bool = True, query: Optional[str] = None) -> Dict[str, Any]:
    """
    Reads unread or recent emails from Gmail INBOX using IMAP.
    If GMAIL_APP_PASSWORD is not configured in .env, seamlessly opens Gmail in Chrome.
    """
    password = os.getenv("GMAIL_APP_PASSWORD", GMAIL_APP_PASSWORD).replace(" ", "").strip()
    username = os.getenv("GMAIL_USER", GMAIL_USER).strip()

    if not password:
        open_gmail("inbox")
        return {
            "status": "browser_opened",
            "message": (
                "Boss, I've opened your Gmail Inbox in Google Chrome! 📬\n\n"
                "💡 Pro-Tip for Terminal Reading: To let SHIVA read and summarize your emails directly in the console/voice, "
                "generate a 16-character Google App Password (at https://myaccount.google.com/apppasswords) "
                "and set GMAIL_APP_PASSWORD=your_password in .env."
            ),
            "emails": [],
        }

    try:
        mail = imaplib.IMAP4_SSL("imap.gmail.com", 993)
        mail.login(username, password)
        mail.select("INBOX")

        search_criteria = "UNSEEN" if unread_only else "ALL"
        if query:
            search_criteria = f'(OR (SUBJECT "{query}") (FROM "{query}"))'

        status, messages = mail.search(None, search_criteria)
        if status != "OK" or not messages[0]:
            mail.logout()
            return {
                "status": "success",
                "total": 0,
                "message": f"Boss, no {'unread ' if unread_only else ''}emails found in your INBOX! You are all caught up. ✨",
                "emails": [],
            }

        msg_ids = messages[0].split()
        # Take the most recent emails
        recent_ids = msg_ids[-limit:]
        recent_ids.reverse()

        emails_list: List[Dict[str, Any]] = []

        for msg_id in recent_ids:
            status, data = mail.fetch(msg_id, "(RFC822)")
            if status != "OK" or not data:
                continue

            raw_email = data[0][1]
            msg = email.message_from_bytes(raw_email)

            subject = _decode_mime_words(msg.get("Subject", "(No Subject)"))
            from_sender = _decode_mime_words(msg.get("From", "(Unknown Sender)"))
            date_str = msg.get("Date", "")

            # Extract snippet of body
            body_snippet = ""
            if msg.is_multipart():
                for part in msg.walk():
                    content_type = part.get_content_type()
                    content_disposition = str(part.get("Content-Disposition"))
                    if content_type == "text/plain" and "attachment" not in content_disposition:
                        payload = part.get_payload(decode=True)
                        if payload:
                            body_snippet = payload.decode("utf-8", errors="replace")[:300].strip()
                            break
            else:
                payload = msg.get_payload(decode=True)
                if payload:
                    body_snippet = payload.decode("utf-8", errors="replace")[:300].strip()

            emails_list.append({
                "from": from_sender,
                "subject": subject,
                "date": date_str,
                "snippet": body_snippet.replace("\n", " ").strip(),
            })

        mail.logout()

        conversational_message = build_conversational_recent_emails(emails_list)

        return {
            "status": "success",
            "total": len(emails_list),
            "message": conversational_message,
            "emails": emails_list,
        }

    except imaplib.IMAP4.error:
        open_gmail("inbox")
        return {
            "status": "auth_error",
            "message": "Boss, Gmail authentication issue detect hua hai. Maine aapka inbox Chrome mein open kar diya hai.",
            "emails": [],
        }
    except Exception:
        open_gmail("inbox")
        return {
            "status": "error",
            "message": "Boss, Gmail connect karne mein issue aaya hai. Maine aapka inbox Chrome browser mein open kar diya hai.",
            "emails": [],
        }


def classify_email(sender: str, subject: str, snippet: str) -> str:
    """Classifies email into 'urgent', 'work_career', or 'general'."""
    text = f"{sender} {subject} {snippet}".lower()
    urgent_keywords = [
        "urgent", "action required", "immediately", "security alert", "unauthorized",
        "password reset", "verification code", "otp", "interview", "offer letter",
        "hired", "shortlisted", "deadline", "invoice", "payment due", "bank", "credit card", "bill"
    ]
    if any(k in text for k in urgent_keywords):
        return "urgent"

    work_keywords = [
        "fakhri", "fakhri it", "jamaatcloud", "client", "github", "pull request",
        "commit", "deploy", "vercel", "render", "docker", "aws", "sirt",
        "college", "exam", "assignment", "leetcode", "linkedin", "job application"
    ]
    if any(k in text for k in work_keywords):
        return "work_career"

    return "general"


def get_24h_email_briefing(timeframe_hours: int = 24) -> Dict[str, Any]:
    """
    Fetches all emails received in the last 24 hours (or specified hours),
    calculates total count, classifies important/urgent vs general,
    and returns an executive briefing with context.
    """
    password = os.getenv("GMAIL_APP_PASSWORD", GMAIL_APP_PASSWORD).replace(" ", "").strip()
    username = os.getenv("GMAIL_USER", GMAIL_USER).strip()

    if not password:
        open_gmail("inbox")
        return {
            "status": "browser_opened",
            "message": (
                "Boss, I've opened your Gmail Inbox in Google Chrome! 📬\n\n"
                "💡 To let SHIVA automatically analyze your 24-hour emails, count them, "
                "filter important messages and read them aloud:\n"
                "1. Visit: https://myaccount.google.com/apppasswords\n"
                "2. Create an App Password named 'SHIVA'\n"
                "3. Set `GMAIL_APP_PASSWORD=your_password` in `.env`.\n"
                "Once set, SHIVA will deliver complete 24h & morning email executive briefings anytime!"
            ),
            "total_emails": 0,
            "emails": [],
        }

    try:
        mail = imaplib.IMAP4_SSL("imap.gmail.com", 993)
        mail.login(username, password)
        mail.select("INBOX")

        target_dt = datetime.now() - timedelta(hours=timeframe_hours)
        months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
        since_date = f"{target_dt.day:02d}-{months[target_dt.month - 1]}-{target_dt.year}"

        status, messages = mail.search(None, f'SINCE "{since_date}"')
        if status != "OK" or not messages[0]:
            mail.logout()
            return {
                "status": "success",
                "total_emails": 0,
                "message": f"Boss, pichhle {timeframe_hours} ghante mein koi naya email nahi aaya hai. Inbox all clear! ✨",
                "emails": [],
            }

        msg_ids = messages[0].split()
        total_count = len(msg_ids)

        recent_ids = msg_ids[-8:]
        recent_ids.reverse()

        emails_list: List[Dict[str, Any]] = []

        for msg_id in recent_ids:
            st, data = mail.fetch(msg_id, "(RFC822)")
            if st != "OK" or not data:
                continue
            raw_email = data[0][1]
            msg = email.message_from_bytes(raw_email)

            subject = _decode_mime_words(msg.get("Subject", "(No Subject)"))
            from_sender = _decode_mime_words(msg.get("From", "(Unknown Sender)"))
            date_str = msg.get("Date", "")

            body_snippet = ""
            if msg.is_multipart():
                for part in msg.walk():
                    content_type = part.get_content_type()
                    content_disposition = str(part.get("Content-Disposition"))
                    if content_type == "text/plain" and "attachment" not in content_disposition:
                        payload = part.get_payload(decode=True)
                        if payload:
                            body_snippet = payload.decode("utf-8", errors="replace")[:300].strip()
                            break
            else:
                payload = msg.get_payload(decode=True)
                if payload:
                    body_snippet = payload.decode("utf-8", errors="replace")[:300].strip()

            category = classify_email(from_sender, subject, body_snippet)
            emails_list.append({
                "from": from_sender,
                "subject": subject,
                "date": date_str,
                "snippet": body_snippet.replace("\n", " ").strip(),
                "category": category,
            })

        mail.logout()

        urgent_emails = [e for e in emails_list if e["category"] == "urgent"]
        work_emails = [e for e in emails_list if e["category"] == "work_career"]
        general_emails = [e for e in emails_list if e["category"] == "general"]

        general_count = max(0, total_count - len(urgent_emails) - len(work_emails))
        conversational_message = build_conversational_email_briefing(
            timeframe_hours=timeframe_hours,
            total_count=total_count,
            urgent_emails=urgent_emails,
            work_emails=work_emails,
            general_count=general_count,
        )

        return {
            "status": "success",
            "total_emails": total_count,
            "urgent_count": len(urgent_emails),
            "work_count": len(work_emails),
            "message": conversational_message,
            "emails": emails_list,
        }

    except Exception:
        open_gmail("inbox")
        return {
            "status": "error",
            "message": "Boss, Gmail connect karne mein issue aaya hai. Maine aapka inbox Chrome browser mein open kar diya hai.",
            "total_emails": 0,
            "emails": [],
        }


def get_morning_briefing() -> Dict[str, Any]:
    """
    Fetches emails received from overnight (last 12 hours) to morning,
    giving Boss a quick morning catch-up digest.
    """
    return get_24h_email_briefing(timeframe_hours=12)


def send_email(to_email: str, subject: str, body: str, is_html: bool = False) -> Dict[str, Any]:
    """
    Sends an email using Gmail SMTP (smtp.gmail.com:587).
    If GMAIL_APP_PASSWORD is not configured, opens the compose window in Chrome with fields pre-filled.
    """
    password = os.getenv("GMAIL_APP_PASSWORD", GMAIL_APP_PASSWORD).replace(" ", "").strip()
    username = os.getenv("GMAIL_USER", GMAIL_USER).strip()

    if not password:
        browser_msg = compose_email_in_browser(to_email=to_email, subject=subject, body=body)
        return {
            "status": "browser_fallback",
            "message": browser_msg,
        }

    try:
        msg = MIMEMultipart()
        msg["From"] = f"Shivam Jaiswal <{username}>"
        msg["To"] = to_email
        msg["Subject"] = subject

        mime_type = "html" if is_html else "plain"
        msg.attach(MIMEText(body, mime_type, "utf-8"))

        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(username, password)
        server.send_message(msg)
        server.quit()

        return {
            "status": "success",
            "message": f"Boss, aapka email '{to_email}' ko successfully bhej diya gaya hai. Subject tha: '{subject}'. 🚀✉️",
        }
    except Exception:
        # Fall back to opening in browser so Boss's action never fails!
        compose_email_in_browser(to_email=to_email, subject=subject, body=body)
        return {
            "status": "partial_success",
            "message": "Boss, direct email bhejane mein issue aaya tha, isliye maine aapke liye Chrome mein compose window open kar diya hai.",
        }

