
from flask import Flask, render_template, request, jsonify
from falkordb import FalkorDB
from investigation import get_investigation
from ai_investigator import generate_ai_analysis
from graph_explorer import get_graph_evidence
from datetime import datetime, timezone


app = Flask(__name__)

ALLOWED_SCENARIOS = {
    "wayanad": "Wayanad, Kerala",
    "assam": "Assam River Flooding",
}


def get_selected_scenario():
    """Return a validated scenario ID from the request."""

    if request.is_json:
        data = request.get_json(silent=True) or {}
        scenario_id = data.get("scenario_id", "wayanad")
    else:
        scenario_id = request.args.get("scenario_id", "wayanad")

    if not isinstance(scenario_id, str):
        return None

    scenario_id = scenario_id.strip().lower()

    if scenario_id not in ALLOWED_SCENARIOS:
        return None

    return scenario_id


@app.route("/")
def dashboard():
    scenario_id = get_selected_scenario()

    if scenario_id is None:
        return "Invalid scenario. Choose wayanad or assam.", 400

    try:
        case = get_investigation(scenario_id=scenario_id)

        return render_template(
            "index.html",
            case=case,
            scenario_id=scenario_id,
            scenarios=ALLOWED_SCENARIOS,
        )

    except Exception:
        app.logger.exception("Dashboard loading failed")
        return "Could not load the investigation. Check the server terminal.", 500


@app.route("/api/investigate", methods=["POST"])
def investigate():
    scenario_id = get_selected_scenario()

    if scenario_id is None:
        return jsonify({
            "error": "Invalid scenario. Choose wayanad or assam."
        }), 400

    try:
        case = get_investigation(scenario_id=scenario_id)

        if case is None:
            return jsonify({
                "error": "No matching investigation found."
            }), 404

        return jsonify(case)

    except Exception:
        app.logger.exception("Investigation failed")
        return jsonify({
            "error": "Investigation failed. Check the server terminal."
        }), 500


@app.route("/api/ai-investigate", methods=["POST"])
def ai_investigate():
    scenario_id = get_selected_scenario()

    if scenario_id is None:
        return jsonify({
            "error": "Invalid scenario. Choose wayanad or assam."
        }), 400

    try:
        case = get_investigation(scenario_id=scenario_id)

        if case is None:
            return jsonify({
                "error": "No matching investigation found."
            }), 404

        analysis = generate_ai_analysis(case)

        return jsonify({
            "case_id": case.get("case_id"),
            "scenario_id": scenario_id,
            "ai_analysis": analysis,
        })

    except Exception:
        app.logger.exception("AI investigation failed")
        return jsonify({
            "error": (
                "AI investigation failed. "
                "Check the server terminal and try again."
            )
        }), 500


@app.route("/api/update-route", methods=["POST"])
def update_route():
    data = request.get_json(silent=True) or {}
    status = data.get("status")
    scenario_id = data.get("scenario_id", "wayanad")

    if not isinstance(scenario_id, str):
        return jsonify({"error": "Invalid scenario."}), 400

    scenario_id = scenario_id.strip().lower()

    if scenario_id not in ALLOWED_SCENARIOS:
        return jsonify({
            "error": "Invalid scenario. Choose wayanad or assam."
        }), 400

    if status not in ("Disrupted", "Operational"):
        return jsonify({
            "error": "Invalid route status."
        }), 400

    try:
        db = FalkorDB(host="localhost", port=6379)
        graph = db.select_graph("aidtrace")

        result = graph.query("""
            MATCH (route:Route {
                id: 'ROUTE-001',
                scenario_id: $scenario_id
            })
            SET route.status = $status
            RETURN route.name, route.status
        """, {
            "status": status,
            "scenario_id": scenario_id,
        })

        if not result.result_set:
            return jsonify({
                "error": (
                    "No matching route was found for the selected scenario."
                )
            }), 404

        route_name, route_status = result.result_set[0]

        return jsonify({
            "scenario_id": scenario_id,
            "route": route_name,
            "route_status": route_status,
            "message": "Route status updated successfully.",
        })

    except Exception:
        app.logger.exception("Route update failed")
        return jsonify({
            "error": (
                "Could not update route status. "
                "Check the server terminal."
            )
        }), 500


