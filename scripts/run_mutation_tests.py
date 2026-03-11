#!/usr/bin/env python3
# Lightweight mutation testing script for Windows compatibility.
# Applies source-level mutations, runs pytest, checks if tests catch them.
#
# Usage:
#     python scripts/run_mutation_tests.py <source_file> <test_file_or_dir>
#     python scripts/run_mutation_tests.py --batch   (runs all configured targets)

from __future__ import annotations

import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import List, Tuple

PROJECT_ROOT = Path(__file__).resolve().parent.parent

TQ = chr(34) * 3  # triple double-quote
SQ = chr(39) * 3  # triple single-quote


@dataclass
class MutationResult:
    source_file: str
    line: int
    original: str
    mutant: str
    killed: bool
    description: str


COMPARE_SWAPS = {
    "<": "<=", "<=": "<", ">": ">=", ">=": ">",
    "==": "!=", "!=": "==",
}

ARITH_SWAPS = {"+": "-", "-": "+", "*": "/", "/": "*"}

BOOL_SWAPS = {"True": "False", "False": "True"}

RETURN_MUTATIONS = [
    (r"return\s+0\.0\b", "return 1.0"),
    (r"return\s+1\.0\b", "return 0.0"),
    (r"return\s+0\b", "return 1"),
    (r"return\s+True\b", "return False"),
    (r"return\s+False\b", "return True"),
    (r"return\s+None\b", "return 42"),
]

# Extra test files always included alongside the primary test target
EXTRA_TEST_FILES = [
    "tests/test_mutant_killers.py",
]


def generate_mutations(source_lines):
    mutations = []
    in_docstring = False
    docstring_char = None

    for i, line in enumerate(source_lines):
        stripped = line.strip()

        # Track multi-line docstrings
        if not in_docstring:
            for dc in [TQ, SQ]:
                if stripped.startswith(dc):
                    if stripped.count(dc) >= 2:
                        break  # single-line docstring, skip this line
                    in_docstring = True
                    docstring_char = dc
                    break
            if in_docstring or stripped.startswith(TQ) or stripped.startswith(SQ):
                continue
        else:
            if docstring_char in stripped:
                in_docstring = False
            continue

        # Skip non-code lines
        if (not stripped or stripped.startswith("#") or
            stripped.startswith("import ") or stripped.startswith("from ") or
            stripped.startswith("@") or stripped.startswith("class ") or
            stripped.startswith("def ")):
            continue

        # Skip standalone string literals
        if ((stripped.startswith(chr(34)) and stripped.endswith(chr(34))) or
            (stripped.startswith(chr(39)) and stripped.endswith(chr(39)))):
            continue

        # Comparison operator swaps
        for orig_op, new_op in COMPARE_SWAPS.items():
            pattern = r"(?<!=)\s*" + re.escape(orig_op) + r"\s*(?!=)"
            if re.search(pattern, line) and orig_op in line:
                mutated = line.replace(orig_op, new_op, 1)
                if mutated != line:
                    mutations.append((i, line, mutated,
                        "L%d: %s -> %s" % (i + 1, orig_op, new_op)))

        # Arithmetic operator swaps
        for orig_op, new_op in ARITH_SWAPS.items():
            if orig_op in stripped and not stripped.startswith((chr(39), chr(34), "#")):
                if orig_op == "*" and "**" in line:
                    continue
                if orig_op == "/" and "//" in line:
                    continue
                idx = line.find(orig_op)
                if idx > 0 and line[idx - 1] not in "=<>!+-*/":
                    mutated = line[:idx] + new_op + line[idx + len(orig_op):]
                    if mutated != line:
                        mutations.append((i, line, mutated,
                            "L%d: %s -> %s" % (i + 1, orig_op, new_op)))

        # Boolean literal swaps
        for orig_val, new_val in BOOL_SWAPS.items():
            if orig_val in stripped and ("= " + orig_val) in line:
                mutated = line.replace("= " + orig_val, "= " + new_val, 1)
                if mutated != line:
                    mutations.append((i, line, mutated,
                        "L%d: %s -> %s" % (i + 1, orig_val, new_val)))

        # Return value mutations
        for pattern, replacement in RETURN_MUTATIONS:
            if re.search(pattern, stripped):
                mutated_stripped = re.sub(pattern, replacement, stripped, count=1)
                mutated = line.replace(stripped, mutated_stripped)
                if mutated != line:
                    mutations.append((i, line, mutated,
                        "L%d: return mutation" % (i + 1,)))

        # Constant value mutations
        const_match = re.match(r"^(\s*\w+\s*[=:]\s*.*?)(\d+\.\d+)(.*)", line)
        if const_match and "def " not in line and "class " not in line:
            val = float(const_match.group(2))
            if val != 0.0:
                new_val = val + 0.1 if val < 1.0 else val * 1.1
                mutated = "%s%s%s" % (const_match.group(1), new_val, const_match.group(3))
                if mutated != line:
                    mutations.append((i, line, mutated,
                        "L%d: %s -> %s" % (i + 1, val, new_val)))

    return mutations


