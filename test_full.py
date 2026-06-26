"""
Comprehensive end-to-end test suite for QueueStorm Investigator.
Tests: health check, schema validation, safety shield, and live API calls.
Includes retry logic and delays for rate-limited APIs.
"""

import json
import sys
import time
import requests

BASE_URL = "http://localhost:8000"
passed = 0
failed = 0
RETRY_DELAY = 10  # seconds between API calls
MAX_RETRIES = 3


def test(name, condition, detail=""):
    global passed, failed
    if condition:
        passed += 1
        print(f"  [PASS] {name}")
    else:
        failed += 1
        print(f"  [FAIL] {name} -- {detail}")


def api_call_with_retry(payload, label=""):
    """POST to /analyze-ticket with retry on 429/500."""
    for attempt in range(1, MAX_RETRIES + 1):
        r = requests.post(
            f"{BASE_URL}/analyze-ticket",
            json=payload,
            timeout=120,
        )
        if r.status_code == 200:
            return r
        if r.status_code in (429, 500) and attempt < MAX_RETRIES:
            wait = RETRY_DELAY * attempt
            print(f"  [RETRY] Attempt {attempt} got {r.status_code}, waiting {wait}s...")
            time.sleep(wait)
        else:
            return r
    return r


# =====================================================================
print("\n=== TEST 1: Health Check (GET /health) ===")
# =====================================================================
try:
    r = requests.get(f"{BASE_URL}/health", timeout=5)
    test("Status code is 200", r.status_code == 200, f"Got {r.status_code}")
    data = r.json()
    test("Response is {\"status\": \"ok\"}", data == {"status": "ok"}, f"Got {data}")
except Exception as e:
    test("Health endpoint reachable", False, str(e))
    print("\n*** Server not reachable. Is uvicorn running on port 8000? ***")
    sys.exit(1)


# =====================================================================
print("\n=== TEST 2: Schema Validation - Missing required field ===")
# =====================================================================
r = requests.post(
    f"{BASE_URL}/analyze-ticket",
    json={"ticket_id": "TKT-BAD"},  # missing 'complaint'
    timeout=10,
)
test("Returns 422 for missing 'complaint'", r.status_code == 422, f"Got {r.status_code}")


# =====================================================================
print("\n=== TEST 3: Unauthorized Transaction Analysis (with history) ===")
# =====================================================================
payload_1 = {
    "ticket_id": "TKT-001",
    "complaint": "I did not authorize a $500 transfer to an unknown account yesterday. I was at home and did not make this transaction.",
    "transaction_history": [
        {
            "transaction_id": "TXN-9821",
            "amount": 500.00,
            "currency": "USD",
            "timestamp": "2025-06-24T14:32:00Z",
            "type": "transfer",
            "status": "completed",
            "merchant": "Unknown Account"
        },
        {
            "transaction_id": "TXN-9820",
            "amount": 25.00,
            "currency": "USD",
            "timestamp": "2025-06-24T10:15:00Z",
            "type": "purchase",
            "status": "completed",
            "merchant": "Coffee Shop"
        }
    ]
}

print("  Sending request (calls Gemini API, may take a few seconds)...")
r = api_call_with_retry(payload_1, "Test 3")
test("Status code is 200", r.status_code == 200, f"Got {r.status_code}")

if r.status_code == 200:
    data = r.json()
    print(f"  Response: {json.dumps(data, indent=2)}")

    test("ticket_id echoed correctly", data.get("ticket_id") == "TKT-001", f"Got {data.get('ticket_id')}")
    test("case_type is valid enum", data.get("case_type") in [
        "wrong_transfer", "payment_failed", "phishing_or_social_engineering",
        "account_takeover", "unauthorized_transaction", "service_complaint", "other"
    ], f"Got {data.get('case_type')}")
    test("department is valid enum", data.get("department") in [
        "customer_support", "dispute_resolution", "fraud_risk", "compliance", "technical_support"
    ], f"Got {data.get('department')}")
    test("priority is valid enum", data.get("priority") in [
        "low", "medium", "high", "critical"
    ], f"Got {data.get('priority')}")
    test("evidence_verdict is valid enum", data.get("evidence_verdict") in [
        "consistent", "inconsistent", "insufficient_data"
    ], f"Got {data.get('evidence_verdict')}")
    test("confidence_score is float 0-1",
         isinstance(data.get("confidence_score"), (int, float)) and 0 <= data["confidence_score"] <= 1,
         f"Got {data.get('confidence_score')}")
    test("reasoning is non-empty string",
         isinstance(data.get("reasoning"), str) and len(data["reasoning"]) > 0)
    test("customer_reply is non-empty string",
         isinstance(data.get("customer_reply"), str) and len(data["customer_reply"]) > 0)
    test("human_review_required is boolean",
         isinstance(data.get("human_review_required"), bool),
         f"Got {type(data.get('human_review_required'))}")
    test("relevant_transaction_id is string or null",
         data.get("relevant_transaction_id") is None or isinstance(data.get("relevant_transaction_id"), str))

    # Safety shield checks on the reply
    reply = data.get("customer_reply", "").lower()
    test("Reply does NOT promise refund", "we will refund you" not in reply)
