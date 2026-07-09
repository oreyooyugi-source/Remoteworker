/* =========================================================================
   Remote Worker Tracker — Chart.js helpers
   Renders charts from JSON embedded in the page.
   ========================================================================= */
(function () {
    "use strict";

    function themeColors() {
        const styles = getComputedStyle(document.documentElement);
        return {
            primary: styles.getPropertyValue("--rwt-primary").trim() || "#2563eb",
            accent: styles.getPropertyValue("--rwt-accent").trim() || "#7c3aed",
            success: styles.getPropertyValue("--rwt-success").trim() || "#16a34a",
            warning: styles.getPropertyValue("--rwt-warning").trim() || "#d97706",
            danger: styles.getPropertyValue("--rwt-danger").trim() || "#dc2626",
            info: styles.getPropertyValue("--rwt-info").trim() || "#0891b2",
            grid: styles.getPropertyValue("--border-color").trim() || "#e2e8f0",
            text: styles.getPropertyValue("--text-secondary").trim() || "#64748b",
        };
    }

    function baseOptions(colors) {
        return {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { labels: { color: colors.text, usePointStyle: true, padding: 16 } },
            },
            scales: {
                x: { grid: { color: colors.grid }, ticks: { color: colors.text } },
                y: { grid: { color: colors.grid }, ticks: { color: colors.text }, beginAtZero: true },
            },
        };
    }

    function readJSON(id) {
        const el = document.getElementById(id);
        if (!el) return null;
        try { return JSON.parse(el.textContent); } catch (e) { return null; }
    }

    function makeGradient(ctx, color) {
        const gradient = ctx.createLinearGradient(0, 0, 0, 240);
        gradient.addColorStop(0, color + "55");
        gradient.addColorStop(1, color + "05");
        return gradient;
    }

    window.RWTCharts = {
        line: function (canvasId, labels, datasets) {
            const canvas = document.getElementById(canvasId);
            if (!canvas || typeof Chart === "undefined") return;
            const colors = themeColors();
            const ctx = canvas.getContext("2d");
            new Chart(ctx, {
                type: "line",
                data: {
                    labels: labels,
                    datasets: datasets.map(function (ds) {
                        return Object.assign({
                            tension: 0.4,
                            fill: true,
                            borderWidth: 2,
                            pointRadius: 3,
                            backgroundColor: makeGradient(ctx, ds.color || colors.primary),
                            borderColor: ds.color || colors.primary,
                        }, ds);
                    }),
                },
                options: baseOptions(colors),
            });
        },

        bar: function (canvasId, labels, data, color) {
            const canvas = document.getElementById(canvasId);
            if (!canvas || typeof Chart === "undefined") return;
            const colors = themeColors();
            new Chart(canvas.getContext("2d"), {
                type: "bar",
                data: {
                    labels: labels,
                    datasets: [{
                        data: data,
                        backgroundColor: color || colors.primary,
                        borderRadius: 6,
                        maxBarThickness: 42,
                    }],
                },
                options: Object.assign(baseOptions(colors), {
                    plugins: { legend: { display: false } },
                }),
            });
        },

        doughnut: function (canvasId, labels, data, palette) {
            const canvas = document.getElementById(canvasId);
            if (!canvas || typeof Chart === "undefined") return;
            const colors = themeColors();
            const defaultPalette = [
                colors.primary, colors.success, colors.warning,
                colors.danger, colors.info, colors.accent,
            ];
            new Chart(canvas.getContext("2d"), {
                type: "doughnut",
                data: {
                    labels: labels,
                    datasets: [{
                        data: data,
                        backgroundColor: palette || defaultPalette,
                        borderWidth: 0,
                    }],
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    cutout: "68%",
                    plugins: { legend: { position: "bottom", labels: { color: colors.text, usePointStyle: true, padding: 14 } } },
                },
            });
        },
    };

    document.addEventListener("DOMContentLoaded", function () {
        const colors = themeColors();

        // Dashboard attendance trend
        const dash = readJSON("dashboard-charts");
        if (dash && dash.attendance_trend) {
            window.RWTCharts.line("attendanceTrendChart", dash.attendance_trend.labels, [
                { label: "Present", data: dash.attendance_trend.present, color: colors.primary },
            ]);
        }

        // Generic analytics charts
        const analytics = readJSON("analytics-charts");
        if (analytics) {
            if (analytics.headcount_by_department) {
                window.RWTCharts.doughnut(
                    "headcountChart",
                    analytics.headcount_by_department.labels,
                    analytics.headcount_by_department.data,
                    analytics.headcount_by_department.colors
                );
            }
            if (analytics.productivity_distribution) {
                window.RWTCharts.doughnut(
                    "prodDistChart",
                    analytics.productivity_distribution.labels,
                    analytics.productivity_distribution.data
                );
            }
            if (analytics.attendance_trend) {
                window.RWTCharts.line("attendanceChart", analytics.attendance_trend.labels, [
                    { label: "Present", data: analytics.attendance_trend.present, color: colors.success },
                    { label: "Absent", data: analytics.attendance_trend.absent, color: colors.danger },
                ]);
            }
            if (analytics.department_productivity) {
                window.RWTCharts.bar(
                    "deptProdChart",
                    analytics.department_productivity.labels,
                    analytics.department_productivity.data,
                    colors.accent
                );
            }
            if (analytics.hours_trend) {
                window.RWTCharts.line("hoursTrendChart", analytics.hours_trend.labels, [
                    { label: "Hours", data: analytics.hours_trend.hours, color: colors.info },
                ]);
            }
            if (analytics.forecast) {
                window.RWTCharts.line("forecastChart", analytics.forecast.labels, [
                    { label: "Forecast", data: analytics.forecast.forecast, color: colors.warning, borderDash: [6, 4] },
                ]);
            }
        }

        // Productivity trend (employee)
        const prod = readJSON("productivity-trend");
        if (prod) {
            window.RWTCharts.line("productivityTrendChart", prod.labels, [
                { label: "Productivity %", data: prod.scores, color: colors.primary },
            ]);
        }

        // Time tracking weekly
        const week = readJSON("weekly-hours");
        if (week) {
            window.RWTCharts.bar("weeklyHoursChart", Object.keys(week), Object.values(week), colors.primary);
        }
    });
})();
