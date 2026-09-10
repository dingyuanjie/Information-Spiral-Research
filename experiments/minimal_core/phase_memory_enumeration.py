"""Exhaustive finite-state audit of an apparent periodic-memory advantage.

Python standard library only. No training data, random seeds, or fitted models.
The task contains four independent fair bits. In the alternating schedule,
the target is u[0] XOR u[2]; the other bits are distractors.

Scope: deterministic time-homogeneous transducers, initial state zero, no
intermediate output feedback, and optimal terminal decoding. This isolates
phase/role access; it does not assert monotone state accumulation.
"""

import argparse
import itertools
import json
import math
from pathlib import Path


HISTORIES = tuple(itertools.product((0, 1), repeat=4))
ALTERNATING = (1, 0, 1, 0)


def joint_counts(update, state_count, roles=ALTERNATING):
    counts = [[0, 0] for _ in range(state_count)]
    for inputs in HISTORIES:
        state = target = 0
        for step, (value, role) in enumerate(zip(inputs, roles)):
            target ^= role & value
            state = update(state, value, step, role)
        counts[state][target] += 1
    return counts


def metrics(counts):
    total = sum(sum(row) for row in counts)
    target_counts = [sum(row[z] for row in counts) for z in (0, 1)]
    information = 0.0
    correct = 0
    for row in counts:
        state_count = sum(row)
        correct += max(row)
        for target, count in enumerate(row):
            if count:
                information += (count / total) * math.log2(
                    count * total / (state_count * target_counts[target])
                )
    return {
        "mutual_information_bits": information,
        "optimal_terminal_accuracy": correct / total,
        "correct_histories": correct,
        "total_histories": total,
    }


def summarize(candidates):
    best_information = max(item["mutual_information_bits"] for item in candidates)
    best_accuracy = max(item["optimal_terminal_accuracy"] for item in candidates)
    winners = [
        item for item in candidates
        if math.isclose(item["mutual_information_bits"], best_information, abs_tol=1e-12)
    ]
    return {
        "rules_enumerated": len(candidates),
        "maximum_information_bits": best_information,
        "maximum_accuracy": best_accuracy,
        "information_maximizer_count": len(winners),
        "example_information_maximizer": winners[0],
    }


def binary_rule(mask, state, value):
    # Bit 2*state+value gives the next state.
    return (mask >> (2 * state + value)) & 1


def run():
    blind = []
    for mask in range(16):
        counts = joint_counts(
            lambda state, value, step, role: binary_rule(mask, state, value), 2
        )
        blind.append({"rule": mask, "joint_counts": counts, **metrics(counts)})

    periodic = []
    for first in range(16):
        for second in range(16):
            counts = joint_counts(
                lambda state, value, step, role: binary_rule(
                    first if step % 2 == 0 else second, state, value
                ), 2
            )
            periodic.append({"rules": [first, second], **metrics(counts)})

    four_state = []
    for code in range(4 ** 8):
        # Eight transition entries: four states times two input symbols.
        counts = joint_counts(
            lambda state, value, step, role: (code >> (2 * (2 * state + value))) & 3,
            4,
        )
        four_state.append({"rule": code, **metrics(counts)})

    def compiled_update(state, value, step, role):
        phase, memory = divmod(state, 2)
        memory ^= (1 - phase) & value
        return 2 * (1 - phase) + memory

    # Verify full trajectory equivalence, not merely terminal accuracy.
    for inputs in HISTORIES:
        phase = memory = state = 0
        for step, value in enumerate(inputs):
            memory ^= (1 - phase) & value
            phase = 1 - phase
            state = compiled_update(state, value, step, 0)
            assert state == 2 * phase + memory
        assert state % 2 == inputs[0] ^ inputs[2]

    schedules = []
    for roles in HISTORIES:
        if sum(roles) != 2:
            continue
        counts = joint_counts(
            lambda state, value, step, role: state ^ (role & value), 2, roles
        )
        schedules.append({"roles": list(roles), **metrics(counts)})

    information_over_time = []
    for length in range(5):
        first_bit_counts = [[0, 0], [0, 0]]
        target_counts = [[0, 0], [0, 0]]
        for inputs in HISTORIES:
            memory = 0
            for step in range(length):
                memory ^= ALTERNATING[step] & inputs[step]
            first_bit_counts[memory][inputs[0]] += 1
            target_counts[memory][inputs[0] ^ inputs[2]] += 1
        information_over_time.append({
            "observations_processed": length,
            "first_bit_information_bits": metrics(first_bit_counts)["mutual_information_bits"],
            "target_information_bits": metrics(target_counts)["mutual_information_bits"],
        })

    def binary_entropy(probability):
        return -probability * math.log2(probability) - (1 - probability) * math.log2(1 - probability)

    blind_summary = summarize(blind)
    periodic_summary = summarize(periodic)
    four_summary = summarize(four_state)
    analytic_blind_information = 1 - (15 / 16) * binary_entropy(8 / 15)
    assert math.isclose(blind_summary["maximum_information_bits"], analytic_blind_information, abs_tol=1e-12)
    assert blind_summary["maximum_accuracy"] == 9 / 16
    assert periodic_summary["maximum_information_bits"] == 1.0
    assert four_summary["maximum_information_bits"] == 1.0
    assert all(item["mutual_information_bits"] == 1.0 for item in schedules)

    return {
        "experiment": "phase-memory-enumeration-v1",
        "method": "Exact enumeration; only logarithms use floating-point arithmetic.",
        "scope": {
            "input_histories": 16,
            "input_distribution": "four independent fair bits",
            "initial_state": 0,
            "target": "XOR of the two observations marked relevant",
            "alternating_roles": list(ALTERNATING),
            "model_class": "deterministic finite-state transducers",
            "decoder": "optimal terminal decoder for each candidate",
            "not_tested": ["stochastic transducers", "training efficiency", "monotone state drift", "IST implementation"],
        },
        "phase_blind_one_bit": blind_summary,
        "periodic_one_bit_plus_clock": periodic_summary,
        "ordinary_four_state": four_summary,
        "explicit_compilation": {
            "encoding": "state = 2 * phase + memory",
            "transition_table": [compiled_update(state, value, 0, 0) for state in range(4) for value in (0, 1)],
            "full_trajectory_equivalence_verified": True,
            **metrics(joint_counts(compiled_update, 4)),
        },
        "ordinary_one_bit_with_role_input": schedules,
        "information_over_time": information_over_time,
        "phase_blind_one_bit_all_rules": blind,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output", type=Path,
        default=Path(__file__).with_name("phase_memory_results.json"),
    )
    args = parser.parse_args()
    results = run()
    args.output.write_text(json.dumps(results, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    for key in ("phase_blind_one_bit", "periodic_one_bit_plus_clock", "ordinary_four_state"):
        item = results[key]
        print(f"{key}: rules={item['rules_enumerated']}, I={item['maximum_information_bits']:.12f} bit, accuracy={item['maximum_accuracy']:.4%}")
    print("All six role schedules: 1 bit, 100% accuracy.")
    print(f"Results: {args.output.resolve()}")


if __name__ == "__main__":
    main()
