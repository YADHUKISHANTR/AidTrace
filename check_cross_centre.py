from investigation import get_investigation

case = get_investigation()

if case is None:
    print("ERROR: No main investigation returned.")
else:
    print("Main case:", case["case_id"])
    print("Original unconfirmed quantity:", case["gap"])

    print("\nCross-centre findings:")
    for finding in case.get("cross_centre_findings", []):
        print(finding)

    print("\nCross-centre actions:")
    for action in case.get("cross_centre_actions", []):
        print("-", action)

    assert case["case_id"] == "REQ-001"
    assert case["gap"] == 50

    findings = case.get("cross_centre_findings", [])

    centre_a = [
        f for f in findings
        if f.get("centre") == "Centre A"
        and f.get("title") == "Confirmed quantity exceeds request"
    ]
    centre_b = [
        f for f in findings
        if f.get("centre") == "Centre B"
        and f.get("title") == "Confirmed quantity below request"
    ]

    assert centre_a and centre_a[0]["variance"] == 40
    assert centre_b and centre_b[0]["variance"] == -40

    print("\nSUCCESS: Live cross-centre checks passed.")
