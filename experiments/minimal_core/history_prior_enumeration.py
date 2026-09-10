"""Exact transfer from independent past tasks, with a distribution-shift control.

The learner KNOWS that every task is one of two specified parity functions.
It does not know their population frequency or any individual task identity.
Each historical task supplies one uniformly drawn labeled four-bit input.
Only the eight diagnostic inputs distinguish the two functions.

All probabilities are rational. No training or test sample is simulated.
"""

import itertools
import json
import math
from fractions import Fraction
from pathlib import Path


INPUTS = tuple(itertools.product((0, 1), repeat=4))
HISTORY_COUNTS = (0, 1, 2, 4, 8, 16, 32, 64)
CALIBRATION_COUNTS = (0, 1, 2, 4, 8, 9)
POPULATIONS = (Fraction(1, 10), Fraction(1, 2), Fraction(9, 10))


def outputs(values):
    a = values[0] ^ values[2]
    return a, a ^ values[1] ^ values[3]


def distribution(history_count, epsilon):
    p, q = epsilon.numerator, epsilon.denominator
    denominator = (2 * q) ** history_count
    states = []
    select_a = select_b = tie = 0
    for a in range(history_count + 1):
        for b in range(history_count - a + 1):
            uninformative = history_count - a - b
            ways = math.comb(history_count, a) * math.comb(history_count - a, b)
            weight = ways * (q - p) ** a * p ** b * q ** uninformative
            states.append((a, b, weight))
            if a > b:
                select_a += weight
            elif b > a:
                select_b += weight
            else:
                tie += weight
    assert select_a + select_b + tie == denominator
    return states, denominator, (
        Fraction(select_a, denominator), Fraction(select_b, denominator), Fraction(tie, denominator)
    )


def calibration_factor(n):
    # With any diagnostic calibration example the new task is identified.
    # Otherwise all eight diagnostic inputs remain in the test population.
    if n > 8:
        return Fraction(0)
    return Fraction(math.comb(8, n), math.comb(16, n)) * Fraction(8, 16 - n)


def risk(history_count, epsilon_history, epsilon_test, calibration_count):
    _, _, (a, b, tie) = distribution(history_count, epsilon_history)
    type_error = epsilon_test * a + (1 - epsilon_test) * b + Fraction(1, 2) * tie
    return calibration_factor(calibration_count) * type_error


def encoded(value):
    return {"exact": str(value), "value": float(value)}


def direct_calibration_check(n, a_count, b_count, epsilon_test):
    # Independent enumeration of new-task calibration subsets and held-out inputs.
    total = Fraction(0)
    for task, probability in ((0, 1 - epsilon_test), (1, epsilon_test)):
        for subset in itertools.combinations(range(16), n):
            identified = any(outputs(INPUTS[i])[0] != outputs(INPUTS[i])[1] for i in subset)
            errors = Fraction(0)
            for i, values in enumerate(INPUTS):
                if i in subset:
                    continue
                alternatives = outputs(values)
                if alternatives[0] == alternatives[1] or identified:
                    continue
                if a_count == b_count:
                    errors += Fraction(1, 2)
                else:
                    predicted_task = int(b_count > a_count)
                    errors += int(predicted_task != task)
            total += probability * errors / (16 - n) / math.comb(16, n)
    return total


