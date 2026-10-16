
const runButton = document.getElementById("run-investigation");
const investigationStatus = document.getElementById("investigation-status");
const routeSelect = document.getElementById("route-status-select");
const updateRouteButton = document.getElementById("update-route-button");
const routeUpdateStatus = document.getElementById("route-update-status");

const runAIButton = document.getElementById("run-ai-investigation");
const aiInvestigationStatus = document.getElementById("ai-investigation-status");
const aiAnalysisContainer = document.getElementById("ai-analysis");

let aiAnalysisNeedsRefresh = false;

function updateText(id, value) {
    const element = document.getElementById(id);

    if (element) {
        element.textContent =
            value === null || value === undefined || value === ""
                ? "Unknown"
                : value;
    }
}

function renderActions(actions) {
    const list = document.getElementById("recommended-actions");

    if (!list) return;

    list.replaceChildren();

    actions.forEach((action, index) => {
        const item = document.createElement("li");

        const number = document.createElement("span");
        number.className = "action-number";
        number.textContent = index + 1;

        const text = document.createElement("p");
        text.textContent = action;

        item.append(number, text);
        list.appendChild(item);
    });
}

// --------------------------------------------------
// NEW: Cross-centre findings and action rendering
// --------------------------------------------------

function appendFindingDetail(container, label, value) {
    if (value === null || value === undefined || value === "") {
        return;
    }

    const paragraph = document.createElement("p");
    const strong = document.createElement("strong");

    strong.textContent = `${label}: `;
    paragraph.appendChild(strong);
    paragraph.appendChild(document.createTextNode(String(value)));

    container.appendChild(paragraph);
}

function renderCrossCentreFindings(findings, actions) {
    const findingsContainer =
        document.getElementById("cross-centre-findings");

    const actionsContainer =
        document.getElementById("cross-centre-actions");

    const section = document.getElementById("cross-centre-section");

    if (!section) return;

    const sectionCount = section.querySelector(".section-count");

    if (sectionCount) {
        sectionCount.textContent =
            `${Array.isArray(findings) ? findings.length : 0} findings`;
    }

    if (findingsContainer) {
        findingsContainer.replaceChildren();

        if (!Array.isArray(findings) || findings.length === 0) {
            const empty = document.createElement("p");
            empty.className = "investigation-status";
            empty.textContent =
                "No cross-centre discrepancy findings were returned by the current graph query.";

            findingsContainer.appendChild(empty);
        } else {
            findings.forEach((finding, index) => {
                const article = document.createElement("article");
                article.className = "evidence-row cross-centre-finding";

                const number = document.createElement("div");
                number.className = "evidence-index";
                number.textContent = String(index + 1).padStart(2, "0");

                const content = document.createElement("div");
                content.className = "evidence-content";

                const heading = document.createElement("h3");
                heading.textContent = finding.title || "Discrepancy finding";
                content.appendChild(heading);

                if (finding.centre) {
                    appendFindingDetail(content, "Centre", finding.centre);
                }

                if (Array.isArray(finding.centres)) {
                    appendFindingDetail(
                        content,
                        "Centres compared",
                        finding.centres.join(" ↔ ")
                    );
                }

                appendFindingDetail(content, "Item", finding.item);
                appendFindingDetail(
                    content,
                    "Request reference",
                    finding.request_id
                );

                if (finding.requested_quantity !== undefined) {
                    appendFindingDetail(
                        content,
                        "Requested",
                        finding.requested_quantity
                    );
                }

                if (
                    finding.reported_quantity !== undefined &&
                    finding.reported_quantity !== null
                ) {
                    appendFindingDetail(
                        content,
                        "Reported delivered",
                        finding.reported_quantity
                    );
                }

                if (
                    finding.confirmed_quantity !== undefined &&
                    finding.confirmed_quantity !== null
                ) {
                    appendFindingDetail(
                        content,
                        "Receipt-confirmed",
                        finding.confirmed_quantity
                    );
                }

                appendFindingDetail(content, "Finding", finding.finding);
                appendFindingDetail(
                    content,
                    "Verification step",
                    finding.next_step
                );

                const status = document.createElement("span");
                status.className = "tag";
                status.textContent = finding.status || "Unverified";

                article.append(number, content, status);
                findingsContainer.appendChild(article);
            });
        }
    }

    if (actionsContainer) {
        actionsContainer.replaceChildren();

        if (!Array.isArray(actions) || actions.length === 0) {
            const empty = document.createElement("li");
            empty.textContent = "No additional cross-centre actions.";
            actionsContainer.appendChild(empty);
        } else {
            actions.forEach((action, index) => {
                const item = document.createElement("li");

                const number = document.createElement("span");
                number.className = "action-number";
                number.textContent = index + 1;

                const text = document.createElement("p");
                text.textContent = action;

                item.append(number, text);
                actionsContainer.appendChild(item);
            });
        }
    }
}

