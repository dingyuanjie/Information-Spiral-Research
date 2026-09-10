"""Exact task-mixture risk for hard and soft structural priors.

Each episode chooses ONE fixed target function. All training and test labels
within that episode use that function. Epsilon is the fraction of alternate
task episodes, not within-episode label noise or temporal concept drift.
"""

import json
import math
import sys
from fractions import Fraction
from pathlib import Path

sys.dont_write_bytecode = True
from sample_efficiency_enumeration import INPUTS, prediction_vectors


PRIORS = ((0, 1), (1, 2), (9, 10), (1, 1))
TASKS = {
    "compatible": tuple(u[0] ^ u[2] for u in INPUTS),
    "incompatible": tuple(sum(u) % 2 for u in INPUTS),
}


def run_task(vectors, labels):
    all_rules = (1 << len(vectors)) - 1
    # prediction_vectors lists first-table then second-table in ascending order.
    structured = sum(1 << (first * 16 + 12) for first in range(16))
    assert structured.bit_count() == 16
    outside = all_rules ^ structured
    ones = [sum(1 << h for h, vector in enumerate(vectors) if vector[i]) for i in range(16)]
    compatible = [ones[i] if labels[i] else all_rules ^ ones[i] for i in range(16)]
    versions = [0] * (1 << 16)
    versions[0] = all_rules
    errors = [[0] * 17 for _ in PRIORS]
    rejections = [[0] * 17 for _ in PRIORS]
    for subset in range(1 << 16):
        if subset:
            last = subset & -subset
            index = last.bit_length() - 1
            versions[subset] = versions[subset ^ last] & compatible[index]
        version = versions[subset]
        assert version  # Both tasks are realizable in the general class.
        n = subset.bit_count()
        s_count = (version & structured).bit_count()
        o_count = (version & outside).bit_count()
        totals = [(q + 15 * p) * s_count + (q - p) * o_count for p, q in PRIORS]
        for prior, total in enumerate(totals):
            if not total:
                rejections[prior][n] += 1
        remaining = ((1 << 16) - 1) ^ subset
        while remaining:
            bit = remaining & -remaining
            index = bit.bit_length() - 1
            remaining ^= bit
            positive = version & ones[index]
            sp = (positive & structured).bit_count()
            op = (positive & outside).bit_count()
            for prior, (p, q) in enumerate(PRIORS):
                total = totals[prior]
                weighted_positive = (q + 15 * p) * sp + (q - p) * op
                if not total or 2 * weighted_positive == total:
                    # Empty posterior is reported separately. A declared fair
                    # coin fallback gives a defined comparison loss of 1/2.
                    errors[prior][n] += 1
                elif int(2 * weighted_positive > total) != labels[index]:
                    errors[prior][n] += 2
    results = {}
    for prior, (p, q) in enumerate(PRIORS):
        key = str(Fraction(p, q))
        curve = []
        for n in range(17):
            subsets = math.comb(16, n)
            denominator = 2 * subsets * (16 - n)
            curve.append({
                "training_examples": n,
                "twice_error_sum": errors[prior][n],
                "error_denominator": denominator,
                "unseen_error": errors[prior][n] / denominator if denominator else None,
                "empty_posterior_subsets": rejections[prior][n],
                "training_subsets": subsets,
                "empty_posterior_probability": rejections[prior][n] / subsets,
            })
        results[key] = curve
    return results


def exact_error(point):
    return Fraction(point["twice_error_sum"], point["error_denominator"])


def main():
    vectors = prediction_vectors()
    tasks = {name: run_task(vectors, labels) for name, labels in TASKS.items()}
    boundaries = []
    mixture_risks = []
    for n in range(16):
        g0 = exact_error(tasks["compatible"]["0"][n])
        h0 = exact_error(tasks["compatible"]["1"][n])
        g1 = exact_error(tasks["incompatible"]["0"][n])
        h1 = exact_error(tasks["incompatible"]["1"][n])
        benefit = g0 - h0
        penalty = h1 - g1
        crossing = benefit / (benefit + penalty) if benefit + penalty else None
        boundaries.append({
            "training_examples": n,
            "compatible_benefit": float(benefit),
            "incompatible_penalty": float(penalty),
            "algebraic_crossing_exact": str(crossing) if crossing is not None else None,
            "algebraic_crossing": float(crossing) if crossing is not None else None,
            "crossing_in_unit_interval": crossing is not None and 0 <= crossing <= 1,
        })
        for epsilon in (Fraction(0), Fraction(1, 100), Fraction(1, 20), Fraction(1, 10), Fraction(1, 4), Fraction(1, 2), Fraction(1)):
            risks = {}
            for p, q in PRIORS:
                key = str(Fraction(p, q))
                risk = ((1 - epsilon) * exact_error(tasks["compatible"][key][n])
                        + epsilon * exact_error(tasks["incompatible"][key][n]))
                risks[key] = {"exact": str(risk), "value": float(risk)}
            mixture_risks.append({"training_examples": n, "epsilon": str(epsilon), "risks": risks})

    previous = json.loads(Path(__file__).with_name("sample_efficiency_results.json").read_text(encoding="utf-8"))
    for n in range(16):
        assert tasks["compatible"]["0"][n]["unseen_error"] == previous["general_pair_and_flat"]["curve"][n]["expected_unseen_error"]
        assert tasks["compatible"]["1"][n]["unseen_error"] == previous["ignore_distractor_pair_and_flat"]["curve"][n]["expected_unseen_error"]
    for name in TASKS:
        for key in ("0", "1/2", "9/10"):
            assert all(point["empty_posterior_probability"] == 0 for point in tasks[name][key])
    assert tasks["incompatible"]["1"][16]["empty_posterior_probability"] == 1
    assert all(point["empty_posterior_probability"] == 0 for point in tasks["compatible"]["1"])

    results = {
        "experiment": "misspecification-enumeration-v1",
        "task_mixture": "Choose compatible parity with probability 1-epsilon, all-bit parity with probability epsilon once per episode; task ID is hidden; train/test rule is fixed within episode.",
        "prior": "pi_lambda(h)=(1-lambda)/256 + lambda*1[h in S]/16; S fixes the second-phase update to identity.",
        "learner": "Exact consistency posterior, weighted majority prediction, fair ties; empty posterior explicitly reported and assigned fair-coin fallback loss.",
        "evaluation": "Uniform n-element training subsets without replacement; test only remaining examples.",
        "task_curves": tasks,
        "hard_vs_uniform_crossings": boundaries,
        "mixture_risks": mixture_risks,
        "limitations": [
            "Only two specified task functions; epsilon is a stipulated deployment mixture.",
            "Mixture boundaries depend on the learner, prior and declared failure cost.",
            "Hard-prior rejection is not a valid Bayesian posterior; coin fallback is an external failure policy.",
            "No neural training, hardware timing, continual concept drift or monotone state direction tested.",
            "Soft-prior strengths were fixed for comparison, not learned online or selected on independent validation.",
        ],
    }
    path = Path(__file__).with_name("misspecification_results.json")
    path.write_text(json.dumps(results, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    for n in (4, 5, 7, 8, 10):
        print("n", n, "crossing", boundaries[n]["algebraic_crossing"], "hard rejection on alternate", tasks["incompatible"]["1"][n]["empty_posterior_probability"])
        for name in TASKS:
            print(name, {key: tasks[name][key][n]["unseen_error"] for key in tasks[name]})
    print("Results:", path)


if __name__ == "__main__":
    main()