else:
    print(f"  Error response: {r.text[:300]}")

# Wait before next API call
print("  Waiting before next API call...")
time.sleep(RETRY_DELAY)

# =====================================================================
print("\n=== TEST 4: Phishing / Social Engineering (human_review forced) ===")
# =====================================================================
payload_2 = {
    "ticket_id": "TKT-002",
    "complaint": "Someone called me claiming to be from the bank and asked for my OTP. I gave it to them and now money is missing from my account.",
    "transaction_history": [
        {
            "transaction_id": "TXN-5544",
            "amount": 1200.00,
            "currency": "USD",
            "timestamp": "2025-06-25T09:00:00Z",
            "type": "transfer",
            "status": "completed",
            "merchant": "Unknown"
        }
    ]
}

print("  Sending phishing scenario...")
r = api_call_with_retry(payload_2, "Test 4")
test("Status code is 200", r.status_code == 200, f"Got {r.status_code}")

if r.status_code == 200:
    data = r.json()
    print(f"  Response: {json.dumps(data, indent=2)}")
    test("ticket_id echoed correctly", data.get("ticket_id") == "TKT-002")
    test("case_type is phishing_or_social_engineering",
         data.get("case_type") == "phishing_or_social_engineering",
         f"Got {data.get('case_type')}")
    test("human_review_required is True",
         data.get("human_review_required") is True,
         f"Got {data.get('human_review_required')}")
    test("department is fraud_risk",
         data.get("department") == "fraud_risk",
         f"Got {data.get('department')}")
else:
    print(f"  Error response: {r.text[:300]}")

# Wait before next API call
print("  Waiting before next API call...")
time.sleep(RETRY_DELAY)

# =====================================================================
print("\n=== TEST 5: No Transaction History (insufficient_data expected) ===")
# =====================================================================
payload_3 = {
    "ticket_id": "TKT-003",
    "complaint": "My payment of $75 to Amazon failed yesterday but the money was debited.",
    "transaction_history": None
}

print("  Sending request with no transaction history...")
r = api_call_with_retry(payload_3, "Test 5")
test("Status code is 200", r.status_code == 200, f"Got {r.status_code}")

if r.status_code == 200:
    data = r.json()
    print(f"  Response: {json.dumps(data, indent=2)}")
    test("ticket_id echoed correctly", data.get("ticket_id") == "TKT-003")
    test("evidence_verdict is insufficient_data",
         data.get("evidence_verdict") == "insufficient_data",
         f"Got {data.get('evidence_verdict')}")
else:
    print(f"  Error response: {r.text[:300]}")


# =====================================================================
print("\n=== TEST 6: Safety Shield - Direct regex test ===")
# =====================================================================
from ai_engine import _sanitize_reply

test("Blocks 'PIN'", _sanitize_reply("Please share your PIN") != "Please share your PIN")
test("Blocks 'OTP'", _sanitize_reply("Enter your OTP here") != "Enter your OTP here")
test("Blocks 'password'", _sanitize_reply("What is your password?") != "What is your password?")
test("Blocks 'we will refund you'",
     _sanitize_reply("Don't worry, we will refund you soon") != "Don't worry, we will refund you soon")
test("Blocks 'CVV'", _sanitize_reply("Please provide your CVV") != "Please provide your CVV")
test("Blocks 'credit card number'",
     _sanitize_reply("Share your credit card number") != "Share your credit card number")
test("Allows safe text",
     _sanitize_reply("We are reviewing your case.") == "We are reviewing your case.")
test("Allows safe text 2",
     _sanitize_reply("A specialist will contact you shortly.") == "A specialist will contact you shortly.")


# =====================================================================
print("\n" + "=" * 60)
print(f"RESULTS: {passed} passed, {failed} failed, {passed + failed} total")
print("=" * 60)

if failed == 0:
    print("ALL TESTS PASSED!")
else:
    print(f"{failed} test(s) need attention.")
    sys.exit(1)
