"""Exact finite-data comparison of two bijective recurrent representations.

All examples are four-bit sequences, labels are u0 XOR u2. Training sets
are uniformly drawn n-element subsets without replacement from 16 examples.
The learner uses a uniform prior on transition tables, conditions on exact
training labels, and makes posterior-majority predictions (fair random ties).
Evaluation uses only examples outside each training set.
"""

import itertools
import json
import math
from pathlib import Path


INPUTS = tuple(itertools.product((0, 1), repeat=4))
LABELS = tuple(u[0] ^ u[2] for u in INPUTS)


def flatten(first, second):
    # Pair uses index (phase, memory, input); flat table (memory, phase, input).
    flat = 0
    for phase in (0, 1):
        table = first if phase == 0 else second
        for memory in (0, 1):
            for value in (0, 1):
                output = (table >> (2 * memory + value)) & 1
                flat |= output << (4 * memory + 2 * phase + value)
    return flat


def predict_pair(first, second, inputs):
    memory = 0
    for step, value in enumerate(inputs):
        table = first if step % 2 == 0 else second
        memory = (table >> (2 * memory + value)) & 1
    return memory


def predict_flat(table, inputs):
    memory = 0
    for step, value in enumerate(inputs):
        memory = (table >> (4 * memory + 2 * (step % 2) + value)) & 1
    return memory


def prediction_vectors(restrict_ignore=False):
    vectors = []
    flat_tables = set()
    for first in range(16):
        # Mask 12 is the identity map on memory, independent of input.
        for second in ([12] if restrict_ignore else range(16)):
            flat = flatten(first, second)
            assert flat not in flat_tables
            flat_tables.add(flat)
            pair = tuple(predict_pair(first, second, u) for u in INPUTS)
            ordinary = tuple(predict_flat(flat, u) for u in INPUTS)
            assert pair == ordinary
            vectors.append(pair)
    return vectors


def learning_curve(vectors):
    count = len(vectors)
    initial = (1 << count) - 1
    ones = [sum(1 << h for h, vector in enumerate(vectors) if vector[i]) for i in range(16)]
    compatible = [ones[i] if LABELS[i] else initial ^ ones[i] for i in range(16)]
    versions = [0] * (1 << 16)
    versions[0] = initial
    # Twice the mistake count: a fair prediction tie contributes exactly one.
    twice_errors = [0] * 17
    subset_counts = [0] * 17
    unique_function_counts = [0] * 17
    vector_ids = {vector: i for i, vector in enumerate(set(vectors))}
    distinct_masks = [0] * len(vector_ids)
    for h, vector in enumerate(vectors):
        distinct_masks[vector_ids[vector]] |= 1 << h
    for subset in range(1 << 16):
        if subset:
            bit = subset & -subset
            index = bit.bit_length() - 1
            versions[subset] = versions[subset ^ bit] & compatible[index]
        version = versions[subset]
        # Both classes contain the true labeling function.
        assert version != 0
        n = subset.bit_count()
        subset_counts[n] += 1
        if sum(bool(version & mask) for mask in distinct_masks) == 1:
            unique_function_counts[n] += 1
        posterior_count = version.bit_count()
        remaining = ((1 << 16) - 1) ^ subset
        while remaining:
            bit = remaining & -remaining
            index = bit.bit_length() - 1
            remaining ^= bit
            positive = (version & ones[index]).bit_count()
            if 2 * positive == posterior_count:
                twice_errors[n] += 1
            elif int(2 * positive > posterior_count) != LABELS[index]:
                twice_errors[n] += 2
    curve = []
    for n in range(17):
        assert subset_counts[n] == math.comb(16, n)
        denominator = 2 * subset_counts[n] * (16 - n)
        curve.append({
            "training_examples": n,
            "training_subsets": subset_counts[n],
            "expected_unseen_error": twice_errors[n] / denominator if denominator else None,
            "twice_error_sum": twice_errors[n],
            "error_denominator": denominator,
            "unique_labeling_probability": unique_function_counts[n] / subset_counts[n],
        })
    threshold = next(item["training_examples"] for item in curve
                     if item["expected_unseen_error"] is not None and item["expected_unseen_error"] <= 0.05)
    stable_threshold = next(n for n in range(16)
                            if all(point["expected_unseen_error"] <= 0.05 for point in curve[n:16]))
    alternate_labels = tuple(sum(u) % 2 for u in INPUTS)
    best_alternate_error = min(sum(a != b for a, b in zip(vector, alternate_labels)) / 16 for vector in vectors)
    return {
        "hypotheses": count,
        "distinct_labeling_functions": len(vector_ids),
        "curve": curve,
        "first_n_with_expected_unseen_error_at_most_5_percent": threshold,
        "first_n_staying_at_most_5_percent_through_n15": stable_threshold,
        "best_error_on_all_four_bit_parity": best_alternate_error,
    }


