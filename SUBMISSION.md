# GenLayer Intelligent Contract Submission

## Basic Information

- **Contract Name**: SyndicationFirewall
- **Builder / Submitter**: vix
- **Category**: Content Provenance / Copyright & Plagiarism Defense / Grant Governance
- **License**: MIT
- **Canonical Address**: `0xEF723bc4D197fDcDcda32e853783DedDd49429c6`
- **Network**: GenLayer Studionet (Chain ID `61999`)
- **Explorer Link**: [https://explorer-studio.genlayer.com/address/0xEF723bc4D197fDcDcda32e853783DedDd49429c6](https://explorer-studio.genlayer.com/address/0xEF723bc4D197fDcDcda32e853783DedDd49429c6)

---

## 280-Character Short Pitch

> SyndicationFirewall protects on-chain publishing and grant distribution from plagiarism. GenLayer validators independently fetch canonical reference URLs, evaluate semantic originality via equivalence consensus, and fail-closed against copycat IP theft.

---

## Long Description

Decentralized grant allocation rounds (Gitcoin, Optimism RetroPGF), scientific research bounties, and web3 publishing platforms (Mirror, Paragraph) distribute millions in capital conditioned on original intellectual contribution. Traditional smart contracts have no native mechanism to verify whether a submitted paper or proposal was copy-pasted or paraphrased from an existing publication without relying on centralized, censorship-prone plagiarism APIs.

`SyndicationFirewall` is a standalone GenLayer Intelligent Contract primitive that provides decentralized originality verification and content provenance.

Using GenLayer's non-deterministic web retrieval and LLM equivalence capabilities, validators independently fetch canonical reference documents and compare submitted excerpts against published baselines. Validators reach multi-node consensus on semantic originality, categorizing submissions into `ORIGINAL`, `SYNDICATED`, or `PLAGIARIZED`, and recording an immutable originality score. Downstream contracts consume `is_cleared()` to enforce autonomous, fail-closed funding and minting gates.

---

## Verified On-Chain Evidence

- **Deployment Tx**: `0x0a20a69aa1bfad79dd0e107d47d75a906edaa15b5cd8f2a82e4aa99ffdeb1c09` (`MAJORITY_AGREE`, `ACCEPTED`)
- **Content Submission Tx**: `0xaa6a0c6df93d662b72ce06deaeb31263efbb1f4dfff7bf66e9e57a47c8470ecb` (`MAJORITY_AGREE`, `ACCEPTED`)
- **Live Semantic Originality Evaluation Tx**: `0x014821d3b98864f863d03c5b1a449c8778b9f6d2dd9677893ac77693656e1f08` (`MAJORITY_AGREE`, `ACCEPTED`, verdict `ORIGINAL`, score `98`)

---

## Verification Reproducibility

1. **Preflight Linting**: `python scripts/preflight.py` (16/16 checks pass).
2. **Direct Mode Unit Tests**: `python -m pytest tests/direct/test_syndication_firewall.py -v` (14/14 pass in 0.86s).
3. **Studionet Integration Tests**: `python -m pytest tests/integration/test_syndication_firewall_studionet.py -v` (5/5 pass in 43.39s).
