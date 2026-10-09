# Downstream Integration Guide

Author: vix

`SyndicationFirewall` provides a standardized on-chain originality and copyright gate for decentralized publishing, retroactive grant programs, and media syndication escrows.

---

## 1. Interface Specification

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

interface ISyndicationFirewall {
    struct Submission {
        uint256 id;
        address submitter;
        string title;
        string content_excerpt;
        string canonical_url;
        string status; // "PENDING", "CLEARED", "FLAGGED", "QUARANTINED"
        uint32 latest_evaluation_id;
        bool active;
        uint64 created_at;
        uint32 total_evaluations;
    }

    struct EvaluationReceipt {
        uint32 id;
        uint256 submission_id;
        string verdict; // "ORIGINAL", "SYNDICATED", "PLAGIARIZED", "UNAVAILABLE", "ERROR"
        uint32 originality_score; // 0 to 100
        bool is_derivative;
        uint32 evidence_status_code;
        uint64 evaluated_at;
        string reasoning;
    }

    function is_cleared(uint256 submission_id, uint32 min_originality) external view returns (bool);
    function latest_verdict(uint256 submission_id) external view returns (string memory, uint32, bool);
    function get_submission(uint256 submission_id) external view returns (Submission memory);
    function get_evaluation(uint32 evaluation_id) external view returns (EvaluationReceipt memory);
}
```

---

## 2. Example: Retroactive Grant Disbursement Vault (Solidity)

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "./ISyndicationFirewall.sol";

contract RetroGrantDisbursementVault {
    ISyndicationFirewall public immutable firewall;
    uint32 public immutable requiredOriginalityThreshold;

    event GrantDisbursed(uint256 indexed submissionId, address indexed recipient, uint256 amount);
    event GrantBlocked(uint256 indexed submissionId, string reason);

    constructor(address _firewall, uint32 _minOriginality) {
        firewall = ISyndicationFirewall(_firewall);
        requiredOriginalityThreshold = _minOriginality;
    }

    /// @notice Releases retroactive grant funding only if proposal passes originality check
    function disburseGrant(uint256 submissionId, address payable recipient, uint256 amount) external {
        // 1. Verify firewall clearance
        bool cleared = firewall.is_cleared(submissionId, requiredOriginalityThreshold);
        require(cleared, "GrantVault: Proposal flagged as plagiarized or failed originality threshold");

        // 2. Disburse funds
        require(address(this).balance >= amount, "GrantVault: Insufficient liquidity");
        recipient.transfer(amount);

        emit GrantDisbursed(submissionId, recipient, amount);
    }
}
```

---

## 3. Example: GenLayer Python Publishing Gate

```python
import genlayer.gl as gl

class AutonomousMediaPublishingGate(gl.Contract):
    def __init__(self, firewall_address: str):
        self.firewall_address = firewall_address

    @gl.public.write
    def publish_article(self, submission_id: int) -> bool:
        # Query canonical firewall clearance gate
        firewall = gl.get_contract(self.firewall_address)
        is_cleared = firewall.is_cleared(submission_id, 75)
        
        if not is_cleared:
            raise gl.vm.UserError("Publishing rejected: content failed originality verification")
        
        return True
```
