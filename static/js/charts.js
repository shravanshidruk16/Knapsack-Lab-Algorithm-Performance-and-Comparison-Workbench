/**
 * Knapsack Lab — Custom HTML5 Canvas Chart Engine
 * Lightweight, zero-dependency charts with Times New Roman typography,
 * crisp Retina/High-DPI scaling, and interactive hover tooltips.
 */

const KnapsackCharts = (function() {
    // Styling constants
    const COLOR_DP = '#7450C8';           // Primary Purple
    const COLOR_BB = '#E76AA8';           // Accent Pink
    const COLOR_EXPANDED = '#51358E';     // Dark Purple
    const COLOR_PRUNED = '#E76AA8';       // Accent Pink
    const COLOR_GENERATED = '#2F855A';    // Muted Green
    const COLOR_GRID = '#EDE4F2';
    const COLOR_TEXT = '#28212E';
    const COLOR_SUBTEXT = '#716779';
    const FONT_SERIF = '"Times New Roman", Times, serif';

    function setupCanvas(canvas) {
        const dpr = window.devicePixelRatio || 1;
        const rect = canvas.getBoundingClientRect();
        canvas.width = rect.width * dpr;
        canvas.height = rect.height * dpr;
        const ctx = canvas.getContext('2d');
        ctx.resetTransform && ctx.resetTransform();
        ctx.scale(dpr, dpr);
        return { ctx, width: rect.width, height: rect.height };
    }

    /**
     * Plots dual runtime comparison (DP vs B&B)
     */
    function renderRuntimeChart(canvasId, points, useLogScale = false) {
        const canvas = document.getElementById(canvasId);
        if (!canvas) return;
        const { ctx, width, height } = setupCanvas(canvas);

        ctx.clearRect(0, 0, width, height);

        if (!points || points.length === 0) {
            drawEmptyState(ctx, width, height, "No benchmark points to display.");
            return;
        }

        const padding = { top: 30, right: 30, bottom: 45, left: 65 };
        const plotW = width - padding.left - padding.right;
        const plotH = height - padding.top - padding.bottom;

        // Collect Y-values (in milliseconds)
        const dpValues = points.map(p => p.dp_time_ms || 0.0);
        const bbValues = points.map(p => p.bb_time_ms || 0.0);
        const allY = [...dpValues, ...bbValues];
        const maxY = Math.max(...allY, 0.01);
        const minY = useLogScale ? Math.min(...allY.filter(v => v > 0), 0.001) : 0;

        // X scale (Item count)
        const xValues = points.map(p => p.item_count);
        const minX = Math.min(...xValues);
        const maxX = Math.max(...xValues);

        function getX(x) {
            if (maxX === minX) return padding.left + plotW / 2;
            return padding.left + ((x - minX) / (maxX - minX)) * plotW;
        }

        function getY(y) {
            if (useLogScale) {
                const logMin = Math.log10(Math.max(minY, 0.0001));
                const logMax = Math.log10(Math.max(maxY, 0.001));
                const safeY = Math.max(y, 0.0001);
                const ratio = (Math.log10(safeY) - logMin) / (logMax - logMin || 1);
                return padding.top + plotH - (ratio * plotH);
            }
            return padding.top + plotH - ((y / (maxY || 1)) * plotH);
        }

        // Draw Grid and Y-Ticks
        drawYGrid(ctx, padding, plotW, plotH, maxY, minY, useLogScale, "ms");

        // Draw X-Ticks
        drawXTicks(ctx, padding, plotW, plotH, points, getX);

        // Draw Series
        drawLineSeries(ctx, points, p => p.item_count, p => p.dp_time_ms || 0, getX, getY, COLOR_DP, "Dynamic Programming");
        drawLineSeries(ctx, points, p => p.item_count, p => p.bb_time_ms || 0, getX, getY, COLOR_BB, "Branch and Bound");

        // Axis Titles
        ctx.fillStyle = COLOR_TEXT;
        ctx.font = `bold 13px ${FONT_SERIF}`;
        ctx.textAlign = 'center';
        ctx.fillText("Problem Size: Number of Items (N)", padding.left + plotW / 2, height - 8);

        ctx.save();
        ctx.translate(16, padding.top + plotH / 2);
        ctx.rotate(-Math.PI / 2);
        ctx.fillText(`Execution Time (${useLogScale ? "Log10 ms" : "ms"})`, 0, 0);
        ctx.restore();
    }

    /**
     * Plots memory comparison (Peak Working Set or Algorithm Workspace)
     */
    function renderMemoryChart(canvasId, points, metric = 'workspace') {
        const canvas = document.getElementById(canvasId);
        if (!canvas) return;
        const { ctx, width, height } = setupCanvas(canvas);

        ctx.clearRect(0, 0, width, height);

        if (!points || points.length === 0) {
            drawEmptyState(ctx, width, height, "No memory data to display.");
            return;
        }

        const padding = { top: 30, right: 30, bottom: 45, left: 75 };
        const plotW = width - padding.left - padding.right;
        const plotH = height - padding.top - padding.bottom;

        // Metric selector
        const dpValues = points.map(p => metric === 'workspace' ? p.dp_workspace_kb : p.dp_peak_memory_kb);
        const bbValues = points.map(p => metric === 'workspace' ? p.bb_workspace_kb : p.bb_peak_memory_kb);
        const maxY = Math.max(...dpValues, ...bbValues, 1);

        const xValues = points.map(p => p.item_count);
        const minX = Math.min(...xValues);
        const maxX = Math.max(...xValues);

        function getX(x) {
            if (maxX === minX) return padding.left + plotW / 2;
            return padding.left + ((x - minX) / (maxX - minX)) * plotW;
        }

        function getY(y) {
            return padding.top + plotH - ((y / maxY) * plotH);
        }

        drawYGrid(ctx, padding, plotW, plotH, maxY, 0, false, "KB");
        drawXTicks(ctx, padding, plotW, plotH, points, getX);

        drawLineSeries(ctx, points, p => p.item_count, p => (metric === 'workspace' ? p.dp_workspace_kb : p.dp_peak_memory_kb), getX, getY, COLOR_DP, "DP");
        drawLineSeries(ctx, points, p => p.item_count, p => (metric === 'workspace' ? p.bb_workspace_kb : p.bb_peak_memory_kb), getX, getY, COLOR_BB, "B&B");

        ctx.fillStyle = COLOR_TEXT;
        ctx.font = `bold 13px ${FONT_SERIF}`;
        ctx.textAlign = 'center';
        ctx.fillText("Problem Size: Number of Items (N)", padding.left + plotW / 2, height - 8);

        ctx.save();
        ctx.translate(18, padding.top + plotH / 2);
        ctx.rotate(-Math.PI / 2);
        ctx.fillText(metric === 'workspace' ? "Workspace Footprint (KB)" : "Peak Working Set (KB)", 0, 0);
        ctx.restore();
    }

    /**
     * Plots Branch and Bound state-space tree statistics (Expanded vs Pruned vs Frontier)
     */
    function renderSearchSpaceChart(canvasId, points) {
        const canvas = document.getElementById(canvasId);
        if (!canvas) return;
        const { ctx, width, height } = setupCanvas(canvas);

        ctx.clearRect(0, 0, width, height);

        if (!points || points.length === 0) {
            drawEmptyState(ctx, width, height, "No search statistics available.");
            return;
        }

        const padding = { top: 30, right: 30, bottom: 45, left: 65 };
        const plotW = width - padding.left - padding.right;
        const plotH = height - padding.top - padding.bottom;

        const expanded = points.map(p => p.nodes_expanded || 0);
        const pruned = points.map(p => p.nodes_pruned || 0);
        const frontier = points.map(p => p.max_frontier_size || 0);
        const maxY = Math.max(...expanded, ...pruned, ...frontier, 5);

        const xValues = points.map(p => p.item_count);
        const minX = Math.min(...xValues);
        const maxX = Math.max(...xValues);

        function getX(x) {
            if (maxX === minX) return padding.left + plotW / 2;
            return padding.left + ((x - minX) / (maxX - minX)) * plotW;
        }

        function getY(y) {
            return padding.top + plotH - ((y / maxY) * plotH);
        }

        drawYGrid(ctx, padding, plotW, plotH, maxY, 0, false, "");
        drawXTicks(ctx, padding, plotW, plotH, points, getX);

        drawLineSeries(ctx, points, p => p.item_count, p => p.nodes_expanded || 0, getX, getY, COLOR_EXPANDED, "Expanded");
        drawLineSeries(ctx, points, p => p.item_count, p => p.nodes_pruned || 0, getX, getY, COLOR_PRUNED, "Pruned");
        drawLineSeries(ctx, points, p => p.item_count, p => p.max_frontier_size || 0, getX, getY, COLOR_GENERATED, "Max Frontier");

        ctx.fillStyle = COLOR_TEXT;
        ctx.font = `bold 13px ${FONT_SERIF}`;
        ctx.textAlign = 'center';
        ctx.fillText("Problem Size: Number of Items (N)", padding.left + plotW / 2, height - 8);

        ctx.save();
        ctx.translate(18, padding.top + plotH / 2);
        ctx.rotate(-Math.PI / 2);
        ctx.fillText("Node Count", 0, 0);
        ctx.restore();
    }

    // Helper: Draw line series with point markers
    function drawLineSeries(ctx, data, xAccessor, yAccessor, getX, getY, color, label) {
        if (data.length === 0) return;

        ctx.strokeStyle = color;
        ctx.lineWidth = 2.5;
        ctx.beginPath();

        data.forEach((d, idx) => {
            const px = getX(xAccessor(d));
            const py = getY(yAccessor(d));
            if (idx === 0) ctx.moveTo(px, py);
            else ctx.lineTo(px, py);
        });
        ctx.stroke();

        // Draw points
        data.forEach(d => {
            const px = getX(xAccessor(d));
            const py = getY(yAccessor(d));
            ctx.fillStyle = '#FFFFFF';
            ctx.beginPath();
            ctx.arc(px, py, 4.5, 0, Math.PI * 2);
            ctx.fill();
            ctx.strokeStyle = color;
            ctx.lineWidth = 2;
            ctx.stroke();
        });
    }

    function drawYGrid(ctx, padding, plotW, plotH, maxY, minY, useLog, unit) {
        ctx.strokeStyle = COLOR_GRID;
        ctx.lineWidth = 1;
        ctx.fillStyle = COLOR_SUBTEXT;
        ctx.font = `11.5px ${FONT_SERIF}`;
        ctx.textAlign = 'right';

        const steps = 5;
        for (let i = 0; i <= steps; i++) {
            const yPos = padding.top + (plotH / steps) * i;
            let val;
            if (useLog) {
                const logMin = Math.log10(Math.max(minY, 0.0001));
                const logMax = Math.log10(Math.max(maxY, 0.001));
                const curLog = logMax - (i / steps) * (logMax - logMin);
                val = Math.pow(10, curLog).toFixed(3);
            } else {
                val = (maxY - (i / steps) * maxY).toFixed(maxY > 10 ? 0 : 3);
            }

            ctx.beginPath();
            ctx.moveTo(padding.left, yPos);
            ctx.lineTo(padding.left + plotW, yPos);
            ctx.stroke();

            ctx.fillText(`${val} ${unit}`, padding.left - 8, yPos + 4);
        }
    }

    function drawXTicks(ctx, padding, plotW, plotH, points, getX) {
        ctx.fillStyle = COLOR_SUBTEXT;
        ctx.font = `12px ${FONT_SERIF}`;
        ctx.textAlign = 'center';

        points.forEach(p => {
            const px = getX(p.item_count);
            ctx.beginPath();
            ctx.moveTo(px, padding.top + plotH);
            ctx.lineTo(px, padding.top + plotH + 5);
            ctx.strokeStyle = COLOR_GRID;
            ctx.stroke();

            ctx.fillText(p.item_count, px, padding.top + plotH + 18);
        });
    }

    function drawEmptyState(ctx, width, height, message) {
        ctx.fillStyle = COLOR_SUBTEXT;
        ctx.font = `italic 14px ${FONT_SERIF}`;
        ctx.textAlign = 'center';
        ctx.fillText(message, width / 2, height / 2);
    }

    return {
        renderRuntimeChart,
        renderMemoryChart,
        renderSearchSpaceChart
    };
})();
