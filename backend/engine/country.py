"""Country model for Historia Lite"""
from typing import Dict, List, Optional, Literal
from pydantic import BaseModel, Field


# Alignment targets for Tier 4 countries
AlignmentTarget = Literal["USA", "CHN", "RUS", "EU", "NONE"]

# Religious/cultural categories
Religion = Literal[
    "secular",        # Secular state (France, USA)
    "christian",      # Christian majority
    "muslim",         # Muslim majority
    "hindu",          # Hindu majority (India)
    "buddhist",       # Buddhist majority
    "jewish",         # Jewish state (Israel)
    "orthodox",       # Orthodox Christian (Russia, Greece)
    "mixed"           # Multi-religious
]


class SocialProfile(BaseModel):
    """Social/cultural profile that affects reactions to certain policies"""
    religion: Religion = "secular"
    conservatism: int = Field(default=50, ge=0, le=100)  # 0=progressive, 100=conservative
    religiosity: int = Field(default=50, ge=0, le=100)   # 0=secular, 100=very religious
    nationalism: int = Field(default=50, ge=0, le=100)   # 0=globalist, 100=nationalist


class Personality(BaseModel):
    """AI personality traits that influence decision-making"""
    aggression: int = Field(default=50, ge=0, le=100)
    expansionism: int = Field(default=50, ge=0, le=100)
    diplomacy: int = Field(default=50, ge=0, le=100)
    risk_tolerance: int = Field(default=50, ge=0, le=100)


class MemoryScore(BaseModel):
    """
    Weighted temporal memory of events involving another country.
    Influences: diplomacy, aggression, alliances, stability, perception.
    Updated by TimelineManager based on events.
    """
    positive: float = 0.0       # Positive events (treaties, aid, cooperation)
    negative: float = 0.0       # Negative events (sanctions, attacks, betrayals)
    conflicts: float = 0.0      # Conflicts suffered/initiated
    diplomatic: float = 0.0     # Diplomatic interactions (positive or negative)
    last_updated_month: int = 0  # For decay calculation

    def get_net_sentiment(self) -> float:
        """Get net sentiment towards this country (-100 to +100 scale)"""
        raw = (self.positive - self.negative + self.diplomatic - self.conflicts * 2)
        return max(-100.0, min(100.0, raw))

    def decay(self, months_passed: int = 1) -> None:
        """Apply natural memory decay over time"""
        decay_rate = 0.95 ** months_passed  # 5% decay per month
        self.positive *= decay_rate
        self.negative *= decay_rate
        self.conflicts *= decay_rate
        self.diplomatic *= decay_rate


class Country(BaseModel):
    """Represents a nation in the simulation"""
    id: str
    name: str
    name_fr: str
    flag: str = ""
    tier: int = Field(default=3, ge=1, le=3)

    # Core stats (0-100)
    population: int = Field(default=50, ge=0, le=100)
    economy: int = Field(default=50, ge=0, le=100)
    military: int = Field(default=50, ge=0, le=100)
    nuclear: int = Field(default=0, ge=0, le=100)
    technology: int = Field(default=50, ge=0, le=100)
    stability: int = Field(default=50, ge=0, le=100)
    soft_power: int = Field(default=50, ge=0, le=100)
    resources: int = Field(default=50, ge=0, le=100)

    # AI behavior
    personality: Personality = Field(default_factory=Personality)

    # Social/cultural profile
    social_profile: SocialProfile = Field(default_factory=SocialProfile)

    # Political system
    regime: str = "democracy"

    # Alliances and blocs
    blocs: List[str] = Field(default_factory=list)

    # Diplomatic relations (-100 to +100)
    relations: Dict[str, int] = Field(default_factory=dict)

    # Temporal memory of other countries (Timeline Backbone)
    # Maps country_id -> MemoryScore
    memory_scores: Dict[str, MemoryScore] = Field(default_factory=dict)

    # Conflict state
    sanctions_on: List[str] = Field(default_factory=list)
    at_war: List[str] = Field(default_factory=list)
    allies: List[str] = Field(default_factory=list)
    rivals: List[str] = Field(default_factory=list)

    # Influence
    sphere_of_influence: List[str] = Field(default_factory=list)
    under_influence_of: Dict[str, int] = Field(default_factory=dict)

    # Player control
    is_player: bool = False

    def get_power_score(self) -> int:
        """Calculate overall power score"""
        return (
            self.economy * 0.25 +
            self.military * 0.25 +
            self.technology * 0.15 +
            self.population * 0.10 +
            self.nuclear * 0.10 +
            self.soft_power * 0.10 +
            self.resources * 0.05
        )

    def is_nuclear_power(self) -> bool:
        """Check if country has nuclear weapons"""
        return self.nuclear > 0

    def get_relation(self, other_id: str) -> int:
        """Get relation with another country"""
        return self.relations.get(other_id, 0)

    def modify_relation(self, other_id: str, delta: int) -> None:
        """Modify relation with another country"""
        current = self.relations.get(other_id, 0)
        self.relations[other_id] = max(-100, min(100, current + delta))

    def is_ally(self, other_id: str) -> bool:
        """Check if allied with another country"""
        return other_id in self.allies

    def is_at_war(self, other_id: str) -> bool:
        """Check if at war with another country"""
        return other_id in self.at_war

    def is_rival(self, other_id: str) -> bool:
        """Check if rival of another country"""
        return other_id in self.rivals

    def shares_bloc(self, other: "Country") -> bool:
        """Check if both countries share a bloc"""
        return bool(set(self.blocs) & set(other.blocs))

    # =========================================================================
    # MEMORY SYSTEM (Timeline Backbone)
    # =========================================================================

    def get_memory_of(self, country_id: str) -> MemoryScore:
        """Get memory score for another country (creates if doesn't exist)"""
        if country_id not in self.memory_scores:
            self.memory_scores[country_id] = MemoryScore()
        return self.memory_scores[country_id]

    def update_memory(
        self,
        country_id: str,
        positive: float = 0,
        negative: float = 0,
        conflicts: float = 0,
        diplomatic: float = 0,
        current_month: int = 0
    ) -> None:
        """Update memory score for another country based on an event"""
        memory = self.get_memory_of(country_id)
        memory.positive += positive
        memory.negative += negative
        memory.conflicts += conflicts
        memory.diplomatic += diplomatic
        if current_month > 0:
            memory.last_updated_month = current_month

    def get_memory_sentiment(self, country_id: str) -> float:
        """Get net sentiment towards another country from memory"""
        if country_id not in self.memory_scores:
            return 0.0
        return self.memory_scores[country_id].get_net_sentiment()

    def decay_all_memories(self, months_passed: int = 1) -> None:
        """Apply natural decay to all memories"""
        for memory in self.memory_scores.values():
            memory.decay(months_passed)

    def get_combined_relation(self, country_id: str) -> float:
        """
        Get combined relation score (base relation + memory sentiment).
        Memory adds ±30 max to the base relation.
        """
        base = self.get_relation(country_id)
        memory_bonus = self.get_memory_sentiment(country_id) * 0.3  # Max ±30
        return max(-100, min(100, base + memory_bonus))

    def is_tier4(self) -> bool:
        """Check if this is a Tier 4 country"""
        return False


