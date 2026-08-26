import numpy as np
import pandas as pd
from sklearn.preprocessing import PolynomialFeatures
from sklearn.linear_model import LinearRegression

# ====================================================
# 1. LOAD THE DATA
# ====================================================
file_path = "batch_test_20260825_100749/emd_results.txt"

try:
    data = np.loadtxt(file_path, comments="#")
except FileNotFoundError:
    print(f"Error: Could not find '{file_path}'")
    exit(1)

# Extract variables
X_all = data[:, :7]
y = data[:, 7]

# Original 7 variables
x1 = X_all[:, 0]  # size of convective core (km)
x2 = X_all[:, 1]  # core ratio
x3 = X_all[:, 2]  # rain intensity (mm/hr)
x4 = X_all[:, 3]  # apparent motion (m/s)
x5 = X_all[:, 4]  # cloud base height (km)
x6 = X_all[:, 5]  # distance to C-band radar (km)
x7 = X_all[:, 6]  # storm duration (minutes)

n_total = len(y)
grand_mean = np.mean(y)
ss_total = np.sum((y - grand_mean) ** 2)

print("=" * 80)
print("  MAIN EFFECTS ANOVA FOR 7 FACTORS")
print("=" * 80)
print(f"\nModel: Y = β₀ + β₁x₁ + β₂x₂ + β₃x₃ + β₄x₄ + β₅x₅ + β₆x₆ + β₇x₇ + ε")
print(f"\nDesign: 3⁷ full factorial (7 factors, 3 levels each)")
print(f"Total runs: {n_total}")
print(f"Total Sum of Squares (SS_Total): {ss_total:.6f}")
print()

# ====================================================
# 2. CENTER THE VARIABLES (Effect Coding)
# ====================================================
x1_c = x1 - np.mean(x1)
x2_c = x2 - np.mean(x2)
x3_c = x3 - np.mean(x3)
x4_c = x4 - np.mean(x4)
x5_c = x5 - np.mean(x5)
x6_c = x6 - np.mean(x6)
x7_c = x7 - np.mean(x7)

# ====================================================
# 3. BUILD DESIGN MATRIX (Main Effects Only)
# ====================================================
X_model = np.column_stack([
    np.ones(n_total),  # Intercept
    x1_c,
    x2_c,
    x3_c,
    x4_c,
    x5_c,
    x6_c,
    x7_c
])

feature_names = ['Intercept', 'x1', 'x2', 'x3', 'x4', 'x5', 'x6', 'x7']

# ====================================================
# 4. FIT MODEL AND COMPUTE SS (Type III)
# ====================================================
# Fit full model
model = LinearRegression(fit_intercept=False)
model.fit(X_model, y)
y_pred = model.predict(X_model)

# Model SS
ss_model = np.sum((y_pred - grand_mean) ** 2)
ss_residual = ss_total - ss_model

# Compute SS for each main effect (Type III)
ss_effects = {}
df_effects = {}

# Full model residual
ss_full_residual = ss_residual

# For each main effect, remove it and see how much SS increases
for idx, name in enumerate(feature_names):
    if idx == 0:  # Skip intercept
        continue
    
    # Remove this term from the model
    cols_to_keep = [i for i in range(len(feature_names)) if i != idx]
    X_reduced = X_model[:, cols_to_keep]
    
    # Fit reduced model
    model_reduced = LinearRegression(fit_intercept=False)
    model_reduced.fit(X_reduced, y)
    y_pred_reduced = model_reduced.predict(X_reduced)
    
    # SS contributed by this term = increase in residual SS when term is removed
    ss_reduced_model = np.sum((y_pred_reduced - grand_mean) ** 2)
    ss_reduced_residual = ss_total - ss_reduced_model
    ss_term = ss_reduced_residual - ss_full_residual
    
    ss_effects[name] = ss_term
    df_effects[name] = 1

# Degrees of freedom for each factor (3 levels → 2 DF)
# Since we're using effect coding, each factor has 2 DF
for name in feature_names[1:]:
    df_effects[name] = 2

# ====================================================
# 5. DISPLAY ANOVA TABLE
# ====================================================
print("\n" + "=" * 80)
print("  ANOVA TABLE (Main Effects Only)")
print("=" * 80)
print(f"{'Source':<30} {'DF':<8} {'SS':<20} {'% of Total':<15} {'% of Model':<15}")
print("-" * 80)

# Variable names for display
var_display = {
    'x1': 'x₁ (core size)',
    'x2': 'x₂ (core ratio)',
    'x3': 'x₃ (rain intensity)',
    'x4': 'x₄ (motion)',
    'x5': 'x₅ (cloud height)',
    'x6': 'x₆ (distance)',
    'x7': 'x₇ (duration)'
}

# Order by SS (descending)
sorted_effects = sorted(ss_effects.items(), key=lambda x: x[1], reverse=True)

