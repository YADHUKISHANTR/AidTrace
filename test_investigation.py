
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


def fake_cross_centre_findings():
    """Synthetic cross-centre findings for isolated tests."""
    return [
        {
            "title": "Confirmed quantity exceeds request",
            "centre": "Centre A",
            "item": "Water kits",
            "requested_quantity": 100,
            "confirmed_quantity": 140,
            "variance": 40,
            "status": "Requires verification"
        },
        {
            "title": "Confirmed quantity below request",
            "centre": "Centre B",
            "item": "Water kits",
            "requested_quantity": 100,
            "confirmed_quantity": 60,
            "variance": -40,
            "status": "Requires verification"
        },
        {
            "title": "Potential cross-centre allocation imbalance",
            "item": "Water kits",
            "centres": ["Centre A", "Centre B"],
            "status": "Investigation lead only",
            "next_step": (
                "Verify current stock and transfer authority. "
                "Do not assume the excess is available or transferable."
            )
        }
    ]


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


def test_centre_a_excess_is_40():
    findings = fake_cross_centre_findings()

    centre_a = next(
        finding for finding in findings
        if finding.get("centre") == "Centre A"
    )

    assert centre_a["variance"] == 40
    assert centre_a["confirmed_quantity"] == 140
    assert centre_a["status"] == "Requires verification"


def test_centre_b_shortfall_is_40():
    findings = fake_cross_centre_findings()

    centre_b = next(
        finding for finding in findings
        if finding.get("centre") == "Centre B"
    )

    assert centre_b["variance"] == -40
    assert centre_b["confirmed_quantity"] == 60
    assert centre_b["status"] == "Requires verification"


def test_allocation_imbalance_is_not_transfer_authority():
    findings = fake_cross_centre_findings()

    imbalance = next(
        finding for finding in findings
        if finding["title"] == "Potential cross-centre allocation imbalance"
    )

    assert imbalance["status"] == "Investigation lead only"
    assert "Do not assume" in imbalance["next_step"]
    assert "transfer authority" in imbalance["next_step"]


def test_original_case_and_cross_centre_findings_are_separate():
    original_case = fake_investigation()
    cross_centre_findings = fake_cross_centre_findings()

    assert original_case["case_id"] == "REQ-001"
    assert original_case["gap"] == 50

    assert any(
        finding.get("centre") == "Centre A"
        for finding in cross_centre_findings
    )
    assert any(
        finding.get("centre") == "Centre B"
        for finding in cross_centre_findings
    )
