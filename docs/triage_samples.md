# Real Repository Triage Samples

This document records deterministic AST triage outputs for 5 real open-source research and machine learning repositories evaluated by `tools/triage.py`.

---

## 1. Repository: `karpathy/micrograd`
- **URL:** https://github.com/karpathy/micrograd
- **Description:** A tiny scalar autograd engine and neural network library implemented in pure Python with PyTorch equivalence tests.
- **Triage Output:**
  - **Verdict:** `FEASIBLE_WITH_PROVISIONING`
  - **Reason:** Repository is feasible but requires dependency provisioning.
  - **Blockers:** `[]`
  - **Warnings:** `["Unresolved imports may need provisioning: ['torch', 'setuptools']"]`
  - **Frameworks:** `['pytorch']`
  - **GPU Signals:** 0 unguarded CUDA, 0 guarded CUDA
  - **Code Stubs:** 0
- **Human Note:** **Correct**. Micrograd is fully implementable and runnable on CPU; the core engine has zero stubs or GPU dependencies, requiring only `torch` for running the validation test suite.

---

## 2. Repository: `karpathy/minGPT`
- **URL:** https://github.com/karpathy/minGPT
- **Description:** A PyTorch re-implementation of GPT training and inference.
- **Triage Output:**
  - **Verdict:** `NEEDS_LARGE_RESOURCES`
  - **Reason:** Required data files missing from repository (1 files).
  - **Blockers:** `['data_unavailable']`
  - **Warnings:** `["Repository contains 2 guarded torch.cuda.is_available() checks (safe on CPU)."]`
  - **Frameworks:** `['pytorch']`
  - **GPU Signals:** 0 unguarded CUDA, 2 guarded CUDA (`torch.cuda.is_available()`)
  - **Missing Data Files:** `input.txt` (Shakespeare dataset referenced in character-level training demo)
- **Human Note:** **Correct**. MinGPT properly guards its CUDA calls (`device = 'cuda' if torch.cuda.is_available() else 'cpu'`), so it does not block on GPU requirements. However, executing `demo.ipynb` or training scripts references `input.txt`, which must be provisioned or downloaded before execution can begin.

---

## 3. Repository: `lucidrains/denoising-diffusion-pytorch`
- **URL:** https://github.com/lucidrains/denoising-diffusion-pytorch
- **Description:** Implementation of Denoising Diffusion Probabilistic Models in PyTorch.
- **Triage Output:**
  - **Verdict:** `NEEDS_GPU`
  - **Reason:** Hard GPU requirement detected (unguarded CUDA calls or CUDA-only packages).
  - **Blockers:** `['gpu_required']`
  - **Warnings:** `[]`
  - **Frameworks:** `['pytorch']`
  - **GPU Signals:** Unguarded `.cuda()` operations and unconditioned device requirements present in core diffusion sampling loops.
- **Human Note:** **Correct**. DDPM image diffusion training and sampling in this library hard-wires tensor operations to CUDA for fast convolution and attention, making it non-viable for CPU-only sandbox reproduction without extensive patching.

---

## 4. Repository: `fastai/numerical-linear-algebra`
- **URL:** https://github.com/fastai/numerical-linear-algebra
- **Description:** Computational Linear Algebra course materials and notebooks.
- **Triage Output:**
  - **Verdict:** `UNSUPPORTED_FORMAT`
  - **Reason:** Notebook-only repository (contains .ipynb with no runnable Python scripts).
  - **Blockers:** `['notebook_only']`
  - **Warnings:** `[]`
  - **Frameworks:** `[]`
  - **Files:** 14 Jupyter notebooks (`.ipynb`), 0 runnable `.py` entry scripts.
- **Human Note:** **Correct**. Rerun's offline sandbox expects runnable script entrypoints (`python <script>.py`); repositories containing purely Jupyter notebooks without script entrypoints cannot be executed directly by the core runtime without notebook conversion (R6).

---

## 5. Repository: `eriklindernoren/PyTorch-GAN`
- **URL:** https://github.com/eriklindernoren/PyTorch-GAN
- **Description:** Collection of PyTorch implementations of Generative Adversarial Networks.
- **Triage Output:**
  - **Verdict:** `INCOMPLETE_REPO`
  - **Reason:** README-mentioned script 'acgan.py' does not exist.
  - **Blockers:** `['missing_readme_script']`
  - **Warnings:** `[]`
  - **Evidence:** `README.md: script 'acgan.py' not found on disk` (actual path is `implementations/acgan/acgan.py`).
  - **GPU Signals:** 6 unguarded CUDA calls.
- **Human Note:** **Correct**. The repository README directs users to run `python acgan.py`, but the script was refactored into `implementations/acgan/acgan.py` without updating the documentation. Triage catches this broken command path statically before any container is launched.
