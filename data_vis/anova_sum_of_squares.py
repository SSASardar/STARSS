import numpy as np

# Since your script and file are both in 'data_vis/', use a direct local string name
file_path = "batch_test_20260825_100749/emd_results.txt"

try:
    # 1. Load the text data (NumPy automatically ignores your '#' headers)
    data = np.loadtxt(file_path, comments="#")
except FileNotFoundError:
    print(f"Error: Could not find '{file_path}' in the current working directory.")
    print("Please verify your script is running inside the 'data_vis' directory.")
    exit(1)

# Split into factor matrix (columns 1 to 7) and target metric vector
X = data[:, :7]
y = data[:, 7]

n_total = len(y)
grand_mean = np.mean(y)

# Total Sum of Squares (Total Variation)
ss_total = np.sum((y - grand_mean) ** 2)

print(f"Loaded {n_total} lines from {file_path}.\n")
print(f"{'Factor':<10}{'DF':<6}{'Sum of Squares (SS)':<22}{'Variance Explained (%)':<20}")
print("-" * 60)

ss_factors = []
df_factors = []

# 2. Compute Sum of Squares (SS) and Degrees of Freedom (DF) for each factor
for i in range(7):
    factor_col = X[:, i]
    unique_levels = np.unique(factor_col)
    df_f = len(unique_levels) - 1
    df_factors.append(df_f)
    
    ss_f = 0
    for lvl in unique_levels:
        mask = (factor_col == lvl)
        lvl_mean = np.mean(y[mask])
        n_lvl = np.sum(mask)
        ss_f += n_lvl * (lvl_mean - grand_mean) ** 2
        
    ss_factors.append(ss_f)

# 3. Residual Error calculations (Residuals capture all multi-way interactions)
ss_residual = ss_total - sum(ss_factors)
df_residual = n_total - 1 - sum(df_factors)

# 4. Calculate variance percentages
ss_model = sum(ss_factors)
variance_percentages = [ (ss / ss_total) * 100 for ss in ss_factors ]
residual_percent = (ss_residual / ss_total) * 100

# 5. Generate and display the Main Effects ANOVA table (NO F or p-values!)
for i in range(7):
    # Print with percentage of total variance
    print(f"x{i+1:<9}{df_factors[i]:<6}{ss_factors[i]:<22.6f}{variance_percentages[i]:<20.2f}%")

# Residual Row
print(f"{'Residuals':<10}{df_residual:<6}{ss_residual:<22.6f}{residual_percent:<20.2f}%")
print("-" * 60)

# 6. Model Summary
print(f"\nMODEL SUMMARY:")
print(f"  Total Sum of Squares: {ss_total:.6f}")
print(f"  Model Sum of Squares: {ss_model:.6f} ({ (ss_model/ss_total)*100:.2f}% of total)")
print(f"  Residual Sum of Squares: {ss_residual:.6f} ({residual_percent:.2f}% of total)")

# 7. Extract system-wide sweet spots (Level values that minimize EMD)
print("\n================ SYSTEM SWEET SPOTS (MINIMUM EMD) ================")
optimal_configuration = []

for i in range(7):
    factor_col = X[:, i]
    unique_levels = np.unique(factor_col)
    
    best_lvl = None
    min_emd = float('inf')
    
    print(f"\nFactor x{i+1} Level Response Profile:")
    for lvl in unique_levels:
        mean_emd = np.mean(y[factor_col == lvl])
        print(f"  Level {int(lvl):<5} -> Mean EMD: {mean_emd:.6f}")
        if mean_emd < min_emd:
            min_emd = mean_emd
            best_lvl = int(lvl)
            
    print(f"--> Optimal Setting for x{i+1}: {best_lvl}")
    optimal_configuration.append(f"x{i+1}={best_lvl}")

print("\n------------------------------------------------------------------")
print(f"Global Optimized Run Profile Recommendation: {', '.join(optimal_configuration)}")
print("------------------------------------------------------------------")

# ============================================================================
# OPTIONAL: R² Statistic for Main Effects Model
# ============================================================================
r_squared = ss_model / ss_total
r_squared_adjusted = 1 - (1 - r_squared) * (n_total - 1) / (n_total - sum(df_factors) - 1)

print(f"\nR² STATISTICS (Main Effects Model):")
print(f"  R² = {r_squared:.4f} ({r_squared*100:.2f}% of variance explained)")
print(f"  Adjusted R² = {r_squared_adjusted:.4f} ({r_squared_adjusted*100:.2f}%)")
