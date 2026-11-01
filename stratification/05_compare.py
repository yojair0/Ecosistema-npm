# stratification/05_compare.py -- compare stratification techniques.
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from common import RESULTS_DIR, write_results_md, df_to_markdown

# ── Constants ────────────────────────────────────────────────────────
TECHNIQUE = "comparison"
TECHNIQUES = ["01_grid_base", "02_optimal_cuts",
              "03_regression_tree", "04_clustering"]
FIG_DIR = RESULTS_DIR / TECHNIQUE / "figures"
SHOW_COLS = ["technique", "config", "K", "min_n", "n_under_min",
             "r2_log_fi", "r2_log_fo", "r2_log_n_versions", "r2_age",
             "eff_neyman_log_fi", "eff_neyman_log_fo",
             "gap_fi", "gap_fo", "silhouette", "davies_bouldin"]
TARGET_K = [9, 15, 25]

# ── Load ─────────────────────────────────────────────────────────────
def load_all():
    frames = []
    found = []
    missing = []
    for tech in TECHNIQUES:
        path = RESULTS_DIR / tech / "metrics.csv"
        if not path.exists():
            missing.append(tech)
            continue
        df = pd.read_csv(str(path))
        if "technique" in df.columns:
            if not (df["technique"] == tech).all():
                print(f"  WARNING: technique column mismatch in {tech}")
        else:
            df.insert(0, "technique", tech)
        found.append(tech)
        frames.append(df)
    if not frames:
        return pd.DataFrame(), found, missing
    all_df = pd.concat(frames, ignore_index=True)
    all_df["gap_fi"] = all_df["r2_log_fi_train"] - all_df["r2_log_fi_test"]
    all_df["gap_fo"] = all_df["r2_log_fo_train"] - all_df["r2_log_fo_test"]
    all_df["census"] = False
    mask_01_02 = all_df["technique"].isin(
        ["01_grid_base", "02_optimal_cuts"])
    all_df.loc[mask_01_02, "census"] = (
        all_df.loc[mask_01_02, "config"].str.contains("census")
        & ~all_df.loc[mask_01_02, "config"].str.contains("nocensus"))
    for col in ["silhouette", "davies_bouldin"]:
        if col not in all_df.columns:
            all_df[col] = np.nan
    all_df.sort_values(["technique", "K"], inplace=True, ignore_index=True)
    return all_df, found, missing

# ── Comparable K table ───────────────────────────────────────────────
def comparable_k(all_df):
    rows = []
    groups = []
    for _, row in all_df.iterrows():
        tech = row["technique"]
        if tech in ("01_grid_base", "02_optimal_cuts"):
            label = f"{tech}_census" if row["census"] else f"{tech}_nocensus"
        else:
            label = tech
        groups.append(label)
    all_df = all_df.copy()
    all_df["_group"] = groups
    for target in TARGET_K:
        for grp in sorted(all_df["_group"].unique()):
            sub = all_df[all_df["_group"] == grp]
            idx = (sub["K"] - target).abs().idxmin()
            r = sub.loc[idx].copy()
            r["target_K"] = target
            rows.append(r)
    result = pd.DataFrame(rows).reset_index(drop=True)
    result.drop(columns=["_group"], inplace=True)
    return result

# ── Figures ──────────────────────────────────────────────────────────
def _series_key(row):
    tech = row["technique"]
    if tech in ("01_grid_base", "02_optimal_cuts"):
        return f"{tech}_census" if row["census"] else f"{tech}_nocensus"
    return tech
SERIES_STYLE = {
    "01_grid_base_nocensus":    {"marker": "o", "ls": "-",  "color": "C0"},
    "01_grid_base_census":      {"marker": "o", "ls": "--", "color": "C0"},
    "02_optimal_cuts_nocensus": {"marker": "s", "ls": "-",  "color": "C1"},
    "02_optimal_cuts_census":   {"marker": "s", "ls": "--", "color": "C1"},
    "03_regression_tree":       {"marker": "^", "ls": "-",  "color": "C2"},
    "04_clustering":            {"marker": "D", "ls": "-",  "color": "C3"},
}
SERIES_LABEL = {
    "01_grid_base_nocensus":    "Cuadrícula (sin censo)",
    "01_grid_base_census":      "Cuadrícula (con censo)",
    "02_optimal_cuts_nocensus": "Cortes óptimos (sin censo)",
    "02_optimal_cuts_census":   "Cortes óptimos (con censo)",
    "03_regression_tree":       "Árbol de regresión",
    "04_clustering":            "Clustering k-means",
}
def _plot_two_panels(all_df, col_left, col_right, ylabel_l, ylabel_r,
                     title, path, hline=None):
    all_df = all_df.copy()
    all_df["_key"] = all_df.apply(_series_key, axis=1)
    has_inf = False
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4.5))
    for key in sorted(all_df["_key"].unique()):
        sub = all_df[all_df["_key"] == key].sort_values("K")
        sty = SERIES_STYLE.get(key, {"marker": "x", "ls": "-", "color": "gray"})
        lab = SERIES_LABEL.get(key, key)
        for ax, col in [(ax1, col_left), (ax2, col_right)]:
            vals = sub[col].values.astype(float)
            ks = sub["K"].values
            finite = np.isfinite(vals)
            if not finite.all():
                has_inf = True
            ax.plot(ks[finite], vals[finite], label=lab, **sty)
    for ax, col, yl in [(ax1, col_left, ylabel_l),
                         (ax2, col_right, ylabel_r)]:
        ax.set_xlabel("K (estratos)")
        ax.set_ylabel(yl)
        if hline is not None:
            ax.axhline(hline, color="gray", lw=0.8, ls=":")
        ax.legend(fontsize=7)
    fig.suptitle(title, fontsize=11)
    footnote = "Solo con B (sin familias)."
    if has_inf:
        footnote += " Puntos con eficiencia infinita omitidos."
    fig.text(0.5, -0.02, footnote, ha="center", fontsize=7)
    fig.tight_layout()
    fig.savefig(str(path), dpi=150, bbox_inches="tight")
    plt.close(fig)
