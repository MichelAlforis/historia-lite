"""Scoring system with 7 categories and Fog of War for Historia Lite"""
import logging
from typing import Dict, List, Optional, Any
from enum import Enum

from pydantic import BaseModel, Field

from .espionage import espionage_manager, IntelQuality, Confidence

logger = logging.getLogger(__name__)


class ScoreCategory(str, Enum):
    """The 7 scoring categories"""
    MILITARY = "military"
    ECONOMIC = "economic"
    STABILITY = "stability"
    INFLUENCE = "influence"
    INTELLIGENCE = "intelligence"
    RESOURCES = "resources"
    LEADERSHIP = "leadership"


# Category weights for global score
CATEGORY_WEIGHTS = {
    ScoreCategory.MILITARY: 0.20,
    ScoreCategory.ECONOMIC: 0.20,
    ScoreCategory.STABILITY: 0.10,
    ScoreCategory.INFLUENCE: 0.15,
    ScoreCategory.INTELLIGENCE: 0.10,
    ScoreCategory.RESOURCES: 0.10,
    ScoreCategory.LEADERSHIP: 0.15,
}


class CategoryScore(BaseModel):
    """Score for a single category"""
    category: ScoreCategory
    score: int = 0
    confidence: str = "exact"  # exact, estimate, unknown
    breakdown: Dict[str, Any] = Field(default_factory=dict)


class CountryScores(BaseModel):
    """Complete scoring data for a country"""
    country_id: str
    global_score: int = 0
    world_rank: int = 0
    intel_quality: str = "perfect"

    # Individual category scores
    military: CategoryScore
    economic: CategoryScore
    stability: CategoryScore
    influence: CategoryScore
    intelligence: CategoryScore
    resources: CategoryScore
    leadership: CategoryScore

    # Nuclear special handling
    nuclear_info: Optional[Dict[str, Any]] = None


