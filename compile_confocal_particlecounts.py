"""
Created on Wed Mar 25 2026 using ChatGPT prompting
@author: cariefrantz

Compiles analyzed particle counts from confocal images
(from https://github.com/cmfrantz/lab/blob/main/confocal_batch_particlecount.ijm)
and runs summary statistics and creates summary plots.

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>
    
"""

import pandas as pd
import numpy as np
import os
import re
from glob import glob
import tkinter as tk
from tkinter import filedialog
import seaborn as sns
import matplotlib.pyplot as plt
from scipy import stats
import statsmodels.api as sm
from statsmodels.stats.multicomp import pairwise_tukeyhsd

# ==============================
# 1. FILE SELECTION GUI
# ==============================
root = tk.Tk()
root.withdraw()

print("Select directory containing particle count CSV files")
data_dir = filedialog.askdirectory(title="Select Particle Counts Directory")

print("Select metadata CSV file")
metadata_path = filedialog.askopenfilename(title="Select Metadata CSV")

print("Select output directory")
output_dir = filedialog.askdirectory(title="Select Output Directory")
if not output_dir:
    raise ValueError("No output directory selected")
# Create subfolders
plots_dir = os.path.join(output_dir, "plots")
os.makedirs(plots_dir, exist_ok=True)

# ==============================
# 2. LOAD AND COMBINE CSV FILES
# ==============================
csv_files = glob(os.path.join(data_dir, "*.csv"))

dfs = []

for file in csv_files:
    try:
        df = pd.read_csv(file)
    except:
        print(f"Skipping unreadable file: {file}")
        continue

    df.columns = df.columns.str.strip()

    if "Type" not in df.columns or "Area" not in df.columns:
        print(f"Skipping invalid file: {file}")
        continue

    df["Type"] = df["Type"].str.lower().str.strip()

    base = os.path.basename(file).replace(".csv", "")
    df["filename"] = base

    dfs.append(df)

combined = pd.concat(dfs, ignore_index=True)

# ==============================
# 3. PARSE IMAGE NAME
# ==============================
def parse_name(name):
    match = re.search(r"_R(\d+)", name)

    if match:
        random_image = match.group(1)
        sample = name[:match.start()]
    else:
        random_image = None
        sample = name

    return pd.Series({
        "sample": sample,
        "randomImage": random_image
    })

meta = combined["filename"].apply(parse_name)
combined = pd.concat([combined, meta], axis=1)

# ==============================
# 4. LOAD AND MERGE METADATA
# ==============================
meta_df = pd.read_csv(metadata_path)
meta_df.columns = meta_df.columns.str.strip()

#REQUIRED COLUMNS
required_cols = ["sampleID", "sample"]
for col in required_cols:
    if col not in meta_df.columns:
        raise ValueError(f"Metadata must contain column: {col}")

# Clean join columns
meta_df["sampleID"] = meta_df["sampleID"].astype(str).str.strip()
combined["sample"] = combined["sample"].astype(str).str.strip()

# Merge: sampleID ↔ parsed sample
combined = combined.merge(
    meta_df,
    left_on="sample",
    right_on="sampleID",
    how="left"
)

print("Metadata merged")

# Preserve plotting order from metadata
sample_order = meta_df["sample"].drop_duplicates().tolist()

# Use metadata "sample" for grouping + plotting
combined["sample"] = pd.Categorical(
    combined["sample_y"],   # metadata sample
    categories=sample_order,
    ordered=True
)

# Rename for clarity
combined = combined.rename(columns={"sample_x": "parsedSample"})
combined = combined.drop(columns=["sample_y"])


# ==============================
# 5. PER-IMAGE COUNTS
# ==============================
counts = (
    combined
    .groupby(["sample", "randomImage"])
    .apply(lambda df: pd.Series({
        "fibers": (df["Type"] == "fibers").sum(),
        "fragments": (df["Type"] == "fragments").sum(),
        "particles": (df["Type"] == "particles").sum(),
        "total_particles": len(df),
        "area_total": df["Area"].sum(),
        "area_fibers": df.loc[df["Type"] == "fibers", "Area"].sum(),
        "area_fragments": df.loc[df["Type"] == "fragments", "Area"].sum(),
        "area_particles": df.loc[df["Type"] == "particles", "Area"].sum(),
    }))
    .reset_index()
)

