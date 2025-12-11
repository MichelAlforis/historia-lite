"""Stats history tracking for Historia Lite"""
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field, asdict
from collections import defaultdict

logger = logging.getLogger(__name__)

# Maximum history points to keep (24 months = 2 years)
MAX_HISTORY_POINTS = 24


@dataclass
class StatsSnapshot:
    """A snapshot of country stats at a point in time"""
    year: int
    month: int
    economy: int
    military: int
    technology: int
    stability: int
    soft_power: int
    population: int
    nuclear: int
    resources: int

    @property
    def date(self) -> str:
        """Return formatted date string"""
        month_names = ['Jan', 'Fev', 'Mar', 'Avr', 'Mai', 'Juin',
                       'Juil', 'Aout', 'Sep', 'Oct', 'Nov', 'Dec']
        month_name = month_names[self.month - 1] if 1 <= self.month <= 12 else str(self.month)
        return f"{month_name} {self.year}"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        d = asdict(self)
        d['date'] = self.date
        return d


@dataclass
class WorldStatsSnapshot:
    """A snapshot of world stats at a point in time"""
    year: int
    month: int
    global_tension: int
    defcon_level: int
    player_reputation: int
    active_wars: int
    oil_price: float

    @property
    def date(self) -> str:
        """Return formatted date string"""
        month_names = ['Jan', 'Fev', 'Mar', 'Avr', 'Mai', 'Juin',
                       'Juil', 'Aout', 'Sep', 'Oct', 'Nov', 'Dec']
        month_name = month_names[self.month - 1] if 1 <= self.month <= 12 else str(self.month)
        return f"{month_name} {self.year}"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        d = asdict(self)
        d['date'] = self.date
        return d


class StatsHistoryManager:
    """Manages historical stats for countries and world"""

    def __init__(self):
        self.country_history: Dict[str, List[StatsSnapshot]] = defaultdict(list)
        self.world_history: List[WorldStatsSnapshot] = []

    def record_country_stats(self, country_id: str, country: Any, year: int, month: int) -> None:
        """Record current stats for a country"""
        snapshot = StatsSnapshot(
            year=year,
            month=month,
            economy=country.economy,
            military=country.military,
            technology=country.technology,
            stability=country.stability,
            soft_power=country.soft_power,
            population=country.population,
            nuclear=country.nuclear,
            resources=country.resources
        )

        history = self.country_history[country_id]
        history.append(snapshot)

        # Trim to max history
        if len(history) > MAX_HISTORY_POINTS:
            self.country_history[country_id] = history[-MAX_HISTORY_POINTS:]

    def record_world_stats(self, world: Any) -> None:
        """Record current world stats"""
        snapshot = WorldStatsSnapshot(
            year=world.year,
            month=world.month,
            global_tension=world.global_tension,
            defcon_level=world.defcon_level,
            player_reputation=world.player_reputation,
            active_wars=len(world.active_conflicts),
            oil_price=world.oil_price
        )

        self.world_history.append(snapshot)

        # Trim to max history
        if len(self.world_history) > MAX_HISTORY_POINTS:
            self.world_history = self.world_history[-MAX_HISTORY_POINTS:]

    def record_all(self, world: Any) -> None:
        """Record stats for world and all countries"""
        self.record_world_stats(world)

        for country_id, country in world.countries.items():
            self.record_country_stats(country_id, country, world.year, world.month)

        logger.debug(f"Recorded stats for {len(world.countries)} countries at {world.month}/{world.year}")

    def get_country_history(self, country_id: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get historical stats for a country"""
        history = self.country_history.get(country_id, [])
        if limit:
            history = history[-limit:]
        return [s.to_dict() for s in history]

    def get_world_history(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get historical world stats"""
        history = self.world_history
        if limit:
            history = history[-limit:]
        return [s.to_dict() for s in history]

    def get_combined_history(self, country_id: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get combined country + world stats history"""
        country_hist = self.country_history.get(country_id, [])
        world_hist = self.world_history

        if limit:
            country_hist = country_hist[-limit:]
            world_hist = world_hist[-limit:]

        # Combine by date
        result = []
        for i, cs in enumerate(country_hist):
            data = cs.to_dict()
            # Add world stats if available
            if i < len(world_hist):
                ws = world_hist[i]
                data['global_tension'] = ws.global_tension
                data['reputation'] = ws.player_reputation
                data['defcon_level'] = ws.defcon_level
            result.append(data)

        return result

    def reset(self) -> None:
        """Clear all history"""
        self.country_history.clear()
        self.world_history.clear()
        logger.info("Stats history cleared")


# Global instance
stats_history = StatsHistoryManager()
