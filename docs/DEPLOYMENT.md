# Studionet Canonical Deployment Record (v1.0.1)

Author: vix

## 1. Network & Deployment Summary

| Parameter | Value |
| :--- | :--- |
| **Network** | GenLayer Studionet |
| **Chain ID** | `61999` |
| **Canonical Contract Address** | `0x40d5185Fc63107Cb794165271f51D91CEc64879B` |
| **Deployer Address** | `0xb3b09558183aec6c2ff5aa547163b77a9266010a` (`vixDeployer`) |
| **Deployment Transaction** | `0xa84b8a13b1e5aabcf8510fe382cbec6113fc399069842e69f859557164a671aa` |
| **Consensus Result** | `MAJORITY_AGREE` (5 validators: 4 AGREE, 1 IDLE) |
| **Status** | `ACCEPTED` / `FINALIZED` |
| **Explorer URL** | [GenLayer Explorer](https://explorer-studio.genlayer.com/address/0x40d5185Fc63107Cb794165271f51D91CEc64879B) |

---

## 2. On-Chain Transactions & Consensus Verification

### Deployment Transaction
- **Tx Hash**: `0xa84b8a13b1e5aabcf8510fe382cbec6113fc399069842e69f859557164a671aa`
- **Sender**: `0xb3b09558183aec6c2ff5aa547163b77a9266010a` (`vixDeployer`)
- **Status**: `ACCEPTED` (`MAJORITY_AGREE`)
- **Result**: Contract v1.0.1 initialized with zero submissions and zero evaluations.

### Transaction 1: Content Submission
- **Method**: `submit_content`
- **Tx Hash**: `0x00d2110a18bec25b2238a377ece7f464f5b07530d340a9078ccc41ebbea5b631`
- **Status**: `ACCEPTED` (`MAJORITY_AGREE`)
- **Parameters**:
  - `title`: `"Decentralized Compute Scaling"`
  - `content`: `"This research analyses multi-agent consensus protocols and fault-tolerant state machine replication in distributed ledger environments."`
  - `canonical_url`: `"https://raw.githubusercontent.com/genlayer/genlayer-simulator/main/README.md"`
  - `license_proof_url`: `""`
  - `syndication_id`: `""`

### Transaction 2: Non-Deterministic Fail-Closed Evaluation (HTTP 404 Reference)
- **Method**: `evaluate_originality`
- **Tx Hash**: `0x6ac6b921cc58b43bcd2ee5c0c89f9222f91c188e7f3b919cfd0a141f8af9a625`
- **Status**: `ACCEPTED` (`MAJORITY_AGREE`)
- **Outcome Recorded On-Chain**:
  - `verdict`: `"UNAVAILABLE"`
  - `originality_score`: `0`
  - `is_derivative`: `true`
  - `authorization_verified`: `false`
  - `evidence_status_code`: `404`
  - `reasoning`: `"Canonical reference unavailable: HTTP 404."`
  - **Downstream Clearance Gate (`is_cleared(1, 0)`)**: `false` (Fail-closed enforced).

### Transaction 3: Canonical Reference Update
- **Method**: `update_canonical_url`
- **Tx Hash**: `0x11cad61d6b5b748ff16bf5982ab96a07ee7170308cda4dc392fd3618c7847e55`
- **Status**: `ACCEPTED` (`MAJORITY_AGREE` 5/5 AGREE)
- **Parameters**: `submission_id = 1`, `new_url = "https://raw.githubusercontent.com/github/gitignore/main/Python.gitignore"`

### Transaction 4: Non-Deterministic Multi-Validator Consensus Originality Evaluation
- **Method**: `evaluate_originality`
- **Tx Hash**: `0xbe5f8e03c46b4e987e56a34e746c647cd540f66d97effe85cc47378c8def967f`
- **Status**: `ACCEPTED` (`MAJORITY_AGREE`)
- **Outcome Recorded On-Chain**:
  - `verdict`: `"CLEARED_ORIGINAL"`
  - `originality_score`: `100` (Discrete canonical score)
  - `is_derivative`: `false`
  - `authorization_verified`: `false`
  - `evidence_status_code`: `200`
  - `reasoning`: `"The submitted content is a sentence regarding distributed ledger research and has zero textual or conceptual overlap with the canonical reference, which is a .gitignore configuration file for Python."`
- **Downstream Clearance Gate (`is_cleared`)**:
  - `is_cleared(1, 70)`: `true` (Score 100 >= 70)
  - `is_cleared(1, 100)`: `true` (Score 100 >= 100)
  - `is_cleared(1, 101)`: `false` (Score 100 < 101)

---

## 3. Live Studionet CLI Verification Commands

```powershell
# Read submission record #1
genlayer call 0x40d5185Fc63107Cb794165271f51D91CEc64879B get_submission --args 1

# Read consensus evaluation receipt #2 (CLEARED_ORIGINAL score 100)
genlayer call 0x40d5185Fc63107Cb794165271f51D91CEc64879B get_evaluation --args 2

# Verify clearance gate (score 100 passes threshold 70)
genlayer call 0x40d5185Fc63107Cb794165271f51D91CEc64879B is_cleared --args 1 70

# Verify clearance gate at exact boundary 100
genlayer call 0x40d5185Fc63107Cb794165271f51D91CEc64879B is_cleared --args 1 100

# Verify threshold rejection beyond 100
genlayer call 0x40d5185Fc63107Cb794165271f51D91CEc64879B is_cleared --args 1 101
```