function renderInvestigation(result) {
    updateText("requested-quantity", result.requested);
    updateText("reported-quantity", result.reported);
    updateText("confirmed-quantity", result.confirmed);
    updateText("unconfirmed-quantity", result.gap);

    updateText(
        "delivery-description",
        `${result.reported} kits reported as delivered.`
    );
    updateText("delivery-value", `${result.reported} kits`);

    updateText(
        "receipt-description",
        "Quantity confirmed by the available receipt."
    );
    updateText("receipt-value", `${result.confirmed} kits`);

    updateText("route-name", result.route || "No connected route found");
    updateText("route-status", result.route_status || "Unknown");

    updateText(
        "incident-description",
        result.incident || "No connected incident report found."
    );

    updateText(
        "warehouse-name",
        result.warehouse || "No connected warehouse found"
    );

    updateText(
        "warehouse-stock",
        result.stock === null || result.stock === undefined
            ? "Unknown"
            : `${result.stock} kits`
    );

    if (routeSelect && result.route_status) {
        routeSelect.value = result.route_status;
    }

    renderActions(result.recommended_actions || []);

    // Refresh cross-centre findings from the same live API response.
    renderCrossCentreFindings(
        result.cross_centre_findings || [],
        result.cross_centre_actions || []
    );
}

function renderAIList(id, items) {
    const list = document.getElementById(id);

    if (!list) return;

    list.replaceChildren();

    if (!Array.isArray(items) || items.length === 0) {
        const item = document.createElement("li");
        item.textContent = "No items provided.";
        list.appendChild(item);
        return;
    }

    items.forEach((value) => {
        const item = document.createElement("li");
        item.textContent = String(value);
        list.appendChild(item);
    });
}

function renderAIAnalysis(analysis) {
    updateText("ai-summary", analysis.summary);
    updateText("ai-evidence-assessment", analysis.evidence_assessment);
    updateText("ai-confidence", analysis.confidence);

    renderAIList(
        "ai-possible-explanations",
        analysis.possible_explanations
    );

    renderAIList(
        "ai-recommended-actions",
        analysis.recommended_actions
    );

    renderAIList("ai-limitations", analysis.limitations);

    if (aiAnalysisContainer) {
        aiAnalysisContainer.hidden = false;
    }

    aiAnalysisNeedsRefresh = false;
}

async function runAIInvestigation() {
    if (!runAIButton || !aiInvestigationStatus) return;

    runAIButton.disabled = true;
    aiInvestigationStatus.textContent =
        "Analyzing current graph evidence with Gemini. This may take a little while...";

    try {
        const response = await fetch("/api/ai-investigate", {
            method: "POST"
        });

        const result = await response.json();

        if (!response.ok) {
            throw new Error(result.error || "AI investigation failed.");
        }

        if (!result.ai_analysis) {
            throw new Error("The server returned no AI analysis.");
        }

        renderAIAnalysis(result.ai_analysis);

        aiInvestigationStatus.textContent =
            "AI analysis complete. Review the findings and verify all hypotheses against the evidence.";

    } catch (error) {
        aiInvestigationStatus.textContent =
            `${error.message} You can try again.`;
    } finally {
        runAIButton.disabled = false;
    }
}

if (runAIButton) {
    runAIButton.addEventListener("click", runAIInvestigation);
}

if (runButton && investigationStatus) {
    runButton.addEventListener("click", async () => {
        runButton.disabled = true;
        investigationStatus.textContent =
            "Investigating graph evidence and checking all relief centres...";

        try {
            const response = await fetch("/api/investigate", {
                method: "POST"
            });

            const result = await response.json();

            if (!response.ok) {
                throw new Error(result.error || "Investigation failed.");
            }

            renderInvestigation(result);

            // Existing AI output may no longer match the current graph.
            aiAnalysisNeedsRefresh = true;

            if (aiAnalysisContainer) {
                aiAnalysisContainer.hidden = true;
            }

            if (aiInvestigationStatus) {
                aiInvestigationStatus.textContent =
                    "Graph evidence refreshed. Run AI investigation to generate an updated analysis.";
            }

            investigationStatus.textContent =
                `Investigation complete. ${result.gap} kits remain unconfirmed. ` +
                `${(result.leads || []).length} original lead(s) require review. ` +
                `${(result.cross_centre_findings || []).length} cross-centre finding(s) checked.`;

        } catch (error) {
            investigationStatus.textContent = error.message;
        } finally {
            runButton.disabled = false;
        }
    });
}

