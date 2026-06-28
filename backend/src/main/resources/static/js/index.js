// State Management
let currentRunResult = null;
let selectedSetup = null;
let currentScanMode = 'universe'; // 'universe' | 'custom'

// Table sorting/filtering state
let tableSearchQuery = "";
let tableDecisionFilter = "ALL";
let tableSortKey = "";
let tableSortAsc = true;
let currentSetups = [];

// DOM Elements
const btnRunScreener = document.getElementById("btn-run-screener");
const btnText = document.getElementById("btn-text");
const btnLoader = document.getElementById("btn-loader");
const statusPython = document.getElementById("status-python");
const latestRunInfo = document.getElementById("latest-run-info");
const latestRunTime = document.getElementById("latest-run-time");
const dataStaleness = document.getElementById("data-staleness-badge");
const dashboardSubtitle = document.getElementById("dashboard-subtitle");

// Stats Cards
const statScanned = document.getElementById("stat-scanned");
const statFiltered = document.getElementById("stat-filtered");
const statSelected = document.getElementById("stat-selected");
const statRejected = document.getElementById("stat-rejected");

// Table
const tableBody = document.getElementById("screener-table-body");
const tableRowCount = document.getElementById("table-row-count");

// Download Buttons
const btnDownloadJson = document.getElementById("btn-download-json");
const btnDownloadCsv = document.getElementById("btn-download-csv");

// Config inputs
const inputMinPrice = document.getElementById("input-min-price");
const inputMaxPrice = document.getElementById("input-max-price");
const inputMoveVariance = document.getElementById("input-move-variance");
const inputLookback = document.getElementById("input-lookback");
const inputMinRr = document.getElementById("input-min-rr");
const inputInterval = document.getElementById("input-interval");

// Custom Symbol mode elements
const inputSymbols = document.getElementById("input-symbols");
const inputCustomThreshold = document.getElementById("input-custom-threshold");
const customSymbolPanel = document.getElementById("custom-symbol-panel");
const universeFilterPanel = document.getElementById("universe-filter-panel");

// Drawer
const detailsDrawer = document.getElementById("details-drawer");
const btnCloseDrawer = document.getElementById("btn-close-drawer");
const detailsDrawerOverlay = document.getElementById("details-drawer-overlay");

// ─── Mode Toggle ──────────────────────────────────────────────────────────────
window.setScanMode = function (mode) {
    currentScanMode = mode;
    const universePanel = document.getElementById("universe-filter-panel");
    const customPanel = document.getElementById("custom-symbol-panel");
    const btnNifty = document.getElementById("btn-mode-nifty");
    const btnCustom = document.getElementById("btn-mode-custom");

    if (mode === 'universe') {
        if (btnNifty) btnNifty.classList.add("active");
        if (btnCustom) btnCustom.classList.remove("active");
        universePanel.classList.remove("field-disabled");
        customPanel.classList.add("hidden");
        if (dashboardSubtitle) dashboardSubtitle.textContent = "Scans Nifty universe for high-momentum stocks";
    } else {
        if (btnNifty) btnNifty.classList.remove("active");
        if (btnCustom) btnCustom.classList.add("active");
        universePanel.classList.add("field-disabled");
        customPanel.classList.remove("hidden");
        if (dashboardSubtitle) dashboardSubtitle.textContent = "Analyzing custom NSE symbols";
    }
};

// ─── Initialize Dashboard ─────────────────────────────────────────────────────
document.addEventListener("DOMContentLoaded", () => {
    checkHealth();
    loadLatestResult();

    // Bind Event Listeners
    btnRunScreener.addEventListener("click", runScreener);
    btnCloseDrawer.addEventListener("click", closeDrawer);
    detailsDrawerOverlay.addEventListener("click", closeDrawer);

    // Sidebar Toggle Event Listener
    const btnToggleSidebar = document.getElementById("btn-toggle-sidebar");
    const appContainer = document.querySelector(".app-container");
    if (btnToggleSidebar && appContainer) {
        btnToggleSidebar.addEventListener("click", () => {
            appContainer.classList.toggle("sidebar-collapsed");
        });
    }

    // Table Search and Filter Event Listeners
    const tableSearch = document.getElementById("table-search");
    const tableFilterDecision = document.getElementById("table-filter-decision");
    if (tableSearch) {
        tableSearch.addEventListener("input", (e) => {
            tableSearchQuery = e.target.value.toLowerCase().trim();
            renderTable();
        });
    }
    if (tableFilterDecision) {
        tableFilterDecision.addEventListener("change", (e) => {
            tableDecisionFilter = e.target.value;
            renderTable();
        });
    }
});

