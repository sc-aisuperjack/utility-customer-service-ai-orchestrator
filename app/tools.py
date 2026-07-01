from typing import Dict, Any, List
from datetime import datetime, timedelta
from app.schemas import ToolCallResult

CUSTOMERS = {
    "CUST001": {"customer_id": "CUST001", "name": "Sam Taylor", "authenticated": True, "psr": False, "account_id": "ACC001", "preferred_channel": "chat", "address_area": "Windsor"},
    "CUST002": {"customer_id": "CUST002", "name": "Amina Khan", "authenticated": True, "psr": True, "account_id": "ACC002", "preferred_channel": "voice", "address_area": "Slough"},
    "ANON": {"customer_id": "ANON", "name": None, "authenticated": False, "psr": False, "account_id": None, "preferred_channel": "unknown", "address_area": None},
}

BILLING = {
    "ACC001": {"account_id": "ACC001", "current_balance": 246.82, "last_bill": 162.40, "billing_period_days": 42, "meter_read_type": "estimated", "tariff": "Standard Variable", "direct_debit_status": "active", "debt_recovery_amount": 0.0, "smart_meter_connected": False, "usage_change_percent": 31},
    "ACC002": {"account_id": "ACC002", "current_balance": 81.10, "last_bill": 79.20, "billing_period_days": 31, "meter_read_type": "smart", "tariff": "Fixed May 2026", "direct_debit_status": "active", "debt_recovery_amount": 0.0, "smart_meter_connected": True, "usage_change_percent": 2},
}

DIRECT_DEBITS = {
    "ACC001": {
        "account_id": "ACC001",
        "payment_amount": 145.00,
        "payment_date": "15th of each month",
        "payment_method": "Direct Debit",
        "status": "active",
        "change_allowed": True,
    },
    "ACC002": {
        "account_id": "ACC002",
        "payment_amount": 82.00,
        "payment_date": "1st of each month",
        "payment_method": "Direct Debit",
        "status": "active",
        "change_allowed": True,
    },
}

APPOINTMENTS = {
    "ACC001": [{"appointment_id": "APT1001", "type": "boiler_service", "date": (datetime.now() + timedelta(days=5)).strftime("%Y-%m-%d"), "window": "08:00-12:00", "status": "booked"}],
    "ACC002": []
}

def result(tool_name: str, status: str, data: Dict[str, Any] | None = None, error: str | None = None) -> ToolCallResult:
    return ToolCallResult(tool_name=tool_name, status=status, data=data or {}, error=error)

def get_customer_profile(customer_id: str) -> ToolCallResult:
    return result("get_customer_profile", "success", CUSTOMERS.get(customer_id, CUSTOMERS["ANON"]))

def get_billing_summary(account_id: str | None) -> ToolCallResult:
    if not account_id:
        return result("get_billing_summary", "needs_authentication", error="authentication_required")
    data = BILLING.get(account_id)
    if not data:
        return result("get_billing_summary", "error", error="account_not_found")
    return result("get_billing_summary", "success", data)

def get_direct_debit_summary(account_id: str | None) -> ToolCallResult:
    if not account_id:
        return result(
            "get_direct_debit_summary",
            "needs_authentication",
            error="authentication_required"
        )

    data = DIRECT_DEBITS.get(account_id)

    if not data:
        return result(
            "get_direct_debit_summary",
            "error",
            error="direct_debit_not_found"
        )

    return result("get_direct_debit_summary", "success", data)

def get_appointments(account_id: str | None) -> ToolCallResult:
    if not account_id:
        return result("get_appointments", "needs_authentication", error="authentication_required")
    return result("get_appointments", "success", {"appointments": APPOINTMENTS.get(account_id, [])})

def submit_meter_reading(account_id: str | None, reading: str) -> ToolCallResult:
    if not account_id:
        return result("submit_meter_reading", "needs_authentication", error="authentication_required")
    return result("submit_meter_reading", "needs_confirmation", {"account_id": account_id, "reading": reading, "confirmation_required": True})

def create_complaint(account_id: str | None, summary: str) -> ToolCallResult:
    if not account_id:
        return result("create_complaint", "needs_authentication", {"summary": summary, "next_step": "authenticate_customer"})
    return result("create_complaint", "needs_confirmation", {"complaint_summary": summary, "confirmation_required": True})

def create_payment_plan(account_id: str | None, amount: float | None = None) -> ToolCallResult:
    return result("create_payment_plan", "handoff_required", {"reason": "Payment plans are high-impact and may indicate vulnerability or financial difficulty.", "queue": "billing_support", "amount_requested": amount})

def handoff_to_agent(queue: str, reason_code: str, summary: str, context: Dict[str, Any] | None = None) -> ToolCallResult:
    return result("handoff_to_agent", "success", {"queue": queue, "reason_code": reason_code, "summary": summary, "context": context or {}})

def available_tools_manifest() -> List[Dict[str, Any]]:
    return [
        {"name": "get_customer_profile", "risk": "low", "requires_confirmation": False},
        {"name": "get_billing_summary", "risk": "medium", "requires_confirmation": False},
        {"name": "get_appointments", "risk": "low", "requires_confirmation": False},
        {"name": "submit_meter_reading", "risk": "medium", "requires_confirmation": True},
        {"name": "create_complaint", "risk": "high", "requires_confirmation": True},
        {"name": "create_payment_plan", "risk": "high", "requires_confirmation": True},
        {"name": "handoff_to_agent", "risk": "medium", "requires_confirmation": False},
    ]
