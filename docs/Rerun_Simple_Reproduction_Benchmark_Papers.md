# Rerun --- Recommended Simple Reproduction Benchmark Papers

## Purpose

This document defines a small, practical benchmark set for evaluating
**Rerun**.

The goal is **not** to select the most famous or technically difficult
papers. The goal is to select papers that are:

-   small enough to reproduce on a normal CPU where possible;
-   backed by an original implementation or a documented reproduction
    attempt;
-   capable of exercising different Rerun outcomes;
-   simple enough that the team can manually establish a baseline before
    using Rerun;
-   useful for demonstrating dependency repair, configuration diagnosis,
    result comparison, and irreproducibility handling.

The six primary categories are:

1.  Direct reproduction successful --- CPU only
2.  Dependency/environment change --- CPU only
3.  Small reproduction changes because the original code did not
    directly work --- CPU only
4.  Reproduction produced incorrect/divergent results --- CPU only
5.  Irreproducible / unable to execute --- CPU only
6.  One GPU example involving reproduction changes or
    incorrect/divergent results

> **Classification note:** The categories below are based on published
> reproduction reports and repository documentation. Where the published
> work required a substantial environment migration rather than a
> genuinely small patch, that is explicitly stated. Such a paper should
> not be presented as a "small patch" case merely for convenience.

------------------------------------------------------------------------

# Primary Six-Paper Set

## 1. Direct reproduction successful --- CPU only

### Paper

**Neural Networks Fail to Learn Periodic Functions and How to Fix It**

Authors: Liu Ziyin, Tilman Hartwig, Masahito Ueda\
Venue: NeurIPS 2020

### Links

-   Paper: https://arxiv.org/abs/2006.08195
-   Original code: https://github.com/AdenosHermes/NeurIPS_2020_Snake
-   Independent reproduction:
    https://github.com/mayurak47/Reproducibility_Challenge
-   Reproduction report: https://openreview.net/pdf?id=ysFCiXtCOj

### Why it belongs here

The independent reproducibility study explicitly reports that the
central experiments were successfully replicated.

The reproduction report states that the experiments supporting the
central claim --- that the Snake activation can learn periodic functions
--- were successfully reproduced. It also notes that most experiments
could be reproduced from the information in the paper, with one
unavailable dataset and some missing implementation details for specific
experiments.

The **simple analytic periodic-function experiments are CPU-friendly**
and should be used for Rerun's first pass.

### Rerun experiment

Use:

-   analytic periodic functions;
-   conventional activations versus Snake;
-   extrapolation outside the training range;
-   compare the reproduced curves/results with the paper.

Do **not** start with the CIFAR/ResNet experiments.

### Expected Rerun outcome

``` text
REPRODUCED
```

### Rerun value

**Very high.**

This is a clean baseline proving that Rerun can:

-   install a research environment;
-   execute an experiment;
-   extract numerical/graphical results;
-   compare them with a paper claim;
-   determine that the result is actually reproduced.

------------------------------------------------------------------------

# 2. Dependency/environment change --- CPU only

## Explaining Groups of Points in Low-Dimensional Representations

Authors: Gregory Plumb, Jonathan Terhorst, Sriram Sankararaman, Ameet
Talwalkar\
Venue: ICML 2020

### Links

-   Paper: https://proceedings.mlr.press/v119/plumb20a.html
-   Original code: https://github.com/GDPlumb/ELDR
-   Independent reproduction: https://github.com/rajevv/FACT-1
-   Reproduction report: https://openreview.net/pdf?id=hq3TxQK5cox

### Why it belongs here

The published reproduction explicitly says that the original code was
**upgraded to work with newer TensorFlow 2.x and PyTorch 1.7.x
environments**.

The reproduction report says the original results were reproducible
using both:

1.  the upgraded author-provided code; and
2.  the independent implementation.

It also describes the practical setup problems as minor code changes
such as:

-   absolute-path handling;
-   obtaining external dependencies;
-   updating the environment;
-   dealing with the external `scvis` package.

