import csv
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

# ── Read results.csv ──────────────────────────────────────────────────────────
data = {}   # data[size][threads] = (time, speedup)
with open("results.csv") as f:
    reader = csv.DictReader(f)
    for row in reader:
        sz = int(row["size"])
        p  = int(row["threads"])
        t  = float(row["time"])
        sp = float(row["speedup"])
        data.setdefault(sz, {})[p] = (t, sp)

sizes        = sorted(data.keys())
thread_counts = [1, 2, 3, 4, 5, 6, 7, 8, 16, 20, 40]

# ── Build cell values ─────────────────────────────────────────────────────────
#   columns: T1 | T2 S2 | T4 S4 | T7 S7 | T8 S8 | T16 S16 | T20 S20 | T40 S40
col_labels = ["M = N", "T₁ (s)"]
for p in thread_counts[1:]:
    col_labels += [f"T{p} (s)", f"S{p}"]

rows = []
for sz in sizes:
    row_data = data[sz]
    t1 = row_data[1][0]
    row = [f"{sz:,}", f"{t1:.3f}"]
    for p in thread_counts[1:]:
        if p in row_data:
            tp, sp = row_data[p]
            row += [f"{tp:.3f}", f"{sp:.2f}"]
        else:
            row += ["—", "—"]
    rows.append(row)

# ── Figure layout ─────────────────────────────────────────────────────────────
fig, (ax_table, ax_chart) = plt.subplots(
    2, 1,
    figsize=(18, 10),
    gridspec_kw={"height_ratios": [1, 2]},
)
fig.patch.set_facecolor("#f7f9fc")

# ── TABLE ─────────────────────────────────────────────────────────────────────
ax_table.axis("off")

# Colour bands: one shade per thread-group (pairs of columns after T1)
n_cols = len(col_labels)
cell_colors = []
band_colors = ["#dce8f5", "#fef3dc", "#dff2e1", "#fde8e8",
               "#ede8fd", "#fde8f5", "#e8fdf5"]

for row in rows:
    row_colors = ["#c6d9f1", "#e8f0fb"]   # M=N col, T1 col
    for i, p in enumerate(thread_counts[1:]):
        bc = band_colors[i % len(band_colors)]
        row_colors += [bc, bc]
    cell_colors.append(row_colors)

header_colors = [["#2c5f8a"] * n_cols]

tbl = ax_table.table(
    cellText=rows,
    colLabels=col_labels,
    cellLoc="center",
    loc="center",
    cellColours=cell_colors,
)
tbl.auto_set_font_size(False)
tbl.set_fontsize(9.5)
tbl.scale(1, 2.0)

# Style header
for j in range(n_cols):
    cell = tbl[0, j]
    cell.set_facecolor("#2c5f8a")
    cell.set_text_props(color="white", fontweight="bold")

ax_table.set_title(
    "Scalability Analysis — Matrix-Vector Product (OpenMP)",
    fontsize=14, fontweight="bold", pad=12, color="#1a2e45"
)

# ── SPEEDUP CHART ─────────────────────────────────────────────────────────────
ax_chart.set_facecolor("#ffffff")
ax_chart.set_title("Speedup Sₚ vs Number of Threads", fontsize=12,
                   fontweight="bold", color="#1a2e45")

colors = ["#2c7bb6", "#d7191c"]
markers = ["o", "s"]
x_max = 8

# Ideal linear speedup
x_ideal = np.array([1, x_max])
ax_chart.plot(x_ideal, x_ideal, "k--", linewidth=1.2, label="Linear (ideal)", zorder=1)

for idx, sz in enumerate(sizes):
    row_data = data[sz]
    xs, ys = [], []
    for p in thread_counts:
        if p in row_data:
            xs.append(p)
            ys.append(row_data[p][1])
    ax_chart.plot(xs, ys, color=colors[idx], marker=markers[idx],
                  linewidth=2, markersize=7, label=f"M = N = {sz:,}", zorder=2)

ax_chart.set_xlabel("Number of threads (p)", fontsize=11)
ax_chart.set_ylabel("Speedup Sₚ", fontsize=11)
ax_chart.set_xticks(thread_counts)
ax_chart.legend(fontsize=10)
ax_chart.grid(True, linestyle="--", alpha=0.5)
ax_chart.set_xlim(0, x_max)
ax_chart.set_ylim(0)

plt.tight_layout(pad=2.0)
plt.savefig("task2_results.png", dpi=150, bbox_inches="tight",
            facecolor=fig.get_facecolor())
print("Saved → task2_results.png")
# plt.show()