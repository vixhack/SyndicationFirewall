# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }

"""SyndicationFirewall v1.0.0: Autonomous Content Provenance & Anti-Plagiarism Firewall.

Author: vix
A standalone GenLayer Intelligent Contract primitive that audits submitted digital content,
grant proposals, and syndicated journalism against claimed or suspected canonical reference URLs.
Validators independently fetch reference text and evaluate originality vs plagiarism
under the Equivalence Principle, recording immutable, consensus-backed audit receipts.
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
    verdict: str  # "ORIGINAL", "SYNDICATED", "PLAGIARIZED", "UNAVAILABLE", "ERROR"
    originality_score: u32  # 0 to 100
    is_derivative: bool
    evidence_status_code: u32
    evaluated_at: u64
    reasoning: str


class SyndicationFirewall(gl.Contract):
    VERSION = "1.0.0"

    STATUS_PENDING = "PENDING"
    STATUS_CLEARED = "CLEARED"
    STATUS_FLAGGED = "FLAGGED"
    STATUS_QUARANTINED = "QUARANTINED"

    VERDICT_ORIGINAL = "ORIGINAL"
    VERDICT_SYNDICATED = "SYNDICATED"
    VERDICT_PLAGIARIZED = "PLAGIARIZED"
    VERDICT_UNAVAILABLE = "UNAVAILABLE"
    VERDICT_ERROR = "ERROR"

    MIN_TITLE_LENGTH = 1
    MAX_TITLE_LENGTH = 128
    MIN_CONTENT_LENGTH = 1
    MAX_CONTENT_LENGTH = 8192
    MAX_URL_LENGTH = 2048
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

    def _normalize_evaluation_payload(self, raw: dict) -> dict:
        """Sanitize and clamp model output to guaranteed schema."""
        raw_verdict = str(raw.get("verdict", self.VERDICT_ERROR)).strip().upper()
        if raw_verdict in (
            self.VERDICT_ORIGINAL,
            self.VERDICT_SYNDICATED,
            self.VERDICT_PLAGIARIZED,
            self.VERDICT_UNAVAILABLE,
        ):
            verdict = raw_verdict
        else:
            verdict = self.VERDICT_ERROR

        try:
            score = int(raw.get("originality_score", 0))
            if score < 0:
                score = 0
            elif score > 100:
                score = 100
        except Exception:
            score = 0

        is_derivative = bool(raw.get("is_derivative", False))
        if verdict in (self.VERDICT_PLAGIARIZED, self.VERDICT_ERROR):
            is_derivative = True

        reasoning = str(raw.get("reasoning", "")).strip()[:500]
        evidence_status_code = int(raw.get("evidence_status_code", 200))

        return {
            "verdict": verdict,
            "originality_score": score,
            "is_derivative": is_derivative,
            "reasoning": reasoning,
            "evidence_status_code": evidence_status_code,
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
    ) -> u256:
        clean_title = title.strip()
        clean_content = content.strip()
        clean_url = self._validate_url(canonical_url)

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
            status=self.STATUS_PENDING,
            latest_evaluation_id=u32(0),
            active=True,
            created_at=now_ts,
            total_evaluations=u32(0),
        )

        self.submissions[sub_id] = submission
        return sub_id

    @gl.public.write
    def evaluate_originality(self, submission_id: u256) -> u32:
        if isinstance(submission_id, int):
            submission_id = u256(submission_id)

        if submission_id not in self.submissions:
            raise gl.vm.UserError("Submission does not exist")

        sub = self.submissions[submission_id]
        if not sub.active:
            raise gl.vm.UserError("Cannot evaluate an archived submission")

        # Capture snapshot for non-deterministic execution
        target_url = sub.canonical_url
        submitted_excerpt = sub.content_excerpt
        max_ref_chars = self.MAX_REFERENCE_CHARS

        def evaluate() -> dict:
            response = gl.nondet.web.get(target_url)
            status_code = response.status

            if status_code in (404, 410):
                return self._normalize_evaluation_payload({
                    "verdict": self.VERDICT_UNAVAILABLE,
                    "originality_score": 0,
                    "is_derivative": True,
                    "reasoning": f"Canonical reference document not found: HTTP {status_code}.",
                    "evidence_status_code": status_code,
                })
            if status_code >= 400:
                return self._normalize_evaluation_payload({
                    "verdict": self.VERDICT_UNAVAILABLE,
                    "originality_score": 0,
                    "is_derivative": True,
                    "reasoning": f"Canonical reference unavailable: HTTP {status_code}.",
                    "evidence_status_code": status_code,
                })

            body_str = response.body.decode("utf-8", errors="replace").strip()
            if len(body_str) == 0:
                return self._normalize_evaluation_payload({
                    "verdict": self.VERDICT_UNAVAILABLE,
                    "originality_score": 0,
                    "is_derivative": True,
                    "reasoning": "Canonical reference returned an empty document.",
                    "evidence_status_code": status_code,
                })

            bounded_ref = body_str[:max_ref_chars]

            prompt = f"""You are an impartial GenLayer validator magistrate adjudicating copyright, syndication, and plagiarism.
