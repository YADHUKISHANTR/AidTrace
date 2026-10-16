
import investigation


def fake_investigation(
    route_status="Disrupted",
    reported=120,
    confirmed=70
):
    """Provide predictable test data without connecting to FalkorDB."""
    gap = max(reported - confirmed, 0)

    leads = []

    if gap > 0:
        leads.append({
            "title": "Unconfirmed delivery quantity",
            "status": "Unresolved"
        })

    if route_status == "Disrupted":
        leads.append({
            "title": "Transport route requires review",
            "status": "Unverified"
        })

    leads.append({
        "title": "Recorded warehouse stock",
        "status": "Unverified"
    })

    return {
        "case_id": "REQ-001",
        "requested": 120,
        "reported": reported,
        "confirmed": confirmed,
        "gap": gap,
        "route_status": route_status,
        "leads": leads
    }


def test_unconfirmed_quantity_is_50(monkeypatch):
    monkeypatch.setattr(
        investigation,
        "get_investigation",
        lambda: fake_investigation()
    )

    case = investigation.get_investigation()

    assert case["reported"] == 120
    assert case["confirmed"] == 70
    assert case["gap"] == 50


def test_disrupted_route_adds_route_lead():
    case = fake_investigation(route_status="Disrupted")

    titles = [lead["title"] for lead in case["leads"]]

    assert "Transport route requires review" in titles


def test_operational_route_has_no_route_lead():
    case = fake_investigation(route_status="Operational")

    titles = [lead["title"] for lead in case["leads"]]

    assert "Transport route requires review" not in titles
    assert case["gap"] == 50


def test_missing_investigation_is_handled(monkeypatch):
    monkeypatch.setattr(
        investigation,
        "get_investigation",
        lambda: None
    )

    assert investigation.get_investigation() is None
