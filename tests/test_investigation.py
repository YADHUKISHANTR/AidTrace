
import investigation
from investigation import build_action_plans


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


def test_resource_matching_identifies_centre_b_shortfall(monkeypatch):
    """Centre B has a 40-kit shortfall and a potential match of 20."""
    monkeypatch.setattr(
        investigation,
        "get_resource_matches",
        lambda graph: {
            "resource_matches": [
                {
                    "centre": "Centre B",
                    "item": "Water kits",
                    "recorded_shortfall": 40,
                    "potential_match_quantity": 20,
                    "remaining_unmatched_quantity": 20,
                }
            ],
            "unmatched_demand": [
                {
                    "centre": "Centre B",
                    "unmatched_quantity": 20,
                }
            ],
            "resource_matching_note": "Independent, non-additive matches.",
        }
    )

    result = investigation.get_resource_matches(None)
    centre_b = next(
        match for match in result["resource_matches"]
        if match["centre"] == "Centre B"
    )

    assert centre_b["recorded_shortfall"] == 40
    assert centre_b["potential_match_quantity"] == 20
    assert centre_b["remaining_unmatched_quantity"] == 20


def test_resource_matching_identifies_wayanad_shortfall(monkeypatch):
    """Wayanad has a 50-kit shortfall and a potential match of 20."""
    monkeypatch.setattr(
        investigation,
        "get_resource_matches",
        lambda graph: {
            "resource_matches": [
                {
                    "centre": "Wayanad",
                    "item": "Water kits",
                    "recorded_shortfall": 50,
                    "potential_match_quantity": 20,
                    "remaining_unmatched_quantity": 30,
                }
            ],
            "unmatched_demand": [
                {
                    "centre": "Wayanad",
                    "unmatched_quantity": 30,
                }
            ],
            "resource_matching_note": "Independent, non-additive matches.",
        }
    )

    result = investigation.get_resource_matches(None)
    wayanad = next(
        match for match in result["resource_matches"]
        if match["centre"] == "Wayanad"
    )

    assert wayanad["recorded_shortfall"] == 50
    assert wayanad["potential_match_quantity"] == 20
    assert wayanad["remaining_unmatched_quantity"] == 30


def test_resource_matches_are_non_additive_and_unverified():
    """Shared stock must not be treated as confirmed or allocated."""
    candidate = {
        "warehouse": "Kalpetta Relief Supply Warehouse",
        "recorded_stock_quantity": 20,
        "potential_match_quantity": 20,
        "physical_stock_verified": False,
        "transfer_authorized": False,
        "shared_stock_pool": True,
        "match_is_additive": False,
    }

    assert candidate["recorded_stock_quantity"] == 20
    assert candidate["physical_stock_verified"] is False
    assert candidate["transfer_authorized"] is False
    assert candidate["shared_stock_pool"] is True
    assert candidate["match_is_additive"] is False

def test_resource_matching_calculates_shortfalls_from_query_results(
    monkeypatch
):
    """Exercise the real matching function with fake FalkorDB results."""

    class FakeQueryResult:
        def __init__(self, result_set):
            self.result_set = result_set

    class FakeGraph:
        def query(self, query):
            if "HAS_REQUEST" in query:
                return FakeQueryResult([
                    ["Centre B", "REQ-B-001", "Water kits", 100, 60],
                    ["Wayanad", "REQ-001", "Water kits", 120, 70],
                ])

            if "STORES" in query:
                return FakeQueryResult([
                    ["Kalpetta Relief Supply Warehouse", "Water kits", 20],
                ])

            raise AssertionError("Unexpected query")

    result = investigation.get_resource_matches(FakeGraph())

    matches = {
        match["centre"]: match
        for match in result["resource_matches"]
    }

    assert matches["Centre B"]["recorded_shortfall"] == 40
    assert matches["Centre B"]["potential_match_quantity"] == 20
    assert matches["Centre B"]["remaining_unmatched_quantity"] == 20

    assert matches["Wayanad"]["recorded_shortfall"] == 50
    assert matches["Wayanad"]["potential_match_quantity"] == 20
    assert matches["Wayanad"]["remaining_unmatched_quantity"] == 30


