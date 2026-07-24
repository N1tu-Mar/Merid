"""The model registry: which model does which job, and why.

Two inputs, two model classes, one page:

    input                task                model class   reads
    -------------------  ------------------  ------------  ------------------
    any uploaded file    referral_vision      vision       the page itself
    audio transcript     transcript_extract   compact text what was said

Deliberately only two. Every entry here has a live call site; a registry
row without one is decoration, and a routing table nobody can verify is
worse than no routing table. Embedding/reranking for payer criteria and a
large-model escalation tier were both considered and cut — they were
plausible rows with no caller.

Note what is NOT here: an arbiter. When the two readers disagree,
services/extract/reconcile.py settles it by running app.rule_engine over
the candidate readings. That is deterministic and points at a rule; a model
opinion in that slot would be strictly less defensible than the mechanism
it replaced.

Why this is a platform argument rather than a vendor preference: both are
open-weight models behind one OpenAI-compatible API, so swapping the vision
model or promoting the text extractor a size class after an eval says to is
an env var, not an integration project. evals/extraction_ab.py already did
exactly that for the text extractor and picked deepseek-v4-flash over -pro
on measured verdict preservation rather than on vibes.

Every id is overridable by env var, because model availability on an
account is a deployment fact, not a source-code fact — kimi-k2p5 404s and
glm-5p2 rejects images outright, both found by calling them rather than by
reading a docs page. An id that 404s fails closed to ESCALATE: safe, but on
stage indistinguishable from a broken pipeline. Check before demoing.
"""

from __future__ import annotations

import os
from dataclasses import dataclass

# Fireworks accepts the short "fireworks/<name>" form in its docs; the fully
# qualified account path is what the inference API expects and what shows up
# in traces, so we spell it out.
_PREFIX = "accounts/fireworks/models"


@dataclass(frozen=True)
class ModelSpec:
    """One task, the model assigned to it, and the reasoning for the size."""

    task: str
    default: str
    modality: str  # "vision" | "text" | "embedding" | "rerank"
    env_var: str
    why: str

    def resolve(self) -> str:
        """The id actually used. Env always wins — a deployment can pin a
        different model without a code change, which is the whole point."""
        return os.environ.get(self.env_var) or self.default


REGISTRY: dict[str, ModelSpec] = {
    "referral_vision": ModelSpec(
        task="referral_vision",
        # Verified against the live API: kimi-k2p6 accepts image parts AND a
        # json_schema response_format. glm-5p2 rejects images outright
        # ("This model does not support image inputs"), and kimi-k2p5 404s —
        # which is why every id here is env-overridable and worth re-checking
        # against `GET /v1/models` on the account you are demoing from.
        default=f"{_PREFIX}/kimi-k2p6",
        modality="vision",
        env_var="FIREWORKS_VISION_MODEL",
        why=(
            "Reads every uploaded file — referral faxes, insurance cards, "
            "patient-uploaded medical history — as a page rather than as a "
            "transcription of one. Measured on the demo fax: tesseract "
            "renders ticked boxes as 'I/]' and drops unticked ones entirely, "
            "so the text reader returns null for every absent feature while "
            "this one reads them off the page. A dropped checkbox is a "
            "dropped red flag."
        ),
    ),
    "transcript_extract": ModelSpec(
        task="transcript_extract",
        default=f"{_PREFIX}/deepseek-v4-flash",
        modality="text",
        env_var="FIREWORKS_TRANSCRIPT_MODEL",
        why=(
            "Reads audio transcripts — what the patient actually said on the "
            "intake call. The hard part is negation scope, not reasoning "
            "depth: the keyword parser reads 'nope, apart from the bleeding' "
            "as no bleeding at confidence 0.9, and this model reads it "
            "correctly. Verified live. A compact model is the right size, and "
            "evals/extraction_ab.py measured it beating the larger one on "
            "verdict_preserved."
        ),
    ),
}


class UnknownTask(KeyError):
    """Raised for a task with no registered model. Never guess a default."""


def model_for(task: str) -> str:
    """The model id to use for `task`, honouring any env override."""
    try:
        return REGISTRY[task].resolve()
    except KeyError as e:
        raise UnknownTask(f"no model registered for task {task!r}") from e


def spec_for(task: str) -> ModelSpec:
    try:
        return REGISTRY[task]
    except KeyError as e:
        raise UnknownTask(f"no model registered for task {task!r}") from e


def registry_report() -> list[dict[str, str]]:
    """Serialisable view of the routing table.

    Exposed so the dashboard can show which model handled which step of a
    case rather than the claim living only in a slide.
    """
    return [
        {
            "task": s.task,
            "model": s.resolve(),
            "modality": s.modality,
            "env_var": s.env_var,
            "overridden": bool(os.environ.get(s.env_var)),
            "why": s.why,
        }
        for s in REGISTRY.values()
    ]
