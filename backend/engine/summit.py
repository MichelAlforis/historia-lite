"""Periodic summits and international events system

Handles:
- Scheduling periodic summits (G7, G20, BRICS, COP, etc.)
- Processing summit events and generating outcomes
- Special events (World Cup, Olympics)
- Summit resolutions and their effects
"""
import json
import logging
import random
from pathlib import Path
from typing import TYPE_CHECKING, Dict, List, Optional

from pydantic import BaseModel, Field

from engine.events import Event

if TYPE_CHECKING:
    from engine.world import World
    from engine.country import Country

logger = logging.getLogger(__name__)


class SummitResolution(BaseModel):
    """A resolution that can be voted on during a summit"""
    id: str
    name_fr: str
    requires_majority: float = 0.5  # 0.5, 0.66, or 1.0 for unanimity
    effects: Dict = Field(default_factory=dict)
    passed: bool = False
    votes_for: List[str] = Field(default_factory=list)
    votes_against: List[str] = Field(default_factory=list)


class SummitType(BaseModel):
    """Template for a type of periodic summit"""
    id: str
    name: str
    name_fr: str
    frequency: str  # annual, biannual, quarterly, every_4_years
    bloc_id: Optional[str] = None
    mandatory_participants: List[str] | str = Field(default_factory=list)  # "all" for everyone
    rotating_host: bool = True
    host_order: List[str] = Field(default_factory=list)
    default_host: Optional[str] = None
    agenda_topics: List[str] = Field(default_factory=list)
    effects: Dict = Field(default_factory=dict)
    can_invite_guests: bool = False
    max_guests: int = 0
    resolutions_possible: List[Dict] = Field(default_factory=list)
    description_fr: str = ""


class SpecialEvent(BaseModel):
    """Template for special events like World Cup, Olympics"""
    id: str
    name: str
    name_fr: str
    frequency: str  # every_4_years, annual
    start_year: Optional[int] = None  # First occurrence (for every_4_years)
    selection_body: Optional[str] = None  # FIFA, IOC
    effects: Dict = Field(default_factory=dict)
    host_requirements: Dict = Field(default_factory=dict)
    location: Optional[str] = None  # Fixed location for events like Nobel
    description_fr: str = ""


class ActiveSummit(BaseModel):
    """An active summit happening this year"""
    id: str
    summit_type_id: str
    year: int
    host_country: str
    participants: List[str] = Field(default_factory=list)
    guests: List[str] = Field(default_factory=list)
    resolutions: List[SummitResolution] = Field(default_factory=list)
    outcomes: List[str] = Field(default_factory=list)
    status: str = "scheduled"  # scheduled, in_progress, concluded


