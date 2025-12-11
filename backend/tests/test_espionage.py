"""Tests for espionage system"""
import pytest
from unittest.mock import MagicMock

from engine.espionage import (
    EspionageManager,
    SecretLevel,
    IntelQuality,
    Confidence,
    INFO_SECRET_LEVELS,
)


class MockCountry:
    """Mock country for testing"""
    def __init__(self, country_id: str, **kwargs):
        self.id = country_id
        self.name = kwargs.get("name", country_id)
        self.name_fr = kwargs.get("name_fr", country_id)
        self.tier = kwargs.get("tier", 3)
        self.technology = kwargs.get("technology", 50)
        self.soft_power = kwargs.get("soft_power", 50)
        self.intelligence = kwargs.get("intelligence", 50)
        self.relations = kwargs.get("relations", {})
        self.allies = kwargs.get("allies", [])
        self.rivals = kwargs.get("rivals", [])
        self.blocs = kwargs.get("blocs", [])
        self.sanctions_on = kwargs.get("sanctions_on", [])
        self.regime = kwargs.get("regime", "democracy")
        self.nuclear = kwargs.get("nuclear", 0)
        self.military = kwargs.get("military", 50)


class TestEspionageManager:
    """Test EspionageManager class"""

    def setup_method(self):
        """Setup for each test"""
        self.manager = EspionageManager()

    def test_init(self):
        """Test manager initialization"""
        assert self.manager.operations == []
        assert self.manager.intel_cache == {}

    def test_reset(self):
        """Test reset clears state"""
        self.manager.operations.append("test")
        self.manager.intel_cache["test"] = {}
        self.manager.reset()
        assert self.manager.operations == []
        assert self.manager.intel_cache == {}

    def test_get_intel_score_self(self):
        """Test perfect intel on self"""
        country = MockCountry("USA")
        score = self.manager.get_intel_score(country, country)
        assert score == 100

    def test_get_intel_score_ally(self):
        """Test higher intel on allies"""
        observer = MockCountry("USA", allies=["GBR"], technology=60)
        target = MockCountry("GBR")

        score_ally = self.manager.get_intel_score(observer, target)

        observer_no_ally = MockCountry("USA", technology=60)
        score_no_ally = self.manager.get_intel_score(observer_no_ally, target)

        assert score_ally > score_no_ally

    def test_get_intel_score_rival(self):
        """Test lower intel on rivals"""
        observer = MockCountry("USA", rivals=["RUS"], technology=60)
        target = MockCountry("RUS")

        score_rival = self.manager.get_intel_score(observer, target)

        observer_no_rival = MockCountry("USA", technology=60)
        score_no_rival = self.manager.get_intel_score(observer_no_rival, target)

        assert score_rival < score_no_rival

    def test_get_intel_score_tier_effect(self):
        """Test tier affects intel difficulty"""
        observer = MockCountry("FRA", technology=60)

        superpower = MockCountry("USA", tier=1)
        small_country = MockCountry("MCO", tier=3)

        score_superpower = self.manager.get_intel_score(observer, superpower)
        score_small = self.manager.get_intel_score(observer, small_country)

        # Harder to spy on superpowers
        assert score_superpower < score_small

    def test_get_intel_quality_none(self):
        """Test quality for low intel score"""
        quality = self.manager.get_intel_quality(10)
        assert quality == IntelQuality.NONE

    def test_get_intel_quality_partial(self):
        """Test quality for partial intel"""
        quality = self.manager.get_intel_quality(30)
        assert quality == IntelQuality.PARTIAL

    def test_get_intel_quality_good(self):
        """Test quality for good intel"""
        quality = self.manager.get_intel_quality(50)
        assert quality == IntelQuality.GOOD

    def test_get_intel_quality_perfect(self):
        """Test quality for perfect intel"""
        quality = self.manager.get_intel_quality(95)
        assert quality == IntelQuality.PERFECT

    def test_can_see_info_public(self):
        """Test public info visible at any level"""
        assert self.manager.can_see_info(0, "name")
        assert self.manager.can_see_info(0, "id")
        assert self.manager.can_see_info(0, "tier")

    def test_can_see_info_secret(self):
        """Test secret info requires higher intel"""
        # Nuclear requires TOP_SECRET (80)
        assert not self.manager.can_see_info(50, "nuclear")
        assert self.manager.can_see_info(85, "nuclear")

        # Military requires HIGH (60)
        assert not self.manager.can_see_info(40, "military")
        assert self.manager.can_see_info(65, "military")

    def test_get_confidence_unknown(self):
        """Test unknown confidence for hidden fields"""
        confidence = self.manager.get_confidence(30, "nuclear")
        assert confidence == Confidence.UNKNOWN

    def test_get_confidence_estimate(self):
        """Test estimate confidence for near-threshold"""
        confidence = self.manager.get_confidence(85, "nuclear")
        assert confidence == Confidence.ESTIMATE

    def test_get_confidence_exact(self):
        """Test exact confidence for high clearance"""
        confidence = self.manager.get_confidence(100, "nuclear")
        assert confidence == Confidence.EXACT

    def test_apply_fog_of_war(self):
        """Test fog of war filtering"""
        country_data = {
            "id": "USA",
            "name": "United States",
            "economy": 90,
            "military": 95,
            "nuclear": 100,
        }

        # Low intel - should hide military and nuclear
        filtered = self.manager.apply_fog_of_war(country_data, 30)
        assert filtered.get("id") == "USA"
        assert filtered.get("name") == "United States"
        assert "_intel_score" in filtered
        assert filtered.get("nuclear") is None  # Hidden

    def test_nuclear_display_unknown(self):
        """Test nuclear display with low intel"""
        target = MockCountry("USA", nuclear=100)
        display = self.manager.get_nuclear_display(target, 50)

        assert display["status"] == "unknown"
        assert display["warheads"] is None

    def test_nuclear_display_confirmed(self):
        """Test nuclear display with high intel"""
        target = MockCountry("USA", nuclear=100)
        display = self.manager.get_nuclear_display(target, 85)

        assert display["status"] == "confirmed"

    def test_nuclear_display_none(self):
        """Test nuclear display for non-nuclear"""
        target = MockCountry("BRA", nuclear=0)
        display = self.manager.get_nuclear_display(target, 85)

        assert display["status"] == "none"
        assert display["warheads"] == 0


class TestSecretLevels:
    """Test secret level configurations"""

    def test_public_fields(self):
        """Test public fields are level 0"""
        public_fields = ["id", "name", "name_fr", "flag", "tier", "region"]
        for field in public_fields:
            assert INFO_SECRET_LEVELS.get(field) == SecretLevel.PUBLIC

    def test_military_fields(self):
        """Test military fields are HIGH"""
        military_fields = ["military", "military_bases", "at_war"]
        for field in military_fields:
            assert INFO_SECRET_LEVELS.get(field) == SecretLevel.HIGH

    def test_nuclear_fields(self):
        """Test nuclear fields are TOP_SECRET"""
        nuclear_fields = ["nuclear", "nuclear_warheads"]
        for field in nuclear_fields:
            assert INFO_SECRET_LEVELS.get(field) == SecretLevel.TOP_SECRET
