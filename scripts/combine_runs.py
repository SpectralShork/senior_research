"""
Combines the three defender_cost_run_*.csv files from measure_defender_cost.py
into one summary: per-config mean (average of the three run means), pooled
standard deviation across all 300 hashes, and average peak memory.

Usage: python combine_runs.py defender_cost_run_*.csv
(On Windows PowerShell, glob expansion needs: python combine_runs.py (Get-ChildItem defender_cost_run_*.csv))
"""
import csv
import sys
import math
from collections import defaultdict

N_PER_RUN = 100


def pooled_stdev(means, stdevs, grand_mean, n=N_PER_RUN):
    # Combines several equal-size samples' mean/SD into one pooled SD.
    k = len(means)
    ss_within = sum((n - 1) * (s ** 2) for s in stdevs)
    ss_between = sum(n * (m - grand_mean) ** 2 for m in means)
    total_n = k * n
    return math.sqrt((ss_within + ss_between) / (total_n - 1))


def main():
    files = sys.argv[1:]
    if len(files) < 2:
        print("Pass at least two run CSVs, e.g.: python combine_runs.py defender_cost_run_*.csv")
        return

    by_config = defaultdict(list)
    for fname in files:
        with open(fname, newline="") as f:
            for row in csv.DictReader(f):
                by_config[row["label"]].append(row)

    out_rows = []
    for label, rows in by_config.items():
        means = [float(r["mean_ms"]) for r in rows]
        stdevs = [float(r["stdev_ms"]) for r in rows]
        peaks = [float(r["peak_mem_mb"]) for r in rows]
        grand_mean = sum(means) / len(means)
        pooled_sd = pooled_stdev(means, stdevs, grand_mean)
        avg_peak = sum(peaks) / len(peaks)
        out_rows.append({
            "label": label, "n_runs": len(rows),
            "mean_ms": round(grand_mean, 1), "pooled_sd_ms": round(pooled_sd, 1),
            "peak_mem_mb": round(avg_peak, 1),
        })

    out_rows.sort(key=lambda r: r["label"])
    with open("defender_cost_summary.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["label", "n_runs", "mean_ms", "pooled_sd_ms", "peak_mem_mb"])
        w.writeheader()
        w.writerows(out_rows)

    print(f"Combined {len(files)} run files, {len(out_rows)} configs -> defender_cost_summary.csv")
    for r in out_rows:
        print(f"  {r['label']}: {r['mean_ms']} ms (SD {r['pooled_sd_ms']}), peak {r['peak_mem_mb']} MB, n_runs={r['n_runs']}")


if __name__ == "__main__":
    main()
