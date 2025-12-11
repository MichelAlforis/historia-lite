"""Espionage system with Fog of War for Historia Lite"""
import logging
import random
from typing import List, Dict, Optional, Any
from enum import IntEnum, Enum

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class SecretLevel(IntEnum):
    """Classification levels for information"""
    PUBLIC = 0       # Anyone can see
    LOW = 20         # Basic intel needed
    MEDIUM = 40      # Good intel needed
    HIGH = 60        # Very good intel needed
    TOP_SECRET = 80  # Excellent intel needed


class IntelQuality(str, Enum):
    """Quality of intelligence on a target"""
    NONE = "none"           # 0-19: Only public info
    PARTIAL = "partial"     # 20-39: Basic economic info
    GOOD = "good"           # 40-59: Most stats visible
    VERY_GOOD = "very_good" # 60-79: Military visible (approx)
    EXCELLENT = "excellent" # 80-89: Nuclear confirmed
    PERFECT = "perfect"     # 90-100: All details exact


class Confidence(str, Enum):
    """Confidence level for displayed information"""
    EXACT = "exact"         # Real value
    ESTIMATE = "estimate"   # +/- margin of error
    UNKNOWN = "unknown"     # Cannot see


# What info is visible at each secret level
INFO_SECRET_LEVELS = {
    # Public info
    "id": SecretLevel.PUBLIC,
    "name": SecretLevel.PUBLIC,
    "name_fr": SecretLevel.PUBLIC,
    "flag": SecretLevel.PUBLIC,
    "tier": SecretLevel.PUBLIC,
    "region": SecretLevel.PUBLIC,
    "regime": SecretLevel.PUBLIC,

    # Low secret
    "population": SecretLevel.LOW,
    "economy": SecretLevel.LOW,
    "blocs": SecretLevel.LOW,

    # Medium secret
    "stability": SecretLevel.MEDIUM,
    "technology": SecretLevel.MEDIUM,
    "soft_power": SecretLevel.MEDIUM,
    "resources": SecretLevel.MEDIUM,
    "allies": SecretLevel.MEDIUM,
    "rivals": SecretLevel.MEDIUM,

    # High secret (military)
    "military": SecretLevel.HIGH,
    "military_bases": SecretLevel.HIGH,
    "at_war": SecretLevel.HIGH,
    "sanctions_on": SecretLevel.HIGH,

    # Top secret (nuclear + intel)
    "nuclear": SecretLevel.TOP_SECRET,
    "nuclear_warheads": SecretLevel.TOP_SECRET,
    "intelligence_score": SecretLevel.TOP_SECRET,
    "active_operations": SecretLevel.TOP_SECRET,
    "secret_projects": SecretLevel.TOP_SECRET,
}


class SpyMission(BaseModel):
    """An active espionage mission"""
    id: str
    agent_country: str
    target_country: str
    mission_type: str  # recon, deep_intel, sabotage, steal_tech
    progress: int = 0
    success_chance: int = 50
    started_year: int = 0


class IntelReport(BaseModel):
    """Intelligence report on a country"""
    target_id: str
    observer_id: str
    intel_score: int = 0
    intel_quality: IntelQuality = IntelQuality.NONE
    data: Dict[str, Any] = Field(default_factory=dict)
    confidence: Dict[str, Confidence] = Field(default_factory=dict)
    last_updated: int = 0


