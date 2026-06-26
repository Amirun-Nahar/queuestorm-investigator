"""Quick smoke test for the QueueStorm Investigator modules."""

# 1. Models
from models import (
    AnalyzeTicketRequest, AnalyzeTicketResponse,
    CaseType, Department, EvidenceVerdict, Priority,
)
print("[OK] models.py imports OK")

# 2. AI Engine
from ai_engine import analyze_ticket, _sanitize_reply
print("[OK] ai_engine.py imports OK")

# 3. Main app
from main import app
print("[OK] main.py imports OK")

# 4. Schema validation
req = AnalyzeTicketRequest(ticket_id="T1", complaint="Test complaint")
print(f"[OK] Request model: {req.model_dump()}")

resp = AnalyzeTicketResponse(
    ticket_id="T1",
    case_type=CaseType.payment_failed,
    department=Department.customer_support,
    priority=Priority.medium,
    relevant_transaction_id=None,
    evidence_verdict=EvidenceVerdict.insufficient_data,
    confidence_score=0.85,
    reasoning="Test reasoning",
    customer_reply="We are looking into your case.",
    human_review_required=False,
)
print(f"[OK] Response model: {resp.model_dump()}")

# 5. Safety shield
assert _sanitize_reply("Please send your PIN") != "Please send your PIN", "PIN not blocked!"
assert _sanitize_reply("We will refund you immediately") != "We will refund you immediately", "Refund promise not blocked!"
assert _sanitize_reply("We are investigating your case.") == "We are investigating your case.", "Safe text was wrongly blocked!"
print("[OK] Safety shield: all checks passed")

print("\nAll smoke tests passed!")
