import numpy as np
import scipy.stats as stats

# Since your script and file are both in 'data_vis/', use a direct local string name
file_path = "batch_test_20260820_142437/avg_mse_results.txt"

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
print(f"{'Factor':<10}{'DF':<6}{'Sum of Squares (SS)':<22}{'Mean Square (MS)':<18}{'F-value':<12}{'p-value'}")
print("-" * 78)

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
ms_residual = ss_residual / df_residual

# 4. Generate and display the Main Effects ANOVA table rows
for i in range(7):
    ms_f = ss_factors[i] / df_factors[i]
    f_val = ms_f / ms_residual
    p_val = 1 - stats.f.cdf(f_val, df_factors[i], df_residual)
    
    print(f"x{i+1:<9}{df_factors[i]:<6}{ss_factors[i]:<22.6f}{ms_f:<18.6f}{f_val:<12.4f}{p_val:.4e}")

# Residual Row representation
print(f"{'Residuals':<10}{df_residual:<6}{ss_residual:<22.6f}{ms_residual:<18.6f}{'-':<12}{'-'}")
print("-" * 78)

# 5. Extract system-wide sweet spots (Level values that minimize MSE error)
print("\n================ SYSTEM SWEET SPOTS (MINIMUM MSE) ================")
optimal_configuration = []

for i in range(7):
    factor_col = X[:, i]
    unique_levels = np.unique(factor_col)
    
    best_lvl = None
    min_mse = float('inf')
    
    print(f"\nFactor x{i+1} Level Response Profile:")
    for lvl in unique_levels:
        mean_mse = np.mean(y[factor_col == lvl])
        print(f"  Level {int(lvl):<5} -> Mean Avg_MSE: {mean_mse:.6f}")
        if mean_mse < min_mse:
            min_mse = mean_mse
            best_lvl = int(lvl)
            
    print(f"--> Optimal Setting for x{i+1}: {best_lvl}")
    optimal_configuration.append(f"x{i+1}={best_lvl}")

print("\n------------------------------------------------------------------")
print(f"Global Optimized Run Profile Recommendation: {', '.join(optimal_configuration)}")
print("------------------------------------------------------------------")

