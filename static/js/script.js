/* ============================================================
   UkayEase — Client-side scripts
   ============================================================ */

document.addEventListener("DOMContentLoaded", () => {
    // Mobile sidebar toggle
    const menuToggle = document.getElementById("menuToggle");
    const sidebar = document.getElementById("sidebar");
    if (menuToggle && sidebar) {
        menuToggle.addEventListener("click", () => {
            sidebar.classList.toggle("open");
        });
        // Close sidebar when clicking outside on mobile
        document.addEventListener("click", (e) => {
            if (
                sidebar.classList.contains("open") &&
                !sidebar.contains(e.target) &&
                !menuToggle.contains(e.target)
            ) {
                sidebar.classList.remove("open");
            }
        });
    }

    // Auto-dismiss flash messages after 5 seconds
    document.querySelectorAll(".flash").forEach((el) => {
        setTimeout(() => {
            el.style.transition = "opacity 0.4s, transform 0.4s";
            el.style.opacity = "0";
            el.style.transform = "translateY(-8px)";
            setTimeout(() => el.remove(), 400);
        }, 5000);
    });

    // Sales form: real-time price & total calculation
    initSalesCalculator();

    // Client-side product table search (instant filter on top of server search)
    initProductSearch();
});

/* ---------- Sales calculator ---------- */

function initSalesCalculator() {
    const productSelect = document.getElementById("product_id");
    const qtyInput = document.getElementById("quantity");
    const unitDisplay = document.getElementById("unit_price_display");
    const totalDisplay = document.getElementById("total_display");

    if (!productSelect || !qtyInput) return;

    function updateTotals() {
        const opt = productSelect.selectedOptions[0];
        const price = opt && opt.dataset.price ? parseFloat(opt.dataset.price) : 0;
        const maxQty = opt && opt.dataset.qty ? parseInt(opt.dataset.qty, 10) : 1;
        let qty = parseInt(qtyInput.value, 10) || 0;

        // Clamp quantity to available stock
        qtyInput.max = maxQty;
        if (qty > maxQty) {
            qty = maxQty;
            qtyInput.value = maxQty;
        }
        if (qty < 1 && productSelect.value) {
            qty = 1;
            qtyInput.value = 1;
        }

        unitDisplay.value = "₱" + price.toLocaleString("en-PH", {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2,
        });
        totalDisplay.value = "₱" + (price * qty).toLocaleString("en-PH", {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2,
        });
    }

    productSelect.addEventListener("change", updateTotals);
    qtyInput.addEventListener("input", updateTotals);
    updateTotals();
}

/* ---------- Product search (client-side enhancement) ---------- */

function initProductSearch() {
    const searchInput = document.getElementById("searchInput");
    const table = document.getElementById("productsTable");
    if (!searchInput || !table) return;

    // Live filter as user types (works on already-loaded rows)
    searchInput.addEventListener("input", () => {
        const term = searchInput.value.toLowerCase().trim();
        const rows = table.querySelectorAll("tbody tr");
        rows.forEach((row) => {
            if (row.querySelector(".empty")) return;
            const text = row.textContent.toLowerCase();
            row.style.display = text.includes(term) ? "" : "none";
        });
    });
}

/* ---------- Delete confirmation modal ---------- */

function confirmDelete(btn) {
    const id = btn.dataset.id;
    const name = btn.dataset.name;
    const modal = document.getElementById("deleteModal");
    const form = document.getElementById("deleteForm");
    const nameEl = document.getElementById("deleteName");

    if (!modal || !form) return;

    nameEl.textContent = name;
    form.action = "/delete-product/" + id;
    modal.hidden = false;
}

function closeDeleteModal() {
    const modal = document.getElementById("deleteModal");
    if (modal) modal.hidden = true;
}

// Close modal on overlay click
document.addEventListener("click", (e) => {
    const modal = document.getElementById("deleteModal");
    if (modal && e.target === modal) {
        closeDeleteModal();
    }
});

/* ---------- Chart.js renderer for reports ---------- */

function renderSalesChart(labels, values) {
    const canvas = document.getElementById("salesChart");
    if (!canvas || typeof Chart === "undefined") return;

    new Chart(canvas, {
        type: "bar",
        data: {
            labels: labels,
            datasets: [
                {
                    label: "Daily Revenue (₱)",
                    data: values,
                    backgroundColor: "rgba(140, 88, 53, 0.75)",
                    borderColor: "#6b4226",
                    borderWidth: 1,
                    borderRadius: 6,
                    maxBarThickness: 48,
                },
            ],
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false,
                },
                tooltip: {
                    callbacks: {
                        label: (ctx) =>
                            "₱" +
                            ctx.parsed.y.toLocaleString("en-PH", {
                                minimumFractionDigits: 2,
                            }),
                    },
                },
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        callback: (v) => "₱" + v.toLocaleString(),
                    },
                    grid: {
                        color: "rgba(224, 213, 197, 0.5)",
                    },
                },
                x: {
                    grid: {
                        display: false,
                    },
                },
            },
        },
    });
}
