"""Tick processing for Historia Lite"""
import logging
import random
from typing import List

from .world import World
from .country import Country
from .events import Event, EventPool
from .project import project_manager
from .dilemma import dilemma_manager
from .bloc import BlocManager, apply_bloc_effects
from .summit import SummitManager
from .influence import influence_manager, InfluenceCalculator
from ai.decision_tier4 import process_tier4_countries

logger = logging.getLogger(__name__)

# Global managers (initialized once)
bloc_manager = BlocManager()
summit_manager = SummitManager()


def process_tick(world: World, event_pool: EventPool) -> List[Event]:
    """Process one year of simulation"""
    events: List[Event] = []

    # Set random seed for reproducibility
    random.seed(world.seed + world.year)

    # Phase 1: Economy
    events.extend(_process_economy(world))

    # Phase 2: Technology
    events.extend(_process_technology(world))

    # Phase 3: AI Decisions
    events.extend(_process_ai_decisions(world))

    # Phase 4: Conflicts
    events.extend(_process_conflicts(world))

    # Phase 5: Random Events
    random_events = event_pool.get_random_events(
        world.get_countries_list(), world.year, world.seed
    )
    for event in random_events:
        _apply_event(world, event)
        events.append(event)

    # Phase 6: Influence
    events.extend(_process_influence(world))

    # Phase 7: Relations
    _update_relations(world)

    # Phase 8: Projects
    events.extend(_process_projects(world))

    # Phase 9: Dilemma Detection (for player countries)
    events.extend(_detect_dilemmas(world))

    # Phase 10: Tier 4 Countries (processed every 3 ticks)
    tier4_events = process_tier4_countries(world, world.tier4_tick_counter)
    events.extend(tier4_events)
    world.tier4_tick_counter = (world.tier4_tick_counter + 1) % 3

    # Phase 11: Bloc Economic Bonuses
    events.extend(_process_blocs(world))

    # Phase 12: Periodic Summits
    events.extend(_process_summits(world))

    # Phase 13: Special Events (World Cup, Olympics)
    events.extend(_process_special_events(world))

    # Advance year
    world.year += 1

    # Store events in history
    for event in events:
        world.add_event(event)

    logger.info(f"Tick processed: Year {world.year - 1} -> {world.year}")
    return events


def _process_economy(world: World) -> List[Event]:
    """Phase 1: Economic updates"""
    events = []

    # Oil price fluctuation
    oil_delta = random.randint(-10, 10)
    world.oil_price = max(30, min(150, world.oil_price + oil_delta))

    for country in world.countries.values():
        # Base growth
        growth = 1
        if country.stability > 60:
            growth += 1
        if country.technology > 70:
            growth += 1
        if country.economy < 30:
            growth -= 1  # Struggling economies grow slower

        # Sanctions impact
        sanctioners = [
            c for c in world.countries.values()
            if country.id in c.sanctions_on
        ]
        if sanctioners:
            growth -= 2 * len(sanctioners)

        # Resource-rich countries benefit from high oil
        if country.resources > 70 and world.oil_price > 100:
            growth += 2

        country.economy = max(0, min(100, country.economy + growth))

        # Population growth
        pop_growth = 1 if country.stability > 50 else 0
        country.population = max(0, min(100, country.population + pop_growth))

    return events


def _process_technology(world: World) -> List[Event]:
    """Phase 2: Technology updates"""
    events = []

    for country in world.countries.values():
        tech_growth = 1

        # Economy drives tech
        if country.economy > 70:
            tech_growth += 1

        # Stability helps research
        if country.stability > 60:
            tech_growth += 1

        # Tech transfers from allies
        for ally_id in country.allies:
            ally = world.get_country(ally_id)
            if ally and ally.technology > country.technology + 20:
                tech_growth += 1
                break

        country.technology = max(0, min(100, country.technology + tech_growth))

    return events


def _process_ai_decisions(world: World) -> List[Event]:
    """Phase 3: AI decisions for non-player countries"""
    events = []

    for country in world.countries.values():
        if country.is_player:
            continue

        decision = _make_ai_decision(country, world)
        if decision:
            events.append(decision)

    return events


