# Consensus Architecture & Non-Deterministic Boundaries

Author: vix

## 1. Overview

`SyndicationFirewall` uses GenLayer's hybrid consensus architecture to bridge external digital publications, scientific preprints, and syndicated media with on-chain intellectual property gates.

Because external natural-language prose cannot be evaluated through static byte hashing without catastrophic vulnerability to trivial formatting edits or copycat paraphrasing, the contract enforces a strict separation between non-deterministic semantic observation and deterministic state execution.

```
       +-----------------------------------------------------------+
       |                  GenLayer Studionet                       |
       |                                                           |
       |   Leader Node                      Validator Nodes        |
       |   +-----------------------+        +------------------+   |
       |   | 1. HTTP GET           |        | 1. Independent   |   |
       |   |    (canonical_url)    |        |    Fetch & Check |   |
       |   | 2. LLM Originality    |        | 2. Equivalence   |   |
       |   |    Evaluation         |        |    Verification  |   |
       |   | 3. Propose Verdict    |        |    (Score Tol.)  |   |
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
       |                  |  - Immutable Receipt  |                |
       |                  |  - CLEARED / FLAGGED  |                |
       |                  |  - Boolean Gate Check |                |
       |                  +-----------------------+                |
       +-----------------------------------------------------------+
```

---

## 2. Non-Deterministic Boundary

Non-deterministic operations are strictly quarantined within the leader-validator consensus execution of `evaluate_originality`:

1. **Canonical Web Document Retrieval**:
   - Executed via `gl.nondet.web.get(canonical_url)`.
   - Only secure public HTTPS endpoints are allowed.
   - Validators fetch the resource independently to verify data authenticity and HTTP status code.

2. **Comparative Semantic Analysis**:
   - Executed using `gl.nondet.exec_prompt(prompt, response_format="json")`.
   - The LLM compares the submitted text excerpt against the fetched canonical reference text.
   - Output is constrained to a strict JSON schema:
     ```json
     {
       "verdict": "ORIGINAL | SYNDICATED | PLAGIARIZED",
       "originality_score": "<integer 0-100>",
       "is_derivative": "<boolean>",
       "reasoning": "<string justification>"
     }
     ```

3. **Equivalence Principle & Custom Validator**:
   - Executed via `gl.vm.run_nondet_unsafe(evaluate, validate)`.
   - The validator function independently computes the evaluation and enforces:
     - Exact agreement on `verdict` classification.
     - Exact agreement on `is_derivative` flag.
     - Tolerance floor: `originality_score` must agree within $\pm 10$ points.

---

## 3. Deterministic Boundary

Once consensus resolves the non-deterministic observation, all downstream state logic is 100% deterministic:

1. **Submission Status Transitions**:
   - If `verdict == "ORIGINAL"` and `originality_score >= 70`, `submission.status` deterministically transitions to `"CLEARED"`.
   - If `verdict == "SYNDICATED"`, `submission.status` deterministically transitions to `"CLEARED"`.
   - If `verdict == "PLAGIARIZED"` or `is_derivative == True`, `submission.status` deterministically transitions to `"FLAGGED"`.
   - If HTTP status != 200, `submission.status` deterministically transitions to `"QUARANTINED"`.

2. **Clearance Gate for Consumers**:
   - Downstream contracts call `is_cleared(submission_id, min_originality)`.
   - Rejects if the submission is inactive or archived.
   - Rejects if status is not `"CLEARED"`.
   - For `"ORIGINAL"`, deterministically validates `originality_score >= min_originality`.

3. **Bounding & Sanitation**:
   - All string inputs (titles, content, URLs) are strictly length-bounded.
   - Monotonic sequential indexing for all storage collections.
