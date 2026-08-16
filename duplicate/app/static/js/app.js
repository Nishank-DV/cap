let charts = {};


/* =========================================================
   GENERAL HELPERS
========================================================= */

function getJSON(url, options = {}) {

    return fetch(url, options)
        .then(response => {

            if (!response.ok) {
                throw new Error(
                    `Request failed: ${response.status}`
                );
            }

            return response.json();

        });

}


function showError(elementId, error) {

    const element =
        document.getElementById(elementId);

    if (!element) {
        return;
    }

    element.innerHTML =
        `<p class="alert alert-error">
            ${error.message || error}
        </p>`;

}


function createChart(id, config) {

    const canvas =
        document.getElementById(id);

    if (!canvas) {
        console.warn(
            `Chart canvas not found: ${id}`
        );
        return;
    }

    if (charts[id]) {
        charts[id].destroy();
    }

    charts[id] =
        new Chart(canvas, config);

}


function resetChartZoom(id) {

    if (
        charts[id] &&
        charts[id].resetZoom
    ) {

        charts[id].resetZoom();

    }

}


function formatNumber(value) {

    return Number(
        value || 0
    ).toLocaleString();

}


function formatPercentage(value) {

    return `${Number(
        value || 0
    ).toFixed(2)}%`;

}


function setText(id, value) {

    const element =
        document.getElementById(id);

    if (element) {

        element.textContent =
            value;

    }

}


/* =========================================================
   MAIN DASHBOARD
========================================================= */

function loadDashboardStats() {

    console.log(
        "Loading dashboard statistics..."
    );

    getJSON("/api/stats")

        .then(data => {

            console.log(
                "Dashboard statistics:",
                data
            );

            setText(
                "totalRecords",
                formatNumber(
                    data.total_records
                )
            );

            setText(
                "crimeTypes",
                formatNumber(
                    data.unique_crime_types
                )
            );

            setText(
                "arrests",
                formatNumber(
                    data.arrests
                )
            );

            setText(
                "domestic",
                formatNumber(
                    data.domestic_crimes
                )
            );

        })

        .catch(error => {

            console.error(
                "Dashboard statistics error:",
                error
            );

            setText(
                "totalRecords",
                "Error"
            );

            setText(
                "crimeTypes",
                "Error"
            );

            setText(
                "arrests",
                "Error"
            );

            setText(
                "domestic",
                "Error"
            );

        });

}


function loadDashboardYearlyChart() {

    console.log(
        "Loading yearly crime chart..."
    );

    getJSON("/api/charts/yearly")

        .then(data => {

            console.log(
                "Yearly chart data:",
                data
            );

            createChart(
                "yearChart",
                lineChart(
                    data.labels,
                    data.values,
                    "Crime Records"
                )
            );

        })

        .catch(error => {

            console.error(
                "Yearly chart error:",
                error
            );

        });

}


function loadDashboardCrimeTypeChart() {

    getJSON("/api/charts/crime-types")

        .then(data => {

            createChart(
                "crimeTypeChart",
                barChart(
                    data.labels,
                    data.values,
                    "Crime Count"
                )
            );

        })

        .catch(error => {

            console.error(
                "Crime type chart error:",
                error
            );

        });

}


function loadDashboardArrestChart() {

    getJSON("/api/charts/arrest")

        .then(data => {

            createChart(
                "arrestChart",
                doughnutChart(
                    data.labels,
                    data.values
                )
            );

        })

        .catch(error => {

            console.error(
                "Arrest chart error:",
                error
            );

        });

}


function loadDashboardDistrictChart() {

    getJSON("/api/charts/district")

        .then(data => {

            createChart(
                "districtChart",
                barChart(
                    data.labels,
                    data.values,
                    "Crime Count"
                )
            );

        })

        .catch(error => {

            console.error(
                "District chart error:",
                error
            );

        });

}