class Tier4Country(BaseModel):
    """
    Simplified country model for Tier 4 (secondary states).
    Has fewer stats and simpler mechanics than main Country class.
    """
    id: str
    name: str
    name_fr: str
    flag: str = ""
    tier: int = Field(default=4, ge=4, le=4)
    region: str = ""  # africa, asia, middle_east, latam, europe, oceania

    # Simplified stats (4 instead of 8)
    economy: int = Field(default=25, ge=0, le=100)
    stability: int = Field(default=40, ge=0, le=100)
    population: int = Field(default=15, ge=0)  # Population in millions, no upper limit
    military: int = Field(default=15, ge=0, le=100)

    # Alignment system (-100 = pro-West, +100 = pro-China/Russia)
    alignment: int = Field(default=0, ge=-100, le=100)
    alignment_target: AlignmentTarget = "NONE"

    # Strategic resources (optional)
    strategic_resource: Optional[str] = None  # oil, minerals, agriculture, none

    # Relations with major powers only
    relations: Dict[str, int] = Field(default_factory=dict)

    # Simplified memory (major powers only) - Timeline Backbone
    memory_scores: Dict[str, MemoryScore] = Field(default_factory=dict)

    # Neighbors (for regional interactions)
    neighbors: List[str] = Field(default_factory=list)

    # Under influence of which power
    under_influence_of: Optional[str] = None

    # Conflict state (simplified)
    in_crisis: bool = False
    crisis_type: Optional[str] = None  # coup, civil_unrest, economic_collapse

    def is_tier4(self) -> bool:
        """Check if this is a Tier 4 country"""
        return True

    def get_power_score(self) -> int:
        """Calculate simplified power score"""
        return (
            self.economy * 0.35 +
            self.military * 0.30 +
            self.stability * 0.20 +
            self.population * 0.15
        )

    def get_alignment_label(self) -> str:
        """Get human-readable alignment label"""
        if self.alignment <= -60:
            return "pro_west"
        elif self.alignment <= -20:
            return "west_leaning"
        elif self.alignment < 20:
            return "neutral"
        elif self.alignment < 60:
            return "east_leaning"
        else:
            return "pro_east"

    def get_relation(self, other_id: str) -> int:
        """Get relation with a major power"""
        return self.relations.get(other_id, 0)

    def modify_relation(self, other_id: str, delta: int) -> None:
        """Modify relation with a major power"""
        current = self.relations.get(other_id, 0)
        self.relations[other_id] = max(-100, min(100, current + delta))

    def shift_alignment(self, delta: int) -> None:
        """Shift alignment towards East (+) or West (-)"""
        self.alignment = max(-100, min(100, self.alignment + delta))

    # Memory system (simplified for Tier 4)
    def get_memory_of(self, country_id: str) -> MemoryScore:
        """Get memory score for a major power"""
        if country_id not in self.memory_scores:
            self.memory_scores[country_id] = MemoryScore()
        return self.memory_scores[country_id]

    def update_memory(
        self,
        country_id: str,
        positive: float = 0,
        negative: float = 0,
        conflicts: float = 0,
        diplomatic: float = 0,
        current_month: int = 0
    ) -> None:
        """Update memory score for a major power"""
        memory = self.get_memory_of(country_id)
        memory.positive += positive
        memory.negative += negative
        memory.conflicts += conflicts
        memory.diplomatic += diplomatic
        if current_month > 0:
            memory.last_updated_month = current_month

    def get_memory_sentiment(self, country_id: str) -> float:
        """Get net sentiment towards a major power from memory"""
        if country_id not in self.memory_scores:
            return 0.0
        return self.memory_scores[country_id].get_net_sentiment()


