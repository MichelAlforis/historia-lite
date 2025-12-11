"""Procedural event system for Historia Lite - Phase 17"""
import logging
import random
from typing import Any, Dict, List, Optional, Tuple
from pydantic import BaseModel, Field

from .events import Event, EventEffect

logger = logging.getLogger(__name__)


# Zone definitions for regional events
ZONES = {
    "middle_east": ["SAU", "IRN", "IRQ", "SYR", "ISR", "ARE", "KWT", "QAT", "OMN", "YEM", "JOR", "LBN"],
    "east_asia": ["CHN", "JPN", "KOR", "PRK", "TWN", "MNG"],
    "south_asia": ["IND", "PAK", "BGD", "NPL", "LKA", "AFG"],
    "southeast_asia": ["VNM", "THA", "IDN", "MYS", "PHL", "SGP", "MMR"],
    "eastern_europe": ["UKR", "POL", "ROU", "HUN", "CZE", "SVK", "BGR", "BLR", "MDA"],
    "western_europe": ["DEU", "FRA", "GBR", "ITA", "ESP", "NLD", "BEL", "AUT", "CHE"],
    "africa": ["NGA", "ZAF", "EGY", "ETH", "KEN", "DZA", "MAR", "TUN", "GHA", "CIV"],
    "latin_america": ["BRA", "MEX", "ARG", "COL", "CHL", "PER", "VEN", "CUB"],
    "north_america": ["USA", "CAN", "MEX"],
}

# Oil-dependent countries (simplified)
OIL_DEPENDENT = ["JPN", "KOR", "DEU", "FRA", "ITA", "IND", "CHN", "GBR", "ESP", "TUR"]
OIL_PRODUCERS = ["SAU", "RUS", "USA", "IRN", "IRQ", "ARE", "KWT", "VEN", "NGA", "BRA"]


class ProceduralEventTemplate(BaseModel):
    """Template for procedural events with advanced conditions"""
    id: str
    type: str  # crisis, opportunity, diplomatic, military, economic
    title: str
    title_fr: str
    description: str
    description_fr: str
    probability: float = 0.5  # Higher than random events - these are contextual
    cooldown: int = 3  # Years before same event can trigger again
    effects: List[EventEffect] = Field(default_factory=list)
    severity: str = "normal"  # minor, normal, major, critical


