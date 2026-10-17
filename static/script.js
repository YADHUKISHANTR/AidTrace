
const runButton = document.getElementById("run-investigation");
const investigationStatus = document.getElementById("investigation-status");
const routeSelect = document.getElementById("route-status-select");
const updateRouteButton = document.getElementById("update-route-button");
const routeUpdateStatus = document.getElementById("route-update-status");
const runAIButton = document.getElementById("run-ai-investigation");
const aiInvestigationStatus = document.getElementById("ai-investigation-status");
const aiAnalysisContainer = document.getElementById("ai-analysis");
const scenarioSelect = document.getElementById("scenario-select");

let aiAnalysisNeedsRefresh = false;

function getSelectedScenario() {
    return scenarioSelect?.value || new URLSearchParams(window.location.search).get("scenario_id") || "wayanad";
}

function updateText(id, value, fallback = "Not available") {
    const element = document.getElementById(id);
    if (element) {
        element.textContent =
            value !== undefined && value !== null && value !== ""
                ? String(value)
                : fallback;
    }
}

function formatValue(value) {
    if (value === undefined || value === null || value === "") {
        return "Not available";
    }
    if (typeof value === "object") {
        return JSON.stringify(value, null, 2);
    }
    return String(value);
}

async function readResponse(response) {
    let data;

    try {
        data = await response.json();
    } catch {
        throw new Error("The server returned an unreadable response.");
    }

    if (!response.ok) {
        throw new Error(data.error || data.message || `Request failed (${response.status}).`);
    }

    return data;
}


function renderActions(actions) {
    const container = document.getElementById("recommended-actions");

    if (!container) return;

    
    if (!Array.isArray(actions) || actions.length === 0) {
        return;
    }

    container.replaceChildren();

    actions.forEach((action) => {
        const item = document.createElement("li");
        item.className = "action-item";

        if (typeof action === "string") {
            const description = document.createElement("p");
            description.textContent = action;
            item.appendChild(description);
            container.appendChild(item);
            return;
        }

        // Also support structured actions if the API provides them.
        if (!action || typeof action !== "object") {
            return;
        }

        const title = document.createElement("h4");
        title.textContent =
            action.title || action.action || "Recommended action";
        item.appendChild(title);

        const description = document.createElement("p");
        description.textContent =
            action.description || action.reason || action.details || "";
        item.appendChild(description);

        if (
            action.requires_human_review ||
            action.automatically_authorized === false
        ) {
            const reviewNote = document.createElement("p");
            reviewNote.className = "human-review-note";
            reviewNote.textContent = "Requires human review";
            item.appendChild(reviewNote);
        }

        container.appendChild(item);
    });
}

function appendFindingDetail(container, label, value) {
    const detail = document.createElement("p");
    const strong = document.createElement("strong");
    strong.textContent = `${label}: `;
    detail.appendChild(strong);
    detail.appendChild(document.createTextNode(formatValue(value)));
    container.appendChild(detail);
}



