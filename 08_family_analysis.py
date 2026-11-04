# 08_family_analysis.py -- Family inclusion analysis.
import json
import time
from datetime import date
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import rankdata

# -- Constants --------------------------------------------------------
BASE = Path(__file__).resolve().parent
INPUT_STUDY = BASE / "data" / "fanin_population" / "fanin_population.parquet"
INPUT_POP_A = BASE / "data" / "07_inclusion_packages" / "population_with_families.parquet"
SNAPSHOT_DATE = date(2026, 9, 18)
SIGN_DIFF = 0.03
FI_EDGES = [(1, 9), (10, 99), (100, 999), (1000, None)]
FI_LABELS = ["1-9", "10-99", "100-999", "1000+"]
FI_EXT_EDGES = [(0, 0)] + FI_EDGES
FI_EXT_LABELS = ["0"] + FI_LABELS
FO_EDGES = [(0, 0), (1, 2), (3, 9), (10, 49), (50, None)]
FO_LABELS = ["0", "1-2", "3-9", "10-49", "50+"]
PROFILE_VARS = [
    "n_versions", "n_maintainers", "n_keywords", "n_peer", "n_opt",
    "age_years", "has_github", "deprecated", "scoped",
    "fan_in_dev", "fan_out_dev",
]
STUDY_COLS = [
    "name", "scope", "scope_size", "created_date", "created_year",
    "fan_in", "fan_in_internal", "fan_in_external",
    "fan_out", "fan_out_internal", "fan_out_external",
    "fan_in_dev", "fan_out_dev",
    "n_versions", "n_maintainers", "n_keywords", "n_peer", "n_opt",
    "deprecated", "has_github",
]
DIR_OUT = BASE / "data" / "fanin_families"
FIG_DIR = DIR_OUT / "figures"

# -- Helpers ----------------------------------------------------------
def assign_tramo(values, edges, labels):
    out = pd.Series("", index=values.index)
    for (lo, hi), label in zip(edges, labels):
        mask = values >= lo if hi is None else (values >= lo) & (values <= hi)
        out[mask] = label
    return out
def _rho_on_ranks(rx, ry):
    mx, my = rx.mean(), ry.mean()
    dx, dy = rx - mx, ry - my
    den = np.sqrt((dx * dx).sum() * (dy * dy).sum())
    return float((dx * dy).sum() / den) if den > 0 else np.nan
def spearman_pair(x, y):
    x, y = np.asarray(x, dtype=float), np.asarray(y, dtype=float)
    m = ~(np.isnan(x) | np.isnan(y))
    if m.sum() < 3:
        return np.nan
    return _rho_on_ranks(rankdata(x[m], method="average"),
                         rankdata(y[m], method="average"))

# -- Load data --------------------------------------------------------
def load_data():
    df = pd.read_parquet(str(INPUT_STUDY), columns=STUDY_COLS)
    days = (pd.Timestamp(SNAPSHOT_DATE)
            - pd.to_datetime(df["created_date"])).dt.days
    df["age_years"] = days / 365.25
    df["scoped"] = (df["scope"].fillna("") != "").astype(np.int8)
    for col in ("has_github", "deprecated"):
        df[col] = df[col].fillna(0).astype(bool).astype(np.int8)
    pop = pd.read_parquet(str(INPUT_POP_A), columns=["scope", "scope_size"])
    scoped_pop = pop[pop["scope"].fillna("") != ""]
    clean_counts = scoped_pop["scope"].value_counts()
    df["scope_size_clean"] = (df["scope"].map(clean_counts)
                              .fillna(0).astype("int32"))
    scope_ref = (scoped_pop.groupby("scope")["scope_size"]
                 .first().reset_index())
    scope_ref["scope_size_clean"] = (scope_ref["scope"]
                                     .map(clean_counts).astype(int))
    study_counts = df.loc[df["scoped"] == 1, "scope"].value_counts()
    scope_ref["n_fanin"] = (scope_ref["scope"].map(study_counts)
                            .fillna(0).astype(int))
    del pop, scoped_pop
    return df, scope_ref

# -- 1. Scope table ---------------------------------------------------
def compute_scope_table(df, scope_ref):
    return scope_ref.sort_values("scope_size_clean",
                                 ascending=False).reset_index(drop=True)