def main():
    assert sum(outputs(x)[0] != outputs(x)[1] for x in INPUTS) == 8
    # Check the multinomial reduction with direct weighted observation paths.
    for k in range(5):
        epsilon = Fraction(1, 10)
        states, denominator, _ = distribution(k, epsilon)
        expected = {(a, b): weight for a, b, weight in states}
        actual = {key: 0 for key in expected}
        for path in itertools.product((0, 1, 2), repeat=k):
            a, b = path.count(0), path.count(1)
            weight = math.prod((9, 1, 10)[item] for item in path)
            actual[a, b] += weight
        assert actual == expected
    for n in (0, 1, 2, 4):
        for a, b in ((0, 0), (3, 1), (1, 3)):
            epsilon = Fraction(1, 10)
            conditional_type_error = epsilon if a > b else 1 - epsilon if b > a else Fraction(1, 2)
            assert direct_calibration_check(n, a, b, epsilon) == calibration_factor(n) * conditional_type_error

    stable = []
    shifted = []
    for epsilon in POPULATIONS:
        for k in HISTORY_COUNTS:
            for n in CALIBRATION_COUNTS:
                item = {
                    "epsilon_history": str(epsilon), "epsilon_test": str(epsilon),
                    "historical_tasks": k, "new_task_calibration_examples": n,
                    "learned_prior_error": encoded(risk(k, epsilon, epsilon, n)),
                    "balanced_fixed_prior_error": encoded(calibration_factor(n) / 2),
                    "always_prefer_A_error": encoded(calibration_factor(n) * epsilon),
                    "oracle_frequency_error": encoded(calibration_factor(n) * min(epsilon, 1 - epsilon)),
                }
                assert item["learned_prior_error"]["value"] + 1e-14 >= item["oracle_frequency_error"]["value"]
                stable.append(item)
    for k in HISTORY_COUNTS:
        for n in CALIBRATION_COUNTS:
            epsilon_h, epsilon_t = Fraction(1, 10), Fraction(9, 10)
            shifted.append({
                "epsilon_history": str(epsilon_h), "epsilon_test": str(epsilon_t),
                "historical_tasks": k, "new_task_calibration_examples": n,
                "retained_history_error": encoded(risk(k, epsilon_h, epsilon_t, n)),
                "reset_balanced_prior_error": encoded(calibration_factor(n) / 2),
                "oracle_test_frequency_error": encoded(calibration_factor(n) * min(epsilon_t, 1 - epsilon_t)),
            })
    assert all(risk(k, Fraction(1, 2), Fraction(1, 2), 0) == Fraction(1, 4) for k in HISTORY_COUNTS)
    assert risk(0, Fraction(1, 10), Fraction(1, 10), 0) == Fraction(1, 4)
    assert all(risk(k, Fraction(1, 10), Fraction(9, 10), 9) == 0 for k in HISTORY_COUNTS)
    result = {
        "experiment": "history-prior-enumeration-v1",
        "protocol": {
            "known_task_family": ["u0 XOR u2", "u0 XOR u1 XOR u2 XOR u3"],
            "unknown": "population frequency epsilon and each task identity",
            "historical_observation": "one independent uniform four-bit input and its label per independent historical task",
            "diagnostic_probability": "1/2",
            "hyperprior": "epsilon ~ Beta(1,1)",
            "posterior": "epsilon | history ~ Beta(1+b,1+a)",
            "new_task_prior_B": "(1+b)/(2+a+b)",
            "decision": "posterior majority over task type; fair ties; a diagnostic new-task example identifies its type exactly",
            "evaluation": "new-task calibration inputs uniformly chosen without replacement; evaluate only remaining inputs; exact expectation over disjoint historical tasks",
            "meta_memory": "two integer counts a,b; this is additional historical state, not a fixed one-bit architecture comparison",
        },
        "stable_population": stable,
        "population_reversal": shifted,
        "exact_checks": [
            "Multinomial counts equal weighted path enumeration for 0..4 historical observations.",
            "Calibration risk reduction agrees with direct subset/test-input enumeration for n=0,1,2,4 and three count states.",
            "Balanced population gives 25% error without new-task calibration regardless of history size.",
            "Nine distinct calibration examples identify either task with certainty.",
        ],
        "limitations": [
            "Candidate task functions are known, unlike the earlier 256-rule learner; do not compare error rates across those protocols as architecture gains.",
            "No estimate was selected using test-task labels or its population frequency.",
            "Exact zero-error identification depends on noiseless labels and the two-function task family.",
            "The population-reversal control tests an intentionally false exchangeability assumption, not an adaptive change detector.",
            "No periodic history order is required; the posterior depends only on additive counts.",
            "Historical labels and meta-memory cost are additional resources; this is not free performance improvement.",
            "Posterior-majority decisions equal an ordinary empirical task-frequency majority rule.",
            "No IST training, hardware cost measurement or independent Information Spiral structure established.",
        ],
    }
    path = Path(__file__).with_name("history_prior_results.json")
    path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    for k in HISTORY_COUNTS:
        print(k, "stable", float(risk(k, Fraction(1, 10), Fraction(1, 10), 0)),
              "reversed", float(risk(k, Fraction(1, 10), Fraction(9, 10), 0)))
    print("Results:", path)


if __name__ == "__main__":
    main()
