import numpy as np
from scipy.optimize import brentq

def r1(theta, s, k_eA, h):
    return np.sin(s / k_eA) * (k_eA + h) / np.cos(theta)

def r2(theta, k_eA, h):
    return (
        -k_eA * np.sin(theta)
        + np.sqrt((k_eA * np.sin(theta))**2 + h**2 + 2 * h * k_eA)
    )

def r_diff(theta, s, k_eA, h):
    return r2(theta, k_eA, h) - r1(theta, s, k_eA, h)

def solve_theta(s, k_eA, h, theta_min=-1.4, theta_max=1.4):
    """
    Solves r2(theta) - r1(theta) = 0 for theta.
    The interval avoids cos(theta)=0 singularities.
    """
    return brentq(
        r_diff,
        theta_min,
        theta_max,
        args=(s, k_eA, h)
    )

# -------------------------
# Example usage
# -------------------------
if __name__ == "__main__":
    s = 113950
    k_eA  = 1.3333333*6371000
    h = 8550

    theta_solution = solve_theta(s, k_eA, h)
    print("theta(rad) =", theta_solution)
    print("theta(deg) =", theta_solution*180/3.14)
    print("range_1 =", r1(theta_solution,s,k_eA,h))
    print("range_2 =", r2(theta_solution,k_eA,h))

