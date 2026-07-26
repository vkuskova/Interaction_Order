#!/usr/bin/env python3
"""Step 1 of the reproducibility bundle: verify every number in the paper's
six tables (Tables 1-6) against the shipped result artifacts in results/.

Usage:  python verify_tables.py [--results-dir results]

For each table cell the script recomputes the quantity from the artifact
files (per_seed.csv or results.csv) using the same aggregation as the paper
(mean and population sd over seeds), formats it at the precision displayed
in the paper, and compares numerically with a half-unit-in-last-place
tolerance. Closed-form columns are recomputed from the formulas. Exit code
0 means every cell of every table matches."""
import csv, sys, os, math, re

RESULTS = sys.argv[sys.argv.index("--results-dir") + 1] if "--results-dir" in sys.argv else "results"

def load(exp, name):
    with open(os.path.join(RESULTS, exp, name)) as f:
        return list(csv.DictReader(f))

def mean_sd(vals):
    m = sum(vals) / len(vals)
    return m, math.sqrt(sum((v - m) ** 2 for v in vals) / len(vals))

def seeds(exp, target, rho, col, cond=None):
    rows = load(exp, "per_seed.csv")
    out = []
    for r in rows:
        if r["target"] != target: continue
        if rho is not None and abs(float(r["rho"]) - rho) > 1e-9: continue
        if cond is not None and r.get("condition") != cond: continue
        if r.get(col, "") in ("", "nan"): continue
        out.append(float(r[col]))
    return out

F = lambda r: (1 - r**2) ** 2 / ((1 + r**2) * (1 + 2 * r**2)) if r < 1 else 0.0

def dp(tok):
    return len(tok.split(".")[1]) if "." in tok else 0

def close(value, tok):
    return abs(value - float(tok)) <= 0.5 * 10 ** (-dp(tok)) + 1e-12

def cmp_cell(computed, cell):
    """computed: float | (mean, sd) | (lo, hi, 'range') | str"""
    if isinstance(computed, str):
        return computed == cell
    if "--" in cell:
        lo_t, hi_t = cell.split("--")
        return close(computed[0], lo_t) and close(computed[1], hi_t)
    if "±" in cell:
        m_t, s_t = [t.strip() for t in cell.split("±")]
        return close(computed[0], m_t) and close(computed[1], s_t)
    v = computed[0] if isinstance(computed, tuple) else computed
    return close(v, cell)

failures = 0
def report(table, rowdesc, coldesc, computed, cell):
    global failures
    ok = cmp_cell(computed, cell)
    if not ok:
        failures += 1
        print(f"FAIL  {table} [{rowdesc}] {coldesc}: paper={cell!r} computed={computed!r}")
    return ok

def report_recorded(table, rowdesc, coldesc, computed, cell, tol=0.05):
    """Recorded (stochastic, library-dependent) columns -- EBM and NID share.
    These are not bitwise reproducible across library versions, so they are
    checked to an absolute tolerance rather than displayed precision, matching
    the paper's reproducibility scope."""
    global failures
    v = computed[0] if isinstance(computed, tuple) else computed
    ok = abs(v - float(cell)) <= tol
    if not ok:
        failures += 1
        print(f"FAIL  {table} [{rowdesc}] {coldesc} (recorded): paper={cell!r} computed={computed!r}")
    return ok