function renderCrossCentreFindings(findings) {
    const container = document.getElementById("cross-centre-findings");
    const actionsContainer = document.getElementById("cross-centre-actions");

    if (!container) return;

    container.replaceChildren();

    if (!Array.isArray(findings) || findings.length === 0) {
        const message = document.createElement("p");
        message.className = "investigation-status";
        message.textContent =
            "No cross-centre discrepancy findings were returned by the current graph query.";
        container.appendChild(message);
        return;
    }

    findings.forEach((finding, index) => {
        const card = document.createElement("article");
        card.className = "evidence-row cross-centre-finding";

        const number = document.createElement("div");
        number.className = "evidence-index";
        number.textContent = String(index + 1).padStart(2, "0");
        card.appendChild(number);

        const content = document.createElement("div");
        content.className = "evidence-content";

        const title = document.createElement("h3");
        title.textContent = finding.title || finding.type || "Cross-centre finding";
        content.appendChild(title);

        function addDetail(label, value) {
            if (value === undefined || value === null || value === "") return;

            const paragraph = document.createElement("p");
            const strong = document.createElement("strong");
            strong.textContent = `${label}: `;
            paragraph.appendChild(strong);
            paragraph.appendChild(document.createTextNode(formatValue(value)));
            content.appendChild(paragraph);
        }

        addDetail("Centre", finding.centre);

        if (Array.isArray(finding.centres) && finding.centres.length) {
            addDetail("Centres compared", finding.centres.join(" ↔ "));
        }

        addDetail("Item", finding.item);
        addDetail("Request reference", finding.request_id);
        addDetail("Requested", finding.requested_quantity);
        addDetail("Reported delivered", finding.reported_quantity);
        addDetail("Receipt-confirmed", finding.confirmed_quantity);

        const description =
            finding.finding ||
            finding.description ||
            finding.summary;

        if (description) {
            const paragraph = document.createElement("p");
            paragraph.textContent = description;
            content.appendChild(paragraph);
        }

        addDetail(
            "Verification step",
            finding.next_step ||
            finding.verification_step
        );

        if (finding.evidence) addDetail("Evidence", finding.evidence);
        if (finding.uncertainty) addDetail("Uncertainty", finding.uncertainty);

        card.appendChild(content);

        const status = document.createElement("span");
        status.className = "tag";
        status.textContent = finding.status || "Requires verification";
        card.appendChild(status);

        container.appendChild(card);
    });

    // Preserve the checklist from the existing HTML instead of clearing it
    // and replacing it with a different list from the findings.
    // If the API provides explicit cross-centre actions, use those.
    if (actionsContainer) {
        const actions = findings
            .flatMap((finding) => finding.recommended_actions || [])
            .filter(Boolean);

        if (actions.length > 0) {
            actionsContainer.replaceChildren();

            actions.forEach((action, index) => {
                const item = document.createElement("li");

                const number = document.createElement("span");
                number.className = "action-number";
                number.textContent = String(index + 1);

                const description = document.createElement("p");
                description.textContent = typeof action === "string"
                    ? action
                    : action.title ||
                      action.description ||
                      JSON.stringify(action);

                item.append(number, description);
                actionsContainer.appendChild(item);
            });
        }
    }
}



function renderResourceMatching(data) {
    const matchesContainer = document.getElementById("resource-matches");
    const unmatchedContainer = document.getElementById("unmatched-resource-demand");
    const note = document.getElementById("resource-matching-note");

    if (matchesContainer) matchesContainer.replaceChildren();
    if (unmatchedContainer) unmatchedContainer.replaceChildren();

    if (!data) {
        if (note) note.textContent = "Resource-matching results are not available.";
        return;
    }

    const matches = data.matches || data.resource_matches || [];
    const unmatched = data.unmatched_demand || data.unmatched || [];

    if (note) {
        note.textContent = data.note || data.summary ||
            "Potential matches use recorded stock only. Physical availability, existing commitments, and transfer authority are unverified. Matches are not allocations, and the same stock may appear for multiple centres.";
    }

    if (matchesContainer) {
        if (!Array.isArray(matches) || matches.length === 0) {
            const message = document.createElement("p");
            message.textContent = "No matching recorded stock was found in this scenario.";
            matchesContainer.appendChild(message);
        } else {
            matches.forEach((match) => {
                const card = document.createElement("div");
                card.className = "resource-match-card";

                const title = document.createElement("h4");
                title.textContent = `${match.centre || "Centre"} — ${match.item || "Resource"}`;
                card.appendChild(title);

                const warehouses = match.candidate_warehouses
                    ?.map((entry) =>
                        `${entry.warehouse}: ${entry.recorded_stock_quantity} recorded units (unverified)`
                    )
                    .join("; ");

                appendFindingDetail(
                    card,
                    "Candidate warehouse(s)",
                    warehouses || "No recorded candidate warehouses"
                );

                appendFindingDetail(
                    card,
                    "Recorded shortfall",
                    match.recorded_shortfall
                );

                appendFindingDetail(
                    card,
                    "Potential match from recorded stock — not confirmed available",
                    match.potential_match_quantity
                );

                appendFindingDetail(
                    card,
                    "Shortfall remaining after potential matching — not confirmed covered",
                    match.remaining_unmatched_quantity
                );

                const caution = document.createElement("p");
                caution.className = "record-reference";
                caution.textContent =
                    "This is a planning lead, not confirmed supply coverage. Verify physical stock, duplicate records, existing commitments, and transfer authority before considering allocation.";
                card.appendChild(caution);

                matchesContainer.appendChild(card);
            });
        }
    }

    if (unmatchedContainer) {
        if (!Array.isArray(unmatched) || unmatched.length === 0) {
            const message = document.createElement("p");
            message.textContent =
                "No additional unmatched quantity was returned by the matching calculation. This does not mean demand is fulfilled or that candidate stock is available.";
            unmatchedContainer.appendChild(message);
        } else {
            unmatched.forEach((item) => {
                const entry = document.createElement("p");
                entry.textContent = typeof item === "string"
                    ? item
                    : `${item.item || item.resource || item.name || "Resource"}: ${formatValue(item.unmatched_quantity ?? item.shortfall ?? item.quantity ?? item)}`;
                unmatchedContainer.appendChild(entry);
            });
        }
    }
}


