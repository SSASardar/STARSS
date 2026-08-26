import numpy as np
import pandas as pd
from sklearn.preprocessing import PolynomialFeatures
from sklearn.linear_model import LinearRegression

# Load the data
file_path = "batch_test_20260826_132848/emd_results.txt"

try:
    data = np.loadtxt(file_path, comments="#")
except FileNotFoundError:
    print(f"Error: Could not find '{file_path}'")
    exit(1)

# Extract variables
X_all = data[:, :7]
y = data[:, 7]

# Map to new variables:
# x'_1 = x4 (apparent motion)
# x'_2 = x2 (core ratio)
# x'_3 = x5 (cloud base height)
# x'_4 = x7 (storm duration)
x1 = X_all[:, 3]  # x'_1: apparent motion (m/s)
x2 = X_all[:, 1]  # x'_2: core ratio (ratio*100)
x3 = X_all[:, 4]  # x'_3: cloud base height (km*10)
x4 = X_all[:, 6]  # x'_4: storm duration (minutes)

n_total = len(y)
grand_mean = np.mean(y)
ss_total = np.sum((y - grand_mean) ** 2)

print("=" * 80)
print("  SUM OF SQUARES ANALYSIS FOR QUADRATIC MODEL WITH INTERACTIONS")
print("=" * 80)
print(f"\nModel: Y' = β'0 + Σβ'i*x'i + Σβ'ij*x'i*x'j + Σβ'ii*(x'i)^2")
print(f"\nDesign: 5⁴ factorial (4 factors, 5 levels each)")
print(f"Total runs: {n_total}")
print(f"Total Sum of Squares (SS_Total): {ss_total:.6f}")
print()

# Center the variables (effect coding)
x1_centered = x1 - np.mean(x1)
x2_centered = x2 - np.mean(x2)
x3_centered = x3 - np.mean(x3)
x4_centered = x4 - np.mean(x4)

# Create polynomial features (includes intercept)
poly = PolynomialFeatures(degree=2, include_bias=True)
X_poly = poly.fit_transform(np.column_stack([x1_centered, x2_centered, x3_centered, x4_centered]))

# Feature names - only include terms we want in the model
# We want: linear, quadratic, and 2-way interactions (linear x linear only)
feature_names = ['Intercept', 
                 "x'1_L", "x'2_L", "x'3_L", "x'4_L",
                 "x'1_Q", "x'2_Q", "x'3_Q", "x'4_Q",
                 "x'1:x'2", "x'1:x'3", "x'1:x'4", 
                 "x'2:x'3", "x'2:x'4", "x'3:x'4"]

# We need to select only these columns from X_poly
# PolynomialFeatures order: [1, x1, x2, x3, x4, x1^2, x2^2, x3^2, x4^2, 
#                            x1*x2, x1*x3, x1*x4, x2*x3, x2*x4, x3*x4]
# Indices: 0=Intercept, 1=x1, 2=x2, 3=x3, 4=x4, 
#          5=x1^2, 6=x2^2, 7=x3^2, 8=x4^2,
#          9=x1*x2, 10=x1*x3, 11=x1*x4, 12=x2*x3, 13=x2*x4, 14=x3*x4

selected_indices = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14]
X_selected = X_poly[:, selected_indices]

# Fit full model
model = LinearRegression(fit_intercept=False)
model.fit(X_selected, y)
y_pred = model.predict(X_selected)

# Total SS
ss_total = np.sum((y - grand_mean) ** 2)

# Model SS
ss_model = np.sum((y_pred - grand_mean) ** 2)

# Residual SS
ss_residual = ss_total - ss_model

# Compute SS for each term using Type III approach
ss_terms = {}
df_terms = {}

# Full model residual
ss_full_residual = ss_residual

