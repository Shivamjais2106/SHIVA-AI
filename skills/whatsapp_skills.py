"""
WhatsApp & Call Automation Skills for S.H.I.V.A.
Features:
1. Drop WhatsApp messages directly to contacts or phone numbers (Desktop app + Web)
2. Initiate WhatsApp calls
3. Unknown Number Auto-Responder:
   - Detects incoming messages from unknown numbers
   - Automatically generates a professional greeting
   - Asks qualifying questions (Name, purpose, urgency)
   - Saves conversations to memory/whatsapp_inbox.json
"""

import os
import json
import re
import time
import threading
import ctypes
import urllib.parse
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
from config import BASE_DIR, USER_REAL_NAME, USER_TITLE, ASSISTANT_NAME
from skills.system_skills import open_in_chrome

CONTACTS_FILE = BASE_DIR / "memory" / "contacts.json"
INBOX_FILE = BASE_DIR / "memory" / "whatsapp_inbox.json"


def _clean_phone(phone: str) -> str:
    """Cleans phone number and formats to standard international digits without +."""
    raw = re.sub(r"[^\d]", "", phone.strip())
    # If 10 digits (standard Indian mobile), prepend 91
    if len(raw) == 10:
        return f"91{raw}"
    return raw


def _load_contacts() -> List[Dict[str, Any]]:
    if CONTACTS_FILE.exists():
        try:
            with open(CONTACTS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("contacts", [])
        except Exception:
            pass
    return []


def _save_contacts(contacts: List[Dict[str, Any]]) -> None:
    try:
        with open(CONTACTS_FILE, "w", encoding="utf-8") as f:
            json.dump({"contacts": contacts}, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"[Error saving contacts]: {e}")


def _load_inbox() -> Dict[str, Any]:
    if INBOX_FILE.exists():
        try:
            with open(INBOX_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"messages": [], "auto_responder_enabled": True, "last_updated": None}


def _save_inbox(inbox_data: Dict[str, Any]) -> None:
    try:
        inbox_data["last_updated"] = datetime.now().isoformat()
        with open(INBOX_FILE, "w", encoding="utf-8") as f:
            json.dump(inbox_data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"[Error saving inbox]: {e}")


def find_contact_phone(target: str) -> Optional[str]:
    """Finds phone number by contact name or returns clean phone if already digits."""
    clean_target = target.strip()
    # Check if target is already numeric
    digits = re.sub(r"[^\d]", "", clean_target)
    if len(digits) >= 10:
        return _clean_phone(digits)

    # Search contacts catalog
    contacts = _load_contacts()
    query = clean_target.lower()
    for c in contacts:
        if query in c.get("name", "").lower():
            return _clean_phone(c.get("phone", ""))
    return None


def add_known_contact(name: str, phone: str, relationship: str = "Contact") -> str:
    """Adds a new contact to Boss's known contacts list so they are not flagged as unknown."""
    contacts = _load_contacts()
    clean_p = _clean_phone(phone)
    
    # Check if exists
    for c in contacts:
        if _clean_phone(c.get("phone", "")) == clean_p:
            c["name"] = name
            c["relationship"] = relationship
            _save_contacts(contacts)
            return f"Boss, updated existing contact '{name}' ({clean_p}) in contacts directory. 📇"

    contacts.append({
        "name": name,
        "phone": f"+{clean_p}",
        "relationship": relationship,
        "is_known": True,
    })
    _save_contacts(contacts)
    return f"Boss, saved '{name}' ({phone}) to your known contacts directory. 📇"


def list_known_contacts() -> Dict[str, Any]:
    """Lists all saved contacts in Boss's phonebook."""
    contacts = _load_contacts()
    return {
        "status": "success",
        "total": len(contacts),
        "contacts": contacts,
    }


def _auto_press_enter_after_delay(delay: float = 2.0):
    """
    Waits for WhatsApp to load the chat and pre-populate the text box,
    then automatically simulates an ENTER keypress via PyAutoGUI to dispatch the message hands-free!
    """
    def _worker():
        time.sleep(delay)
        try:
            import pyautogui
            pyautogui.press('enter')
        except Exception:
            pass

        # Native user32 keybd_event fallback
        try:
            VK_RETURN = 0x0D
            KEYEVENTF_KEYUP = 0x0002
            ctypes.windll.user32.keybd_event(VK_RETURN, 0, 0, 0)
            time.sleep(0.05)
            ctypes.windll.user32.keybd_event(VK_RETURN, 0, KEYEVENTF_KEYUP, 0)
        except Exception:
            pass

    threading.Thread(target=_worker, daemon=True).start()


def send_whatsapp_message(target: str, message: str, use_web: bool = False, auto_send: bool = True) -> str:
    """
    Sends a WhatsApp message to a contact name or phone number.
    If auto_send is True, automatically hits Enter after chat loads so Boss doesn't have to touch anything!
    """
    phone = find_contact_phone(target)
    if not phone:
        # Fall back to target if it has any numbers
        phone = _clean_phone(target)
        if len(phone) < 10:
            return (
                f"Boss, mujhe '{target}' ka contact number nahi mila. "
                f"Aap bol sakte hain: 'add contact {target} phone <number>', ya fir 10-digit phone number batayein."
            )

    display_name = target if not target.isdigit() else f"+{phone}"
    encoded_msg = urllib.parse.quote(message)

    if use_web:
        web_url = f"https://web.whatsapp.com/send?phone={phone}&text={encoded_msg}"
        open_in_chrome(web_url)
        if auto_send:
            _auto_press_enter_after_delay(delay=5.0)
            return f"Boss, {display_name} ko WhatsApp par message bhej diya hai: '{message}'."
        return f"Boss, {display_name} ke liye WhatsApp Web open kar diya hai."

    # Try WhatsApp Desktop URI protocol
    uri = f"whatsapp://send?phone={phone}&text={encoded_msg}"
    try:
        subprocess.Popen(f'start "" "{uri}"', shell=True)
        if auto_send:
            _auto_press_enter_after_delay(delay=2.5)
            return f"Boss, {display_name} ko WhatsApp par message bhej diya hai: '{message}'."
        return f"Boss, {display_name} ke liye WhatsApp chat open kar di hai."
    except Exception:
        # Fall back to web
        web_url = f"https://web.whatsapp.com/send?phone={phone}&text={encoded_msg}"
        open_in_chrome(web_url)
        if auto_send:
            _auto_press_enter_after_delay(delay=5.0)
        return f"Boss, {display_name} ko WhatsApp par message bhej diya hai: '{message}'."


def initiate_whatsapp_call(target: str, call_type: str = "voice") -> str:
    """
    Initiates a WhatsApp call to a contact name or phone number.
    """
    phone = find_contact_phone(target)
    if not phone:
        phone = _clean_phone(target)
        if len(phone) < 10:
            return (
                f"Boss, mujhe call karne ke liye '{target}' ka contact number nahi mila. "
                f"Aap bol sakte hain: 'add contact {target} phone <number>', ya fir 10-digit number batayein."
            )

    display_name = target if not target.isdigit() else f"+{phone}"
    uri = f"whatsapp://send?phone={phone}"
    try:
        subprocess.Popen(f'start "" "{uri}"', shell=True)
        return f"Boss, {display_name} ke saath WhatsApp {call_type} call window open kar di hai."
    except Exception as e:
        return f"Boss, WhatsApp call connect karne mein error aaya: {e}"


def get_unknown_greeting_template(sender_phone: str) -> str:
    """Generates the polite greeting and qualifying questionnaire for unknown senders."""
    return (
        f"Namaste! 🙏\n"
        f"You have reached the personal contact of {USER_REAL_NAME}.\n"
        f"I am {ASSISTANT_NAME}, Shivam's synthetic AI Assistant.\n\n"
        f"Boss (Shivam) is currently focused on development work and away from his desk. "
        f"To help him assist you promptly, please reply with:\n"
        f"1️⃣ What is your Full Name & Organization / Reference?\n"
        f"2️⃣ What is the purpose of your message?\n"
        f"3️⃣ Urgency level (Urgent / Normal / For Information)?\n\n"
        f"Thank you! Your inquiry has been registered, and Shivam will get back to you shortly. ✨"
    )


def process_incoming_whatsapp_message(
    sender_phone: str,
    message_text: str,
    sender_name: Optional[str] = None
) -> Dict[str, Any]:
    """
    Processes an incoming WhatsApp message.
    If the number is UNKNOWN:
      1. Generates an automated greeting message asking the 3 qualifying questions.
      2. Records the incoming message & auto-reply in whatsapp_inbox.json.
      3. Stages or sends the reply back.
    """
    clean_p = _clean_phone(sender_phone)
    contacts = _load_contacts()
    
    # Check if number is in known contacts
    matched_contact = None
    for c in contacts:
        if _clean_phone(c.get("phone", "")) == clean_p:
            matched_contact = c
            break

    is_unknown = matched_contact is None
    inbox = _load_inbox()

    auto_reply = ""
    if is_unknown and inbox.get("auto_responder_enabled", True):
        auto_reply = get_unknown_greeting_template(clean_p)

    entry = {
        "timestamp": datetime.now().isoformat(),
        "sender_phone": f"+{clean_p}",
        "sender_name": sender_name or (matched_contact.get("name") if matched_contact else "Unknown"),
        "is_known_contact": not is_unknown,
        "message": message_text,
        "auto_replied": bool(auto_reply),
        "auto_reply_sent": auto_reply,
        "status": "inquiry_pending" if is_unknown else "message_logged",
    }

    inbox["messages"].append(entry)
    _save_inbox(inbox)

    return {
        "status": "success",
        "is_unknown": is_unknown,
        "sender": entry["sender_name"],
        "phone": entry["sender_phone"],
        "received_message": message_text,
        "auto_reply": auto_reply,
    }


def simulate_incoming_whatsapp(sender_phone: str, message_text: str) -> str:
    """
    Simulates an incoming WhatsApp message from an unknown number to test the auto-greeting & question engine.
    """
    result = process_incoming_whatsapp_message(sender_phone, message_text)
    if result["is_unknown"]:
        return (
            f"🔔 [WHATSAPP INCOMING - UNKNOWN NUMBER DETECTED]: +{_clean_phone(sender_phone)}\n"
            f"Message: \"{message_text}\"\n\n"
            f"🤖 [SHIVA AUTO-RESPONDER FIRED]:\n"
            f"{result['auto_reply']}\n\n"
            f"✅ Logged to whatsapp_inbox.json, Boss!"
        )
    else:
        return (
            f"🔔 [WHATSAPP INCOMING - KNOWN CONTACT]: {result['sender']} ({result['phone']})\n"
            f"Message: \"{message_text}\"\n"
            f"✅ Logged to whatsapp_inbox.json, Boss!"
        )


def get_whatsapp_inbox(unread_only: bool = False) -> Dict[str, Any]:
    """Retrieves all received WhatsApp inquiries and their auto-responder status."""
    inbox = _load_inbox()
    msgs = inbox.get("messages", [])
    if unread_only:
        msgs = [m for m in msgs if m.get("status") == "inquiry_pending"]
    return {
        "status": "success",
        "total": len(msgs),
        "auto_responder_active": inbox.get("auto_responder_enabled", True),
        "messages": msgs,
    }


def toggle_whatsapp_auto_responder(enable: bool) -> str:
    """Enables or disables the automatic greeting & questioning bot for unknown numbers."""
    inbox = _load_inbox()
    inbox["auto_responder_enabled"] = enable
    _save_inbox(inbox)
    state = "enabled" if enable else "disabled"
    return f"Boss, WhatsApp Auto-Responder for unknown numbers is now {state}. 🤖"