function renderActionPlans(actionPlans) {
    const section = document.getElementById("action-plans-section");
    if (!section || !Array.isArray(actionPlans)) return;

    let container = document.getElementById("action-plans-live");
    if (!container) {
        container = document.createElement("div");
        container.id = "action-plans-live";
        section.appendChild(container);
    }

    container.replaceChildren();

    if (actionPlans.length === 0) {
        const message = document.createElement("p");
        message.textContent = "No action plans are available for this investigation.";
        container.appendChild(message);
        return;
    }

    actionPlans.forEach((plan) => {
        const card = document.createElement("div");
        card.className = "action-plan-card";

        const title = document.createElement("h4");
        title.textContent = plan.title || plan.action || "Suggested next step";
        card.appendChild(title);

        appendFindingDetail(card, "Reason", plan.reason || plan.description);
        if (plan.supporting_evidence) {
            appendFindingDetail(card, "Supporting evidence", plan.supporting_evidence);
        }
        if (plan.uncertainty) {
            appendFindingDetail(card, "Uncertainty", plan.uncertainty);
        }

        const review = document.createElement("p");
        review.className = "record-reference";
        review.textContent = "Human review required. This recommendation is not automatically authorized.";
        card.appendChild(review);

        container.appendChild(card);
    });
}


function renderInvestigation(result) {
    // investigation.py returns a flat dictionary.
    updateText("requested-quantity", result.requested_quantity);
    updateText("reported-quantity", result.reported_delivered);
    updateText("confirmed-quantity", result.receipt_confirmed);
    updateText("unconfirmed-quantity", result.unconfirmed_quantity);

    updateText("delivery-description", result.reported_delivered);
    updateText("delivery-value", result.reported_delivered);
    updateText("delivery-reference", result.delivery_id);

    updateText("receipt-description", result.receipt_confirmed);
    updateText("receipt-value", result.receipt_confirmed);
    updateText("receipt-reference", result.receipt_id);

    updateText("route-name", result.route, "No route record available for this scenario");
    updateText("route-status", result.route_status, "No route record available");

    updateText(
        "incident-description",
        result.incident,
        "No linked incident lead is available. This does not establish that no disruption occurred."
    );

    updateText("warehouse-name", result.warehouse, "No warehouse record available");
    updateText("warehouse-stock", result.stock, "No stock quantity available");

    const routeExists = Boolean(result.route);

    if (routeSelect) routeSelect.disabled = !routeExists;
    if (updateRouteButton) updateRouteButton.disabled = !routeExists;

    if (routeUpdateStatus) {
        routeUpdateStatus.textContent = routeExists
            ? ""
            : "Route updates are unavailable because this scenario has no route record.";
    }

    renderActions(result.recommended_actions || []);
    renderCrossCentreFindings(result.cross_centre_findings || []);

    // The backend returns these fields at the top level.
    renderResourceMatching({
        matches: result.resource_matches || [],
        unmatched_demand: result.unmatched_demand || [],
        note: result.resource_matching_note || ""
    });

    // Action plans are already rendered by the Flask template.
    // Do not append a second set of cards here.

    if (investigationStatus) {
        investigationStatus.textContent =
            "Investigation complete. Review the linked records and uncertainty before acting.";
    }

    aiAnalysisNeedsRefresh = true;
}