def main():
    unrestricted = prediction_vectors()
    restricted = prediction_vectors(restrict_ignore=True)
    results = {
        "experiment": "sample-efficiency-enumeration-v1",
        "method": "All 65536 training subsets enumerated for each hypothesis class; error fractions exact.",
        "learner": "Uniform prior over transition tables; exact consistency posterior; majority terminal prediction; fair ties.",
        "state_and_information": "One bit of content state; identical externally supplied phase; fixed identity terminal readout.",
        "general_pair_and_flat": learning_curve(unrestricted),
        "ignore_distractor_pair_and_flat": learning_curve(restricted),
        "uniform_function_prior_sensitivity": {
            "description": "Give each distinct labeling function equal prior mass instead of each transition table.",
            "general": learning_curve(list(dict.fromkeys(unrestricted))),
            "ignore_distractor": learning_curve(list(dict.fromkeys(restricted))),
        },
        "pair_flat_predictions_identical_for_every_hypothesis_and_input": True,
        "pair_flat_sample_efficiency_difference": 0,
        "limitations": [
            "No gradient optimization or neural architecture training tested.",
            "Training sets sampled without replacement; not an IID-with-replacement sample complexity bound.",
            "Primary prior is uniform over tables; a separate uniform-function-prior sensitivity check is included.",
            "Five-percent threshold is a reporting convention, not a preregistered universal guarantee.",
            "Expected held-out error is not a high-probability PAC guarantee.",
            "The restricted class has an extra correct task assumption and fewer free table bits.",
            "No monotone state drift or IST implementation tested.",
        ],
    }
    assert results["general_pair_and_flat"]["best_error_on_all_four_bit_parity"] == 0
    assert results["ignore_distractor_pair_and_flat"]["best_error_on_all_four_bit_parity"] == 0.5
    path = Path(__file__).with_name("sample_efficiency_results.json")
    path.write_text(json.dumps(results, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    for key in ("general_pair_and_flat", "ignore_distractor_pair_and_flat"):
        item = results[key]
        print(f"{key}: hypotheses={item['hypotheses']}, functions={item['distinct_labeling_functions']}, n_5pct={item['first_n_with_expected_unseen_error_at_most_5_percent']}, stable_n_5pct={item['first_n_staying_at_most_5_percent_through_n15']}, alternate_error={item['best_error_on_all_four_bit_parity']}")
        print([(point['training_examples'], point['expected_unseen_error']) for point in item['curve'] if point['training_examples'] in (0, 1, 2, 4, 6, 8, 10, 12, 15)])
    for key in ("general", "ignore_distractor"):
        item = results["uniform_function_prior_sensitivity"][key]
        print(f"function_uniform/{key}: zero_data_error={item['curve'][0]['expected_unseen_error']}, stable_n_5pct={item['first_n_staying_at_most_5_percent_through_n15']}")
    print(f"Results: {path}")


if __name__ == "__main__":
    main()
