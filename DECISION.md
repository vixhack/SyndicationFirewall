# DECISION.md — SyndicationFirewall

## 1. Executive Primitive Thesis

`SyndicationFirewall` is a standalone GenLayer Intelligent Contract that protects on-chain publishing platforms, grant distribution protocols, and syndication networks from plagiarism, unauthorized copycat republishing, and intellectual property theft.

Given a submitted article or grant proposal text and a claimed or suspected canonical reference URL, GenLayer validators independently fetch the reference work, evaluate semantic similarity and originality under the Equivalence Principle, and record an immutable, consensus-backed originality receipt.

---

## 2. Builder Identity & Isolation

- **Builder**: `vix`
- **Deployer Signer**: `vixDeployer` (`0xb3b09558183aec6c2ff5aa547163b77a9266010a`)
- **Dedicated Testers**: `vixTesterOne` (`0x3278964d50d032549a37a1f5ceebf5628b030e94`), `vixTesterTwo` (`0xf9cf430e3860bb6392053f3e1b73e5bf0d937012`)
- **Isolation Policy**: Completely independent builder category with dedicated signers, zero cross-linking, and standalone repository structure.

---

## 3. Candidate Exploration & Selection Matrix

Ten candidate primitives were evaluated during architecture scouting:

| Candidate Primitive | Core Trust Question | GenLayer Necessity (0-10) | State Reusability | Status / Rejection Rationale |
| :--- | :--- | :---: | :---: | :--- |
| 1. `SyndicationFirewall` | Does submitted text plagiarize a canonical reference publication? | **10** | High | **SELECTED**: High-impact primitive for publishing, grants, research. |
| 2. `SocialSentimentIndex` | What is general social sentiment on token X? | 4 | Low | **REJECTED**: Sybil-prone, noisy, subjective chatter. |
| 3. `OnChainResume` | Did an applicant work at company Y? | 6 | Low | **REJECTED**: Requires private HR verification inaccessible to validators. |
| 4. `BugBountyCourt` | Does submitted vulnerability meet payout severity? | 8 | Medium | **REJECTED**: Highly domain-complex code exploit verification. |
| 5. `CodeAuditOracle` | Does a smart contract repository contain critical bugs? | 8 | Medium | **REJECTED**: Repository scale exceeds validator execution timeouts. |
| 6. `WeatherParametric` | Did rainfall fall below X mm? | 3 | Medium | **REJECTED**: Deterministic API numbers; traditional Chainlink suffices. |
| 7. `AgentTuringGate` | Is an external caller an autonomous agent? | 5 | Low | **REJECTED**: Adversarially unstable; heuristic rather than protocol primitive. |
| 8. `LegalContractSigner` | Did two parties sign a legal agreement? | 4 | Low | **REJECTED**: Static e-signature verification; better served by standard crypto. |
| 9. `ModelCardAuditor` | Did an AI model's safety weights/bias change? | 7 | Medium | **REJECTED**: Special case of policy drift with heavy binary dependencies. |
| 10. `DomainSquatShield` | Did a trademark holder's domain get hijacked? | 6 | Low | **REJECTED**: ICANN/WHOIS privacy blocks live validator inspection. |

---

## 4. Candidate Scoring & The Delete-GenLayer Test

### Scoring Dimensions (0–10)
1. **GenLayer Necessity**: 10/10 — Natural-language text comparison against live web publications cannot be performed deterministically without single-point-of-failure or naive byte-hashing failure.
2. **Ecosystem Utility**: 10/10 — Public grant rounds (Gitcoin, Optimism RetroPGF), decentralized publications (Mirror, Paragraph), and news syndicates urgently require sybil-resistant originality verification.
3. **State Machine & Failure Bounds**: 10/10 — Fail-closed on fetch errors; strict bounds on submissions; immutable audit records.

### The "Delete-GenLayer" Test
> *If GenLayer is removed, what exact trust property disappears?*
Without GenLayer, an application verifying whether a publication or proposal is plagiarized must either:
1. Rely on a **centralized off-chain API service** (Turnitin / Copyleaks), creating a centralized censorship point and vendor lock-in.
2. Rely on a **rigid sha256 byte hash**, which fails immediately if the plagiarist changes a single synonym, removes a sentence, or reformats markdown headers.

GenLayer is load-bearing because independent validators fetch the canonical source, read the prose, and reach consensus on whether the submitted text is **original, legitimate syndication with attribution, or copycat plagiarism**.

---

## 5. The Three-Consumer Test

`SyndicationFirewall` exposes a compact machine-readable view interface (`is_cleared`, `get_evaluation`, `latest_score`) consumed by three distinct architectures without modifying the primitive:

1. **Retroactive Grant Allocation Protocol (Gitcoin / RetroPGF)**:
   - A grant funding vault calls `is_cleared(submission_id, min_originality=75)`.
   - If a proposal is flagged as copycat plagiarism from an existing paper or project website, milestone disbursements are autonomously blocked.

2. **Decentralized Publishing Protocol (Mirror / Paragraph)**:
   - A publishing contract verifies that a submitted article is original before minting a commemorative entry NFT.
   - If `verdict == "SYNDICATED"`, it automatically routes a mandatory split royalty to the canonical author address.

3. **Autonomous Research Bounty Escrow**:
   - An escrow contract holding bounties for academic or technical research briefs verifies that the deliverable is not scraped from arXiv or Wikipedia before releasing collateral.

---

## 6. Deterministic vs. Non-Deterministic Boundary

```
+-------------------------------------------------------------+
| NON-DETERMINISTIC STAGE (Validators in GenVM)               |
| - Fetch canonical reference article via gl.get_webpage      |
| - Compare submitted text against fetched canonical content  |
| - Classify originality score (0-100) and verdict enum        |
| - Equivalence Principle: Consensus on score band & verdict  |
+-------------------------------------------------------------+
                              |
                              v (Structured observation)
+-------------------------------------------------------------+
| DETERMINISTIC STAGE (Contract Logic)                        |
| - Validate URL format, scheme (HTTPS), and SSRF denylist     |
| - Enforce text and title length bounds                      |
| - Enforce cooldown and status transitions                   |
| - Fail-closed on HTTP errors (unreachable canonical source) |
| - Map consensus evaluation into immutable audit receipt     |
| - Expose machine-readable boolean gate: is_cleared()        |
+-------------------------------------------------------------+
```
