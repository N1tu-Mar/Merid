"""The model registry: which model does which job, and why.

This file is the architecture argument in one page. Meridian does not call
"an LLM" — it routes each task to the smallest model that can do that task,
across four different model classes:

    task                 class        why not something bigger / smaller
    -------------------  -----------  ------------------------------------
    referral_vision      vision       a scanned fax is an image; checkbox
                                      state and margin handwriting do not
                                      survive OCR-to-text at all
    transcript_extract   compact text closed-form facts from one call; the
                                      job is negation scope, not reasoning
    escalated_extract    large text   only for documents the compact model
                                      returned low confidence on
    criteria_embed       embedding    retrieve payer criteria by meaning
    criteria_rerank      reranker     order retrieved criteria by fit

Why this is a platform argument rather than a vendor preference: all five
classes are open-weight models behind one OpenAI-compatible API. Swapping
the vision model, or promoting the compact extractor a size class after an
eval says to, is an env var — not an integration project. `evals/
extraction_ab.py` already exercises exactly that for the text extractor and
picked deepseek-v4-flash over -pro on measured verdict preservation, not on
vibes.

Every id here is overridable by env var, because model availability on any
account is a deployment fact, not a source-code fact. Verify against your
own account before a demo: an id that 404s fails closed to ESCALATE, which
is safe but looks like a broken pipeline.
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
        default=f"{_PREFIX}/kimi-k2p5",
        modality="vision",
        env_var="FIREWORKS_VISION_MODEL",
        why=(
            "A faxed referral is a page image, not text. Ticked checkboxes, "
            "margin handwriting, and which value sits under which field label "
            "are exactly what OCR-to-text discards — and a dropped checkbox is "
            "a dropped red flag."
        ),
    ),
    "transcript_extract": ModelSpec(
        task="transcript_extract",
        default=f"{_PREFIX}/deepseek-v4-flash",
        modality="text",
        env_var="FIREWORKS_TRANSCRIPT_MODEL",
        why=(
            "Reading closed-form answers out of one call transcript. The hard "
            "part is negation scope ('nope, apart from the bleeding'), not "
            "reasoning depth, so a compact model is the right size. Matches "
            "the model evals/extraction_ab.py measured as best on "
            "verdict_preserved."
        ),
    ),
    "escalated_extract": ModelSpec(
        task="escalated_extract",
        default=f"{_PREFIX}/deepseek-v4-pro",
        modality="text",
        env_var="FIREWORKS_ESCALATED_MODEL",
        why=(
            "Second pass for documents the compact extractor returned low "
            "confidence on. Deliberately NOT used to adjudicate disagreements "
            "— app.rule_engine settles those deterministically, and a model "
            "opinion there would be less auditable than the rule it replaced."
        ),
    ),
    "criteria_embed": ModelSpec(
        task="criteria_embed",
        default=f"{_PREFIX}/qwen3-embedding-8b",
        modality="embedding",
        env_var="FIREWORKS_EMBED_MODEL",
        why=(
            "Payer policy is written in the payer's words, not the chart's. "
            "Retrieving the criteria a packet must satisfy is a similarity "
            "problem, and a generative model is the wrong tool for it."
        ),
    ),
    "criteria_rerank": ModelSpec(
        task="criteria_rerank",
        default=f"{_PREFIX}/qwen3-reranker-8b",
        modality="rerank",
        env_var="FIREWORKS_RERANK_MODEL",
        why=(
            "Embedding recall is broad; a PA packet should cite the two or "
            "three criteria that actually apply. Reranking is a scoring task, "
            "so it gets a scoring model."
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
