"""Deterministic, zero-cost visual editorial gate for AION News.

This module deliberately does not download, generate, or license images. It
evaluates evidence produced by the acquisition pipeline, persists an auditable
decision in the existing agent memory store, and fails closed when evidence is
missing.  No model or paid API is required.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from hashlib import sha256
from urllib.parse import urlparse

from .core import mem_get, mem_set


SCORE_CAPS = {
    "editorial_relevance": 30,
    "visual_quality": 20,
    "credibility": 15,
    "provenance": 15,
    "crop": 10,
    "originality": 5,
    "naturalness": 5,
}
STANDARD_THRESHOLD = 80
HERO_THRESHOLD = 90
RECENT_VISUAL_LIMIT = 24

PROHIBITED_DEFECTS = frozenset({
    "deformed_face", "deformed_hands", "extra_fingers", "illegible_text",
    "invented_logo", "fake_interface", "nonsense_screen", "pseudo_infographic",
    "generic_neon", "generic_hologram", "unrelated_humanoid", "generic_digital_brain",
    "unrelated_robot", "obvious_stock", "unrelated", "low_resolution",
    "cropped_head", "cropped_eyes", "cropped_subject", "broken_image",
})

VERIFIABLE_RIGHTS_BASES = frozenset({
    "owned", "official", "press-kit", "media-kit", "public-domain",
    "creative-commons", "licensed-free", "editorial-permission",
})


def _http_url(value: str) -> bool:
    parsed = urlparse((value or "").strip())
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def _bounded(value: int, cap: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError("Visual criterion scores must be integers")
    if not 0 <= value <= cap:
        raise ValueError(f"Visual criterion score must be between 0 and {cap}")
    return value


def _asset_fingerprint(asset_url: str) -> str:
    """Hash managed bytes; URL hashing is only a fail-safe for remote evidence."""
    try:
        from .imagegen import managed_image_path
        path = managed_image_path(asset_url)
        if path:
            return sha256(path.read_bytes()).hexdigest()
    except (OSError, ImportError):
        pass
    return sha256(asset_url.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class RightsMetadata:
    """Evidence supporting editorial reuse; empty/unknown evidence never passes."""

    source_url: str
    credit: str
    rights_basis: str
    author: str = ""
    license_name: str = ""
    license_url: str = ""

    def issues(self) -> list[str]:
        issues: list[str] = []
        if not _http_url(self.source_url):
            issues.append("original source URL is missing or invalid")
        if not self.credit.strip():
            issues.append("image credit is missing")
        basis = self.rights_basis.strip().lower()
        if basis not in VERIFIABLE_RIGHTS_BASES:
            issues.append("reuse rights are not verifiable")
        if basis in {"official", "press-kit", "media-kit", "creative-commons", "licensed-free"}:
            if not self.license_name.strip():
                issues.append("rights evidence name is missing")
            if not _http_url(self.license_url):
                issues.append("rights evidence URL is missing or invalid")
        return issues


@dataclass(frozen=True)
class VisualCandidate:
    """A candidate plus human/machine evidence, never an inferred copyright claim."""

    asset_url: str
    rights: RightsMetadata
    editorial_relevance: int
    visual_quality: int
    credibility: int
    provenance: int
    crop: int
    originality: int
    naturalness: int
    width: int
    height: int
    visual_type: str
    dominant_color: str = ""
    main_person: str = ""
    framing: str = ""
    focal_subject: str = ""
    defects: tuple[str, ...] = field(default_factory=tuple)

    def score_breakdown(self) -> dict[str, int]:
        return {
            key: _bounded(getattr(self, key), cap)
            for key, cap in SCORE_CAPS.items()
        }


@dataclass(frozen=True)
class VisualDecision:
    approved: bool
    score: int
    threshold: int
    hero: bool
    issues: tuple[str, ...]
    breakdown: dict[str, int]
    diversity_penalty: int = 0

    def as_dict(self) -> dict:
        return asdict(self)


def recent_visuals() -> list[dict]:
    value = mem_get("agent:aion-visual-editor", "recent-visuals", []) or []
    return value if isinstance(value, list) else []


def _same(a: str, b: str) -> bool:
    return bool(a and b and a.strip().casefold() == b.strip().casefold())


def diversity_assessment(candidate: VisualCandidate, recent: list[dict] | None = None) -> dict:
    """Measure home rhythm using only recent approved assets.

    Reusing the exact asset is a hard block. Repetition of subject/type/color/
    framing reduces only the five originality points, so scoring stays within
    the mission's published 100-point rubric.
    """
    recent = (recent_visuals() if recent is None else recent)[:RECENT_VISUAL_LIMIT]
    fingerprint = _asset_fingerprint(candidate.asset_url)
    if any(item.get("asset_fingerprint") == fingerprint or
           item.get("asset_url") == candidate.asset_url for item in recent):
        return {"duplicate_asset": True, "penalty": 5,
                "reasons": ["image was used recently"]}

    penalty, reasons = 0, []
    windows = (
        ("main_person", candidate.main_person, 4, 2, "same person repeated"),
        ("visual_type", candidate.visual_type, 3, 1, "same visual type repeated"),
        ("dominant_color", candidate.dominant_color, 4, 1, "same dominant color repeated"),
        ("framing", candidate.framing, 3, 1, "same framing repeated"),
    )
    for key, value, window, points, reason in windows:
        if value and any(_same(item.get(key, ""), value) for item in recent[:window]):
            penalty += points
            reasons.append(reason)
    return {"duplicate_asset": False, "penalty": min(5, penalty), "reasons": reasons}


def evaluate_candidate(candidate: VisualCandidate, *, hero: bool = False,
                       recent: list[dict] | None = None) -> VisualDecision:
    """Return an auditable decision; any mandatory failure overrides the score."""
    breakdown = candidate.score_breakdown()
    diversity = diversity_assessment(candidate, recent)
    diversity_penalty = min(diversity["penalty"], breakdown["originality"])
    breakdown["originality"] -= diversity_penalty
    score = sum(breakdown.values())
    threshold = HERO_THRESHOLD if hero else STANDARD_THRESHOLD
    issues = candidate.rights.issues()

    if not _http_url(candidate.asset_url):
        issues.append("asset URL is missing or invalid")
    if candidate.width < 1200 or candidate.height < 630:
        issues.append("image is below the 1200x630 editorial minimum")
    defects = sorted(set(candidate.defects) & PROHIBITED_DEFECTS)
    if defects:
        issues.append("prohibited visual defects: " + ", ".join(defects))
    if diversity["duplicate_asset"]:
        issues.append("image was used recently")
    if not candidate.visual_type.strip():
        issues.append("visual type is missing")
    if not candidate.focal_subject.strip():
        issues.append("focal subject is missing")
    if score < threshold:
        issues.append(f"score {score} is below the required {threshold}")

    # De-duplicate while preserving stable, testable ordering.
    issues = list(dict.fromkeys(issues))
    return VisualDecision(not issues, score, threshold, hero, tuple(issues),
                          breakdown, diversity_penalty)


def record_visual_review(content_id: int, candidate: VisualCandidate,
                         decision: VisualDecision) -> dict:
    """Persist provenance and the decision; only approved assets enter memory."""
    if content_id <= 0:
        raise ValueError("content_id must be a positive integer")
    fingerprint = _asset_fingerprint(candidate.asset_url)
    record = {
        "content_id": content_id,
        "asset_url": candidate.asset_url,
        "asset_fingerprint": fingerprint,
        "rights": asdict(candidate.rights),
        "visual_type": candidate.visual_type,
        "dominant_color": candidate.dominant_color,
        "main_person": candidate.main_person,
        "framing": candidate.framing,
        "focal_subject": candidate.focal_subject,
        "width": candidate.width,
        "height": candidate.height,
        "decision": decision.as_dict(),
    }
    mem_set("agent:aion-visual-editor", f"review:{content_id}", record)
    if decision.approved:
        recent = [item for item in recent_visuals()
                  if item.get("asset_url") != candidate.asset_url]
        mem_set("agent:aion-visual-editor", "recent-visuals",
                [record, *recent][:RECENT_VISUAL_LIMIT])
    return record


def visual_publication_issues(content_id: int, *, asset_url: str = "",
                              hero: bool = False) -> list[str]:
    """Fail-closed publication check for pipeline integration."""
    review = mem_get("agent:aion-visual-editor", f"review:{content_id}")
    if not isinstance(review, dict):
        return ["AION Visual Editor approval is missing"]
    if asset_url and (review.get("asset_url") != asset_url or
                      review.get("asset_fingerprint") != _asset_fingerprint(asset_url)):
        return ["published image does not match the approved visual asset"]
    decision = review.get("decision") or {}
    required = HERO_THRESHOLD if hero else STANDARD_THRESHOLD
    if decision.get("approved") is not True:
        return ["AION Visual Editor rejected the image"]
    if int(decision.get("score", 0)) < required:
        return [f"visual score is below the required {required}"]
    rights = review.get("rights") or {}
    try:
        rights_issues = RightsMetadata(**rights).issues()
    except (TypeError, ValueError):
        rights_issues = ["visual rights metadata is invalid"]
    return rights_issues


def approve_and_record(content_id: int, candidate: VisualCandidate, *, hero: bool = False,
                       recent: list[dict] | None = None) -> VisualDecision:
    """Convenience entry point for Visual Editor and independent auditors."""
    decision = evaluate_candidate(candidate, hero=hero, recent=recent)
    record_visual_review(content_id, candidate, decision)
    return decision
