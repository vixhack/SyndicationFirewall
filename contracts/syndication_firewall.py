# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }

"""SyndicationFirewall v1.0.1: Autonomous Content Provenance & Anti-Plagiarism Firewall.

Author: vix
A standalone GenLayer Intelligent Contract primitive that audits submitted digital content,
grant proposals, and syndicated journalism against claimed or suspected canonical reference URLs.
Validators independently fetch canonical reference documents and independent licensing evidence,
enforcing discrete canonical clearance outcomes and exact consensus binding under the
Equivalence Principle.
"""

from dataclasses import dataclass
from datetime import datetime, timezone
import json

from genlayer import *


def _coerce_to_str(val) -> str:
    if isinstance(val, int):
        return hex(val)
    return str(val)


@allow_storage
@dataclass
class Submission:
    id: u256
    submitter: Address
    title: str
    content_excerpt: str
    canonical_url: str
    license_proof_url: str
    syndication_id: str
    status: str  # "PENDING", "CLEARED", "FLAGGED", "QUARANTINED"
    latest_evaluation_id: u32
    active: bool
    created_at: u64
    total_evaluations: u32


@allow_storage
@dataclass
class EvaluationReceipt:
    id: u32
    submission_id: u256
    verdict: str  # "CLEARED_ORIGINAL", "CLEARED_AUTHORIZED_SYNDICATION", "FLAGGED_DERIVATIVE", "QUARANTINED_PLAGIARISM", "UNAVAILABLE", "ERROR"
    originality_score: u32  # Discrete canonical scores: 100, 85, 30, 0
    is_derivative: bool
    authorization_verified: bool
    evidence_status_code: u32
    license_status_code: u32
    evaluated_at: u64
    reasoning: str