/* =========================================================
   UC1 — LOAD & CLEAN
========================================================= */

function loadUC1Data() {

    getJSON("/api/uc1/summary")

        .then(data => {

            setText(
                "uc1TotalRecords",
                formatNumber(data.rows)
            );

            setText(
                "uc1TotalColumns",
                formatNumber(data.columns)
            );

            setText(
                "uc1DuplicateRecords",
                formatNumber(data.duplicate_records)
            );

            setText(
                "uc1DuplicateIDs",
                formatNumber(data.duplicate_ids)
            );

            setText(
                "uc1FinalRecords",
                formatNumber(data.rows)
            );

            setText(
                "uc1FinalColumns",
                formatNumber(data.columns + 2)
            );

            setText(
                "uc1FinalDuplicateRecords",
                formatNumber(data.duplicate_records)
            );

            setText(
                "uc1FinalDuplicateIDs",
                formatNumber(data.duplicate_ids)
            );

            setText(
                "uc1UniqueCrimeTypes",
                formatNumber(data.unique_crime_types)
            );

            setText(
                "uc1MissingDates",
                formatNumber(data.missing_dates)
            );


            /* -----------------------------------------
               MISSING VALUES LIST
            ----------------------------------------- */

            const missingContainer =
                document.getElementById("uc1MissingList");

            if (missingContainer) {

                if (
                    !data.missing_values ||
                    data.missing_values.length === 0
                ) {

                    missingContainer.innerHTML =
                        `<p class="muted-text">
                            No missing values remain in the
                            cleaned dataset.
                        </p>`;

                } else {

                    missingContainer.innerHTML =
                        data.missing_values
                            .map(item => `
                                <div class="missing-row">
                                    <span>${item.column}</span>
                                    <strong>${item.percentage}%</strong>
                                </div>
                            `)
                            .join("");

                }

            }


            /* -----------------------------------------
               DATA MODEL — MASTER + REFERENCE FILES
            ----------------------------------------- */

            const modelBody =
                document.getElementById("uc1DataModelBody");

            if (modelBody) {

                if (
                    !data.data_model ||
                    data.data_model.length === 0
                ) {

                    modelBody.innerHTML =
                        `<tr>
                            <td colspan="6" class="loading-cell">
                                Data model unavailable.
                            </td>
                        </tr>`;

                } else {

                    modelBody.innerHTML =
                        data.data_model
                            .map(item => {

                                const statusLabel =
                                    item.invalid_keys === 0
                                        ? '<span class="database-badge">✓ All keys match</span>'
                                        : `<span class="database-badge" style="background:#ffeded;color:#c62828;">
                                               ${item.invalid_keys} unmatched
                                           </span>`;

                                return `
                                    <tr>
                                        <td><code>${item.file}</code></td>
                                        <td>${item.role}</td>
                                        <td>${item.join_key}</td>
                                        <td>${formatNumber(item.rows)}</td>
                                        <td>${item.columns}</td>
                                        <td>${statusLabel}</td>
                                    </tr>
                                `;

                            })
                            .join("");

                }

            }

        })

        .catch(error => {

            console.error(
                "UC1 error:",
                error
            );

        });

}


/* =========================================================
   UC2 — SUMMARY STATS
   (charts for this page are static matplotlib images
   generated by usecases/usecase2.py and served straight
   from /static/charts — no Chart.js involved)
========================================================= */

function loadUC2Summary() {

    getJSON("/api/uc2/summary")

        .then(data => {

            setText(
                "uc2TotalRecords",
                formatNumber(
                    data.total_records
                )
            );

            setText(
                "uc2TopCrime",
                data.top_crime ||
                "—"
            );

            setText(
                "uc2ArrestRate",
                formatPercentage(
                    data.arrest_rate
                )
            );

            setText(
                "uc2PeakDay",
                data.peak_day ||
                "—"
            );

            setText(
                "uc2Insight",
                data.insight ||
                "No additional insight available."
            );

        })

        .catch(error => {

            console.error(
                "UC2 summary error:",
                error
            );

            showError(
                "uc2Insight",
                error
            );

        });

}