for name, ss in sorted_effects:
    df = df_effects[name]
    pct_total = ss / ss_total * 100
    pct_model = ss / ss_model * 100 if ss_model > 0 else 0
    display = var_display.get(name, name)
    print(f"{display:<30} {df:<8} {ss:<20.6f} {pct_total:<15.2f}% {pct_model:<15.2f}%")

# Residual
df_residual = n_total - len(feature_names)
print("-" * 80)
print(f"{'Residual':<30} {df_residual:<8} {ss_residual:<20.6f} {ss_residual/ss_total*100:<15.2f}% {'':<15}")
print("-" * 80)
print(f"{'Total':<30} {n_total - 1:<8} {ss_total:<20.6f} {100:<15.2f}% {'':<15}")

# ====================================================
# 6. MODEL STATISTICS
# ====================================================
r_squared = ss_model / ss_total
r_squared_adj = 1 - (1 - r_squared) * (n_total - 1) / (n_total - len(feature_names))

print("\n" + "=" * 80)
print("  MODEL STATISTICS")
print("=" * 80)
print(f"R² = {r_squared:.4f} ({r_squared*100:.2f}%)")
print(f"Adjusted R² = {r_squared_adj:.4f} ({r_squared_adj*100:.2f}%)")
print(f"Number of parameters: {len(feature_names)}")
print(f"Degrees of freedom residual: {df_residual}")

# ====================================================
# 7. MODEL COEFFICIENTS
# ====================================================
print("\n" + "=" * 80)
print("  MODEL COEFFICIENTS")
print("=" * 80)
print(f"{'Term':<20} {'Coefficient':<15} {'Std Error':<15} {'t-value':<15}")
print("-" * 80)

# Standard errors
residual_std = np.sqrt(ss_residual / df_residual)
X_inv = np.linalg.pinv(X_model.T @ X_model)
std_errors = np.sqrt(np.diag(X_inv) * ss_residual / df_residual)

for i, name in enumerate(feature_names):
    coef = model.coef_[i]
    se = std_errors[i]
    t_val = coef / se if se > 0 else 0
    print(f"{name:<20} {coef:<15.6f} {se:<15.6f} {t_val:<15.2f}")

# ====================================================
# 8. OPTIMAL CONFIGURATION (MINIMUM EMD)
# ====================================================
print("\n" + "=" * 80)
print("  OPTIMAL CONFIGURATION FOR MINIMUM EMD")
print("=" * 80)

# Combine all variables
X_transformed = np.column_stack([x1, x2, x3, x4, x5, x6, x7])
var_names = [
    "x₁ (core size)",
    "x₂ (core ratio)",
    "x₃ (rain intensity)",
    "x₄ (motion)",
    "x₅ (cloud height)",
    "x₆ (distance)",
    "x₇ (duration)"
]

# Level labels (from your 3⁷ design)
level_labels = [
    [5, 10, 15],     # x1: core size (km)
    [0.1, 0.3, 0.5], # x2: core ratio
    [20, 30, 40],    # x3: rain intensity (mm/hr)
    [3, 9, 15],      # x4: motion (m/s)
    [1, 2, 3],       # x5: cloud height (km)
    [20, 110, 200],  # x6: distance (km)
    [20, 35, 50]     # x7: duration (minutes)
]

optimal_config = []

for i in range(7):
    factor_col = X_transformed[:, i]
    unique_levels = np.unique(factor_col)
    
    best_lvl = None
    min_emd = float('inf')
    
    print(f"\n{var_names[i]} Level Response Profile:")
    # Sort levels to match labels
    sorted_indices = np.argsort(unique_levels)
    for j in sorted_indices:
        lvl = unique_levels[j]
        mean_emd = np.mean(y[factor_col == lvl])
        display_val = level_labels[i][j]
        print(f"  Level {display_val:<6} -> Mean EMD: {mean_emd:.6f}")
        if mean_emd < min_emd:
            min_emd = mean_emd
            best_lvl = display_val
    
    print(f"--> Optimal Setting: {best_lvl}")
    optimal_config.append(f"{var_names[i]} = {best_lvl}")

print("\n" + "=" * 80)
print("  RECOMMENDED OPTIMAL CONFIGURATION")
print("=" * 80)
for config in optimal_config:
    print(f"  {config}")

# ====================================================
# 9. SUMMARY OF VARIANCE EXPLAINED
# ====================================================
print("\n" + "=" * 80)
print("  SUMMARY OF VARIANCE EXPLAINED")
print("=" * 80)

print(f"Main effects (7 factors):       {ss_model:.6f} ({ss_model/ss_total*100:.2f}%)")

# Individual contributions
for name, ss in sorted_effects:
    display = var_display.get(name, name)
    print(f"  {display:<20} {ss:.6f} ({ss/ss_total*100:.2f}%)")

print(f"Residual:                       {ss_residual:.6f} ({ss_residual/ss_total*100:.2f}%)")
print("-" * 80)
print(f"Total:                          {ss_total:.6f} (100.00%)")

print("\n" + "=" * 80)
