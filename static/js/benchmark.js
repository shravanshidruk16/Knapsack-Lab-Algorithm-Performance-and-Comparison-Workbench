/**
 * Knapsack Lab — Benchmark Suite & Generator Module
 * Handles reproducible dataset generation, empirical benchmark parameter sweeps,
 * canvas chart triggering, and export functionality.
 */

const KnapsackBenchmark = (function() {
    let lastBenchmarkData = null;
    let useLogScale = false;
    let memoryMetric = 'workspace';

    function init() {
        setupEventListeners();
    }

    function setupEventListeners() {
        const btnRunBenchmark = document.getElementById("btn-run-benchmark");
        if (btnRunBenchmark) btnRunBenchmark.addEventListener("click", handleRunBenchmark);

        const btnGenerate = document.getElementById("btn-generate-dataset");
        if (btnGenerate) btnGenerate.addEventListener("click", handleGenerateDataset);

        const toggleLogScale = document.getElementById("toggle-log-scale");
        if (toggleLogScale) {
            toggleLogScale.addEventListener("change", e => {
                useLogScale = e.target.checked;
                if (lastBenchmarkData && lastBenchmarkData.points) {
                    KnapsackCharts.renderRuntimeChart("canvas-runtime", lastBenchmarkData.points, useLogScale);
                }
            });
        }

        const selectMemMetric = document.getElementById("select-mem-metric");
        if (selectMemMetric) {
            selectMemMetric.addEventListener("change", e => {
                memoryMetric = e.target.value;
                if (lastBenchmarkData && lastBenchmarkData.points) {
                    KnapsackCharts.renderMemoryChart("canvas-memory", lastBenchmarkData.points, memoryMetric);
                }
            });
        }

        const btnExportCsv = document.getElementById("btn-export-csv");
        if (btnExportCsv) btnExportCsv.addEventListener("click", handleExportCsv);

        const btnExportJson = document.getElementById("btn-export-json");
        if (btnExportJson) btnExportJson.addEventListener("click", handleExportJson);
    }

    async function handleGenerateDataset() {
        const alertBox = document.getElementById("generator-alert-box");
        alertBox.style.display = "none";

        const count = parseInt(document.getElementById("gen-count").value, 10);
        const capacity = parseInt(document.getElementById("gen-capacity").value, 10);
        const minW = parseInt(document.getElementById("gen-min-w").value, 10);
        const maxW = parseInt(document.getElementById("gen-max-w").value, 10);
        const minV = parseInt(document.getElementById("gen-min-v").value, 10);
        const maxV = parseInt(document.getElementById("gen-max-v").value, 10);
        const seed = parseInt(document.getElementById("gen-seed").value, 10);

        if (isNaN(count) || count < 1) {
            showGenError("Item count must be a positive integer.");
            return;
        }
        if (isNaN(capacity) || capacity < 1) {
            showGenError("Capacity must be a positive integer.");
            return;
        }

        const btn = document.getElementById("btn-generate-dataset");
        btn.disabled = true;

        try {
            const res = await fetch("/api/generate", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    item_count: count,
                    capacity: capacity,
                    min_weight: minW,
                    max_weight: maxW,
                    min_value: minV,
                    max_value: maxV,
                    seed: seed
                })
            });

            const data = await res.json();
            if (!res.ok || !data.success) {
                showGenError(data.error || "Dataset generation failed.");
                return;
            }

            window.__lastGeneratedDataset = data.dataset;
            renderGeneratedPreview(data.dataset);
        } catch (e) {
            showGenError("Generation error: " + e.message);
        } finally {
            btn.disabled = false;
        }
    }

    function showGenError(msg) {
        const alertBox = document.getElementById("generator-alert-box");
        if (alertBox) {
            alertBox.className = "alert alert-danger";
            alertBox.style.display = "block";
            alertBox.textContent = msg;
        }
    }

    function renderGeneratedPreview(dataset) {
        const previewCard = document.getElementById("generator-preview-card");
        const tbody = document.getElementById("generator-preview-body");
        const meta = document.getElementById("generator-preview-meta");
        if (!previewCard || !tbody) return;

        previewCard.style.display = "block";
        meta.textContent = `Generated ${dataset.items.length} items (Capacity: ${dataset.capacity.toLocaleString()}, Seed: ${dataset.seed})`;

        tbody.innerHTML = "";
        dataset.items.forEach((itm, idx) => {
            const ratio = (itm.value / itm.weight).toFixed(2);
            const tr = document.createElement("tr");
            tr.innerHTML = `
                <td><strong>#${idx + 1}</strong></td>
                <td>${itm.name}</td>
                <td class="num">${itm.weight.toLocaleString()}</td>
                <td class="num">${itm.value.toLocaleString()}</td>
                <td class="num" style="color: var(--secondary-text);">${ratio}</td>
            `;
            tbody.appendChild(tr);
        });
    }

    async function handleRunBenchmark() {
        const alertBox = document.getElementById("benchmark-alert-box");
        alertBox.style.display = "none";

        const minItems = parseInt(document.getElementById("bench-min-items").value, 10);
        const maxItems = parseInt(document.getElementById("bench-max-items").value, 10);
        const stepItems = parseInt(document.getElementById("bench-step-items").value, 10);
        const capacity = parseInt(document.getElementById("bench-capacity").value, 10);
        const minW = parseInt(document.getElementById("bench-min-w").value, 10);
        const maxW = parseInt(document.getElementById("bench-max-w").value, 10);
        const minV = parseInt(document.getElementById("bench-min-v").value, 10);
        const maxV = parseInt(document.getElementById("bench-max-v").value, 10);
        const seed = parseInt(document.getElementById("bench-seed").value, 10);
        const trials = parseInt(document.getElementById("bench-trials").value, 10) || 3;

        if (minItems > maxItems) {
            showBenchError("Min items cannot be greater than max items.");
            return;
        }

        const btnRun = document.getElementById("btn-run-benchmark");
        const origText = btnRun.innerHTML;
        btnRun.disabled = true;
        btnRun.innerHTML = `<span class="spinner"></span> Running C++ Sweep...`;

        try {
            const payload = {
                min_items: minItems,
                max_items: maxItems,
                step_items: stepItems,
                capacity: capacity,
                min_weight: minW,
                max_weight: maxW,
                min_value: minV,
                max_value: maxV,
                seed: seed,
                trials: trials
            };

            const res = await fetch("/api/benchmark", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload)
            });

            const data = await res.json();
            if (!res.ok || !data.success) {
                showBenchError(data.error || "Benchmark sweep failed.");
                return;
            }

            lastBenchmarkData = data;
            renderBenchmarkResults(data);
        } catch (e) {
            showBenchError("Benchmark execution error: " + e.message);
        } finally {
            btnRun.disabled = false;
            btnRun.innerHTML = origText;
        }
    }

    function showBenchError(msg) {
        const alertBox = document.getElementById("benchmark-alert-box");
        if (alertBox) {
            alertBox.className = "alert alert-danger";
            alertBox.style.display = "block";
            alertBox.textContent = msg;
        }
    }

    function renderBenchmarkResults(data) {
        const container = document.getElementById("benchmark-results-container");
        if (!container) return;
        container.style.display = "block";

        const tbody = document.getElementById("benchmark-table-body");
        tbody.innerHTML = "";

        data.points.forEach(p => {
            const tr = document.createElement("tr");

            let fasterAlgo = "Tie";
            let speedupStr = "1.00x";
            if (p.bb_time_ms < p.dp_time_ms * 0.95 && p.bb_time_ms > 0) {
                fasterAlgo = "<span class='badge badge-pink'>B&B Faster</span>";
                speedupStr = `${(p.dp_time_ms / p.bb_time_ms).toFixed(2)}x`;
            } else if (p.dp_time_ms < p.bb_time_ms * 0.95 && p.dp_time_ms > 0) {
                fasterAlgo = "<span class='badge badge-purple'>DP Faster</span>";
                speedupStr = `${(p.bb_time_ms / p.dp_time_ms).toFixed(2)}x`;
            }

            const agreementBadge = p.agreement ?
                `<span class="badge badge-success">Match (${p.dp_optimal_value.toLocaleString()})</span>` :
                `<span class="badge badge-danger">Mismatch</span>`;

            tr.innerHTML = `
                <td><strong>N = ${p.item_count}</strong></td>
                <td class="num">${p.dp_time_ms.toFixed(4)} ms</td>
                <td class="num">${p.bb_time_ms.toFixed(4)} ms</td>
                <td style="text-align: center;">${fasterAlgo} (${speedupStr})</td>
                <td class="num">${p.dp_workspace_kb.toFixed(1)} KB</td>
                <td class="num">${p.bb_workspace_kb.toFixed(1)} KB</td>
                <td class="num">${p.nodes_expanded.toLocaleString()}</td>
                <td class="num">${p.nodes_pruned.toLocaleString()}</td>
                <td style="text-align: center;">${agreementBadge}</td>
            `;
            tbody.appendChild(tr);
        });

        // Trigger Canvas Charts
        KnapsackCharts.renderRuntimeChart("canvas-runtime", data.points, useLogScale);
        KnapsackCharts.renderMemoryChart("canvas-memory", data.points, memoryMetric);
        KnapsackCharts.renderSearchSpaceChart("canvas-search-space", data.points);

        // Scroll to results
        container.scrollIntoView({ behavior: 'smooth' });
    }

    function handleExportCsv() {
        if (!lastBenchmarkData || !lastBenchmarkData.points) {
            alert("No benchmark results to export.");
            return;
        }
        const headers = ["ItemCount", "Capacity", "DP_OptimalValue", "BB_OptimalValue", "DP_Time_ms", "BB_Time_ms", "DP_Workspace_KB", "BB_Workspace_KB", "NodesExpanded", "NodesPruned", "Agreement"];
        const rows = lastBenchmarkData.points.map(p => [
            p.item_count,
            p.capacity,
            p.dp_optimal_value,
            p.bb_optimal_value,
            p.dp_time_ms,
            p.bb_time_ms,
            p.dp_workspace_kb,
            p.bb_workspace_kb,
            p.nodes_expanded,
            p.nodes_pruned,
            p.agreement ? "YES" : "NO"
        ]);

        const csvContent = "data:text/csv;charset=utf-8," + [headers.join(","), ...rows.map(e => e.join(","))].join("\n");
        const encodedUri = encodeURI(csvContent);
        const link = document.createElement("a");
        link.setAttribute("href", encodedUri);
        link.setAttribute("download", `knapsack_benchmark_${Date.now()}.csv`);
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    }

    function handleExportJson() {
        if (!lastBenchmarkData) {
            alert("No benchmark results to export.");
            return;
        }
        const jsonStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(lastBenchmarkData, null, 2));
        const link = document.createElement("a");
        link.setAttribute("href", jsonStr);
        link.setAttribute("download", `knapsack_benchmark_${Date.now()}.json`);
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    }

    return {
        init
    };
})();
