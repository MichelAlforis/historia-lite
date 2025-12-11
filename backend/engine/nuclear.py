"""Nuclear escalation system for Historia Lite - DEFCON mechanics"""
import logging
import random
from typing import List, Tuple, Optional
from enum import IntEnum
from pydantic import BaseModel, Field

from .world import World
from .country import Country
from .events import Event

logger = logging.getLogger(__name__)


class DefconLevel(IntEnum):
    """DEFCON levels - lower is more dangerous"""
    PEACE = 5          # Normal peacetime
    ELEVATED = 4       # Increased readiness
    HIGH_ALERT = 3     # Air Force ready in 15 minutes
    CRITICAL = 2       # Armed forces ready for combat
    IMMINENT = 1       # Nuclear war imminent
    NUCLEAR_WAR = 0    # Nuclear exchange has occurred


# DEFCON thresholds for various actions
DEFCON_TRIGGERS = {
    "nuclear_test": -0.3,           # Testing nukes raises tension
    "nuclear_threat": -0.5,         # Threatening nuclear use
    "nuclear_buildup": -0.2,        # Increasing arsenal
    "nuclear_war_between_powers": -2.0,  # War between nuclear powers
    "peace_treaty": +0.3,           # Peace agreements
    "arms_reduction": +0.5,         # Reducing nuclear arsenal
    "diplomatic_summit": +0.2,      # High-level talks
    "conflict_ended": +0.2,         # End of conventional war
    "alliance_formed": +0.1,        # Defensive alliance
}


class NuclearStrike(BaseModel):
    """Represents a nuclear strike"""
    attacker_id: str
    target_id: str
    warheads: int
    year: int
    retaliation: bool = False