class ScoringManager:
    """Manages game scoring with 7 categories"""

    def __init__(self):
        self.cache: Dict[str, CountryScores] = {}

    def reset(self):
        """Reset scoring state"""
        self.cache = {}

    def calculate_category_score(self, country, category: ScoreCategory) -> CategoryScore:
        """Calculate score for a single category"""
        breakdown = {}

        if category == ScoreCategory.MILITARY:
            base = country.military
            breakdown["base_military"] = country.military
            breakdown["nuclear_bonus"] = min(20, country.nuclear // 5)
            breakdown["tech_bonus"] = country.technology // 10
            score = base + breakdown["nuclear_bonus"] + breakdown["tech_bonus"]

        elif category == ScoreCategory.ECONOMIC:
            base = country.economy
            breakdown["base_economy"] = country.economy
            breakdown["tech_bonus"] = country.technology // 10
            breakdown["stability_bonus"] = country.stability // 20
            score = base + breakdown["tech_bonus"] + breakdown["stability_bonus"]

        elif category == ScoreCategory.STABILITY:
            base = country.stability
            breakdown["base_stability"] = country.stability
            breakdown["economy_factor"] = min(10, country.economy // 10)
            score = base + breakdown["economy_factor"]

        elif category == ScoreCategory.INFLUENCE:
            base = country.soft_power
            breakdown["soft_power"] = country.soft_power
            breakdown["sphere_size"] = len(country.sphere_of_influence) * 5
            breakdown["allies_count"] = len(country.allies) * 3
            score = base + breakdown["sphere_size"] + breakdown["allies_count"]

        elif category == ScoreCategory.INTELLIGENCE:
            # Intelligence score is based on tech and soft power
            base = (country.technology * 0.4 + country.soft_power * 0.3)
            breakdown["tech_base"] = int(country.technology * 0.4)
            breakdown["soft_power_base"] = int(country.soft_power * 0.3)
            # Bonus for tier
            tier_bonus = {1: 20, 2: 10, 3: 5, 4: 0}
            breakdown["tier_bonus"] = tier_bonus.get(country.tier, 0)
            score = base + breakdown["tier_bonus"]

        elif category == ScoreCategory.RESOURCES:
            base = country.resources
            breakdown["base_resources"] = country.resources
            breakdown["economy_factor"] = country.economy // 10
            score = base + breakdown["economy_factor"]

        elif category == ScoreCategory.LEADERSHIP:
            # Based on regime effectiveness and stability
            regime_scores = {
                "democracy": 70,
                "republic": 65,
                "monarchy": 55,
                "authoritarian": 50,
                "communist": 45,
                "theocracy": 40,
                "military_junta": 35,
            }
            base = regime_scores.get(country.regime, 50)
            breakdown["regime_base"] = base
            breakdown["stability_factor"] = country.stability // 5
            score = base + breakdown["stability_factor"]

        else:
            score = 50
            breakdown["default"] = 50

        return CategoryScore(
            category=category,
            score=min(100, max(0, int(score))),
            confidence="exact",
            breakdown=breakdown
        )

    def calculate_country_scores(
        self,
        country,
        world,
        observer_id: Optional[str] = None
    ) -> CountryScores:
        """Calculate all scores for a country with optional fog of war"""

        # Calculate all category scores
        categories = {}
        for cat in ScoreCategory:
            categories[cat.value] = self.calculate_category_score(country, cat)

        # Calculate global score
        global_score = sum(
            categories[cat.value].score * weight
            for cat, weight in CATEGORY_WEIGHTS.items()
        )

        # Get world rank
        world_rank = self._get_world_rank(country, world)

        # Apply fog of war if observer specified
        intel_quality = "perfect"
        if observer_id and observer_id != country.id:
            observer = world.get_country(observer_id)
            if observer:
                intel_score = espionage_manager.get_intel_score(observer, country, world)
                intel_quality = espionage_manager.get_intel_quality(intel_score).value

                # Apply fog to categories
                categories = self._apply_fog_to_categories(categories, intel_score)
                global_score = self._apply_fog_to_global(global_score, intel_score)

        # Nuclear info with special handling
        nuclear_info = None
        if observer_id:
            observer = world.get_country(observer_id)
            if observer:
                intel_score = espionage_manager.get_intel_score(observer, country, world)
                nuclear_info = espionage_manager.get_nuclear_display(country, intel_score)

        return CountryScores(
            country_id=country.id,
            global_score=int(global_score),
            world_rank=world_rank,
            intel_quality=intel_quality,
            military=categories["military"],
            economic=categories["economic"],
            stability=categories["stability"],
            influence=categories["influence"],
            intelligence=categories["intelligence"],
            resources=categories["resources"],
            leadership=categories["leadership"],
            nuclear_info=nuclear_info
        )

    def _apply_fog_to_categories(
        self,
        categories: Dict[str, CategoryScore],
        intel_score: int
    ) -> Dict[str, CategoryScore]:
        """Apply fog of war to category scores"""
        import random

        result = {}

        # Category visibility thresholds
        thresholds = {
            "economic": 20,
            "stability": 40,
            "influence": 40,
            "resources": 40,
            "leadership": 40,
            "military": 60,
            "intelligence": 80,
        }

        for cat_name, cat_score in categories.items():
            threshold = thresholds.get(cat_name, 40)

            if intel_score < threshold:
                # Cannot see this category
                result[cat_name] = CategoryScore(
                    category=cat_score.category,
                    score=0,
                    confidence="unknown",
                    breakdown={}
                )
            elif intel_score < threshold + 20:
                # Estimate with error
                margin = 15 if cat_name == "military" else 10
                error = random.randint(-margin, margin)
                result[cat_name] = CategoryScore(
                    category=cat_score.category,
                    score=max(0, min(100, cat_score.score + error)),
                    confidence="estimate",
                    breakdown={}  # Hide breakdown
                )
            else:
                # Full visibility
                result[cat_name] = cat_score

        return result

    def _apply_fog_to_global(self, global_score: float, intel_score: int) -> float:
        """Apply fog of war to global score"""
        import random

        if intel_score < 30:
            # Very rough estimate
            return global_score + random.randint(-20, 20)
        elif intel_score < 60:
            # Moderate estimate
            return global_score + random.randint(-10, 10)
        return global_score

    def _get_world_rank(self, country, world) -> int:
        """Get country's rank among all countries"""
        countries = sorted(
            world.get_countries_list(),
            key=lambda c: c.get_power_score(),
            reverse=True
        )
        for i, c in enumerate(countries):
            if c.id == country.id:
                return i + 1
        return len(countries)

    def get_rankings(
        self,
        world,
        observer_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get country rankings with optional fog of war"""
        countries = sorted(
            world.get_countries_list(),
            key=lambda c: c.power_score,
            reverse=True
        )

        results = []
        for i, country in enumerate(countries):
            entry = {
                "rank": i + 1,
                "id": country.id,
                "name": country.name,
                "name_fr": country.name_fr,
                "tier": country.tier,
                "score": country.power_score,
                "confidence": "exact"
            }

            # Apply fog of war
            if observer_id and observer_id != country.id:
                observer = world.get_country(observer_id)
                if observer:
                    intel_score = espionage_manager.get_intel_score(observer, country, world)
                    intel_quality = espionage_manager.get_intel_quality(intel_score)

                    if intel_quality == IntelQuality.NONE:
                        entry["score"] = None
                        entry["confidence"] = "unknown"
                    elif intel_quality in [IntelQuality.PARTIAL, IntelQuality.GOOD]:
                        import random
                        error = random.randint(-15, 15)
                        entry["score"] = max(0, country.power_score + error)
                        entry["confidence"] = "estimate"

            results.append(entry)

        return results


# Global instance
scoring_manager = ScoringManager()