class EspionageManager:
    """Manages espionage and Fog of War"""

    def __init__(self):
        self.operations: List[SpyMission] = []
        self.intel_cache: Dict[str, Dict[str, IntelReport]] = {}  # observer -> target -> report

    def reset(self):
        """Reset espionage state"""
        self.operations = []
        self.intel_cache = {}

    def get_intel_score(self, observer, target, world=None) -> int:
        """
        Calculate intelligence score between two countries.
        Higher = better intel on target.
        """
        if observer.id == target.id:
            return 100  # Perfect intel on self

        base_score = 0

        # Base from observer's capabilities
        base_score += observer.technology * 0.3
        base_score += observer.soft_power * 0.2
        base_score += getattr(observer, 'intelligence', 50) * 0.3

        # Relationship bonuses
        relations = observer.relations.get(target.id, 0)

        if target.id in observer.allies:
            base_score += 15
        elif target.id in observer.rivals:
            base_score -= 25
        elif relations > 50:
            base_score += 10
        elif relations < -50:
            base_score -= 15

        # Bloc bonuses
        shared_blocs = set(observer.blocs) & set(target.blocs)
        if shared_blocs:
            base_score += 10

        # Sanctions penalty
        if target.id in observer.sanctions_on:
            base_score -= 15
        if observer.id in target.sanctions_on:
            base_score -= 10

        # Regime type affects openness
        regime_modifier = {
            "democracy": 10,
            "republic": 5,
            "monarchy": 0,
            "authoritarian": -10,
            "communist": -15,
            "theocracy": -10,
        }
        base_score += regime_modifier.get(target.regime, 0)

        # Tier affects intel difficulty
        if target.tier == 1:
            base_score -= 10  # Superpowers harder to spy on
        elif target.tier >= 3:
            base_score += 5   # Smaller countries easier

        return max(0, min(100, int(base_score)))

    def get_intel_quality(self, intel_score: int) -> IntelQuality:
        """Convert intel score to quality level"""
        if intel_score >= 90:
            return IntelQuality.PERFECT
        elif intel_score >= 80:
            return IntelQuality.EXCELLENT
        elif intel_score >= 60:
            return IntelQuality.VERY_GOOD
        elif intel_score >= 40:
            return IntelQuality.GOOD
        elif intel_score >= 20:
            return IntelQuality.PARTIAL
        return IntelQuality.NONE

    def can_see_info(self, intel_score: int, field: str) -> bool:
        """Check if observer can see this field"""
        required_level = INFO_SECRET_LEVELS.get(field, SecretLevel.MEDIUM)
        return intel_score >= required_level

    def get_confidence(self, intel_score: int, field: str) -> Confidence:
        """Determine confidence level for a field"""
        required_level = INFO_SECRET_LEVELS.get(field, SecretLevel.MEDIUM)

        if intel_score < required_level:
            return Confidence.UNKNOWN

        # High clearance = exact, otherwise estimate
        margin = intel_score - required_level
        if margin >= 20:
            return Confidence.EXACT
        return Confidence.ESTIMATE

    def apply_fog_of_war(self, country_data: dict, intel_score: int) -> Dict[str, Any]:
        """
        Apply fog of war to country data.
        Returns filtered data with confidence levels.
        """
        result = {}
        confidence = {}

        for field, value in country_data.items():
            if not self.can_see_info(intel_score, field):
                # Cannot see this field
                confidence[field] = Confidence.UNKNOWN.value
                if field in ["nuclear", "military"]:
                    result[field] = None  # Explicitly hidden
                # Don't include other hidden fields
                continue

            field_confidence = self.get_confidence(intel_score, field)
            confidence[field] = field_confidence.value

            if field_confidence == Confidence.EXACT:
                result[field] = value
            elif field_confidence == Confidence.ESTIMATE:
                # Add error margin to numeric values
                if isinstance(value, (int, float)):
                    margin = self._get_error_margin(intel_score, field)
                    error = random.uniform(-margin, margin)
                    result[field] = max(0, min(100, int(value + error)))
                else:
                    result[field] = value
            # UNKNOWN fields not included

        result["_confidence"] = confidence
        result["_intel_score"] = intel_score
        result["_intel_quality"] = self.get_intel_quality(intel_score).value

        return result

    def _get_error_margin(self, intel_score: int, field: str) -> float:
        """Get error margin for estimated values"""
        required = INFO_SECRET_LEVELS.get(field, SecretLevel.MEDIUM)
        gap = required - intel_score + 20

        # Military always has some uncertainty
        if field == "military":
            return max(10, gap * 1.5)
        if field == "nuclear":
            return max(15, gap * 2)

        return max(5, gap)

    def get_nuclear_display(self, target, intel_score: int) -> Dict[str, Any]:
        """
        Special handling for nuclear information.
        Returns display info about nuclear capability.
        """
        actual_nuclear = getattr(target, 'nuclear', 0)

        if intel_score < 80:
            return {
                "status": "unknown",
                "display": "Intel insuffisante",
                "display_fr": "Intel insuffisante",
                "warheads": None,
                "confidence": "unknown"
            }

        if actual_nuclear == 0:
            return {
                "status": "none",
                "display": "No nuclear capability",
                "display_fr": "Pas de capacite nucleaire",
                "warheads": 0,
                "confidence": "exact" if intel_score >= 90 else "estimate"
            }

        if intel_score >= 90:
            # Perfect intel - exact warhead count
            warheads = self._estimate_warheads(actual_nuclear)
            return {
                "status": "confirmed",
                "display": f"{warheads} operational warheads",
                "display_fr": f"{warheads} tetes nucleaires",
                "warheads": warheads,
                "confidence": "exact"
            }
        else:
            # 80-89: Confirmed but no count
            return {
                "status": "confirmed",
                "display": "Nuclear arsenal confirmed",
                "display_fr": "Arsenal nucleaire confirme",
                "warheads": None,
                "confidence": "estimate"
            }

    def _estimate_warheads(self, nuclear_score: int) -> int:
        """Estimate warhead count from nuclear score"""
        # Rough mapping: score 1-100 to warheads
        if nuclear_score >= 90:
            return random.randint(5000, 7000)  # USA/Russia level
        elif nuclear_score >= 70:
            return random.randint(200, 500)    # China/France level
        elif nuclear_score >= 50:
            return random.randint(100, 200)    # UK/India level
        elif nuclear_score >= 30:
            return random.randint(20, 100)     # Pakistan/Israel level
        elif nuclear_score > 0:
            return random.randint(5, 20)       # North Korea level
        return 0

    def process_espionage(self, world) -> List:
        """Process active espionage operations"""
        events = []

        for mission in self.operations[:]:
            mission.progress += random.randint(10, 30)

            if mission.progress >= 100:
                success = random.randint(1, 100) <= mission.success_chance
                if success:
                    events.extend(self._complete_mission(mission, world))
                else:
                    events.extend(self._fail_mission(mission, world))
                self.operations.remove(mission)

        return events

    def start_mission(self, agent_id: str, target_id: str, mission_type: str, world) -> Optional[SpyMission]:
        """Start a new espionage mission"""
        agent = world.get_country(agent_id)
        target = world.get_country(target_id)

        if not agent or not target:
            return None

        # Calculate success chance
        intel_score = self.get_intel_score(agent, target, world)
        base_chance = 30 + intel_score // 3

        mission = SpyMission(
            id=f"{agent_id}_{target_id}_{world.year}",
            agent_country=agent_id,
            target_country=target_id,
            mission_type=mission_type,
            success_chance=min(90, base_chance),
            started_year=world.year
        )

        self.operations.append(mission)
        return mission

    def _complete_mission(self, mission: SpyMission, world) -> List:
        """Handle successful mission completion"""
        from .events import Event

        events = []

        if mission.mission_type == "deep_intel":
            # Boost intel on target temporarily
            agent = world.get_country(mission.agent_country)
            if agent:
                # Could store intel bonus somewhere
                pass

            events.append(Event(
                type="espionage_success",
                year=world.year,
                description=f"Intelligence operation successful against {mission.target_country}",
                description_fr=f"Operation de renseignement reussie contre {mission.target_country}",
                severity="medium",
                country_ids=[mission.agent_country]
            ))

        return events

    def _fail_mission(self, mission: SpyMission, world) -> List:
        """Handle failed/detected mission"""
        from .events import Event

        events = []
        target = world.get_country(mission.target_country)
        agent = world.get_country(mission.agent_country)

        if target and agent:
            # Worsen relations
            current = target.relations.get(mission.agent_country, 0)
            target.relations[mission.agent_country] = max(-100, current - 15)

            events.append(Event(
                type="espionage_detected",
                year=world.year,
                description=f"{target.name} caught spies from {agent.name}",
                description_fr=f"{target.name_fr} a capture des espions de {agent.name_fr}",
                severity="high",
                country_ids=[mission.target_country, mission.agent_country]
            ))

        return events


# Global instance
espionage_manager = EspionageManager()
