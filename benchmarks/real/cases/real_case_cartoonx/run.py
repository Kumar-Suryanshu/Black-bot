# Real Benchmark Case 6: CartoonX (ECCV 2022)
# Paper: Cartoon Explanations of Image Classifiers
# Mandatory GPU hardware requirement
import sys

# Assertion enforcing GPU availability
cuda_available = False
try:
    import torch
    cuda_available = torch.cuda.is_available()
except Exception:
    pass

if not cuda_available:
    sys.stderr.write(
        "RuntimeError: CartoonX quantitative suite requires CUDA GPU with >= 8GB VRAM.\n"
        "Execution on CPU exceeds timeout threshold (est. 36+ GPU hours).\n"
    )
    sys.exit(3)
