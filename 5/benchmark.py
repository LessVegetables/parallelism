"""
Benchmark main.py (offline video mode) across several thread counts and plot
the classic speedup / efficiency graphs.

    python benchmark.py --input test.mp4
    python benchmark.py --input test.mp4 --threads 1,2,4,8,16
    python benchmark.py --input test.mp4 --output-dir benchmark_results

For every thread count it runs `main.py --input <video> --threads N` as a fresh
subprocess (clean interpreter, no warm caches between runs), parses the printed
`Time elapsed:` value, then computes speedup and parallel efficiency relative to
the smallest thread count tested.
"""

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

import matplotlib.pyplot as plt


# ---------------------------------------------------------------------------
# Running a single configuration
# ---------------------------------------------------------------------------

def run_once(video_path: str, num_threads: int, output_dir: Path) -> float | None:
    """Run main.py with `num_threads` workers; return inference time in seconds."""
    out_file = output_dir / f"output_threads_{num_threads}.mp4"
    cmd = [
        sys.executable, "main.py",
        "--input", video_path,
        "--threads", str(num_threads),
        "--save", str(out_file),
    ]

    print(f"\n[*] Running with {num_threads} thread(s)...")
    print(f"    {' '.join(cmd)}")

    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
    except subprocess.TimeoutExpired:
        print("[!] Timed out after 600 s")
        return None

    if proc.returncode != 0:
        print(f"[!] Failed (exit {proc.returncode}):\n{proc.stderr}")
        return None

    # Parse "Time elapsed: <sec> seconds" printed by main.py
    for line in proc.stdout.splitlines():
        if "Time elapsed:" in line:
            return float(line.split(":")[-1].strip().split()[0])

    print("[!] Could not find 'Time elapsed:' in output")
    return None


# ---------------------------------------------------------------------------
# Analysis
# ---------------------------------------------------------------------------

def analyze(results: dict[int, float]) -> dict:
    """Compute speedup and efficiency relative to the smallest thread count."""
    baseline_threads = min(results)
    baseline_time = results[baseline_threads]

    analysis = {}
    print("\n" + "=" * 56)
    print(f"{'Threads':<10}{'Time (s)':<12}{'Speedup':<12}{'Efficiency':<12}")
    print("-" * 56)

    best_threads, best_speedup = baseline_threads, 1.0
    for n in sorted(results):
        t = results[n]
        speedup = baseline_time / t
        efficiency = speedup / n * 100
        analysis[n] = {"time": t, "speedup": speedup, "efficiency": efficiency}
        if speedup > best_speedup:
            best_speedup, best_threads = speedup, n
        print(f"{n:<10}{t:<12.2f}{speedup:<12.2f}{efficiency:<12.1f}")

    print("=" * 56)
    print(f"[✓] Best: {best_threads} threads → {best_speedup:.2f}x speedup\n")
    return analysis


# ---------------------------------------------------------------------------
# Plotting
# ---------------------------------------------------------------------------

def plot(results: dict[int, float], output_dir: Path, fname: str = "benchmark.png"):
    plt.rcParams["font.family"] = "DejaVu Sans"

    threads = sorted(results)
    times = [results[n] for n in threads]
    baseline = min(times)
    speedups = [baseline / t for t in times]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

    ax1.plot(threads, times, "b-o", linewidth=2, markersize=8)
    ax1.set_xlabel("Количество потоков", fontsize=12)
    ax1.set_ylabel("Время (секунды)", fontsize=12)
    ax1.set_title("Время обработки vs Количество потоков", fontsize=14)
    ax1.grid(True, alpha=0.3)
    ax1.set_xticks(threads)

    ax2.plot(threads, speedups, "g-s", linewidth=2, markersize=8, label="Реальное ускорение")
    ax2.plot(threads, threads, "r--", linewidth=1, label="Теоретический максимум")
    ax2.set_xlabel("Количество потоков", fontsize=12)
    ax2.set_ylabel("Ускорение", fontsize=12)
    ax2.set_title("Ускорение vs Количество потоков", fontsize=14)
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    ax2.set_xticks(threads)

    plt.tight_layout()
    out_path = output_dir / fname
    plt.savefig(str(out_path), dpi=150)
    plt.close()
    print(f"[✓] Plot saved → {out_path}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    p = argparse.ArgumentParser(description="Benchmark main.py over several thread counts")
    p.add_argument("-i", "--input", required=True, help="Path to input video file")
    p.add_argument("-t", "--threads", default="1,2,4,8",
                   help="Comma-separated thread counts to test (default: 1,2,4,8)")
    p.add_argument("-o", "--output-dir", default="benchmark_results",
                   help="Directory for outputs (default: benchmark_results)")
    args = p.parse_args()

    if not Path(args.input).exists():
        print(f"[!] Video file not found: {args.input}")
        return

    try:
        thread_counts = [int(x) for x in args.threads.split(",")]
    except ValueError:
        print("[!] Invalid --threads, use e.g. 1,2,4,8")
        return

    output_dir = Path(args.output_dir)
    output_dir.mkdir(exist_ok=True)

    print("=" * 56)
    print("YOLOv8s-pose – Threading Benchmark")
    print("=" * 56)

    results: dict[int, float] = {}
    for n in thread_counts:
        t = run_once(args.input, n, output_dir)
        if t is not None:
            results[n] = t
            print(f"[✓] {n:2d} threads → {t:.2f} s")

    if not results:
        print("[!] No successful runs, nothing to report")
        return

    analysis = analyze(results)
    plot(results, output_dir)
    with open(output_dir / "results.json", "w") as f:
        json.dump({"results": results, "analysis": analysis}, f, indent=2)
    print(f"[✓] Results saved → {output_dir / 'results.json'}")


if __name__ == "__main__":
    main()
