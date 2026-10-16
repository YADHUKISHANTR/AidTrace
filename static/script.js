
const runButton = document.getElementById("run-investigation");
const investigationStatus = document.getElementById("investigation-status");
const routeSelect = document.getElementById("route-status-select");
const updateRouteButton = document.getElementById("update-route-button");
const routeUpdateStatus = document.getElementById("route-update-status");
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
}

if (runButton && investigationStatus) {
    runButton.addEventListener("click", async () => {
        runButton.disabled = true;
        investigationStatus.textContent = "Investigating graph evidence...";

        try {
            const response = await fetch("/api/investigate", {
                method: "POST"
            });

            const result = await response.json();

            if (!response.ok) {
                throw new Error(result.error || "Investigation failed.");
            }

            renderInvestigation(result);

            investigationStatus.textContent =
                `Investigation complete. ${result.gap} kits remain unconfirmed. ` +
                `${(result.leads || []).length} lead(s) require review.`;

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

            routeUpdateStatus.textContent =
                `${result.route} status updated to ${result.route_status}.`;

        } catch (error) {
            routeUpdateStatus.textContent = error.message;
        } finally {
            updateRouteButton.disabled = false;
        }
    });
}
