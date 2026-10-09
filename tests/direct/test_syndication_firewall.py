"""Direct Mode Adversarial Test Suite for SyndicationFirewall.

Author: vix
Covers submission admission, SSRF rejection, bounds, non-deterministic web and LLM
originality evaluations, fail-closed handling, and downstream clearance gates.
"""

import json
import pytest

CONTRACT_PATH = "contracts/syndication_firewall.py"


def deploy_contract(direct_deploy):
    return direct_deploy(CONTRACT_PATH)


def test_deployment_initial_state(direct_deploy, direct_alice):
    contract = deploy_contract(direct_deploy)
    assert contract.get_submission_count() == 0
    assert contract.get_evaluation_count() == 0


def test_submit_content_success(direct_vm, direct_deploy, direct_alice):
    contract = deploy_contract(direct_deploy)
    direct_vm.sender = direct_alice

    sub_id = contract.submit_content(
        title="Decentralized Storage Market Dynamics",
        content="This article explores the economic mechanisms governing decentralized storage networks.",
        canonical_url="https://example.com/research/storage-paper.html",
    )
    assert sub_id == 1
    assert contract.get_submission_count() == 1

    sub = contract.get_submission(1)
    assert sub["id"] == 1
    assert sub["title"] == "Decentralized Storage Market Dynamics"
    assert sub["canonical_url"] == "https://example.com/research/storage-paper.html"
    assert sub["status"] == "PENDING"
    assert sub["active"] is True
    assert sub["latest_evaluation_id"] == 0


def test_submit_content_bounds_validation(direct_vm, direct_deploy):
    contract = deploy_contract(direct_deploy)

    # Empty title
    with direct_vm.expect_revert("Title length"):
        contract.submit_content(
            title="",
            content="Some body text",
            canonical_url="https://example.com/article",
        )

    # Oversized title (>128 chars)
    with direct_vm.expect_revert("Title length"):
        contract.submit_content(
            title="A" * 129,
            content="Some body text",
            canonical_url="https://example.com/article",
        )

    # Empty content
    with direct_vm.expect_revert("Content length"):
        contract.submit_content(
            title="Valid Title",
            content="",
            canonical_url="https://example.com/article",
        )

    # Oversized content (>8192 chars)
    with direct_vm.expect_revert("Content length"):
        contract.submit_content(
            title="Valid Title",
            content="B" * 8193,
            canonical_url="https://example.com/article",
        )


def test_submit_content_invalid_url_and_ssrf(direct_vm, direct_deploy):
    contract = deploy_contract(direct_deploy)

    # Non-HTTPS
    with direct_vm.expect_revert("Only secure HTTPS URLs are permitted"):
        contract.submit_content(
            title="HTTP Test",
            content="Valid content",
            canonical_url="http://example.com/paper",
        )

    # Localhost
    with direct_vm.expect_revert("Prohibited host or IP in URL"):
        contract.submit_content(
            title="Localhost Attack",
            content="Valid content",
            canonical_url="https://localhost/secret.json",
        )

    # Loopback IP
    with direct_vm.expect_revert("Prohibited host or IP in URL"):
        contract.submit_content(
            title="Loopback Attack",
            content="Valid content",
            canonical_url="https://127.0.0.1/admin",
        )

    # AWS/Cloud Metadata IP
    with direct_vm.expect_revert("Prohibited host or IP in URL"):
        contract.submit_content(
            title="Metadata Attack",
            content="Valid content",
            canonical_url="https://169.254.169.254/latest/meta-data/",
        )


def test_evaluate_original_content(direct_vm, direct_deploy, direct_alice):
    contract = deploy_contract(direct_deploy)
    direct_vm.sender = direct_alice

    sub_id = contract.submit_content(
        title="Novel Consensus Analysis",
        content="Our research introduces a multi-agent fault tolerant mechanism distinct from PBFT.",
        canonical_url="https://research.org/papers/pbft-classic.html",
    )

    canonical_body = "Practical Byzantine Fault Tolerance describes state machine replication using three-phase commits."
    direct_vm.mock_web(
        r"research\.org/papers/.*",
        {"status": 200, "body": canonical_body},
    )

    llm_response = json.dumps({
        "verdict": "ORIGINAL",
        "originality_score": 92,
        "is_derivative": False,
        "reasoning": "The submitted text discusses novel multi-agent consensus and has negligible semantic overlap with the PBFT reference.",
    })
    direct_vm.mock_llm(r".*", llm_response)

    eval_id = contract.evaluate_originality(sub_id)
    assert eval_id == 1
    assert contract.get_evaluation_count() == 1

    sub = contract.get_submission(sub_id)
    assert sub["status"] == "CLEARED"
    assert sub["latest_evaluation_id"] == 1

    ev = contract.get_evaluation(eval_id)
    assert ev["verdict"] == "ORIGINAL"
    assert ev["originality_score"] == 92
    assert ev["is_derivative"] is False
    assert ev["evidence_status_code"] == 200

    assert contract.is_cleared(sub_id, 70) is True
    assert contract.is_cleared(sub_id, 95) is False