# -- 2. Group sizes and changes ---------------------------------------
def compute_groups(df):
    sizes = {
        "G1": len(df),
        "G2": int((df["fan_in_external"] > 0).sum()),
        "G3": int((df["scope_size"] < 2).sum()),
        "G4": int((df["scope_size_clean"] < 2).sum()),
    }
    g4_not_g3 = (df["scope_size_clean"] < 2) & (df["scope_size"] >= 2)
    n_change = int(g4_not_g3.sum())
    tramo = assign_tramo(df["fan_in"], FI_EDGES, FI_LABELS)
    change_by_tramo = (tramo[g4_not_g3].value_counts()
                       .reindex(FI_LABELS, fill_value=0))
    fam_reg = df["scope_size"] >= 2
    fam_clean = df["scope_size_clean"] >= 2
    rows = []
    for label in FI_LABELS:
        m = tramo == label
        rows.append({"tramo": label,
                      "family_registry": int((m & fam_reg).sum()),
                      "family_clean": int((m & fam_clean).sum())})
    return {"sizes": sizes, "n_change": n_change,
            "change_by_tramo": change_by_tramo,
            "fam_by_tramo": pd.DataFrame(rows).set_index("tramo")}

# -- 3. Internal-only packages ----------------------------------------
def compute_internal_only(df):
    ext_zero = df["fan_in_external"] == 0
    n = len(df)
    n_int = int(ext_zero.sum())
    tramo = assign_tramo(df["fan_in"], FI_EDGES, FI_LABELS)
    rows = []
    for label in FI_LABELS:
        m = tramo == label
        t_n = int(m.sum())
        t_int = int((m & ext_zero).sum())
        rows.append({"tramo": label, "total": t_n, "internal_only": t_int,
                      "pct": t_int / t_n * 100 if t_n > 0 else 0})
    return {"n": n_int, "pct": n_int / n * 100,
            "by_tramo": pd.DataFrame(rows)}

# -- 4. Internal share ------------------------------------------------
def _share_by_tramo(df, val_col, int_col, edges, labels):
    tramo = assign_tramo(df[val_col], edges, labels)
    rows = []
    for label in labels:
        m = tramo == label
        s = int(df.loc[m, val_col].sum())
        si = int(df.loc[m, int_col].sum())
        rows.append({"tramo": label, "sum_total": s, "sum_internal": si,
                      "pct": si / s * 100 if s > 0 else 0})
    return pd.DataFrame(rows)
def compute_internal_share(df):
    fi_total = int(df["fan_in"].sum())
    fi_int = int(df["fan_in_internal"].sum())
    fo_total = int(df["fan_out"].sum())
    fo_int = int(df["fan_out_internal"].sum())
    g4 = df[df["scope_size_clean"] < 2]
    g4_scoped = g4[g4["scoped"] == 1]
    return {
        "fi_total": fi_total, "fi_internal": fi_int,
        "fi_share": fi_int / fi_total * 100 if fi_total > 0 else 0,
        "fi_by_tramo": _share_by_tramo(df, "fan_in", "fan_in_internal",
                                        FI_EDGES, FI_LABELS),
        "fo_total": fo_total, "fo_internal": fo_int,
        "fo_share": fo_int / fo_total * 100 if fo_total > 0 else 0,
        "fo_by_tramo": _share_by_tramo(df, "fan_out", "fan_out_internal",
                                        FO_EDGES, FO_LABELS),
        "g4_scoped_with_internal": int(
            (g4_scoped["fan_in_internal"] > 0).sum()),
    }

# -- 5. Tramo crossover -----------------------------------------------
def compute_tramo_cross(df):
    fi = pd.Categorical(assign_tramo(df["fan_in"], FI_EDGES, FI_LABELS),
                         categories=FI_LABELS, ordered=True)
    fi_ext = pd.Categorical(
        assign_tramo(df["fan_in_external"], FI_EXT_EDGES, FI_EXT_LABELS),
        categories=FI_EXT_LABELS, ordered=True)
    cross = pd.crosstab(fi, fi_ext, dropna=False)
    cross.index.name = "fan_in"
    cross.columns.name = "fan_in_external"
    return cross

# -- 6. Retention and differences --------------------------------------
def _retention_table(df, stays, group_col, categories):
    total = df.groupby(group_col).size()
    stayed = df[stays].groupby(group_col).size()
    result = pd.DataFrame({"n_g1": total, "n_stays": stayed})
    result = result.reindex(categories, fill_value=0)
    result["n_stays"] = result["n_stays"].fillna(0).astype(int)
    result["n_g1"] = result["n_g1"].fillna(0).astype(int)
    result["pct"] = (result["n_stays"] / result["n_g1"] * 100).fillna(0)
    return result
