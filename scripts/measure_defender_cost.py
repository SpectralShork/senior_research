import time
import csv
import os
import statistics
import psutil
import hashlib
import bcrypt
from argon2.low_level import hash_secret_raw, Type

PASSWORD = b"password123"
RUNS = 100


def build_configs():
    configs = []
    for it in (100_000, 600_000, 1_200_000):
        configs.append({"algo": "pbkdf2", "iterations": it})
    for cost in (10, 12, 14):
        configs.append({"algo": "bcrypt", "cost": cost})
    for mem_mib in (19, 46, 64, 256, 1024, 2048):
        for t in (1, 2, 3):
            for p in (1, 4):
                configs.append({
                    "algo": "argon2id", "memory_mib": mem_mib,
                    "memory_kib": mem_mib * 1024, "time_cost": t, "parallelism": p,
                })
    return configs

def run_once(cfg):
    if cfg["algo"] == "pbkdf2":
        salt = os.urandom(16)
        start = time.perf_counter()
        hashlib.pbkdf2_hmac("sha256", PASSWORD, salt, cfg["iterations"], dklen=32)
        return time.perf_counter() - start
    if cfg["algo"] == "bcrypt":
        start = time.perf_counter()
        bcrypt.hashpw(PASSWORD, bcrypt.gensalt(rounds=cfg["cost"]))
        return time.perf_counter() - start
    if cfg["algo"] == "argon2id":
        salt = os.urandom(16)
        start = time.perf_counter()
        hash_secret_raw(PASSWORD, salt, time_cost=cfg["time_cost"],
                         memory_cost=cfg["memory_kib"], parallelism=cfg["parallelism"],
                         hash_len=32, type=Type.ID)
        return time.perf_counter() - start
    raise ValueError(cfg["algo"])


def config_label(cfg):
    if cfg["algo"] == "pbkdf2":
        return f"PBKDF2-HMAC-SHA256 it={cfg['iterations']}"
    if cfg["algo"] == "bcrypt":
        return f"bcrypt cost={cfg['cost']}"
    return f"Argon2id m={cfg['memory_mib']}MiB t={cfg['time_cost']} p={cfg['parallelism']}"


def main():
    proc = psutil.Process(os.getpid())
    configs = build_configs()
    results = []
    overall_start = time.time()
    for i, cfg in enumerate(configs, 1):
        times_ms = [run_once(cfg) * 1000 for _ in range(RUNS)]
        peak_mb = proc.memory_info().peak_wset / (1024 * 1024)
        mean_t = statistics.mean(times_ms)
        stdev_t = statistics.stdev(times_ms)
        label = config_label(cfg)
        elapsed = time.time() - overall_start
        print(f"[{i}/{len(configs)}] {label}: mean={mean_t:.2f} ms, "
              f"stdev={stdev_t:.2f} ms, peak={peak_mb:.1f} MB "
              f"(elapsed {elapsed/60:.1f} min)")
        results.append({**cfg, "label": label, "mean_ms": mean_t,
                         "stdev_ms": stdev_t, "peak_mem_mb": peak_mb})

    ts = time.strftime("%Y%m%dT%H%M%S")
    fname = f"defender_cost_run_{ts}.csv"
    fields = ["label", "algo", "memory_mib", "time_cost", "parallelism",
              "iterations", "cost", "mean_ms", "stdev_ms", "peak_mem_mb"]
    with open(fname, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(results)
    print(f"\nSaved {len(results)} configs to {fname}")


if __name__ == "__main__":
    main()