# For each term, remove it and see how much SS increases
for idx, name in enumerate(feature_names):
    if idx == 0:  # Skip intercept
        continue
    
    # Remove this term from the model
    cols_to_keep = [i for i in range(X_selected.shape[1]) if i != idx]
    X_reduced = X_selected[:, cols_to_keep]
    
    # Fit reduced model
    model_reduced = LinearRegression(fit_intercept=False)
    model_reduced.fit(X_reduced, y)
    y_pred_reduced = model_reduced.predict(X_reduced)
    
    # SS contributed by this term = increase in residual SS when term is removed
    ss_reduced_residual = np.sum((y - y_pred_reduced) ** 2)
    ss_term = ss_reduced_residual - ss_full_residual
    ss_terms[name] = ss_term
    df_terms[name] = 1

# Now combine linear + quadratic for each factor
ss_x1 = ss_terms["x'1_L"] + ss_terms["x'1_Q"]
ss_x2 = ss_terms["x'2_L"] + ss_terms["x'2_Q"]
ss_x3 = ss_terms["x'3_L"] + ss_terms["x'3_Q"]
ss_x4 = ss_terms["x'4_L"] + ss_terms["x'4_Q"]

# Get interaction SS
interaction_terms = ["x'1:x'2", "x'1:x'3", "x'1:x'4", "x'2:x'3", "x'2:x'4", "x'3:x'4"]
ss_interactions = sum([ss_terms[name] for name in interaction_terms])

print("\nANOVA Table (Type III Sum of Squares):")
print("-" * 80)
print(f"{'Source':<25} {'DF':<8} {'SS':<20} {'% of Total':<15} {'% of Model':<15}")
print("-" * 80)

# Main effects with decomposition (DF = 2 for each: linear + quadratic)
print(f"{'x1 (motion)':<25} {2:<8} {ss_x1:<20.6f} {ss_x1/ss_total*100:<15.2f}% {ss_x1/ss_model*100:<15.2f}%")
print(f"{'  Linear':<25} {1:<8} {ss_terms['x\'1_L']:<20.6f} {ss_terms['x\'1_L']/ss_total*100:<15.2f}% {ss_terms['x\'1_L']/ss_model*100:<15.2f}%")
print(f"{'  Quadratic':<25} {1:<8} {ss_terms['x\'1_Q']:<20.6f} {ss_terms['x\'1_Q']/ss_total*100:<15.2f}% {ss_terms['x\'1_Q']/ss_model*100:<15.2f}%")

print(f"{'x2 (core ratio)':<25} {2:<8} {ss_x2:<20.6f} {ss_x2/ss_total*100:<15.2f}% {ss_x2/ss_model*100:<15.2f}%")
print(f"{'  Linear':<25} {1:<8} {ss_terms['x\'2_L']:<20.6f} {ss_terms['x\'2_L']/ss_total*100:<15.2f}% {ss_terms['x\'2_L']/ss_model*100:<15.2f}%")
print(f"{'  Quadratic':<25} {1:<8} {ss_terms['x\'2_Q']:<20.6f} {ss_terms['x\'2_Q']/ss_total*100:<15.2f}% {ss_terms['x\'2_Q']/ss_model*100:<15.2f}%")

print(f"{'x3 (cloud height)':<25} {2:<8} {ss_x3:<20.6f} {ss_x3/ss_total*100:<15.2f}% {ss_x3/ss_model*100:<15.2f}%")
print(f"{'  Linear':<25} {1:<8} {ss_terms['x\'3_L']:<20.6f} {ss_terms['x\'3_L']/ss_total*100:<15.2f}% {ss_terms['x\'3_L']/ss_model*100:<15.2f}%")
print(f"{'  Quadratic':<25} {1:<8} {ss_terms['x\'3_Q']:<20.6f} {ss_terms['x\'3_Q']/ss_total*100:<15.2f}% {ss_terms['x\'3_Q']/ss_model*100:<15.2f}%")