def _characterize(sub, tramo_all):
    n = len(sub)
    if n == 0:
        d = {"n": 0, "med_n_versions": np.nan,
             "med_n_maintainers": np.nan, "med_age_years": np.nan,
             "pct_has_github": 0, "pct_deprecated": 0,
             "pct_fi_dev_gt0": 0, "pct_fo_dev_gt0": 0}
        for label in FI_LABELS:
            d[f"pct_{label}"] = 0
        return d
    sub_tramo = tramo_all[sub.index]
    d = {
        "n": n,
        "med_n_versions": float(sub["n_versions"].median()),
        "med_n_maintainers": float(sub["n_maintainers"].median()),
        "med_age_years": float(sub["age_years"].median()),
        "pct_has_github": float(sub["has_github"].mean() * 100),
        "pct_deprecated": float(sub["deprecated"].mean() * 100),
        "pct_fi_dev_gt0": float((sub["fan_in_dev"] > 0).mean() * 100),
        "pct_fo_dev_gt0": float((sub["fan_out_dev"] > 0).mean() * 100),
    }
    for label in FI_LABELS:
        d[f"pct_{label}"] = float((sub_tramo == label).mean() * 100)
    return d
def compute_retention(df):
    tramo = assign_tramo(df["fan_in"], FI_EDGES, FI_LABELS)
    years = sorted(df["created_year"].dropna().unique())
    results = {}
    for gname, stays_mask in [("G3", df["scope_size"] < 2),
                               ("G4", df["scope_size_clean"] < 2)]:
        ret_tramo = _retention_table(df, stays_mask, tramo, FI_LABELS)
        ret_year = _retention_table(df, stays_mask,
                                     df["created_year"], years)
        ret_scoped = _retention_table(df, stays_mask,
                                       df["scoped"], [0, 1])
        stays_c = _characterize(df[stays_mask], tramo)
        leaves_c = _characterize(df[~stays_mask], tramo)
        results[gname] = {
            "ret_tramo": ret_tramo,
            "ret_year": ret_year,
            "ret_scoped": ret_scoped,
            "char": pd.DataFrame([stays_c, leaves_c],
                                  index=["stays", "leaves"]),
        }
    return results

# -- 7. Spearman correlations -----------------------------------------
def _spearman_table(sub, fi_col, fo_col):
    fi = sub[fi_col].values.astype(float)
    fo = sub[fo_col].values.astype(float)
    vs_fi, vs_fo = {}, {}
    for v in PROFILE_VARS:
        x = sub[v].values.astype(float)
        vs_fi[v] = spearman_pair(fi, x)
        vs_fo[v] = spearman_pair(fo, x)
    rho_fi_fo = spearman_pair(fi, fo)
    vs_fi["fan_out"] = rho_fi_fo
    vs_fo["fan_in"] = rho_fi_fo
    return pd.DataFrame({"vs_fan_in": pd.Series(vs_fi),
                          "vs_fan_out": pd.Series(vs_fo)})
def compute_spearman(df):
    groups = {
        "G1": (df, "fan_in", "fan_out"),
        "G2": (df[df["fan_in_external"] > 0],
               "fan_in_external", "fan_out_external"),
        "G3": (df[df["scope_size"] < 2], "fan_in", "fan_out"),
        "G4": (df[df["scope_size_clean"] < 2], "fan_in", "fan_out"),
    }
    tables = {}
    for gname, (sub, fi_col, fo_col) in groups.items():
        tables[gname] = _spearman_table(sub, fi_col, fo_col)
    pairs = [("G2-G1", "G2", "G1"),
             ("G3-G2", "G3", "G2"),
             ("G4-G3", "G4", "G3")]
    diffs, marks = {}, {}
    for label, ga, gb in pairs:
        d = tables[ga] - tables[gb]
        diffs[label] = d
        m = pd.DataFrame(False, index=d.index, columns=d.columns)
        for col in d.columns:
            sa = np.sign(tables[ga][col])
            sb = np.sign(tables[gb][col])
            changed = (sa != sb) & (sa != 0) & (sb != 0)
            m[col] = changed & (d[col].abs() >= SIGN_DIFF)
        marks[label] = m
    return {"tables": tables, "diffs": diffs, "marks": marks}

# -- Gather results ---------------------------------------------------
def gather_results():
    df, scope_ref = load_data()
    return {
        "scope_table": compute_scope_table(df, scope_ref),
        "groups": compute_groups(df),
        "internal_only": compute_internal_only(df),
        "internal_share": compute_internal_share(df),
        "tramo_cross": compute_tramo_cross(df),
        "retention": compute_retention(df),
        "spearman": compute_spearman(df),
    }