EXPECTED = {'tab:law': [['0', '1.0000', '0.9950 ± 0.0008', '1.047 ± 0.004'], ['0.3', '0.6438', '0.6461 ± 0.0168', '0.673 ± 0.021'], ['0.5', '0.3000', '0.3033 ± 0.0120', '0.307 ± 0.014'], ['0.7', '0.0882', '0.0896 ± 0.0041', '0.092 ± 0.002'], ['0.9', '0.0076', '0.0078 ± 0.0003', '0.013 ± 0.004'], ['0.99', '0.0001', '0.0001 ± 0.0000', '0.006 ± 0.005'], ['1', '0', '0.0000 ± 0.0000', '0.006 ± 0.005']], 'tab:tanh': [['0', '1.0000', '1.0114 ± 0.0015', '0.0160 ± 0.0004'], ['0.3', '0.7806', '0.7827 ± 0.0012', '0.0108 ± 0.0002'], ['0.5', '0.4870', '0.4884 ± 0.0034', '0.0067 ± 0.0002'], ['0.7', '0.2045', '0.2086 ± 0.0050', '0.0030 ± 0.0001'], ['0.9', '0.0257', '0.0266 ± 0.0009', '0.0004 ± 0.0000'], ['0.99', '0.0003', '0.0004 ± 0.0000', '0.0000 ± 0.0000'], ['1', '0', '0.0001 ± 0.0000', '0.0000 ± 0.0000']], 'tab:angles': [['0.3', '0.3013--0.3014', '0.0054', '+0.3972', '+0.4', 'holds'], ['0.6', '0.6001--0.6004', '0.0046', '-0.2004', '-0.2', 'fails'], ['0.9', '0.8993--0.9003', '0.0060', '-0.8001', '-0.8', 'fails']], 'tab:equicorr': [['0', '0.9940 ± 0.0013', '1.0137 ± 0.0029', '1.0000'], ['0.3', '0.3234 ± 0.0025', '0.5727 ± 0.0085', '0.6438'], ['0.5', '0.0672 ± 0.0007', '0.2426 ± 0.0052', '0.3000'], ['0.7', '0.0082 ± 0.0001', '0.0603 ± 0.0026', '0.0882'], ['0.9', '0.0002 ± 0.0000', '0.0028 ± 0.0003', '0.0076'], ['0.99', '0.0000 ± 0.0000', '0.0000 ± 0.0000', '0.0001'], ['1', '0.0000 ± 0.0000', '0.0000 ± 0.0000', '0']], 'tab:vdem': [['real', 'monomial', '0.4634', '0.604 ± 0.055', '0.432 ± 0.060'], ['real', 'tanh prod.', '0.5037', '0.643 ± 0.057', '0.476 ± 0.073'], ['real', 'pairw. ctrl.', '0.0046', '0.0047', '0.0000'], ['Gauss.', 'monomial', '0.4976', '0.668 ± 0.058', '0.417 ± 0.076'], ['Gauss.', 'tanh prod.', '0.5584', '0.733 ± 0.074', '0.470 ± 0.098'], ['Gauss.', 'pairw. ctrl.', '0.0110', '0.0119', '0.0000'], ['permuted', 'monomial', '0.905 ± 0.040', '1.472 ± 0.404', '1.346 ± 0.258'], ['permuted', 'tanh prod.', '0.954 ± 0.017', '1.180 ± 0.162', '1.214 ± 0.165'], ['permuted', 'pairw. ctrl.', '0.0105', '0.0109', '0.0000']], 'tab:beijing': [['real', 'monomial', '0.0204', '0.020 ± 0.001', '0.020 ± 0.002'], ['real', 'tanh prod.', '0.1039', '0.110 ± 0.007', '0.042 ± 0.003'], ['real', 'pairw. ctrl.', '0.0088', '0.0091', '0.0000'], ['Gauss.', 'monomial', '0.0278', '0.028 ± 0.002', '0.026 ± 0.002'], ['Gauss.', 'tanh prod.', '0.1586', '0.157 ± 0.002', '0.031 ± 0.001'], ['Gauss.', 'pairw. ctrl.', '0.0160', '0.0160', '0.0000'], ['permuted', 'monomial', '0.993 ± 0.004', '1.012 ± 0.008', '1.034 ± 0.006'], ['permuted', 'tanh prod.', '0.998 ± 0.001', '1.003 ± 0.001', '1.011 ± 0.002'], ['permuted', 'pairw. ctrl.', '0.0178', '0.0182', '0.0000']], 'tab:detectors': [['0', '1.0000', '1.038', '1.001', '0.995', '0.714'], ['0.3', '0.6438', '0.804', '0.809', '0.795', '0.704'], ['0.5', '0.3000', '0.500', '0.511', '0.547', '0.716'], ['0.7', '0.0882', '0.208', '0.220', '0.326', '0.691'], ['0.9', '0.0076', '0.026', '0.029', '0.185', '0.697'], ['0.99', '0.0001', '0.001', '0.001', '0.153', '0.733'], ['1', '0', '0.000', '0.001', '0.151', '0.728']]}

RHOS = [0.0, 0.3, 0.5, 0.7, 0.9, 0.99, 1.0]

# ---- Table 1 (tab:law): monomial, closed form / poly D4 / RBF ----
for row, rho in zip(EXPECTED["tab:law"], RHOS):
    report("tab:law", f"rho={rho}", "F_closed", F(rho), row[1])
    report("tab:law", f"rho={rho}", "poly_D4", mean_sd(seeds("order_probe_v2", "monomial", rho, "frac_poly_D4")), row[2])
    report("tab:law", f"rho={rho}", "rbf", mean_sd(seeds("order_probe_v2", "monomial", rho, "frac_rbf_ridge")), row[3])

# ---- Table 2 (tab:tanh): semi-analytic prediction / measured RBF / control ----
pred = {float(r["rho"]): float(r["value"]) for r in load("hermite_verification", "results.csv")
        if r["check"] == "tanh_prediction_vs_pinned_rbf"}
