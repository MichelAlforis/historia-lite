"""Victory and defeat conditions for Historia Lite"""
import logging
from typing import Optional, Tuple, List
from enum import Enum

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class GameEndReason(str, Enum):
    """Reasons for game ending"""
    SCENARIO_COMPLETE = "scenario_complete"
    DOMINATION = "domination"
    ECONOMIC_VICTORY = "economic_victory"
    MILITARY_VICTORY = "military_victory"
    TIME_LIMIT = "time_limit"
    COLLAPSE = "collapse"
    BANKRUPTCY = "bankruptcy"
    ANNEXED = "annexed"
    NUCLEAR_WAR = "nuclear_war"
    COUP_DETAT = "coup_detat"


class GameEndState(BaseModel):
    """State when game ends"""
    ended: bool = True
    reason: GameEndReason
    message: str = ""
    message_fr: str = ""
    score: int = 0
    winner: Optional[str] = None
    year: int = 0
    details: dict = Field(default_factory=dict)


class VictoryManager:
    """Manages victory and defeat conditions"""

    def __init__(self):
        self.game_end_state: Optional[GameEndState] = None
        self.stability_tracker: dict[str, List[int]] = {}

    def reset(self):
        """Reset for new game"""
        self.game_end_state = None
        self.stability_tracker = {}

    def check_game_end(self, world) -> Tuple[bool, Optional[GameEndState]]:
        """
        Check if game should end.
        Returns (game_ended, end_state)
        """
        if self.game_end_state:
            return True, self.game_end_state

        self._update_stability_tracker(world)

        defeat = self._check_defeat_conditions(world)
        if defeat:
            self.game_end_state = defeat
            logger.info(f"Game ended: {defeat.reason.value}")
            return True, defeat

        victory = self._check_victory_conditions(world)
        if victory:
            self.game_end_state = victory
            logger.info(f"Victory: {victory.reason.value}")
            return True, victory

        return False, None

    def _update_stability_tracker(self, world):
        """Track stability for coup detection"""
        for country in world.get_countries_list():
            if country.id not in self.stability_tracker:
                self.stability_tracker[country.id] = []
            tracker = self.stability_tracker[country.id]
            tracker.append(country.stability)
            if len(tracker) > 5:
                tracker.pop(0)

    def _check_defeat_conditions(self, world) -> Optional[GameEndState]:
        """Check all defeat conditions"""

        if world.defcon_level <= 0:
            return GameEndState(
                reason=GameEndReason.NUCLEAR_WAR,
                message="Nuclear war has devastated the world.",
                message_fr="La guerre nucleaire a devaste le monde.",
                score=0,
                year=world.year
            )

        for country in world.get_countries_list():
            if country.tier >= 3:
                continue

            if self._check_prolonged_instability(country.id, 10, 3):
                return GameEndState(
                    reason=GameEndReason.COUP_DETAT,
                    message=f"{country.name} fell to a military coup.",
                    message_fr=f"{country.name_fr} est tombe sous un coup d'etat.",
                    score=self._calculate_score(world, country),
                    year=world.year
                )

            if country.economy < 5:
                return GameEndState(
                    reason=GameEndReason.BANKRUPTCY,
                    message=f"{country.name} has collapsed economically.",
                    message_fr=f"{country.name_fr} s'est effondre economiquement.",
                    score=self._calculate_score(world, country),
                    year=world.year
                )

        return None

    def _check_prolonged_instability(self, country_id: str, threshold: int, years: int) -> bool:
        """Check if country below stability threshold for N years"""
        history = self.stability_tracker.get(country_id, [])
        if len(history) < years:
            return False
        return all(s < threshold for s in history[-years:])

    def _check_victory_conditions(self, world) -> Optional[GameEndState]:
        """Check all victory conditions"""

        if world.year >= 2100:
            return GameEndState(
                reason=GameEndReason.TIME_LIMIT,
                message="The simulation has reached year 2100.",
                message_fr="La simulation a atteint l'annee 2100.",
                score=self._calculate_final_score(world),
                year=world.year
            )

        dominator = self._check_domination(world)
        if dominator:
            return GameEndState(
                reason=GameEndReason.DOMINATION,
                message=f"{dominator.name} achieved global domination.",
                message_fr=f"{dominator.name_fr} a atteint la domination mondiale.",
                score=self._calculate_final_score(world),
                winner=dominator.id,
                year=world.year
            )

        econ_winner = self._check_economic_victory(world)
        if econ_winner:
            return GameEndState(
                reason=GameEndReason.ECONOMIC_VICTORY,
                message=f"{econ_winner.name} achieved economic hegemony.",
                message_fr=f"{econ_winner.name_fr} a atteint l'hegemonie economique.",
                score=self._calculate_final_score(world),
                winner=econ_winner.id,
                year=world.year
            )

        return None

    def _check_domination(self, world):
        """Check if any power has 60%+ global influence"""
        total = sum(c.soft_power + len(c.sphere_of_influence) * 5
                   for c in world.get_countries_list())
        if total == 0:
            return None
        for country in world.get_countries_list():
            influence = country.soft_power + len(country.sphere_of_influence) * 5
            if influence / total >= 0.60:
                return country
        return None

    def _check_economic_victory(self, world):
        """Check if any power has 40%+ of world GDP"""
        total = sum(c.economy for c in world.get_countries_list())
        if total == 0:
            return None
        for country in world.get_countries_list():
            if country.economy / total >= 0.40:
                return country
        return None

    def _calculate_score(self, world, country) -> int:
        """Calculate score for a country"""
        return int(
            country.economy * 10 + country.military * 8 +
            country.technology * 12 + country.stability * 5 +
            country.soft_power * 7 + len(country.sphere_of_influence) * 20 +
            (world.year - 2024) * 50
        )

    def _calculate_final_score(self, world) -> int:
        """Calculate overall final score"""
        return sum(self._calculate_score(world, c)
                  for c in world.get_countries_list() if c.tier <= 2)


# Global instance
victory_manager = VictoryManager()
