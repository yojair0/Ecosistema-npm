#!/usr/bin/env python3
"""Checks on the profile report: date artefacts, tie attenuation, k=5 boundaries."""
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans

SNAPSHOT = pd.Timestamp("2026-09-18")
COLLECTION = pd.Timestamp("2026-10-10")

df = pd.read_parquet("data/06_profile_analysis/profile_table.parquet")
p = df[df["has_profile"]]

created = SNAPSHOT - pd.to_timedelta(p["age_days"], unit="D")
print("Oldest creation years:")
print(created.dt.year.value_counts().sort_index().head(5).to_string(), "\n")

modified = COLLECTION - pd.to_timedelta(p["days_since_mod"], unit="D")
print("Most common modification dates:")
print(modified.dt.date.value_counts().head(5).to_string(), "\n")

miss = p["file_count"].isna()
print(f"file_count missing: {miss.sum():,} | median creation year, "
      f"missing vs present: {created[miss].dt.year.median():.0f} vs "
      f"{created[~miss].dt.year.median():.0f}\n")

q = p[p["fan_in"] > 0]
cols = ["age_days", "days_since_mod", "n_versions", "n_maintainers",
        "n_keywords", "file_count", "unpacked", "fan_out", "fan_in_dev",
        "fan_in_peer", "scoped", "has_github", "deprecated"]
rho = q[["fan_in"] + cols].corr(method="spearman")["fan_in"].drop("fan_in")
print(f"Spearman with fan-in, fan-in > 0 only (n={len(q):,}):")
print(rho.sort_values(key=abs, ascending=False).round(3).to_string(), "\n")

fi = df.loc[df["fan_in"] > 0, "fan_in"].to_numpy()
km = KMeans(n_clusters=5, n_init=10, random_state=42).fit(np.log1p(fi).reshape(-1, 1))
print("k-means k=5 ranges:")
for c in np.argsort(km.cluster_centers_.ravel()):
    m = fi[km.labels_ == c]
    print(f"  {m.min():>7,} - {m.max():>7,}  n={len(m):,}")