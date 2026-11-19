"""
Unit Test Suite for S.H.I.V.A. Direct Actions & Classification Engine.
Validates:
1. LeetCode vs VS Code disambiguation
2. Personal Portfolio direct opening
3. Browser tab close vs application kill
4. Gmail actions
5. WhatsApp messaging & unknown number auto-responder
"""

import sys
from core.direct_actions import try_handle_direct_action
from skills.whatsapp_skills import process_incoming_whatsapp_message, get_unknown_greeting_template

def run_tests():
    print("========================================")
    print("RUNNING S.H.I.V.A. TEST SUITE")
    print("========================================\n")

    test_cases = [
        # (user_input, expected_keyword_in_response, fail_keyword_in_response, test_name)
        ("okey lets open leetcode", "leetcode", "VS Code", "1. Open LeetCode (Should open LeetCode in Chrome, NOT VS Code)"),
        ("open mine leetcode", "leetcode", "VS Code", "2. Open Mine LeetCode (Should open LeetCode in Chrome, NOT VS Code)"),
        ("my portfolio", "portfolio", "google.com/search", "3. My Portfolio (Should open live portfolio, NOT search Google)"),
        ("open my portfolio", "portfolio", "VS Code", "4. Open My Portfolio (Should open live portfolio in Chrome)"),
        ("close my github on chrome", "tab", "terminated", "5. Close GitHub on Chrome (Should close TAB, NOT kill Chrome process)"),
        ("close tab", "tab", "process", "6. Close Tab (Should close TAB)"),
        ("close vs code", "vscode", None, "7. Close VS Code (Should close VS Code process)"),
        ("read my emails", "email", None, "8. Read My Emails (Should check Gmail)"),
        ("simulate incoming whatsapp message from +919988776655", "UNKNOWN NUMBER DETECTED", None, "9. WhatsApp Unknown Number Auto-Responder"),
        ("send whatsapp to Office message meeting at 5", "Office", None, "10. WhatsApp Send By Contact Name"),
        ("whatsapp call to Shivam", "Shivam", None, "11. WhatsApp Call By Contact Name"),
        ("list contacts", "contact", None, "12. List Contacts Directory"),
        ("kitne mail aaye hai 24 ghante mai", "email", None, "13. 24-Hour Email Briefing Query"),
        ("night se morning tak kitne mail aaye hai", "email", None, "14. Night-to-Morning Email Query"),
        ("important mail padh ke batao", "email", None, "15. Important Email Briefing Query"),
        ("news tell me today", "khabar", "Shall I search", "16. Live News Headlines (Should fetch real news, NOT ask to search Google)"),
        ("weather today", "mausam", None, "17. Live Weather (Should fetch real weather for Bhopal)"),
        ("search Python programming", "Python", None, "18. Real-Time Web Search (Should fetch live info)"),
    ]

    all_passed = True
    for user_input, expected_str, fail_str, test_name in test_cases:
        handled, response = try_handle_direct_action(user_input)
        print(f"Testing: {test_name}")
        print(f"Input:    \"{user_input}\"")
        print(f"Handled:  {handled}")
        print(f"Response: {response}")

        if not handled:
            print("❌ FAILED: Action was not handled by direct dispatcher!\n")
            all_passed = False
            continue

        if expected_str and expected_str.lower() not in response.lower():
            print(f"❌ FAILED: Expected '{expected_str}' in response!\n")
            all_passed = False
            continue

        if fail_str and fail_str.lower() in response.lower():
            print(f"❌ FAILED: Found forbidden '{fail_str}' in response!\n")
            all_passed = False
            continue

        print("✅ PASSED\n")

    # Test Unknown Number Auto-Responder Logic directly
    print("Testing: 10. WhatsApp Auto-Greeting & Qualifying Questions Engine")
    res = process_incoming_whatsapp_message("+919123456789", "Hello, are you available for hiring?")
    assert res["is_unknown"] is True, "Sender should be identified as unknown"
    assert "Full Name" in res["auto_reply"], "Auto-reply must ask for Full Name"
    assert "purpose" in res["auto_reply"], "Auto-reply must ask for Purpose"
    assert "Urgency" in res["auto_reply"], "Auto-reply must ask for Urgency"
    print("Auto-reply template generated:")
    print(res["auto_reply"])
    print("✅ PASSED: WhatsApp Auto-Greeting & Questions Verified!\n")

    from core.voice import clean_text_for_speech

    # Test Speech Text Cleaner (No robotic 1., 2., labels, or brackets spoken)
    print("Testing: 16. Human Speech Cleaner (Strips 1., 2., bullet points, and headers)")
    sample_raw = "1. Security alert\n   • Sender: Google\n   • Context: [image: Google] Someone signed in.\n2. Work Update"
    cleaned_speech = clean_text_for_speech(sample_raw)
    print(f"Raw Input:\n{sample_raw}")
    print(f"Cleaned Spoken Text:\n{cleaned_speech}")
    assert "1." not in cleaned_speech, "Numbers like 1. must not be spoken"
    assert "2." not in cleaned_speech, "Numbers like 2. must not be spoken"
    assert "•" not in cleaned_speech, "Bullet symbols must not be spoken"
    assert "Sender:" not in cleaned_speech, "Headers like Sender: must not be spoken"
    assert "[image:" not in cleaned_speech, "Image annotations must not be spoken"
    print("✅ PASSED: Human Speech Cleaner verified!\n")

    if all_passed:
        print("🎉 ALL TESTS PASSED SUCCESSFULLY! Everything is verified.")
    else:
        print("⚠️ SOME TESTS FAILED. Review output above.")
        sys.exit(1)

if __name__ == "__main__":
    run_tests()

