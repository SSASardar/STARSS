"""
anova_quadratic_model.py
Fits the quadratic response-surface model with interactions:

    Y' = b0 + sum_i bi*xi + sum_{j>i} bij*xi*xj + sum_i bii*xi^2
         + x1*x2*x3 + eps

for both X-band and C-band separately, and produces an ANOVA table
with linear/quadratic decomposition of each main effect (like a
classical response-surface ANOVA).
"""

import numpy as np
from sklearn.linear_model import LinearRegression
import sys
import os
from itertools import combinations

# ====================================================
# CONFIGURATION
# ====================================================
BATCH_FOLDER = "batch_test_20260914_110306"

FILES = {
    "X": f"{BATCH_FOLDER}/results_sums_X.txt",
    "C": f"{BATCH_FOLDER}/results_sums_C.txt",
}

LOGS = {
    "X": "figures/cs_anova_quadratic_X.txt",
    "C": "figures/cs_anova_quadratic_C.txt",
}

# Variable names (mapped from old x3, x4, x5)
VAR_NAMES = [
    "x'1 (apparent motion) [old x3]",
    "x'2 (cloud base height) [old x4]",
    "x'3 (sub-cloud gradient) [old x5]",
]

# Old column indices: x3 -> 2, x4 -> 3, x5 -> 4
OLD_INDICES = [2, 3, 4]


# ====================================================
# HELPERS
# ====================================================
def build_quadratic_design(X_factors):
    """
    Build the design matrix for:
       intercept
       + 3 linear terms (centered)
       + 3 quadratic terms (squared centered linear terms)
       + 3 two-way interactions (products of centered linear terms)
       + 1 three-way interaction

    Returns:
       X_model : (n, 11) design matrix
       feature_names : list of column names
       blocks : dict mapping block name -> list of column indices
    """
    n = X_factors.shape[0]
    Xc = X_factors - X_factors.mean(axis=0)   # center

    # Linear terms
    lin_cols = [Xc[:, i] for i in range(3)]

    # Quadratic terms
    quad_cols = [Xc[:, i] ** 2 for i in range(3)]

    # Two-way interactions
    two_way_cols = []
    two_way_names = []
    for i, j in combinations(range(3), 2):
        two_way_cols.append(Xc[:, i] * Xc[:, j])
        two_way_names.append(f"x{i+1}:x{j+1}")

    # Three-way interaction
    three_way_col = Xc[:, 0] * Xc[:, 1] * Xc[:, 2]

    # Assemble
    columns = [np.ones(n)] + lin_cols + quad_cols + two_way_cols + [three_way_col]
    X_model = np.column_stack(columns)

    feature_names = (
        ["Intercept"]
        + [f"x{i+1} (linear)" for i in range(3)]
        + [f"x{i+1} (quadratic)" for i in range(3)]
        + two_way_names
        + ["x1:x2:x3"]
    )

    # Column index blocks for SS extraction
    blocks = {
        "x1_linear":      [1],
        "x2_linear":      [2],
        "x3_linear":      [3],
        "x1_quadratic":   [4],
        "x2_quadratic":   [5],
        "x3_quadratic":   [6],
        "x1_x2":          [7],
        "x1_x3":          [8],
        "x2_x3":          [9],
        "x1_x2_x3":       [10],
    }
    return X_model, feature_names, blocks


def ss_for_columns(X_model, y, col_indices, grand_mean):
    """
    Compute the sum of squares attributable to a set of columns
    (marginal, ignoring other columns). Used here as a
    sequential/hierarchical SS for small effect blocks.
    """
    if not col_indices:
        return 0.0
    X_sub = X_model[:, col_indices]
    model = LinearRegression(fit_intercept=False)
    model.fit(X_sub, y)
    y_pred = model.predict(X_sub)
    ss_model = np.sum((y_pred - grand_mean) ** 2)
    return ss_model


