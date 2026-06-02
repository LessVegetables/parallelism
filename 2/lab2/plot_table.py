import csv
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

# ── Read results.csv ──────────────────────────────────────────────────────────
data = {}   # data[size][variant][threads] = (time, speedup)
with open("results_jacobi.csv") as f:
    reader = csv.DictReader(f)
    for row in reader:
        sz  = int(row["size"])
        var = row["variant"]
        p   = int(row["threads"])
        t   = float(row["time"])
        sp  = float(row["speedup"])
        data.setdefault(sz, {}).setdefault(var, {})[p] = (t, sp)

sizes         = sorted(data.keys())
variants      = ["serial", "v1", "v2"]
thread_counts = [1, 2, 4, 7, 8, 16, 20, 40]

# ── Build cell values ─────────────────────────────────────────────────────────
# columns: size | variant | T1 | T2 S2 | T4 S4 | ...
col_labels = ["M = N", "Variant", "T₁ (s)"]
for p in thread_counts[1:]:
    col_labels += [f"T{p} (s)", f"S{p}"]

rows = []
for sz in sizes:
    for var in variants:
        if var not in data[sz]:
            continue
        var_data = data[sz][var]
        t1 = var_data.get(1, (None,))[0]
        t1_str = f"{t1:.3f}" if t1 is not None else "—"
        row = [f"{sz:,}", var, t1_str]
        for p in thread_counts[1:]:
            if p in var_data:
                tp, sp = var_data[p]
                row += [f"{tp:.3f}", f"{sp:.2f}"]
            else:
                row += ["—", "—"]
        rows.append((sz, var, row))

# ── Figure layout ─────────────────────────────────────────────────────────────
fig, (ax_table, ax_chart) = plt.subplots(
    2, 1,
    figsize=(18, 10),
    gridspec_kw={"height_ratios": [1, 2]},
)
fig.patch.set_facecolor("#f7f9fc")

# ── TABLE ─────────────────────────────────────────────────────────────────────
ax_table.axis("off")

n_cols = len(col_labels)
band_colors = ["#dce8f5", "#fef3dc", "#dff2e1", "#fde8e8",
               "#ede8fd", "#fde8f5", "#e8fdf5"]

# Colour by variant within each size group
variant_colors = {"serial": "#e8f0fb", "v1": "#dff2e1", "v2": "#fde8e8"}

cell_colors = []
table_rows  = []
for sz, var, row in rows:
    base = variant_colors.get(var, "#ffffff")
    row_colors = ["#c6d9f1", base, base]   # size col, variant col, T1 col
    for i in range(len(thread_counts) - 1):
        bc = band_colors[i % len(band_colors)]
        # Slightly tint the band color toward the variant color
        row_colors += [base, base]
    cell_colors.append(row_colors)
    table_rows.append(row)

tbl = ax_table.table(
    cellText=table_rows,
    colLabels=col_labels,
    cellLoc="center",
    loc="center",
    cellColours=cell_colors,
)
tbl.auto_set_font_size(False)
tbl.set_fontsize(9.5)
tbl.scale(1, 2.0)

for j in range(n_cols):
    cell = tbl[0, j]
    cell.set_facecolor("#2c5f8a")
    cell.set_text_props(color="white", fontweight="bold")

ax_table.set_title(
    "Scalability Analysis — Matrix-Matrix Product (OpenMP)",
    fontsize=14, fontweight="bold", pad=12, color="#1a2e45"
)

# ── SPEEDUP CHART ─────────────────────────────────────────────────────────────
ax_chart.set_facecolor("#ffffff")
ax_chart.set_title("Speedup Sₚ vs Number of Threads", fontsize=12,
                   fontweight="bold", color="#1a2e45")

# One colour per size, one linestyle per variant
size_colors   = ["#2c7bb6", "#d7191c", "#1a9641", "#f57f20"]
variant_styles = {"v1": "-", "v2": "--"}
variant_markers = {"v1": "o", "v2": "s"}

x_max = max(thread_counts) + 2
x_ideal = np.array([1, x_max])
ax_chart.plot(x_ideal, x_ideal, "k--", linewidth=1.2, label="Linear (ideal)", zorder=1)

for idx, sz in enumerate(sizes):
    for var in ["v1", "v2"]:
        if var not in data[sz]:
            continue
        var_data = data[sz][var]
        xs, ys = [], []
        for p in thread_counts:
            if p in var_data:
                xs.append(p)
                ys.append(var_data[p][1])
        ax_chart.plot(
            xs, ys,
            color=size_colors[idx % len(size_colors)],
            linestyle=variant_styles[var],
            marker=variant_markers[var],
            linewidth=2, markersize=7,
            label=f"N={sz:,} {var}",
            zorder=2,
        )

ax_chart.set_xlabel("Number of threads (p)", fontsize=11)
ax_chart.set_ylabel("Speedup Sₚ", fontsize=11)
ax_chart.set_xticks(thread_counts)
ax_chart.legend(fontsize=9, ncol=2)
ax_chart.grid(True, linestyle="--", alpha=0.5)
ax_chart.set_xlim(0, x_max)
ax_chart.set_ylim(0)

plt.tight_layout(pad=2.0)
plt.savefig("task1_results.png", dpi=150, bbox_inches="tight",
            facecolor=fig.get_facecolor())
print("Saved task1_results.png")
plt.show()