# -- Formatting (Spanish) --------------------------------------------
def fmt(n):
    return f"{int(n):,}".replace(",", ".")
def fmtp(v):
    if pd.isna(v):
        return "—"
    return f"{v:.1f}".replace(".", ",") + " %"
def fmtr(v):
    if pd.isna(v):
        return "—"
    return f"{v:+.3f}".replace(".", ",")
def fmtd(v, d=1):
    if pd.isna(v):
        return "—"
    return f"{v:.{d}f}".replace(".", ",")

# -- Figures ----------------------------------------------------------
def fig_spearman(res, target):
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    sp = res["spearman"]["tables"]
    col = "vs_fan_in" if target == "fi" else "vs_fan_out"
    var_list = list(PROFILE_VARS) + (["fan_out"] if target == "fi"
                                      else ["fan_in"])
    title = ("ρ Spearman vs Fan-In por grupo" if target == "fi"
             else "ρ Spearman vs Fan-Out por grupo")
    fname = ("spearman_fan_in_by_group.png" if target == "fi"
             else "spearman_fan_out_by_group.png")
    x = np.arange(len(var_list))
    w = 0.2
    fig, ax = plt.subplots(figsize=(10, 5))
    for k, g in enumerate(["G1", "G2", "G3", "G4"]):
        vals = [float(sp[g].loc[v, col]) if v in sp[g].index
                else np.nan for v in var_list]
        ax.bar(x + (k - 1.5) * w, vals, w, label=g)
    ax.set_xticks(x)
    ax.set_xticklabels(var_list, rotation=45, ha="right", fontsize=7)
    ax.set_ylabel("ρ Spearman")
    ax.set_title(title)
    ax.axhline(0, color="grey", linewidth=0.5)
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(str(FIG_DIR / fname), dpi=150)
    plt.close(fig)
def fig_internal_share(res):
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    t = res["internal_share"]["fi_by_tramo"]
    x = np.arange(len(t))
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.bar(x, t["pct"].values)
    ax.set_xticks(x)
    ax.set_xticklabels(t["tramo"].values, fontsize=9)
    ax.set_ylabel("% interno")
    ax.set_xlabel("Tramo de Fan-In")
    ax.set_title("Parte interna del Fan-In por tramo (G1)")
    fig.tight_layout()
    fig.savefig(str(FIG_DIR / "internal_share_by_band.png"), dpi=150)
    plt.close(fig)
def fig_retention(res):
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    ret = res["retention"]
    x = np.arange(len(FI_LABELS))
    w = 0.35
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.bar(x - w / 2, ret["G3"]["ret_tramo"]["pct"].values, w, label="G3")
    ax.bar(x + w / 2, ret["G4"]["ret_tramo"]["pct"].values, w, label="G4")
    ax.set_xticks(x)
    ax.set_xticklabels(FI_LABELS, fontsize=9)
    ax.set_ylabel("% retenido")
    ax.set_xlabel("Tramo de Fan-In")
    ax.set_title("Retención de G3 y G4 respecto de G1")
    ax.legend()
    fig.tight_layout()
    fig.savefig(str(FIG_DIR / "retention_by_band.png"), dpi=150)
    plt.close(fig)
def fig_band_change(res):
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    cross = res["tramo_cross"]
    row_sums = cross.sum(axis=1).replace(0, 1)
    pct = cross.div(row_sums, axis=0) * 100
    fig, ax = plt.subplots(figsize=(7, 5))
    im = ax.imshow(pct.values, cmap="YlOrRd", aspect="auto")
    ax.set_xticks(range(len(pct.columns)))
    ax.set_xticklabels(pct.columns, fontsize=8)
    ax.set_yticks(range(len(pct.index)))
    ax.set_yticklabels(pct.index, fontsize=8)
    ax.set_xlabel("Tramo de fan_in_external")
    ax.set_ylabel("Tramo de fan_in")
    ax.set_title("Cambio de tramo: fan_in vs fan_in_external (% por fila)")
    for i in range(pct.shape[0]):
        for j in range(pct.shape[1]):
            v = pct.values[i, j]
            c = "white" if v > 50 else "black"
            ax.text(j, i, f"{v:.1f}%", ha="center", va="center",
                    fontsize=7, color=c)
    fig.colorbar(im, ax=ax, shrink=0.7)
    fig.tight_layout()
    fig.savefig(str(FIG_DIR / "band_change.png"), dpi=150)
    plt.close(fig)