class NuclearManager:
    """Manages nuclear escalation and DEFCON system"""

    def __init__(self):
        self.defcon_level: float = 5.0  # Use float for gradual changes
        self.nuclear_strikes: List[NuclearStrike] = []
        self.tensions: dict[str, float] = {}  # Per-country pair tensions

    def get_defcon(self) -> int:
        """Get current DEFCON level as integer"""
        return max(0, min(5, int(self.defcon_level)))

    def update_defcon(self, world: World) -> List[Event]:
        """
        Update DEFCON level based on world state.
        Called each tick.
        """
        events = []

        # Calculate tension factors
        tension_delta = 0.0

        # Wars between nuclear powers are VERY dangerous
        for conflict in world.active_conflicts:
            nuclear_attackers = [
                aid for aid in conflict.attackers
                if world.get_country(aid) and world.get_country(aid).nuclear > 0
            ]
            nuclear_defenders = [
                did for did in conflict.defenders
                if world.get_country(did) and world.get_country(did).nuclear > 0
            ]

            if nuclear_attackers and nuclear_defenders:
                # Nuclear powers at war!
                tension_delta -= 0.5  # Massive escalation
                events.append(self._create_tension_event(
                    world.year,
                    "Nuclear powers at war",
                    "Puissances nucleaires en guerre",
                    f"War between nuclear powers dramatically increases the risk of nuclear exchange.",
                    f"La guerre entre puissances nucleaires augmente dramatiquement le risque d'echange nucleaire.",
                    "extreme"
                ))

        # Global tension affects DEFCON
        if world.global_tension > 80:
            tension_delta -= 0.2
        elif world.global_tension > 60:
            tension_delta -= 0.1
        elif world.global_tension < 30:
            tension_delta += 0.1

        # Active conflicts increase tension
        tension_delta -= len(world.active_conflicts) * 0.05

        # Natural de-escalation in peacetime
        if not world.active_conflicts and world.global_tension < 40:
            tension_delta += 0.15

        # Apply changes with bounds
        old_level = self.get_defcon()
        self.defcon_level = max(0.0, min(5.0, self.defcon_level + tension_delta))
        new_level = self.get_defcon()

        # Create event if DEFCON level changed
        if new_level != old_level:
            if new_level < old_level:
                events.append(self._create_defcon_change_event(world.year, new_level, "up"))
            else:
                events.append(self._create_defcon_change_event(world.year, new_level, "down"))

        # Update world state
        world.defcon_level = new_level

        # Check for nuclear war trigger
        if new_level <= 1:
            war_events = self._check_nuclear_war_trigger(world)
            events.extend(war_events)

        return events

    def trigger_event(self, event_type: str, world: World) -> List[Event]:
        """Trigger a specific nuclear-related event"""
        events = []

        delta = DEFCON_TRIGGERS.get(event_type, 0)
        if delta != 0:
            old_level = self.get_defcon()
            self.defcon_level = max(0.0, min(5.0, self.defcon_level + delta))
            new_level = self.get_defcon()
            world.defcon_level = new_level

            if new_level != old_level:
                direction = "up" if new_level < old_level else "down"
                events.append(self._create_defcon_change_event(world.year, new_level, direction))

        return events

    def _check_nuclear_war_trigger(self, world: World) -> List[Event]:
        """Check if conditions trigger nuclear war"""
        events = []

        # At DEFCON 1, there's a chance of nuclear exchange each tick
        if self.get_defcon() == 1:
            # Find conflicts between nuclear powers
            for conflict in world.active_conflicts:
                attackers_nuclear = [
                    world.get_country(aid) for aid in conflict.attackers
                    if world.get_country(aid) and world.get_country(aid).nuclear > 20
                ]
                defenders_nuclear = [
                    world.get_country(did) for did in conflict.defenders
                    if world.get_country(did) and world.get_country(did).nuclear > 20
                ]

                if attackers_nuclear and defenders_nuclear:
                    # 10% chance per tick at DEFCON 1 with nuclear powers at war
                    if random.random() < 0.10:
                        # Nuclear war begins
                        attacker = attackers_nuclear[0]
                        defender = defenders_nuclear[0]

                        events.extend(self._execute_nuclear_war(attacker, defender, world))

        return events

    def _execute_nuclear_war(
        self, attacker: Country, defender: Country, world: World
    ) -> List[Event]:
        """Execute nuclear war - catastrophic consequences"""
        events = []

        # First strike
        strike = NuclearStrike(
            attacker_id=attacker.id,
            target_id=defender.id,
            warheads=attacker.nuclear,
            year=world.year,
            retaliation=False
        )
        self.nuclear_strikes.append(strike)

        events.append(Event(
            id=f"nuclear_strike_{world.year}_{attacker.id}_{defender.id}",
            year=world.year,
            type="nuclear",
            title=f"NUCLEAR STRIKE: {attacker.name} attacks {defender.name}",
            title_fr=f"FRAPPE NUCLEAIRE: {attacker.name_fr} attaque {defender.name_fr}",
            description=f"{attacker.name} has launched a nuclear strike against {defender.name}. "
                       f"{attacker.nuclear} warheads have been deployed.",
            description_fr=f"{attacker.name_fr} a lance une frappe nucleaire contre {defender.name_fr}. "
                          f"{attacker.nuclear} ogives ont ete deployees.",
            country_id=attacker.id,
            target_id=defender.id,
            severity="catastrophic"
        ))

        # Massive damage to defender
        defender.economy = max(0, defender.economy - 60)
        defender.stability = max(0, defender.stability - 50)
        defender.population = max(0, defender.population - 40)
        defender.military = max(0, defender.military - 30)

        # Retaliation if defender has nukes
        if defender.nuclear > 10:
            retaliation = NuclearStrike(
                attacker_id=defender.id,
                target_id=attacker.id,
                warheads=defender.nuclear,
                year=world.year,
                retaliation=True
            )
            self.nuclear_strikes.append(retaliation)

            events.append(Event(
                id=f"nuclear_retaliation_{world.year}_{defender.id}_{attacker.id}",
                year=world.year,
                type="nuclear",
                title=f"NUCLEAR RETALIATION: {defender.name} strikes back",
                title_fr=f"REPRESAILLES NUCLEAIRES: {defender.name_fr} contre-attaque",
                description=f"{defender.name} has launched a retaliatory nuclear strike. "
                           f"Mutually Assured Destruction is underway.",
                description_fr=f"{defender.name_fr} a lance une frappe nucleaire de represailles. "
                              f"La destruction mutuelle assuree est en cours.",
                country_id=defender.id,
                target_id=attacker.id,
                severity="catastrophic"
            ))

            # Damage to attacker
            attacker.economy = max(0, attacker.economy - 60)
            attacker.stability = max(0, attacker.stability - 50)
            attacker.population = max(0, attacker.population - 40)
            attacker.military = max(0, attacker.military - 30)

        # Global effects - nuclear winter
        world.global_tension = 100
        self.defcon_level = 0  # Game essentially over
        world.defcon_level = 0

        # All countries affected by nuclear winter
        for country in world.countries.values():
            if country.id not in [attacker.id, defender.id]:
                country.economy = max(0, country.economy - 20)
                country.stability = max(0, country.stability - 15)

        events.append(Event(
            id=f"nuclear_winter_{world.year}",
            year=world.year,
            type="nuclear",
            title="NUCLEAR WINTER BEGINS",
            title_fr="L'HIVER NUCLEAIRE COMMENCE",
            description="Global nuclear exchange has triggered nuclear winter. "
                       "Civilization as we know it has ended.",
            description_fr="L'echange nucleaire mondial a declenche l'hiver nucleaire. "
                          "La civilisation telle que nous la connaissons a pris fin.",
            severity="apocalyptic"
        ))

        return events

    def attempt_first_strike(
        self, attacker: Country, defender: Country, world: World
    ) -> Tuple[bool, List[Event]]:
        """
        Attempt a deliberate first strike.
        This is a player action with severe consequences.
        """
        events = []

        if attacker.nuclear < 10:
            return False, [Event(
                id=f"nuclear_failed_{world.year}_{attacker.id}",
                year=world.year,
                type="info",
                title="Insufficient Nuclear Arsenal",
                title_fr="Arsenal nucleaire insuffisant",
                description=f"{attacker.name} lacks sufficient nuclear weapons for a strike.",
                description_fr=f"{attacker.name_fr} n'a pas assez d'armes nucleaires pour une frappe.",
                country_id=attacker.id
            )]

        # This action triggers immediate DEFCON 0
        self.defcon_level = 0
        world.defcon_level = 0

        # Global condemnation
        for country in world.countries.values():
            if country.id != attacker.id:
                attacker.modify_relation(country.id, -100)

        # Execute the strike
        events.extend(self._execute_nuclear_war(attacker, defender, world))

        return True, events

    def propose_arms_reduction(
        self, country1: Country, country2: Country, world: World, reduction_percent: int = 20
    ) -> List[Event]:
        """
        Propose nuclear arms reduction between two powers.
        Improves DEFCON and relations.
        """
        events = []

        # Reduce arsenals
        reduction1 = int(country1.nuclear * reduction_percent / 100)
        reduction2 = int(country2.nuclear * reduction_percent / 100)

        country1.nuclear = max(0, country1.nuclear - reduction1)
        country2.nuclear = max(0, country2.nuclear - reduction2)

        # Improve relations
        country1.modify_relation(country2.id, 25)
        country2.modify_relation(country1.id, 25)

        # Improve DEFCON
        self.defcon_level = min(5.0, self.defcon_level + 0.5)
        world.defcon_level = self.get_defcon()
        world.global_tension = max(0, world.global_tension - 10)

        events.append(Event(
            id=f"arms_reduction_{world.year}_{country1.id}_{country2.id}",
            year=world.year,
            type="diplomatic",
            title=f"Nuclear Arms Reduction Treaty",
            title_fr=f"Traite de reduction des armes nucleaires",
            description=f"{country1.name} and {country2.name} have agreed to reduce their nuclear arsenals by {reduction_percent}%.",
            description_fr=f"{country1.name_fr} et {country2.name_fr} ont accepte de reduire leurs arsenaux nucleaires de {reduction_percent}%.",
            country_id=country1.id,
            target_id=country2.id,
            severity="positive"
        ))

        # Check if DEFCON improved
        if self.get_defcon() > world.defcon_level:
            events.append(self._create_defcon_change_event(world.year, self.get_defcon(), "down"))

        return events

    def _create_defcon_change_event(self, year: int, level: int, direction: str) -> Event:
        """Create event for DEFCON level change"""
        level_names = {
            5: ("DEFCON 5 - PEACE", "DEFCON 5 - PAIX"),
            4: ("DEFCON 4 - ELEVATED", "DEFCON 4 - ELEVE"),
            3: ("DEFCON 3 - HIGH ALERT", "DEFCON 3 - ALERTE HAUTE"),
            2: ("DEFCON 2 - CRITICAL", "DEFCON 2 - CRITIQUE"),
            1: ("DEFCON 1 - IMMINENT", "DEFCON 1 - IMMINENT"),
            0: ("DEFCON 0 - NUCLEAR WAR", "DEFCON 0 - GUERRE NUCLEAIRE"),
        }

        name_en, name_fr = level_names.get(level, (f"DEFCON {level}", f"DEFCON {level}"))

        if direction == "up":
            desc_en = f"Global nuclear threat has INCREASED. Status now: {name_en}"
            desc_fr = f"La menace nucleaire mondiale a AUGMENTE. Statut actuel: {name_fr}"
            severity = "high" if level <= 2 else "medium"
        else:
            desc_en = f"Global nuclear threat has decreased. Status now: {name_en}"
            desc_fr = f"La menace nucleaire mondiale a diminue. Statut actuel: {name_fr}"
            severity = "positive"

        return Event(
            id=f"defcon_change_{year}_{level}",
            year=year,
            type="nuclear",
            title=name_en,
            title_fr=name_fr,
            description=desc_en,
            description_fr=desc_fr,
            severity=severity
        )

    def _create_tension_event(
        self, year: int, title: str, title_fr: str, desc: str, desc_fr: str, severity: str
    ) -> Event:
        """Create a nuclear tension event"""
        return Event(
            id=f"nuclear_tension_{year}_{random.randint(1000, 9999)}",
            year=year,
            type="nuclear",
            title=title,
            title_fr=title_fr,
            description=desc,
            description_fr=desc_fr,
            severity=severity
        )

    def reset(self):
        """Reset nuclear manager state"""
        self.defcon_level = 5.0
        self.nuclear_strikes.clear()
        self.tensions.clear()


# Global instance
nuclear_manager = NuclearManager()
