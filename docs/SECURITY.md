# Security Model & Threat Mitigation (v1.0.1)

Author: vix

## 1. Threat Matrix

| Threat | Impact | Mitigation Strategy |
| :--- | :--- | :--- |
| **Server-Side Request Forgery (SSRF)** | Validators probe internal network addresses or cloud metadata services. | Strict URL validation rejecting non-HTTPS, localhost, private RFC-1918 IPs, and cloud metadata endpoints for both canonical and license URLs. |
| **Prompt Injection via Reference Text** | Malicious off-chain text attempts to override oracle instructions. | Delimiter encapsulation (`<canonical_reference>`, `<licensing_evidence>`), strict JSON schema output requirements, defensive fallback. |
| **Threshold Drift Across Consensus Boundary** | Continuous scores differing by tolerance cross decision boundaries (e.g. 75 vs 66 crossing threshold 70). | Enforce exact validator agreement on discrete canonical scores (100, 85, 30, 0) and canonical verdicts. |
| **Submitter-Controlled Unverified Syndication** | Submitter plagiarizes content, provides sole reference URL, and falsely claims syndication without proof. | Dual independent evidence acquisition: validators independently fetch `license_proof_url` and verify authorization. If evidence is missing or fails, content is downgraded to `FLAGGED_DERIVATIVE` and blocked from clearance. |
| **Denial of Service (Storage Bloat)** | Spammers submit massive text payloads to exhaust validator memory. | Bounded submission fields: title $\le 128$ chars, content $\le 8192$ chars, excerpt capped at $1000$ chars, URLs $\le 2048$ chars. |
| **Downstream Fund Drainage** | Plagiarized proposal receives automated grant funds due to ambiguous state. | Strict fail-closed boolean gate `is_cleared()` returning `False` on any unconfirmed, flagged, quarantined, or unverified status. |

---

## 2. SSRF Protection Specifications

The contract enforces strict validation on reference and licensing URLs in `_validate_url`:

```python
# 1. Scheme Enforcement
if not clean.startswith("https://"):
    raise gl.vm.UserError("Only secure HTTPS URLs are permitted")

# 2. Host Denylist
forbidden_patterns = (
    "://localhost",
    "://127.0.0.1",
    "://0.0.0.0",
    "://169.254.169.254", # AWS/GCP metadata
    "://10.",             # Class A private
    "://192.168.",        # Class C private
    "://172.16.",         # Class B private
    "://172.17.",
    "://172.18.",
    "://172.19.",
    "://172.20.",
    ".internal",
    ".local",
)
```

Both `canonical_url` and `license_proof_url` are validated with this filter before admission or web fetching.

---

## 3. Independent Evidence Acquisition & Syndication Grounding

In v1.0.0, the submitter controlled the comparison URL, and syndication claims lacked independent verification. In v1.0.1:
1. **Submitter-Provided Licensing Proof**: Submitter must provide `license_proof_url` and `syndication_id`.
2. **Independent Fetch**: Validators independently perform HTTP GET to `license_proof_url`.
3. **Mandatory Authorization Gate**: If `license_status_code != 200` or licensing text does not confirm syndication rights, the contract **automatically downgrades** the verdict to `FLAGGED_DERIVATIVE` (score 30, `authorization_verified = False`), even if the LLM output suggests syndication.
4. Content with overlap can NEVER be cleared as authorized syndication without independently verified proof.

---

## 4. Exact Consensus Binding on Decision Thresholds

In v1.0.0, a $\pm 10$ point continuous score tolerance allowed a leader score of 75 (cleared) and validator score of 66 (not cleared) to both pass consensus, creating downstream ambiguity.
In v1.0.1:
- Discrete canonical scores are enforced: `100` (Original), `85` (Authorized Syndication), `30` (Derivative), `0` (Plagiarism/Unavailable/Error).
- In `validate()`, validators require **EXACT agreement** on:
  - Canonical `verdict`
  - Discrete `originality_score`
  - `is_derivative` flag
  - `authorization_verified` flag
  - Material clearance outcome
- Zero fuzzy tolerance across thresholds.

---

## 5. Fail-Closed Architectural Principle

In automated grant release and publishing protocols, uncertainty must never result in permission.

- If a canonical reference server returns HTTP 404 or 500: `originality_score = 0`, `status = "QUARANTINED"`.
- If licensing evidence fails or is missing: `originality_score = 30`, `status = "FLAGGED"`.
- If model output cannot be parsed: `verdict = "ERROR"`, `originality_score = 0`, `is_derivative = True`, `status = "FLAGGED"`.
- If the submission is archived or inactive: `is_cleared()` returns `False`.