class SummitManager:
    """Manages all periodic summits and special events"""

    def __init__(self):
        self.summit_types: Dict[str, SummitType] = {}
        self.special_events: Dict[str, SpecialEvent] = {}
        self.active_summits: List[ActiveSummit] = []
        self.summit_history: List[ActiveSummit] = []
        self._host_rotation: Dict[str, int] = {}  # summit_type_id -> current host index
        self._load_summit_data()

    def _load_summit_data(self):
        """Load summit types from JSON"""
        data_path = Path(__file__).parent.parent / "data" / "periodic_summits.json"
        if not data_path.exists():
            logger.warning("periodic_summits.json not found")
            return

        with open(data_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        for st_data in data.get("summit_types", []):
            st = SummitType(**st_data)
            self.summit_types[st.id] = st
            self._host_rotation[st.id] = 0

        for se_data in data.get("special_events", []):
            se = SpecialEvent(**se_data)
            self.special_events[se.id] = se

        logger.info(
            f"Loaded {len(self.summit_types)} summit types, "
            f"{len(self.special_events)} special events"
        )

    def get_scheduled_summits(self, year: int) -> List[str]:
        """Get list of summit type IDs scheduled for a given year"""
        scheduled = []

        for st_id, st in self.summit_types.items():
            if self._is_scheduled(st, year):
                scheduled.append(st_id)

        return scheduled

    def _is_scheduled(self, summit_type: SummitType, year: int) -> bool:
        """Check if a summit type should occur in a given year"""
        if summit_type.frequency == "annual":
            return True
        elif summit_type.frequency == "biannual":
            return year % 2 == 0
        elif summit_type.frequency == "quarterly":
            return True  # Happens every year, 4 times
        elif summit_type.frequency == "every_4_years":
            return year % 4 == 0
        return False

    def _get_host(self, summit_type: SummitType, world: "World") -> str:
        """Determine the host country for a summit"""
        if not summit_type.rotating_host:
            return summit_type.default_host or ""

        if summit_type.host_order:
            idx = self._host_rotation.get(summit_type.id, 0)
            host = summit_type.host_order[idx % len(summit_type.host_order)]
            self._host_rotation[summit_type.id] = idx + 1
            return host

        # Random host from participants
        participants = self._get_participants(summit_type, world)
        if participants:
            return random.choice(participants)
        return ""

    def _get_participants(self, summit_type: SummitType, world: "World") -> List[str]:
        """Get list of participants for a summit"""
        if summit_type.mandatory_participants == "all":
            return list(world.countries.keys())

        if isinstance(summit_type.mandatory_participants, list):
            return summit_type.mandatory_participants

        return []

    def create_summit(
        self, summit_type_id: str, year: int, world: "World"
    ) -> Optional[ActiveSummit]:
        """Create a new active summit"""
        st = self.summit_types.get(summit_type_id)
        if not st:
            return None

        host = self._get_host(st, world)
        participants = self._get_participants(st, world)

        summit = ActiveSummit(
            id=f"{summit_type_id}_{year}",
            summit_type_id=summit_type_id,
            year=year,
            host_country=host,
            participants=participants,
            status="scheduled"
        )

        # Add possible resolutions
        for res_data in st.resolutions_possible:
            resolution = SummitResolution(
                id=res_data["id"],
                name_fr=res_data["name_fr"],
                requires_majority=res_data.get("requires_majority", 0.5),
                effects=res_data.get("effects", {})
            )
            summit.resolutions.append(resolution)

        self.active_summits.append(summit)
        logger.info(f"Created summit {summit.id} hosted by {host}")
        return summit

    def process_summit(self, summit: ActiveSummit, world: "World") -> List[Event]:
        """Process a summit and generate events"""
        events = []
        st = self.summit_types.get(summit.summit_type_id)
        if not st:
            return events

        summit.status = "in_progress"

        # Apply base effects
        host = world.get_country(summit.host_country)
        if host and "soft_power_host" in st.effects:
            host.soft_power = min(100, host.soft_power + st.effects["soft_power_host"])

        # Relation bonus between participants
        relation_bonus = st.effects.get("relation_bonus_participants", 0)
        if relation_bonus > 0:
            for i, p1 in enumerate(summit.participants):
                for p2 in summit.participants[i+1:]:
                    c1 = world.get_country(p1)
                    c2 = world.get_country(p2)
                    if c1 and c2:
                        c1.modify_relation(p2, relation_bonus)
                        c2.modify_relation(p1, relation_bonus)

        # Global tension reduction
        tension_reduction = st.effects.get("global_tension_reduction", 0)
        if tension_reduction > 0:
            world.global_tension = max(0, world.global_tension - tension_reduction)

        # Process resolutions (AI votes based on interests)
        for resolution in summit.resolutions:
            self._process_resolution(resolution, summit, world)

            if resolution.passed:
                summit.outcomes.append(f"Resolution adoptee: {resolution.name_fr}")
                # Apply resolution effects
                self._apply_resolution_effects(resolution, summit, world)

        # Create summit event
        event = Event(
            id=summit.id,
            year=world.year,
            type="diplomatic",
            title=f"{st.name}",
            title_fr=f"{st.name_fr}",
            description=f"{st.name} hosted by {summit.host_country}",
            description_fr=f"{st.name_fr} organise par {summit.host_country}. "
                          f"{len([r for r in summit.resolutions if r.passed])} resolution(s) adoptee(s).",
            country_id=summit.host_country
        )
        events.append(event)

        summit.status = "concluded"
        self.summit_history.append(summit)
        self.active_summits.remove(summit)

        return events

    def _process_resolution(
        self, resolution: SummitResolution, summit: ActiveSummit, world: "World"
    ):
        """Process voting on a resolution"""
        for country_id in summit.participants:
            country = world.get_country(country_id)
            if not country:
                continue

            # Simple AI voting logic based on personality and bloc alignment
            vote_probability = 50

            # Diplomacy-oriented countries more likely to vote yes
            if hasattr(country, 'personality') and country.personality:
                vote_probability += (country.personality.diplomacy - 50) // 5

            # Check if resolution affects them negatively
            if "economy_penalty" in resolution.id or "sanction" in resolution.id:
                vote_probability -= 20

            # Same bloc as host = more likely to support
            if country.shares_bloc(world.get_country(summit.host_country)):
                vote_probability += 15

            if random.randint(0, 100) < vote_probability:
                resolution.votes_for.append(country_id)
            else:
                resolution.votes_against.append(country_id)

        # Check if resolution passed
        total_votes = len(resolution.votes_for) + len(resolution.votes_against)
        if total_votes > 0:
            ratio = len(resolution.votes_for) / total_votes
            resolution.passed = ratio >= resolution.requires_majority

    def _apply_resolution_effects(
        self, resolution: SummitResolution, summit: ActiveSummit, world: "World"
    ):
        """Apply the effects of a passed resolution"""
        effects = resolution.effects

        # Global effects
        if "global_stability" in effects:
            # All participants get stability bonus
            for country_id in summit.participants:
                country = world.get_country(country_id)
                if country:
                    country.stability = min(
                        100, country.stability + effects["global_stability"]
                    )

        if "oil_price" in effects:
            world.oil_price = max(0, world.oil_price + effects["oil_price"])

        if "economy_bonus_all" in effects:
            for country_id in summit.participants:
                country = world.get_country(country_id)
                if country:
                    country.economy = min(
                        100, country.economy + effects["economy_bonus_all"]
                    )

    def process_special_events(self, year: int, world: "World") -> List[Event]:
        """Process special events like World Cup, Olympics"""
        events = []

        for se_id, se in self.special_events.items():
            if se.frequency == "every_4_years":
                if se.start_year is None:
                    continue  # Skip if no start year for 4-year event
                if (year - se.start_year) % 4 != 0:
                    continue
            elif se.frequency == "annual":
                pass  # Happens every year
            else:
                continue

            # Determine host (simplified - could be more complex with bidding)
            eligible_hosts = []
            for country_id, country in world.countries.items():
                eligible = True
                for req, value in se.host_requirements.items():
                    if hasattr(country, req) and getattr(country, req) < value:
                        eligible = False
                        break
                if eligible:
                    eligible_hosts.append(country_id)

            if not eligible_hosts:
                continue

            host_id = random.choice(eligible_hosts)
            host = world.get_country(host_id)

            if host:
                # Apply effects
                for effect, value in se.effects.items():
                    if effect == "soft_power_host":
                        host.soft_power = min(100, host.soft_power + value)
                    elif effect == "economy_host":
                        host.economy = min(100, host.economy + value)
                    elif effect == "stability_host":
                        host.stability = min(100, host.stability + value)

                event = Event(
                    id=f"{se_id}_{year}",
                    year=year,
                    type="positive",
                    title=se.name,
                    title_fr=se.name_fr,
                    description=f"{se.name} hosted by {host.name}",
                    description_fr=f"{se.name_fr} organise par {host.name_fr}. "
                                  f"Soft power +{se.effects.get('soft_power_host', 0)}",
                    country_id=host_id
                )
                events.append(event)

        return events

    def get_upcoming_summits(self, year: int, count: int = 5) -> List[Dict]:
        """Get list of upcoming summits for the next few years"""
        upcoming = []
        for y in range(year, year + count):
            for st_id in self.get_scheduled_summits(y):
                st = self.summit_types[st_id]
                upcoming.append({
                    "year": y,
                    "summit_type": st_id,
                    "name_fr": st.name_fr
                })
        return upcoming


# Global instance
summit_manager = SummitManager()