function renderAIList(id, items) {
    const container = document.getElementById(id);
    if (!container) return;

    container.replaceChildren();

    if (!Array.isArray(items) || items.length === 0) {
        const message = document.createElement("li");
        message.textContent = "No items returned.";
        container.appendChild(message);
        return;
    }

    items.forEach((item) => {
        const element = document.createElement("li");
        element.textContent = typeof item === "string"
            ? item
            : item.description || item.title || JSON.stringify(item);
        container.appendChild(element);
    });
}

function renderAIAnalysis(data) {
    const analysis = data.analysis || data.ai_analysis || data;
    updateText("ai-summary", analysis.summary || analysis.overview);
    updateText("ai-evidence-assessment", analysis.evidence_assessment);
    renderAIList("ai-possible-explanations", analysis.possible_explanations || []);
    renderAIList("ai-recommended-actions", analysis.recommended_actions || []);
    updateText("ai-confidence", analysis.confidence);
    updateText("ai-limitations", analysis.limitations);

    if (aiAnalysisContainer) {
        aiAnalysisContainer.hidden = false;
    }
}

async function runAIInvestigation() {
    if (!runAIButton) return;

    runAIButton.disabled = true;
    if (aiInvestigationStatus) {
        aiInvestigationStatus.textContent = "Running AI analysis for the selected scenario…";
    }

    try {
        const response = await fetch("/api/ai-investigate", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ scenario_id: getSelectedScenario() })
        });

        const data = await readResponse(response);
        renderAIAnalysis(data);

        if (aiInvestigationStatus) {
            aiInvestigationStatus.textContent =
                "AI analysis complete. Treat explanations as hypotheses and verify them against the records.";
        }
        aiAnalysisNeedsRefresh = false;
    } catch (error) {
        if (aiInvestigationStatus) {
            aiInvestigationStatus.textContent = `AI analysis failed: ${error.message}`;
        }
    } finally {
        runAIButton.disabled = false;
    }
}

async function runInvestigation() {
    if (!runButton) return;

    runButton.disabled = true;
    if (investigationStatus) {
        investigationStatus.textContent = "Investigating the selected scenario…";
    }

    try {
        const response = await fetch("/api/investigate", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ scenario_id: getSelectedScenario() })
        });

        const data = await readResponse(response);
        renderInvestigation(data);

        if (investigationStatus) {
            investigationStatus.textContent = "Investigation complete.";
        }

                await loadGraphEvidence();

        // Scroll to the investigation results after they finish loading.
        const resultsSection =
            document.getElementById("action-plans-section");

        if (resultsSection) {
            resultsSection.scrollIntoView({
                behavior: "smooth",
                block: "start"
            });
        }

    } catch (error) {
        if (investigationStatus) {
            investigationStatus.textContent = `Investigation failed: ${error.message}`;
        }
    } finally {
        runButton.disabled = false;
    }
}

async function updateRouteStatus() {
    if (!updateRouteButton || !routeSelect) return;

    updateRouteButton.disabled = true;
    if (routeUpdateStatus) routeUpdateStatus.textContent = "Updating route status…";

    try {
        const response = await fetch("/api/update-route", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                status: routeSelect.value,
                scenario_id: getSelectedScenario()
            })
        });

        const data = await readResponse(response);

        if (routeUpdateStatus) {
            routeUpdateStatus.textContent = data.message || "Route status updated.";
        }

        await runInvestigation();
    } catch (error) {
        if (routeUpdateStatus) {
            routeUpdateStatus.textContent = `Route update failed: ${error.message}`;
        }
    } finally {
        updateRouteButton.disabled = !document.getElementById("route-status-select") ||
            document.getElementById("route-status-select").disabled;
    }
}