// ─── API Helper ───────────────────────────────────────────────────────────────
async function apiCall(url, options = {}) {
    try {
        const response = await fetch(url, options);
        const json = await response.json();
        if (!response.ok) {
            const errorMsg = json.message || `HTTP error! status: ${response.status}`;
            const errorsList = json.errors || [];
            throw { message: errorMsg, errors: errorsList };
        }
        return json;
    } catch (err) {
        console.error("API Call error:", err);
        throw err;
    }
}

// ─── Health Diagnostics ───────────────────────────────────────────────────────
async function checkHealth() {
    try {
        const res = await apiCall("/api/v1/screener/health");
        if (res.status === "SUCCESS") {
            const data = res.data;
            statusPython.textContent = `${data.pythonEngineStatus} (${data.pythonVersion})`;
            if (data.pythonEngineStatus === "UP") {
                statusPython.className = "status-badge badge-green";
            } else {
                statusPython.className = "status-badge badge-red";
            }
        }
    } catch (err) {
        statusPython.textContent = "DOWN";
        statusPython.className = "status-badge badge-red";
    }
}

// ─── Load Latest Snapshot ─────────────────────────────────────────────────────
async function loadLatestResult() {
    try {
        const res = await apiCall("/api/v1/screener/latest");
        if (res.status === "SUCCESS" && res.data) {
            updateDashboard(res.data);
        }
    } catch (err) {
        console.log("No previous screener snapshot found on disk yet.");
    }
}

// ─── Run Screener ─────────────────────────────────────────────────────────────
async function runScreener() {
    let requestPayload;

    if (currentScanMode === 'custom') {
        // Custom symbol mode
        const symbolsRaw = inputSymbols ? inputSymbols.value.trim() : "";
        if (!symbolsRaw) {
            alert("Please enter at least one NSE symbol (e.g. HSCL.NS).");
            return;
        }
        const symbols = symbolsRaw.split(",")
            .map(s => {
                let symbol = s.trim().toUpperCase();
                if (symbol && !symbol.includes('.')) {
                    symbol += '.NS';
                }
                return symbol;
            })
            .filter(s => s.length > 0);
        if (symbols.length === 0) {
            alert("No valid symbols found. Please enter symbols like HSCL.NS, RELIANCE.NS");
            return;
        }
        const customThreshold = parseFloat(inputCustomThreshold ? inputCustomThreshold.value : 0.5);
        const minRrVal = inputMinRr ? (parseFloat(inputMinRr.value) || 0.1) : 0.1;

        requestPayload = {
            runMode: "LIVE",
            symbols: symbols,
            filters: {
                minPrice: 0,
                maxPrice: 999999,
                moveThreshold: isNaN(customThreshold) ? 0.5 : customThreshold,
                moveVariance: 3.0
            },
            analytics: {
                lookbackDays: parseInt(inputLookback.value),
                rsiPeriod: 14,
                bollingerPeriod: 20,
                bollingerStdDev: 2.0,
                atrPeriod: 14,
                atrMultiplier: 1.5,
                minRiskReward: minRrVal,
                useRiskRewardFilter: true,
                intradayInterval: inputInterval.value
            }
        };
    } else {
        // Nifty Universe mode
        const minPrice = parseFloat(inputMinPrice.value);
        const maxPrice = parseFloat(inputMaxPrice.value);
        const moveVariance = parseFloat(inputMoveVariance.value);
        if (minPrice >= maxPrice) {
            alert("Min Price must be less than Max Price.");
            return;
        }
        if (isNaN(moveVariance) || moveVariance < 0) {
            alert("Variance threshold must be greater than or equal to 0.");
            return;
        }
        const minRiskRewardVal = parseFloat(inputMinRr.value) || 0.1;
        if (isNaN(minRiskRewardVal) || minRiskRewardVal < 0) {
            alert("Min Risk-Reward Ratio must be greater than or equal to 0.");
            return;
        }

        requestPayload = {
            runMode: "LIVE",
            symbols: [],
            includeTopGainers: true,
            includeTopLosers: true,
            snapshotMode: true,
            outputFormats: ["JSON", "CSV"],
            filters: {
                minPrice: minPrice,
                maxPrice: maxPrice,
                moveThreshold: 0.0, // Ignore in Nifty mode
                moveVariance: moveVariance
            },
            analytics: {
                lookbackDays: parseInt(inputLookback.value),
                rsiPeriod: 14,
                bollingerPeriod: 20,
                bollingerStdDev: 2.0,
                atrPeriod: 14,
                atrMultiplier: 1.5,
                minRiskReward: minRiskRewardVal,
                useRiskRewardFilter: true,
                intradayInterval: inputInterval.value
            }
        };
    }

    setLoadingState(true);

    try {
        const res = await apiCall("/api/v1/screener/run", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(requestPayload)
        });

        if (res.status === "SUCCESS") {
            updateDashboard(res.data);
        }
    } catch (err) {
        let msg = "Failed to run screener. ";
        if (err.message) msg += err.message;
        if (err.errors && err.errors.length > 0) {
            msg += "\nDetails:\n" + err.errors.map(e => `- ${e.detail}`).join("\n");
        }
        alert(msg);
    } finally {
        setLoadingState(false);
        checkHealth();
    }
}

