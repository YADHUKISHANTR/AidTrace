# AidTrace — Cypher Queries and Graph Algorithms

## 1. Overview

AidTrace is a graph-powered relief investigation prototype built with FalkorDB and Python.

It uses connected relief-operation records to help investigators examine reported deliveries, receipt confirmations, route information, incidents, warehouse stock, and potential resource gaps.

This document explains the graph queries used by AidTrace, the relationships they traverse, and how the retrieved information supports investigation.

**Important:** A discrepancy is an investigative lead, not proof of theft, fraud, or wrongdoing. Quantities and relationships should be verified against reliable operational records before decisions are made.

## 2. Technology and graph connection

AidTrace connects to FalkorDB using the Python client:

```python
from falkordb import FalkorDB

db = FalkorDB(host="localhost", port=6379)
graph = db.select_graph("aidtrace")
```

The application uses the `aidtrace` graph.

Cypher queries are submitted through the selected graph's `query()` method. Query results are processed by Python and returned to the application or displayed by the relevant script.

## 3. Graph data model

The graph represents relief operations through nodes and relationships.

### 3.1 Node labels

The current query code references these node labels:

| Label            | Purpose                                                   |
| ---------------- | --------------------------------------------------------- |
| `Community`      | Community or destination associated with a relief request |
| `ReliefRequest`  | Request for a relief item and quantity                    |
| `Delivery`       | Delivery record, including its reported quantity          |
| `Receipt`        | Receipt or confirmation record                            |
| `Route`          | Route associated with a delivery                          |
| `IncidentReport` | Reported incident that may affect a route                 |
| `Warehouse`      | Warehouse that stores supplies                            |
| `Supply`         | Supply item and its recorded quantity                     |

### 3.2 Important properties

The queries use the following properties:

| Property             | Meaning                                                 |
| -------------------- | ------------------------------------------------------- |
| `id`                 | Identifier used by some records                         |
| `name`               | Human-readable name                                     |
| `item`               | Relief item                                             |
| `quantity`           | Requested or available quantity, depending on node type |
| `reported_quantity`  | Quantity recorded as delivered                          |
| `confirmed_quantity` | Quantity confirmed by a receipt                         |
| `status`             | Recorded route status                                   |
| `description`        | Description of an incident                              |
| `scenario_id`        | Scenario identifier used to separate graph data         |

Property availability depends on the node type and the seeded record.

### 3.3 Relationships

The current queries use these relationship types:

| Relationship      | Meaning                                          |
| ----------------- | ------------------------------------------------ |
| `HAS_REQUEST`     | Connects a community to a relief request         |
| `FULFILLED_BY`    | Connects a relief request to a delivery          |
| `HAS_RECEIPT`     | Connects a delivery to a receipt                 |
| `TRANSPORTED_VIA` | Connects a delivery to a route                   |
| `AFFECTS`         | Connects an incident report to an affected route |
| `STORES`          | Connects a warehouse to a supply record          |

These relationships allow the application to follow a delivery from its original request through its reported delivery and receipt confirmation, then retrieve associated route, incident, and supply evidence.

## 4. Query 1 — Investigate delivery discrepancies

**Source:** `investigate.py`

### Purpose

Follow the connected path from a community to a relief request, delivery, and receipt. Return the requested, reported, and confirmed quantities and calculate the difference between reported and receipt-confirmed delivery.

### Cypher query

```cypher
MATCH (c:Community)-[:HAS_REQUEST]->(r:ReliefRequest)
      -[:FULFILLED_BY]->(d:Delivery)
      -[:HAS_RECEIPT]->(rec:Receipt)

RETURN
    c.name AS community,
    r.item AS item,
    r.quantity AS requested,
    d.reported_quantity AS reported_delivered,
    rec.confirmed_quantity AS confirmed,
    d.reported_quantity - rec.confirmed_quantity
        AS unconfirmed_quantity
```

### How it works

1. Finds a community connected to a relief request.
2. Follows the request to its delivery record.
3. Follows the delivery to its receipt.
4. Returns the relevant quantities.
5. Calculates the difference between reported delivery and receipt-confirmed delivery.

The calculated difference is:

`reported_quantity - confirmed_quantity`

For example, if a delivery reports 120 units and its receipt confirms 70 units, the difference is 50 units.

That difference indicates a quantity that has not yet been reconciled between those two records. It does not, by itself, establish why the figures differ.

### Current limitation to consider

This query uses `MATCH` for every relationship in the evidence chain. As a result, a request without a delivery or a delivery without a receipt will not appear in these results.

The query also does not filter on `scenario_id`. If the same graph contains records from multiple scenarios, scenario filtering should be added before relying on its results for scenario-specific totals.

## 5. Query 2 — Trace connected evidence

