"""Enhanced war mechanics for Historia Lite"""
import logging
import random
from typing import List, Dict, Optional, Tuple
from enum import Enum

from pydantic import BaseModel, Field

from .events import Event

logger = logging.getLogger(__name__)


class TerrainType(str, Enum):
    """Terrain types affecting combat"""
    PLAIN = "plain"
    MOUNTAIN = "mountain"
    DESERT = "desert"
    URBAN = "urban"
    FOREST = "forest"
    JUNGLE = "jungle"
    ARCTIC = "arctic"
    NAVAL = "naval"


class WarPhase(str, Enum):
    """Phases of a war"""
    INITIAL = "initial"          # First year - high intensity
    STALEMATE = "stalemate"      # Long war, trench warfare
    OFFENSIVE = "offensive"       # Major push
    DEFENSIVE = "defensive"       # Holding ground
    COLLAPSE = "collapse"         # One side failing


# Terrain defense bonuses
TERRAIN_DEFENSE_BONUS = {
    TerrainType.PLAIN: 0,
    TerrainType.MOUNTAIN: 30,
    TerrainType.DESERT: 10,
    TerrainType.URBAN: 25,
    TerrainType.FOREST: 15,
    TerrainType.JUNGLE: 20,
    TerrainType.ARCTIC: 20,
    TerrainType.NAVAL: 0,
}

# Distance penalty per 1000km
DISTANCE_PENALTY_PER_1000KM = 5

# Region distances (approximate, in 1000km units)
REGION_DISTANCES = {
    ("north_america", "europe"): 6,
    ("north_america", "asia_pacific"): 10,
    ("north_america", "middle_east"): 11,
    ("north_america", "africa"): 9,
    ("north_america", "south_america"): 5,
    ("europe", "middle_east"): 4,
    ("europe", "asia_pacific"): 8,
    ("europe", "africa"): 4,
    ("asia_pacific", "middle_east"): 5,
    ("asia_pacific", "africa"): 8,
    ("middle_east", "africa"): 3,
    ("south_america", "africa"): 7,
}


class WarStats(BaseModel):
    """War statistics for a country in a conflict"""
    casualties: int = 0
    economic_cost: int = 0
    morale: int = 100
    supplies: int = 100
    territory_lost: int = 0
    territory_gained: int = 0


class EnhancedConflict(BaseModel):
    """Enhanced conflict with detailed war mechanics"""
    id: str
    type: str = "war"
    attackers: List[str] = Field(default_factory=list)
    defenders: List[str] = Field(default_factory=list)
    region: Optional[str] = None
    terrain: TerrainType = TerrainType.PLAIN
    intensity: int = Field(default=5, ge=1, le=10)
    duration: int = 0
    phase: WarPhase = WarPhase.INITIAL
    nuclear_risk: int = Field(default=0, ge=0, le=100)

    # Detailed stats per country
    war_stats: Dict[str, WarStats] = Field(default_factory=dict)

    # War objectives
    attacker_objective: str = "conquest"  # conquest, regime_change, territory, resources
    defender_objective: str = "survival"  # survival, liberation, status_quo

    # Blockades and sieges
    naval_blockade: bool = False
    air_superiority: Optional[str] = None  # country_id with air superiority