def make_figures(all_df):
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    _plot_two_panels(
        all_df, "r2_log_fi", "r2_log_fo",
        "R² log(1+fi)", "R² log(1+fo)",
        "Varianza explicada de Fan-In y Fan-Out",
        FIG_DIR / "fig01_r2_fan_vs_k.png")
    _plot_two_panels(
        all_df, "r2_log_n_versions", "r2_age",
        "R² log(1+n_versions)", "R² age_years",
        "Varianza explicada de variables de perfil",
        FIG_DIR / "fig02_r2_profile_vs_k.png")
    _plot_two_panels(
        all_df, "eff_neyman_log_fi", "eff_neyman_log_fo",
        "Eficiencia Neyman log(1+fi)", "Eficiencia Neyman log(1+fo)",
        "Eficiencia de muestreo estratificado (Neyman)",
        FIG_DIR / "fig03_neyman_efficiency_vs_k.png")
    _plot_two_panels(
        all_df, "gap_fi", "gap_fo",
        "Gap fi (train − test)", "Gap fo (train − test)",
        "Brecha de generalización",
        FIG_DIR / "fig04_train_test_gap_vs_k.png", hline=0)

# ── Main ─────────────────────────────────────────────────────────────
def main():
    print("Loading metrics ...")
    all_df, found, missing = load_all()
    if all_df.empty:
        print("No metrics found. Run scripts 01-04 first.")
        return
    for t in found:
        sub = all_df[all_df["technique"] == t]
        print(f"  {t}: {len(sub)} configs, K={int(sub['K'].min())}"
              f"-{int(sub['K'].max())}")
    for t in missing:
        print(f"  {t}: MISSING")
    # Unified table
    show = [c for c in SHOW_COLS if c in all_df.columns]
    unified = all_df[show].copy()
    # Comparable K
    comp = comparable_k(all_df)
    comp_show = ["target_K"] + show
    comp_show = [c for c in comp_show if c in comp.columns]
    comp = comp[comp_show]
    # Figures
    print("Generating figures ...")
    make_figures(all_df)
    # Markdown
    lines = ["# Comparación de técnicas de estratificación\n"]
    lines.append("## Técnicas\n")
    lines.append(f"- Encontradas: {', '.join(found)}")
    if missing:
        lines.append(f"- Faltantes: {', '.join(missing)}")
    lines.append("")
    lines.append("## Tabla única — todas las configuraciones\n")
    lines.append(df_to_markdown(unified))
    lines.append("")
    lines.append("## Configuraciones de K comparable\n")
    lines.append(df_to_markdown(comp))
    lines.append("")
    lines.append("## Figuras\n")
    figs = [
        ("fig01_r2_fan_vs_k.png",
         "Varianza explicada de Fan-In y Fan-Out vs K"),
        ("fig02_r2_profile_vs_k.png",
         "Varianza explicada de n_versions y age vs K"),
        ("fig03_neyman_efficiency_vs_k.png",
         "Eficiencia de muestreo Neyman vs K"),
        ("fig04_train_test_gap_vs_k.png",
         "Brecha de generalización (train − test) vs K"),
    ]
    for fname, caption in figs:
        lines.append(f"### {caption}\n")
        lines.append(f"![{caption}](figures/{fname})\n")
    lines.append("## Notas\n")
    lines.append("- La cuadrícula y los cortes óptimos se arman con "
                 "Fan-In y Fan-Out, por eso su varianza explicada de "
                 "esas variables es alta por construcción.")
    lines.append("- El árbol usa log(1+Fan-In) y log(1+Fan-Out) como "
                 "objetivo.")
    lines.append("- La clusterización no usa Fan-In ni Fan-Out.")
    lines.append("- Todo es solo con el dataset B (sin familias).\n")
    write_results_md(TECHNIQUE, "\n".join(lines))
    print("Done.")

if __name__ == "__main__":
    main()
