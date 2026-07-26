# Reproducibility bundle — "When Is Interaction Order Identifiable?"

Anonymized supplementary material. This bundle supports two independent
levels of reproduction:

- **Step 1 — Verify:** recompute every number in the paper's seven tables
  from the shipped result artifacts, without running any experiment.
- **Step 2 — Rerun:** regenerate all artifacts from scratch in Google
  Colab, then re-verify against the fresh artifacts.

## Layout

```
paperA_repro/
  README.md
  verify_tables.py        Step 1 script (Python 3, standard library only)
  results/                shipped artifacts, one directory per experiment
    order_probe_v2/       Tables 1-2 (law; tanh prediction; control)
    ridge_check/          ridge-strength sensitivity (inline claim)
    hermite_verification/ Table 2 prediction column; closed-form checks
    nid_ebm_order_probe/  Table 3 (deployed detectors: EBM, NID)
    equicorr_probe/       Table 4 (equicorrelated geometry)
    feshchenko_check/     Table 5 (angles, spectrum, A2 threshold)
    vdem_order_demo/      Table 6 (social-science panel, Appendix C)
    beijing_order_demo/   Table 7 (air-quality panel, Appendix C)
  notebooks/              seven Colab notebooks that produced the artifacts
  data/
    HDL_merged_notdev_selected.csv   country-year panel (Table 5)
    beijing_panel.npz                multi-site air-quality panel (Table 6)
```

Each experiment directory contains `per_seed.csv` and/or `results.csv`
(every row stamped with an `experiment` identifier), `metadata.json`
(configuration and a provenance hash over estimator bytecode plus
configuration constants), and, where applicable, `check.txt` (the
transcript of the pre-registered acceptance checks).

## Step 1 — Verify every table from the shipped artifacts

```
python verify_tables.py
```

No dependencies beyond the Python 3 standard library. The script
recomputes each cell of Tables 1-7 from the artifact files using the
paper's aggregation (mean and population standard deviation over seeds),
recomputes closed-form columns from the formulas, and compares at the
precision displayed in the paper (half-unit-in-last-place tolerance).
Expected output ends with:

```
167 table cells checked, 0 failures.
ALL TABLES VERIFIED
```

## Step 2 — Rerun everything from scratch (Google Colab)

1. Copy this directory to Google Drive as `MyDrive/KDD_Interactions`
   (the notebooks resolve all paths from that base; `data/` is included).
2. Preserve the shipped artifacts:
   `mv results results_shipped` (or copy) — reruns write into `results/`.
3. Open each notebook in Colab and run all cells in order. Approximate
   CPU runtimes: `order_probe` 10-15 min (two experiments),
   `hermite_verification` 2 min, `feshchenko_check` 10 min,
   `equicorr_probe` 8-12 min, `vdem_order_demo` 5-10 min,
   `beijing_order_demo` 5-10 min; `nid_ebm_order_probe` 20-35 min
   (installs `interpret-core` in its first cell; the EBM fit at
   $\rho=1$, where two inputs coincide, is the slow step). The
   notebooks are independent and can run in any order.
4. Each notebook ends with a verification cell that re-reads its own
   artifacts from disk and reruns the pre-registered acceptance checks,
   writing `check.txt`. All checks should report `PASS`.
5. Re-verify the paper tables against the fresh artifacts:
   `python verify_tables.py --results-dir results`.

Determinism: all data generators, train/test splits, permutations, and
subsamples are seeded; the shipped artifacts were produced with
numpy 2.0.2. Exact floating-point reproduction is expected under the
same numpy version; under other versions, minor float drift is absorbed
by the acceptance-check tolerances and the displayed-precision
comparison of Step 1. One exception: the EBM and NID-share columns of
`nid_ebm_order_probe` (Table 3) call scikit-learn and interpret-core
and are stochastic and library-dependent; they are recorded rather
than reproduced bitwise, so `verify_tables.py` checks those two
columns to a loose absolute tolerance and exact-checks only the
closed-form, polynomial, and RBF columns. Library versions are logged
in the artifact's `metadata.json`.

## Notes

- The acceptance-check label inside `equicorr_probe` (and its shipped
  `check.txt`) reads "provable zero" for the pairwise control. The
  precise statement, used in the paper and in the later notebooks, is:
  the population fraction is zero by construction (provable); the
  numeric threshold on the RBF estimate is an empirical class-adequacy
  criterion. The shipped artifact is kept byte-identical to what the
  runs produced.
- `results/ridge_check` supports the ridge-insensitivity statement in
  Section 5.1 (values reported inline, not in a table); it is included
  for completeness.
- Data provenance: `HDL_merged_notdev_selected.csv` is a country-year
  panel of political-institutional indicators derived from the V-Dem
  dataset (see the paper's references for the dataset citation).
  `beijing_panel.npz` contains the standardized numeric columns of the
  Beijing multi-site air-quality dataset (Zhang et al., 2017; UCI
  Machine Learning Repository), stored per site with contiguous-run
  index pairs. Both are provided for reproduction of the paper's
  experiments; consult the original sources for terms of use.
- This bundle contains no author-identifying information.