function getNodeLabel(node) {
    const properties = node.properties || {};
    return properties.name ||
        properties.id ||
        properties.item ||
        properties.description ||
        (node.labels || []).join(", ") ||
        "Graph node";
}

function getNodeType(node) {
    return (node.labels || []).find((label) => label !== "") || "Node";
}

function getNodeColor(node) {
    const type = getNodeType(node);

    const colors = {
        Community: "#2563eb",
        ReliefRequest: "#0d9488",
        Delivery: "#d97706",
        Receipt: "#16a34a",
        Route: "#7c3aed",
        Incident: "#dc2626",
        IncidentReport: "#dc2626",
        Warehouse: "#475569",
        Supply: "#0891b2"
    };

    return colors[type] || "#64748b";
}


function renderGraphEvidence(data) {
    const visualization = document.getElementById("graph-visualization");
    const nodeDetails = document.getElementById("graph-node-details");
    if (!visualization) return;

    visualization.replaceChildren();

    const nodes = Array.isArray(data.nodes) ? data.nodes : [];
    const relationships = Array.isArray(data.relationships)
        ? data.relationships
        : [];

    updateText("graph-node-count", data.node_count ?? nodes.length);
    updateText(
        "graph-relationship-count",
        data.relationship_count ?? relationships.length
    );

    if (nodes.length === 0) {
        const message = document.createElement("p");
        message.textContent =
            "No tagged graph records were found for this scenario.";
        visualization.appendChild(message);

        if (nodeDetails) {
            nodeDetails.textContent =
                "No nodes are available to inspect.";
        }
        return;
    }

    const width = Math.max(
        760,
        Math.min(1200, 180 * Math.ceil(Math.sqrt(nodes.length)))
    );
    const nodeWidth = 150;
    const nodeHeight = 58;
    const gapX = 34;
    const gapY = 54;
    const columns = Math.max(
        1,
        Math.floor((width - 30) / (nodeWidth + gapX))
    );
    const rows = Math.ceil(nodes.length / columns);
    const height = Math.max(
        330,
        rows * (nodeHeight + gapY) + 40
    );

    const svgNS = "http://www.w3.org/2000/svg";
    const svg = document.createElementNS(svgNS, "svg");
    svg.setAttribute("viewBox", `0 0 ${width} ${height}`);
    svg.setAttribute("width", "100%");
    svg.setAttribute("role", "img");
    svg.setAttribute("aria-label", "Scenario evidence graph");

    const positions = new Map();

    nodes.forEach((node, index) => {
        const column = index % columns;
        const row = Math.floor(index / columns);

        positions.set(String(node.id), {
            x: 15 + column * (nodeWidth + gapX),
            y: 20 + row * (nodeHeight + gapY)
        });
    });

    relationships.forEach((relationship) => {
        const source = positions.get(String(relationship.source));
        const target = positions.get(String(relationship.target));
        if (!source || !target) return;

        const line = document.createElementNS(svgNS, "line");
        line.setAttribute("x1", String(source.x + nodeWidth / 2));
        line.setAttribute("y1", String(source.y + nodeHeight / 2));
        line.setAttribute("x2", String(target.x + nodeWidth / 2));
        line.setAttribute("y2", String(target.y + nodeHeight / 2));
        line.setAttribute("stroke", "#94a3b8");
        line.setAttribute("stroke-width", "2");
        svg.appendChild(line);

        const label = document.createElementNS(svgNS, "text");
        label.setAttribute(
            "x",
            String((source.x + target.x + nodeWidth) / 2)
        );
        label.setAttribute(
            "y",
            String((source.y + target.y + nodeHeight) / 2 - 5)
        );
        label.setAttribute("font-size", "10");
        label.setAttribute("text-anchor", "middle");
        label.setAttribute("fill", "#475569");
        label.textContent = relationship.type || "RELATED";
        svg.appendChild(label);
    });

    let selectedGroup = null;

    function showNodeDetails(node, group) {
        if (!nodeDetails) return;

        if (selectedGroup) {
            selectedGroup.setAttribute("aria-pressed", "false");
            const oldRect = selectedGroup.querySelector("rect");
            if (oldRect) {
                oldRect.setAttribute("stroke", "#ffffff");
                oldRect.setAttribute("stroke-width", "1.5");
            }
        }

        selectedGroup = group;
        group.setAttribute("aria-pressed", "true");

        const rect = group.querySelector("rect");
        if (rect) {
            rect.setAttribute("stroke", "#fbbf24");
            rect.setAttribute("stroke-width", "3");
        }

        nodeDetails.replaceChildren();

        const heading = document.createElement("h4");
        heading.textContent = getNodeLabel(node);
        nodeDetails.appendChild(heading);

        const type = document.createElement("p");
        type.textContent = `Type: ${getNodeType(node)}`;
        nodeDetails.appendChild(type);

        const properties = node.properties || {};
        const pre = document.createElement("pre");
        pre.textContent = JSON.stringify(properties, null, 2);
        nodeDetails.appendChild(pre);

        const editButton = document.createElement("button");
        editButton.type = "button";
        editButton.textContent = "Edit node";
        editButton.className = "secondary-button";

        editButton.addEventListener("click", () => {
            showNodeEditor(node, nodeDetails);
        });

        nodeDetails.appendChild(editButton);
    }

    nodes.forEach((node) => {
        const position = positions.get(String(node.id));
        const group = document.createElementNS(svgNS, "g");

        group.setAttribute("tabindex", "0");
        group.setAttribute("role", "button");
        group.setAttribute("aria-pressed", "false");
        group.setAttribute("aria-label", `Inspect ${getNodeLabel(node)}`);
        group.style.cursor = "pointer";

        const rectangle = document.createElementNS(svgNS, "rect");
        rectangle.setAttribute("x", String(position.x));
        rectangle.setAttribute("y", String(position.y));
        rectangle.setAttribute("width", String(nodeWidth));
        rectangle.setAttribute("height", String(nodeHeight));
        rectangle.setAttribute("rx", "10");
        rectangle.setAttribute("fill", getNodeColor(node));
        rectangle.setAttribute("stroke", "#ffffff");
        rectangle.setAttribute("stroke-width", "1.5");
        group.appendChild(rectangle);

        const typeLabel = document.createElementNS(svgNS, "text");
        typeLabel.setAttribute(
            "x",
            String(position.x + nodeWidth / 2)
        );
        typeLabel.setAttribute("y", String(position.y + 20));
        typeLabel.setAttribute("text-anchor", "middle");
        typeLabel.setAttribute("font-size", "10");
        typeLabel.setAttribute("fill", "#ffffff");
        typeLabel.textContent = getNodeType(node);
        group.appendChild(typeLabel);

        const nameLabel = document.createElementNS(svgNS, "text");
        nameLabel.setAttribute(
            "x",
            String(position.x + nodeWidth / 2)
        );
        nameLabel.setAttribute("y", String(position.y + 40));
        nameLabel.setAttribute("text-anchor", "middle");
        nameLabel.setAttribute("font-size", "10");
        nameLabel.setAttribute("fill", "#ffffff");

        const labelText = getNodeLabel(node);
        nameLabel.textContent = labelText.length > 21
            ? `${labelText.slice(0, 18)}…`
            : labelText;

        group.appendChild(nameLabel);

        group.addEventListener("click", () => {
            showNodeDetails(node, group);
        });

        group.addEventListener("keydown", (event) => {
            if (event.key === "Enter" || event.key === " ") {
                event.preventDefault();
                showNodeDetails(node, group);
            }
        });

        svg.appendChild(group);
    });

    visualization.appendChild(svg);

    if (nodeDetails) {
        nodeDetails.textContent =
            "Select a node to inspect its record.";
    }
}


