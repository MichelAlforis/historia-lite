"""Tests for Ollama AI system"""
import pytest
from unittest.mock import MagicMock, AsyncMock, patch

from ai.ollama_ai import (
    OllamaAI,
    DecisionCache,
    RateLimiter,
    CachedDecision,
)


class MockCountry:
    """Mock country for testing"""
    def __init__(self, country_id: str, **kwargs):
        self.id = country_id
        self.name = kwargs.get("name", country_id)
        self.name_fr = kwargs.get("name_fr", country_id)
        self.tier = kwargs.get("tier", 2)
        self.economy = kwargs.get("economy", 50)
        self.military = kwargs.get("military", 50)
        self.stability = kwargs.get("stability", 50)
        self.nuclear = kwargs.get("nuclear", 0)
        self.technology = kwargs.get("technology", 50)
        self.soft_power = kwargs.get("soft_power", 50)
        self.resources = kwargs.get("resources", 50)
        self.population = kwargs.get("population", 50)
        self.regime = kwargs.get("regime", "democracy")
        self.blocs = kwargs.get("blocs", [])
        self.at_war = kwargs.get("at_war", [])
        self.sanctions_on = kwargs.get("sanctions_on", [])
        self.allies = kwargs.get("allies", [])
        self.rivals = kwargs.get("rivals", [])
        self.relations = kwargs.get("relations", {})

    def get_relation(self, other_id: str) -> int:
        return self.relations.get(other_id, 0)


class MockWorld:
    """Mock world for testing"""
    def __init__(self):
        self.year = 2025
        self.oil_price = 80
        self.global_tension = 50
        self.defcon_level = 5
        self.countries = {}

    def get_country(self, country_id: str):
        return self.countries.get(country_id)


class TestDecisionCache:
    """Test DecisionCache class"""

    def setup_method(self):
        self.cache = DecisionCache(max_size=10, ttl_ticks=5)
        self.country = MockCountry("USA")
        self.world = MockWorld()

    def test_init(self):
        """Test cache initialization"""
        assert len(self.cache.cache) == 0
        assert self.cache.hits == 0
        assert self.cache.misses == 0

    def test_hash_situation(self):
        """Test situation hashing"""
        hash1 = self.cache._hash_situation(self.country, self.world)
        assert isinstance(hash1, str)

        # Same situation should give same hash
        hash2 = self.cache._hash_situation(self.country, self.world)
        assert hash1 == hash2

        # Different situation should give different hash
        self.country.economy = 90
        hash3 = self.cache._hash_situation(self.country, self.world)
        assert hash1 != hash3

    def test_set_and_get(self):
        """Test setting and getting cached decisions"""
        decision = {"action": "ECONOMIE", "target": None}

        self.cache.set(self.country, self.world, decision)

        result = self.cache.get(self.country, self.world)
        assert result == decision

    def test_cache_miss(self):
        """Test cache miss returns None"""
        result = self.cache.get(self.country, self.world)
        assert result is None
        assert self.cache.misses == 1

    def test_cache_hit_increments_counter(self):
        """Test cache hit increments counter"""
        decision = {"action": "ECONOMIE"}
        self.cache.set(self.country, self.world, decision)

        self.cache.get(self.country, self.world)
        assert self.cache.hits == 1

    def test_cache_ttl_expiry(self):
        """Test cache entries expire after TTL"""
        decision = {"action": "ECONOMIE"}
        self.cache.set(self.country, self.world, decision)

        # Advance world year beyond TTL
        self.world.year = 2025 + 10

        result = self.cache.get(self.country, self.world)
        assert result is None

    def test_cache_max_size(self):
        """Test cache evicts oldest when at capacity"""
        cache = DecisionCache(max_size=3, ttl_ticks=100)

        for i in range(5):
            country = MockCountry(f"C{i}")
            cache.set(country, self.world, {"action": f"A{i}"})

        assert len(cache.cache) == 3

    def test_get_stats(self):
        """Test getting cache statistics"""
        decision = {"action": "ECONOMIE"}
        self.cache.set(self.country, self.world, decision)
        self.cache.get(self.country, self.world)  # Hit
        self.cache.get(MockCountry("OTHER"), self.world)  # Miss

        stats = self.cache.get_stats()

        assert stats["size"] == 1
        assert stats["hits"] == 1
        assert stats["misses"] == 1
        assert stats["hit_rate"] == 0.5

    def test_clear(self):
        """Test clearing the cache"""
        self.cache.set(self.country, self.world, {"action": "ECONOMIE"})
        self.cache.hits = 5
        self.cache.misses = 3

        self.cache.clear()

        assert len(self.cache.cache) == 0
        assert self.cache.hits == 0
        assert self.cache.misses == 0