/* =========================================================
   UC3 — STATISTICAL INSIGHTS
========================================================= */

function loadUC3Analysis() {

    getJSON("/api/uc3")

        .then(data => {

            setText(
                "uc3Total",
                formatNumber(
                    data.total_records
                )
            );


            setText(
                "uc3CrimeTypes",
                formatNumber(
                    data.unique_crime_types
                )
            );


            setText(
                "uc3MonthlyAverage",
                Number(
                    data.monthly_average || 0
                ).toFixed(2)
            );


            setText(
                "uc3Anomalies",
                formatNumber(
                    data.anomalies
                )
            );


            setText(
                "corrLatLong",
                Number(
                    data.correlations?.latitude_longitude ||
                    0
                ).toFixed(3)
            );


            setText(
                "corrXY",
                Number(
                    data.correlations?.x_y ||
                    0
                ).toFixed(3)
            );


            setText(
                "corrWardCommunity",
                Number(
                    data.correlations?.ward_community ||
                    0
                ).toFixed(3)
            );


            setText(
                "uc3Insight",
                data.insight ||
                "No statistical conclusion available."
            );


            drawUC3Charts(
                data
            );

            renderCorrelationMatrix(data);


            populateAnomalyTable(
                data.anomalies_list ||
                []
            );

        })

        .catch(error => {

            console.error(
                "UC3 error:",
                error
            );

        });

}

function renderCorrelationMatrix(data) {
    const target = document.getElementById("uc3CorrelationMatrix");
    if (!target || !data.correlation_labels) return;
    let html = "<table class='crime-table'><thead><tr><th></th>" + data.correlation_labels.map(x => `<th>${x}</th>`).join("") + "</tr></thead><tbody>";
    data.correlation_matrix.forEach((row, index) => {
        html += `<tr><th>${data.correlation_labels[index]}</th>` + row.map(value => `<td style='background:rgba(76,175,80,${Math.abs(value) * .55})'>${Number(value).toFixed(3)}</td>`).join("") + "</tr>";
    });
    target.innerHTML = html + "</tbody></table>";
}


function drawUC3Charts(data) {

    createChart(
        "uc3MonthlyChart",
        barChart(
            data.hour_labels,
            data.hour_values,
            "Crimes by hour"
        )
    );


    createChart(
        "uc3ConcentrationChart",
        doughnutChart(
            data.concentration_labels,
            data.concentration_values
        )
    );


    createChart(
        "uc3ArrestRateChart",
        barChart(
            data.arrest_rate_labels,
            data.arrest_rate_values,
            "Arrest Rate (%)"
        )
    );


    createChart(
        "uc3DistrictChart",
        barChart(
            data.district_labels,
            data.district_values,
            "Crimes"
        )
    );

}


function populateAnomalyTable(
    anomalies
) {

    const table =
        document.getElementById(
            "uc3AnomalyTable"
        );


    if (!table) {
        return;
    }


    if (
        !anomalies ||
        anomalies.length === 0
    ) {

        table.innerHTML =
            `<tr>
                <td colspan="4">
                    No statistical anomalies detected.
                </td>
            </tr>`;

        return;

    }


    table.innerHTML =
        anomalies.map(
            item => {

                return `
                    <tr>

                        <td>
                            ${item.category || "—"}
                        </td>

                        <td>
                            ${item.value ?? "—"}
                        </td>

                        <td>
                            ${item.expected_range || "—"}
                        </td>

                        <td>
                            ${item.status ||
                            "Potential Outlier"}
                        </td>

                    </tr>
                `;

            }
        ).join("");

}


/* =========================================================
   UC4 — STATS
========================================================= */