print(f"{'x4 (duration)':<25} {2:<8} {ss_x4:<20.6f} {ss_x4/ss_total*100:<15.2f}% {ss_x4/ss_model*100:<15.2f}%")
print(f"{'  Linear':<25} {1:<8} {ss_terms['x\'4_L']:<20.6f} {ss_terms['x\'4_L']/ss_total*100:<15.2f}% {ss_terms['x\'4_L']/ss_model*100:<15.2f}%")
print(f"{'  Quadratic':<25} {1:<8} {ss_terms['x\'4_Q']:<20.6f} {ss_terms['x\'4_Q']/ss_total*100:<15.2f}% {ss_terms['x\'4_Q']/ss_model*100:<15.2f}%")

# Interactions (DF = 6 total, 1 for each 2-way interaction)
print(f"{'Interactions':<25} {6:<8} {ss_interactions:<20.6f} {ss_interactions/ss_total*100:<15.2f}% {ss_interactions/ss_model*100:<15.2f}%")
for name in interaction_terms:
    print(f"{'  ' + name:<25} {1:<8} {ss_terms[name]:<20.6f} {ss_terms[name]/ss_total*100:<15.2f}% {ss_terms[name]/ss_model*100:<15.2f}%")

# Residual (DF = 625 - 1 - 8 - 6 = 610)
# Total parameters = 1 intercept + 8 (linear+quadratic) + 6 (interactions) = 15
# Residual DF = 625 - 15 = 610
df_residual = n_total - len(feature_names)
print(f"{'Residual':<25} {df_residual:<8} {ss_residual:<20.6f} {ss_residual/ss_total*100:<15.2f}% {'':<15}")
print("-" * 80)
print(f"{'Total':<25} {n_total - 1:<8} {ss_total:<20.6f} {100:<15.2f}% {'':<15}")

# Model statistics
r_squared = ss_model / ss_total
r_squared_adj = 1 - (1 - r_squared) * (n_total - 1) / (n_total - len(feature_names))

print("\n" + "=" * 80)
print("  MODEL STATISTICS")
print("=" * 80)
print(f"R² = {r_squared:.4f} ({r_squared*100:.2f}%)")
print(f"Adjusted R² = {r_squared_adj:.4f} ({r_squared_adj*100:.2f}%)")
print(f"Number of parameters: {len(feature_names)}")
print(f"Degrees of freedom residual: {df_residual}")

# Show coefficients
print("\n" + "=" * 80)
print("  MODEL COEFFICIENTS")
print("=" * 80)
for name, coef in zip(feature_names, model.coef_):
    print(f"{name:<15}: {coef:12.6f}")

# Find optimal configuration (minimize EMD)
print("\n" + "=" * 80)
print("  OPTIMAL CONFIGURATION FOR MINIMUM EMD")
print("=" * 80)

X_transformed = np.column_stack([x1, x2, x3, x4])
var_names = ["x'_1 (motion)", "x'_2 (core ratio)", "x'_3 (cloud height)", "x'_4 (duration)"]
level_labels = [
    [4, 8, 12, 16, 20],              # x1: motion (m/s)
    [0.20, 0.30, 0.40, 0.50, 0.60],  # x2: core ratio
    [1.0, 1.5, 2.0, 2.5, 3.0],       # x3: cloud height (km)
    [20, 30, 40, 50, 60]             # x4: duration (minutes)
]

for i in range(4):
    factor_col = X_transformed[:, i]
    unique_levels = np.unique(factor_col)
    
    best_lvl = None
    min_emd = float('inf')
    
    print(f"\n{var_names[i]} Level Response Profile:")
    for j, lvl in enumerate(sorted(unique_levels)):
        mean_emd = np.mean(y[factor_col == lvl])
        display_val = level_labels[i][j]
        print(f"  Level {display_val} -> Mean EMD: {mean_emd:.6f}")
        if mean_emd < min_emd:
            min_emd = mean_emd
            best_lvl = display_val
    
    print(f"--> Optimal Setting: {best_lvl}")

print("\n" + "=" * 80)