class WarManager:
    """Manages enhanced war mechanics"""

    def calculate_combat_power(
        self,
        country,  # Country model
        world,    # World model
        is_attacker: bool,
        conflict: EnhancedConflict,
    ) -> int:
        """Calculate effective combat power considering all factors"""

        # Base military power
        base_power = country.military

        # Technology bonus (up to +20)
        tech_bonus = min(20, country.technology // 5)

        # Economy sustains war effort
        economy_factor = country.economy / 100

        # Stability affects morale
        morale_factor = country.stability / 100

        # Nuclear deterrence
        nuclear_factor = 1.0
        if country.nuclear > 0:
            nuclear_factor = 1.1  # 10% psychological bonus

        # Distance penalty for attackers
        distance_penalty = 0
        if is_attacker and conflict.region:
            # Calculate distance based on country's region
            country_region = self._get_country_region(country.id)
            distance_penalty = self._calculate_distance_penalty(
                country_region, conflict.region
            )

        # Terrain bonus for defenders
        terrain_bonus = 0
        if not is_attacker:
            terrain_bonus = TERRAIN_DEFENSE_BONUS.get(conflict.terrain, 0)

        # Alliance support bonus
        alliance_bonus = 0
        if is_attacker:
            allies_in_war = [a for a in conflict.attackers if a != country.id]
        else:
            allies_in_war = [d for d in conflict.defenders if d != country.id]

        for ally_id in allies_in_war:
            ally = world.get_country(ally_id)
            if ally:
                alliance_bonus += ally.military // 10  # Each ally contributes 10%

        # War exhaustion from stats
        war_stats = conflict.war_stats.get(country.id, WarStats())
        exhaustion_penalty = (100 - war_stats.morale) // 4 + (100 - war_stats.supplies) // 5

        # Calculate final power
        effective_power = (
            base_power +
            tech_bonus +
            terrain_bonus +
            alliance_bonus -
            distance_penalty -
            exhaustion_penalty
        ) * economy_factor * morale_factor * nuclear_factor

        return max(1, int(effective_power))

    def process_war_tick(
        self,
        conflict: EnhancedConflict,
        world,
    ) -> Tuple[List[Event], bool]:
        """
        Process one year of war.
        Returns (events, war_ended)
        """
        events = []
        conflict.duration += 1

        # Initialize war stats if needed
        for country_id in conflict.attackers + conflict.defenders:
            if country_id not in conflict.war_stats:
                conflict.war_stats[country_id] = WarStats()

        # Calculate total power for each side
        attacker_power = 0
        defender_power = 0

        for attacker_id in conflict.attackers:
            attacker = world.get_country(attacker_id)
            if attacker:
                attacker_power += self.calculate_combat_power(
                    attacker, world, is_attacker=True, conflict=conflict
                )

        for defender_id in conflict.defenders:
            defender = world.get_country(defender_id)
            if defender:
                defender_power += self.calculate_combat_power(
                    defender, world, is_attacker=False, conflict=conflict
                )

        # Add randomness (fog of war)
        attacker_roll = random.randint(80, 120) / 100
        defender_roll = random.randint(80, 120) / 100

        effective_attacker = attacker_power * attacker_roll
        effective_defender = defender_power * defender_roll

        # Determine outcome
        power_ratio = effective_attacker / max(1, effective_defender)

        # Update war phase
        if conflict.duration == 1:
            conflict.phase = WarPhase.INITIAL
        elif conflict.duration > 3 and 0.8 < power_ratio < 1.2:
            conflict.phase = WarPhase.STALEMATE
        elif power_ratio > 1.5:
            conflict.phase = WarPhase.OFFENSIVE  # Attackers winning
        elif power_ratio < 0.7:
            conflict.phase = WarPhase.DEFENSIVE  # Defenders pushing back
        elif power_ratio < 0.4 or power_ratio > 2.5:
            conflict.phase = WarPhase.COLLAPSE  # One side collapsing

        # Apply effects
        events.extend(self._apply_war_effects(
            conflict, world, power_ratio
        ))

        # Check for war end conditions
        war_ended = self._check_war_end(conflict, world, power_ratio)

        return events, war_ended

    def _apply_war_effects(
        self,
        conflict: EnhancedConflict,
        world,
        power_ratio: float,
    ) -> List[Event]:
        """Apply war effects to participating countries"""
        events = []

        # Base costs scale with intensity
        base_economic_cost = conflict.intensity * 2
        base_stability_cost = conflict.intensity

        for attacker_id in conflict.attackers:
            attacker = world.get_country(attacker_id)
            if not attacker:
                continue

            stats = conflict.war_stats[attacker_id]

            # Economic drain (attackers pay more)
            economic_drain = base_economic_cost + 2
            if conflict.naval_blockade and attacker_id in conflict.attackers:
                economic_drain += 3  # Blockade hits attackers harder

            attacker.economy = max(0, attacker.economy - economic_drain)
            stats.economic_cost += economic_drain

            # Stability drain
            stability_drain = base_stability_cost
            if power_ratio < 0.8:  # Losing
                stability_drain += 3

            attacker.stability = max(0, attacker.stability - stability_drain)

            # Morale and supplies
            if power_ratio < 1.0:
                stats.morale = max(0, stats.morale - 5)
            stats.supplies = max(0, stats.supplies - 3)

            # Casualties affect population
            if conflict.intensity >= 7:
                attacker.population = max(0, attacker.population - 1)

        for defender_id in conflict.defenders:
            defender = world.get_country(defender_id)
            if not defender:
                continue

            stats = conflict.war_stats[defender_id]

            # Economic drain (defenders on home turf - slightly less)
            economic_drain = base_economic_cost
            defender.economy = max(0, defender.economy - economic_drain)
            stats.economic_cost += economic_drain

            # Stability drain (worse if losing)
            stability_drain = base_stability_cost
            if power_ratio > 1.2:  # Losing
                stability_drain += 4

            defender.stability = max(0, defender.stability - stability_drain)

            # Morale and supplies
            if power_ratio > 1.0:
                stats.morale = max(0, stats.morale - 5)
            stats.supplies = max(0, stats.supplies - 2)

            # Casualties
            if conflict.intensity >= 7:
                defender.population = max(0, defender.population - 1)

            # Territory loss if losing badly
            if power_ratio > 1.5:
                stats.territory_lost += 5

        # Generate events based on phase
        main_attacker = world.get_country(conflict.attackers[0])
        main_defender = world.get_country(conflict.defenders[0])

        if main_attacker and main_defender:
            if conflict.phase == WarPhase.COLLAPSE:
                if power_ratio > 2.0:
                    events.append(Event(
                        id=f"war_collapse_{world.year}_{conflict.id}",
                        year=world.year,
                        type="war",
                        title="Defensive Collapse",
                        title_fr="Effondrement defensif",
                        description=f"{main_defender.name}'s defenses are collapsing against {main_attacker.name}",
                        description_fr=f"Les defenses de {main_defender.name_fr} s'effondrent face a {main_attacker.name_fr}",
                        country_id=main_attacker.id,
                        target_id=main_defender.id,
                    ))
                else:
                    events.append(Event(
                        id=f"war_collapse_{world.year}_{conflict.id}",
                        year=world.year,
                        type="war",
                        title="Offensive Collapse",
                        title_fr="Effondrement offensif",
                        description=f"{main_attacker.name}'s offensive has stalled and is collapsing",
                        description_fr=f"L'offensive de {main_attacker.name_fr} s'est enlisee et s'effondre",
                        country_id=main_defender.id,
                        target_id=main_attacker.id,
                    ))
            elif conflict.phase == WarPhase.STALEMATE and conflict.duration % 2 == 0:
                events.append(Event(
                    id=f"war_stalemate_{world.year}_{conflict.id}",
                    year=world.year,
                    type="war",
                    title="War Stalemate",
                    title_fr="Guerre d'usure",
                    description=f"The war between {main_attacker.name} and {main_defender.name} has become a costly stalemate",
                    description_fr=f"La guerre entre {main_attacker.name_fr} et {main_defender.name_fr} est devenue une guerre d'usure couteuse",
                    country_id=main_attacker.id,
                ))

        return events

    def _check_war_end(
        self,
        conflict: EnhancedConflict,
        world,
        power_ratio: float,
    ) -> bool:
        """Check if war should end"""

        # Check for decisive victory
        if conflict.phase == WarPhase.COLLAPSE:
            # Attacker victory
            if power_ratio > 2.5:
                self._apply_victory(conflict, world, attacker_won=True)
                return True
            # Defender victory
            if power_ratio < 0.4:
                self._apply_victory(conflict, world, attacker_won=False)
                return True

        # Check for exhaustion peace (both sides tired)
        if conflict.duration >= 5:
            total_exhaustion = 0
            for stats in conflict.war_stats.values():
                total_exhaustion += (100 - stats.morale) + (100 - stats.supplies)

            avg_exhaustion = total_exhaustion / len(conflict.war_stats) if conflict.war_stats else 0

            if avg_exhaustion > 120:  # Both sides very tired
                peace_chance = 0.3 + (avg_exhaustion - 120) * 0.01
                if random.random() < peace_chance:
                    return True

        # Random peace after long war
        if conflict.duration >= 8:
            if random.random() < 0.4:  # 40% chance each year after 8 years
                return True

        return False

    def _apply_victory(
        self,
        conflict: EnhancedConflict,
        world,
        attacker_won: bool,
    ) -> None:
        """Apply victory effects"""
        winners = conflict.attackers if attacker_won else conflict.defenders
        losers = conflict.defenders if attacker_won else conflict.attackers

        for winner_id in winners:
            winner = world.get_country(winner_id)
            if winner:
                # Victory boost
                winner.stability = min(100, winner.stability + 15)
                winner.soft_power = min(100, winner.soft_power + 10)

        for loser_id in losers:
            loser = world.get_country(loser_id)
            if loser:
                # Defeat penalties
                loser.stability = max(0, loser.stability - 20)
                loser.military = max(0, loser.military - 15)

                # Territory loss
                stats = conflict.war_stats.get(loser_id, WarStats())
                if stats.territory_lost > 0:
                    loser.economy = max(0, loser.economy - stats.territory_lost // 2)

    def _get_country_region(self, country_id: str) -> str:
        """Get region for a country (simplified mapping)"""
        # Simplified region mapping
        region_map = {
            "USA": "north_america",
            "CAN": "north_america",
            "MEX": "north_america",
            "BRA": "south_america",
            "ARG": "south_america",
            "GBR": "europe",
            "FRA": "europe",
            "DEU": "europe",
            "ITA": "europe",
            "ESP": "europe",
            "POL": "europe",
            "UKR": "europe",
            "RUS": "europe",  # Straddles, but capital in Europe
            "CHN": "asia_pacific",
            "JPN": "asia_pacific",
            "KOR": "asia_pacific",
            "IND": "asia_pacific",
            "AUS": "asia_pacific",
            "SAU": "middle_east",
            "IRN": "middle_east",
            "ISR": "middle_east",
            "TUR": "middle_east",
            "EGY": "middle_east",
            "ZAF": "africa",
            "NGA": "africa",
            "ETH": "africa",
        }
        return region_map.get(country_id, "europe")

    def _calculate_distance_penalty(
        self,
        from_region: str,
        to_region: str,
    ) -> int:
        """Calculate distance penalty between regions"""
        if from_region == to_region:
            return 0

        # Check both orderings
        key1 = (from_region, to_region)
        key2 = (to_region, from_region)

        distance = REGION_DISTANCES.get(key1) or REGION_DISTANCES.get(key2, 5)

        return distance * DISTANCE_PENALTY_PER_1000KM


# Global instance
war_manager = WarManager()