function loadUC4Stats() {

    getJSON("/api/uc4/stats")

        .then(data => {

            setText(
                "uc4Records",
                formatNumber(
                    data.total_records
                )
            );


            setText(
                "uc4CrimeTypes",
                formatNumber(
                    data.unique_crime_types
                )
            );

        })

        .catch(error => {

            console.error(
                "UC4 stats error:",
                error
            );

        });

}


/* =========================================================
   UC4 — REPORTS
========================================================= */

function loadUC4Report(
    reportType
) {

    const endpoint =
        `/api/uc4/report/${reportType}`;


    getJSON(endpoint)

        .then(data => {

            let targetId;


            if (
                reportType ===
                "top-crimes"
            ) {

                targetId =
                    "topCrimesReport";

            }

            else if (
                reportType ===
                "districts"
            ) {

                targetId =
                    "districtReport";

            }

            else if (
                reportType ===
                "years"
            ) {

                targetId =
                    "yearReport";

            }

            else if (
                reportType ===
                "arrests"
            ) {

                targetId =
                    "arrestReport";

            }


            renderReport(
                targetId,
                data
            );

        })

        .catch(error => {

            console.error(
                "UC4 report error:",
                error
            );

        });

}


function renderReport(
    targetId,
    data
) {

    const target =
        document.getElementById(
            targetId
        );


    if (!target) {
        return;
    }


    const rows =
        data.rows ||
        data;


    if (
        !Array.isArray(rows) ||
        rows.length === 0
    ) {

        target.innerHTML =
            "<p>No results found.</p>";

        return;

    }


    const columns =
        Object.keys(
            rows[0]
        );


    let html =
        `<table class="crime-table">
            <thead>
                <tr>`;


    columns.forEach(
        column => {

            html +=
                `<th>
                    ${column}
                </th>`;

        }
    );


    html +=
        `</tr>
        </thead>
        <tbody>`;


    rows.forEach(
        row => {

            html += "<tr>";


            columns.forEach(
                column => {

                    html +=
                        `<td>
                            ${row[column] ?? "—"}
                        </td>`;

                }
            );


            html += "</tr>";

        }
    );


    html +=
        `</tbody>
        </table>`;


    target.innerHTML =
        html;

}


/* =========================================================
   CHART CONFIGURATIONS
========================================================= */

function lineChart(
    labels,
    values,
    label
) {

    return {

        type: "line",

        data: {

            labels:
                labels || [],

            datasets: [

                {

                    label:
                        label,

                    data:
                        values || [],

                    borderWidth:
                        2,

                    fill:
                        false,

                    tension:
                        0.3

                }

            ]

        },

        options: {

            responsive:
                true,

            maintainAspectRatio:
                false,

            plugins: {

                legend: {

                    display:
                        true

                }

            },

            scales: {

                y: {

                    beginAtZero:
                        true

                }

            }

        }

    };

}


function barChart(
    labels,
    values,
    label
) {

    return {

        type: "bar",

        data: {

            labels:
                labels || [],

            datasets: [

                {

                    label:
                        label,

                    data:
                        values || [],

                    borderWidth:
                        1

                }

            ]

        },

        options: {

            responsive:
                true,

            maintainAspectRatio:
                false,

            scales: {

                y: {

                    beginAtZero:
                        true

                }

            }

        }

    };

}


function doughnutChart(
    labels,
    values
) {

    return {

        type: "doughnut",

        data: {

            labels:
                labels || [],

            datasets: [

                {

                    data:
                        values || [],

                    borderWidth:
                        1

                }

            ]

        },

        options: {

            responsive:
                true,

            maintainAspectRatio:
                false,

            plugins: {

                legend: {

                    position:
                        "bottom"

                }

            }

        }

    };

}


/* =========================================================
   PAGE INITIALIZATION
========================================================= */