# -- Markdown report --------------------------------------------------
def write_md(res, started):
    DIR_OUT.mkdir(parents=True, exist_ok=True)
    g = res["groups"]
    sizes = g["sizes"]
    with open(str(DIR_OUT / "results.md"), "w", encoding="utf-8") as f:
        # Header
        f.write("# Análisis de familias en la población Fan-In > 0\n\n")
        f.write(f"Generado: {started}\n\n")
        f.write("## Entradas\n\n")
        f.write(f"- Población de estudio: `{INPUT_STUDY}`\n")
        f.write(f"- Población A completa: `{INPUT_POP_A}`\n")
        f.write(f"- Fecha del snapshot: {SNAPSHOT_DATE}\n")
        f.write(f"- Paquetes en la población de estudio: {fmt(sizes['G1'])}\n\n")
        # Definitions
        f.write("## Definiciones\n\n")
        f.write("- **G1** (con familias): todas las filas. "
                "Fan-In = fan_in, Fan-Out = fan_out.\n")
        f.write("- **G2** (solo vínculos externos): fan_in_external > 0. "
                "Fan-In = fan_in_external, Fan-Out = fan_out_external.\n")
        f.write("- **G3** (sin familias, registro): scope_size < 2. "
                "Fan-In = fan_in, Fan-Out = fan_out.\n")
        f.write("- **G4** (sin familias, población limpia): "
                "scope_size_clean < 2. Fan-In = fan_in, Fan-Out = fan_out.\n")
        f.write("- **scope_size**: tamaño del scope en el registro completo, "
                "antes de aplicar reglas de inclusión.\n")
        f.write("- **scope_size_clean**: tamaño del scope en la población A "
                "(después de reglas de inclusión, con cualquier fan_in).\n")
        f.write(f"- **Tramos de Fan-In**: {', '.join(FI_LABELS)}. "
                "Para Fan-In externo se agrega el tramo 0.\n")
        f.write(f"- **Tramos de Fan-Out**: {', '.join(FO_LABELS)}.\n")
        f.write(f"- **Variables de perfil**: {', '.join(PROFILE_VARS)}.\n\n")
        f.write("**Nota:** el Fan-In y el Fan-Out vienen del script 05, "
                "contados con los dependientes de todo el registro. "
                "Este script no los recalcula.\n\n")
        # 1. Scopes
        st = res["scope_table"]
        fam_reg = int((st["scope_size"] >= 2).sum())
        fam_clean = int((st["scope_size_clean"] >= 2).sum())
        change_s = int(((st["scope_size"] >= 2)
                        & (st["scope_size_clean"] < 2)).sum())
        f.write("## 1. Scopes\n\n")
        f.write(f"Scopes en la población A: {fmt(len(st))}. "
                f"Familia por registro (scope_size ≥ 2): {fmt(fam_reg)}. "
                f"Familia por población limpia (scope_size_clean ≥ 2): "
                f"{fmt(fam_clean)}. "
                f"Scopes que pasan de familia a no familia: "
                f"{fmt(change_s)}.\n\n")
        # 2. Group sizes
        f.write("## 2. Tamaño de los grupos\n\n")
        f.write("Contados dentro de la población de estudio "
                "(fan_in > 0).\n\n")
        f.write("| Grupo | N | % |\n|---|---|---|\n")
        for gn in ["G1", "G2", "G3", "G4"]:
            n = sizes[gn]
            f.write(f"| {gn} | {fmt(n)} "
                    f"| {fmtp(n / sizes['G1'] * 100)} |\n")
        f.write(f"\nPaquetes en G4 y no en G3: {fmt(g['n_change'])}.\n\n")
        f.write("Por tramo de Fan-In:\n\n")
        f.write("| Tramo | Cambio G3→G4 | Familia registro "
                "| Familia limpia |\n|---|---|---|---|\n")
        fbt = g["fam_by_tramo"]
        for label in FI_LABELS:
            f.write(f"| {label} "
                    f"| {fmt(g['change_by_tramo'].get(label, 0))} "
                    f"| {fmt(fbt.loc[label, 'family_registry'])} "
                    f"| {fmt(fbt.loc[label, 'family_clean'])} |\n")
        f.write("\n")
        # 3. Internal only
        io = res["internal_only"]
        f.write("## 3. Paquetes solo usados por su familia\n\n")
        f.write(f"Paquetes de G1 con fan_in_external = 0: {fmt(io['n'])} "
                f"({fmtp(io['pct'])}).\n\n")
        f.write("| Tramo | Total | Solo internos | % |\n|---|---|---|---|\n")
        for _, row in io["by_tramo"].iterrows():
            f.write(f"| {row['tramo']} | {fmt(row['total'])} "
                    f"| {fmt(row['internal_only'])} "
                    f"| {fmtp(row['pct'])} |\n")
        f.write("\n")
        # 4. Internal share
        ish = res["internal_share"]
        f.write("## 4. Parte interna\n\n")
        f.write("Proporción de vínculos internos (mismo scope) sobre el "
                "total, en G1.\n\n")
        f.write(f"**Fan-In:** Σ interno = {fmt(ish['fi_internal'])}, "
                f"Σ total = {fmt(ish['fi_total'])}, "
                f"parte = {fmtp(ish['fi_share'])}.\n\n")
        f.write("| Tramo | Σ total | Σ interno | % |\n|---|---|---|---|\n")
        for _, row in ish["fi_by_tramo"].iterrows():
            f.write(f"| {row['tramo']} | {fmt(row['sum_total'])} "
                    f"| {fmt(row['sum_internal'])} "
                    f"| {fmtp(row['pct'])} |\n")
        f.write(f"\n**Fan-Out:** Σ interno = {fmt(ish['fo_internal'])}, "
                f"Σ total = {fmt(ish['fo_total'])}, "
                f"parte = {fmtp(ish['fo_share'])}.\n\n")
        f.write("| Tramo | Σ total | Σ interno | % |\n|---|---|---|---|\n")
        for _, row in ish["fo_by_tramo"].iterrows():
            f.write(f"| {row['tramo']} | {fmt(row['sum_total'])} "
                    f"| {fmt(row['sum_internal'])} "
                    f"| {fmtp(row['pct'])} |\n")
        f.write(f"\nPaquetes de G4 con scope y fan_in_internal > 0: "
                f"{fmt(ish['g4_scoped_with_internal'])}.\n\n")
        f.write("![Parte interna](figures/internal_share_by_band.png)\n\n")
        f.write("*Eje X: tramo de Fan-In. Eje Y: porcentaje de Fan-In "
                "interno sobre el total. Grupo: G1.*\n\n")
        _write_md_sections_5_to_7(f, res)
