import argparse
import csv
import glob
import math
import statistics
import sys
from collections import defaultdict

N_PER_RUN = 100  # hashes per configuration per run (RUNS in measure_defender_cost.py)
ALGO_ORDER = {"argon2id": 0, "pbkdf2": 1, "bcrypt": 2}
OUT_FIELDS = [
    "algo", "label", "n_runs", "mean_ms", "pooled_sd_ms", "sd_pct_of_mean",
    "peak_mem_mib", "min_run_mean_ms", "max_run_mean_ms", "run_spread_pct",
]


def pooled_stdev(means, stdevs, grand_mean, n=N_PER_RUN):
    """Pooled sample SD of k equal-size samples given each sample's mean and SD."""
    k = len(means)
    ss_within = sum((n - 1) * (s ** 2) for s in stdevs)
    ss_between = sum(n * (m - grand_mean) ** 2 for m in means)
    return math.sqrt((ss_within + ss_between) / (k * n - 1))


def num(value):
    """CSV cell -> float; blank cells (e.g. memory_mib for bcrypt) become 0."""
    return float(value) if value not in (None, "") else 0.0


def sort_key(row):
    """Argon2id first, then PBKDF2, then bcrypt; numeric order within each."""
    return (
        ALGO_ORDER.get(row["algo"], 99),
        num(row.get("memory_mib")),
        num(row.get("time_cost")),
        num(row.get("parallelism")),
        num(row.get("iterations")),
        num(row.get("cost")),
    )


def peak_column(fieldnames):
    for name in ("peak_mem_mib", "peak_mem_mb"):
        if name in fieldnames:
            return name
    sys.exit("No peak memory column (peak_mem_mib / peak_mem_mb) found in the run files.")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("files", nargs="*", help="run CSVs (default: defender_cost_run_*.csv in this folder)")
    ap.add_argument("--expected-runs", type=int, default=5, help="runs you expect per config (default 5)")
    ap.add_argument("--out", default="defender_cost_summary.csv", help="output file name")
    args = ap.parse_args()

    # Expand patterns ourselves so this works the same in PowerShell, cmd and bash.
    files = []
    for pattern in (args.files or ["defender_cost_run_*.csv"]):
        files.extend(glob.glob(pattern) or [pattern])
    files = sorted(set(files))

    if len(files) < 2:
        sys.exit("Need at least two run CSVs. Run this from the folder that contains "
                 "defender_cost_run_*.csv, or pass the file names.")
    if len(files) != args.expected_runs:
        print(f"WARNING: found {len(files)} run files but expected {args.expected_runs}.")

    by_config = defaultdict(list)
    for fname in files:
        with open(fname, newline="") as f:
            reader = csv.DictReader(f)
            peak_col = peak_column(reader.fieldnames)
            for row in reader:
                row["_peak"] = row[peak_col]
                by_config[row["label"]].append(row)

    out_rows = []
    for label, rows in by_config.items():
        means = [float(r["mean_ms"]) for r in rows]
        stdevs = [float(r["stdev_ms"]) for r in rows]
        peaks = [float(r["_peak"]) for r in rows]
        grand_mean = statistics.mean(means)
        pooled_sd = pooled_stdev(means, stdevs, grand_mean)
        out_rows.append({
            "_sort": sort_key(rows[0]),
            "algo": rows[0]["algo"],
            "label": label,
            "n_runs": len(rows),
            "mean_ms": round(grand_mean, 1),
            "pooled_sd_ms": round(pooled_sd, 1),
            "sd_pct_of_mean": round(pooled_sd / grand_mean * 100, 1),
            "peak_mem_mib": round(statistics.mean(peaks), 1),
            "min_run_mean_ms": round(min(means), 1),
            "max_run_mean_ms": round(max(means), 1),
            "run_spread_pct": round((max(means) - min(means)) / grand_mean * 100, 1),
        })

    out_rows.sort(key=lambda r: r["_sort"])

    bad = [r["label"] for r in out_rows if r["n_runs"] != len(files)]
    if bad:
        print(f"WARNING: these configs are missing from some run files: {bad}")

    with open(args.out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=OUT_FIELDS, extrasaction="ignore")
        w.writeheader()
        w.writerows(out_rows)

    print(f"Combined {len(files)} run files, {len(out_rows)} configs -> {args.out}\n")
    for r in out_rows:
        print(f"{r['label']:<38} {r['mean_ms']:>8} ms  SD {r['pooled_sd_ms']:>6} "
              f"({r['sd_pct_of_mean']}%)  peak {r['peak_mem_mib']} MiB  "
              f"run spread {r['run_spread_pct']}%")

    argon = [r for r in out_rows if r["algo"] == "argon2id"]
    if argon:
        spreads = [r["run_spread_pct"] for r in argon]
        sds = [r["sd_pct_of_mean"] for r in argon]
        print(f"\nArgon2id run-to-run spread: {min(spreads)}% to {max(spreads)}% "
              f"(median {statistics.median(spreads)}%)")
        print(f"Argon2id pooled SD: {min(sds)}% to {max(sds)}% of the mean")


if __name__ == "__main__":
    main()