document.addEventListener(
    "DOMContentLoaded",
    function () {

        const currentPath =
            window.location.pathname;


        console.log(
            "Current page:",
            currentPath
        );


        /* -----------------------------------------
           NAVIGATION
        ----------------------------------------- */

        document
            .querySelectorAll(
                ".nav-link"
            )
            .forEach(
                link => {

                    const href =
                        link.getAttribute(
                            "href"
                        );


                    if (
                        href &&
                        href !== "/" &&
                        currentPath === href
                    ) {

                        link.classList.add(
                            "active"
                        );

                    }

                }
            );


        /* -----------------------------------------
           MAIN DASHBOARD
        ----------------------------------------- */

        if (
            currentPath === "/" ||
            currentPath === ""
        ) {

            loadDashboardStats();

            loadDashboardYearlyChart();

            loadDashboardCrimeTypeChart();

            loadDashboardArrestChart();

            loadDashboardDistrictChart();

        }


        /* -----------------------------------------
           USE CASE 1
        ----------------------------------------- */

        if (
            currentPath ===
            "/usecase1"
        ) {

            loadUC1Data();

        }


        /* -----------------------------------------
           USE CASE 2
        ----------------------------------------- */

        if (
            currentPath ===
            "/usecase2"
        ) {

            loadUC2Summary();

        }


        /* -----------------------------------------
           USE CASE 3
        ----------------------------------------- */

        if (
            currentPath ===
            "/usecase3"
        ) {

            loadUC3Analysis();

        }


        /* -----------------------------------------
           USE CASE 4
        ----------------------------------------- */

        if (
            currentPath ===
            "/usecase4"
        ) {

            loadUC4Stats();
            loadUC4Report("top-crimes");
            loadUC4Report("years");
            loadUC4Report("arrests");
            loadUC4Report("districts");

        }


        /* -----------------------------------------
           CHART LIGHTBOX (click to expand)
        ----------------------------------------- */

        initChartLightbox();

    }
);


/* =========================================================
   CHART LIGHTBOX
========================================================= */