def _write_md_sections_5_to_7(f, res):
    # 5. Tramo cross
    cross = res["tramo_cross"]
    cols = list(cross.columns)
    f.write("## 5. Cambio de tramo\n\n")
    f.write("Tabla cruzada en G1: tramo de fan_in (filas) contra tramo de "
            "fan_in_external (columnas).\n\n")
    f.write("| fan_in \\ fan_in_ext | "
            + " | ".join(str(c) for c in cols) + " |\n")
    f.write("|---|" + "---|" * len(cols) + "\n")
    for label in cross.index:
        cells = [fmt(cross.loc[label, c]) for c in cols]
        f.write(f"| {label} | " + " | ".join(cells) + " |\n")
    f.write("\n![Cambio de tramo](figures/band_change.png)\n\n")
    f.write("*Filas: tramo de fan_in. Columnas: tramo de fan_in_external. "
            "Valores: porcentaje por fila. Grupo: G1.*\n\n")
    # 6. Retention
    f.write("## 6. Diferencias entre grupos\n\n")
    for gname, glabel in [("G3", "sin familias, registro"),
                            ("G4", "sin familias, población limpia")]:
        ret = res["retention"][gname]
        f.write(f"### {gname} ({glabel}) respecto de G1\n\n")
        f.write("**Retención por tramo de Fan-In:**\n\n")
        f.write(f"| Tramo | N en G1 | N en {gname} | % |\n")
        f.write("|---|---|---|---|\n")
        for label in FI_LABELS:
            r = ret["ret_tramo"].loc[label]
            f.write(f"| {label} | {fmt(r['n_g1'])} "
                    f"| {fmt(r['n_stays'])} | {fmtp(r['pct'])} |\n")
        f.write("\n**Retención por año de creación:**\n\n")
        f.write(f"| Año | N en G1 | N en {gname} | % |\n")
        f.write("|---|---|---|---|\n")
        for yr in ret["ret_year"].index:
            r = ret["ret_year"].loc[yr]
            if r["n_g1"] > 0:
                yr_s = str(int(yr)) if not pd.isna(yr) else "NA"
                f.write(f"| {yr_s} | {fmt(r['n_g1'])} "
                        f"| {fmt(r['n_stays'])} | {fmtp(r['pct'])} |\n")
        f.write("\n**Retención por scoped:**\n\n")
        f.write(f"| Scoped | N en G1 | N en {gname} | % |\n")
        f.write("|---|---|---|---|\n")
        for s in [0, 1]:
            r = ret["ret_scoped"].loc[s]
            f.write(f"| {s} | {fmt(r['n_g1'])} "
                    f"| {fmt(r['n_stays'])} | {fmtp(r['pct'])} |\n")
        f.write("\n**Los que salen vs los que se quedan:**\n\n")
        char = ret["char"]
        hdr = ["", "N", "Med n_ver", "Med n_maint", "Med edad",
               "% GitHub", "% deprecated", "% fi_dev>0", "% fo_dev>0"]
        for lb in FI_LABELS:
            hdr.append(f"% {lb}")
        f.write("| " + " | ".join(hdr) + " |\n")
        f.write("|" + "---|" * len(hdr) + "\n")
        for idx, lbl in [("stays", "Quedan"), ("leaves", "Salen")]:
            c = char.loc[idx]
            cells = [lbl, fmt(c["n"]),
                     fmtd(c["med_n_versions"]),
                     fmtd(c["med_n_maintainers"]),
                     fmtd(c["med_age_years"]),
                     fmtp(c["pct_has_github"]),
                     fmtp(c["pct_deprecated"]),
                     fmtp(c["pct_fi_dev_gt0"]),
                     fmtp(c["pct_fo_dev_gt0"])]
            for lb in FI_LABELS:
                cells.append(fmtp(c[f"pct_{lb}"]))
            f.write("| " + " | ".join(cells) + " |\n")
        f.write("\n")
    f.write("![Retención](figures/retention_by_band.png)\n\n")
    f.write("*Eje X: tramo de Fan-In. Eje Y: porcentaje retenido "
            "respecto de G1. Grupos: G3 y G4.*\n\n")
    # 7. Spearman
    sp = res["spearman"]
    vars_fi = list(PROFILE_VARS) + ["fan_out"]
    vars_fo = list(PROFILE_VARS) + ["fan_in"]
    f.write("## 7. Correlaciones de Spearman\n\n")
    f.write("ρ de cada variable de perfil con el Fan-In y el Fan-Out de "
            "cada grupo. Rangos con empates promediados.\n\n")
    f.write("### ρ vs Fan-In\n\n")
    f.write("| Variable | G1 | G2 | G3 | G4 |\n|---|---|---|---|---|\n")
    for v in vars_fi:
        cells = [v]
        for gn in ["G1", "G2", "G3", "G4"]:
            t = sp["tables"][gn]
            cells.append(fmtr(t.loc[v, "vs_fan_in"])
                         if v in t.index else "—")
        f.write("| " + " | ".join(cells) + " |\n")
    f.write("\n### ρ vs Fan-Out\n\n")
    f.write("| Variable | G1 | G2 | G3 | G4 |\n|---|---|---|---|---|\n")
    for v in vars_fo:
        cells = [v]
        for gn in ["G1", "G2", "G3", "G4"]:
            t = sp["tables"][gn]
            cells.append(fmtr(t.loc[v, "vs_fan_out"])
                         if v in t.index else "—")
        f.write("| " + " | ".join(cells) + " |\n")
    f.write(f"\n### Diferencias ((**) = cambio de signo con "
            f"|Δ| ≥ {fmtd(SIGN_DIFF, 2)})\n\n")
    for target, vl in [("vs Fan-In", vars_fi), ("vs Fan-Out", vars_fo)]:
        col = "vs_fan_in" if "In" in target else "vs_fan_out"
        f.write(f"**{target}:**\n\n")
        f.write("| Variable | G2−G1 | G3−G2 | G4−G3 |\n")
        f.write("|---|---|---|---|\n")
        for v in vl:
            cells = [v]
            for pk in ["G2-G1", "G3-G2", "G4-G3"]:
                d = sp["diffs"][pk]
                m = sp["marks"][pk]
                val = d.loc[v, col] if v in d.index else np.nan
                mark = m.loc[v, col] if v in m.index else False
                s = fmtr(val)
                if mark:
                    s += " (**)"
                cells.append(s)
            f.write("| " + " | ".join(cells) + " |\n")
        f.write("\n")
    f.write("![Spearman vs Fan-In](figures/spearman_fan_in_by_group.png)"
            "\n\n")
    f.write("*Eje X: variable de perfil. Eje Y: ρ de Spearman con el "
            "Fan-In del grupo. Una barra por grupo (G1 a G4). "
            "Línea en 0.*\n\n")
    f.write("![Spearman vs Fan-Out](figures/spearman_fan_out_by_group.png)"
            "\n\n")
    f.write("*Eje X: variable de perfil. Eje Y: ρ de Spearman con el "
            "Fan-Out del grupo. Una barra por grupo (G1 a G4). "
            "Línea en 0.*\n\n")
    # Notes
    f.write("## Notas de alcance\n\n")
    f.write("- Las familias se definen solo por scope (@scope/paquete). "
            "Los grupos de paquetes del mismo autor sin scope no se "
            "detectan.\n")
    ish = res["internal_share"]
    f.write(f"- Paquetes de G4 con scope que tienen dependientes internos "
            f"excluidos de la población: "
            f"{fmt(ish['g4_scoped_with_internal'])}.\n")
    f.write("- No se incluye la comprobación de cuántos paquetes tienen "
            "Fan-In > 0 solo gracias a dependientes excluidos de la "
            "población.\n")