class Tier5Country(BaseModel):
    """
    Small country model for Tier 5 (minor states).
    Minimal AI - batch processing by region every 3 ticks.
    Only 4 stats, no military, no individual relations.
    """
    id: str
    name: str
    name_fr: str
    flag: str = ""
    tier: int = Field(default=5, ge=5, le=5)
    region: str = ""  # africa, asia, middle_east, latam, europe, oceania, caribbean

    # Minimal stats (4 instead of 8)
    economy: int = Field(default=20, ge=0, le=100)
    stability: int = Field(default=40, ge=0, le=100)
    population: int = Field(default=10, ge=0, le=100)
    alignment: int = Field(default=0, ge=-100, le=100)  # -100=pro-West, +100=pro-East

    # Neighbors (for regional interactions only)
    neighbors: List[str] = Field(default_factory=list)

    # Protector (major power that defends this country)
    protector: Optional[str] = None  # USA, FRA, GBR, CHN, RUS, etc.

    # Influence zone (for regional reactions)
    influence_zone: Optional[str] = None  # western_europe, east_asia, etc.

    # Crisis state
    in_crisis: bool = False
    crisis_type: Optional[str] = None  # coup, civil_unrest, economic_collapse, famine

    def is_tier4(self) -> bool:
        return False

    def is_tier5(self) -> bool:
        return True

    def is_tier6(self) -> bool:
        return False

    def get_power_score(self) -> int:
        """Calculate minimal power score (no military)"""
        return int(
            self.economy * 0.40 +
            self.stability * 0.35 +
            self.population * 0.25
        )

    def get_alignment_label(self) -> str:
        """Get human-readable alignment label"""
        if self.alignment <= -60:
            return "pro_west"
        elif self.alignment <= -20:
            return "west_leaning"
        elif self.alignment < 20:
            return "neutral"
        elif self.alignment < 60:
            return "east_leaning"
        else:
            return "pro_east"

    def shift_alignment(self, delta: int) -> None:
        """Shift alignment towards East (+) or West (-)"""
        self.alignment = max(-100, min(100, self.alignment + delta))


class Tier6Country(BaseModel):
    """
    Micro-nation model for Tier 6 (micro-states, territories).
    Passive AI - bulk update every 5 ticks, follows protector.
    Only 3 stats, no autonomous decisions.
    """
    id: str
    name: str
    name_fr: str
    flag: str = ""
    tier: int = Field(default=6, ge=6, le=6)
    region: str = ""  # europe, caribbean, pacific, indian_ocean, etc.

    # Ultra-minimal stats (3 only)
    economy: int = Field(default=30, ge=0, le=100)  # Can be high (Monaco, Luxembourg)
    stability: int = Field(default=70, ge=0, le=100)  # Usually stable
    population: int = Field(default=1, ge=0, le=10)  # Always very small (0-10 scale)

    # Protector (usually required for Tier 6, but can be null for independent micro-states)
    protector: Optional[str] = None  # USA, FRA, GBR, AUS, NZL, DNK, NLD, etc.

    # Influence zone
    influence_zone: Optional[str] = None  # western_europe, pacific, caribbean, etc.

    # Special status
    is_territory: bool = False  # True for non-sovereign territories (GUM, PYF, etc.)
    special_status: Optional[str] = None  # tax_haven, tourism, strategic_base

    def is_tier4(self) -> bool:
        return False

    def is_tier5(self) -> bool:
        return False

    def is_tier6(self) -> bool:
        return True

    def get_power_score(self) -> int:
        """Calculate micro power score"""
        return int(
            self.economy * 0.50 +
            self.stability * 0.40 +
            self.population * 0.10
        )

    def get_protector_alignment(self, world) -> int:
        """Get alignment from protector"""
        if self.protector and hasattr(world, 'countries'):
            protector = world.countries.get(self.protector)
            if protector:
                # Tier 6 follows protector's geopolitical stance
                # Pro-West protectors (USA, FRA, GBR, etc.) = negative alignment
                # Pro-East protectors (CHN, RUS) = positive alignment
                if self.protector in ("USA", "GBR", "FRA", "DEU", "AUS", "NZL", "CAN", "JPN"):
                    return -50
                elif self.protector in ("CHN", "RUS"):
                    return 50
        return 0
