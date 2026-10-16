
from flask import Flask, render_template, request, jsonify
from falkordb import FalkorDB

app = Flask(__name__)

def get_investigation():
    db = FalkorDB(host="localhost", port=6379)
    graph = db.select_graph("aidtrace")

    query = """
    MATCH (c:Community)-[:HAS_REQUEST]->(r:ReliefRequest)
          -[:FULFILLED_BY]->(d:Delivery)
          -[:HAS_RECEIPT]->(rec:Receipt)
    OPTIONAL MATCH (d)-[:TRANSPORTED_VIA]->(route:Route)
    OPTIONAL MATCH (incident:IncidentReport)-[:AFFECTS]->(route)
    OPTIONAL MATCH (w:Warehouse)-[:STORES]->(s:Supply)
    WHERE s.item = r.item
    RETURN c.name, r.id, r.item, r.quantity,
           d.reported_quantity, rec.confirmed_quantity,
           route.name, route.status, incident.description,
           w.name, s.quantity
    """

    result = graph.query(query)

    if not result.result_set:
        return None

    row = result.result_set[0]

    (
        community, request_id, item, requested,
        reported, confirmed, route, route_status,
        incident, warehouse, stock
    ) = row

    return {
        "community": community,
        "request_id": request_id,
        "item": item,
        "requested": requested,
        "reported": reported,
        "confirmed": confirmed,
        "gap": reported - confirmed,
        "route": route,
        "route_status": route_status,
        "incident": incident,
        "warehouse": warehouse,
        "stock": stock,
    }

@app.route("/")
def dashboard():
    case = get_investigation()
    return render_template("index.html", case=case)
@app.route("/api/investigate", methods=["POST"])
def investigate():
    try:
        case = get_investigation()

        if case is None:
            return jsonify({
                "error": "No matching investigation found."
            }), 404

        case["status"] = "Needs human review"

        case["leads"] = []

        if case["route_status"] == "Disrupted":
            case["leads"].append(
                "Investigate whether the route disruption affected the delivery."
            )

        if case["stock"] is not None and case["stock"] > 0:
            case["leads"].append(
                f"Verify whether {case['stock']} kits at "
                f"{case['warehouse']} are available and unallocated."
            )

        case["recommended_actions"] = [
            "Request additional receipt or handover evidence.",
            "Ask the delivery organisation to reconcile the reported quantity.",
            "Check route and dispatch records before drawing conclusions."
        ]

        return jsonify(case)

    except Exception:
        app.logger.exception("Investigation failed")
        return jsonify({
            "error": "Investigation failed. Check the server terminal."
        }), 500

    
@app.route("/api/update-route", methods=["POST"])
def update_route():
    data = request.get_json(silent=True) or {}
    status = data.get("status")

    # Only allow these two route statuses
    if status not in ("Disrupted", "Operational"):
        return jsonify({"error": "Invalid route status."}), 400

    try:
        db = FalkorDB(host="localhost", port=6379)
        graph = db.select_graph("aidtrace")

        query = f"""
        MATCH (route:Route {{id: 'ROUTE-001'}})
        SET route.status = '{status}'
        RETURN route.name, route.status
        """

        result = graph.query(query)

        if not result.result_set:
            return jsonify({
                "error": "Route ROUTE-001 was not found."
            }), 404

        route_name, route_status = result.result_set[0]

        return jsonify({
            "route": route_name,
            "route_status": route_status,
            "message": "Route status updated successfully."
        })

    except Exception:
        app.logger.exception("Route update failed")
        return jsonify({
            "error": "Could not update route status. Check the server terminal."
        }), 500

    
if __name__ == "__main__":
    app.run(debug=True)
