# SyndicationFirewall (v1.0.1)

> **Autonomous Content Provenance, Licensing & Anti-Plagiarism Firewall for GenLayer**
>
> A standalone GenLayer Intelligent Contract that protects on-chain publishing protocols, retroactive grant distribution rounds, and research repositories against copycat plagiarism, unverified syndication, and intellectual property theft.

[![GenLayer Studionet](https://img.shields.io/badge/GenLayer-Studionet-blue)](https://explorer-studio.genlayer.com/address/0x40d5185Fc63107Cb794165271f51D91CEc64879B)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Tests: Direct Mode](https://img.shields.io/badge/Direct_Mode_Tests-18%2F18_PASS-brightgreen)](#)
[![Tests: Studionet](https://img.shields.io/badge/Studionet_Integration-5%2F5_PASS-brightgreen)](#)

---

## 1. The 30-Second Reviewer Summary

### The Trust Problem
Decentralized protocols govern millions of dollars in retroactive grants (Gitcoin, Optimism RetroPGF), research bounties, and media publishing rewards conditioned on original creative or technical output. 

When a malicious applicant submits plagiarized text or slightly paraphrases an existing paper, traditional smart contracts have no way to observe the theft without trusted, centralized plagiarism APIs (e.g. Turnitin).

### Why GenLayer is Strictly Required
Traditional oracles can only compute SHA256 hashes of raw bytes. If a plagiarist changes a single sentence, swaps words with synonyms, or updates markdown styling, byte hashing fails completely. Traditional oracles cannot:
1. Fetch and read natural-language text across arbitrary web endpoints.
2. Independently acquire and verify off-chain licensing agreements and syndication evidence.
3. Reach decentralized validator consensus on copyright, originality, and syndication without a centralized LLM operator.

`SyndicationFirewall` uses GenLayer validators to fetch the canonical reference URL, independently acquire and verify licensing documentation, enforce exact consensus agreement on discrete canonical clearance buckets, and record tamper-proof audit receipts.

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
|  - Verifies submission is active and status == "CLEARED"                        |
|  - Validates URL format and blocks SSRF targets                                 |
|  - Enforces exact threshold comparison against canonical discrete scores        |
|                                                                                 |
|  [Non-Deterministic Consensus Audit: evaluate_originality]                       |
|  - Validators independently fetch canonical reference document (HTTPS)          |
|  - Validators independently fetch licensing proof URL (if claimed)              |
|  - LLM evaluates originality against reference and verifies licensing evidence  |
|  - Quorum reaches MAJORITY_AGREE on exact canonical bucket & discrete score     |
|    * CLEARED_ORIGINAL: Score 100                                                |
|    * CLEARED_AUTHORIZED_SYNDICATION: Score 85 (Requires verified license)       |
|    * FLAGGED_DERIVATIVE: Score 30 (Unlicensed overlap)                          |
|    * QUARANTINED_PLAGIARISM: Score 0 (Verbatim copycat duplication)             |
+---------------------------------------------------------------------------------+
```

---

## 3. Canonical Studionet Deployment

- **Contract Address**: [`0x40d5185Fc63107Cb794165271f51D91CEc64879B`](https://explorer-studio.genlayer.com/address/0x40d5185Fc63107Cb794165271f51D91CEc64879B)
- **Deployer**: `0xb3b09558183aec6c2ff5aa547163b77a9266010a` (`vixDeployer`)
- **Deployment Transaction**: `0xa84b8a13b1e5aabcf8510fe382cbec6113fc399069842e69f859557164a671aa`
- **Network**: GenLayer Studionet (Chain ID `61999`)

---

## 4. Repository Structure

```text
SyndicationFirewall/
├── contracts/
│   └── syndication_firewall.py        # Canonical GenLayer Intelligent Contract v1.0.1
├── docs/
│   ├── CONSENSUS.md                   # Consensus model & Equivalence Principle binding
│   ├── SECURITY.md                    # SSRF defense, prompt injection & threshold mitigations
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
│   │   └── test_syndication_firewall.py # 18 Direct Mode unit tests
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
# 18 passed in 1.76s
```

### 3. Run Live Studionet Integration Tests
```powershell
python -m pytest tests/integration/test_syndication_firewall_studionet.py -v
# 5 passed in 48.73s
```

---

## 6. Live State Queries

You can query the deployed contract on Studionet using the GenLayer CLI:

```powershell
# Query submission record #1
genlayer call 0x40d5185Fc63107Cb794165271f51D91CEc64879B get_submission --args 1

# Query validator consensus evaluation receipt #2 (CLEARED_ORIGINAL with discrete score 100)
genlayer call 0x40d5185Fc63107Cb794165271f51D91CEc64879B get_evaluation --args 2

# Verify clearance gate (score 100 passes threshold 70)
genlayer call 0x40d5185Fc63107Cb794165271f51D91CEc64879B is_cleared --args 1 70

# Verify clearance gate at exact boundary 100
genlayer call 0x40d5185Fc63107Cb794165271f51D91CEc64879B is_cleared --args 1 100

# Verify threshold rejection beyond 100
genlayer call 0x40d5185Fc63107Cb794165271f51D91CEc64879B is_cleared --args 1 101
```