def test_evaluate_syndicated_content(direct_vm, direct_deploy, direct_alice):
    contract = deploy_contract(direct_deploy)
    direct_vm.sender = direct_alice

    sub_id = contract.submit_content(
        title="Syndicated Tech Dispatch",
        content="Published with authorization from Tech Wire. The latest developments in decentralized compute...",
        canonical_url="https://techwire.com/articles/compute-dispatch.html",
    )

    canonical_body = "The latest developments in decentralized compute show significant scaling improvements."
    direct_vm.mock_web(
        r"techwire\.com/.*",
        {"status": 200, "body": canonical_body},
    )

    llm_response = json.dumps({
        "verdict": "SYNDICATED",
        "originality_score": 45,
        "is_derivative": True,
        "reasoning": "Legitimate syndication with clear attribution and licensing notice.",
    })
    direct_vm.mock_llm(r".*", llm_response)

    eval_id = contract.evaluate_originality(sub_id)
    assert eval_id == 1

    sub = contract.get_submission(sub_id)
    assert sub["status"] == "CLEARED"

    ev = contract.get_evaluation(eval_id)
    assert ev["verdict"] == "SYNDICATED"
    assert contract.is_cleared(sub_id, 70) is True


def test_evaluate_plagiarized_content(direct_vm, direct_deploy, direct_alice):
    contract = deploy_contract(direct_deploy)
    direct_vm.sender = direct_alice

    sub_id = contract.submit_content(
        title="Copied Technical Proposal",
        content="We provide state machine replication using three-phase commit pre-prepare prepare commit without any changes.",
        canonical_url="https://research.org/papers/pbft-classic.html",
    )

    canonical_body = "We provide state machine replication using three-phase commit pre-prepare prepare commit."
    direct_vm.mock_web(
        r"research\.org/papers/.*",
        {"status": 200, "body": canonical_body},
    )

    llm_response = json.dumps({
        "verdict": "PLAGIARIZED",
        "originality_score": 10,
        "is_derivative": True,
        "reasoning": "Substantial verbatim copying of the core algorithm without original commentary or attribution.",
    })
    direct_vm.mock_llm(r".*", llm_response)

    eval_id = contract.evaluate_originality(sub_id)
    assert eval_id == 1

    sub = contract.get_submission(sub_id)
    assert sub["status"] == "FLAGGED"

    ev = contract.get_evaluation(eval_id)
    assert ev["verdict"] == "PLAGIARIZED"
    assert ev["originality_score"] == 10
    assert ev["is_derivative"] is True

    # Downstream gate blocks payment/release
    assert contract.is_cleared(sub_id, 50) is False
    assert contract.is_cleared(sub_id, 0) is False


def test_evaluate_unreachable_reference_fails_closed(direct_vm, direct_deploy):
    contract = deploy_contract(direct_deploy)

    sub_id = contract.submit_content(
        title="Unreachable Source Test",
        content="Testing fail-closed behavior when reference URL returns 404.",
        canonical_url="https://example.com/missing-paper.html",
    )

    direct_vm.mock_web(
        r"example\.com/missing-paper\.html",
        {"status": 404, "body": ""},
    )

    eval_id = contract.evaluate_originality(sub_id)
    assert eval_id == 1

    sub = contract.get_submission(sub_id)
    assert sub["status"] == "QUARANTINED"

    ev = contract.get_evaluation(eval_id)
    assert ev["verdict"] == "UNAVAILABLE"
    assert ev["originality_score"] == 0
    assert ev["evidence_status_code"] == 404

    # Fail closed
    assert contract.is_cleared(sub_id, 0) is False