function showNodeEditor(node, container) {
    container.replaceChildren();

    const properties = node.properties || {};
    const editableProperties = new Set([
        "name",
        "description",
        "status",
        "quantity",
        "reported_quantity",
        "confirmed_quantity"
    ]);

    const heading = document.createElement("h4");
    heading.textContent = `Edit node: ${getNodeLabel(node)}`;
    container.appendChild(heading);

    const notice = document.createElement("p");
    notice.className = "record-reference";
    notice.textContent =
        "Edit one permitted property at a time. Every saved change requires a reason and creates an audit record.";
    container.appendChild(notice);

    const form = document.createElement("form");
    form.className = "node-editor-form";

    Object.entries(properties).forEach(([key, value]) => {
        const field = document.createElement("div");
        field.className = "node-editor-field";

        const label = document.createElement("label");
        label.textContent = key;
        label.htmlFor = `node-property-${key}`;
        field.appendChild(label);

        const input = document.createElement("input");
        input.id = `node-property-${key}`;
        input.name = key;
        input.value = value == null ? "" : String(value);

        const canEdit = editableProperties.has(key);

        input.disabled = !canEdit;
        if (!canEdit) {
            input.title = "This property is read-only.";
        }

        if (
            ["quantity", "reported_quantity", "confirmed_quantity"].includes(key)
        ) {
            input.type = "number";
            input.step = "1";
            input.min = "0";
            input.required = true;
        } else {
            input.type = "text";
        }

        field.appendChild(input);
        form.appendChild(field);
    });

    const reasonField = document.createElement("div");
    reasonField.className = "node-editor-field";

    const reasonLabel = document.createElement("label");
    reasonLabel.textContent = "Reason for change";
    reasonLabel.htmlFor = "node-edit-reason";
    reasonField.appendChild(reasonLabel);

    const reasonInput = document.createElement("textarea");
    reasonInput.id = "node-edit-reason";
    reasonInput.name = "reason";
    reasonInput.required = true;
    reasonInput.minLength = 3;
    reasonInput.placeholder =
        "Explain why this record needs to be corrected.";
    reasonField.appendChild(reasonInput);
    form.appendChild(reasonField);

    const buttons = document.createElement("div");
    buttons.className = "node-editor-buttons";

    const cancelButton = document.createElement("button");
    cancelButton.type = "button";
    cancelButton.textContent = "Cancel";
    cancelButton.addEventListener("click", () => {
        renderGraphEvidenceSelectionPlaceholder(container, node);
    });

    const previewButton = document.createElement("button");
    previewButton.type = "submit";
    previewButton.textContent = "Preview changes";

    buttons.append(cancelButton, previewButton);
    form.appendChild(buttons);

    form.addEventListener("submit", (event) => {
        event.preventDefault();

        if (!form.reportValidity()) return;

        const changes = [];

        for (const key of editableProperties) {
            if (!Object.prototype.hasOwnProperty.call(properties, key)) {
                continue;
            }

            const input = form.elements.namedItem(key);
            if (!input) continue;

            const oldValue = properties[key];
            let newValue = input.value;

            if (
                ["quantity", "reported_quantity", "confirmed_quantity"].includes(key)
            ) {
                if (newValue.trim() === "") {
                    input.setCustomValidity("Enter a whole number.");
                    input.reportValidity();
                    return;
                }

                newValue = Number(newValue);

                if (
                    !Number.isSafeInteger(newValue) ||
                    newValue < 0
                ) {
                    input.setCustomValidity(
                        "Enter a non-negative whole number."
                    );
                    input.reportValidity();
                    return;
                }

                input.setCustomValidity("");
            }

            if (String(newValue) !== String(oldValue ?? "")) {
                changes.push({
                    property: key,
                    old_value: oldValue,
                    new_value: newValue
                });
            }
        }

        container.replaceChildren();

        const previewHeading = document.createElement("h4");
        previewHeading.textContent = "Change preview";
        container.appendChild(previewHeading);

        if (changes.length === 0) {
            const message = document.createElement("p");
            message.textContent = "No property values were changed.";
            container.appendChild(message);
        } else {
            const list = document.createElement("pre");
            list.textContent = JSON.stringify(changes, null, 2);
            container.appendChild(list);
        }

        const reason = document.createElement("p");
        reason.textContent = `Reason: ${reasonInput.value.trim()}`;
        container.appendChild(reason);

        const explanation = document.createElement("p");
        explanation.className = "record-reference";
        explanation.textContent =
            "Review the change carefully. Nothing has been saved yet.";
        container.appendChild(explanation);

        const backButton = document.createElement("button");
        backButton.type = "button";
        backButton.textContent = "Back to editor";
        backButton.addEventListener("click", () => {
            showNodeEditor(node, container);
        });
        container.appendChild(backButton);

        if (changes.length !== 1) {
            const guidance = document.createElement("p");
            guidance.textContent = changes.length > 1
                ? "Save one property at a time. Return to the editor and change only one property."
                : "Change one editable property before saving.";
            container.appendChild(guidance);
            return;
        }

        const saveButton = document.createElement("button");
        saveButton.type = "button";
        saveButton.textContent = "Save changes";
        saveButton.className = "primary-button";
        container.appendChild(saveButton);

        const saveStatus = document.createElement("p");
        saveStatus.setAttribute("role", "status");
        saveStatus.setAttribute("aria-live", "polite");
        container.appendChild(saveStatus);

        saveButton.addEventListener("click", async () => {
            saveButton.disabled = true;
            backButton.disabled = true;
            saveStatus.textContent = "Saving change to FalkorDB…";

            try {
                const response = await fetch("/api/update-node", {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json"
                    },
                    body: JSON.stringify({
                        scenario_id: getSelectedScenario(),
                        node_id: node.id,
                        property: changes[0].property,
                        new_value: changes[0].new_value,
                        reason: reasonInput.value.trim()
                    })
                });

                const result = await readResponse(response);

                saveStatus.textContent =
                    result.message || "The server reported that the change was saved.";

                // Reload the graph and current investigation from the server.
                await runInvestigation();
            } catch (error) {
                saveStatus.textContent =
                    `Save failed: ${error.message}. Check the current database value before retrying.`;
                saveButton.disabled = false;
                backButton.disabled = false;
            }
        });
    });

    container.appendChild(form);
}