### Important qualification

This is a good **dependency/environment migration** case, but not a pure
one-line dependency fix. The reproduction also involved rewriting parts
of the code and the VAE architecture.

Therefore:

> Use it to test **dependency/environment repair**, not as proof that
> Rerun can automatically fix arbitrary legacy ML repositories.

### Expected Rerun outcome

``` text
PARTIALLY_REPRODUCED
        or
REPRODUCED
```

depending on exactly which experiment is selected.

### Rerun value

**High.**

It tests whether Rerun can distinguish:

``` text
old environment
       ↓
dependency incompatibility
       ↓
minimal environment/code adaptation
       ↓
successful reproduction
```

------------------------------------------------------------------------

# 3. Small reproduction changes --- CPU only

## Learning to Deceive with Attention-Based Explanations

Authors: Danish Pruthi, Mansi Gupta, Bhuwan Dhingra, Graham Neubig,
Zachary C. Lipton\
Venue: ACL 2020

### Links

-   Paper: https://aclanthology.org/2020.acl-main.432/
-   Original code: https://github.com/danishpruthi/deceptive-attention
-   Independent reproduction:
    https://github.com/MatPrst/deceptive-attention-reproduced
-   Reproduction report:
    https://rescience.github.io/bibliography/Habacker_2021.html
-   Reproduction article:
    https://zenodo.org/record/4834146/files/article.pdf

### Why it belongs here

The reproduction report states that the authors' code **worked
straightaway with minor adjustments**.

The reproducing team:

-   used the authors' code for the classifier and sequence-to-sequence
    experiments;
-   reimplemented BERT;
-   refactored the original code;
-   ported components to PyTorch Lightning.

The report states that the BERT results were also replicated, with one
result not as strongly in the reported direction.

### Important qualification

The **full paper is not a CPU-only benchmark**. The reproduction used
approximately 130 GPU-hours across its complete experimental suite.

Therefore, for this benchmark, only use a **small CPU-feasible subset**
if it can be independently verified on the chosen hardware.

Do not use the full reproduction as the first Rerun test.

### Expected Rerun outcome

For a reduced experiment:

``` text
REPRODUCED
or
PARTIALLY_REPRODUCED
```

### Rerun value

**High**, because the paper gives Rerun a realistic example where:

``` text
original code
      ↓
minor compatibility/code changes
      ↓
reproduction
```

------------------------------------------------------------------------

# 4. Reproduction with divergent/incorrect results --- CPU only

## Exacerbating Algorithmic Bias through Fairness Attacks

Authors: Ninareh Mehrabi, Muhammad Naveed, Fred Morstatter, Aram
Galstyan\
Venue: AAAI 2021

### Links

-   Paper: https://arxiv.org/abs/2012.08723
-   Original code: https://github.com/Ninarehm/attack
-   Independent reproduction:
    https://github.com/imandrealombardo/FACT-AI
-   Another reproduction study: https://github.com/DCHamerslag/FACT
-   Reproduction report: https://openreview.net/pdf?id=rKbgh3fXnRK

### Why it belongs here

This is one of the most useful Rerun cases.

The reproduction studies report that the main qualitative claims were
supported, but the **reproduced numerical/graphical results did not
exactly match the original results**.

The reproduction work identified problems involving:

-   insufficient documentation;
-   unspecified model details;
-   unclear preprocessing;
-   assumptions required to recreate altered datasets;
-   environment/dependency issues;
-   ambiguity around experimental details.

One reproduction study states that the results obtained using recreated
datasets were noticeably different from the original paper, although the
overall attack patterns still supported the claims.

Another reproduction study reports that the original environment had to
be reconstructed and that substantial changes were needed to modernize
dependencies.

### Important qualification

This is **not a clean "small patch" case**.

The published evidence supports the classification:

> **CPU-only reproduction with result divergence / configuration and
> data ambiguity**

rather than:

> "one tiny code change fixed the result."

That distinction matters for Rerun.

### Rerun experiment

Use the authors' supplied data first.

