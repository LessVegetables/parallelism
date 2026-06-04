import csv
import matplotlib.pyplot as plt
import numpy as np

# ── Read CSV ──────────────────────────────────────────────────────────────────
data = {}  # data[size][variant][threads] = (time, speedup)
with open("results_jacobi.csv") as f:
    reader = csv.DictReader(f)
    for row in reader:
        sz  = int(row["size"])
        var = row["variant"]
        p   = int(row["threads"])
        sp  = float(row["speedup"])
        data.setdefault(sz, {}).setdefault(var, {})[p] = sp

sizes         = sorted(data.keys())
variants      = ["v1", "v2"]
thread_counts = [1, 2, 3, 4, 5, 6, 7, 8, 16, 20, 40]

# ── Compute P_eff(p) = S(p)² / p ─────────────────────────────────────────────
size_colors    = ["#2c7bb6", "#d7191c", "#1a9641", "#f57f20"]
variant_styles = {"v1": "-",  "v2": "--"}
variant_markers= {"v1": "o",  "v2": "s"}

fig, ax = plt.subplots(figsize=(11, 6))
fig.patch.set_facecolor("#f7f9fc")
ax.set_facecolor("#ffffff")

for idx, sz in enumerate(sizes):
    for var in variants:
        if var not in data[sz]:
            continue
        xs, ys = [], []
        for p in thread_counts:
            sp = data[sz][var].get(p)
            if sp is not None:
                xs.append(p)
                ys.append(sp**2 / p)   # P_eff = S² / p
        ax.plot(
            xs, ys,
            color=size_colors[idx % len(size_colors)],
            linestyle=variant_styles[var],
            marker=variant_markers[var],
            linewidth=2, markersize=7,
            label=f"N={sz:,} {var}",
        )

ax.set_xlabel("Number of threads (p)", fontsize=11)
ax.set_ylabel("P_eff = S(p)² / p", fontsize=11)
ax.set_title("Effective Performance  P_eff(p) = S(p)² / p\n",
             fontsize=12, fontweight="bold", color="#1a2e45")
ax.set_xticks(thread_counts)
ax.legend(fontsize=9, ncol=2)
ax.grid(True, linestyle="--", alpha=0.5)
ax.set_xlim(0, max(thread_counts) + 2)
ax.set_ylim(0)

plt.tight_layout(pad=2.0)
plt.savefig("task1_effectiveness.png", dpi=150, bbox_inches="tight",
            facecolor=fig.get_facecolor())
print("Saved task1_effectiveness.png")
plt.show()