Compare the submitted content excerpt against the canonical reference document.

CANONICAL REFERENCE DOCUMENT:
<canonical_reference>
{bounded_ref}
</canonical_reference>

SUBMITTED CONTENT:
<submitted_content>
{submitted_excerpt}
</submitted_content>

TASK:
- If the submitted content is genuinely original with minimal overlap, return "ORIGINAL" with originality_score 70-100 and is_derivative false.
- If it is legitimate authorized syndication with proper attribution, return "SYNDICATED" with originality_score 30-69.
- If it is copycat or verbatim plagiarism without original commentary, return "PLAGIARIZED" with originality_score 0-29 and is_derivative true.

OUTPUT FORMAT:
Respond with ONLY valid JSON:
{{
  "verdict": "ORIGINAL" | "SYNDICATED" | "PLAGIARIZED",
  "originality_score": 0,
  "is_derivative": false,
  "reasoning": "Concise justification"
}}
"""
            try:
                result = gl.nondet.exec_prompt(prompt, response_format="json")
                if isinstance(result, str):
                    result = json.loads(result)
            except Exception:
                result = {"verdict": self.VERDICT_ERROR, "originality_score": 0}

            if not isinstance(result, dict):
                result = {"verdict": self.VERDICT_ERROR, "originality_score": 0}

            result["evidence_status_code"] = status_code
            return self._normalize_evaluation_payload(result)

        def validate(leader_result: gl.vm.Result) -> bool:
            if not isinstance(leader_result, gl.vm.Return):
                return False
            try:
                leader_val = self._normalize_evaluation_payload(leader_result.calldata)
                validator_val = evaluate()

                # Verdict agreement
                if leader_val["verdict"] != validator_val["verdict"]:
                    return False

                # Agreement on whether derivative
                if leader_val["is_derivative"] != validator_val["is_derivative"]:
                    return False

                # Originality score tolerance (+/- 10 points)
                score_diff = abs(int(leader_val["originality_score"]) - int(validator_val["originality_score"]))
                if score_diff > 10:
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
            evidence_status_code=u32(eval_payload["evidence_status_code"]),
            evaluated_at=now_ts,
            reasoning=eval_payload["reasoning"],
        )
        self.evaluations[eval_id] = receipt

        # Deterministic status update
        if receipt.verdict == self.VERDICT_ORIGINAL and receipt.originality_score >= 70:
            sub.status = self.STATUS_CLEARED
        elif receipt.verdict == self.VERDICT_SYNDICATED:
            sub.status = self.STATUS_CLEARED
        elif receipt.verdict == self.VERDICT_UNAVAILABLE:
            sub.status = self.STATUS_QUARANTINED
        else:
            sub.status = self.STATUS_FLAGGED

        sub.latest_evaluation_id = eval_id
        sub.total_evaluations += u32(1)
        self.submissions[submission_id] = sub

        return eval_id

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
            "evidence_status_code": int(ev.evidence_status_code),
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
        if ev.verdict == self.VERDICT_SYNDICATED:
            return True
        return (
            ev.verdict == self.VERDICT_ORIGINAL
            and ev.originality_score >= min_originality
        )

    @gl.public.view
    def get_submission_count(self) -> int:
        return int(self.submission_count)

    @gl.public.view
    def get_evaluation_count(self) -> int:
        return int(self.evaluation_count)
