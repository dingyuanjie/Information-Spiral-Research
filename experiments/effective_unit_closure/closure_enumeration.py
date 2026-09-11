"""Finite-state closure audit; standard library only, no fitting or sampling.

Probabilities and transition checks use Fraction; information uses float log2.
X=(A,B,R), M=(A,B), Y=A. R consists of optional independent refreshed bits.
The four-state kernel exactly marginalizes R; the padded model is also checked
by explicit enumeration. Interventions prepare B at the current time and leave
the subsequent transition mechanism unchanged.
"""

import argparse
import hashlib
import itertools
import json
import math
import platform
from fractions import Fraction as F
from pathlib import Path


def entropy(probabilities):
    return -sum(float(p) * math.log2(float(p)) for p in probabilities if p)


def h2(p):
    return entropy((p, 1 - p))


def tv(p, q):
    return sum((abs(a - b) for a, b in zip(p, q)), F(0)) / 2


def build(r, e0, e1, noise_bits=0):
    states = list(itertools.product((0, 1), repeat=2 + noise_bits))
    pi = [(r if s[1] else 1 - r) / (2 ** (1 + noise_bits)) for s in states]
    kernel = []
    for s in states:
        e = e1 if s[1] else e0
        kernel.append([
            (e if t[0] != s[0] else 1 - e)
            * (r if t[1] else 1 - r) / (2 ** noise_bits)
            for t in states
        ])
    assert sum(pi) == 1
    assert all(sum(row) == 1 for row in kernel)
    assert all(p > 0 for row in kernel for p in row)
    assert all(sum(pi[i] * kernel[i][j] for i in range(len(states))) == pi[j]
               for j in range(len(states)))
    return states, pi, kernel


def coarse_metrics(states, pi, kernel, projection):
    labels = list(dict.fromkeys(projection(s) for s in states))
    groups = [[i for i, s in enumerate(states) if projection(s) == label]
              for label in labels]
    group_of = {i: j for j, group in enumerate(groups) for i in group}
    weights = [sum(pi[i] for i in group) for group in groups]
    push = [[sum(row[j] for j in group) for group in groups] for row in kernel]
    reduced = [[sum(pi[i] * push[i][j] for i in group) / weights[g]
                for j in range(len(groups))] for g, group in enumerate(groups)]
    # I(Y';X | Y) = E_X KL(K_phi(X) || Q_phi(phi(X))).
    cmi = sum(float(pi[i]) * sum(
        float(p) * math.log2(float(p / reduced[group_of[i]][j]))
        for j, p in enumerate(push[i]) if p
    ) for i in range(len(states)))
    predictive = entropy(weights) - sum(float(w) * entropy(row)
                                       for w, row in zip(weights, reduced))
    micro_predictive = entropy(weights) - sum(float(w) * entropy(row)
                                             for w, row in zip(pi, push))
    diameter = max(tv(push[i], push[j]) for group in groups
                   for i in group for j in group)
    errors = [tv(push[i], reduced[group_of[i]]) for i in range(len(states))]
    average_tv = sum(w * err for w, err in zip(pi, errors))
    return {
        "cmi_bits": cmi,
        "predictive_information_bits": predictive,
        "micro_information_about_same_target_bits": micro_predictive,
        "prediction_retained_fraction": predictive / micro_predictive
        if micro_predictive > 1e-14 else None,
        "fiber_diameter_tv": float(diameter),
        "maximum_tv_to_observed_kernel": float(max(errors)),
        "average_tv_to_observed_kernel": float(average_tv),
        "strong_lumpability_exact": diameter == 0,
        "macro_entropy_bits": entropy(weights),
        "micro_entropy_bits": entropy(pi),
        "entropy_ratio": entropy(weights) / entropy(pi),
        "log_cardinality_ratio": math.log2(len(labels)) / math.log2(len(states)),
        "pushforward_kernel_rational": [[str(p) for p in row] for row in push],
        "observed_kernel_rational": [[str(p) for p in row] for row in reduced],
    }


def assert_close(a, b, tolerance=1e-12):
    assert math.isclose(a, b, abs_tol=tolerance, rel_tol=tolerance), (a, b)


