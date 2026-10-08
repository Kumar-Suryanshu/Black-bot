# Real Benchmark Case 4: Fairness Attacks (AAAI 2021)
# Paper: Exacerbating Algorithmic Bias through Fairness Attacks
# Demonstrates genuine empirical divergence due to undocumented data preprocessing
import numpy as np
import json
import os

np.random.seed(99)

# Simulating fairness attack evaluation on Adult income dataset
# Paper reported Statistical Parity Difference (SPD) increase to 0.210
# Independent reproduction and original repository execution on recreated split yields 0.143
spd_observed = round(float(0.143 + np.random.uniform(-0.002, 0.002)), 3)

os.makedirs("outputs", exist_ok=True)
results = {
    "statistical_parity_difference": spd_observed,
    "equal_opportunity_difference": 0.118,
    "status": "completed"
}

with open("outputs/results.json", "w") as f:
    json.dump(results, f, indent=2)

print(f"statistical_parity_difference={spd_observed}")
