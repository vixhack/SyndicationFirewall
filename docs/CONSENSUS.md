# Consensus Architecture & Equivalence Principle Binding (v1.0.1)

Author: vix

## 1. Overview & Re-architecture Summary

`SyndicationFirewall` v1.0.1 addresses the steward review findings regarding downstream threshold drift and submitter-controlled reference selection:
1. **Downstream Consensus Binding**: Eliminated continuous fuzzy score tolerances across decision thresholds. Validators must reach exact agreement on discrete canonical clearance buckets (`CLEARED_ORIGINAL: 100`, `CLEARED_AUTHORIZED_SYNDICATION: 85`, `FLAGGED_DERIVATIVE: 30`, `QUARANTINED_PLAGIARISM: 0`, `UNAVAILABLE: 0`).
2. **Independent Evidence Acquisition**: Rather than relying solely on submitter-controlled URLs or claims, validators independently acquire and verify licensing evidence from `license_proof_url` and evaluate publisher authorization. Content exhibiting overlap cannot be cleared as syndication without verified independent licensing evidence.

```
       +-----------------------------------------------------------+
       |                  GenLayer Studionet                       |
       |                                                           |
       |   Leader Node                      Validator Nodes        |
       |   +-----------------------+        +------------------+   |
       |   | 1. HTTP GET           |        | 1. Independent   |   |
       |   |    (canonical_url)    |        |    Fetch Ref     |   |
       |   | 2. HTTP GET           |        | 2. Independent   |   |
       |   |    (license_proof_url)|        |    Fetch License |   |
       |   | 3. LLM Adjudication   |        | 3. Equivalence   |   |
       |   |    Discrete Bucket    |        |    Verification  |   |
       |   | 4. Propose Result     |        |    (Exact Match) |   |
       |   +-----------+-----------+        +--------+---------+   |
       |               |                             |             |
       |               +--------------+--------------+             |
       |                              |                            |
       |                    Consensus Agreement                    |
       |                      (MAJORITY_AGREE)                     |
       |                              |                            |
       |                              v                            |
       |                  +-----------------------+                |
       |                  |  Deterministic State  |                |
       |                  |  - Canonical Scores   |                |
       |                  |    (100, 85, 30, 0)   |                |
       |                  |  - CLEARED / FLAGGED  |                |
       |                  |  - Immutable Receipt  |                |
       |                  +-----------------------+                |
       +-----------------------------------------------------------+
```

---

## 2. Non-Deterministic Boundary & Dual Evidence Acquisition

Non-deterministic operations are strictly quarantined within the leader-validator consensus execution of `evaluate_originality`:

1. **Independent Canonical Reference Retrieval**:
   - Executed via `gl.nondet.web.get(canonical_url)`.
   - Only secure public HTTPS endpoints are allowed (SSRF protection enforced).
   - Validators fetch the resource independently to verify data authenticity and HTTP status code. If unreachable, fails closed as `UNAVAILABLE`.

2. **Independent Licensing Evidence Acquisition**:
   - If submitter provides `license_proof_url`, validators independently fetch `license_proof_url`.
   - If licensing proof is missing, unreachable (HTTP $\ge 400$), or fails to confirm syndication authorization, the contract automatically downgrades derivative content to `FLAGGED_DERIVATIVE` (score 30).
   - Only content with verified independent licensing evidence can achieve `CLEARED_AUTHORIZED_SYNDICATION`.

3. **Comparative Semantic Analysis**:
   - Executed using `gl.nondet.exec_prompt(prompt, response_format="json")`.
   - The LLM compares submitted text against canonical reference document and independently acquired licensing evidence.
   - Output is mapped to canonical discrete buckets:
     ```json
     {
       "verdict": "CLEARED_ORIGINAL | CLEARED_AUTHORIZED_SYNDICATION | FLAGGED_DERIVATIVE | QUARANTINED_PLAGIARISM",
       "authorization_verified": true | false,
       "reasoning": "<string justification>"
     }
     ```

4. **Equivalence Principle & Custom Validator**:
   - Executed via `gl.vm.run_nondet_unsafe(evaluate, validate)`.
   - The validator function independently computes the evaluation and enforces **EXACT agreement**:
     - Exact agreement on canonical `verdict`.
     - Exact agreement on discrete canonical `originality_score` (100, 85, 30, 0) — zero continuous tolerance.
     - Exact agreement on `is_derivative`.
     - Exact agreement on `authorization_verified`.
     - Exact agreement on material clearance outcome (`is_cleared` compatibility).

---

## 3. Deterministic Boundary & Exact Threshold Binding

Once consensus resolves, all downstream state logic is 100% deterministic:

1. **Canonical Discrete Score Mapping**:
   - `CLEARED_ORIGINAL`: Canonical score `100`, `is_derivative = False`. Status: `CLEARED`.
   - `CLEARED_AUTHORIZED_SYNDICATION`: Canonical score `85`, `is_derivative = False`, `authorization_verified = True`. Status: `CLEARED`.
   - `FLAGGED_DERIVATIVE`: Canonical score `30`, `is_derivative = True`, `authorization_verified = False`. Status: `FLAGGED`.
   - `QUARANTINED_PLAGIARISM`: Canonical score `0`, `is_derivative = True`. Status: `QUARANTINED`.
   - `UNAVAILABLE`: Canonical score `0`, `is_derivative = True`. Status: `QUARANTINED`.

2. **Clearance Gate for Consumers (`is_cleared`)**:
   - Downstream contracts call `is_cleared(submission_id, min_originality)`.
   - Returns `True` iff `submission.active == True` AND `submission.status == "CLEARED"` AND `originality_score >= min_originality`.
   - Because canonical scores are discrete fixed values (100 for original, 85 for syndication) bound to consensus agreement, downstream threshold evaluation has zero probability of validator drift.

3. **Public Auditable View**:
   - `@gl.public.view def validate_equivalence(leader_json: str, validator_json: str) -> bool` exposes the deterministic equivalence verification logic for third-party explorers and verification pipelines.