class ProceduralEventGenerator:
    """Generates contextual events based on world state"""

    def __init__(self):
        self.cooldowns: Dict[str, int] = {}  # event_id -> year last triggered
        self.stat_history: Dict[str, List[int]] = {}  # country_id -> [economy values]

    def generate_events(self, world: Any, player_country_id: Optional[str] = None) -> List[Event]:
        """Generate procedural events for this tick"""
        events = []

        # Get player country for player-focused events
        player = None
        if player_country_id:
            player = world.countries.get(player_country_id)
            if not player and hasattr(world, 'get_country'):
                player = world.get_country(player_country_id)

        # Track stat history for trend detection
        self._update_stat_history(world)

        # Generate events by category
        events.extend(self._check_alliance_events(world, player))
        events.extend(self._check_regional_crisis_events(world, player))
        events.extend(self._check_economic_events(world, player))
        events.extend(self._check_political_events(world, player))
        events.extend(self._check_rivalry_events(world, player))
        events.extend(self._check_opportunity_events(world, player))

        return events

    def _is_on_cooldown(self, event_id: str, year: int) -> bool:
        """Check if event is on cooldown"""
        if event_id not in self.cooldowns:
            return False
        return (year - self.cooldowns[event_id]) < 3

    def _set_cooldown(self, event_id: str, year: int) -> None:
        """Set cooldown for event"""
        self.cooldowns[event_id] = year

    def _update_stat_history(self, world: Any) -> None:
        """Track stat history for trend detection"""
        countries = []
        if hasattr(world, 'countries') and isinstance(world.countries, dict):
            countries = list(world.countries.values())
        elif hasattr(world, 'get_countries_list'):
            countries = world.get_countries_list()

        for country in countries:
            key = country.id
            if key not in self.stat_history:
                self.stat_history[key] = []

            economy = getattr(country, 'economy', 50)
            self.stat_history[key].append(economy)

            # Keep only last 5 years
            if len(self.stat_history[key]) > 5:
                self.stat_history[key] = self.stat_history[key][-5:]

    def _get_trend(self, country_id: str) -> str:
        """Get economic trend for country: 'up', 'down', or 'stable'"""
        if country_id not in self.stat_history:
            return "stable"

        history = self.stat_history[country_id]
        if len(history) < 3:
            return "stable"

        # Check last 3 values
        recent = history[-3:]
        if recent[-1] > recent[0] + 10:
            return "up"
        elif recent[-1] < recent[0] - 10:
            return "down"
        return "stable"

    def _check_alliance_events(self, world: Any, player: Any) -> List[Event]:
        """Check for alliance-related events"""
        events = []
        if not player:
            return events

        year = getattr(world, 'year', 2025)
        allies = getattr(player, 'allies', []) or []
        at_war = getattr(player, 'at_war', []) or []

        # Check if any ally is at war
        for ally_id in allies:
            ally = self._get_country(world, ally_id)
            if not ally:
                continue

            ally_at_war = getattr(ally, 'at_war', []) or []
            for enemy_id in ally_at_war:
                if enemy_id in at_war:
                    continue  # Already at war with them

                event_id = f"ally_under_attack_{ally_id}"
                if self._is_on_cooldown(event_id, year):
                    continue

                enemy = self._get_country(world, enemy_id)
                enemy_name = getattr(enemy, 'name_fr', enemy_id) if enemy else enemy_id
                ally_name = getattr(ally, 'name_fr', ally_id)

                if random.random() < 0.7:  # 70% chance when conditions met
                    events.append(Event(
                        id=f"{event_id}_{year}",
                        year=year,
                        type="diplomatic_crisis",
                        title=f"Ally Under Attack: {ally_name}",
                        title_fr=f"Allie attaque: {ally_name}",
                        description=f"Your ally {ally_name} is under attack by {enemy_name}. They request military support.",
                        description_fr=f"Votre allie {ally_name} est attaque par {enemy_name}. Ils demandent un soutien militaire.",
                        country_id=player.id,
                        target_id=ally_id,
                        effects=[],
                    ))
                    self._set_cooldown(event_id, year)
                    break  # One alliance crisis per tick

        return events

    def _check_regional_crisis_events(self, world: Any, player: Any) -> List[Event]:
        """Check for regional crisis events"""
        events = []
        year = getattr(world, 'year', 2025)
        global_tension = getattr(world, 'global_tension', 50)

        # Middle East oil crisis
        if global_tension > 60:
            event_id = "oil_crisis"
            if not self._is_on_cooldown(event_id, year) and random.random() < 0.3:
                # Affects oil-dependent countries
                if player and player.id in OIL_DEPENDENT:
                    events.append(Event(
                        id=f"{event_id}_{year}",
                        year=year,
                        type="economic_crisis",
                        title="Oil Price Shock",
                        title_fr="Choc petrolier",
                        description="Tensions in the Middle East cause oil prices to spike, affecting your economy.",
                        description_fr="Les tensions au Moyen-Orient font flamber les prix du petrole, affectant votre economie.",
                        country_id=player.id if player else None,
                        effects=[
                            EventEffect(stat="economy", delta=-8),
                        ],
                    ))
                    self._set_cooldown(event_id, year)

        # Regional instability check
        for zone_name, zone_countries in ZONES.items():
            avg_stability = self._get_zone_avg_stability(world, zone_countries)
            if avg_stability < 35:
                event_id = f"regional_instability_{zone_name}"
                if not self._is_on_cooldown(event_id, year) and random.random() < 0.4:
                    zone_name_fr = {
                        "middle_east": "Moyen-Orient",
                        "east_asia": "Asie de l'Est",
                        "south_asia": "Asie du Sud",
                        "southeast_asia": "Asie du Sud-Est",
                        "eastern_europe": "Europe de l'Est",
                        "western_europe": "Europe de l'Ouest",
                        "africa": "Afrique",
                        "latin_america": "Amerique latine",
                        "north_america": "Amerique du Nord",
                    }.get(zone_name, zone_name)

                    events.append(Event(
                        id=f"{event_id}_{year}",
                        year=year,
                        type="crisis",
                        title=f"Regional Instability: {zone_name.replace('_', ' ').title()}",
                        title_fr=f"Instabilite regionale: {zone_name_fr}",
                        description=f"The {zone_name.replace('_', ' ')} region faces widespread instability.",
                        description_fr=f"La region {zone_name_fr} fait face a une instabilite generalisee.",
                        country_id=None,
                        effects=[],
                    ))
                    self._set_cooldown(event_id, year)

        return events

    def _check_economic_events(self, world: Any, player: Any) -> List[Event]:
        """Check for economic events based on trends"""
        events = []
        if not player:
            return events

        year = getattr(world, 'year', 2025)
        trend = self._get_trend(player.id)
        economy = getattr(player, 'economy', 50)

        # Economic boom after sustained growth
        if trend == "up" and economy > 70:
            event_id = "economic_boom"
            if not self._is_on_cooldown(event_id, year) and random.random() < 0.5:
                events.append(Event(
                    id=f"{event_id}_{year}_{player.id}",
                    year=year,
                    type="positive",
                    title="Economic Boom",
                    title_fr="Boom economique",
                    description="Your sustained economic growth has attracted foreign investment.",
                    description_fr="Votre croissance economique soutenue attire les investissements etrangers.",
                    country_id=player.id,
                    effects=[
                        EventEffect(stat="economy", delta=5),
                        EventEffect(stat="soft_power", delta=5),
                    ],
                ))
                self._set_cooldown(event_id, year)

        # Recession warning after sustained decline
        elif trend == "down" and economy < 50:
            event_id = "recession_warning"
            if not self._is_on_cooldown(event_id, year) and random.random() < 0.6:
                events.append(Event(
                    id=f"{event_id}_{year}_{player.id}",
                    year=year,
                    type="crisis",
                    title="Recession Warning",
                    title_fr="Alerte recession",
                    description="Economic indicators point to an impending recession.",
                    description_fr="Les indicateurs economiques annoncent une recession imminente.",
                    country_id=player.id,
                    effects=[
                        EventEffect(stat="stability", delta=-5),
                    ],
                ))
                self._set_cooldown(event_id, year)

        return events

    def _check_political_events(self, world: Any, player: Any) -> List[Event]:
        """Check for political events (coups, reforms, etc.)"""
        events = []
        if not player:
            return events

        year = getattr(world, 'year', 2025)
        stability = getattr(player, 'stability', 50)
        military = getattr(player, 'military', 50)

        # Coup risk: low stability + high military
        if stability < 30 and military > 60:
            event_id = "coup_risk"
            if not self._is_on_cooldown(event_id, year) and random.random() < 0.4:
                events.append(Event(
                    id=f"{event_id}_{year}_{player.id}",
                    year=year,
                    type="political_crisis",
                    title="Military Unrest",
                    title_fr="Agitation militaire",
                    description="Senior military officers are rumored to be plotting against the government.",
                    description_fr="Des officiers superieurs comploteraient contre le gouvernement.",
                    country_id=player.id,
                    effects=[
                        EventEffect(stat="stability", delta=-10),
                    ],
                ))
                self._set_cooldown(event_id, year)

        # Reform movement: moderate stability, high education
        technology = getattr(player, 'technology', 50)
        if 40 < stability < 60 and technology > 60:
            event_id = "reform_movement"
            if not self._is_on_cooldown(event_id, year) and random.random() < 0.3:
                events.append(Event(
                    id=f"{event_id}_{year}_{player.id}",
                    year=year,
                    type="political",
                    title="Reform Movement",
                    title_fr="Mouvement reformiste",
                    description="Citizens demand political and economic reforms.",
                    description_fr="Les citoyens exigent des reformes politiques et economiques.",
                    country_id=player.id,
                    effects=[],  # Player choice would determine effects
                ))
                self._set_cooldown(event_id, year)

        return events

    def _check_rivalry_events(self, world: Any, player: Any) -> List[Event]:
        """Check for rivalry-related events"""
        events = []
        if not player:
            return events

        year = getattr(world, 'year', 2025)
        rivals = getattr(player, 'rivals', []) or []
        player_military = getattr(player, 'military', 50)

        for rival_id in rivals:
            rival = self._get_country(world, rival_id)
            if not rival:
                continue

            rival_military = getattr(rival, 'military', 50)
            rival_name = getattr(rival, 'name_fr', rival_id)

            # Arms race when military levels are close
            if abs(player_military - rival_military) < 15:
                event_id = f"arms_race_{rival_id}"
                if not self._is_on_cooldown(event_id, year) and random.random() < 0.35:
                    events.append(Event(
                        id=f"{event_id}_{year}",
                        year=year,
                        type="military",
                        title=f"Arms Race with {rival_name}",
                        title_fr=f"Course aux armements avec {rival_name}",
                        description=f"Military competition with {rival_name} intensifies.",
                        description_fr=f"La competition militaire avec {rival_name} s'intensifie.",
                        country_id=player.id,
                        target_id=rival_id,
                        effects=[
                            EventEffect(stat="military", delta=5),
                            EventEffect(stat="economy", delta=-3),
                        ],
                    ))
                    self._set_cooldown(event_id, year)
                    break

            # Rival growing stronger
            rival_trend = self._get_trend(rival_id)
            if rival_trend == "up":
                event_id = f"rival_growing_{rival_id}"
                if not self._is_on_cooldown(event_id, year) and random.random() < 0.4:
                    events.append(Event(
                        id=f"{event_id}_{year}",
                        year=year,
                        type="intelligence",
                        title=f"Rival Power Growing",
                        title_fr=f"Puissance rivale en hausse",
                        description=f"Intelligence reports indicate {rival_name} is rapidly strengthening.",
                        description_fr=f"Les renseignements indiquent que {rival_name} se renforce rapidement.",
                        country_id=player.id,
                        target_id=rival_id,
                        effects=[],
                    ))
                    self._set_cooldown(event_id, year)

        return events

    def _check_opportunity_events(self, world: Any, player: Any) -> List[Event]:
        """Check for diplomatic opportunities"""
        events = []
        if not player:
            return events

        year = getattr(world, 'year', 2025)
        relations = getattr(player, 'relations', {}) or {}
        allies = getattr(player, 'allies', []) or []

        # Alliance opportunity: high relation with non-ally
        for country_id, relation_value in relations.items():
            if country_id in allies:
                continue
            if relation_value < 60:
                continue

            country = self._get_country(world, country_id)
            if not country:
                continue

            # Only major powers can propose alliances
            tier = getattr(country, 'tier', 5)
            if tier > 3:
                continue

            event_id = f"alliance_offer_{country_id}"
            if not self._is_on_cooldown(event_id, year) and random.random() < 0.25:
                country_name = getattr(country, 'name_fr', country_id)
                events.append(Event(
                    id=f"{event_id}_{year}",
                    year=year,
                    type="diplomatic_opportunity",
                    title=f"Alliance Proposal from {country_name}",
                    title_fr=f"Proposition d'alliance de {country_name}",
                    description=f"{country_name} proposes formalizing your good relations into an alliance.",
                    description_fr=f"{country_name} propose de formaliser vos bonnes relations en alliance.",
                    country_id=player.id,
                    target_id=country_id,
                    effects=[],  # Would be a dilemma with choices
                ))
                self._set_cooldown(event_id, year)
                break  # One opportunity per tick

        # Diplomatic scandal (random for high soft power countries)
        soft_power = getattr(player, 'soft_power', 50)
        if soft_power > 60:
            event_id = "diplomatic_scandal"
            if not self._is_on_cooldown(event_id, year) and random.random() < 0.15:
                events.append(Event(
                    id=f"{event_id}_{year}_{player.id}",
                    year=year,
                    type="scandal",
                    title="Diplomatic Scandal",
                    title_fr="Scandale diplomatique",
                    description="A diplomatic incident threatens your international reputation.",
                    description_fr="Un incident diplomatique menace votre reputation internationale.",
                    country_id=player.id,
                    effects=[
                        EventEffect(stat="soft_power", delta=-10),
                    ],
                ))
                self._set_cooldown(event_id, year)

        return events

    def _get_country(self, world: Any, country_id: str) -> Any:
        """Get country from world by ID"""
        if hasattr(world, 'countries') and isinstance(world.countries, dict):
            return world.countries.get(country_id)
        elif hasattr(world, 'get_country'):
            return world.get_country(country_id)
        return None

    def _get_zone_avg_stability(self, world: Any, zone_countries: List[str]) -> float:
        """Calculate average stability for a zone"""
        total = 0
        count = 0
        for country_id in zone_countries:
            country = self._get_country(world, country_id)
            if country:
                total += getattr(country, 'stability', 50)
                count += 1
        return total / count if count > 0 else 50


# Global instance
procedural_generator = ProceduralEventGenerator()