**Source:** `trace_evidence.py`

### Purpose

Retrieve the delivery discrepancy together with related route, incident, warehouse, and supply information.

This query extends the basic investigation by collecting context that may help an investigator understand a discrepancy.

### Cypher query

```cypher
MATCH (c:Community)-[:HAS_REQUEST]->(r:ReliefRequest)
      -[:FULFILLED_BY]->(d:Delivery)
      -[:HAS_RECEIPT]->(rec:Receipt)

OPTIONAL MATCH (d)-[:TRANSPORTED_VIA]->(route:Route)
OPTIONAL MATCH (incident:IncidentReport)-[:AFFECTS]->(route)

OPTIONAL MATCH (w:Warehouse)-[:STORES]->(s:Supply)
WHERE s.item = r.item

RETURN
    c.name AS community,
    r.item AS item,
    d.reported_quantity AS reported,
    rec.confirmed_quantity AS confirmed,
    d.reported_quantity - rec.confirmed_quantity AS gap,
    route.name AS route,
    route.status AS route_status,
    incident.description AS incident,
    w.name AS warehouse,
    s.quantity AS stock_quantity
```

### How it works

- The initial `MATCH` retrieves the community, request, delivery, and receipt.
- The first `OPTIONAL MATCH` looks for a route linked to the delivery.
- The second `OPTIONAL MATCH` looks for an incident affecting that route.
- The final `OPTIONAL MATCH` looks for warehouse supply records whose item matches the requested item.
- The `RETURN` clause combines the delivery figures with the related evidence.

`OPTIONAL MATCH` is useful because the absence of a route, incident, or matching supply record should not necessarily prevent the core delivery evidence from being returned.

### How the results are interpreted

The Python code in `trace_evidence.py` checks the route status and recorded stock, then prints investigation guidance.

A recorded route disruption can be a reason to investigate whether the route affected a delivery. Recorded stock can indicate a potential source of supply, but availability, allocation, and delivery feasibility still need verification.

Neither relationship proves that a route disruption caused a discrepancy or that warehouse stock is available for immediate distribution.

### Current limitations to consider

- The query does not filter on `scenario_id`.
- The warehouse/supply match is based on item name, not on allocation, distance, availability, or delivery feasibility.
- If multiple routes, incidents, or matching supply records exist, the joins can produce multiple result rows.
- A missing receipt is not returned by the initial `MATCH`.
- The query should not be used to calculate aggregate stock totals without checking for duplicate rows and join multiplication.

These limitations should be addressed in the investigation logic before using the output as a complete inventory or reconciliation report.

## 6. Query 3 — Retrieve graph nodes for a scenario

**Source:** `graph_explorer.py`

### Purpose

Retrieve the nodes belonging to the selected scenario so the website can display their labels, properties, and identifiers in the graph evidence explorer.

### Cypher query

```cypher
MATCH (n)
WHERE n.scenario_id = $scenario_id
RETURN
    id(n) AS internal_id,
    labels(n) AS labels,
    properties(n) AS properties
```

### Parameters

The application passes `scenario_id` as a query parameter.

The current code accepts these scenario identifiers:

- `wayanad`
- `assam`

The code validates the scenario identifier before querying the graph.

### How it works

- `MATCH (n)` finds graph nodes.
- The `WHERE` clause retains nodes whose `scenario_id` matches the selected scenario.
- `id(n)` supplies the graph's internal identifier for the returned node.
- `labels(n)` returns its labels.
- `properties(n)` returns its stored properties.

The Python function converts the results into node objects for the frontend.

The graph explorer is read-only when retrieving these nodes. Editing is handled separately through the application's update functionality.

## 7. Query 4 — Retrieve relationships for a scenario

**Source:** `graph_explorer.py`

### Purpose

Retrieve directed relationships whose source and target nodes both belong to the selected scenario.

### Cypher query

```cypher
MATCH (source)-[r]->(target)
WHERE source.scenario_id = $scenario_id
  AND target.scenario_id = $scenario_id
RETURN
    id(source) AS source_id,
    type(r) AS relationship_type,
    properties(r) AS relationship_properties,
    id(target) AS target_id
```

### How it works

- Matches directed relationships between nodes.
- Filters both endpoints by the selected scenario.
- Returns the source and target identifiers.
- Returns the relationship type and its properties.

The Python code also checks that both endpoints exist in the set of returned nodes before including a relationship in the graph visualization.

This helps keep the displayed graph consistent with the selected scenario.

## 8. Scenario isolation

Scenario isolation is important because AidTrace supports Wayanad and Assam.

The graph explorer explicitly filters nodes and relationships using the `scenario_id` parameter. The investigation queries shown earlier do not currently include that filter.