/* Data Management CRUD UI */
let crimeOffset = 0;
const crimeLimit = 25;
function loadDatabaseStats() { getJSON('/api/stats').then(d => { setText('databaseRecordCount', formatNumber(d.total_records)); setText('databaseCrimeTypes', formatNumber(d.unique_crime_types)); setText('databaseArrests', formatNumber(d.arrests)); setText('databaseDomestic', formatNumber(d.domestic_crimes)); }); }
function loadCrimeRecords() { const search = document.getElementById('crimeSearch').value.trim(); getJSON(`/api/crimes?limit=${crimeLimit}&offset=${crimeOffset}&search=${encodeURIComponent(search)}`).then(d => { const body=document.getElementById('crimeTableBody'); body.innerHTML=d.data.map(r=>`<tr><td>${r.id}</td><td>${r.case_number}</td><td>${r.date}</td><td>${r.primary_type}</td><td>${r.description}</td><td>${r.arrest ? 'Yes':'No'}</td><td>${r.district_code}</td><td><button class="secondary-button" onclick="editCrime(${r.id})">Edit</button> <button class="secondary-button" onclick="deleteCrime(${r.id})">Delete</button></td></tr>`).join('') || '<tr><td colspan="8">No records found.</td></tr>'; setText('pageInfo', `Page ${Math.floor(crimeOffset/crimeLimit)+1}`); document.getElementById('previousPage').disabled=crimeOffset===0; document.getElementById('nextPage').disabled=crimeOffset+crimeLimit>=d.total; }); }
function searchCrimes(){ crimeOffset=0; loadCrimeRecords(); }
function previousCrimePage(){ crimeOffset=Math.max(0,crimeOffset-crimeLimit); loadCrimeRecords(); }
function nextCrimePage(){ crimeOffset+=crimeLimit; loadCrimeRecords(); }
function openAddRecordModal(){ document.getElementById('recordForm').reset(); setText('recordMode','add'); document.getElementById('recordMode').value='add'; document.getElementById('recordModal').classList.add('open'); }
function closeRecordModal(){ document.getElementById('recordModal').classList.remove('open'); }
function editCrime(id){ getJSON(`/api/crimes/${id}`).then(r=>{ const fields={recordId:'id',caseNumber:'case_number',recordDate:'date',block:'block',iucrCode:'iucr_code',primaryType:'primary_type',description:'description',locationDesc:'location_desc',arrest:'arrest',domestic:'domestic',districtCode:'district_code',wardNo:'ward_no',communityCode:'community_code',fbiCode:'fbi_code',latitude:'latitude',longitude:'longitude'}; Object.entries(fields).forEach(([element,key])=>{ const node=document.getElementById(element); if(node && r[key]!==null) node.value=key==='date'?String(r[key]).replace(' ','T').slice(0,16):r[key]; }); document.getElementById('recordMode').value='edit'; document.getElementById('recordModal').classList.add('open'); }); }
function saveCrimeRecord(event){ event.preventDefault(); const value=id=>document.getElementById(id).value; const data={id:Number(value('recordId')),case_number:value('caseNumber'),date:value('recordDate').replace('T',' ')+':00',block:value('block')||'UNKNOWN',iucr_code:String(value('iucrCode')).padStart(4,'0'),primary_type:value('primaryType'),description:value('description')||'UNSPECIFIED',location_desc:value('locationDesc')||null,arrest:Number(value('arrest')),domestic:Number(value('domestic')),district_code:Number(value('districtCode')),ward_no:value('wardNo')?Number(value('wardNo')):null,community_code:value('communityCode')?Number(value('communityCode')):null,fbi_code:value('fbiCode')||'00',latitude:value('latitude')?Number(value('latitude')):null,longitude:value('longitude')?Number(value('longitude')):null,year:Number(value('recordDate').slice(0,4)),date_of_update:value('recordDate').replace('T',' ')+':00'}; const edit=document.getElementById('recordMode').value==='edit'; fetch(edit?`/api/crimes/${data.id}`:'/api/crimes',{method:edit?'PUT':'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(data)}).then(async r=>({ok:r.ok,body:await r.json()})).then(r=>{if(!r.ok) throw Error(r.body.error); closeRecordModal(); loadCrimeRecords(); loadDatabaseStats();}).catch(e=>setText('recordMessage',e.message)); }
function deleteCrime(id){ if(!confirm('Delete this record?')) return; fetch(`/api/crimes/${id}`,{method:'DELETE'}).then(r=>{if(!r.ok) throw Error('Delete failed'); loadCrimeRecords(); loadDatabaseStats();}).catch(e=>alert(e.message)); }
function uploadDataset(event){ event.preventDefault(); setText('uploadMessage','Dataset replacement is disabled to protect persisted records.'); }

function initChartLightbox() {

    const overlay =
        document.getElementById("chartLightbox");

    const lightboxImage =
        document.getElementById("lightboxImage");

    const lightboxTitle =
        document.getElementById("lightboxTitle");

    const closeButton =
        document.getElementById("lightboxClose");

    if (!overlay || !lightboxImage) {
        return;
    }


    function openLightbox(src, title) {

        lightboxImage.src = src;

        lightboxTitle.textContent = title || "";

        overlay.classList.add("open");

        document.body.style.overflow = "hidden";

    }


    function closeLightbox() {

        overlay.classList.remove("open");

        document.body.style.overflow = "";

        lightboxImage.src = "";

    }


    closeButton.addEventListener("click", closeLightbox);

    overlay.addEventListener("click", function (event) {

        if (event.target === overlay) {
            closeLightbox();
        }

    });

    document.addEventListener("keydown", function (event) {

        if (
            event.key === "Escape" &&
            overlay.classList.contains("open")
        ) {
            closeLightbox();
        }

    });


    /* Delegate clicks from any chart-container on the page,
       whether it holds a static <img> or a live Chart.js canvas. */

    document
        .querySelectorAll(".chart-container")
        .forEach(function (container) {

            container.classList.add("expandable");

            container.addEventListener("click", function () {

                const card =
                    container.closest(".chart-card");

                const titleEl =
                    card ? card.querySelector(".chart-header h2") : null;

                const title =
                    titleEl ? titleEl.textContent.trim() : "";

                const img =
                    container.querySelector("img");

                if (img && img.src) {
                    openLightbox(img.src, title);
                    return;
                }

                const canvas =
                    container.querySelector("canvas");

                if (canvas) {

                    const chartInstance =
                        charts[canvas.id];

                    if (chartInstance) {

                        openLightbox(
                            chartInstance.toBase64Image(),
                            title
                        );

                    }

                }

            });

        });

}

/* =========================================================
   SHARED SHELL: SIDEBAR AND THEME
========================================================= */
function initializeShellUX() {
    const body = document.body;
    const sidebarToggle = document.getElementById("sidebarToggle");
    const themeToggle = document.getElementById("themeToggle");
    const backdrop = document.getElementById("sidebarBackdrop");
    const mobile = window.matchMedia("(max-width: 850px)");
    const storageKey = "crimeLensTheme";

    function applyTheme(theme) {
        const dark = theme === "dark";
        body.classList.toggle("dark-theme", dark);
        themeToggle.setAttribute("aria-label", dark ? "Switch to light mode" : "Switch to dark mode");
        themeToggle.setAttribute("title", dark ? "Switch to light mode" : "Switch to dark mode");
        themeToggle.querySelector(".theme-label").textContent = dark ? "Light" : "Dark";
        themeToggle.querySelector(".theme-icon").textContent = dark ? "☀" : "◐";
        if (window.Chart) {
            Chart.defaults.color = dark ? "#d8dfec" : "#596273";
            Chart.defaults.borderColor = dark ? "#333d4f" : "#e5e7eb";
            Object.values(charts).forEach(chart => chart.update());
        }
    }
    applyTheme(localStorage.getItem(storageKey) || "light");

    function closeMobileDrawer() {
        body.classList.remove("sidebar-mobile-open");
        sidebarToggle.setAttribute("aria-expanded", "false");
        sidebarToggle.setAttribute("aria-label", "Open sidebar");
        sidebarToggle.setAttribute("title", "Open sidebar");
    }
    function toggleSidebar() {
        if (mobile.matches) {
            const open = body.classList.toggle("sidebar-mobile-open");
            sidebarToggle.setAttribute("aria-expanded", String(open));
            sidebarToggle.setAttribute("aria-label", open ? "Close sidebar" : "Open sidebar");
            sidebarToggle.setAttribute("title", open ? "Close sidebar" : "Open sidebar");
            return;
        }
        const collapsed = body.classList.toggle("sidebar-collapsed");
        sidebarToggle.setAttribute("aria-expanded", String(!collapsed));
        sidebarToggle.setAttribute("aria-label", collapsed ? "Expand sidebar" : "Collapse sidebar");
        sidebarToggle.setAttribute("title", collapsed ? "Expand sidebar" : "Collapse sidebar");
    }
    sidebarToggle.addEventListener("click", toggleSidebar);
    themeToggle.addEventListener("click", () => {
        const theme = body.classList.contains("dark-theme") ? "light" : "dark";
        localStorage.setItem(storageKey, theme);
        applyTheme(theme);
    });
    backdrop.addEventListener("click", closeMobileDrawer);
    document.querySelectorAll(".sidebar a").forEach(link => link.addEventListener("click", () => { if (mobile.matches) closeMobileDrawer(); }));
    mobile.addEventListener("change", () => { body.classList.remove("sidebar-mobile-open"); });
}

document.addEventListener("DOMContentLoaded", initializeShellUX);