# -- README -----------------------------------------------------------
def write_readme():
    DIR_OUT.mkdir(parents=True, exist_ok=True)
    with open(str(DIR_OUT / "README.md"), "w", encoding="utf-8") as f:
        f.write("# data/fanin_families/\n\n")
        f.write("Generated by `08_family_analysis.py`.\n\n")
        f.write("## Inputs\n\n")
        f.write("- `data/fanin_population/fanin_population.parquet` "
                "(from 07)\n")
        f.write("- `data/07_inclusion_packages/"
                "population_with_families.parquet` (from 05)\n\n")
        f.write("## Files\n\n")
        f.write("- `scope_sizes.parquet`: one row per scope in "
                "population A.\n")
        f.write("- `results.md`: analysis report.\n")
        f.write("- `run_metadata.json`: execution metadata.\n")
        f.write("- `figures/`: PNG figures referenced by the report.\n\n")
        f.write("## Columns in scope_sizes.parquet\n\n")
        f.write("| Column | Description |\n|---|---|\n")
        f.write("| scope | Scope name (e.g. @babel). |\n")
        f.write("| scope_size | Number of packages in this scope in the "
                "full registry (before inclusion rules). Comes from "
                "script 05. |\n")
        f.write("| scope_size_clean | Number of packages in this scope "
                "in population A (after inclusion rules, any fan_in). "
                "Computed by this script. |\n")
        f.write("| n_fanin | Number of packages in this scope in the "
                "study population (fan_in > 0). |\n")

