"""Unified country model for all tiers - Phase 12 Architecture Unification"""
from typing import Dict, List, Optional, Literal, Union
from pydantic import BaseModel, Field, computed_field


# AI processing levels
AILevel = Literal["full", "standard", "simplified", "minimal", "passive"]

# Alignment targets
AlignmentTarget = Literal["USA", "CHN", "RUS", "EU", "NONE"]

# Religious/cultural categories
Religion = Literal[
    "secular", "christian", "muslim", "hindu", "buddhist",
    "jewish", "orthodox", "confucian", "mixed"
]


class Personality(BaseModel):
    """AI personality traits (Tier 1-3 only)"""
    aggression: int = Field(default=50, ge=0, le=100)
    expansionism: int = Field(default=50, ge=0, le=100)
    diplomacy: int = Field(default=50, ge=0, le=100)
    risk_tolerance: int = Field(default=50, ge=0, le=100)


class SocialProfile(BaseModel):
    """Social/cultural profile (Tier 1-3 only)"""
    religion: Religion = "secular"
    conservatism: int = Field(default=50, ge=0, le=100)
    religiosity: int = Field(default=50, ge=0, le=100)
    nationalism: int = Field(default=50, ge=0, le=100)


class BaseCountry(BaseModel):
    """
    Unified model for ALL countries (Tier 1-6).

    Stats and features are progressively available based on tier:
    - Tier 1-2: Full stats (8), personality, relations, alliances
    - Tier 3: Full stats (8), simplified personality, regional relations
    - Tier 4: Reduced stats (5), alignment system, major power relations
    - Tier 5: Minimal stats (4), regional batch processing, protector
    - Tier 6: Ultra-minimal stats (3), passive, follows protector
    """
    # Core identity
    id: str
    name: str
    name_fr: str
    flag: str = ""
    tier: int = Field(default=4, ge=1, le=6)
    region: str = "unknown"

    # Base stats (present for all tiers)
    economy: int = Field(default=50, ge=0, le=100)
    stability: int = Field(default=50, ge=0, le=100)
    population: int = Field(default=10, ge=0)

    # Extended stats (Tier 1-4, Optional for Tier 5-6)
    military: Optional[int] = Field(default=None, ge=0, le=100)

    # Advanced stats (Tier 1-3 only)
    nuclear: Optional[int] = Field(default=None, ge=0, le=100)
    technology: Optional[int] = Field(default=None, ge=0, le=100)
    soft_power: Optional[int] = Field(default=None, ge=0, le=100)
    resources: Optional[int] = Field(default=None, ge=0, le=100)

    # AI personality (Tier 1-3 only)
    personality: Optional[Personality] = None

    # Social profile (Tier 1-3 only)
    social_profile: Optional[SocialProfile] = None

    # Political system
    regime: str = "democracy"

    # Alignment system (-100 = pro-West, +100 = pro-East)
    # Used for Tier 4-6, optional for Tier 1-3
    alignment: Optional[int] = Field(default=None, ge=-100, le=100)
    alignment_target: AlignmentTarget = "NONE"

    # Protection system (Tier 4-6)
    protector: Optional[str] = None
    influence_zone: Optional[str] = None

    # Alliances and blocs (Tier 1-3 mainly)
    blocs: List[str] = Field(default_factory=list)
    allies: List[str] = Field(default_factory=list)
    rivals: List[str] = Field(default_factory=list)
    neighbors: List[str] = Field(default_factory=list)

    # Diplomatic relations
    relations: Dict[str, int] = Field(default_factory=dict)

    # Influence
    sphere_of_influence: List[str] = Field(default_factory=list)
    under_influence_of: Optional[str] = None

    # Conflict state
    sanctions_on: List[str] = Field(default_factory=list)
    at_war: List[str] = Field(default_factory=list)

    # Crisis state (Tier 4-6)
    in_crisis: bool = False
    crisis_type: Optional[str] = None

    # Strategic resources (Tier 4-5)
    strategic_resource: Optional[str] = None

    # Tier 6 specific
    is_territory: bool = False
    special_status: Optional[str] = None

    # AI processing configuration
    ai_level: AILevel = "minimal"
    process_frequency: int = Field(default=1, ge=1, le=10)

    # For tier change tracking (hysteresis)
    tier_stability_counter: int = 0

    # Player control
    is_player: bool = False

    # Additional metadata for Tier 1-3
    religion: Optional[str] = None
    culture: Optional[str] = None
    language: Optional[str] = None
    colonial_history: Optional[str] = None

    @computed_field
    @property
    def power_score(self) -> int:
        """Calculate overall power score based on available stats"""
        if self.tier <= 2:
            # Full calculation for major powers
            return int(
                self.economy * 0.25 +
                (self.military or 0) * 0.25 +
                (self.technology or 0) * 0.15 +
                self.population * 0.10 +
                (self.nuclear or 0) * 0.10 +
                (self.soft_power or 0) * 0.10 +
                (self.resources or 0) * 0.05
            )
        elif self.tier == 3:
            # Standard calculation
            return int(
                self.economy * 0.30 +
                (self.military or 0) * 0.30 +
                (self.technology or 0) * 0.15 +
                self.stability * 0.15 +
                self.population * 0.10
            )
        elif self.tier == 4:
            # Simplified calculation
            return int(
                self.economy * 0.35 +
                (self.military or 0) * 0.30 +
                self.stability * 0.20 +
                min(self.population, 100) * 0.15
            )
        elif self.tier == 5:
            # Minimal calculation (no military)
            return int(
                self.economy * 0.40 +
                self.stability * 0.35 +
                min(self.population, 100) * 0.25
            )
        else:
            # Tier 6: micro calculation
            return int(
                self.economy * 0.50 +
                self.stability * 0.40 +
                min(self.population, 10) * 1.0
            )

    def get_alignment_label(self) -> str:
        """Get human-readable alignment label"""
        if self.alignment is None:
            return "n/a"
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

    def is_nuclear_power(self) -> bool:
        """Check if country has nuclear weapons"""
        return (self.nuclear or 0) > 0

    def get_relation(self, other_id: str) -> int:
        """Get relation with another country"""
        return self.relations.get(other_id, 0)

    def modify_relation(self, other_id: str, delta: int) -> None:
        """Modify relation with another country"""
        current = self.relations.get(other_id, 0)
        self.relations[other_id] = max(-100, min(100, current + delta))

    def shift_alignment(self, delta: int) -> None:
        """Shift alignment towards East (+) or West (-)"""
        if self.alignment is not None:
            self.alignment = max(-100, min(100, self.alignment + delta))

    def is_ally(self, other_id: str) -> bool:
        """Check if allied with another country"""
        return other_id in self.allies

    def is_at_war(self, other_id: str) -> bool:
        """Check if at war with another country"""
        return other_id in self.at_war

    def is_rival(self, other_id: str) -> bool:
        """Check if rival of another country"""
        return other_id in self.rivals

    def shares_bloc(self, other: "BaseCountry") -> bool:
        """Check if both countries share a bloc"""
        return bool(set(self.blocs) & set(other.blocs))

    def should_process_this_tick(self, tick_number: int) -> bool:
        """Check if this country should be processed on this tick"""
        return tick_number % self.process_frequency == 0

    def get_protector_alignment(self, countries_lookup: Dict[str, "BaseCountry"]) -> int:
        """Get alignment from protector (Tier 5-6)"""
        if self.protector and self.protector in countries_lookup:
            protector = countries_lookup[self.protector]
            # Pro-West protectors
            if self.protector in ("USA", "GBR", "FRA", "DEU", "AUS", "NZL", "CAN", "JPN"):
                return -50
            # Pro-East protectors
            elif self.protector in ("CHN", "RUS"):
                return 50
            # Other protectors - use their alignment
            elif protector.alignment is not None:
                return protector.alignment
        return 0

    @classmethod
    def from_tier1_3_data(cls, data: dict) -> "BaseCountry":
        """Create BaseCountry from Tier 1-3 JSON data"""
        # Set AI level based on tier
        tier = data.get("tier", 3)
        ai_level = "full" if tier <= 2 else "standard"

        # Personality
        personality_data = data.get("personality")
        personality = Personality(**personality_data) if personality_data else Personality()

        return cls(
            id=data["id"],
            name=data["name"],
            name_fr=data["name_fr"],
            flag=data.get("flag", ""),
            tier=tier,
            region=data.get("region", "unknown"),
            # Core stats
            economy=data.get("economy", 50),
            stability=data.get("stability", 50),
            population=data.get("population", 50),
            # Extended stats
            military=data.get("military", 50),
            nuclear=data.get("nuclear", 0),
            technology=data.get("technology", 50),
            soft_power=data.get("soft_power", 50),
            resources=data.get("resources", 50),
            # Personality and social
            personality=personality,
            regime=data.get("regime", "democracy"),
            # Alliances
            blocs=data.get("blocs", []),
            allies=data.get("allies", []),
            rivals=data.get("rivals", []),
            # AI config
            ai_level=ai_level,
            process_frequency=1,
            # Metadata
            religion=data.get("religion"),
            culture=data.get("culture"),
            language=data.get("language"),
            colonial_history=data.get("colonial_history"),
        )

    @classmethod
    def from_tier4_data(cls, data: dict) -> "BaseCountry":
        """Create BaseCountry from Tier 4 JSON data"""
        return cls(
            id=data["id"],
            name=data["name"],
            name_fr=data["name_fr"],
            flag=data.get("flag", ""),
            tier=4,
            region=data.get("region", "unknown"),
            # Core stats
            economy=data.get("economy", 25),
            stability=data.get("stability", 40),
            population=data.get("population", 15),
            military=data.get("military", 15),
            # Alignment
            alignment=data.get("alignment", 0),
            # Protection
            protector=data.get("protector"),
            influence_zone=data.get("influence_zone"),
            # Resources
            strategic_resource=data.get("strategic_resource"),
            neighbors=data.get("neighbors", []),
            # AI config
            ai_level="simplified",
            process_frequency=2,
        )

    @classmethod
    def from_tier5_data(cls, data: dict) -> "BaseCountry":
        """Create BaseCountry from Tier 5 JSON data"""
        return cls(
            id=data["id"],
            name=data["name"],
            name_fr=data["name_fr"],
            flag=data.get("flag", ""),
            tier=5,
            region=data.get("region", "unknown"),
            # Core stats (no military)
            economy=data.get("economy", 20),
            stability=data.get("stability", 40),
            population=data.get("population", 10),
            # Alignment
            alignment=data.get("alignment", 0),
            # Protection
            protector=data.get("protector"),
            influence_zone=data.get("influence_zone"),
            neighbors=data.get("neighbors", []),
            # AI config
            ai_level="minimal",
            process_frequency=3,
        )

    @classmethod
    def from_tier6_data(cls, data: dict) -> "BaseCountry":
        """Create BaseCountry from Tier 6 JSON data"""
        return cls(
            id=data["id"],
            name=data["name"],
            name_fr=data["name_fr"],
            flag=data.get("flag", ""),
            tier=6,
            region=data.get("region", "unknown"),
            # Ultra-minimal stats
            economy=data.get("economy", 30),
            stability=data.get("stability", 70),
            population=data.get("population", 1),
            # Protection
            protector=data.get("protector"),
            influence_zone=data.get("influence_zone"),
            # Tier 6 specific
            is_territory=data.get("is_territory", False),
            special_status=data.get("special_status"),
            # AI config
            ai_level="passive",
            process_frequency=5,
        )


# Type alias for backwards compatibility
Country = BaseCountry
Tier4Country = BaseCountry
Tier5Country = BaseCountry
Tier6Country = BaseCountry