// UI Loader control
function setLoadingState(isLoading) {
    const btnTextEl = document.getElementById("btn-text");
    const btnLoaderEl = document.getElementById("btn-loader");
    const btn = document.getElementById("btn-run-screener");
    if (isLoading) {
        btn.disabled = true;
        if (btnTextEl) btnTextEl.textContent = "Running...";
        if (btnLoaderEl) btnLoaderEl.classList.remove("hidden");
    } else {
        btn.disabled = false;
        if (btnTextEl) btnTextEl.textContent = "Run Screener";
        if (btnLoaderEl) btnLoaderEl.classList.add("hidden");
    }
}

// ─── Dashboard Updater ────────────────────────────────────────────────────────
function updateDashboard(data) {
    currentRunResult = data;

    // Display run time
    const runDate = new Date(data.runTime);
    const parsedTime = runDate.toLocaleString();
    latestRunTime.textContent = parsedTime;
    latestRunInfo.classList.remove("hidden");

    // Staleness check: show warning if run date is not today
    const today = new Date();
    const isToday = runDate.toDateString() === today.toDateString();
    if (!isToday && dataStaleness) {
        dataStaleness.classList.remove("hidden");
        dataStaleness.title = `Data is from ${runDate.toLocaleDateString()} — run a fresh screener for today's data`;
    } else if (dataStaleness) {
        dataStaleness.classList.add("hidden");
    }

    // Summary Cards
    statScanned.textContent = data.totalScanned;
    statFiltered.textContent = data.totalFiltered;
    statSelected.textContent = data.totalSelected;
    statRejected.textContent = data.totalRejected;

    // Download links
    if (btnDownloadJson) btnDownloadJson.classList.remove("disabled");
    if (btnDownloadCsv) btnDownloadCsv.classList.remove("disabled");

    // Populate Results Table
    populateTable(data.setups);
}

// ─── Table Builder ────────────────────────────────────────────────────────────
function populateTable(setups) {
    currentSetups = setups || [];
    renderTable();
}

window.handleSort = function (key) {
    if (tableSortKey === key) {
        tableSortAsc = !tableSortAsc;
    } else {
        tableSortKey = key;
        tableSortAsc = true;
    }

    // Update sort headers UI
    const thElements = document.querySelectorAll("#screener-table th.sortable");
    thElements.forEach(th => {
        th.classList.remove("sort-asc", "sort-desc");
        const onclickAttr = th.getAttribute("onclick");
        if (onclickAttr && onclickAttr.includes(`'${key}'`)) {
            th.classList.add(tableSortAsc ? "sort-asc" : "sort-desc");
        }
    });

    renderTable();
};