# -- Metadata ---------------------------------------------------------
def write_metadata(res, started):
    DIR_OUT.mkdir(parents=True, exist_ok=True)
    sizes = res["groups"]["sizes"]
    meta = {
        "executed_at": started,
        "input": {
            "study_population": str(INPUT_STUDY),
            "population_a": str(INPUT_POP_A),
        },
        "output_dir": str(DIR_OUT),
        "params": {
            "snapshot_date": str(SNAPSHOT_DATE),
            "family_min_size": 2,
            "sign_diff_threshold": SIGN_DIFF,
            "fi_labels": FI_LABELS,
            "fi_ext_labels": FI_EXT_LABELS,
            "fo_labels": FO_LABELS,
        },
        "counts": sizes,
        "n_change_g3_g4": res["groups"]["n_change"],
    }
    with open(str(DIR_OUT / "run_metadata.json"), "w",
              encoding="utf-8") as f:
        json.dump(meta, f, indent=2, ensure_ascii=False)

# -- Main -------------------------------------------------------------
def main():
    started = time.strftime("%Y-%m-%d %H:%M:%S")
    print("08_family_analysis.py")
    res = gather_results()
    sizes = res["groups"]["sizes"]
    print(f"  G1 (con familias):       {sizes['G1']:>10,}")
    print(f"  G2 (solo externos):      {sizes['G2']:>10,}")
    print(f"  G3 (sin fam, registro):  {sizes['G3']:>10,}")
    print(f"  G4 (sin fam, limpia):    {sizes['G4']:>10,}")
    print(f"  Cambio G3→G4:            {res['groups']['n_change']:>10,}")
    print("Writing scope_sizes.parquet ...")
    DIR_OUT.mkdir(parents=True, exist_ok=True)
    res["scope_table"].to_parquet(str(DIR_OUT / "scope_sizes.parquet"),
                                  index=False)
    print("Writing figures ...")
    fig_spearman(res, "fi")
    fig_spearman(res, "fo")
    fig_internal_share(res)
    fig_retention(res)
    fig_band_change(res)
    print("Writing results.md ...")
    write_md(res, started)
    print("Writing README.md ...")
    write_readme()
    print("Writing run_metadata.json ...")
    write_metadata(res, started)
    print("Done.")

if __name__ == "__main__":
    main()