function renderGraphEvidenceSelectionPlaceholder(container, node) {
    const heading = document.createElement("h4");
    heading.textContent = getNodeLabel(node);

    const message = document.createElement("p");
    message.textContent =
        "Select this node in the graph again to inspect its properties.";

    container.replaceChildren(heading, message);
}


async function loadGraphEvidence() {
    const status = document.getElementById("graph-explorer-status");
    if (status) status.textContent = "Loading graph evidence…";

    try {
        const scenario = encodeURIComponent(getSelectedScenario());
        const response = await fetch(`/api/graph-evidence?scenario_id=${scenario}`);
        const data = await readResponse(response);
        renderGraphEvidence(data);

        if (status) {
            status.textContent = `Showing graph evidence for ${data.scenario_id || getSelectedScenario()}.`;
        }
    } catch (error) {
        if (status) status.textContent = `Could not load graph evidence: ${error.message}`;
    }
}

if (scenarioSelect) {
    scenarioSelect.addEventListener("change", () => {
        const scenario = encodeURIComponent(scenarioSelect.value);
        window.location.href = `/?scenario_id=${scenario}`;
    });
}

if (runButton) {
    runButton.addEventListener("click", runInvestigation);
}

if (updateRouteButton) {
    updateRouteButton.addEventListener("click", updateRouteStatus);
}

if (runAIButton) {
    runAIButton.addEventListener("click", runAIInvestigation);
}

if (routeSelect && updateRouteButton) {
    const routeName = document.getElementById("route-name")?.textContent || "";
    const routeMissing = !routeName || routeName.toLowerCase().includes("no route record");
    routeSelect.disabled = routeMissing;
    updateRouteButton.disabled = routeMissing;
}

loadGraphEvidence();