def target_metrics(states, pi, kernel, projection):
    """Use the SAME target A' for every candidate representation."""
    labels = list(dict.fromkeys(projection(s) for s in states))
    groups = [[i for i, s in enumerate(states) if projection(s) == label]
              for label in labels]
    conditional = 0.0
    for group in groups:
        weight = sum(pi[i] for i in group)
        p1 = sum(pi[i] * sum(kernel[i][j] for j, s in enumerate(states) if s[0])
                 for i in group) / weight
        conditional += float(weight) * h2(p1)
    return {"target": "A_next", "information_bits": 1 - conditional}


def binary_partition_audit(states, pi, kernel):
    """All seven nonconstant binary partitions, modulo label exchange."""
    rows = []
    for tail in itertools.product((0, 1), repeat=len(states) - 1):
        labels = (0,) + tail
        if max(labels) == 0:
            continue
        mapping = dict(zip(states, labels))
        metrics = coarse_metrics(states, pi, kernel, mapping.__getitem__)
        rows.append({
            "labels_in_state_order": labels,
            "representation_entropy_bits": metrics["macro_entropy_bits"],
            "cmi_bits": metrics["cmi_bits"],
            "fiber_diameter_tv": metrics["fiber_diameter_tv"],
            "strong_lumpability_exact": metrics["strong_lumpability_exact"],
            **target_metrics(states, pi, kernel, mapping.__getitem__),
        })
    assert len(rows) == 7
    return rows


def macro_path_check(states, pi, kernel, r, e0, e1, steps=4):
    """Check every macro path against the stationary first-order model."""
    q = (1 - r) * e0 + r * e1
    for path in itertools.product((0, 1), repeat=steps + 1):
        distribution = [p if s[0] == path[0] else F(0) for s, p in zip(states, pi)]
        expected = F(1, 2)
        for previous, current in zip(path, path[1:]):
            distribution = [sum(distribution[i] * kernel[i][j]
                                for i in range(len(states))) if s[0] == current else F(0)
                            for j, s in enumerate(states)]
            expected *= q if previous != current else 1 - q
        assert sum(distribution) == expected
    return 2 ** (steps + 1)


def evaluate(name, r, e0, e1):
    states, pi, kernel = build(r, e0, e1)
    macro = coarse_metrics(states, pi, kernel, lambda s: s[0])
    meso = coarse_metrics(states, pi, kernel, lambda s: s[:2])
    parity = coarse_metrics(states, pi, kernel, lambda s: s[0] ^ s[1])
    parity_target = target_metrics(states, pi, kernel, lambda s: s[0] ^ s[1])
    q = (1 - r) * e0 + r * e1
    conditional_entropy = float(1 - r) * h2(e0) + float(r) * h2(e1)
    assert_close(macro["cmi_bits"], h2(q) - conditional_entropy)
    assert_close(macro["predictive_information_bits"], 1 - h2(q))
    assert_close(macro["fiber_diameter_tv"], float(abs(e1 - e0)))
    assert_close(macro["average_tv_to_observed_kernel"],
                 float(2 * r * (1 - r) * abs(e1 - e0)))
    assert_close(meso["cmi_bits"], 0)
    assert meso["strong_lumpability_exact"]
    if e1 == 1 - e0:
        assert parity["strong_lumpability_exact"]
        assert_close(parity_target["information_bits"], 1 - h2(e0))
    assert macro["average_tv_to_observed_kernel"] <= math.sqrt(
        math.log(2) * max(macro["cmi_bits"], 0) / 2) + 1e-12
    # Every within-fiber mixture is a convex combination of these endpoints.
    interventions = []
    for a in (0, 1):
        for b in (0, 1):
            i = states.index((a, b))
            pushed = [sum(kernel[i][j] for j, s in enumerate(states) if s[0] == z)
                      for z in (0, 1)]
            obs = [F(p) for p in macro["observed_kernel_rational"][a]]
            error = tv(pushed, obs)
            assert error == abs((e1 if b else e0) - q)
            interventions.append({
                "prepare_A": a, "prepare_B": b,
                "next_Y_distribution_rational": [str(p) for p in pushed],
                "tv_to_observed_kernel": float(error),
            })
    return {
        "name": name, "r": str(r), "e0": str(e0), "e1": str(e1),
        "states": states, "stationary_rational": [str(p) for p in pi],
        "kernel_rational": [[str(p) for p in row] for row in kernel],
        "observed_flip_probability": float(q), "macro": macro, "meso": meso,
        "same_capacity_parity": parity, "parity_fixed_target": parity_target,
        "macro_fixed_target": target_metrics(states, pi, kernel, lambda s: s[0]),
        "all_binary_partitions": binary_partition_audit(states, pi, kernel),
        "causal_preparations": interventions,
        "macro_paths_checked_exactly": macro_path_check(states, pi, kernel, r, e0, e1),
    }


