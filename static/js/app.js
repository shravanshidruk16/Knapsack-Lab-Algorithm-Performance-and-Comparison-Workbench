/**
 * Knapsack Lab — Main Application Coordinator
 * Handles tab navigation, engine status checks, and view transitions.
 */

document.addEventListener("DOMContentLoaded", () => {
    initNavigation();
    initEngineStatus();
    KnapsackSolver.init();
    KnapsackBenchmark.init();
});

function initNavigation() {
    const navLinks = document.querySelectorAll(".nav-link[data-view]");
    const viewSections = document.querySelectorAll(".view-section");
    const pageTitle = document.getElementById("header-page-title");
    const pageDesc = document.getElementById("header-page-desc");

    const viewTitles = {
        "view-overview": {
            title: "Overview & Workbench Introduction",
            desc: "Comparative study of 0/1 Knapsack: Dynamic Programming vs. Branch and Bound"
        },
        "view-solver": {
            title: "Solve Knapsack Instance",
            desc: "Configure items, set knapsack capacity, and execute exact C++17 algorithms"
        },
        "view-compare": {
            title: "Algorithm Performance Comparison",
            desc: "Detailed side-by-side analysis, memory footprint, and speedup metrics"
        },
        "view-benchmark": {
            title: "Benchmark Laboratory",
            desc: "Empirical performance testing across problem sizes using reproducible seeds"
        },
        "view-theory": {
            title: "Algorithm Theory & Complexity",
            desc: "Mathematical formulations, state-space tree pruning, and pseudo-polynomial analysis"
        },
        "view-about": {
            title: "About the Project",
            desc: "DAA Mini-Project specifications, technology stack, and engineering notes"
        }
    };

    navLinks.forEach(link => {
        link.addEventListener("click", e => {
            e.preventDefault();
            const targetViewId = link.getAttribute("data-view");

            // Update active state in nav
            navLinks.forEach(l => l.classList.remove("active"));
            link.classList.add("active");

            // Switch visible view
            viewSections.forEach(section => {
                if (section.id === targetViewId) {
                    section.classList.add("active");
                } else {
                    section.classList.remove("active");
                }
            });

            // Update header title and description
            if (viewTitles[targetViewId]) {
                if (pageTitle) pageTitle.textContent = viewTitles[targetViewId].title;
                if (pageDesc) pageDesc.textContent = viewTitles[targetViewId].desc;
            }

            // Window resize trigger to re-render any visible canvas
            window.dispatchEvent(new Event("resize"));
        });
    });
}

async function initEngineStatus() {
    const statusPill = document.getElementById("engine-status-text");
    const statusDot = document.getElementById("engine-status-dot");

    try {
        const res = await fetch("/api/health");
        const data = await res.json();

        if (data && data.status === "healthy") {
            if (statusPill) statusPill.textContent = "C++17 Engine Ready";
            if (statusDot) {
                statusDot.className = "status-indicator-dot";
                statusDot.title = `Compiler: ${data.runner_details} on ${data.platform}`;
            }
        } else {
            if (statusPill) statusPill.textContent = "Engine Degraded / Build Needed";
            if (statusDot) statusDot.className = "status-indicator-dot offline";
        }
    } catch (e) {
        if (statusPill) statusPill.textContent = "Engine Offline";
        if (statusDot) statusDot.className = "status-indicator-dot offline";
    }
}
