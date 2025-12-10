"""Region and Influence Zone models for Historia Lite"""
from typing import Dict, List, Optional
from pydantic import BaseModel, Field
from enum import Enum


class InfluenceType(str, Enum):
    """Types of influence a power can exert"""
    HEGEMONIC = "hegemonic"
    ECONOMIC = "economic"
    MILITARY = "military"
    ALLIANCE = "alliance"
    TERRITORIAL = "territorial"
    MIXED = "mixed"


class Region(BaseModel):
    """Geographic region with strategic value"""
    id: str
    name: str
    name_fr: str
    type: str = "continental"
    strategic_value: int = Field(default=5, ge=1, le=10)
    resources_type: str = "mixed"
    resources_value: int = Field(default=5, ge=1, le=10)
    population: int = 0
    connections: List[str] = Field(default_factory=list)
    controller: Optional[str] = None
    disputed: bool = False
    chokepoint: bool = False


class InfluenceZone(BaseModel):
    """Zone of influence for great powers"""
    id: str
    name: str
    name_fr: str

    # Dominant power and competitors
    dominant_power: Optional[str] = None
    contested_by: List[str] = Field(default_factory=list)

    # Countries in this zone
    countries_in_zone: List[str] = Field(default_factory=list)

    # Type and strength
    influence_type: str = "mixed"
    strength: int = Field(default=50, ge=0, le=100)

    # Influence levels by power (total score)
    influence_levels: Dict[str, int] = Field(default_factory=dict)

    # Detailed breakdown of influence by type for each power
    # Ex: {"USA": {"military": 30, "economic": 25, "monetary": 20, ...}}
    influence_breakdown: Dict[str, Dict[str, int]] = Field(default_factory=dict)

    # Cultural/religious characteristics of the zone
    dominant_religion: Optional[str] = None
    dominant_culture: Optional[str] = None
    dominant_language: Optional[str] = None

    # Resources
    has_oil: bool = False
    has_strategic_resources: bool = False

    # Historical
    former_colonial_power: Optional[str] = None

    def get_dominant_power(self) -> Optional[str]:
        """Get the power with highest influence"""
        if not self.influence_levels:
            return self.dominant_power
        return max(self.influence_levels, key=self.influence_levels.get)

    def is_contested(self) -> bool:
        """Check if zone is contested by multiple powers"""
        significant = [p for p, level in self.influence_levels.items() if level >= 30]
        return len(significant) > 1

    def get_contestants(self, threshold: int = 25) -> List[str]:
        """Get all powers with significant influence in this zone"""
        return [p for p, level in self.influence_levels.items() if level >= threshold]

    def add_influence(self, power_id: str, amount: int) -> None:
        """Add influence for a power"""
        current = self.influence_levels.get(power_id, 0)
        self.influence_levels[power_id] = max(0, min(100, current + amount))

    def remove_influence(self, power_id: str, amount: int) -> None:
        """Remove influence for a power"""
        self.add_influence(power_id, -amount)

    def update_breakdown(self, power_id: str, breakdown: Dict[str, int]) -> None:
        """Update the influence breakdown for a power and recalculate total"""
        self.influence_breakdown[power_id] = breakdown
        self.influence_levels[power_id] = sum(breakdown.values())

    def get_influence_by_type(self, power_id: str, influence_type: str) -> int:
        """Get a specific type of influence for a power"""
        if power_id not in self.influence_breakdown:
            return 0
        return self.influence_breakdown[power_id].get(influence_type, 0)

    def detect_domination_shift(self) -> Optional[str]:
        """Check if dominant power has changed, return new dominant if so"""
        current_dominant = self.get_dominant_power()
        if current_dominant != self.dominant_power:
            return current_dominant
        return None

    def update_contested_status(self) -> None:
        """Update the contested_by list based on current influence levels"""
        dominant = self.get_dominant_power()
        if dominant:
            dominant_level = self.influence_levels.get(dominant, 0)
            # Powers within 20 points of dominant are considered contesting
            self.contested_by = [
                p for p, level in self.influence_levels.items()
                if p != dominant and level >= dominant_level - 20 and level >= 25
            ]
