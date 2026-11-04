# 07_fanin_population.py -- Fan-in > 0 study population.
import json
import time
from pathlib import Path
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

BASE = Path(__file__).resolve().parent
INPUT_A = BASE / "data" / "07_inclusion_packages" / "population_with_families.parquet"
INPUT_B = BASE / "data" / "07_inclusion_packages" / "population_without_families.parquet"
DIR_OUT = BASE / "data" / "fanin_population"
EXCLUDED_COLS = ["file_count", "unpacked", "self_deps"]
FILTER = [("fan_in", ">", 0)]
COLS = [
    "name", "scope", "scope_size", "created_date", "created_year",
    "latest", "latest_p2", "tarball", "dep_hash",
    "fan_in", "fan_in_internal", "fan_in_external",
    "fan_out", "fan_out_internal", "fan_out_external",
    "fan_in_dev", "fan_out_dev",
    "n_versions", "n_maintainers", "deprecated", "has_github",
    "n_keywords", "keywords", "n_peer", "n_opt",
]

def write_parquet_chunked(df, path, chunk_size=500_000):
    n = len(df)
    first_end = min(chunk_size, n)
    first_table = pa.Table.from_pandas(df.iloc[:first_end], preserve_index=False)
    schema = first_table.schema
    if "keywords" in df.columns:
        idx = schema.get_field_index("keywords")
        schema = schema.set(idx, pa.field("keywords", pa.list_(pa.string())))
    with pq.ParquetWriter(str(path), schema) as writer:
        writer.write_table(first_table.cast(schema))
        del first_table
        for start in range(chunk_size, n, chunk_size):
            end = min(start + chunk_size, n)
            chunk = pa.Table.from_pandas(
                df.iloc[start:end], preserve_index=False).cast(schema)
            writer.write_table(chunk)
            del chunk

def fmt(n):
    return f"{n:,}".replace(",", ".")

def run_checks(df, n_b):
    checks = []
    c1 = int((df["fan_in"] <= 0).sum())
    checks.append(("All fan_in > 0",
                    "ok" if c1 == 0 else f"{fmt(c1)} fail"))
    c2 = int(df["name"].duplicated().sum())
    checks.append(("No duplicate names",
                    "ok" if c2 == 0 else f"{fmt(c2)} duplicates"))
    c3 = int(((df["fan_in_internal"] + df["fan_in_external"]) != df["fan_in"]).sum())
    checks.append(("fan_in_internal + fan_in_external = fan_in",
                    "ok" if c3 == 0 else f"{fmt(c3)} fail"))
    no_fam = df["scope_size"] < 2
    c4 = int((no_fam & (df["fan_in_internal"] > 0)).sum())
    checks.append(("scope_size < 2 implies fan_in_internal = 0",
                    "ok" if c4 == 0 else f"{fmt(c4)} fail"))
    n_no_fam = int(no_fam.sum())
    c5 = n_no_fam == n_b
    checks.append(("Without-families count matches population B",
                    "ok" if c5 else
                    f"A filtered: {fmt(n_no_fam)}, B filtered: {fmt(n_b)}"))
    return checks

def write_summary(path, counts, checks):
    with open(str(path), "w", encoding="utf-8") as f:
        f.write("# Fan-in > 0 population\n\n")
        f.write("## Counts\n\n")
        f.write(f"- Total packages: {fmt(counts['total'])}\n")
        f.write(f"- With families (all): {fmt(counts['with_families'])}\n")
        f.write(f"- Without families (scope_size < 2): "
                f"{fmt(counts['without_families'])}\n")
        f.write(f"- With external dependents (fan_in_external > 0): "
                f"{fmt(counts['external_only'])}\n\n")
        f.write("## Checks\n\n")
        for label, result in checks:
            f.write(f"- {label}: {result}\n")

def main():
    started = time.strftime("%Y-%m-%d %H:%M:%S")
    df = pd.read_parquet(str(INPUT_A), columns=COLS, filters=FILTER)
    n_b = len(pd.read_parquet(str(INPUT_B), columns=["fan_in"],
                               filters=FILTER))
    n = len(df)
    n_no_fam = int((df["scope_size"] < 2).sum())
    n_ext = int((df["fan_in_external"] > 0).sum())
    counts = {
        "total": n,
        "with_families": n,
        "without_families": n_no_fam,
        "external_only": n_ext,
    }
    checks = run_checks(df, n_b)
    print(f"Total: {n:,}")
    print(f"Without families: {n_no_fam:,}")
    print(f"With external dependents: {n_ext:,}")
    for label, result in checks:
        if result != "ok":
            print(f"  WARNING: {label}: {result}")
    DIR_OUT.mkdir(parents=True, exist_ok=True)
    write_parquet_chunked(df, DIR_OUT / "fanin_population.parquet")
    write_summary(DIR_OUT / "summary.md", counts, checks)
    metadata = {
        "executed_at": started,
        "input": {
            "population_a": str(INPUT_A),
            "population_b": str(INPUT_B),
        },
        "output": str(DIR_OUT / "fanin_population.parquet"),
        "filter": "fan_in > 0",
        "excluded_columns": EXCLUDED_COLS,
        "counts": counts,
    }
    with open(str(DIR_OUT / "run_metadata.json"), "w",
              encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)
    print("Done.")

if __name__ == "__main__":
    main()