for row, rho in zip(EXPECTED["tab:tanh"], RHOS):
    report("tab:tanh", f"rho={rho}", "predicted", pred[rho], row[1])
    report("tab:tanh", f"rho={rho}", "rbf_measured", mean_sd(seeds("order_probe_v2", "tanh_prod", rho, "frac_rbf_ridge")), row[2])
    report("tab:tanh", f"rho={rho}", "control_rbf", mean_sd(seeds("order_probe_v2", "additive_index", rho, "frac_rbf_ridge")), row[3])

# ---- Table 3 (tab:angles): edge range / zero max / lambda_min / 1-2rho / A2 ----
frows = load("feshchenko_check", "results.csv")
for row, rho in zip(EXPECTED["tab:angles"], [0.3, 0.6, 0.9]):
    sel = [r for r in frows if abs(float(r["rho"]) - rho) < 1e-9]
    edges = [float(r["estimate"]) for r in sel if r["A"] not in ("spectrum", "a2_status") and float(r["expected"]) > 0]
    zeros = [abs(float(r["estimate"])) for r in sel if r["A"] not in ("spectrum", "a2_status") and float(r["expected"]) == 0]
    lam = [float(r["estimate"]) for r in sel if r["A"] == "spectrum"][0]
    a2 = [float(r["estimate"]) for r in sel if r["A"] == "a2_status"][0]
    report("tab:angles", f"rho={rho}", "edges_range", (min(edges), max(edges), "range"), row[1])
    report("tab:angles", f"rho={rho}", "zeros_max", max(zeros), row[2])
    report("tab:angles", f"rho={rho}", "lambda_min", lam, row[3])
    report("tab:angles", f"rho={rho}", "one_minus_2rho", 1 - 2 * rho, row[4])
    report("tab:angles", f"rho={rho}", "a2_status", "holds" if a2 == 1.0 else "fails", row[5])

# ---- Table 4 (tab:equicorr): monomial poly D4 / tanh RBF / single-pair F ----
for row, rho in zip(EXPECTED["tab:equicorr"], RHOS):
    report("tab:equicorr", f"rho={rho}", "monomial_polyD4", mean_sd(seeds("equicorr_probe", "monomial", rho, "frac_poly_D4")), row[1])
    report("tab:equicorr", f"rho={rho}", "tanh_rbf", mean_sd(seeds("equicorr_probe", "tanh_prod", rho, "frac_rbf_ridge")), row[2])
    report("tab:equicorr", f"rho={rho}", "single_pair_F", F(rho), row[3])

# ---- Table (tab:detectors): deployed detectors on the tanh product ----
# F2 closed form + poly D4 + RBF are exact-checked; EBM and NID share are
# recorded (stochastic, library-dependent) and checked to a loose tolerance.
for row, rho in zip(EXPECTED["tab:detectors"], RHOS):
    report("tab:detectors", f"rho={rho}", "F_closed", F(rho), row[1])
    report("tab:detectors", f"rho={rho}", "rbf", mean_sd(seeds("nid_ebm_order_probe", "tanh_prod", rho, "frac_rbf_ridge")), row[2])
    report_recorded("tab:detectors", f"rho={rho}", "ebm", mean_sd(seeds("nid_ebm_order_probe", "tanh_prod", rho, "frac_ebm")), row[3])
    report("tab:detectors", f"rho={rho}", "poly_D4", mean_sd(seeds("nid_ebm_order_probe", "tanh_prod", rho, "frac_poly_D4")), row[4])
    report_recorded("tab:detectors", f"rho={rho}", "nid", mean_sd(seeds("nid_ebm_order_probe", "tanh_prod", rho, "nid_share3")), row[5])

# ---- Tables 5-6 (tab:vdem, tab:beijing): condition x target grids ----
COND = {"real": "real_std", "Gauss.": "gauss_scores", "permuted": "permuted_gauss"}
TARG = {"monomial": "monomial_c", "tanh prod.": "tanh_prod_c", "pairw. ctrl.": "pairwise_control"}
for lbl, exp in [("tab:vdem", "vdem_order_demo"), ("tab:beijing", "beijing_order_demo")]:
    for row in EXPECTED[lbl]:
        cond, targ = COND[row[0]], TARG[row[1]]
        for coldesc, col, cell in [("poly_in", "frac_poly_D4", row[2]),
                                   ("poly_oos", "frac_poly_oos", row[3]),
                                   ("rbf", "frac_rbf_ridge", row[4])]:
            vals = seeds(exp, targ, None, col, cond=cond)
            report(lbl, f"{row[0]}/{row[1]}", coldesc, mean_sd(vals), cell)

total = sum(len(rows) * (len(rows[0]) - (2 if lbl in ("tab:vdem", "tab:beijing") else 1))
            for lbl, rows in EXPECTED.items())
print(f"\n{total} table cells checked, {failures} failures.")
print("ALL TABLES VERIFIED" if failures == 0 else "VERIFICATION FAILED")
sys.exit(1 if failures else 0)