def _make_ai_decision(country: Country, world: World) -> Event | None:
    """Make AI decision for a country"""
    options = []

    # Option: Develop economy
    if country.economy < 70:
        score = (70 - country.economy) * 0.5
        options.append(("develop_economy", score))

    # Option: Build military
    if country.military < 60:
        score = (60 - country.military) * 0.4
        score *= (country.personality.aggression / 50)
        options.append(("build_military", score))

    # Option: Improve stability
    if country.stability < 50:
        score = (50 - country.stability) * 0.6
        options.append(("improve_stability", score))

    # Option: Expand influence (for major powers)
    if country.tier <= 2:
        score = 30 * (country.personality.expansionism / 50)
        options.append(("expand_influence", score))

    # Option: Impose sanctions on rival
    for rival_id in country.rivals:
        rival = world.get_country(rival_id)
        if rival and rival_id not in country.sanctions_on:
            score = 20 * (country.personality.aggression / 50)
            options.append((f"sanction_{rival_id}", score))

    # Option: Do nothing
    options.append(("idle", 20))

    if not options:
        return None

    # Weighted random choice
    total = sum(score for _, score in options)
    r = random.random() * total
    cumulative = 0
    chosen = "idle"
    for option, score in options:
        cumulative += score
        if r <= cumulative:
            chosen = option
            break

    # Execute decision
    return _execute_decision(country, world, chosen)


def _execute_decision(country: Country, world: World, decision: str) -> Event | None:
    """Execute an AI decision"""
    if decision == "develop_economy":
        country.economy = min(100, country.economy + 3)
        return Event(
            id=f"decision_{world.year}_{country.id}_economy",
            year=world.year,
            type="decision",
            title="Economic Development",
            title_fr="Developpement economique",
            description=f"{country.name} focuses on economic development",
            description_fr=f"{country.name_fr} se concentre sur le developpement economique",
            country_id=country.id,
        )

    elif decision == "build_military":
        country.military = min(100, country.military + 3)
        country.economy = max(0, country.economy - 1)
        return Event(
            id=f"decision_{world.year}_{country.id}_military",
            year=world.year,
            type="decision",
            title="Military Buildup",
            title_fr="Renforcement militaire",
            description=f"{country.name} strengthens its military",
            description_fr=f"{country.name_fr} renforce son armee",
            country_id=country.id,
        )

    elif decision == "improve_stability":
        country.stability = min(100, country.stability + 5)
        return Event(
            id=f"decision_{world.year}_{country.id}_stability",
            year=world.year,
            type="decision",
            title="Stability Measures",
            title_fr="Mesures de stabilite",
            description=f"{country.name} implements stability measures",
            description_fr=f"{country.name_fr} met en place des mesures de stabilite",
            country_id=country.id,
        )

    elif decision == "expand_influence":
        country.soft_power = min(100, country.soft_power + 2)
        return Event(
            id=f"decision_{world.year}_{country.id}_influence",
            year=world.year,
            type="decision",
            title="Influence Expansion",
            title_fr="Expansion d'influence",
            description=f"{country.name} expands its global influence",
            description_fr=f"{country.name_fr} etend son influence mondiale",
            country_id=country.id,
        )

    elif decision.startswith("sanction_"):
        target_id = decision.replace("sanction_", "")
        target = world.get_country(target_id)
        if target and target_id not in country.sanctions_on:
            country.sanctions_on.append(target_id)
            country.modify_relation(target_id, -20)
            target.modify_relation(country.id, -20)
            return Event(
                id=f"decision_{world.year}_{country.id}_sanction_{target_id}",
                year=world.year,
                type="sanctions",
                title="Sanctions Imposed",
                title_fr="Sanctions imposees",
                description=f"{country.name} imposes sanctions on {target.name}",
                description_fr=f"{country.name_fr} impose des sanctions a {target.name_fr}",
                country_id=country.id,
                target_id=target_id,
            )

    return None