class TestRateLimiter:
    """Test RateLimiter class"""

    def setup_method(self):
        self.limiter = RateLimiter(min_interval=0.1)

    @pytest.mark.asyncio
    async def test_first_request_no_wait(self):
        """Test first request doesn't wait"""
        import time
        start = time.time()
        await self.limiter.wait("test")
        elapsed = time.time() - start

        assert elapsed < 0.05  # Should be nearly instant

    @pytest.mark.asyncio
    async def test_rapid_requests_throttled(self):
        """Test rapid requests are throttled"""
        import time

        await self.limiter.wait("test")
        start = time.time()
        await self.limiter.wait("test")
        elapsed = time.time() - start

        # Should have waited ~0.1 seconds
        assert elapsed >= 0.09

    @pytest.mark.asyncio
    async def test_different_keys_independent(self):
        """Test different keys are independent"""
        import time

        await self.limiter.wait("key1")
        start = time.time()
        await self.limiter.wait("key2")  # Different key
        elapsed = time.time() - start

        assert elapsed < 0.05  # Should be nearly instant


class TestOllamaAI:
    """Test OllamaAI class"""

    def setup_method(self):
        self.ai = OllamaAI(
            base_url="http://localhost:11434",
            model="test-model",
        )
        self.country = MockCountry("USA", rivals=["RUS"])
        self.world = MockWorld()

    def test_init(self):
        """Test AI initialization"""
        assert self.ai.base_url == "http://localhost:11434"
        assert self.ai.model == "test-model"
        assert self.ai.fallback_count == 0
        assert self.ai.success_count == 0
        assert isinstance(self.ai.cache, DecisionCache)
        assert isinstance(self.ai.rate_limiter, RateLimiter)

    def test_build_prompt(self):
        """Test prompt building"""
        prompt = self.ai._build_prompt(self.country, self.world)

        assert "USA" in prompt
        assert "2025" in prompt
        assert "50" in prompt  # Stats
        assert "ECONOMIE" in prompt  # Actions
        assert "JSON" in prompt

    def test_parse_response_valid(self):
        """Test parsing valid JSON response"""
        response = '{"action": "ECONOMIE", "cible": null, "raison": "test"}'

        result = self.ai._parse_response(response, self.country, self.world)

        assert result is not None
        assert result["action"] == "ECONOMIE"
        assert result["reason"] == "test"

    def test_parse_response_with_text(self):
        """Test parsing response with surrounding text"""
        response = 'Voici ma decision: {"action": "MILITAIRE", "cible": null, "raison": "renforcement"} Merci.'

        result = self.ai._parse_response(response, self.country, self.world)

        assert result is not None
        assert result["action"] == "MILITAIRE"

    def test_parse_response_invalid_action(self):
        """Test parsing response with invalid action"""
        response = '{"action": "INVALID", "cible": null}'

        result = self.ai._parse_response(response, self.country, self.world)

        assert result is None

    def test_parse_response_no_json(self):
        """Test parsing response without JSON"""
        response = "Je pense que nous devrions developper l'economie."

        result = self.ai._parse_response(response, self.country, self.world)

        assert result is None

    def test_algorithmic_fallback_at_war(self):
        """Test fallback prioritizes military when at war"""
        country = MockCountry("USA", at_war=["IRQ"])

        result = self.ai._algorithmic_fallback(country, self.world)

        assert result["action"] == "MILITAIRE"
        assert result["is_fallback"] is True

    def test_algorithmic_fallback_low_stability(self):
        """Test fallback prioritizes stability when low"""
        country = MockCountry("VEN", stability=30)

        result = self.ai._algorithmic_fallback(country, self.world)

        assert result["action"] == "STABILITE"

    def test_algorithmic_fallback_low_economy(self):
        """Test fallback prioritizes economy when low"""
        country = MockCountry("ARG", stability=60, economy=40)

        result = self.ai._algorithmic_fallback(country, self.world)

        assert result["action"] == "ECONOMIE"

    def test_algorithmic_fallback_default(self):
        """Test fallback picks appropriate action based on situation"""
        # Tier 3 country with high stats - should pick influence
        country = MockCountry("CHE", tier=3, stability=80, economy=70, technology=70)

        result = self.ai._algorithmic_fallback(country, self.world)

        # Should pick influence expansion since stable, rich, and not tier 1-2
        assert result["action"] == "INFLUENCE"
        assert result["is_fallback"] is True

    def test_get_stats(self):
        """Test getting AI statistics"""
        self.ai.success_count = 10
        self.ai.fallback_count = 2

        stats = self.ai.get_stats()

        assert stats["success_count"] == 10
        assert stats["fallback_count"] == 2
        assert abs(stats["success_rate"] - 0.833) < 0.01
        assert "cache_stats" in stats

    @pytest.mark.asyncio
    async def test_make_decision_uses_cache(self):
        """Test make_decision returns cached decision"""
        cached_decision = {"action": "TECHNOLOGIE", "target": None, "reason": "cached"}
        self.ai.cache.set(self.country, self.world, cached_decision)

        result = await self.ai.make_decision(self.country, self.world)

        assert result == cached_decision