if (routeSelect && updateRouteButton && routeUpdateStatus) {
    updateRouteButton.addEventListener("click", async () => {
        updateRouteButton.disabled = true;
        routeUpdateStatus.textContent = "Updating route status...";

        try {
            const response = await fetch("/api/update-route", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    status: routeSelect.value
                })
            });

            const result = await response.json();

            if (!response.ok) {
                throw new Error(result.error || "Route update failed.");
            }

            updateText("route-name", result.route);
            updateText("route-status", result.route_status);

            routeSelect.value = result.route_status;

            aiAnalysisNeedsRefresh = true;

            if (aiAnalysisContainer) {
                aiAnalysisContainer.hidden = true;
            }

            if (aiInvestigationStatus) {
                aiInvestigationStatus.textContent =
                    "Route status changed. Run the AI investigation again to refresh its analysis.";
            }

            routeUpdateStatus.textContent =
                `${result.route} status updated to ${result.route_status}.`;

        } catch (error) {
            routeUpdateStatus.textContent = error.message;
        } finally {
            updateRouteButton.disabled = false;
        }
    });
}

// --------------------------------------------------
// EXISTING: Interactive FalkorDB graph explorer
// --------------------------------------------------

async function loadGraphEvidence() {
    const status = document.getElementById("graph-explorer-status");
    const visualization = document.getElementById("graph-visualization");
    const details = document.getElementById("graph-node-details");
    const nodeCount = document.getElementById("graph-node-count");
    const relationshipCount = document.getElementById(
        "graph-relationship-count"
    );

    if (!status || !visualization || !details) {
        return;
    }

    status.textContent = "Loading graph evidence…";

    try {
        const response = await fetch("/api/graph-evidence");
        const data = await response.json();

        if (!response.ok || data.error) {
            throw new Error(data.error || "Could not load graph evidence.");
        }

        nodeCount.textContent = data.node_count;
        relationshipCount.textContent = data.relationship_count;

        visualization.replaceChildren();

        const svgNS = "http://www.w3.org/2000/svg";
        const width = 900;
        const height = 560;

        const svg = document.createElementNS(svgNS, "svg");
        svg.setAttribute("viewBox", `0 0 ${width} ${height}`);
        svg.setAttribute("role", "img");
        svg.setAttribute(
            "aria-label",
            "Connected relief investigation evidence graph"
        );

        const positions = {
            Community: [110, 130],
            ReliefRequest: [310, 130],
            Delivery: [510, 130],
            Receipt: [740, 130],
            Route: [510, 330],
            IncidentReport: [740, 430],
            Warehouse: [110, 390],
            Supply: [310, 390]
        };

        const colors = {
            Community: "#2563eb",
            ReliefRequest: "#7c3aed",
            Delivery: "#0f766e",
            Receipt: "#15803d",
            Route: "#b45309",
            IncidentReport: "#b91c1c",
            Warehouse: "#475569",
            Supply: "#64748b"
        };

        const nodeById = new Map(
            data.nodes.map(node => [node.id, node])
        );

        const nodeElements = new Map();

        function getLabel(node) {
            const label = node.labels?.[0] || "Node";
            const properties = node.properties || {};

            if (label === "Community") {
                return properties.name || label;
            }

            if (
                label === "ReliefRequest" ||
                label === "Delivery" ||
                label === "Receipt"
            ) {
                return properties.id || label;
            }

            if (label === "Warehouse") {
                return properties.name || "Warehouse";
            }

            if (label === "Supply") {
                return properties.item || label;
            }

            if (label === "Route") {
                return properties.name || "Route";
            }

            if (label === "IncidentReport") {
                return "Simulated incident";
            }

            return label;
        }

        // Draw relationship lines before nodes.
        data.relationships.forEach(relationship => {
            const source = nodeById.get(relationship.source);
            const target = nodeById.get(relationship.target);

            if (!source || !target) {
                return;
            }

            const sourcePosition = positions[source.labels?.[0]];
            const targetPosition = positions[target.labels?.[0]];

            if (!sourcePosition || !targetPosition) {
                return;
            }

            const [x1, y1] = sourcePosition;
            const [x2, y2] = targetPosition;

            const line = document.createElementNS(svgNS, "line");
            line.setAttribute("x1", x1);
            line.setAttribute("y1", y1);
            line.setAttribute("x2", x2);
            line.setAttribute("y2", y2);
            line.setAttribute("stroke", "#94a3b8");
            line.setAttribute("stroke-width", "2");
            line.setAttribute("marker-end", "url(#graph-arrow)");
            svg.appendChild(line);

            const text = document.createElementNS(svgNS, "text");
            text.setAttribute("x", (x1 + x2) / 2);
            text.setAttribute("y", (y1 + y2) / 2 - 9);
            text.setAttribute("text-anchor", "middle");
            text.setAttribute("class", "graph-edge-label");
            text.textContent = relationship.type;
            svg.appendChild(text);
        });

        const defs = document.createElementNS(svgNS, "defs");
        const marker = document.createElementNS(svgNS, "marker");
        marker.setAttribute("id", "graph-arrow");
        marker.setAttribute("markerWidth", "8");
        marker.setAttribute("markerHeight", "8");
        marker.setAttribute("refX", "6");
        marker.setAttribute("refY", "3");
        marker.setAttribute("orient", "auto");

        const arrow = document.createElementNS(svgNS, "path");
        arrow.setAttribute("d", "M0,0 L0,6 L6,3 z");
        arrow.setAttribute("fill", "#94a3b8");

        marker.appendChild(arrow);
        defs.appendChild(marker);
        svg.prepend(defs);

        data.nodes.forEach(node => {
            const label = node.labels?.[0] || "Node";
            const position = positions[label];

            if (!position) {
                return;
            }

            const [x, y] = position;
            const group = document.createElementNS(svgNS, "g");

            group.setAttribute("class", "graph-node");
            group.setAttribute("tabindex", "0");
            group.setAttribute("role", "button");
            group.setAttribute(
                "aria-label",
                `Inspect ${label}: ${getLabel(node)}`
            );

            const rect = document.createElementNS(svgNS, "rect");
            rect.setAttribute("x", x - 72);
            rect.setAttribute("y", y - 27);
            rect.setAttribute("width", "144");
            rect.setAttribute("height", "54");
            rect.setAttribute("rx", "10");
            rect.setAttribute("fill", colors[label] || "#475569");

            const title = document.createElementNS(svgNS, "text");
            title.setAttribute("x", x);
            title.setAttribute("y", y + 5);
            title.setAttribute("text-anchor", "middle");
            title.setAttribute("class", "graph-node-label");
            title.textContent = getLabel(node);

            group.append(rect, title);

            function showDetails() {
                details.replaceChildren();

                const heading = document.createElement("h3");
                heading.textContent = label;

                const name = document.createElement("p");
                name.textContent = getLabel(node);

                details.append(heading, name);

                if (label === "IncidentReport") {
                    const warning = document.createElement("p");
                    warning.className = "graph-simulated-warning";
                    warning.textContent =
                        "SIMULATED DEMO DATA — not evidence of a real incident.";
                    details.appendChild(warning);
                }

                const propertiesHeading = document.createElement("h4");
                propertiesHeading.textContent = "Recorded properties";
                details.appendChild(propertiesHeading);

                const list = document.createElement("dl");

                Object.entries(node.properties || {}).forEach(
                    ([key, value]) => {
                        const term = document.createElement("dt");
                        term.textContent = key;

                        const description = document.createElement("dd");
                        description.textContent = String(value);

                        list.append(term, description);
                    }
                );

                details.appendChild(list);

                const connectedHeading = document.createElement("h4");
                connectedHeading.textContent = "Connected relationships";
                details.appendChild(connectedHeading);

                const connected = data.relationships.filter(
                    relationship =>
                        relationship.source === node.id ||
                        relationship.target === node.id
                );

                if (connected.length === 0) {
                    const empty = document.createElement("p");
                    empty.textContent = "No connected relationships.";
                    details.appendChild(empty);
                } else {
                    const relationshipList = document.createElement("ul");

                    connected.forEach(relationship => {
                        const otherId =
                            relationship.source === node.id
                                ? relationship.target
                                : relationship.source;

                        const otherNode = nodeById.get(otherId);
                        const item = document.createElement("li");

                        const direction =
                            relationship.source === node.id ? "→" : "←";

                        item.textContent =
                            `${relationship.type} ${direction} ` +
                            `${otherNode ? getLabel(otherNode) : otherId}`;

                        relationshipList.appendChild(item);
                    });

                    details.appendChild(relationshipList);
                }
            }

            group.addEventListener("click", showDetails);

            group.addEventListener("keydown", event => {
                if (event.key === "Enter" || event.key === " ") {
                    event.preventDefault();
                    showDetails();
                }
            });

            svg.appendChild(group);
            nodeElements.set(node.id, group);
        });

        visualization.appendChild(svg);
        status.textContent = "Graph evidence loaded successfully.";

        if (data.nodes.length > 0) {
            const firstNode = data.nodes[0];
            const firstElement = nodeElements.get(firstNode.id);

            if (firstElement) {
                firstElement.dispatchEvent(new Event("click"));
            }
        }
    } catch (error) {
        console.error("Graph evidence loading failed:", error);
        status.textContent =
            "Could not load graph evidence. Check the Flask terminal.";
    }
}

document.addEventListener("DOMContentLoaded", loadGraphEvidence);