Then compare:

``` text
paper result
    vs
original code result
    vs
reproduction result
```

Specifically compare:

-   accuracy;
-   SPD;
-   EOD;
-   attack behavior.

### Expected Rerun outcome

Potentially:

``` text
PARTIALLY_REPRODUCED
```

or

``` text
NOT_REPRODUCED
```

depending on the exact experiment and environment.

### Rerun value

**Extremely high.**

This is arguably the strongest paper in the set for demonstrating
Rerun's ability to detect:

> "The program ran successfully, but the scientific result is not the
> same."

That is one of the project's central design goals.

------------------------------------------------------------------------

# 5. Irreproducible / unable to execute --- CPU only

## FairCal: Fairness Calibration for Face Verification

Authors: Tiago Salvador et al.

### Links

-   Paper: https://arxiv.org/abs/2106.03761
-   Original code: https://github.com/tiagosalvador/faircal
-   Reproduction: https://github.com/zseljee/re-faircal
-   Reproduction report:
    https://rescience.github.io/bibliography/Salvador_2022.html

### Why it belongs here

The reproduction repository documents that the main experiments depend
on datasets that are **not simply publicly downloadable from the
repository**.

In particular:

-   BFW requires registration;
-   RFW requires requesting research access.

The reproduction pipeline expects those datasets before it can execute
the complete experimental workflow.

The reproduction repository provides both CPU and GPU environments, but
the key issue for Rerun is not GPU availability:

> **the required experimental data cannot be automatically provisioned
> from the repository.**

### Expected Rerun outcome

``` text
UNABLE_TO_EXECUTE
```

with a reason such as:

``` text
Required dataset unavailable.
Manual provisioning required.
```

### Rerun value

**Very high.**

This tests whether Rerun can correctly say:

> "I cannot reproduce this experiment because required external
> resources are unavailable."

rather than incorrectly diagnosing the repository as broken.

------------------------------------------------------------------------

# 6. GPU example --- reproduction with changes / divergent results

## CartoonX: Cartoon Explanations of Image Classifiers

### Links

-   Paper: https://arxiv.org/abs/2110.03485
-   Original code: https://github.com/skmda37/CartoonX
-   Reproduction study: https://openreview.net/pdf?id=DWKJpl8s06

### Why it belongs here

This is the GPU example because the reproduction study explicitly used
CUDA GPUs.

The reproduction reports:

-   RTX 3060 and GTX 2060 Ti GPUs;
-   the same hyperparameters as the original paper;
-   approximately **36.25 hours** for the most computationally expensive
    quantitative experiment;
-   qualitative results broadly aligned with the original;
-   **quantitative results did not match the original results**, even
    when using the same hyperparameters.

### Important qualification

This is the least "simple" paper in the primary set.

Therefore, it should be used only after the CPU cases are working.

The purpose is not to reproduce the entire paper. Use **one small
quantitative experiment** as the GPU demonstration.

### Expected Rerun outcome

``` text
NOT_REPRODUCED
```

or

``` text
PARTIALLY_REPRODUCED
```

with the important observation:

``` text
same stated hyperparameters
        ↓
successful execution
        ↓
different quantitative result
```

### Rerun value

**High for the GPU-specific capability**, but lower priority than all
CPU cases.

------------------------------------------------------------------------

# Recommended execution order

Do not run these in arbitrary order.

Use:

``` text
1. Snake
       ↓
2. Explaining Groups
       ↓
3. Learning to Deceive (small subset)
       ↓
4. Fairness Attacks
       ↓
5. FairCal
       ↓
6. CartoonX GPU subset
```

This progressively increases the difficulty.

------------------------------------------------------------------------