For consistent scenario-specific investigation, the investigation queries should use a scenario filter on the relevant records, with the parameter supplied separately from the query text.

For example, the following is an **illustrative query pattern**, not a claim that the current investigation script already implements it:

```cypher
MATCH (c:Community)-[:HAS_REQUEST]->(r:ReliefRequest)
      -[:FULFILLED_BY]->(d:Delivery)
      -[:HAS_RECEIPT]->(rec:Receipt)
WHERE c.scenario_id = $scenario_id
  AND r.scenario_id = $scenario_id
  AND d.scenario_id = $scenario_id
  AND rec.scenario_id = $scenario_id

RETURN
    c.name AS community,
    r.item AS item,
    r.quantity AS requested,
    d.reported_quantity AS reported_delivered,
    rec.confirmed_quantity AS confirmed,
    d.reported_quantity - rec.confirmed_quantity
        AS unconfirmed_quantity
```

This pattern assumes that all four node types have a populated `scenario_id` property. The actual schema and seed data must be checked before adopting it.

The same principle should be applied to connected routes, incidents, warehouses, and supply records. A scenario filter on only one node is not sufficient if related records from another scenario can be joined into the same result.

## 9. Resource matching

AidTrace uses the relationship between warehouse and supply records, along with item names and quantities, to help identify potential resource matches.

The evidence query includes this pattern:

```cypher
OPTIONAL MATCH (w:Warehouse)-[:STORES]->(s:Supply)
WHERE s.item = r.item
```

This matches supply records with the same item name as the requested item.

**Matching an item is not the same as confirming that the item can fulfil a request.**

A reliable resource allocation calculation should consider, as applicable:

- The requested item and quantity.
- The quantity actually available.
- Existing allocations or reservations.
- The scenario and destination.
- Whether the stock is reachable and deliverable.
- Whether the same stock record is being counted more than once.

The query above retrieves related supply evidence; it does not, by itself, implement all those checks.

## 10. Route updates and node edits

The graph evidence queries described above are read queries. They retrieve data but do not modify it.

AidTrace's Flask backend also exposes route and node update endpoints. The node update functionality supports eligible properties including `name`, `description`, `status`, `quantity`, `reported_quantity`, and `confirmed_quantity`, and requires a reason for the change.

For example, an investigator might correct a stock quantity from 40 to 50 after a physical recount. The change should only be made when supported by reliable evidence.

The update process should validate the node and property, write the change to FalkorDB, and record the reason and old/new values in the audit history.

The update endpoint's actual Cypher statement should be documented here after extracting it from the current backend implementation. This document does not invent a write query for that endpoint.

## 11. Graph algorithms and investigation reasoning

The current query patterns primarily use Cypher graph traversal and filtering rather than a separately implemented graph-algorithm library.

The principal operations are:

1. **Relationship traversal:** Follow the path from a community's request to a delivery and receipt.
2. **Discrepancy calculation:** Subtract receipt-confirmed quantity from reported delivery quantity.
3. **Evidence enrichment:** Retrieve connected routes, incidents, warehouses, and supply records.
4. **Scenario filtering:** Retrieve graph nodes and relationships for the selected scenario.
5. **Item matching:** Identify supply records whose item matches a relief request.

These operations provide structured evidence for the application's investigation output.

The presence of a discrepancy does not prove wrongdoing. Investigators should inspect the supporting records and confirm the context before acting on a finding.

## 12. Query limitations and next steps

The current query implementation should be reviewed for the following issues:

- Add consistent scenario filtering to investigation and evidence queries.
- Decide how requests with no delivery or deliveries with no receipt should appear in investigation results.
- Avoid duplicate counts when multiple routes, incidents, or supply records match.
- Distinguish reported, confirmed, unconfirmed, and available quantities clearly.
- Ensure stock matching does not treat every item-name match as available inventory.
- Verify that a node edit refreshes the relevant investigation results.
- Test queries against both Wayanad and Assam seed data.

These checks are necessary to ensure that findings remain explainable and that scenario results do not accidentally include unrelated records.

## 13. Source files

The relevant implementation files are:

- [`investigate.py`](../investigate.py) — basic delivery discrepancy query.
- [`trace_evidence.py`](../trace_evidence.py) — delivery evidence and related route, incident, and supply query.
- [`graph_explorer.py`](../graph_explorer.py) — scenario-filtered graph nodes and relationships.
- [`app.py`](../app.py) — Flask routes, including investigation and graph update endpoints.

The implementation in these files is the source of truth. When queries change, this document should be updated to match the actual code.

---

**AidTrace uses FalkorDB to traverse connected relief records and retrieve evidence that supports investigation.** Its purpose is to help investigators identify discrepancies, explore possible explanations, and make informed decisions—not to treat a graph relationship or numerical difference as proof of misconduct.
