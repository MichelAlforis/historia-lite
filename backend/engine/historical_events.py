"""Historical events system for Historia Lite - Timeline integrated"""
import json
import logging
import random
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from .events import Event, EventEffect
from .world import World, GameDate

logger = logging.getLogger(__name__)


class HistoricalEventDefinition(BaseModel):
    """Definition of a historical event from JSON"""
    id: str
    year_trigger: int
    month_trigger: int = 1  # Default to January if not specified
    day_trigger: int = 0    # 0 = random day in month
    type: str = "political"
    title: str
    title_fr: str
    description: str
    description_fr: str
    probability: int = 100  # Percentage chance of triggering
    effects: Dict[str, Any] = Field(default_factory=dict)
    conditions: Dict[str, Any] = Field(default_factory=dict)
    tags: List[str] = Field(default_factory=list)
    chain_next: Optional[str] = None  # ID of next event in chain


class EventChain(BaseModel):
    """Definition of an event chain"""
    id: str
    name: str
    name_fr: str
    events: List[str]  # List of event IDs in order
    chain_effects: Dict[str, Any] = Field(default_factory=dict)


class HistoricalEventsManager:
    """Manages historical scripted events with timeline integration"""

    def __init__(self, data_dir: Optional[Path] = None):
        self.triggered_events: set = set()
        self.events: List[HistoricalEventDefinition] = []
        self.chains: List[EventChain] = []
        self._data_dir = data_dir or Path(__file__).parent.parent / "data"
        self._load_events()

    def _load_events(self) -> None:
        """Load historical events from JSON file"""
        events_file = self._data_dir / "historical_events.json"
        if not events_file.exists():
            logger.warning(f"Historical events file not found: {events_file}")
            return

        try:
            with open(events_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Load events
            for event_data in data.get("events", []):
                try:
                    event = HistoricalEventDefinition(**event_data)
                    self.events.append(event)
                except Exception as e:
                    logger.warning(f"Failed to load event {event_data.get('id')}: {e}")

            # Load chains
            for chain_data in data.get("event_chains", []):
                try:
                    chain = EventChain(**chain_data)
                    self.chains.append(chain)
                except Exception as e:
                    logger.warning(f"Failed to load chain {chain_data.get('id')}: {e}")

            logger.info(f"Loaded {len(self.events)} historical events and {len(self.chains)} chains")

        except Exception as e:
            logger.error(f"Failed to load historical events: {e}")

    def check_events(self, world: World) -> List[Event]:
        """Check and trigger historical events for current month/year"""
        triggered = []

        for event_def in self.events:
            # Skip already triggered
            if event_def.id in self.triggered_events:
                continue

            # Check year match
            if event_def.year_trigger != world.year:
                continue

            # Check month match (0 = any month, or specific month)
            if event_def.month_trigger != 0 and event_def.month_trigger != world.month:
                continue

            # Check conditions
            if not self._check_conditions(event_def, world):
                continue

            # Check probability
            if random.randint(1, 100) > event_def.probability:
                logger.debug(f"Historical event {event_def.id} failed probability check")
                continue

            # Trigger event
            event = self._create_event(event_def, world)
            triggered.append(event)
            self.triggered_events.add(event_def.id)
            logger.info(f"Triggered historical event: {event_def.id}")

            # Apply effects
            self._apply_effects(event_def, world)

        # Check chains
        self._check_chains(world)

        return triggered

    def _check_conditions(self, event_def: HistoricalEventDefinition, world: World) -> bool:
        """Check if event conditions are met"""
        conditions = event_def.conditions

        # Check minimum global tension
        if "min_global_tension" in conditions:
            if world.global_tension < conditions["min_global_tension"]:
                return False

        # Check maximum global tension
        if "max_global_tension" in conditions:
            if world.global_tension > conditions["max_global_tension"]:
                return False

        # Check if countries are at war
        if "countries_at_war" in conditions:
            required_countries = set(conditions["countries_at_war"])
            at_war = False
            for conflict in world.active_conflicts:
                belligerents = set(conflict.attackers + conflict.defenders)
                if required_countries.issubset(belligerents):
                    at_war = True
                    break
            if not at_war:
                return False

        # Check if country exists
        if "country_exists" in conditions:
            country_id = conditions["country_exists"]
            if country_id not in world.countries:
                return False

        # Check country stats
        if "country_stat" in conditions:
            stat_cond = conditions["country_stat"]
            country = world.get_country(stat_cond.get("country"))
            if country:
                stat_name = stat_cond.get("stat")
                min_val = stat_cond.get("min", 0)
                max_val = stat_cond.get("max", 100)
                current = getattr(country, stat_name, 50)
                if current < min_val or current > max_val:
                    return False

        return True

    def _create_event(self, event_def: HistoricalEventDefinition, world: World) -> Event:
        """Create a game Event from historical event definition"""
        # Determine the day
        day = event_def.day_trigger
        if day == 0:
            day = random.randint(1, 28)

        # Find primary affected country
        country_id = None
        effects_list = []

        country_effects = event_def.effects.get("countries", {})
        if country_effects:
            # Primary country is first one listed
            country_id = list(country_effects.keys())[0]

            # Build effects list
            for cid, changes in country_effects.items():
                for stat, delta in changes.items():
                    if stat != "relations":  # Handle relations separately
                        effects_list.append(EventEffect(
                            stat=stat,
                            delta=delta if isinstance(delta, int) else 0
                        ))

        return Event(
            id=f"hist_{event_def.id}_{world.year}_{world.month}",
            year=world.year,
            type=event_def.type,
            title=event_def.title,
            title_fr=event_def.title_fr,
            description=event_def.description,
            description_fr=event_def.description_fr,
            country_id=country_id,
            effects=effects_list
        )

    def _apply_effects(self, event_def: HistoricalEventDefinition, world: World) -> None:
        """Apply event effects to world state"""
        effects = event_def.effects

        # Apply country effects
        country_effects = effects.get("countries", {})
        for country_id, changes in country_effects.items():
            country = world.get_country(country_id)
            if not country:
                continue

            for stat, delta in changes.items():
                if stat == "relations":
                    # Handle relation changes
                    for other_id, rel_delta in delta.items():
                        country.modify_relation(other_id, rel_delta)
                else:
                    # Handle stat changes
                    current = getattr(country, stat, None)
                    if current is not None and isinstance(delta, (int, float)):
                        new_value = max(0, min(100, current + delta))
                        setattr(country, stat, new_value)
                        logger.debug(f"Historical event {event_def.id}: {country_id}.{stat} += {delta}")

        # Apply global tension change
        if "global_tension" in effects:
            delta = effects["global_tension"]
            world.global_tension = max(0, min(100, world.global_tension + delta))
            logger.debug(f"Historical event {event_def.id}: global_tension += {delta}")

        # Apply DEFCON change
        if "defcon_change" in effects:
            delta = effects["defcon_change"]
            world.defcon_level = max(1, min(5, world.defcon_level + delta))
            logger.debug(f"Historical event {event_def.id}: defcon_level += {delta}")

    def _check_chains(self, world: World) -> None:
        """Check and apply event chain effects"""
        for chain in self.chains:
            # Check if all events in chain have triggered
            all_triggered = all(eid in self.triggered_events for eid in chain.events)

            if all_triggered and chain.id not in self.triggered_events:
                # Mark chain as processed
                self.triggered_events.add(chain.id)

                # Apply chain effects
                chain_effects = chain.chain_effects.get("if_both_triggered", {})

                if "global_tension" in chain_effects:
                    delta = chain_effects["global_tension"]
                    world.global_tension = max(0, min(100, world.global_tension + delta))
                    logger.info(f"Chain {chain.id} complete: global_tension += {delta}")

                if "defcon_change" in chain_effects:
                    delta = chain_effects["defcon_change"]
                    world.defcon_level = max(1, min(5, world.defcon_level + delta))
                    logger.info(f"Chain {chain.id} complete: defcon_level += {delta}")

    def get_upcoming_events(self, world: World, months_ahead: int = 12) -> List[HistoricalEventDefinition]:
        """Get events scheduled for the next N months"""
        upcoming = []
        current_date = world.current_date

        for event_def in self.events:
            if event_def.id in self.triggered_events:
                continue

            # Calculate event date
            event_year = event_def.year_trigger
            event_month = event_def.month_trigger or 1

            # Check if within range
            event_months = event_year * 12 + event_month
            current_months = current_date.year * 12 + current_date.month
            diff = event_months - current_months

            if 0 < diff <= months_ahead:
                upcoming.append(event_def)

        return sorted(upcoming, key=lambda e: (e.year_trigger, e.month_trigger))

    def get_event_by_id(self, event_id: str) -> Optional[HistoricalEventDefinition]:
        """Get an event definition by ID"""
        for event in self.events:
            if event.id == event_id:
                return event
        return None

    def reset(self) -> None:
        """Reset triggered events for new game"""
        self.triggered_events.clear()
        logger.info("Historical events manager reset")

    def get_triggered_count(self) -> int:
        """Get count of triggered events"""
        return len(self.triggered_events)

    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about historical events"""
        return {
            "total_events": len(self.events),
            "triggered_count": len(self.triggered_events),
            "chains_count": len(self.chains),
            "events_by_year": self._count_by_year(),
            "events_by_type": self._count_by_type()
        }

    def _count_by_year(self) -> Dict[int, int]:
        """Count events by year"""
        counts: Dict[int, int] = {}
        for event in self.events:
            year = event.year_trigger
            counts[year] = counts.get(year, 0) + 1
        return counts

    def _count_by_type(self) -> Dict[str, int]:
        """Count events by type"""
        counts: Dict[str, int] = {}
        for event in self.events:
            etype = event.type
            counts[etype] = counts.get(etype, 0) + 1
        return counts


# Global instance
historical_events_manager = HistoricalEventsManager()
