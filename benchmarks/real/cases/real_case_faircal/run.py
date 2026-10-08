# Real Benchmark Case 5: FairCal (ICLR 2022)
# Paper: FairCal: Fairness Calibration for Face Verification
# External gated datasets BFW / RFW require credentials; missing by default
import os
import sys

dataset_bfw = "data/bfw"
dataset_rfw = "data/rfw"

if not os.path.exists(dataset_bfw) or not os.path.exists(dataset_rfw):
    sys.stderr.write(
        "ERROR: Required benchmark datasets 'BFW' and 'RFW' not found.\n"
        "These datasets require academic registration and approval.\n"
        "Manual provisioning required.\n"
    )
    sys.exit(2)