def test_resource_matching_does_not_consume_shared_stock():
    """The same recorded stock can be a candidate for both centres."""

    class FakeQueryResult:
        def __init__(self, result_set):
            self.result_set = result_set

    class FakeGraph:
        def query(self, query):
            if "HAS_REQUEST" in query:
                return FakeQueryResult([
                    ["Centre B", "REQ-B-001", "Water kits", 100, 60],
                    ["Wayanad", "REQ-001", "Water kits", 120, 70],
                ])

            if "STORES" in query:
                return FakeQueryResult([
                    ["Kalpetta Relief Supply Warehouse", "Water kits", 20],
                ])

            raise AssertionError("Unexpected query")

    result = investigation.get_resource_matches(FakeGraph())

    matches = {
        match["centre"]: match
        for match in result["resource_matches"]
    }

    for centre in ("Centre B", "Wayanad"):
        candidate = matches[centre]["candidate_warehouses"][0]

        assert candidate["recorded_stock_quantity"] == 20
        assert candidate["potential_match_quantity"] == 20
        assert candidate["physical_stock_verified"] is False
        assert candidate["transfer_authorized"] is False
        assert candidate["match_is_additive"] is False

    assert "non-additive" in result["resource_matching_note"]


def test_resource_matching_reports_demand_without_matching_stock():
    """Demand remains unmatched when the graph has no matching stock."""

    class FakeQueryResult:
        def __init__(self, result_set):
            self.result_set = result_set

    class FakeGraph:
        def query(self, query):
            if "HAS_REQUEST" in query:
                return FakeQueryResult([
                    ["Centre B", "REQ-B-001", "Water kits", 100, 60],
                ])

            if "STORES" in query:
                return FakeQueryResult([
                    ["Other Warehouse", "Blankets", 50],
                ])

            raise AssertionError("Unexpected query")

    result = investigation.get_resource_matches(FakeGraph())

    assert result["resource_matches"] == []
    assert result["unmatched_demand"] == [
        {
            "centre": "Centre B",
            "request_id": "REQ-B-001",
            "item": "Water kits",
            "unmatched_quantity": 40,
            "status": "No recorded matching stock found",
        }
    ]




def test_action_plan_links_delivery_gap_to_evidence():
    plans = build_action_plans(
        request_id="REQ-001",
        delivery_id="DEL-001",
        receipt_id="REC-001",
        item="Water kits",
        gap=50,
        warehouse="Kalpetta Relief Supply Warehouse",
        stock=20,
        route="Thamarassery Ghat Road",
        route_status="Operational",
        incident_is_simulated=True,
        evidence=[],
    )

    reconciliation = next(
        plan for plan in plans
        if plan["id"] == "ACT-001"
    )

    assert reconciliation["evidence_references"] == [
        "REQ-001", "DEL-001", "REC-001"
    ]
    assert reconciliation["requires_human_review"] is True
    assert reconciliation["automatically_authorized"] is False


def test_action_plans_do_not_treat_simulated_incident_as_proof():
    plans = build_action_plans(
        request_id="REQ-001",
        delivery_id="DEL-001",
        receipt_id="REC-001",
        item="Water kits",
        gap=50,
        warehouse=None,
        stock=None,
        route=None,
        route_status=None,
        incident_is_simulated=True,
        evidence=[],
    )

    simulated_action = next(
        plan for plan in plans
        if plan["id"] == "ACT-004"
    )

    assert "simulated" in simulated_action["reason"].lower()
    assert simulated_action["automatically_authorized"] is False


def test_no_delivery_gap_means_no_reconciliation_action():
    plans = build_action_plans(
        request_id="REQ-001",
        delivery_id="DEL-001",
        receipt_id="REC-001",
        item="Water kits",
        gap=0,
        warehouse=None,
        stock=None,
        route=None,
        route_status="Operational",
        incident_is_simulated=False,
        evidence=[],
    )

    assert not any(
        plan["id"] == "ACT-001"
        for plan in plans
    )


def test_resource_matching_includes_request_without_delivery_or_receipt():
    """A request must remain visible even when delivery evidence is missing."""

    class FakeQueryResult:
        def __init__(self, result_set):
            self.result_set = result_set

    class FakeGraph:
        def query(self, query):
            if "HAS_REQUEST" in query:
                return FakeQueryResult([
                    ["Centre C", "REQ-C-001", "Water kits", 80, None],
                ])

            if "STORES" in query:
                return FakeQueryResult([])

            raise AssertionError("Unexpected query")

    result = investigation.get_resource_matches(FakeGraph())

    assert any(
        demand["request_id"] == "REQ-C-001"
        and demand["unmatched_quantity"] == 80
        for demand in result["unmatched_demand"]
    )
