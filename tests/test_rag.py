from app.rag import retrieve

def test_high_bill_retrieval():
    assert "BILL-001" in [d.policy_id for d in retrieve("my bill is much higher than usual")]

def test_vulnerability_retrieval():
    assert "VULN-001" in [d.policy_id for d in retrieve("I use medical equipment and need extra support")]

def test_complaint_retrieval():
    assert "COMP-001" in [d.policy_id for d in retrieve("I want to complain to the Ombudsman")]
