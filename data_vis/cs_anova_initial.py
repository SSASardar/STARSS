import numpy as np
from sklearn.linear_model import LinearRegression
import sys
import os

# ====================================================
# CONFIGURATION
# ====================================================
BATCH_FOLDER = "batch_test_20260911_151338"

FILES = {
    "X": f"{BATCH_FOLDER}/results_sums_X.txt",
    "C": f"{BATCH_FOLDER}/results_sums_C.txt",
}

LOGS = {
    "X": "figures/cs_anova_initial_X.txt",
    "C": "figures/cs_anova_initial_C.txt",
}

VAR_NAMES = [
    "x1 (convective core radius)",
    "x2 (max rain intensity)",
    "x3 (apparent motion)",
    "x4 (cloud base height)",
    "x5 (sub-cloud gradient)",
    "x6 (distance to C-band)",
    "x7 (storm duration)",
]


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

        X_all = data[:, :7]
        y = data[:, 7]

        n_total = len(y)
        grand_mean = np.mean(y)
        ss_total = np.sum((y - grand_mean) ** 2)

        print("=" * 80)
        print(f"  MAIN EFFECTS ANOVA — {band_label}-BAND")
        print("=" * 80)
        print(f"\nInput file: {input_file}")
        print(f"Total runs: {n_total}")
        print(f"Total Sum of Squares (SS_Total): {ss_total:.6f}")
        print()

        # Center the variables
        Xc = X_all - X_all.mean(axis=0)

        # Design matrix (intercept + 7 main effects)
        X_model = np.column_stack([np.ones(n_total), Xc])
        feature_names = ['Intercept', 'x1', 'x2', 'x3', 'x4', 'x5', 'x6', 'x7']

        # Full model
        model = LinearRegression(fit_intercept=False)
        model.fit(X_model, y)
        y_pred = model.predict(X_model)

        ss_model = np.sum((y_pred - grand_mean) ** 2)
        ss_residual = ss_total - ss_model
        ss_full_residual = ss_residual

        ss_effects = {}
        df_effects = {}

        # Type III SS: drop one term at a time
        for idx, name in enumerate(feature_names):
            if idx == 0:
                continue
            cols_to_keep = [i for i in range(len(feature_names)) if i != idx]
            X_reduced = X_model[:, cols_to_keep]

            model_reduced = LinearRegression(fit_intercept=False)
            model_reduced.fit(X_reduced, y)
            y_pred_reduced = model_reduced.predict(X_reduced)

            ss_reduced_model = np.sum((y_pred_reduced - grand_mean) ** 2)
            ss_reduced_residual = ss_total - ss_reduced_model
            ss_effects[name] = ss_reduced_residual - ss_full_residual
            df_effects[name] = 2  # 3 levels per factor

        # ANOVA table
        print("\n" + "=" * 80)
        print("  ANOVA TABLE (Main Effects Only)")
        print("=" * 80)
        print(f"{'Source':<35} {'DF':<8} {'SS':<20} {'% of Total':<15} {'% of Model':<15}")
        print("-" * 80)

        var_display = {f'x{i+1}': VAR_NAMES[i] for i in range(7)}
        sorted_effects = sorted(ss_effects.items(), key=lambda item: item[1], reverse=True)

        for name, ss in sorted_effects:
            df = df_effects[name]
            pct_total = ss / ss_total * 100 if ss_total > 0 else 0
            pct_model = ss / ss_model * 100 if ss_model > 0 else 0
            print(f"{var_display[name]:<35} {df:<8} {ss:<20.6f} {pct_total:<15.2f}% {pct_model:<15.2f}%")

        df_residual = n_total - len(feature_names)
        print("-" * 80)
        print(f"{'Residual':<35} {df_residual:<8} {ss_residual:<20.6f} "
              f"{ss_residual/ss_total*100:<15.2f}%")
        print("-" * 80)
        print(f"{'Total':<35} {n_total - 1:<8} {ss_total:<20.6f} {100:<15.2f}%")

        # Model statistics
        r_squared = ss_model / ss_total if ss_total > 0 else 0
        r_squared_adj = 1 - (1 - r_squared) * (n_total - 1) / (n_total - len(feature_names))

        print("\n" + "=" * 80)
        print("  MODEL STATISTICS")
        print("=" * 80)
        print(f"R² = {r_squared:.4f} ({r_squared*100:.2f}%)")
        print(f"Adjusted R² = {r_squared_adj:.4f} ({r_squared_adj*100:.2f}%)")
        print(f"Number of parameters: {len(feature_names)}")
        print(f"Degrees of freedom residual: {df_residual}")

        # Optimal configuration
        print("\n" + "=" * 80)
        print("  OPTIMAL CONFIGURATION FOR MINIMUM DISCREPANCY")
        print("=" * 80)

        optimal_config = []
        for i in range(7):
            factor_col = X_all[:, i]
            levels = np.unique(factor_col)

            best_lvl = None
            min_disc = float('inf')

            print(f"\n{VAR_NAMES[i]} Level Response Profile:")
            for lvl in levels:
                mean_disc = np.mean(y[factor_col == lvl])
                print(f"  Level {lvl:<8} -> Mean Discrepancy: {mean_disc:.6f}")
                if mean_disc < min_disc:
                    min_disc = mean_disc
                    best_lvl = lvl

            print(f"--> Optimal Setting: {best_lvl}")
            optimal_config.append(f"{VAR_NAMES[i]} = {best_lvl}")

        print("\n" + "=" * 80)
        print("  RECOMMENDED OPTIMAL CONFIGURATION")
        print("=" * 80)
        for config in optimal_config:
            print(f"  {config}")

        # Summary
        print("\n" + "=" * 80)
        print("  SUMMARY OF VARIANCE EXPLAINED")
        print("=" * 80)
        print(f"Main effects (7 factors):       {ss_model:.6f} ({ss_model/ss_total*100:.2f}%)")
        for name, ss in sorted_effects:
            print(f"  {var_display[name]:<35} {ss:.6f} ({ss/ss_total*100:.2f}%)")
        print(f"Residual:                       {ss_residual:.6f} ({ss_residual/ss_total*100:.2f}%)")
        print("-" * 80)
        print(f"Total:                          {ss_total:.6f} (100.00%)")
        print("\n" + "=" * 80)

    finally:
        sys.stdout = original_stdout
        log_file.close()


if __name__ == "__main__":
    os.makedirs("figures", exist_ok=True)

    for band in ["X", "C"]:
        print(f"Running ANOVA for {band}-band...")
        run_anova(FILES[band], LOGS[band], band)
        print(f"  → saved to {LOGS[band]}")

    print("Done.")