# What each paper tests

  --------------------------------------------------------------------------------------
  Paper          Primary Rerun capability              CPU              GPU Expected
                                                                            result
  -------------- ------------------------ ---------------- ---------------- ------------
  **Snake**      Clean reproduction                    Yes  No for selected REPRODUCED
                                                                 experiment 

  **Explaining   Dependency/environment                Yes               No REPRODUCED /
  Groups**       migration                                                  PARTIAL

  **Learning to  Minor code/compatibility           Subset  Full suite uses REPRODUCED /
  Deceive**      changes                                                GPU PARTIAL

  **Fairness     Result divergence +                   Yes               No PARTIAL /
  Attacks**      configuration/data                                         NOT
                 diagnosis                                                  

  **FairCal**    Missing external data                 Yes         Optional UNABLE

  **CartoonX**   GPU + incorrect                        No              Yes PARTIAL /
                 quantitative                                               NOT
                 reproduction                                               
  --------------------------------------------------------------------------------------

------------------------------------------------------------------------

# Additional fallback papers

The following are intentionally kept **simple**. They should be
considered backup candidates rather than part of the first six.

------------------------------------------------------------------------

## A1. Hamiltonian Neural Networks

### Paper

**Hamiltonian Neural Networks**

Greydanus, Dzamba, Yosinski

### Links

-   Paper: https://arxiv.org/abs/1906.01563
-   Original code: https://github.com/greydanus/hamiltonian-nn

### Best experiment

Use:

``` text
ideal mass-spring
```

or:

``` text
ideal pendulum
```

The official repository directly provides commands for these
experiments.

### Why it is useful

The repository has a very clean progression:

``` text
mass-spring
pendulum
real pendulum
two-body
three-body
pixel pendulum
```

The first experiments are much simpler than the later vision experiment.

### Classification

**Fallback #1**

CPU-friendly, scientific/numerical, and very easy to understand.

------------------------------------------------------------------------

# A2. FedAvg

## Communication-Efficient Learning of Deep Networks from Decentralized Data

McMahan et al., AISTATS 2017

### Links

-   Paper: https://proceedings.mlr.press/v54/mcmahan17a.html
-   Paper: https://arxiv.org/abs/1602.05629
-   Simple MNIST implementation: https://github.com/alexbie98/fedavg
-   Another implementation with explicit CPU mode:
    https://github.com/intworist/FedAvg

### Best experiment

Use:

``` text
MNIST
MLP
CPU
IID
```

Then optionally:

``` text
MNIST
MLP
CPU
non-IID
```

The `intworist/FedAvg` implementation explicitly documents CPU execution
and exposes parameters such as learning rate, epochs, seed, number of
users and IID/non-IID distribution.

### Classification

**Fallback #2**

Very good for testing configuration-sensitive reproduction without
requiring distributed hardware.

------------------------------------------------------------------------

# A3. Fashion-MNIST

## Fashion-MNIST: A Novel Image Dataset for Benchmarking Machine Learning Algorithms

Xiao, Rasul, Vollgraf

### Links

-   Paper: https://arxiv.org/abs/1708.07747
-   Official repository:
    https://github.com/zalandoresearch/fashion-mnist

### Important distinction

This is a **dataset/benchmark paper**, not a conventional ML-method
paper.

The official repository provides a CPU-oriented scikit-learn benchmark
covering 129 classifiers and a benchmark runner.

### Best experiment

Use one of the documented classical ML benchmarks.

### Classification

**Fallback #3**

Extremely easy to execute, but scientifically less valuable for
demonstrating Rerun than Snake, HNN or FedAvg.

Use it as a **sanity/control case**, not as a flagship reproduction.

------------------------------------------------------------------------

# A4. Learning to Deceive --- reduced classifier experiment

If the full Learning-to-Deceive experiment proves too expensive, keep
only one of the simpler classifier experiments.

The reproduction study explicitly says the original code worked with
minor adjustments, while the complete reproduction used substantial GPU
resources.

### Classification

**Fallback #4**

Useful if a small NLP reproduction is wanted.

------------------------------------------------------------------------

# A5. Explaining Groups --- original/reproduction implementation

If the main dependency-migration experiment becomes too difficult, use
the simpler TGT experiment from the reproduction repository.

The reproduction study reports that the original results were reproduced
with both the upgraded author code and the independent implementation.