def _process_conflicts(world: World) -> List[Event]:
    """Phase 4: Conflict resolution"""
    events = []

    for conflict in world.active_conflicts[:]:
        conflict.duration += 1

        # Simple war exhaustion
        for attacker_id in conflict.attackers:
            attacker = world.get_country(attacker_id)
            if attacker:
                attacker.economy = max(0, attacker.economy - 2)
                attacker.stability = max(0, attacker.stability - 1)

        for defender_id in conflict.defenders:
            defender = world.get_country(defender_id)
            if defender:
                defender.economy = max(0, defender.economy - 3)
                defender.stability = max(0, defender.stability - 2)

        # Check for peace (simplified)
        if conflict.duration >= 3 and random.random() < 0.3:
            world.end_conflict(conflict.id)
            events.append(
                Event(
                    id=f"peace_{world.year}_{conflict.id}",
                    year=world.year,
                    type="peace",
                    title="Peace Agreement",
                    title_fr="Accord de paix",
                    description=f"Peace agreement reached in {conflict.id}",
                    description_fr=f"Accord de paix conclu dans {conflict.id}",
                )
            )

    return events


def _process_influence(world: World) -> List[Event]:
    """Phase 6: Advanced multi-factor influence zone updates"""
    events = []
    calculator = InfluenceCalculator()

    # Get list of major powers to calculate influence for
    major_powers = [c.id for c in world.countries.values() if c.tier <= 2]

    for zone in world.influence_zones.values():
        old_dominant = zone.dominant_power
        old_contested = zone.contested_by.copy()

        # Calculate influence for each major power
        for power_id in major_powers:
            # Calculate multi-factor influence breakdown
            breakdown = calculator.calculate_total_influence(zone, power_id, world)

            # Update zone with breakdown (this also updates total)
            zone.update_breakdown(power_id, breakdown)

        # Update contested status based on new levels
        zone.update_contested_status()

        # Check for domination shift
        new_dominant = zone.detect_domination_shift()
        if new_dominant and new_dominant != old_dominant:
            zone.dominant_power = new_dominant

            old_power = world.get_country(old_dominant) if old_dominant else None
            new_power = world.get_country(new_dominant)

            if new_power:
                old_name = old_power.name if old_power else "None"
                old_name_fr = old_power.name_fr if old_power else "Aucun"

                events.append(Event(
                    id=f"influence_shift_{world.year}_{zone.id}",
                    year=world.year,
                    type="influence_shift",
                    title=f"Influence Shift in {zone.name}",
                    title_fr=f"Changement d'influence en {zone.name_fr}",
                    description=(
                        f"{new_power.name} has become the dominant power in {zone.name}, "
                        f"displacing {old_name}"
                    ),
                    description_fr=(
                        f"{new_power.name_fr} est devenu la puissance dominante en {zone.name_fr}, "
                        f"deplacant {old_name_fr}"
                    ),
                    country_id=new_dominant,
                    target_id=old_dominant
                ))

                # Relation impact: old dominant loses face
                if old_power:
                    old_power.modify_relation(new_dominant, -15)
                    new_power.modify_relation(old_dominant, -10)

        # Check for new contestation
        new_contestants = set(zone.contested_by) - set(old_contested)
        for contestant_id in new_contestants:
            contestant = world.get_country(contestant_id)
            dominant = world.get_country(zone.dominant_power) if zone.dominant_power else None

            if contestant and dominant:
                events.append(Event(
                    id=f"zone_contested_{world.year}_{zone.id}_{contestant_id}",
                    year=world.year,
                    type="zone_contested",
                    title=f"Rising Influence in {zone.name}",
                    title_fr=f"Influence croissante en {zone.name_fr}",
                    description=(
                        f"{contestant.name} is now contesting {dominant.name}'s "
                        f"influence in {zone.name}"
                    ),
                    description_fr=(
                        f"{contestant.name_fr} conteste maintenant l'influence de "
                        f"{dominant.name_fr} en {zone.name_fr}"
                    ),
                    country_id=contestant_id
                ))

    return events


def _update_relations(world: World) -> None:
    """Phase 7: Update diplomatic relations"""
    for country in world.countries.values():
        for other_id, relation in list(country.relations.items()):
            other = world.get_country(other_id)
            if not other:
                continue

            # Same bloc improves relations
            if country.shares_bloc(other):
                country.modify_relation(other_id, 2)

            # Rivals drift apart
            if other_id in country.rivals:
                country.modify_relation(other_id, -2)

            # Sanctions hurt relations
            if other_id in country.sanctions_on:
                country.modify_relation(other_id, -5)

            # Natural drift toward neutral
            if abs(relation) > 20 and other_id not in country.allies + country.rivals:
                drift = -1 if relation > 0 else 1
                country.modify_relation(other_id, drift)


