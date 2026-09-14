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
    "X": "figures/cs_anova_10x10x10_X.txt",
    "C": "figures/cs_anova_10x10x10_C.txt",
}

# New variable names (mapped from old x3, x4, x5)
VAR_NAMES = [
    "x'1 (apparent motion) [old x3]",
    "x'2 (cloud base height) [old x4]",
    "x'3 (sub-cloud gradient) [old x5]",
]

# Old column indices: x3 -> index 2, x4 -> index 3, x5 -> index 4
OLD_INDICES = [2, 3, 4]


def build_effects_design(X_factors):
    """
    Build a design matrix containing:
      - intercept
      - 3 main effects (centered)
      - 3 two-way interactions (products of centered main effects)
      - 1 three-way interaction (product of all three centered main effects)
    Returns the design matrix and the effect names.
    """
    n = X_factors.shape[0]

    # Center each factor
    Xc = X_factors - X_factors.mean(axis=0)

    # Main effects
    mains = [Xc[:, i] for i in range(3)]

    # Two-way interactions
    two_way = []
    two_way_names = []
    for i, j in combinations(range(3), 2):
        two_way.append(mains[i] * mains[j])
        two_way_names.append(f"x'{i+1} * x'{j+1}")

    # Three-way interaction
    three_way = mains[0] * mains[1] * mains[2]

    # Assemble design matrix
    columns = [np.ones(n)] + mains + two_way + [three_way]
    X_model = np.column_stack(columns)

    effect_names = (
        ["Intercept"]
        + [f"x'{i+1} (main)" for i in range(3)]
        + two_way_names
        + ["x'1 * x'2 * x'3"]
    )

    return X_model, effect_names


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

        # Extract the three new factors (old x3, x4, x5) and the response
        X_factors = data[:, OLD_INDICES]
        y = data[:, 7]

        n_total = len(y)
        grand_mean = np.mean(y)
        ss_total = np.sum((y - grand_mean) ** 2)

        print("=" * 80)
        print(f"  10^3 FACTORIAL ANOVA — {band_label}-BAND")
        print("=" * 80)
        print(f"\nInput file: {input_file}")
        print(f"Total runs: {n_total}")
        print(f"Total Sum of Squares (SS_Total): {ss_total:.6f}")

        # Check design is balanced 10x10x10
        for i, name in enumerate(VAR_NAMES):
            levels = np.unique(X_factors[:, i])
            print(f"  {name}: {len(levels)} levels -> {levels}")
        print()

        # Build full model design matrix
        X_model, feature_names = build_effects_design(X_factors)

        # Full model
        model = LinearRegression(fit_intercept=False)
        model.fit(X_model, y)
        y_pred = model.predict(X_model)

        ss_model = np.sum((y_pred - grand_mean) ** 2)
        ss_residual = ss_total - ss_model
        ss_full_residual = ss_residual

        # Type III SS: drop one term at a time (excluding intercept)
        ss_effects = {}
        df_effects = {}

        # Degrees of freedom for each effect in a 10^3 design:
        #   main effect: (10-1) = 9
        #   two-way:     (10-1)*(10-1) = 81
        #   three-way:   (10-1)^3 = 729
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

            # Assign df based on effect type
            if "(main)" in name:
                df_effects[name] = 9
            elif "*" in name and name.count("*") == 1:
                df_effects[name] = 81
            else:
                df_effects[name] = 729

        # ANOVA table
        print("\n" + "=" * 80)
        print("  ANOVA TABLE (Main + Interaction Effects)")
        print("=" * 80)
        print(f"{'Source':<35} {'DF':<8} {'SS':<20} {'% of Total':<15} {'% of Model':<15}")
        print("-" * 80)

        sorted_effects = sorted(ss_effects.items(), key=lambda item: item[1], reverse=True)

        for name, ss in sorted_effects:
            df = df_effects[name]
            pct_total = ss / ss_total * 100 if ss_total > 0 else 0
            pct_model = ss / ss_model * 100 if ss_model > 0 else 0
            print(f"{name:<35} {df:<8} {ss:<20.6f} {pct_total:<15.2f}% {pct_model:<15.2f}%")

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

        # Grouped variance summary
        print("\n" + "=" * 80)
        print("  SUMMARY OF VARIANCE EXPLAINED (grouped)")
        print("=" * 80)

        main_total = sum(ss for name, ss in ss_effects.items() if "(main)" in name)
        two_way_total = sum(ss for name, ss in ss_effects.items()
                            if "*" in name and name.count("*") == 1)
        three_way_total = sum(ss for name, ss in ss_effects.items()
                              if name.count("*") == 2)

        print(f"Main effects (3 factors):       {main_total:.6f} "
              f"({main_total/ss_total*100:.2f}%)")
        for name, ss in sorted_effects:
            if "(main)" in name:
                print(f"  {name:<33} {ss:.6f} ({ss/ss_total*100:.2f}%)")

        print(f"\nTwo-way interactions (3):       {two_way_total:.6f} "
              f"({two_way_total/ss_total*100:.2f}%)")
        for name, ss in sorted_effects:
            if "*" in name and name.count("*") == 1:
                print(f"  {name:<33} {ss:.6f} ({ss/ss_total*100:.2f}%)")

        print(f"\nThree-way interaction (1):      {three_way_total:.6f} "
              f"({three_way_total/ss_total*100:.2f}%)")
        for name, ss in sorted_effects:
            if name.count("*") == 2:
                print(f"  {name:<33} {ss:.6f} ({ss/ss_total*100:.2f}%)")

        print(f"\nModel total:                    {ss_model:.6f} "
              f"({ss_model/ss_total*100:.2f}%)")
        print(f"Residual:                       {ss_residual:.6f} "
              f"({ss_residual/ss_total*100:.2f}%)")
        print("-" * 80)
        print(f"Total:                          {ss_total:.6f} (100.00%)")
        print("\n" + "=" * 80)

    finally:
        sys.stdout = original_stdout
        log_file.close()


if __name__ == "__main__":
    os.makedirs("figures", exist_ok=True)

    for band in ["X", "C"]:
        print(f"Running 10^3 factorial ANOVA for {band}-band...")
        run_anova(FILES[band], LOGS[band], band)
        print(f"  → saved to {LOGS[band]}")

    print("Done.")
