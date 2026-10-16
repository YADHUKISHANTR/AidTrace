
from investigation import get_investigation
from ai_investigator import generate_ai_analysis


def test_ai_analysis_does_not_overstate_confidence():
    case = get_investigation()
    assert case is not None

    analysis = generate_ai_analysis(case)

    if case.get("gap", 0) > 0:
        assert analysis["confidence"] != "High", (
            "Confidence should not be High while the quantity gap "
            "remains unresolved."
        )


def test_ai_analysis_does_not_blame_simulated_incident():
    case = get_investigation()
    assert case is not None

    if not case.get("incident_is_simulated"):
        return

    analysis = generate_ai_analysis(case)

    explanations = " ".join(
        analysis["possible_explanations"]
    ).lower()

    forbidden_phrases = [
        "simulated incident caused",
        "simulated disruption caused",
        "real-world transit delays",
        "real world transit delays",
    ]

    for phrase in forbidden_phrases:
        assert phrase not in explanations, (
            f"AI explanation improperly references a simulated cause: "
            f"{phrase}"
        )