def _apply_event(world: World, event: Event) -> None:
    """Apply event effects to the world"""
    if not event.country_id:
        return

    country = world.get_country(event.country_id)
    if not country:
        return

    for effect in event.effects:
        current = getattr(country, effect.stat, None)
        if current is not None:
            new_value = max(0, min(100, current + effect.delta))
            setattr(country, effect.stat, new_value)


def _process_projects(world: World) -> List[Event]:
    """Phase 8: Process all active projects"""
    events = []

    for country_id, projects in list(world.active_projects.items()):
        country = world.get_country(country_id)
        if not country:
            continue

        # Process projects for this country
        updated_projects, project_events = project_manager.process_projects(
            projects, country, world
        )

        # Update the projects list (remove completed ones)
        world.active_projects[country_id] = updated_projects
        events.extend(project_events)

    return events


def _detect_dilemmas(world: World) -> List[Event]:
    """Phase 9: Detect dilemmas for player countries"""
    events = []

    # Process expired dilemmas first
    expiration_events = dilemma_manager.process_expirations(world)
    events.extend(expiration_events)

    # Detect new dilemmas only for player countries
    for country in world.countries.values():
        if not country.is_player:
            continue

        active_projects = world.active_projects.get(country.id, [])
        new_dilemmas = dilemma_manager.detect_dilemmas(
            country=country,
            world=world,
            active_projects=active_projects
        )

        # Create events for new dilemmas
        for dilemma in new_dilemmas:
            events.append(Event(
                id=f"dilemma_triggered_{world.year}_{dilemma.id}",
                year=world.year,
                type="dilemma",
                title=dilemma.title,
                title_fr=dilemma.title_fr,
                description=f"Critical decision required: {dilemma.description}",
                description_fr=f"Decision critique requise: {dilemma.description_fr}",
                country_id=country.id
            ))

    return events


def _process_blocs(world: World) -> List[Event]:
    """Phase 11: Apply economic bloc bonuses"""
    events = []

    for country in world.countries.values():
        changes = apply_bloc_effects(country, bloc_manager)

        # Apply economy bonus
        if changes["economy"] > 0:
            old_economy = country.economy
            country.economy = min(100, country.economy + changes["economy"])
            if country.economy > old_economy:
                logger.debug(
                    f"{country.id}: +{changes['economy']} economy from bloc membership"
                )

        # Apply relation bonuses (smaller increment to avoid inflation)
        for other_id, bonus in changes.get("relations", {}).items():
            if bonus > 0:
                # Apply smaller bonus than the full amount (already done in _update_relations)
                pass  # Relations handled in Phase 7

    # Check for defense clauses being triggered
    for conflict in world.active_conflicts:
        for defender_id in conflict.defenders:
            defense_allies = bloc_manager.get_defense_allies(defender_id)
            for ally_id in defense_allies:
                if ally_id not in conflict.defenders:
                    ally = world.get_country(ally_id)
                    defender = world.get_country(defender_id)
                    if ally and defender:
                        # NATO Article 5 or similar - ally joins war
                        conflict.defenders.append(ally_id)
                        events.append(Event(
                            id=f"defense_clause_{world.year}_{ally_id}_{conflict.id}",
                            year=world.year,
                            type="diplomatic",
                            title="Defense Clause Activated",
                            title_fr="Clause de defense activee",
                            description=f"{ally.name} joins the war to defend {defender.name}",
                            description_fr=f"{ally.name_fr} entre en guerre pour defendre {defender.name_fr}",
                            country_id=ally_id
                        ))

    return events


def _process_summits(world: World) -> List[Event]:
    """Phase 12: Process periodic summits"""
    events = []

    # Get summits scheduled for this year
    scheduled = summit_manager.get_scheduled_summits(world.year)

    for summit_type_id in scheduled:
        # Create and process the summit
        summit = summit_manager.create_summit(summit_type_id, world.year, world)
        if summit:
            summit_events = summit_manager.process_summit(summit, world)
            events.extend(summit_events)

    return events


def _process_special_events(world: World) -> List[Event]:
    """Phase 13: Process special events (World Cup, Olympics)"""
    return summit_manager.process_special_events(world.year, world)
