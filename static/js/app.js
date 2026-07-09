/* =========================================================================
   Remote Worker Tracker — Application JavaScript
   Theme toggle, sidebar, toasts, kanban drag/drop, timers and polling.
   ========================================================================= */
(function () {
    "use strict";

    /* ---- CSRF helper --------------------------------------------------- */
    function getCookie(name) {
        const value = `; ${document.cookie}`;
        const parts = value.split(`; ${name}=`);
        if (parts.length === 2) return parts.pop().split(";").shift();
        return null;
    }
    const CSRF_TOKEN = getCookie("csrftoken");
    window.RWT = window.RWT || {};
    window.RWT.csrf = CSRF_TOKEN;

    function postData(url, data) {
        return fetch(url, {
            method: "POST",
            headers: {
                "X-CSRFToken": CSRF_TOKEN,
                "X-Requested-With": "XMLHttpRequest",
                "Content-Type": data instanceof FormData ? undefined : "application/json",
            },
            body: data instanceof FormData ? data : JSON.stringify(data),
        });
    }
    window.RWT.postData = postData;

    /* ---- Theme --------------------------------------------------------- */
    function applyTheme(theme) {
        document.documentElement.setAttribute("data-theme", theme);
        localStorage.setItem("rwt-theme", theme);
        const icon = document.querySelector("#theme-toggle i");
        if (icon) {
            icon.className = theme === "dark" ? "fa-solid fa-sun" : "fa-solid fa-moon";
        }
    }

    function initTheme() {
        const stored = localStorage.getItem("rwt-theme")
            || document.documentElement.getAttribute("data-theme")
            || "light";
        applyTheme(stored);

        const toggle = document.getElementById("theme-toggle");
        if (toggle) {
            toggle.addEventListener("click", function () {
                const current = document.documentElement.getAttribute("data-theme");
                const next = current === "dark" ? "light" : "dark";
                applyTheme(next);
                const url = toggle.dataset.url;
                if (url) {
                    const fd = new FormData();
                    fd.append("theme", next);
                    postData(url, fd).catch(function () {});
                }
            });
        }
    }

    /* ---- Sidebar ------------------------------------------------------- */
    function initSidebar() {
        const shell = document.getElementById("app-shell");
        const collapseBtn = document.getElementById("sidebar-collapse");
        const mobileBtn = document.getElementById("sidebar-mobile-toggle");

        if (localStorage.getItem("rwt-sidebar") === "collapsed" && shell) {
            shell.classList.add("sidebar-collapsed");
        }

        if (collapseBtn && shell) {
            collapseBtn.addEventListener("click", function () {
                shell.classList.toggle("sidebar-collapsed");
                const collapsed = shell.classList.contains("sidebar-collapsed");
                localStorage.setItem("rwt-sidebar", collapsed ? "collapsed" : "expanded");
                const url = collapseBtn.dataset.url;
                if (url) {
                    const fd = new FormData();
                    fd.append("collapsed", collapsed);
                    postData(url, fd).catch(function () {});
                }
            });
        }

        if (mobileBtn && shell) {
            mobileBtn.addEventListener("click", function () {
                shell.classList.toggle("sidebar-open");
            });
        }
    }

    /* ---- Toasts -------------------------------------------------------- */
    function showToast(message, type) {
        type = type || "info";
        let container = document.querySelector(".toast-container");
        if (!container) {
            container = document.createElement("div");
            container.className = "toast-container position-fixed top-0 end-0 p-3";
            document.body.appendChild(container);
        }
        const toast = document.createElement("div");
        toast.className = `toast align-items-center text-bg-${type} border-0 show`;
        toast.setAttribute("role", "alert");
        toast.innerHTML =
            '<div class="d-flex">' +
            `<div class="toast-body">${message}</div>` +
            '<button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>' +
            "</div>";
        container.appendChild(toast);
        setTimeout(function () { toast.remove(); }, 4500);
    }
    window.RWT.showToast = showToast;

    /* ---- Auto-dismiss server messages ---------------------------------- */
    function initAlerts() {
        document.querySelectorAll(".alert-dismissible").forEach(function (alert) {
            setTimeout(function () {
                alert.classList.add("fade");
                setTimeout(function () { alert.remove(); }, 300);
            }, 5000);
        });
    }

    /* ---- Confirm dialogs ----------------------------------------------- */
    function initConfirm() {
        document.querySelectorAll("[data-confirm]").forEach(function (el) {
            el.addEventListener("click", function (e) {
                if (!window.confirm(el.dataset.confirm)) {
                    e.preventDefault();
                    e.stopPropagation();
                }
            });
        });
    }

    /* ---- Live clock ---------------------------------------------------- */
    function initClock() {
        const el = document.getElementById("live-clock");
        if (!el) return;
        function tick() {
            const now = new Date();
            el.textContent = now.toLocaleTimeString();
        }
        tick();
        setInterval(tick, 1000);
    }

    /* ---- Attendance clock widget --------------------------------------- */
    function initClockWidget() {
        const widget = document.getElementById("clock-widget");
        if (!widget) return;
        const url = widget.dataset.url;
        const elapsedEl = document.getElementById("clock-elapsed");
        let startTime = widget.dataset.start ? new Date(widget.dataset.start) : null;

        function updateElapsed() {
            if (!startTime || !elapsedEl) return;
            const diff = Math.floor((Date.now() - startTime.getTime()) / 1000);
            const h = String(Math.floor(diff / 3600)).padStart(2, "0");
            const m = String(Math.floor((diff % 3600) / 60)).padStart(2, "0");
            const s = String(diff % 60).padStart(2, "0");
            elapsedEl.textContent = `${h}:${m}:${s}`;
        }
        if (startTime) setInterval(updateElapsed, 1000);

        widget.querySelectorAll("[data-action]").forEach(function (btn) {
            btn.addEventListener("click", function () {
                const fd = new FormData();
                fd.append("action", btn.dataset.action);
                postData(url, fd)
                    .then(function (r) { return r.json(); })
                    .then(function (data) {
                        showToast(data.message || "Updated", "success");
                        setTimeout(function () { window.location.reload(); }, 600);
                    })
                    .catch(function () { showToast("Something went wrong", "danger"); });
            });
        });
    }

    /* ---- Time tracking timer ------------------------------------------- */
    function initTimer() {
        const timer = document.getElementById("timer-widget");
        if (!timer) return;
        const url = timer.dataset.url;
        const display = document.getElementById("timer-display");
        let start = timer.dataset.start ? new Date(timer.dataset.start) : null;
        let interval = null;

        function render() {
            if (!start || !display) return;
            const diff = Math.floor((Date.now() - start.getTime()) / 1000);
            const h = String(Math.floor(diff / 3600)).padStart(2, "0");
            const m = String(Math.floor((diff % 3600) / 60)).padStart(2, "0");
            const s = String(diff % 60).padStart(2, "0");
            display.textContent = `${h}:${m}:${s}`;
        }
        if (start) { render(); interval = setInterval(render, 1000); }

        const startBtn = document.getElementById("timer-start");
        const stopBtn = document.getElementById("timer-stop");
        if (startBtn) {
            startBtn.addEventListener("click", function () {
                const fd = new FormData();
                fd.append("action", "start");
                const desc = document.getElementById("timer-description");
                if (desc) fd.append("description", desc.value);
                postData(url, fd).then(function () { window.location.reload(); });
            });
        }
        if (stopBtn) {
            stopBtn.addEventListener("click", function () {
                const fd = new FormData();
                fd.append("action", "stop");
                postData(url, fd).then(function () {
                    if (interval) clearInterval(interval);
                    window.location.reload();
                });
            });
        }
    }

    /* ---- Kanban drag & drop -------------------------------------------- */
    function initKanban() {
        const board = document.getElementById("kanban-board");
        if (!board) return;
        const moveUrl = board.dataset.moveUrl;
        let dragged = null;

        board.querySelectorAll(".kanban-card").forEach(function (card) {
            card.setAttribute("draggable", "true");
            card.addEventListener("dragstart", function () {
                dragged = card;
                card.classList.add("dragging");
            });
            card.addEventListener("dragend", function () {
                card.classList.remove("dragging");
            });
        });

        board.querySelectorAll(".kanban-cards").forEach(function (zone) {
            zone.addEventListener("dragover", function (e) {
                e.preventDefault();
                zone.classList.add("drag-over");
            });
            zone.addEventListener("dragleave", function () {
                zone.classList.remove("drag-over");
            });
            zone.addEventListener("drop", function (e) {
                e.preventDefault();
                zone.classList.remove("drag-over");
                if (!dragged) return;
                zone.appendChild(dragged);
                const status = zone.dataset.status;
                const order = Array.from(zone.children).indexOf(dragged);
                postData(moveUrl, {
                    task_id: dragged.dataset.taskId,
                    status: status,
                    order: order,
                }).then(function () {
                    showToast("Task moved", "success");
                    updateCounts();
                });
            });
        });

        function updateCounts() {
            board.querySelectorAll(".kanban-column").forEach(function (col) {
                const count = col.querySelectorAll(".kanban-card").length;
                const badge = col.querySelector(".column-count");
                if (badge) badge.textContent = count;
            });
        }
    }

    /* ---- Notification polling ------------------------------------------ */
    function initNotifications() {
        const bell = document.getElementById("notif-dropdown");
        if (!bell) return;
        const url = bell.dataset.url;
        const markAllUrl = bell.dataset.markAllUrl;

        const markAll = document.getElementById("mark-all-read");
        if (markAll && markAllUrl) {
            markAll.addEventListener("click", function (e) {
                e.preventDefault();
                postData(markAllUrl, {}).then(function () {
                    const dot = document.querySelector("#notif-btn .notif-dot");
                    if (dot) dot.remove();
                    showToast("All notifications marked as read", "success");
                });
            });
        }
    }

    /* ---- Init ---------------------------------------------------------- */
    document.addEventListener("DOMContentLoaded", function () {
        initTheme();
        initSidebar();
        initAlerts();
        initConfirm();
        initClock();
        initClockWidget();
        initTimer();
        initKanban();
        initNotifications();
    });
})();