def run():
    e0, e1 = F(1, 100), F(99, 100)
    rows = [evaluate("independent_exact_control", F(1, 2), e0, e0)]
    broken = evaluate("broken_complement_control", F(1, 1000000), e0, F(98, 100))
    assert not broken["same_capacity_parity"]["strong_lumpability_exact"]
    assert all(abs(row["information_bits"]) < 1e-12
               for row in broken["all_binary_partitions"] if row["strong_lumpability_exact"])
    rows.append(broken)
    rows += [evaluate("rare_hidden_driver", F(r), e0, e1)
             for r in ("1/2", "1/10", "1/100", "1/1000", "1/10000",
                       "1/100000", "1/1000000")]
    padding_checks = []
    # Enumerate all 256 microstates and all 65,536 transitions for each case.
    for row in (rows[0], rows[-1]):
        states, pi, kernel = build(F(row["r"]), F(row["e0"]), F(row["e1"]), 6)
        macro = coarse_metrics(states, pi, kernel, lambda s: s[0])
        meso = coarse_metrics(states, pi, kernel, lambda s: s[:2])
        parity = coarse_metrics(states, pi, kernel, lambda s: s[0] ^ s[1])
        for key in ("cmi_bits", "predictive_information_bits", "fiber_diameter_tv"):
            assert_close(macro[key], row["macro"][key])
        assert meso["strong_lumpability_exact"]
        # Direct full-X future information equals I(X;A') because B',R' refresh.
        full_predictive = entropy(pi) - sum(float(p) * entropy(k)
                                            for p, k in zip(pi, kernel))
        assert_close(full_predictive, macro["micro_information_about_same_target_bits"])
        padding_checks.append({
            "case": row["name"], "noise_bits": 6, "microstates": len(states),
            "transitions": len(states) ** 2,
            "macro": {k: v for k, v in macro.items() if "kernel" not in k},
            "meso": {k: v for k, v in meso.items() if "kernel" not in k},
            "parity": {k: v for k, v in parity.items() if "kernel" not in k},
            "parity_fixed_target": target_metrics(states, pi, kernel, lambda s: s[0] ^ s[1]),
            "full_micro_one_step_predictive_information_bits": full_predictive,
        })
    return {
        "schema_version": 1,
        "question": "Does small stationary micro-conditioned closure error ensure uniform closure under fiber-preserving preparations?",
        "probability_arithmetic": "exact fractions; float only for logarithms and reported metrics",
        "seeds": "not applicable: exhaustive deterministic enumeration, no learned model",
        "cases": rows, "padding_checks": padding_checks,
        "checks": {
            "positive_stochastic_kernels_and_stationarity": "PASS (rational equality)",
            "closed_form_vs_generic_metrics": "PASS (1e-12 tolerance)",
            "all_32_macro_paths_per_base_case": "PASS (rational equality)",
            "same_fiber_causal_preparations": "PASS (rational equality)",
            "retaining_B_restores_closure": "PASS (rational equality)",
            "same_capacity_parity_restores_closure_and_target_sufficiency": "PASS",
            "all_seven_binary_partitions_per_base_case": "PASS",
            "parity_success_depends_on_complementary_noise": "PASS",
            "explicit_noise_padding": "PASS (two 256-state models)",
            "average_pinsker_bound": "PASS",
        },
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path,
                        default=Path(__file__).with_name("closure_results.json"))
    args = parser.parse_args()
    result = run()
    result["reproducibility"] = {
        "python": platform.python_version(),
        "source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(args.output), "checks": result["checks"],
                      "rare_case_macro": result["cases"][-1]["macro"]}, indent=2))
