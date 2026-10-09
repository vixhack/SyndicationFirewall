# Studionet Canonical Deployment Record

Author: vix

## 1. Network & Deployment Summary

| Parameter | Value |
| :--- | :--- |
| **Network** | GenLayer Studionet |
| **Chain ID** | `61999` |
| **Canonical Contract Address** | `0xEF723bc4D197fDcDcda32e853783DedDd49429c6` |
| **Deployer Address** | `0xb3b09558183aec6c2ff5aa547163b77a9266010a` (`vixDeployer`) |
| **Deployment Transaction** | `0x0a20a69aa1bfad79dd0e107d47d75a906edaa15b5cd8f2a82e4aa99ffdeb1c09` |
| **Consensus Result** | `MAJORITY_AGREE` |
| **Status** | `ACCEPTED` / `FINALIZED` |
| **Explorer URL** | [GenLayer Explorer](https://explorer-studio.genlayer.com/address/0xEF723bc4D197fDcDcda32e853783DedDd49429c6) |

---

## 2. On-Chain Transaction & Consensus Log

### Deployment Transaction
- **Tx Hash**: `0x0a20a69aa1bfad79dd0e107d47d75a906edaa15b5cd8f2a82e4aa99ffdeb1c09`
- **Sender**: `0xb3b09558183aec6c2ff5aa547163b77a9266010a`
- **Result**: Contract initialized with zero submissions and zero evaluations.

### Transaction 1: Content Submission
- **Method**: `submit_content`
- **Tx Hash**: `0xaa6a0c6df93d662b72ce06deaeb31263efbb1f4dfff7bf66e9e57a47c8470ecb`
- **Status**: `ACCEPTED` (`MAJORITY_AGREE`)
- **Parameters**:
  - `title`: `"Decentralized Compute Scaling"`
  - `content`: `"This proposal presents an optimized pipeline for decentralized compute allocation."`
  - `canonical_url`: `"https://raw.githubusercontent.com/ethereum/solidity/develop/README.md"`

### Transaction 2: Non-Deterministic Consensus Originality Evaluation
- **Method**: `evaluate_originality`
- **Tx Hash**: `0x014821d3b98864f863d03c5b1a449c8778b9f6d2dd9677893ac77693656e1f08`
- **Status**: `ACCEPTED` (`MAJORITY_AGREE`)
- **Outcome Recorded On-Chain**:
  - `verdict`: `"ORIGINAL"`
  - `originality_score`: `98`
  - `is_derivative`: `false`
  - `evidence_status_code`: `200`
  - `reasoning`: `"The submitted sentence does not overlap materially with the canonical Solidity reference in wording, structure, or subject matter. It appears to be an unrelated, original statement with minimal to no detectable copying."`

---

## 3. Live Verification Commands

```powershell
# Read submission record #1
genlayer call 0xEF723bc4D197fDcDcda32e853783DedDd49429c6 get_submission --args 1

# Read consensus evaluation receipt #1
genlayer call 0xEF723bc4D197fDcDcda32e853783DedDd49429c6 get_evaluation --args 1

# Verify clearance gate (score 98 passes threshold 75)
genlayer call 0xEF723bc4D197fDcDcda32e853783DedDd49429c6 is_cleared --args 1 75

# Verify threshold enforcement (score 98 fails threshold 99)
genlayer call 0xEF723bc4D197fDcDcda32e853783DedDd49429c6 is_cleared --args 1 99
```
