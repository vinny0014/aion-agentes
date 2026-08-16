"""Focused contract tests for the zero-cost AION visual editorial gate."""
from pathlib import Path
import sys

import pytest


BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))

from app.agents import visual_desk  # noqa: E402
from app.agents.visual_desk import (  # noqa: E402
    RightsMetadata,
    VisualCandidate,
    approve_and_record,
    evaluate_candidate,
    visual_publication_issues,
)


def candidate(**overrides) -> VisualCandidate:
    values = {
        "asset_url": "https://media.example.com/openai-event.webp",
        "rights": RightsMetadata(
            source_url="https://openai.com/news/example",
            credit="OpenAI",
            rights_basis="official",
            author="OpenAI newsroom",
            license_name="OpenAI media terms",
            license_url="https://openai.com/policies/terms-of-use/",
        ),
        "editorial_relevance": 30,
        "visual_quality": 20,
        "credibility": 15,
        "provenance": 15,
        "crop": 10,
        "originality": 5,
        "naturalness": 5,
        "width": 1600,
        "height": 900,
        "visual_type": "event",
        "dominant_color": "neutral",
        "main_person": "Sam Altman",
        "framing": "medium shot",
        "focal_subject": "OpenAI product announcement on stage",
    }
    values.update(overrides)
    return VisualCandidate(**values)


def test_world_class_candidate_passes_standard_and_hero_thresholds():
    standard = evaluate_candidate(candidate(), recent=[])
    hero = evaluate_candidate(candidate(), hero=True, recent=[])

    assert standard.approved is True
    assert standard.score == 100
    assert standard.threshold == 80
    assert hero.approved is True
    assert hero.threshold == 90


def test_hero_requires_90_even_when_standard_story_would_pass():
    item = candidate(editorial_relevance=25, visual_quality=18,
                     credibility=13, provenance=13, crop=8,
                     originality=5, naturalness=5)

    assert evaluate_candidate(item, recent=[]).approved is True
    hero = evaluate_candidate(item, hero=True, recent=[])
    assert hero.score == 87
    assert hero.approved is False
    assert "score 87 is below the required 90" in hero.issues


def test_rights_are_mandatory_even_with_a_perfect_score():
    unknown_rights = RightsMetadata(
        source_url="https://images.example.com/found-online",
        credit="",
        rights_basis="unknown",
    )

    decision = evaluate_candidate(candidate(rights=unknown_rights), recent=[])

    assert decision.score == 100
    assert decision.approved is False
    assert "image credit is missing" in decision.issues
    assert "reuse rights are not verifiable" in decision.issues


def test_prohibited_defects_and_low_resolution_fail_closed():
    decision = evaluate_candidate(
        candidate(width=800, height=450, defects=("fake_interface", "extra_fingers")),
        recent=[],
    )

    assert decision.approved is False
    assert "image is below the 1200x630 editorial minimum" in decision.issues
    assert any("extra_fingers" in issue and "fake_interface" in issue
               for issue in decision.issues)


def test_recent_visual_memory_blocks_duplicate_and_penalizes_repetition():
    item = candidate()
    duplicate = evaluate_candidate(item, recent=[{"asset_url": item.asset_url}])
    repetitive = evaluate_candidate(
        item,
        recent=[{
            "asset_url": "https://media.example.com/other.webp",
            "main_person": "Sam Altman",
            "visual_type": "event",
            "dominant_color": "neutral",
            "framing": "medium shot",
        }],
    )

    assert duplicate.approved is False
    assert "image was used recently" in duplicate.issues
    assert duplicate.breakdown["originality"] == 0
    assert repetitive.diversity_penalty == 5
    assert repetitive.score == 95


def test_review_storage_and_publication_gate_are_fail_closed(monkeypatch):
    memory = {}

    monkeypatch.setattr(visual_desk, "mem_get",
                        lambda scope, key, default=None: memory.get((scope, key), default))
    monkeypatch.setattr(visual_desk, "mem_set",
                        lambda scope, key, value: memory.__setitem__((scope, key), value))

    assert visual_publication_issues(41) == ["AION Visual Editor approval is missing"]
    decision = approve_and_record(41, candidate(), recent=[])

    assert decision.approved is True
    assert visual_publication_issues(41) == []
    assert visual_publication_issues(
        41, asset_url="https://media.example.com/replaced.webp"
    ) == ["published image does not match the approved visual asset"]
    assert memory[("agent:aion-visual-editor", "recent-visuals")][0]["content_id"] == 41


def test_scores_outside_the_published_rubric_are_rejected():
    with pytest.raises(ValueError):
        evaluate_candidate(candidate(editorial_relevance=31), recent=[])
