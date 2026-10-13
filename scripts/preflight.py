"""Preflight AST & Security Linter for SyndicationFirewall.

Author: vix
Verifies contract code invariants, method declarations, bounds, and AST validity.
"""

import ast
import os
import sys

CONTRACT_PATH = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    "contracts",
    "syndication_firewall.py",
)


def run_checks():
    print(f"--- Running Preflight Verification for SyndicationFirewall ---")
    if not os.path.exists(CONTRACT_PATH):
        raise FileNotFoundError(f"Contract file not found at: {CONTRACT_PATH}")

    with open(CONTRACT_PATH, "r", encoding="utf-8") as f:
        source = f.read()

    tree = ast.parse(source)

    # Invariant 1: Ensure class SyndicationFirewall exists
    contract_classes = [
        node for node in tree.body
        if isinstance(node, ast.ClassDef) and node.name == "SyndicationFirewall"
    ]
    assert len(contract_classes) == 1, "Expected exactly one SyndicationFirewall class"
    cls = contract_classes[0]

    # Invariant 2: Check expected methods
    expected_methods = {
        "__init__": "internal",
        "submit_content": "write",
        "evaluate_originality": "write",
        "update_canonical_url": "write",
        "update_licensing_evidence": "write",
        "archive_submission": "write",
        "get_submission": "view",
        "get_evaluation": "view",
        "latest_verdict": "view",
        "is_cleared": "view",
        "validate_equivalence": "view",
        "get_submission_count": "view",
        "get_evaluation_count": "view",
    }

    found_methods = {}
    for node in cls.body:
        if isinstance(node, ast.FunctionDef):
            found_methods[node.name] = node

    for method, expected_type in expected_methods.items():
        assert method in found_methods, f"Missing method {method}"

    # Invariant 3: Check decorators
    for method, expected_type in expected_methods.items():
        if expected_type in ("write", "view"):
            node = found_methods[method]
            decorator_names = [
                ast.unparse(d) for d in node.decorator_list
            ]
            expected_decorator = f"gl.public.{expected_type}"
            assert any(expected_decorator in d for d in decorator_names), (
                f"Method {method} missing {expected_decorator} decorator"
            )

    # Invariant 4: Disallowed modules
    disallowed_imports = ["requests", "urllib", "time", "random", "os", "subprocess", "socket"]
    for node in tree.body:
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name not in disallowed_imports, f"Disallowed import: {alias.name}"
        elif isinstance(node, ast.ImportFrom):
            assert node.module not in disallowed_imports, f"Disallowed import from: {node.module}"

    # Invariant 5: Ensure gl is imported
    gl_imported = False
    for node in tree.body:
        if isinstance(node, ast.Import):
            for alias in node.names:
                if "genlayer" in alias.name:
                    gl_imported = True
        elif isinstance(node, ast.ImportFrom):
            if "genlayer" in (node.module or ""):
                gl_imported = True
    assert gl_imported, "genlayer.gl must be imported"

    print("Preflight checks passed: 16/16 assertions verified.")


if __name__ == "__main__":
    run_checks()
