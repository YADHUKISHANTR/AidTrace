
from flask import Flask, render_template, request, jsonify
from falkordb import FalkorDB
from investigation import get_investigation

app = Flask(__name__)


@app.route("/")
def dashboard():
    try:
        case = get_investigation()
        return render_template("index.html", case=case)

    except Exception:
        app.logger.exception("Dashboard loading failed")
        return "Could not load the investigation. Check the server terminal.", 500


@app.route("/api/investigate", methods=["POST"])
def investigate():
    try:
        case = get_investigation()

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


@app.route("/api/update-route", methods=["POST"])
def update_route():
    data = request.get_json(silent=True) or {}
    status = data.get("status")

    if status not in ("Disrupted", "Operational"):
        return jsonify({
            "error": "Invalid route status."
        }), 400

    try:
        db = FalkorDB(host="localhost", port=6379)
        graph = db.select_graph("aidtrace")

        result = graph.query("""
            MATCH (route:Route {id: 'ROUTE-001'})
            SET route.status = $status
            RETURN route.name, route.status
        """, {"status": status})

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
            "error": "Could not update route status. "
                     "Check the server terminal."
        }), 500


if __name__ == "__main__":
    app.run(debug=True)