# Add metadata again to counts
counts = counts.merge(meta_df, on="sample", how="left")

counts["sample"] = pd.Categorical(
    counts["sample"],
    categories=sample_order,
    ordered=True
)

# ==============================
# 6. SUMMARY STATISTICS
# ==============================
def mode_safe(x):
    m = x.mode()
    return m.iloc[0] if not m.empty else np.nan

summary = (
    counts
    .groupby(["sample"])
    .agg({
        "fibers": ["sum", "mean", "median", mode_safe, "min", "max"],
        "fragments": ["sum", "mean", "median", mode_safe, "min", "max"],
        "particles": ["sum", "mean", "median", mode_safe, "min", "max"],
        "total_particles": ["sum", "mean", "median", mode_safe, "min", "max"],
        "area_fibers": ["sum", "mean", "median", mode_safe, "min", "max"],
        "area_fragments": ["sum", "mean", "median", mode_safe, "min", "max"],
        "area_particles": ["sum", "mean", "median", mode_safe, "min", "max"],
        "area_total": ["sum", "mean", "median", mode_safe, "min", "max"],
    })
)

summary.columns = [
    f"{col[0]}_{col[1] if isinstance(col[1], str) else 'mode'}"
    for col in summary.columns
]

summary = summary.reset_index()


# ==============================
# 7. STATISTICAL TESTS
# ==============================

# ANOVA and turkey tests
def run_anova_and_tukey(data, metric):

    df = data[["sample", metric]].dropna()

    groups = [group[metric].values for name, group in df.groupby("sample")]

    f_stat, p_val = stats.f_oneway(*groups)

    # Tukey
    tukey = pairwise_tukeyhsd(
        endog=df[metric],
        groups=df["sample"],
        alpha=0.05
    )

    tukey_df = pd.DataFrame(
        data=tukey._results_table.data[1:],
        columns=tukey._results_table.data[0]
    )

    tukey_df["metric"] = metric

    return f_stat, p_val, tukey_df

# Significance labels
def get_sig_label(p):
    if p < 0.001:
        return "***"
    elif p < 0.01:
        return "**"
    elif p < 0.05:
        return "*"
    else:
        return ""



# ==============================
# 9. PLOTTING
# ==============================
plot_dir = os.path.join(output_dir, "plots")
os.makedirs(plot_dir, exist_ok=True)

plot_dir_clean = os.path.join(plot_dir, "clean")
plot_dir_stats = os.path.join(plot_dir, "with_stats")

os.makedirs(plot_dir_clean, exist_ok=True)
os.makedirs(plot_dir_stats, exist_ok=True)

anova_results = []
tukey_results_all = []

sns.set(style="whitegrid")

metrics = [
    "fibers", "fragments", "particles", "total_particles",
    "area_fibers", "area_fragments", "area_particles", "area_total"
]

