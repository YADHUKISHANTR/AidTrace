
const button = document.getElementById("run-investigation");
const statusMessage = document.getElementById("investigation-status");

function updateText(id, value, fallback = "Not recorded") {
    const element = document.getElementById(id);

    if (element) {
        element.textContent = value ?? fallback;
    }
}

if (button && statusMessage) {
    button.addEventListener("click", async () => {
        button.disabled = true;
        statusMessage.textContent = "Investigating graph evidence...";

        try {
            const response = await fetch("/api/investigate", {
                method: "POST"
            });

            const result = await response.json();

            if (!response.ok) {
                throw new Error(
                    result.error || "Investigation failed."
                );
            }

            // Update the quantities.
            updateText("requested-quantity", result.requested);
            updateText("reported-quantity", result.reported);
            updateText("confirmed-quantity", result.confirmed);
            updateText("unconfirmed-quantity", result.gap);

            // Update the connected evidence.
            updateText("route-name", result.route);
            updateText("route-status", result.route_status);
            updateText("incident-description", result.incident);
            updateText("warehouse-name", result.warehouse);
            updateText("warehouse-stock", result.stock);

            // Replace the recommendations with the latest results.
            const actions = document.getElementById("recommended-actions");

            if (actions) {
                actions.replaceChildren();

                for (const action of result.recommended_actions || []) {
                    const item = document.createElement("li");
                    item.textContent = action;
                    actions.appendChild(item);
                }
            }

            statusMessage.textContent =
                `Investigation complete. ${result.gap} kits remain unconfirmed. ` +
                `${(result.leads || []).length} lead(s) require review.`;

        } catch (error) {
            console.error("AidTrace investigation failed:", error);
            statusMessage.textContent = error.message;
        } finally {
            button.disabled = false;
        }
    });
}

const routeSelect = document.getElementById("route-status-select");
const updateRouteButton = document.getElementById("update-route-button");
const routeUpdateStatus = document.getElementById("route-update-status");

if (routeSelect && updateRouteButton && routeUpdateStatus) {
    updateRouteButton.addEventListener("click", async () => {
        const selectedStatus = routeSelect.value;

        updateRouteButton.disabled = true;
        routeUpdateStatus.textContent = "Updating route status...";

        try {
            const response = await fetch("/api/update-route", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    status: selectedStatus
                })
            });

            const result = await response.json();

            if (!response.ok) {
                throw new Error(result.error || "Route update failed.");
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
