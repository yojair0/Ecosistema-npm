# stratification/03_regression_tree.py -- tree-based stratification on dataset B.
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import numpy as np
import pandas as pd
try:
    from sklearn.tree import DecisionTreeRegressor
except ImportError:
    sys.exit("scikit-learn is required: pip install scikit-learn")
from common import (load_dataset_b, split_halves, partition_metrics,
                     validation_r2, strata_table, write_metrics, write_strata,
                     write_results_md, df_to_markdown, SEED, VARS,
                     ZERO_CELL_NAMES)

# ── Constants ────────────────────────────────────────────────────────
TECHNIQUE = "03_regression_tree"
TOTAL_LEAVES = [8, 15, 25]
MIN_LEAF = 5000
FIT_SAMPLE_MAX = 500_000
CELL_TARGETS = {1: ["fo"], 2: ["fi"], 3: ["fi", "fo"]}

# ── Leaf allocation (largest remainder) ──────────────────────────────
def allocate_leaves(total, cell_sizes):
    cells = sorted(cell_sizes.keys())
    distributable = total - 1  # minus Aislado
    min_per = 2
    remaining = distributable - min_per * len(cells)
    size_total = sum(cell_sizes[c] for c in cells)
    ideal = {c: remaining * cell_sizes[c] / size_total for c in cells}
    floored = {c: int(ideal[c]) for c in cells}
    leftover = remaining - sum(floored.values())
    by_rem = sorted(cells, key=lambda c: ideal[c] - floored[c], reverse=True)
    for i in range(leftover):
        floored[by_rem[i]] += 1
    return {c: min_per + floored[c] for c in cells}

# ── Tree rule extraction ─────────────────────────────────────────────
def _leaf_conditions(tree, feature_names):
    t = tree.tree_
    result = {}
    def walk(node, conds):
        if t.children_left[node] == -1:
            result[node] = conds[:]
            return
        f = feature_names[t.feature[node]]
        th = float(t.threshold[node])
        walk(t.children_left[node], conds + [(f, "<=", th)])
        walk(t.children_right[node], conds + [(f, ">", th)])
    walk(0, [])
    return result
def _fmt_t(v):
    return f"{v:.2f}".replace(".", ",")
def _format_rule(cell_name, conds):
    if not conds:
        return cell_name
    bounds = {}
    order = []
    for f, op, th in conds:
        if f not in bounds:
            bounds[f] = [None, None]
            order.append(f)
        if op == "<=":
            if bounds[f][1] is None or th < bounds[f][1]:
                bounds[f][1] = th
        else:
            if bounds[f][0] is None or th > bounds[f][0]:
                bounds[f][0] = th
    parts = []
    for f in order:
        lo, hi = bounds[f]
        if lo is not None and hi is not None:
            parts.append(f"{_fmt_t(lo)} < {f} \u2264 {_fmt_t(hi)}")
        elif hi is not None:
            parts.append(f"{f} \u2264 {_fmt_t(hi)}")
        else:
            parts.append(f"{f} > {_fmt_t(lo)}")
    return cell_name + ", " + " y ".join(parts)