@app.route("/api/graph-evidence", methods=["GET"])
def graph_evidence():
    scenario_id = get_selected_scenario()

    if scenario_id is None:
        return jsonify({
            "error": "Invalid scenario. Choose wayanad or assam."
        }), 400

    try:
        data = get_graph_evidence(scenario_id=scenario_id)
        return jsonify(data)

    except Exception:
        app.logger.exception("Graph evidence retrieval failed")
        return jsonify({
            "error": (
                "Could not retrieve graph evidence. "
                "Check the server terminal."
            )
        }), 500



@app.route("/api/update-node", methods=["POST"])
def update_node():
    data = request.get_json(silent=True) or {}

    scenario_id = data.get("scenario_id")
    node_id = data.get("node_id")
    property_name = data.get("property")
    new_value = data.get("new_value")
    reason = data.get("reason")

    if not isinstance(scenario_id, str):
        return jsonify({"error": "Invalid scenario."}), 400

    scenario_id = scenario_id.strip().lower()

    if scenario_id not in ALLOWED_SCENARIOS:
        return jsonify({"error": "Invalid scenario."}), 400

    try:
        node_id = int(node_id)
        if node_id < 0:
            raise ValueError
    except (TypeError, ValueError):
        return jsonify({"error": "Invalid node ID."}), 400

    if not isinstance(property_name, str):
        return jsonify({"error": "Invalid property name."}), 400

    if not isinstance(reason, str) or not reason.strip():
        return jsonify({"error": "A reason for the change is required."}), 400

    # Explicit allowlist: only these properties can be edited.
    editable_properties = {
        "name": "text",
        "description": "text",
        "status": "text",
        "quantity": "number",
        "reported_quantity": "number",
        "confirmed_quantity": "number",
    }

    if property_name not in editable_properties:
        return jsonify({
            "error": "This property cannot be edited."
        }), 400

    property_type = editable_properties[property_name]

    if property_type == "text":
        if not isinstance(new_value, str) or not new_value.strip():
            return jsonify({
                "error": "Enter a non-empty text value."
            }), 400
    else:
        if (
            isinstance(new_value, bool)
            or not isinstance(new_value, (int, float))
        ):
            return jsonify({
                "error": "Enter a valid numeric value."
            }), 400

        if new_value < 0:
            return jsonify({
                "error": "Quantity cannot be negative."
            }), 400

        if isinstance(new_value, float) and not new_value.is_integer():
            return jsonify({
                "error": "Quantity must be a whole number."
            }), 400

        new_value = int(new_value)

    timestamp = datetime.now(timezone.utc).isoformat()

    # The property identifier is safe because it comes from the allowlist.
    property_expression = f"n.{property_name}"

    query = f"""
        MATCH (n)
        WHERE id(n) = $node_id
          AND n.scenario_id = $scenario_id
          AND EXISTS(n.{property_name})
        WITH n, {property_expression} AS old_value
        WHERE old_value <> $new_value
        SET {property_expression} = $new_value
        CREATE (a:AuditLog {{
            scenario_id: $scenario_id,
            node_id: toString(id(n)),
            node_labels: labels(n),
            property: $property_name,
            old_value: toString(old_value),
            new_value: toString($new_value),
            reason: $reason,
            timestamp: $timestamp
        }})
        RETURN old_value,
               {property_expression} AS new_value,
               id(a) AS audit_id
    """

    try:
        db = FalkorDB(host="localhost", port=6379)
        graph = db.select_graph("aidtrace")

        result = graph.query(query, {
            "node_id": node_id,
            "scenario_id": scenario_id,
            "new_value": new_value,
            "property_name": property_name,
            "reason": reason.strip(),
            "timestamp": timestamp,
        })

        if not result.result_set:
            return jsonify({
                "error": (
                    "No change was saved. The node may not belong to this "
                    "scenario, the property may be missing, or the value "
                    "may already be unchanged."
                )
            }), 400

        old_value, saved_value, audit_id = result.result_set[0]

        return jsonify({
            "message": "Node updated and audit entry created.",
            "scenario_id": scenario_id,
            "node_id": node_id,
            "property": property_name,
            "old_value": old_value,
            "new_value": saved_value,
            "reason": reason.strip(),
            "timestamp": timestamp,
            "audit_id": audit_id,
        }), 200

    except Exception:
        app.logger.exception("Node update failed")
        return jsonify({
            "error": "Could not update the node. Check the server terminal."
        }), 500


if __name__ == "__main__":
    app.run(debug=True)
