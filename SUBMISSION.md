# GenLayer Intelligent Contract Resubmission (v1.0.1)

## Basic Information

- **Contract Name**: SyndicationFirewall
- **Builder / Submitter**: vix
- **Category**: Content Provenance / Copyright & Plagiarism Defense / Grant Governance
- **License**: MIT
- **Canonical Address**: `0x40d5185Fc63107Cb794165271f51D91CEc64879B`
- **Network**: GenLayer Studionet (Chain ID `61999`)
- **Explorer Link**: [https://explorer-studio.genlayer.com/address/0x40d5185Fc63107Cb794165271f51D91CEc64879B](https://explorer-studio.genlayer.com/address/0x40d5185Fc63107Cb794165271f51D91CEc64879B)

---

## 280-Character Short Pitch

> SyndicationFirewall safeguards on-chain publishing and grant distribution from IP theft. Validators independently acquire canonical references and licensing proofs, binding clearance outcomes to exact discrete consensus buckets (100/85/30/0) with zero threshold drift.

---

## Long Description & Resubmission Resolution

Decentralized grant allocation rounds (Gitcoin, Optimism RetroPGF), scientific research bounties, and web3 publishing platforms (Mirror, Paragraph) distribute millions in capital conditioned on original intellectual contribution. Traditional smart contracts have no native mechanism to verify whether a submitted paper or proposal was copy-pasted or paraphrased from an existing publication without relying on centralized, censorship-prone plagiarism APIs.

`SyndicationFirewall` is a standalone GenLayer Intelligent Contract primitive that provides decentralized originality verification, licensing evidence validation, and content provenance.

### Resolution of Reviewer Feedback:
1. **Consensus Binding of Downstream Clearance Outcomes**:
   - Replaced continuous fuzzy integer scores with discrete canonical clearance buckets:
     - `CLEARED_ORIGINAL` (Canonical Score: `100`, `is_cleared` = `True`)
     - `CLEARED_AUTHORIZED_SYNDICATION` (Canonical Score: `85`, `is_cleared` = `True`, requires verified licensing)
     - `FLAGGED_DERIVATIVE` (Canonical Score: `30`, `is_cleared` = `False`)
     - `QUARANTINED_PLAGIARISM` (Canonical Score: `0`, `is_cleared` = `False`)
     - `UNAVAILABLE` (Canonical Score: `0`, `is_cleared` = `False`)
   - In `validate()`, validators require **exact agreement** on the canonical verdict, discrete score, derivative status, and authorization verification. This eliminates any possibility of validator scores differing across downstream threshold boundaries.
2. **Independent Evidence Acquisition for Syndication & Reference Grounding**:
   - Submissions include verifiable licensing proof references (`license_proof_url`, `syndication_id`).
   - Validators independently fetch and inspect licensing evidence directly from the web (`gl.nondet.web.get(license_proof_url)`).
   - If licensing evidence fails or is missing, derivative work is **automatically downgraded** to `FLAGGED_DERIVATIVE` (Score 30) and blocked from clearance, preventing submitters from circumventing originality checks via unverified syndication claims.
3. **Auditable Equivalence Principle View**:
   - Added `@gl.public.view def validate_equivalence(leader_json, validator_json) -> bool` to expose deterministic consensus validation for external verification.

---

## Verified On-Chain Evidence

- **Deployment Tx**: `0xa84b8a13b1e5aabcf8510fe382cbec6113fc399069842e69f859557164a671aa` (`MAJORITY_AGREE`, `ACCEPTED`)
- **Content Submission Tx**: `0x00d2110a18bec25b2238a377ece7f464f5b07530d340a9078ccc41ebbea5b631` (`MAJORITY_AGREE`, `ACCEPTED`)
- **Fail-Closed 404 Reference Evaluation Tx**: `0x6ac6b921cc58b43bcd2ee5c0c89f9222f91c188e7f3b919cfd0a141f8af9a625` (`MAJORITY_AGREE`, `ACCEPTED`, verdict `UNAVAILABLE`, score `0`, `is_cleared` = `False`)
- **Canonical Reference Update Tx**: `0x11cad61d6b5b748ff16bf5982ab96a07ee7170308cda4dc392fd3618c7847e55` (`MAJORITY_AGREE`, 5/5 AGREE)
- **Live Multi-Validator Semantic Originality Evaluation Tx**: `0xbe5f8e03c46b4e987e56a34e746c647cd540f66d97effe85cc47378c8def967f` (`MAJORITY_AGREE`, `ACCEPTED`, verdict `CLEARED_ORIGINAL`, discrete score `100`, `is_cleared(1, 70)` = `True`, `is_cleared(1, 100)` = `True`, `is_cleared(1, 101)` = `False`)

---

## Verification Reproducibility

1. **Preflight Linting**: `python scripts/preflight.py` (16/16 checks pass).
2. **Direct Mode Unit Tests**: `python -m pytest tests/direct/test_syndication_firewall.py -v` (18/18 pass in 1.76s).
3. **Studionet Integration Tests**: `python -m pytest tests/integration/test_syndication_firewall_studionet.py -v` (5/5 pass in 48.73s).