function renderTable() {
    if (!currentSetups) return;
    tableBody.innerHTML = "";

    // 1. Filter setups
    let filtered = currentSetups;

    // Respect decision filter from UI
    if (tableDecisionFilter !== "ALL") {
        filtered = filtered.filter(s => s.finalDecision === tableDecisionFilter);
    } else {
        // If filter is ALL, filter out REJECT for universe mode only
        if (currentScanMode !== 'custom') {
            filtered = filtered.filter(s => s.finalDecision !== "REJECT");
        }
    }

    // Filter by search query
    if (tableSearchQuery) {
        filtered = filtered.filter(s => s.symbol.toLowerCase().includes(tableSearchQuery));
    }

    // 2. Sort setups
    if (tableSortKey) {
        filtered.sort((a, b) => {
            let valA = a[tableSortKey];
            let valB = b[tableSortKey];

            if (typeof valA === 'string') valA = valA.toLowerCase();
            if (typeof valB === 'string') valB = valB.toLowerCase();

            if (valA == null) return tableSortAsc ? 1 : -1;
            if (valB == null) return tableSortAsc ? -1 : 1;

            if (valA < valB) return tableSortAsc ? -1 : 1;
            if (valA > valB) return tableSortAsc ? 1 : -1;
            return 0;
        });
    }

    tableRowCount.textContent = `${filtered.length} items`;

    if (filtered.length === 0) {
        const tr = document.createElement("tr");
        tr.className = "empty-state";
        tr.innerHTML = `
            <td colspan="9">
                <div class="empty-state-content">
                    <svg class="empty-icon" viewBox="0 0 24 24"><path d="M15.5 14h-.79l-.28-.27C15.41 12.59 16 11.11 16 9.5 16 5.91 13.09 3 9.5 3S3 5.91 3 9.5 5.91 16 9.5 16c1.61 0 3.09-.59 4.23-1.57l.27.28v.79l5 4.99L20.49 19l-4.99-5zm-6 0C7.01 14 5 11.99 5 9.5S7.01 5 9.5 5 14 7.01 14 9.5 11.99 14 9.5 14z"/></svg>
                    <p>No matching setups found.</p>
                </div>
            </td>
        `;
        tableBody.appendChild(tr);
        return;
    }

    filtered.forEach(setup => {
        const tr = document.createElement("tr");

        const decisionClass = setup.finalDecision === "TRADE" ? "badge-trade"
            : (setup.finalDecision === "WATCHLIST" ? "badge-watchlist" : "badge-reject");
        const moveClass = setup.currentPercentMove >= 0 ? "text-green" : "text-red";
        const rsiColorClass = setup.rsiLabel === "BULLISH" ? "text-green"
            : (setup.rsiLabel === "BEARISH" ? "text-red" : "");

        const expRange = setup.targetMin && setup.targetMax
            ? `₹${setup.targetMin.toFixed(2)} - ₹${setup.targetMax.toFixed(2)}`
            : '-';

        const symbolClean = setup.symbol.replace('.NS', '');
        const tvUrl = `https://in.tradingview.com/chart/?symbol=NSE%3A${symbolClean}`;

        tr.innerHTML = `
            <td>
                <strong>
                    <a href="${tvUrl}" target="_blank" rel="noopener noreferrer" class="tv-link" title="Open TradingView Chart">
                        ${symbolClean}
                        <svg class="tv-icon" viewBox="0 0 24 24" width="12" height="12" style="display:inline-block; vertical-align:middle; margin-left:4px;">
                            <path fill="currentColor" d="M14 3h7v7h-2V6.4l-9.3 9.3-1.4-1.4L17.6 5H14V3zm-2 11h-2v4H6V8h4V6H6c-1.1 0-2 .9-2 2v10c0 1.1.9 2 2 2h6c1.1 0 2-.9 2-2v-4z"/>
                        </svg>
                    </a>
                </strong>
            </td>
            <td>₹${setup.currentPrice.toFixed(2)}</td>
            <td class="${moveClass}">${setup.currentPercentMove >= 0 ? '+' : ''}${setup.currentPercentMove.toFixed(2)}%</td>
            <td>${expRange}</td>
            <td>${setup.typicalHighTime || '-'}</td>
            <td>${setup.typicalLowTime || '-'}</td>
            <td class="${rsiColorClass}">${setup.rsi14 ? setup.rsi14.toFixed(1) : '-'}</td>
            <td><span class="badge ${decisionClass}">${setup.finalDecision}</span></td>
            <td>
                <button type="button" class="btn-view" onclick="openDetails('${setup.symbol}')">Details</button>
            </td>
        `;
        tableBody.appendChild(tr);
    });
}