def run_anova(input_file, log_file_path, band_label):
    original_stdout = sys.stdout
    log_file = open(log_file_path, "w")
    sys.stdout = log_file

    try:
        if not os.path.exists(input_file):
            print(f"Error: Could not find '{input_file}'")
            return

        data = np.loadtxt(input_file, comments="#")
        if data.ndim == 1:
            data = data.reshape(1, -1)

        X_factors = data[:, OLD_INDICES]
        y = data[:, 7]

        n_total = len(y)
        grand_mean = np.mean(y)
        ss_total = np.sum((y - grand_mean) ** 2)

        print("=" * 80)
        print(f"  QUADRATIC RESPONSE-SURFACE ANOVA - {band_label}-BAND")
        print("=" * 80)
        print(f"\nInput file: {input_file}")
        print(f"Total runs: {n_total}")
        print(f"Total Sum of Squares (SS_Total): {ss_total:.6f}")

        for i, name in enumerate(VAR_NAMES):
            levels = np.unique(X_factors[:, i])
            print(f"  {name}: {len(levels)} unique values -> {levels}")
        print()

        # ----- Build the model -----
        X_model, feature_names, blocks = build_quadratic_design(X_factors)

        # Full model fit
        model_full = LinearRegression(fit_intercept=False)
        model_full.fit(X_model, y)
        y_pred = model_full.predict(X_model)
        ss_model = np.sum((y_pred - grand_mean) ** 2)
        ss_residual = ss_total - ss_model

        n_params = X_model.shape[1]
        df_residual = n_total - n_params

        # ----- Hierarchical SS: fit incrementally -----
        # Order: linear, quadratic, two-way, three-way
        ordered_blocks = [
            ("x1_linear",      ["x1_linear"]),
            ("x2_linear",      ["x2_linear"]),
            ("x3_linear",      ["x3_linear"]),
            ("x1_quadratic",   ["x1_quadratic"]),
            ("x2_quadratic",   ["x2_quadratic"]),
            ("x3_quadratic",   ["x3_quadratic"]),
            ("x1_x2",          ["x1_x2"]),
            ("x1_x3",          ["x1_x3"]),
            ("x2_x3",          ["x2_x3"]),
            ("x1_x2_x3",       ["x1_x2_x3"]),
        ]

        current_cols = [0]  # intercept
        prev_ss = 0.0
        ss_effects = {}
        for block_label, block_keys in ordered_blocks:
            new_cols = current_cols + [c for k in block_keys for c in blocks[k]]
            ss_now = ss_for_columns(X_model, y, new_cols, grand_mean)
            ss_effects[block_label] = ss_now - prev_ss
            prev_ss = ss_now
            current_cols = new_cols

        # ----- Grouped totals -----
        lin_x1  = ss_effects["x1_linear"]
        lin_x2  = ss_effects["x2_linear"]
        lin_x3  = ss_effects["x3_linear"]
        quad_x1 = ss_effects["x1_quadratic"]
        quad_x2 = ss_effects["x2_quadratic"]
        quad_x3 = ss_effects["x3_quadratic"]

        main_x1 = lin_x1 + quad_x1
        main_x2 = lin_x2 + quad_x2
        main_x3 = lin_x3 + quad_x3

        inter_x1x2 = ss_effects["x1_x2"]
        inter_x1x3 = ss_effects["x1_x3"]
        inter_x2x3 = ss_effects["x2_x3"]
        inter_3way = ss_effects["x1_x2_x3"]

        total_interactions = inter_x1x2 + inter_x1x3 + inter_x2x3 + inter_3way

        def pct(x):
            return 100.0 * x / ss_total if ss_total > 0 else 0.0

        def pct_model(x):
            return 100.0 * x / ss_model if ss_model > 0 else 0.0

        # ----- Print ANOVA table -----
        print("=" * 80)
        print("  ANOVA TABLE (Quadratic + Interactions, hierarchical SS)")
        print("=" * 80)
        header = f"{'Source':<35} {'DF':<6} {'SS':<18} {'% of Total':<14} {'% of Model':<14}"
        print(header)
        print("-" * 80)

        # x1 block
        print(f"{'x1':<35} {2:<6} {main_x1:<18.6f} {pct(main_x1):<14.2f}% {pct_model(main_x1):<14.2f}%")
        print(f"{'    Linear':<35} {1:<6} {lin_x1:<18.6f} {pct(lin_x1):<14.2f}% {pct_model(lin_x1):<14.2f}%")
        print(f"{'    Quadratic':<35} {1:<6} {quad_x1:<18.6f} {pct(quad_x1):<14.2f}% {pct_model(quad_x1):<14.2f}%")
        print("-" * 80)

        # x2 block
        print(f"{'x2':<35} {2:<6} {main_x2:<18.6f} {pct(main_x2):<14.2f}% {pct_model(main_x2):<14.2f}%")
        print(f"{'    Linear':<35} {1:<6} {lin_x2:<18.6f} {pct(lin_x2):<14.2f}% {pct_model(lin_x2):<14.2f}%")
        print(f"{'    Quadratic':<35} {1:<6} {quad_x2:<18.6f} {pct(quad_x2):<14.2f}% {pct_model(quad_x2):<14.2f}%")
        print("-" * 80)

        # x3 block
        print(f"{'x3':<35} {2:<6} {main_x3:<18.6f} {pct(main_x3):<14.2f}% {pct_model(main_x3):<14.2f}%")
        print(f"{'    Linear':<35} {1:<6} {lin_x3:<18.6f} {pct(lin_x3):<14.2f}% {pct_model(lin_x3):<14.2f}%")
        print(f"{'    Quadratic':<35} {1:<6} {quad_x3:<18.6f} {pct(quad_x3):<14.2f}% {pct_model(quad_x3):<14.2f}%")
        print("-" * 80)

        # Interactions
        print(f"{'Interactions':<35} {5:<6} {total_interactions:<18.6f} "
              f"{pct(total_interactions):<14.2f}% {pct_model(total_interactions):<14.2f}%")
        print(f"{'    x1:x2':<35} {1:<6} {inter_x1x2:<18.6f} "
              f"{pct(inter_x1x2):<14.2f}% {pct_model(inter_x1x2):<14.2f}%")
        print(f"{'    x1:x3':<35} {1:<6} {inter_x1x3:<18.6f} "
              f"{pct(inter_x1x3):<14.2f}% {pct_model(inter_x1x3):<14.2f}%")
        print(f"{'    x2:x3':<35} {1:<6} {inter_x2x3:<18.6f} "
              f"{pct(inter_x2x3):<14.2f}% {pct_model(inter_x2x3):<14.2f}%")
        print(f"{'    x1:x2:x3':<35} {1:<6} {inter_3way:<18.6f} "
              f"{pct(inter_3way):<14.2f}% {pct_model(inter_3way):<14.2f}%")
        print("-" * 80)

        # Residuals / Total
        print(f"{'Residuals':<35} {df_residual:<6} {ss_residual:<18.6f} "
              f"{pct(ss_residual):<14.2f}%")
        print("-" * 80)
        print(f"{'Total':<35} {n_total - 1:<6} {ss_total:<18.6f} {100.00:<14.2f}%")
        print("=" * 80)

        # ----- Model statistics -----
        r2 = ss_model / ss_total if ss_total > 0 else 0.0
        r2_adj = 1 - (1 - r2) * (n_total - 1) / df_residual if df_residual > 0 else 0.0

        print("\n" + "=" * 80)
        print("  MODEL STATISTICS")
        print("=" * 80)
        print(f"R^2             = {r2:.4f} ({r2*100:.2f}%)")
        print(f"Adjusted R^2    = {r2_adj:.4f} ({r2_adj*100:.2f}%)")
        print(f"Parameters      = {n_params}")
        print(f"df residual     = {df_residual}")
        print(f"df model        = {n_params - 1}")
        print("=" * 80)

    finally:
        sys.stdout = original_stdout
        log_file.close()


if __name__ == "__main__":
    os.makedirs("figures", exist_ok=True)

    for band in ["X", "C"]:
        print(f"Fitting quadratic ANOVA for {band}-band...")
        run_anova(FILES[band], LOGS[band], band)
        print(f"  -> saved to {LOGS[band]}")

    print("Done.")
