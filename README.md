# SyndicationFirewall

> **Autonomous Content Provenance & Anti-Plagiarism Firewall for GenLayer**
>
> A standalone GenLayer Intelligent Contract that protects on-chain publishing protocols, retroactive grant distribution rounds, and research repositories against copycat plagiarism, unauthorized syndication, and intellectual property theft.

[![GenLayer Studionet](https://img.shields.io/badge/GenLayer-Studionet-blue)](https://explorer-studio.genlayer.com/address/0xEF723bc4D197fDcDcda32e853783DedDd49429c6)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Tests: Direct Mode](https://img.shields.io/badge/Direct_Mode_Tests-14%2F14_PASS-brightgreen)](#)
[![Tests: Studionet](https://img.shields.io/badge/Studionet_Integration-5%2F5_PASS-brightgreen)](#)

---

## 1. The 30-Second Reviewer Summary

### The Trust Problem
Decentralized protocols govern millions of dollars in retroactive grants (Gitcoin, Optimism RetroPGF), research bounties, and media publishing rewards conditioned on original creative or technical output. 

When a malicious applicant submits plagiarized text or slightly paraphrases an existing paper, traditional smart contracts have no way to observe the theft without trusted, centralized plagiarism APIs (e.g. Turnitin).

### Why GenLayer is Strictly Required
Traditional oracles can only compute SHA256 hashes of raw bytes. If a plagiarist changes a single sentence, swaps words with synonyms, or updates markdown styling, byte hashing fails completely. Traditional oracles cannot:
1. Fetch and read natural-language text across arbitrary web endpoints.
2. Reason about semantic originality versus verbatim copying.
3. Reach decentralized validator consensus on copyright and syndication without a centralized LLM operator.

`SyndicationFirewall` uses GenLayer validators to fetch the canonical reference URL, compare the submitted text under the Equivalence Principle, and record tamper-proof originality receipts.

---

## 2. Architecture & Flow

```
+---------------------------------------------------------------------------------+
|                                 CONSUMER PROTOCOL                               |
|          (Grant Payout Vault / Decentralized Publishing / Royalty Escrow)       |
+---------------------------------------------------------------------------------+
                                       |
                   Calls is_cleared(submission_id, min_originality)
                                       v
+---------------------------------------------------------------------------------+
|                           SyndicationFirewall (GenVM)                           |
|                                                                                 |
|  [Deterministic Gate]                                                           |
|  - Verifies submission is active                                                |
|  - Validates URL format and blocks SSRF targets                                 |
|  - Rejects if status == "FLAGGED" or originality_score < threshold              |
|                                                                                 |
|  [Non-Deterministic Consensus Audit: evaluate_originality]                       |
|  - Leader fetches canonical reference document (HTTPS)                          |
|  - Validators execute equivalence prompt comparing baseline against submission  |
|  - Quorum reaches MAJORITY_AGREE on verdict, originality score & derivative flag|
+---------------------------------------------------------------------------------+
```

---

## 3. Canonical Studionet Deployment

- **Contract Address**: [`0xEF723bc4D197fDcDcda32e853783DedDd49429c6`](https://explorer-studio.genlayer.com/address/0xEF723bc4D197fDcDcda32e853783DedDd49429c6)
- **Deployer**: `0xb3b09558183aec6c2ff5aa547163b77a9266010a` (`vixDeployer`)
- **Deployment Transaction**: `0x0a20a69aa1bfad79dd0e107d47d75a906edaa15b5cd8f2a82e4aa99ffdeb1c09`
- **Network**: GenLayer Studionet (Chain ID `61999`)

---

## 4. Repository Structure

```text
SyndicationFirewall/
├── contracts/
│   └── syndication_firewall.py        # Canonical GenLayer Intelligent Contract
├── docs/
│   ├── CONSENSUS.md                   # Consensus model & non-deterministic bounds
│   ├── SECURITY.md                    # SSRF defense, prompt injection mitigations
│   ├── INTEGRATION.md                 # Downstream Solidity & GenLayer guides
│   └── DEPLOYMENT.md                  # Studionet proof and transaction log
├── fixtures/
│   ├── canonical_article.md           # Sample original research fixture
│   └── derivative_copy.md             # Sample copycat derivative fixture
├── scripts/
│   ├── preflight.py                   # AST, schema, and security linter
│   └── deploy_studionet.py            # Reproducible deployment script
├── tests/
│   ├── conftest.py                    # Direct Mode environment patch & fixtures
│   ├── direct/
│   │   └── test_syndication_firewall.py # 14 Direct Mode unit tests
│   └── integration/
│       └── test_syndication_firewall_studionet.py # 5 live Studionet on-chain tests
├── DECISION.md                        # Design rationale & primitive selection
├── gltest.config.yaml                 # Network & test configuration
├── requirements.txt                   # Production dependencies
├── requirements-test.txt              # Test dependencies
├── LICENSE                            # MIT License (vix)
└── SUBMISSION.md                      # Ecosystem submission form summary
```

---

## 5. Verification & Testing

### 1. Run Preflight Linter
```powershell
python scripts/preflight.py
# Preflight checks passed: 16/16 assertions verified.
```

### 2. Run Direct Mode Tests
```powershell
python -m pytest tests/direct/test_syndication_firewall.py -v
# 14 passed in 0.86s
```

### 3. Run Live Studionet Integration Tests
```powershell
python -m pytest tests/integration/test_syndication_firewall_studionet.py -v
# 5 passed in 43.39s
```

---

## 6. Live State Queries

You can query the deployed contract on Studionet using the GenLayer CLI:

```powershell
# Query submission record #1
genlayer call 0xEF723bc4D197fDcDcda32e853783DedDd49429c6 get_submission --args 1

# Query validator consensus evaluation receipt #1
genlayer call 0xEF723bc4D197fDcDcda32e853783DedDd49429c6 get_evaluation --args 1

# Verify clearance gate (score 98 passes threshold 75)
genlayer call 0xEF723bc4D197fDcDcda32e853783DedDd49429c6 is_cleared --args 1 75

# Verify threshold enforcement (score 98 fails threshold 99)
genlayer call 0xEF723bc4D197fDcDcda32e853783DedDd49429c6 is_cleared --args 1 99
```