// ─── Drawer Actions ───────────────────────────────────────────────────────────
window.openDetails = function (symbol) {
    if (!currentRunResult) return;

    const setup = currentRunResult.setups.find(s => s.symbol === symbol);
    if (!setup) return;

    selectedSetup = setup;

    // Title
    const symbolClean = setup.symbol.replace('.NS', '');
    const tvUrl = `https://in.tradingview.com/chart/?symbol=NSE%3A${symbolClean}`;
    document.getElementById("drawer-symbol").innerHTML = `
        <a href="${tvUrl}" target="_blank" rel="noopener noreferrer" class="tv-link" title="Open TradingView Chart">
            ${setup.symbol}
            <svg class="tv-icon" viewBox="0 0 24 24" width="16" height="16" style="display:inline-block; vertical-align:middle; margin-left:6px;">
                <path fill="currentColor" d="M14 3h7v7h-2V6.4l-9.3 9.3-1.4-1.4L17.6 5H14V3zm-2 11h-2v4H6V8h4V6H6c-1.1 0-2 .9-2 2v10c0 1.1.9 2 2 2h6c1.1 0 2-.9 2-2v-4z"/>
            </svg>
        </a>
    `;
    const drawerSide = document.getElementById("drawer-side");
    drawerSide.textContent = setup.tradeSide;
    drawerSide.className = setup.tradeSide === "LONG" ? "badge badge-long" : "badge badge-short";

    // Price Info & Decision
    const drawerDecision = document.getElementById("drawer-decision");
    drawerDecision.textContent = setup.finalDecision;
    drawerDecision.className = setup.finalDecision === "TRADE" ? "badge-big badge-trade" : "badge-big badge-watchlist";

    const moveSign = setup.currentPercentMove >= 0 ? "+" : "";
    document.getElementById("drawer-price-info").innerHTML = `Current Price: <strong>₹${setup.currentPrice.toFixed(2)}</strong> (${moveSign}${setup.currentPercentMove.toFixed(2)}%)`;

    // Notes list
    const notesList = document.getElementById("drawer-notes-list");
    notesList.innerHTML = "";
    (setup.decisionNotes || []).forEach(note => {
        const li = document.createElement("li");
        li.textContent = note;
        notesList.appendChild(li);
    });

    // Warnings
    const warningsBox = document.getElementById("drawer-warnings-box");
    const warningsList = document.getElementById("drawer-warnings-list");
    warningsList.innerHTML = "";
    if (setup.warnings && setup.warnings.length > 0) {
        setup.warnings.forEach(w => {
            const li = document.createElement("li");
            li.textContent = w;
            warningsList.appendChild(li);
        });
        warningsBox.classList.remove("hidden");
    } else {
        warningsBox.classList.add("hidden");
    }

    // Volatility Stats
    document.getElementById("drawer-sample-count").textContent = setup.comparableSampleCount || '-';
    document.getElementById("drawer-max-gain").textContent = setup.historicalMaxGainPercent != null ? `${setup.historicalMaxGainPercent >= 0 ? '+' : ''}${setup.historicalMaxGainPercent.toFixed(2)}%` : '-';
    document.getElementById("drawer-max-loss").textContent = setup.historicalMaxLossPercent != null ? `${setup.historicalMaxLossPercent >= 0 ? '+' : ''}${setup.historicalMaxLossPercent.toFixed(2)}%` : '-';
    document.getElementById("drawer-avg-ext").textContent = setup.avgExtensionPercent != null ? `${setup.avgExtensionPercent.toFixed(2)}%` : '-';
    document.getElementById("drawer-avg-close").textContent = setup.avgClosePercent != null ? `${setup.avgClosePercent.toFixed(2)}%` : '-';

    // Timing & Swing
    document.getElementById("drawer-high-time").textContent = setup.typicalHighTime || '-';
    document.getElementById("drawer-low-time").textContent = setup.typicalLowTime || '-';
    document.getElementById("drawer-time-pattern").textContent = setup.timePatternLabel ? setup.timePatternLabel.replace(/_/g, ' ') : '-';
    document.getElementById("drawer-swing-ref").textContent = setup.swingStopReference ? `₹${setup.swingStopReference.toFixed(2)}` : '-';
    document.getElementById("drawer-bollinger").textContent = (setup.bollingerState || '-').replace(/_/g, ' ');
    document.getElementById("drawer-atr").textContent = setup.atr14 ? setup.atr14.toFixed(2) : '-';

    // Execution Plan targets
    document.getElementById("drawer-sl-type").textContent = setup.stopLossType || '-';
    document.getElementById("drawer-stop-loss").textContent = setup.stopLoss ? `₹${setup.stopLoss.toFixed(2)}` : '-';
    document.getElementById("drawer-risk-amount").textContent = setup.riskAmount ? `₹${setup.riskAmount.toFixed(2)}` : '-';
    document.getElementById("drawer-target-range").textContent = setup.targetMin ? `₹${setup.targetMin.toFixed(2)} - ₹${setup.targetMax.toFixed(2)}` : '-';
    document.getElementById("drawer-reward-amount").textContent = setup.rewardAmount ? `₹${setup.rewardAmount.toFixed(2)}` : '-';
    document.getElementById("drawer-exit-zone").textContent = setup.expectedExitZone ? `₹${setup.expectedExitZone.toFixed(2)}` : '-';
    document.getElementById("drawer-rr-ratio").textContent = setup.riskRewardRatio ? `${setup.riskRewardRatio.toFixed(1)}x` : '-';

    // Open drawer
    detailsDrawer.classList.remove("hidden");
    document.body.style.overflow = "hidden";
};

function closeDrawer() {
    detailsDrawer.classList.add("hidden");
    document.body.style.overflow = "";
    selectedSetup = null;
}