def test_evaluate_malformed_llm_output_fails_closed(direct_vm, direct_deploy):
    contract = deploy_contract(direct_deploy)

    sub_id = contract.submit_content(
        title="Malformed LLM Output Test",
        content="Checking resilience against non-JSON LLM responses.",
        canonical_url="https://example.com/valid-page.html",
    )

    direct_vm.mock_web(
        r"example\.com/valid-page\.html",
        {"status": 200, "body": "Valid body text"},
    )
    direct_vm.mock_llm(r".*", "I am an AI and I cannot output JSON right now.")

    eval_id = contract.evaluate_originality(sub_id)
    assert eval_id == 1

    sub = contract.get_submission(sub_id)
    assert sub["status"] == "FLAGGED"

    ev = contract.get_evaluation(eval_id)
    assert ev["verdict"] == "ERROR"
    assert ev["originality_score"] == 0
    assert ev["is_derivative"] is True
    assert contract.is_cleared(sub_id, 0) is False


def test_update_canonical_url_permissions_and_reset(direct_vm, direct_deploy, direct_alice, direct_bob):
    contract = deploy_contract(direct_deploy)
    direct_vm.sender = direct_alice

    sub_id = contract.submit_content(
        title="Updatable URL Article",
        content="Content to be re-pointed to correct canonical reference.",
        canonical_url="https://initial.org/paper.html",
    )

    # Unauthorized party attempts update -> reverts
    direct_vm.sender = direct_bob
    with direct_vm.expect_revert("Only submitter can update canonical URL"):
        contract.update_canonical_url(
            sub_id,
            "https://new.org/paper.html",
        )

    # Submitter updates URL -> succeeds and resets status to PENDING
    direct_vm.sender = direct_alice
    contract.update_canonical_url(
        sub_id,
        "https://new.org/paper.html",
    )
    sub = contract.get_submission(sub_id)
    assert sub["canonical_url"] == "https://new.org/paper.html"
    assert sub["status"] == "PENDING"


def test_archive_submission_and_prevent_further_evaluation(direct_vm, direct_deploy, direct_alice, direct_bob):
    contract = deploy_contract(direct_deploy)
    direct_vm.sender = direct_alice

    sub_id = contract.submit_content(
        title="Archival Test",
        content="Content to be archived.",
        canonical_url="https://example.com/paper.html",
    )

    # Unauthorized archival -> reverts
    direct_vm.sender = direct_bob
    with direct_vm.expect_revert("Only submitter can archive submission"):
        contract.archive_submission(sub_id)

    # Submitter archives -> succeeds
    direct_vm.sender = direct_alice
    contract.archive_submission(sub_id)
    sub = contract.get_submission(sub_id)
    assert sub["active"] is False
    assert sub["status"] == "QUARANTINED"

    # Evaluation on archived submission must revert
    with direct_vm.expect_revert("Cannot evaluate an archived submission"):
        contract.evaluate_originality(sub_id)


def test_latest_verdict_view(direct_vm, direct_deploy):
    contract = deploy_contract(direct_deploy)

    sub_id = contract.submit_content(
        title="Verdict View Test",
        content="Sample content",
        canonical_url="https://example.com/paper.html",
    )

    # Before evaluation
    verdict, score, is_deriv = contract.latest_verdict(sub_id)
    assert verdict == "PENDING"
    assert score == 0
    assert is_deriv is False

    # After evaluation
    direct_vm.mock_web(
        r"example\.com/paper\.html",
        {"status": 200, "body": "Reference body"},
    )
    llm_response = json.dumps({
        "verdict": "ORIGINAL",
        "originality_score": 88,
        "is_derivative": False,
        "reasoning": "High originality.",
    })
    direct_vm.mock_llm(r".*", llm_response)

    contract.evaluate_originality(sub_id)

    verdict, score, is_deriv = contract.latest_verdict(sub_id)
    assert verdict == "ORIGINAL"
    assert score == 88
    assert is_deriv is False


def test_nonexistent_submission_reverts(direct_vm, direct_deploy):
    contract = deploy_contract(direct_deploy)

    with direct_vm.expect_revert("does not exist"):
        contract.evaluate_originality(999)

    with direct_vm.expect_revert("Submission not found"):
        contract.get_submission(999)

    with direct_vm.expect_revert("Evaluation not found"):
        contract.get_evaluation(999)


def test_multiple_independent_submissions(direct_deploy):
    contract = deploy_contract(direct_deploy)

    sub1 = contract.submit_content("Title 1", "Content 1", "https://site1.com/paper")
    sub2 = contract.submit_content("Title 2", "Content 2", "https://site2.com/paper")
    assert sub1 == 1
    assert sub2 == 2
    assert contract.get_submission_count() == 2

    assert contract.get_submission(1)["title"] == "Title 1"
    assert contract.get_submission(2)["title"] == "Title 2"