# ── Main ─────────────────────────────────────────────────────────────
def main():
    print("Loading dataset B ...")
    df = load_dataset_b()
    n = len(df)
    mask_fit, mask_test = split_halves(n, SEED)
    zc = df["zero_cell"].values
    cell_sizes = {c: int((zc == c).sum()) for c in [1, 2, 3]}
    print(f"  n={n:,}  cells: {cell_sizes}")
    metric_rows = []
    strata_tables_list = []
    configs = {}
    for total in TOTAL_LEAVES:
        config = f"leaves{total}"
        alloc = allocate_leaves(total, cell_sizes)
        strata = np.full(n, -1, dtype=np.int32)
        info_rows = []
        imp_rows = []
        notes = []
        next_id = 0
        # Cell 0: Aislado — single stratum
        strata[zc == 0] = next_id
        info_rows.append({"stratum": next_id, "description": ZERO_CELL_NAMES[0]})
        next_id += 1
        for cell_code in [1, 2, 3]:
            cell_name = ZERO_CELL_NAMES[cell_code]
            n_leaves = alloc[cell_code]
            cell_mask = zc == cell_code
            cell_fit = cell_mask & mask_fit
            X_fit = df.loc[cell_fit, VARS].values.astype(np.float64)
            # Build standardised targets
            targets = []
            for col in CELL_TARGETS[cell_code]:
                y = np.log1p(df.loc[cell_fit, col].values).astype(np.float64)
                mu, sd = float(y.mean()), float(y.std())
                if sd > 0:
                    targets.append((y - mu) / sd)
            if not targets:
                strata[cell_mask] = next_id
                info_rows.append({"stratum": next_id,
                                  "description": cell_name})
                notes.append(f"{cell_name}: objetivo constante, 1 estrato")
                next_id += 1
                continue
            # Subsample fit data if needed
            n_fit_cell = len(X_fit)
            if n_fit_cell > FIT_SAMPLE_MAX:
                rng = np.random.default_rng(SEED)
                idx = rng.choice(n_fit_cell, FIT_SAMPLE_MAX, replace=False)
                X_fit = X_fit[idx]
                targets = [t[idx] for t in targets]
            y_train = (np.column_stack(targets) if len(targets) > 1
                       else targets[0].reshape(-1, 1))
            n_cell_total = int(cell_mask.sum())
            min_leaf_scaled = max(1, round(
                MIN_LEAF * len(X_fit) / n_cell_total))
            tree = DecisionTreeRegressor(
                max_leaf_nodes=n_leaves,
                min_samples_leaf=min_leaf_scaled,
                random_state=SEED)
            tree.fit(X_fit, y_train)
            # Apply to all rows of cell
            X_all = df.loc[cell_mask, VARS].values.astype(np.float64)
            leaf_ids = tree.apply(X_all)
            unique_leaves = np.sort(np.unique(leaf_ids))
            actual = len(unique_leaves)
            if actual < n_leaves:
                notes.append(f"{cell_name}: {actual} hojas "
                             f"en vez de {n_leaves}")
            # Rules and stratum mapping
            conds_map = _leaf_conditions(tree, list(VARS))
            remap = np.empty(int(unique_leaves.max()) + 1, dtype=np.int32)
            for uid in unique_leaves:
                remap[uid] = next_id
                info_rows.append({
                    "stratum": next_id,
                    "description": _format_rule(cell_name, conds_map[uid]),
                })
                next_id += 1
            strata[cell_mask] = remap[leaf_ids]
            for vi, var in enumerate(VARS):
                imp_rows.append({
                    "cell": cell_name, "variable": var,
                    "importance": float(tree.feature_importances_[vi]),
                })
        # Metrics
        met = partition_metrics(df, strata)
        val = validation_r2(df, strata, mask_fit, mask_test)
        alloc_str = "/".join(str(alloc[c]) for c in [1, 2, 3])
        params = (f"total={total}, reparto=1/{alloc_str}, "
                  f"min_leaf={MIN_LEAF}, fit_max={FIT_SAMPLE_MAX}")
        row = {"config": config, "params": params}
        row.update(met)
        row.update(val)
        metric_rows.append(row)
        info_df = pd.DataFrame(info_rows)
        st = strata_table(df, strata, info_df, TECHNIQUE, config)
        strata_tables_list.append(st)
        imp_df = pd.DataFrame(imp_rows) if imp_rows else pd.DataFrame()
        configs[config] = {"strata_df": st, "alloc": alloc,
                           "notes": notes, "importance": imp_df}
        print(f"  {config:12s}  leaves=1/{alloc_str}"
              f"  K={met['K']:3d}  min_n={met['min_n']:7,}"
              f"  r2_fi={met['r2_log_fi']:.4f}"
              f"  r2_fo={met['r2_log_fo']:.4f}")
    # ── Write outputs ────────────────────────────────────────────────
    write_metrics(TECHNIQUE, metric_rows)
    write_strata(TECHNIQUE, pd.concat(strata_tables_list, ignore_index=True))
    # ── Markdown ─────────────────────────────────────────────────────
    lines = ["# Estratificación por árbol de regresión\n"]
    lines.append("## Parámetros\n")
    lines.append(f"- Semilla: {SEED}")
    lines.append(f"- Mínimo por hoja (sobre B completo): {MIN_LEAF:,}")
    lines.append(f"- Máximo de filas para ajuste: {FIT_SAMPLE_MAX:,}")
    lines.append(f"- Total de hojas probadas: {TOTAL_LEAVES}")
    lines.append(f"- Variables: {', '.join(VARS)}\n")
    lines.append("## Reparto de hojas por configuración\n")
    alloc_rows = []
    for total in TOTAL_LEAVES:
        a = configs[f"leaves{total}"]["alloc"]
        alloc_rows.append({"config": f"leaves{total}", "total": total,
                           "Aislado": 1, "Consumidor": a[1],
                           "Consumido": a[2], "Ambas": a[3]})
    lines.append(df_to_markdown(pd.DataFrame(alloc_rows)))
    lines.append("")
    lines.append("## Métricas\n")
    met_df = pd.DataFrame(metric_rows)
    show_cols = ["config", "K", "min_n", "n_under_min",
                 "r2_log_fi", "r2_log_fo", "r2_log_n_versions", "r2_age",
                 "eff_prop_log_fi", "eff_neyman_log_fi",
                 "eff_prop_log_fo", "eff_neyman_log_fo",
                 "r2_log_fi_train", "r2_log_fi_test",
                 "r2_log_fo_train", "r2_log_fo_test"]
    lines.append(df_to_markdown(met_df[show_cols]))
    lines.append("")
    lines.append("## Tabla de estratos por configuración\n")
    show_st = ["stratum", "description", "n", "share",
               "mean_log_fi", "mean_log_fo",
               "median_n_versions", "median_age"]
    for config, data in configs.items():
        lines.append(f"### {config}\n")
        if data["notes"]:
            for note in data["notes"]:
                lines.append(f"- *{note}*")
            lines.append("")
        lines.append(df_to_markdown(data["strata_df"][show_st]))
        lines.append("")
        if not data["importance"].empty:
            lines.append(f"#### Importancia de variables — {config}\n")
            imp = data["importance"].copy()
            imp["importance"] = imp["importance"].round(4)
            lines.append(df_to_markdown(imp))
            lines.append("")
    write_results_md(TECHNIQUE, "\n".join(lines))
    print("Done.")

if __name__ == "__main__":
    main()