for metric in metrics:

    # --------------------------
    # RUN STATS
    # --------------------------
    f_stat, p_val, tukey_df = run_anova_and_tukey(counts, metric)

    anova_results.append({
        "metric": metric,
        "F_stat": f_stat,
        "p_value": p_val
    })

    tukey_results_all.append(tukey_df)

    # ==========================
    # CLEAN PLOT (NO STATS)
    # ==========================
    plt.figure()

    sns.boxplot(
        data=counts,
        x="sample",
        y=metric,
        order=sample_order
    )

    sns.stripplot(
        data=counts,
        x="sample",
        y=metric,
        order=sample_order,
        color="black",
        size=4,
        jitter=True
    )

    plt.xticks(rotation=45)
    plt.title(metric)
    plt.tight_layout()

    plt.savefig(os.path.join(plot_dir_clean, f"{metric}_boxplot.png"), dpi=300)
    plt.close()

    # ==========================
    # STATS PLOT
    # ==========================
    plt.figure()

    sns.boxplot(
        data=counts,
        x="sample",
        y=metric,
        order=sample_order
    )

    sns.stripplot(
        data=counts,
        x="sample",
        y=metric,
        order=sample_order,
        color="black",
        size=4,
        jitter=True
    )

    sig_pairs = tukey_df[tukey_df["reject"] == True]

    y_max = counts[metric].max()
    y_offset = y_max * 0.1

    for i, row in sig_pairs.iterrows():

        group1 = row["group1"]
        group2 = row["group2"]
        p_adj = row["p-adj"]

        label = get_sig_label(p_adj)
        if label == "":
            continue

        x1 = sample_order.index(group1)
        x2 = sample_order.index(group2)

        y = y_max + (i + 1) * y_offset

        plt.plot([x1, x1, x2, x2],
                 [y, y + y_offset, y + y_offset, y],
                 lw=1.5)

        plt.text((x1 + x2) / 2, y + y_offset,
                 label, ha='center')

    plt.xticks(rotation=45)
    plt.title(f"{metric} (ANOVA p={p_val:.3e})")
    plt.tight_layout()

    plt.savefig(os.path.join(plot_dir_stats, f"{metric}_boxplot.png"), dpi=300)
    plt.close()


# ==============================
# 11.  STACKED BARPLOTS (TOTAL AND %)
# ==============================

plot_configs = [
    {
        "name": "count",
        "columns": ["fibers", "fragments", "particles"],
        "ylabel": "Count"
    },
    {
        "name": "area",
        "columns": ["area_fibers", "area_fragments", "area_particles"],
        "ylabel": "Total Area"
    }
]

# Optional consistent colors
colors = ["#4CAF50", "#2196F3", "#FF9800"]  # fibers, fragments, particles

for config in plot_configs:

    # --------------------------
    # Aggregate data
    # --------------------------
    data = counts.groupby("sample")[config["columns"]].sum()

    data = data.loc[sample_order]

    # Rename columns for consistency in legend
    data.columns = ["fibers", "fragments", "particles"]

    # --------------------------
    # LOOP: raw + normalized
    # --------------------------
    for mode in ["raw", "percent"]:

        if mode == "percent":
            plot_data = data.div(data.sum(axis=1), axis=0) * 100
            ylabel = "Percent (%)"
            suffix = "_percent"
        else:
            plot_data = data
            ylabel = config["ylabel"]
            suffix = ""

        # --------------------------
        # Plot
        # --------------------------
        plot_data.plot(
            kind="bar",
            stacked=True,
            figsize=(10, 6),
            color=colors
        )

        plt.xticks(rotation=45)
        plt.ylabel(ylabel)
        plt.title(f"Microplastic Composition by Sample ({config['name']} - {mode})")
        plt.legend(["Fibers", "Fragments", "Particles"], title="Type")
        plt.tight_layout()

        filename = f"stacked_barplot_{config['name']}{suffix}.png"
        plt.savefig(os.path.join(plot_dir, filename), dpi=300)

        plt.close()
        
        
        
# ==============================
# 8. SAVE OUTPUTS
# ==============================
output_base = os.path.join(output_dir, "compiled_results")

combined.to_csv(output_base + ".csv", index=False)
    
anova_df = pd.DataFrame(anova_results)
tukey_df_all = pd.concat(tukey_results_all, ignore_index=True)

with pd.ExcelWriter(output_base + ".xlsx") as writer:
    combined.to_excel(writer, sheet_name="All_Data", index=False)
    summary.to_excel(writer, sheet_name="Summary_Stats", index=False)
    anova_df.to_excel(writer, sheet_name="ANOVA", index=False)
    tukey_df_all.to_excel(writer, sheet_name="Tukey_HSD", index=False)

print("Results saved.")n .
print("Pipeline complete!")