def run_tests(test_target, timeout=60):
    cmd = [sys.executable, "-m", "pytest", "-x", "-q", "--tb=no",
           "--no-header", test_target]
    for extra in EXTRA_TEST_FILES:
        extra_path = PROJECT_ROOT / extra
        if extra_path.exists():
            cmd.append(str(extra))
    result = subprocess.run(
        cmd, capture_output=True, text=True, timeout=timeout,
        cwd=str(PROJECT_ROOT),
    )
    return result.returncode == 0


def run_mutation_testing(source_file, test_target):
    source_path = PROJECT_ROOT / source_file
    original_content = source_path.read_text(encoding="utf-8")
    source_lines = original_content.splitlines(keepends=True)
    mutations = generate_mutations(source_lines)
    results = []
    total = len(mutations)
    print()
    print("=" * 60)
    print("  " + source_file)
    print("  %d mutations to test against %s" % (total, test_target))
    print("=" * 60)

    for idx, (line_idx, original, mutated, desc) in enumerate(mutations):
        mutant_lines = list(source_lines)
        mutant_lines[line_idx] = mutated
        source_path.write_text("".join(mutant_lines), encoding="utf-8")
        try:
            tests_pass = run_tests(test_target)
            killed = not tests_pass
        except subprocess.TimeoutExpired:
            killed = True
        except Exception:
            killed = True
        status = "KILLED" if killed else "SURVIVED"
        marker = "." if killed else "!"
        print("  [%d/%d] %s %s -> %s" % (idx + 1, total, marker, desc, status))
        results.append(MutationResult(
            source_file=source_file, line=line_idx + 1,
            original=original.strip(), mutant=mutated.strip(),
            killed=killed, description=desc,
        ))

    source_path.write_text(original_content, encoding="utf-8")
    return results


TARGETS = [
    ("jarvis/systems/control_flow.py", "tests/unit/systems/test_control_flow.py"),
    ("jarvis/systems/validation_gates.py", "tests/unit/systems/test_validation_gates.py"),
    ("jarvis/systems/mode_controller.py", "tests/unit/systems/test_mode_controller.py"),
    ("jarvis/systems/reproducibility.py", "tests/unit/systems/test_reproducibility.py"),
    ("jarvis/metrics/fragility_index.py", "tests/unit/metrics/test_fragility_index.py"),
    ("jarvis/metrics/trust_score.py", "tests/unit/metrics/test_trust_score.py"),
    ("jarvis/core/event_log.py", "tests/unit/core/"),
    ("jarvis/core/governance_monitor.py", "tests/unit/core/test_governance_monitor.py"),
    ("jarvis/intelligence/regime_transition.py", "tests/unit/intelligence/"),
    ("jarvis/intelligence/bayesian_confidence.py", "tests/unit/intelligence/"),
]


def main():
    if len(sys.argv) == 3:
        targets = [(sys.argv[1], sys.argv[2])]
    elif len(sys.argv) == 2 and sys.argv[1] == "--batch":
        targets = TARGETS
    else:
        print("Usage:")
        print("  python scripts/run_mutation_tests.py <source> <tests>")
        print("  python scripts/run_mutation_tests.py --batch")
        sys.exit(1)

    all_results = []
    for source, tests in targets:
        results = run_mutation_testing(source, tests)
        all_results.extend(results)

    print()
    print("=" * 60)
    print("  MUTATION TESTING SUMMARY")
    print("=" * 60)

    per_file = {}
    for r in all_results:
        if r.source_file not in per_file:
            per_file[r.source_file] = {"killed": 0, "survived": 0, "total": 0}
        per_file[r.source_file]["total"] += 1
        if r.killed:
            per_file[r.source_file]["killed"] += 1
        else:
            per_file[r.source_file]["survived"] += 1

    total_killed = sum(d["killed"] for d in per_file.values())
    total_all = sum(d["total"] for d in per_file.values())

    for f, d in sorted(per_file.items()):
        rate = d["killed"] / d["total"] * 100 if d["total"] > 0 else 0
        status = "PASS" if rate >= 90 else "FAIL"
        print("  [%s] %s: %d/%d killed (%d%%)" % (status, f, d["killed"], d["total"], rate))

    overall = total_killed / total_all * 100 if total_all > 0 else 0
    print()
    print("  OVERALL: %d/%d killed (%.1f%%)" % (total_killed, total_all, overall))

    survivors = [r for r in all_results if not r.killed]
    if survivors:
        print()
        print("  SURVIVORS (%d):" % len(survivors))
        for s in survivors:
            print("    %s:%d -- %s" % (s.source_file, s.line, s.description))
            print("      original: %s" % s.original[:80])
            print("      mutant:   %s" % s.mutant[:80])

    sys.exit(0 if overall >= 90 else 1)


if __name__ == "__main__":
    main()
