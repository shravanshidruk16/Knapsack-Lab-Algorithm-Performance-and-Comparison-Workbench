/**
 * Knapsack Lab — Solver & Item Table Management
 * Handles custom item inputs, presets, execution invocation, and dual result rendering.
 */

const KnapsackSolver = (function() {
    // Built-in presets for instantaneous offline loading
    const DEFAULT_PRESETS = [
        {
            id: "clrs_classic",
            name: "Classic Textbook Instance (4 items)",
            capacity: 50,
            items: [
                { id: 1, name: "Item 1", weight: 10, value: 60 },
                { id: 2, name: "Item 2", weight: 20, value: 100 },
                { id: 3, name: "Item 3", weight: 30, value: 120 },
                { id: 4, name: "Item 4", weight: 15, value: 70 }
            ]
        },
        {
            id: "bb_dominates",
            name: "High Capacity & Distinct Ratios (B&B Dominates)",
            capacity: 80000,
            items: [
                { id: 1, name: "Gold Alloy", weight: 15000, value: 45000 },
                { id: 2, name: "Platinum Catalyst", weight: 22000, value: 55000 },
                { id: 3, name: "Titanium Ingot", weight: 30000, value: 66000 },
                { id: 4, name: "Silver Bar", weight: 18000, value: 36000 },
                { id: 5, name: "Rare Earth Sample", weight: 25000, value: 42000 },
                { id: 6, name: "Cobalt Canister", weight: 12000, value: 28000 },
                { id: 7, name: "Lithium Cell", weight: 20000, value: 41000 },
                { id: 8, name: "Silicon Wafer", weight: 16000, value: 31000 }
            ]
        },
        {
            id: "dp_dominates",
            name: "Dense Small Capacity (DP Dominates)",
            capacity: 60,
            items: [
                { id: 1, name: "Component A", weight: 12, value: 24 },
                { id: 2, name: "Component B", weight: 14, value: 28 },
                { id: 3, name: "Component C", weight: 16, value: 32 },
                { id: 4, name: "Component D", weight: 18, value: 36 },
                { id: 5, name: "Component E", weight: 20, value: 40 },
                { id: 6, name: "Component F", weight: 22, value: 44 },
                { id: 7, name: "Component G", weight: 24, value: 48 },
                { id: 8, name: "Component H", weight: 26, value: 52 },
                { id: 9, name: "Component I", weight: 10, value: 20 },
                { id: 10, name: "Component J", weight: 15, value: 30 }
            ]
        },
        {
            id: "heavy_exclusion",
            name: "Heavy High-Value Trap",
            capacity: 40,
            items: [
                { id: 1, name: "Oversized Diamond", weight: 45, value: 1000 },
                { id: 2, name: "Ruby Ring", weight: 15, value: 180 },
                { id: 3, name: "Sapphire Pendant", weight: 20, value: 240 },
                { id: 4, name: "Emerald Brooch", weight: 18, value: 210 }
            ]
        }
    ];

    let items = JSON.parse(JSON.stringify(DEFAULT_PRESETS[0].items));
    let nextItemId = 5;

    function init() {
        populatePresetsDropdown(DEFAULT_PRESETS);
        renderItemsTable();
        setupEventListeners();
        // Optional background sync with server
        loadPresetsFromServer();
    }

    function setupEventListeners() {
        const btnAdd = document.getElementById("btn-add-item");
        if (btnAdd) btnAdd.addEventListener("click", handleAddItem);

        const btnClear = document.getElementById("btn-clear-items");
        if (btnClear) btnClear.addEventListener("click", handleClearItems);

        const btnRun = document.getElementById("btn-run-solver");
        if (btnRun) btnRun.addEventListener("click", handleRunSolver);

        const selectPreset = document.getElementById("select-preset");
        if (selectPreset) selectPreset.addEventListener("change", handlePresetChange);

        const btnCopyGen = document.getElementById("btn-copy-generated");
        if (btnCopyGen) btnCopyGen.addEventListener("click", handleCopyGeneratedToSolver);

        // Preset pill buttons
        document.querySelectorAll(".preset-pill-btn").forEach(pill => {
            pill.addEventListener("click", () => {
                const presetId = pill.dataset.presetId;
                const found = DEFAULT_PRESETS.find(p => p.id === presetId);
                if (found) {
                    applyPreset(found);
                    if (selectPreset) selectPreset.value = presetId;
                    document.querySelectorAll(".preset-pill-btn").forEach(p => p.classList.remove("active"));
                    pill.classList.add("active");
                }
            });
        });
    }

    function populatePresetsDropdown(presetsList) {
        const select = document.getElementById("select-preset");
        if (!select) return;

        select.innerHTML = '<option value="">-- Select a Sample Preset --</option>';
        presetsList.forEach(p => {
            const opt = document.createElement("option");
            opt.value = p.id;
            opt.textContent = `${p.name} (Cap: ${p.capacity.toLocaleString()}, ${p.items.length} items)`;
            opt.dataset.json = JSON.stringify(p);
            select.appendChild(opt);
        });
    }

    async function loadPresetsFromServer() {
        try {
            const res = await fetch("/api/samples");
            if (res.ok) {
                const data = await res.json();
                if (data && data.presets && data.presets.length > 0) {
                    populatePresetsDropdown(data.presets);
                }
            }
        } catch (e) {
            console.log("Operating with built-in presets.");
        }
    }

    function applyPreset(preset) {
        const capInput = document.getElementById("solver-capacity");
        if (capInput) capInput.value = preset.capacity;

        items = preset.items.map((itm, idx) => ({
            id: itm.id || idx + 1,
            name: itm.name || `Item ${idx + 1}`,
            weight: itm.weight,
            value: itm.value
        }));
        nextItemId = items.length + 1;
        renderItemsTable();

        // Hide old results on new preset load
        const resultsContainer = document.getElementById("solver-results-container");
        if (resultsContainer) resultsContainer.style.display = "none";
    }

    function handlePresetChange(e) {
        const selected = e.target.selectedOptions[0];
        if (!selected || !selected.dataset.json) return;
        const preset = JSON.parse(selected.dataset.json);
        applyPreset(preset);

        // Sync pill buttons
        document.querySelectorAll(".preset-pill-btn").forEach(p => {
            if (p.dataset.presetId === preset.id) p.classList.add("active");
            else p.classList.remove("active");
        });
    }

    function renderItemsTable() {
        const tbody = document.getElementById("items-table-body");
        const countSpan = document.getElementById("items-count-badge");
        if (!tbody) return;

        tbody.innerHTML = "";
        if (countSpan) countSpan.textContent = `${items.length} items`;

        if (items.length === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="6" class="empty-state" style="padding: 24px;">
                        No items added. Click "+ Add Item" or select a preset above.
                    </td>
                </tr>
            `;
            return;
        }

        items.forEach((item, index) => {
            const tr = document.createElement("tr");
            const ratio = item.weight > 0 ? (item.value / item.weight).toFixed(2) : "0.00";
            tr.innerHTML = `
                <td><strong>${index + 1}</strong></td>
                <td><input type="text" class="form-control form-control-sm item-name-input" data-index="${index}" value="${escapeHtml(item.name)}"></td>
                <td class="num"><input type="number" min="1" class="form-control form-control-sm item-weight-input num" data-index="${index}" value="${item.weight}"></td>
                <td class="num"><input type="number" min="1" class="form-control form-control-sm item-value-input num" data-index="${index}" value="${item.value}"></td>
                <td class="num" style="color: var(--secondary-text); font-style: italic; font-weight: 600;">${ratio}</td>
                <td style="text-align: center;">
                    <button class="btn btn-outline btn-sm btn-remove-item" data-index="${index}" title="Remove Item" style="padding: 2px 8px; color: var(--danger-color); border-color: var(--danger-border);">
                        &times;
                    </button>
                </td>
            `;
            tbody.appendChild(tr);
        });

        tbody.querySelectorAll(".item-name-input").forEach(input => {
            input.addEventListener("input", e => {
                const idx = parseInt(e.target.dataset.index, 10);
                items[idx].name = e.target.value.trim() || `Item ${idx + 1}`;
            });
        });

        tbody.querySelectorAll(".item-weight-input").forEach(input => {
            input.addEventListener("input", e => {
                const idx = parseInt(e.target.dataset.index, 10);
                const val = parseInt(e.target.value, 10);
                items[idx].weight = isNaN(val) ? 1 : Math.max(1, val);
                updateRatioCell(idx);
            });
        });

        tbody.querySelectorAll(".item-value-input").forEach(input => {
            input.addEventListener("input", e => {
                const idx = parseInt(e.target.dataset.index, 10);
                const val = parseInt(e.target.value, 10);
                items[idx].value = isNaN(val) ? 1 : Math.max(1, val);
                updateRatioCell(idx);
            });
        });

        tbody.querySelectorAll(".btn-remove-item").forEach(btn => {
            btn.addEventListener("click", e => {
                const idx = parseInt(e.target.dataset.index, 10);
                items.splice(idx, 1);
                renderItemsTable();
            });
        });
    }

    function updateRatioCell(index) {
        const tbody = document.getElementById("items-table-body");
        if (!tbody) return;
        const row = tbody.children[index];
        if (row && items[index]) {
            const ratioCell = row.children[4];
            const ratio = items[index].weight > 0 ? (items[index].value / items[index].weight).toFixed(2) : "0.00";
            if (ratioCell) ratioCell.textContent = ratio;
        }
    }

    function handleAddItem() {
        items.push({
            id: nextItemId++,
            name: `Item ${items.length + 1}`,
            weight: 15,
            value: 60
        });
        renderItemsTable();
    }

    function handleClearItems() {
        if (confirm("Are you sure you want to remove all items?")) {
            items = [];
            renderItemsTable();
        }
    }

    function handleCopyGeneratedToSolver() {
        if (!window.__lastGeneratedDataset) {
            alert("No random dataset generated yet. Please click 'Generate Dataset' first.");
            return;
        }
        const ds = window.__lastGeneratedDataset;
        const capInput = document.getElementById("solver-capacity");
        if (capInput) capInput.value = ds.capacity;

        items = ds.items.map((itm, idx) => ({
            id: itm.id || idx + 1,
            name: itm.name || `Item ${idx + 1}`,
            weight: itm.weight,
            value: itm.value
        }));
        nextItemId = items.length + 1;
        renderItemsTable();

        // Switch to Solve tab
        const navSolve = document.querySelector('[data-view="view-solver"]');
        if (navSolve) navSolve.click();
    }

    async function handleRunSolver() {
        const alertBox = document.getElementById("solver-alert-box");
        alertBox.style.display = "none";
        alertBox.textContent = "";

        const capInput = document.getElementById("solver-capacity");
        const capacity = parseInt(capInput.value, 10);

        if (isNaN(capacity) || capacity <= 0) {
            showError("Capacity must be a positive integer greater than zero.");
            capInput.focus();
            return;
        }

        if (items.length === 0) {
            showError("Please add at least one item to solve.");
            return;
        }

        for (let i = 0; i < items.length; i++) {
            if (items[i].weight <= 0 || items[i].value <= 0) {
                showError(`Item row ${i + 1} ('${items[i].name}') must have positive weight and value.`);
                return;
            }
        }

        const trialsInput = document.getElementById("solver-trials");
        const trials = trialsInput ? parseInt(trialsInput.value, 10) || 1 : 1;

        const btnRun = document.getElementById("btn-run-solver");
        const originalText = btnRun.innerHTML;
        btnRun.disabled = true;
        btnRun.innerHTML = `<span class="spinner"></span> Running C++ Engine...`;

        try {
            const payload = {
                capacity: capacity,
                trials: trials,
                items: items
            };

            const response = await fetch("/api/solve", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload)
            });

            const data = await response.json();

            if (!response.ok || !data.success) {
                showError(data.error || "Solver execution failed.");
                return;
            }

            renderResults(data);
        } catch (err) {
            showError("Network or server connection error: " + err.message);
        } finally {
            btnRun.disabled = false;
            btnRun.innerHTML = originalText;
        }
    }

    function showError(msg) {
        const alertBox = document.getElementById("solver-alert-box");
        if (alertBox) {
            alertBox.className = "alert alert-danger";
            alertBox.style.display = "block";
            alertBox.textContent = msg;
        }
    }

    function renderResults(data) {
        const resultsContainer = document.getElementById("solver-results-container");
        if (!resultsContainer) return;
        resultsContainer.style.display = "block";

        const dp = data.dp;
        const bb = data.branch_and_bound;
        const ver = data.verification;
        const comp = data.comparison;

        // Agreement Banner
        const banner = document.getElementById("results-agreement-banner");
        if (banner) {
            if (ver.verified) {
                banner.className = "comparison-banner success";
                banner.innerHTML = `
                    <div>
                        <div class="comparison-title" style="color: var(--success-color);">
                            <svg class="nav-icon" viewBox="0 0 20 20" style="fill: var(--success-color);"><path d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"/></svg>
                            Optimal Values Match Exactly (V* = ${dp.optimal_value.toLocaleString()})
                        </div>
                        <div class="comparison-desc">${ver.agreement_message} Both algorithm item selections verified feasible.</div>
                    </div>
                    <span class="badge badge-success">Verified Exact</span>
                `;
            } else {
                banner.className = "comparison-banner mismatch";
                banner.innerHTML = `
                    <div>
                        <div class="comparison-title" style="color: var(--danger-color);">
                            <svg class="nav-icon" viewBox="0 0 20 20" style="fill: var(--danger-color);"><path d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"/></svg>
                            Verification Alert: Discrepancy Detected
                        </div>
                        <div class="comparison-desc">${ver.validation_errors.join("<br>")}</div>
                    </div>
                    <span class="badge badge-danger">Mismatch</span>
                `;
            }
        }

        // DP Card
        document.getElementById("dp-opt-val").textContent = dp.optimal_value.toLocaleString();
        document.getElementById("dp-tot-weight").textContent = `${dp.total_weight.toLocaleString()} / ${data.capacity.toLocaleString()}`;
        document.getElementById("dp-exec-time").textContent = `${dp.execution_time_ms.toFixed(4)} ms (${dp.execution_time_us.toFixed(1)} µs)`;
        document.getElementById("dp-peak-mem").textContent = `${(dp.peak_working_set_bytes / 1024).toFixed(1)} KB`;
        document.getElementById("dp-workspace-mem").textContent = `${(dp.algorithm_workspace_bytes / 1024).toFixed(2)} KB`;
        document.getElementById("dp-table-cells").textContent = `${dp.dp_table_entries.toLocaleString()} cells (${dp.dp_rows} × ${dp.dp_cols})`;

        renderSelectedItemsTags("dp-selected-items", dp.selected_indices);

        // Branch and Bound Card
        document.getElementById("bb-opt-val").textContent = bb.optimal_value.toLocaleString();
        document.getElementById("bb-tot-weight").textContent = `${bb.total_weight.toLocaleString()} / ${data.capacity.toLocaleString()}`;
        document.getElementById("bb-exec-time").textContent = `${bb.execution_time_ms.toFixed(4)} ms (${bb.execution_time_us.toFixed(1)} µs)`;
        document.getElementById("bb-peak-mem").textContent = `${(bb.peak_working_set_bytes / 1024).toFixed(1)} KB`;
        document.getElementById("bb-workspace-mem").textContent = `${(bb.algorithm_workspace_bytes / 1024).toFixed(2)} KB`;
        document.getElementById("bb-nodes-expanded").textContent = bb.nodes_expanded.toLocaleString();
        document.getElementById("bb-nodes-pruned").textContent = bb.nodes_pruned.toLocaleString();
        document.getElementById("bb-nodes-generated").textContent = bb.nodes_generated.toLocaleString();
        document.getElementById("bb-max-frontier").textContent = bb.max_frontier_size.toLocaleString();

        renderSelectedItemsTags("bb-selected-items", bb.selected_indices);

        // Summary Statistics Card
        document.getElementById("comp-faster-algo").textContent = comp.faster_algorithm;
        document.getElementById("comp-speedup-summary").textContent = comp.speedup_summary;
        document.getElementById("comp-time-diff").textContent = `${comp.runtime_difference_ms.toFixed(4)} ms`;
        document.getElementById("comp-speedup-ratio").textContent = `${comp.speedup}x`;

        // Theoretical context note
        const rationaleEl = document.getElementById("comp-rationale");
        if (rationaleEl) {
            if (comp.faster_algorithm === "Branch and Bound") {
                rationaleEl.innerHTML = `
                    <strong>Why B&B won on this instance:</strong> Knapsack capacity (W=${data.capacity.toLocaleString()}) is relatively large,
                    forcing DP to compute a massive ${dp.dp_table_entries.toLocaleString()}-cell recurrence table (\u004F(nW)).
                    In contrast, Branch and Bound's continuous fractional upper bound pruned large portions of the state space,
                    expanding only ${bb.nodes_expanded} nodes.
                `;
            } else if (comp.faster_algorithm === "Dynamic Programming") {
                rationaleEl.innerHTML = `
                    <strong>Why DP won on this instance:</strong> The knapsack capacity (W=${data.capacity.toLocaleString()}) is compact,
                    allowing the pseudo-polynomial DP table (${dp.dp_table_entries.toLocaleString()} cells) to be filled
                    rapidly with high CPU cache locality and zero heap-allocation overhead.
                `;
            } else {
                rationaleEl.innerHTML = `
                    <strong>Observation:</strong> Both algorithms completed in under a few hundred microseconds on this instance size.
                `;
            }
        }
    }

    function renderSelectedItemsTags(containerId, indices) {
        const container = document.getElementById(containerId);
        if (!container) return;
        container.innerHTML = "";
        if (!indices || indices.length === 0) {
            container.innerHTML = `<span style="color: var(--secondary-text); font-style: italic;">No items selected (Value = 0)</span>`;
            return;
        }

        indices.forEach(idx => {
            const itm = items[idx];
            if (itm) {
                const tag = document.createElement("span");
                tag.className = "item-tag";
                tag.innerHTML = `<strong>#${idx + 1} ${escapeHtml(itm.name)}</strong> (w:${itm.weight}, v:${itm.value})`;
                container.appendChild(tag);
            }
        });
    }

    function escapeHtml(str) {
        return (str || "")
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }

    return {
        init,
        getItems: () => items
    };
})();