class SyndicationFirewall(gl.Contract):
    VERSION = "1.0.1"

    # Status Constants
    STATUS_PENDING = "PENDING"
    STATUS_CLEARED = "CLEARED"
    STATUS_FLAGGED = "FLAGGED"
    STATUS_QUARANTINED = "QUARANTINED"

    # Canonical Verdict Buckets
    VERDICT_CLEARED_ORIGINAL = "CLEARED_ORIGINAL"
    VERDICT_CLEARED_SYNDICATION = "CLEARED_AUTHORIZED_SYNDICATION"
    VERDICT_FLAGGED_DERIVATIVE = "FLAGGED_DERIVATIVE"
    VERDICT_QUARANTINED_PLAGIARISM = "QUARANTINED_PLAGIARISM"
    VERDICT_UNAVAILABLE = "UNAVAILABLE"
    VERDICT_ERROR = "ERROR"

    # Backward compatibility aliases
    VERDICT_ORIGINAL = "CLEARED_ORIGINAL"
    VERDICT_SYNDICATED = "CLEARED_AUTHORIZED_SYNDICATION"
    VERDICT_PLAGIARIZED = "QUARANTINED_PLAGIARISM"

    # Discrete Canonical Scores bound to Consensus Buckets
    SCORE_ORIGINAL = 100
    SCORE_SYNDICATION = 85
    SCORE_DERIVATIVE = 30
    SCORE_PLAGIARISM = 0
    SCORE_UNAVAILABLE = 0
    SCORE_ERROR = 0

    # Bounds
    MIN_TITLE_LENGTH = 1
    MAX_TITLE_LENGTH = 128
    MIN_CONTENT_LENGTH = 1
    MAX_CONTENT_LENGTH = 8192
    MAX_URL_LENGTH = 2048
    MAX_ID_LENGTH = 128
    MAX_EXCERPT_CHARS = 1000
    MAX_REFERENCE_CHARS = 4000

    submission_count: u256
    evaluation_count: u32

    submissions: TreeMap[u256, Submission]
    evaluations: TreeMap[u32, EvaluationReceipt]

    def __init__(self):
        self.submission_count = u256(0)
        self.evaluation_count = u32(0)

    # -------------------------------------------------------------
    # Internal Validation Helpers
    # -------------------------------------------------------------

    def _now(self) -> u64:
        return u64(int(datetime.now(timezone.utc).timestamp()))

    def _validate_url(self, url: str) -> str:
        clean = url.strip()
        if len(clean) == 0 or len(clean) > self.MAX_URL_LENGTH:
            raise gl.vm.UserError("URL length out of bounds")
        if not clean.startswith("https://"):
            raise gl.vm.UserError("Only secure HTTPS URLs are permitted")

        lower = clean.lower()
        forbidden_patterns = (
            "://localhost",
            "://127.0.0.1",
            "://0.0.0.0",
            "://169.254.169.254",
            "://10.",
            "://192.168.",
            "://172.16.",
            "://172.17.",
            "://172.18.",
            "://172.19.",
            "://172.20.",
            ".internal",
            ".local",
        )
        for pattern in forbidden_patterns:
            if pattern in lower:
                raise gl.vm.UserError(f"Prohibited host or IP in URL: {pattern}")

        return clean

    def _validate_url_optional(self, url: str) -> str:
        clean = url.strip()
        if len(clean) == 0 or clean.upper() == "NONE":
            return ""
        return self._validate_url(clean)

    def _normalize_evaluation_payload(
        self,
        raw: dict,
        evidence_status_code: int = 200,
        license_status_code: int = 0,
    ) -> dict:
        """Sanitize and map model output to guaranteed canonical clearance buckets and discrete scores."""
        raw_verdict = str(raw.get("verdict", self.VERDICT_ERROR)).strip().upper()

        # Handle legacy or alternative names gracefully
        if raw_verdict in ("ORIGINAL", "CLEARED_ORIGINAL"):
            verdict = self.VERDICT_CLEARED_ORIGINAL
            score = self.SCORE_ORIGINAL
            is_derivative = False
            authorization_verified = False
        elif raw_verdict in ("SYNDICATED", "CLEARED_SYNDICATION", "CLEARED_AUTHORIZED_SYNDICATION"):
            # Enforce that syndication can only be cleared if authorization was verified
            # AND license proof was provided and retrieved successfully
            auth_claimed = bool(raw.get("authorization_verified", True))
            if auth_claimed and (license_status_code == 200 or license_status_code == 0 and "license" in str(raw).lower()):
                verdict = self.VERDICT_CLEARED_SYNDICATION
                score = self.SCORE_SYNDICATION
                is_derivative = False
                authorization_verified = True
            else:
                # Without valid independent licensing evidence, content cannot be cleared as syndication!
                verdict = self.VERDICT_FLAGGED_DERIVATIVE
                score = self.SCORE_DERIVATIVE
                is_derivative = True
                authorization_verified = False
        elif raw_verdict in ("DERIVATIVE", "FLAGGED_DERIVATIVE"):
            verdict = self.VERDICT_FLAGGED_DERIVATIVE
            score = self.SCORE_DERIVATIVE
            is_derivative = True
            authorization_verified = False
        elif raw_verdict in ("PLAGIARIZED", "QUARANTINED_PLAGIARISM"):
            verdict = self.VERDICT_QUARANTINED_PLAGIARISM
            score = self.SCORE_PLAGIARISM
            is_derivative = True
            authorization_verified = False
        elif raw_verdict == self.VERDICT_UNAVAILABLE:
            verdict = self.VERDICT_UNAVAILABLE
            score = self.SCORE_UNAVAILABLE
            is_derivative = True
            authorization_verified = False
        else:
            verdict = self.VERDICT_ERROR
            score = self.SCORE_ERROR
            is_derivative = True
            authorization_verified = False

        reasoning = str(raw.get("reasoning", "")).strip()[:500]
        ev_code = int(raw.get("evidence_status_code", evidence_status_code))
        lic_code = int(raw.get("license_status_code", license_status_code))

        return {
            "verdict": verdict,
            "originality_score": score,
            "is_derivative": is_derivative,
            "authorization_verified": authorization_verified,
            "reasoning": reasoning,
            "evidence_status_code": ev_code,
            "license_status_code": lic_code,
        }

    # -------------------------------------------------------------
    # Public State-Changing Methods
    # -------------------------------------------------------------

    @gl.public.write
    def submit_content(
        self,
        title: str,
        content: str,
        canonical_url: str,
        license_proof_url: str = "",
        syndication_id: str = "",
    ) -> u256:
        clean_title = title.strip()
        clean_content = content.strip()
        clean_url = self._validate_url(canonical_url)
        clean_license_url = self._validate_url_optional(license_proof_url)
        clean_synd_id = syndication_id.strip()[:self.MAX_ID_LENGTH]

        if len(clean_title) < self.MIN_TITLE_LENGTH or len(clean_title) > self.MAX_TITLE_LENGTH:
            raise gl.vm.UserError("Title length out of bounds")
        if len(clean_content) < self.MIN_CONTENT_LENGTH or len(clean_content) > self.MAX_CONTENT_LENGTH:
            raise gl.vm.UserError("Content length out of bounds")

        self.submission_count += u256(1)
        sub_id = self.submission_count

        excerpt = clean_content[:self.MAX_EXCERPT_CHARS]
        now_ts = self._now()

        submission = Submission(
            id=sub_id,
            submitter=gl.message.sender_address,
            title=clean_title,
            content_excerpt=excerpt,
            canonical_url=clean_url,
            license_proof_url=clean_license_url,
            syndication_id=clean_synd_id,
            status=self.STATUS_PENDING,
            latest_evaluation_id=u32(0),
            active=True,
            created_at=now_ts,
            total_evaluations=u32(0),
        )

        self.submissions[sub_id] = submission
        return sub_id

    @gl.public.write
    def update_canonical_url(self, submission_id: u256, new_url: str) -> None:
        if isinstance(submission_id, int):
            submission_id = u256(submission_id)

        if submission_id not in self.submissions:
            raise gl.vm.UserError("Submission not found")

        sub = self.submissions[submission_id]
        if gl.message.sender_address != sub.submitter:
            raise gl.vm.UserError("Only submitter can update canonical URL")

        clean_url = self._validate_url(new_url)
        sub.canonical_url = clean_url
        sub.status = self.STATUS_PENDING
        self.submissions[submission_id] = sub

    @gl.public.write
    def update_licensing_evidence(
        self,
        submission_id: u256,
        new_license_url: str,
        new_syndication_id: str,
    ) -> None:
        if isinstance(submission_id, int):
            submission_id = u256(submission_id)

        if submission_id not in self.submissions:
            raise gl.vm.UserError("Submission not found")

        sub = self.submissions[submission_id]
        if gl.message.sender_address != sub.submitter:
            raise gl.vm.UserError("Only submitter can update licensing evidence")

        sub.license_proof_url = self._validate_url_optional(new_license_url)
        sub.syndication_id = new_syndication_id.strip()[:self.MAX_ID_LENGTH]
        sub.status = self.STATUS_PENDING
        self.submissions[submission_id] = sub

    @gl.public.write
    def archive_submission(self, submission_id: u256) -> None:
        if isinstance(submission_id, int):
            submission_id = u256(submission_id)

        if submission_id not in self.submissions:
            raise gl.vm.UserError("Submission not found")

        sub = self.submissions[submission_id]
        if gl.message.sender_address != sub.submitter:
            raise gl.vm.UserError("Only submitter can archive submission")

        sub.active = False
        sub.status = self.STATUS_QUARANTINED
        self.submissions[submission_id] = sub

    @gl.public.write
    def evaluate_originality(self, submission_id: u256) -> u32:
        if isinstance(submission_id, int):
            submission_id = u256(submission_id)

        if submission_id not in self.submissions:
            raise gl.vm.UserError("Submission does not exist")

        sub = self.submissions[submission_id]
        if not sub.active:
            raise gl.vm.UserError("Cannot evaluate an archived submission")

        # Snapshot parameters for non-deterministic execution
        target_url = sub.canonical_url
        license_url = sub.license_proof_url
        synd_id = sub.syndication_id
        submitted_excerpt = sub.content_excerpt
        max_ref_chars = self.MAX_REFERENCE_CHARS

        def evaluate() -> dict:
            # 1. Fetch canonical reference document independently
            try:
                ref_response = gl.nondet.web.get(target_url)
                ref_status = ref_response.status
            except Exception:
                ref_status = 500

            if ref_status >= 400:
                return self._normalize_evaluation_payload(
                    {
                        "verdict": self.VERDICT_UNAVAILABLE,
                        "originality_score": self.SCORE_UNAVAILABLE,
                        "is_derivative": True,
                        "authorization_verified": False,
                        "reasoning": f"Canonical reference unavailable: HTTP {ref_status}.",
                    },
                    evidence_status_code=ref_status,
                    license_status_code=0,
                )

            body_str = ref_response.body.decode("utf-8", errors="replace").strip()
            if len(body_str) == 0:
                return self._normalize_evaluation_payload(
                    {
                        "verdict": self.VERDICT_UNAVAILABLE,
                        "originality_score": self.SCORE_UNAVAILABLE,
                        "is_derivative": True,
                        "authorization_verified": False,
                        "reasoning": "Canonical reference returned an empty document.",
                    },
                    evidence_status_code=ref_status,
                    license_status_code=0,
                )

            bounded_ref = body_str[:max_ref_chars]

            # 2. Independently acquire licensing authorization evidence if provided
            license_body = ""
            lic_status = 0
            if len(license_url) > 0:
                try:
                    lic_resp = gl.nondet.web.get(license_url)
                    lic_status = lic_resp.status
                    if lic_status < 400:
                        license_body = lic_resp.body.decode("utf-8", errors="replace").strip()[:max_ref_chars]
                except Exception:
                    lic_status = 500
            else:
                license_body = "NO_INDEPENDENT_LICENSING_PROOF_PROVIDED"

            # 3. Adjudicate originality and syndication authorization
            prompt = f"""You are an impartial GenLayer validator magistrate adjudicating copyright, content provenance, syndication licensing, and plagiarism.
Compare the submitted content excerpt against the canonical reference document and any independently acquired licensing proof.

CANONICAL REFERENCE DOCUMENT (from {target_url}):
<canonical_reference>
{bounded_ref}
</canonical_reference>

SUBMITTED CONTENT:
<submitted_content>
{submitted_excerpt}
</submitted_content>

CLAIMED SYNDICATION IDENTIFIER:
{synd_id if synd_id else "NONE"}

INDEPENDENTLY ACQUIRED LICENSING EVIDENCE (from {license_url if license_url else "N/A"}):
<licensing_evidence>
{license_body}
</licensing_evidence>

EVALUATION RULES:
1. ORIGINAL: If the submitted content is genuinely original and novel with minimal conceptual or textual overlap with the canonical reference document, return verdict "CLEARED_ORIGINAL". (No syndication license required).
2. AUTHORIZED SYNDICATION: If the submitted content exhibits material overlap with the canonical reference document, it can ONLY be cleared as authorized syndication if the independently acquired licensing evidence explicitly confirms syndication, republication, or Creative Commons distribution rights authorizing this content or matching the claimed syndication identifier. If valid independent authorization is confirmed, return verdict "CLEARED_AUTHORIZED_SYNDICATION".
3. UNLICENSED DERIVATIVE: If the submitted content exhibits material overlap or paraphrased derivation from the canonical reference, BUT licensing evidence is missing, invalid, or fails to authorize republication, return verdict "FLAGGED_DERIVATIVE".
4. PLAGIARISM: If the submitted content is substantial verbatim or near-verbatim copycat duplication without independent authorization or transformative commentary, return verdict "QUARANTINED_PLAGIARISM".

OUTPUT FORMAT:
Respond with ONLY valid JSON:
{{
  "verdict": "CLEARED_ORIGINAL" | "CLEARED_AUTHORIZED_SYNDICATION" | "FLAGGED_DERIVATIVE" | "QUARANTINED_PLAGIARISM",
  "authorization_verified": true | false,
  "reasoning": "Concise factual justification"
}}
"""
            try:
                result = gl.nondet.exec_prompt(prompt, response_format="json")
                if isinstance(result, str):
                    result = json.loads(result)
            except Exception:
                result = {"verdict": self.VERDICT_ERROR, "reasoning": "LLM adjudication failed"}

            if not isinstance(result, dict):
                result = {"verdict": self.VERDICT_ERROR, "reasoning": "Malformed LLM response"}

            return self._normalize_evaluation_payload(
                result,
                evidence_status_code=ref_status,
                license_status_code=lic_status,
            )

        def validate(leader_result: gl.vm.Result) -> bool:
            if not isinstance(leader_result, gl.vm.Return):
                return False
            try:
                leader_val = self._normalize_evaluation_payload(leader_result.calldata)
                validator_val = evaluate()

                # Verdict agreement (exact canonical bucket)
                if leader_val["verdict"] != validator_val["verdict"]:
                    return False

                # Exact canonical discrete score agreement (100, 85, 30, 0) - no fuzzy tolerance!
                if int(leader_val["originality_score"]) != int(validator_val["originality_score"]):
                    return False

                # Agreement on whether derivative
                if leader_val["is_derivative"] != validator_val["is_derivative"]:
                    return False

                # Agreement on independent authorization verification
                if leader_val["authorization_verified"] != validator_val["authorization_verified"]:
                    return False

                # Exact agreement on material clearance outcome
                leader_cleared = leader_val["verdict"] in (
                    self.VERDICT_CLEARED_ORIGINAL,
                    self.VERDICT_CLEARED_SYNDICATION,
                )
                validator_cleared = validator_val["verdict"] in (
                    self.VERDICT_CLEARED_ORIGINAL,
                    self.VERDICT_CLEARED_SYNDICATION,
                )
                if leader_cleared != validator_cleared:
                    return False

                return True
            except Exception:
                return False

        eval_payload = gl.vm.run_nondet_unsafe(
            evaluate,
            validate,
        )

        self.evaluation_count += u32(1)
        eval_id = self.evaluation_count

        now_ts = self._now()
        receipt = EvaluationReceipt(
            id=eval_id,
            submission_id=submission_id,
            verdict=eval_payload["verdict"],
            originality_score=u32(eval_payload["originality_score"]),
            is_derivative=eval_payload["is_derivative"],
            authorization_verified=eval_payload["authorization_verified"],
            evidence_status_code=u32(eval_payload["evidence_status_code"]),
            license_status_code=u32(eval_payload["license_status_code"]),
            evaluated_at=now_ts,
            reasoning=eval_payload["reasoning"],
        )
        self.evaluations[eval_id] = receipt

        # Deterministic status update directly bound to canonical consensus bucket
        if receipt.verdict == self.VERDICT_CLEARED_ORIGINAL:
            sub.status = self.STATUS_CLEARED
        elif receipt.verdict == self.VERDICT_CLEARED_SYNDICATION:
            sub.status = self.STATUS_CLEARED
        elif receipt.verdict == self.VERDICT_FLAGGED_DERIVATIVE:
            sub.status = self.STATUS_FLAGGED
        elif receipt.verdict == self.VERDICT_QUARANTINED_PLAGIARISM:
            sub.status = self.STATUS_QUARANTINED
        elif receipt.verdict == self.VERDICT_UNAVAILABLE:
            sub.status = self.STATUS_QUARANTINED
        else:
            sub.status = self.STATUS_FLAGGED

        sub.latest_evaluation_id = eval_id
        sub.total_evaluations += u32(1)
        self.submissions[submission_id] = sub

        return eval_id

    # -------------------------------------------------------------
    # Public View Interface
    # -------------------------------------------------------------

    @gl.public.view
    def get_submission(self, submission_id: u256) -> dict:
        if isinstance(submission_id, int):
            submission_id = u256(submission_id)
        if submission_id not in self.submissions:
            raise gl.vm.UserError("Submission not found")
        sub = self.submissions[submission_id]
        return {
            "id": int(sub.id),
            "submitter": _coerce_to_str(sub.submitter),
            "title": sub.title,
            "content_excerpt": sub.content_excerpt,
            "canonical_url": sub.canonical_url,
            "license_proof_url": sub.license_proof_url,
            "syndication_id": sub.syndication_id,
            "status": sub.status,
            "latest_evaluation_id": int(sub.latest_evaluation_id),
            "active": sub.active,
            "created_at": int(sub.created_at),
            "total_evaluations": int(sub.total_evaluations),
        }

    @gl.public.view
    def get_evaluation(self, evaluation_id: u32) -> dict:
        if isinstance(evaluation_id, int):
            evaluation_id = u32(evaluation_id)
        if evaluation_id not in self.evaluations:
            raise gl.vm.UserError("Evaluation not found")
        ev = self.evaluations[evaluation_id]
        return {
            "id": int(ev.id),
            "submission_id": int(ev.submission_id),
            "verdict": ev.verdict,
            "originality_score": int(ev.originality_score),
            "is_derivative": ev.is_derivative,
            "authorization_verified": ev.authorization_verified,
            "evidence_status_code": int(ev.evidence_status_code),
            "license_status_code": int(ev.license_status_code),
            "evaluated_at": int(ev.evaluated_at),
            "reasoning": ev.reasoning,
        }

    @gl.public.view
    def latest_verdict(self, submission_id: u256) -> tuple[str, int, bool]:
        if isinstance(submission_id, int):
            submission_id = u256(submission_id)
        if submission_id not in self.submissions:
            raise gl.vm.UserError("Submission not found")
        sub = self.submissions[submission_id]
        eval_id = sub.latest_evaluation_id
        if eval_id == 0 or eval_id not in self.evaluations:
            return (self.STATUS_PENDING, 0, False)
        ev = self.evaluations[eval_id]
        return (ev.verdict, int(ev.originality_score), ev.is_derivative)

    @gl.public.view
    def is_cleared(self, submission_id: u256, min_originality: u32) -> bool:
        """Determines if a submission is cleared for publication/escrow release.
        The result is strictly bound to validator consensus on canonical discrete scores
        (100 for original, 85 for authorized syndication), ensuring consensus directly
        binds the clearance outcome with zero threshold drift.
        """
        if isinstance(submission_id, int):
            submission_id = u256(submission_id)
        if isinstance(min_originality, int):
            min_originality = u32(min_originality)

        if submission_id not in self.submissions:
            return False
        sub = self.submissions[submission_id]
        if not sub.active or sub.status != self.STATUS_CLEARED:
            return False

        eval_id = sub.latest_evaluation_id
        if eval_id == 0 or eval_id not in self.evaluations:
            return False

        ev = self.evaluations[eval_id]
        if ev.verdict in (self.VERDICT_CLEARED_ORIGINAL, self.VERDICT_CLEARED_SYNDICATION):
            return int(ev.originality_score) >= int(min_originality)
        return False

    @gl.public.view
    def validate_equivalence(self, leader_payload_json: str, validator_payload_json: str) -> bool:
        """Deterministic public view of the Equivalence Principle consensus algorithm.
        Enforces exact agreement on canonical verdict, discrete score, derivative status,
        authorization verification, and material clearance outcome.
        """
        try:
            if isinstance(leader_payload_json, str):
                leader_val = json.loads(leader_payload_json)
            else:
                leader_val = dict(leader_payload_json)

            if isinstance(validator_payload_json, str):
                validator_val = json.loads(validator_payload_json)
            else:
                validator_val = dict(validator_payload_json)

            leader_norm = self._normalize_evaluation_payload(leader_val)
            validator_norm = self._normalize_evaluation_payload(validator_val)

            # Exact verdict agreement
            if leader_norm["verdict"] != validator_norm["verdict"]:
                return False

            # Exact canonical discrete score agreement (no fuzzy tolerance!)
            if int(leader_norm["originality_score"]) != int(validator_norm["originality_score"]):
                return False

            # Exact derivative status agreement
            if leader_norm["is_derivative"] != validator_norm["is_derivative"]:
                return False

            # Exact authorization verification agreement
            if leader_norm["authorization_verified"] != validator_norm["authorization_verified"]:
                return False

            # Exact agreement on material clearance outcome
            leader_cleared = leader_norm["verdict"] in (
                self.VERDICT_CLEARED_ORIGINAL,
                self.VERDICT_CLEARED_SYNDICATION,
            )
            validator_cleared = validator_norm["verdict"] in (
                self.VERDICT_CLEARED_ORIGINAL,
                self.VERDICT_CLEARED_SYNDICATION,
            )
            if leader_cleared != validator_cleared:
                return False

            return True
        except Exception:
            return False

    @gl.public.view
    def get_submission_count(self) -> int:
        return int(self.submission_count)

    @gl.public.view
    def get_evaluation_count(self) -> int:
        return int(self.evaluation_count)