### Classification

**Fallback #5**

Good CPU-only legacy-code test.

------------------------------------------------------------------------

# A6. DECAF

## DECAF: Generating Fair Synthetic Data Using Causally-Aware Generative Networks

### Links

-   Paper: https://arxiv.org/abs/2110.12884
-   **Original implementation:** https://github.com/trentkyono/DECAF
-   Maintained/forked implementation:
    https://github.com/vanderschaarlab/decaf

### Important repository distinction

For Rerun's benchmark, use:

> **`trentkyono/DECAF` as the original implementation.**

Do **not** classify `vanderschaarlab/DECAF` as an independent
reproduction. It is a fork/maintained version of the original
implementation.

### Best experiment

Use the smallest synthetic/tabular DECAF experiment available in the
original repository.

### Classification

**Fallback #6**

Good CPU-oriented research repository if the initial six do not behave
as expected.

------------------------------------------------------------------------

# A7. PGExplainer

## Parameterized Explainer for Graph Neural Network

### Links

-   Paper: https://arxiv.org/abs/2011.04573
-   Original code: https://github.com/flyingdoog/PGExplainer
-   Independent reproduction:
    https://github.com/LarsHoldijk/RE-ParameterizedExplainerForGraphNeuralNetworks

### Best experiment

Use the smallest graph dataset and a single explanation experiment.

### Classification

**Fallback #7**

Still manageable, but more complicated than HNN, Snake or FedAvg because
of graph datasets and the older software stack.

------------------------------------------------------------------------

# Papers deliberately excluded from the simple fallback pool

These should **not** be first-line Rerun demonstrations:

  -----------------------------------------------------------------------
  Paper                               Reason
  ----------------------------------- -----------------------------------
  **LASSI**                           Multiple pretrained models,
                                      datasets and old GPU dependencies

  **Counterfactual Generative         Generative vision setup and heavier
  Networks**                          training

  **EFDM**                            More demanding vision experiments

  **CartoonX full reproduction**      GPU-heavy; keep only a reduced GPU
                                      experiment

  **Ensemble Distribution             Very expensive training
  Distillation**                      

  **EDFM**                            TPU-oriented implementation and old
                                      JAX environment

  **Noisy Labels Revisited**          Larger vision benchmark/training
                                      workload
  -----------------------------------------------------------------------

These are useful later as stress tests, but they work against the
current objective of establishing a reliable, reproducible benchmark
suite.

------------------------------------------------------------------------

# Final recommended set

If the team needs exactly **six papers**, use:

  ---------------------------------------------------------------------------
                            \# Category                 Paper
  ---------------------------- ------------------------ ---------------------
                         **1** Direct reproduction      **Snake**
                               successful --- CPU       

                         **2** Dependency/environment   **Explaining Groups
                               change --- CPU           of Points**

                         **3** Small reproduction       **Learning to
                               changes --- CPU          Deceive** --- reduced
                                                        experiment

                         **4** Divergent/incorrect      **Fairness Attacks**
                               reproduction result ---  
                               CPU                      

                         **5** Irreproducible /         **FairCal**
                               unavailable resource --- 
                               CPU                      

                         **6** GPU + divergent          **CartoonX** --- one
                               quantitative result      reduced experiment
  ---------------------------------------------------------------------------

### If any of these fail as a practical benchmark

Use the fallback order:

``` text
Hamiltonian Neural Networks
        ↓
FedAvg
        ↓
Fashion-MNIST
        ↓
DECAF
        ↓
Explaining Groups
        ↓
PGExplainer
```

## Most important recommendation

For the **first actual Rerun demo**, I would start with:

1.  **Snake**
2.  **Hamiltonian Neural Networks**
3.  **FedAvg**
4.  **Fairness Attacks**

These four are the best balance of **small execution footprint +
meaningful scientific result + different reproducibility failure
modes**.

FairCal and CartoonX should be added only after the basic pipeline
works, because their value is specifically in testing failure/resource
handling rather than validating the basic execution path.
