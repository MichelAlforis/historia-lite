"""Tick processing for Historia Lite - Monthly granularity with Timeline backbone"""
import logging
import random
from typing import List, Tuple, Optional, Any, Dict

from .world import World, GameDate, GeopoliticalEra
from .country import Country
from .events import Event, EventPool
from .project import project_manager
from .dilemma import dilemma_manager
from .bloc import BlocManager, apply_bloc_effects
from .summit import SummitManager
from .influence import influence_manager
from .victory import victory_manager, GameEndState
from .nuclear import nuclear_manager
from .historical_events import historical_events_manager
from .espionage import espionage_manager
from .resources import resource_manager
from .leaders import leader_manager
from .procedural_events import procedural_generator
from .timeline import TimelineManager, TimelineEvent, EventType, EventSource
from ai.decision_tier4 import process_tier4_countries
from ai.ai_event_generator import ai_event_generator
from ai.decision_tier5 import process_tier5_countries
from ai.decision_tier6 import process_tier6_countries

logger = logging.getLogger(__name__)

# Replay recording callback (set by replay_routes)
_record_frame_callback = None


def set_record_frame_callback(callback):
    """Set callback for recording replay frames"""
    global _record_frame_callback
    _record_frame_callback = callback

# Global managers (initialized once)
bloc_manager = BlocManager()
summit_manager = SummitManager()


def process_tick(
    world: World,
    event_pool: EventPool,
    timeline: Optional[TimelineManager] = None
) -> Tuple[List[Event], List[TimelineEvent], Optional[GameEndState]]:
    """
    Process one MONTH of simulation (not year).
    Returns (legacy_events, timeline_events, game_end_state).
    - legacy_events: Old-style Event objects for backward compatibility
    - timeline_events: New TimelineEvent objects with dates for timeline UI
    - game_end_state: None if game continues
    """
    events: List[Event] = []
    timeline_events: List[TimelineEvent] = []

    # Check if game already ended
    if world.game_ended:
        return events, timeline_events, victory_manager.game_end_state

    # Set random seed for reproducibility (based on total months)
    total_months = world.year * 12 + world.month
    random.seed(world.seed + total_months)

    # Current date for this tick
    current_date = world.current_date

    # Phase 0: Check victory/defeat conditions BEFORE processing
    game_ended, end_state = victory_manager.check_game_end(world)
    if game_ended and end_state:
        world.game_ended = True
        world.game_end_reason = end_state.reason.value if end_state.reason else None
        world.game_end_message = end_state.message
        world.game_end_message_fr = end_state.message_fr
        world.final_score = end_state.score
        return events, timeline_events, end_state

    # Phase 1: Economy (adjusted for monthly - effects /12)
    econ_events, econ_timeline = _process_economy_monthly(world, current_date, timeline)
    events.extend(econ_events)
    timeline_events.extend(econ_timeline)

    # Phase 2: Technology (monthly - slower progress)
    tech_events, tech_timeline = _process_technology_monthly(world, current_date, timeline)
    events.extend(tech_events)
    timeline_events.extend(tech_timeline)

    # Phase 3: AI Decisions (some countries act each month)
    ai_events, ai_timeline = _process_ai_decisions_monthly(world, current_date, timeline)
    events.extend(ai_events)
    timeline_events.extend(ai_timeline)

    # Phase 4: Conflicts (monthly attrition)
    conflict_events, conflict_timeline = _process_conflicts_monthly(world, current_date, timeline)
    events.extend(conflict_events)
    timeline_events.extend(conflict_timeline)

    # Phase 5: Random Events (reduced frequency for monthly)
    if random.random() < 0.3:  # 30% chance per month
        random_events = event_pool.get_random_events(
            world.get_countries_list(), world.year, world.seed + world.month
        )
        for event in random_events[:1]:  # Max 1 random event per month
            _apply_event(world, event)
            events.append(event)
            # Convert to timeline event
            if timeline:
                te = _convert_to_timeline_event(event, current_date, timeline)
                timeline_events.append(te)

    # Phase 5b: Procedural Events
    player_id = None
    player_country = None
    for country in world.countries.values():
        if country.is_player:
            player_id = country.id
            player_country = country
            break

    if random.random() < 0.4:  # 40% chance per month
        procedural_events = procedural_generator.generate_events(world, player_id)
        for event in procedural_events[:1]:
            _apply_event(world, event)
            events.append(event)
            if timeline:
                te = _convert_to_timeline_event(event, current_date, timeline)
                timeline_events.append(te)
            logger.info(f"Procedural event: {event.title_fr} for {event.country_id}")

    # Phase 5c: AI Narrative Events (less frequent monthly)
    if player_country and random.random() < 0.15:  # 15% chance per month
        ai_event = _try_generate_ai_event(world, player_country)
        if ai_event:
            _apply_event(world, ai_event)
            events.append(ai_event)
            if timeline:
                te = _convert_to_timeline_event(ai_event, current_date, timeline)
                timeline_events.append(te)
            logger.info(f"AI narrative event: {ai_event.title_fr}")

    # Phase 6: Influence (quarterly - every 3 months)
    if world.month % 3 == 0:
        inf_events, inf_timeline = _process_influence_monthly(world, current_date, timeline)
        events.extend(inf_events)
        timeline_events.extend(inf_timeline)

    # Phase 7: Relations (monthly drift)
    _update_relations_monthly(world)

    # Phase 7b: World Mood update (collective emotional state)
    _update_world_mood(world, timeline, timeline_events)

    # Phase 8: Projects (monthly progress)
    proj_events, proj_timeline = _process_projects_monthly(world, current_date, timeline)
    events.extend(proj_events)
    timeline_events.extend(proj_timeline)

    # Phase 9: Dilemma Detection
    dilemma_events, dilemma_timeline = _detect_dilemmas_monthly(world, current_date, timeline)
    events.extend(dilemma_events)
    timeline_events.extend(dilemma_timeline)

    # Phase 10: Tier 4-6 Countries (adjusted frequencies for monthly)
    # Tier 4: every 6 months, Tier 5: every 12 months, Tier 6: every 24 months
    if world.tick_counter % 6 == 0:
        tier4_events = process_tier4_countries(world, world.tick_counter)
        events.extend(tier4_events)
        for e in tier4_events:
            if timeline:
                timeline_events.append(_convert_to_timeline_event(e, current_date, timeline))

    if world.tick_counter % 12 == 0:
        tier5_events = process_tier5_countries(world, world.tick_counter)
        events.extend(tier5_events)
        for e in tier5_events:
            if timeline:
                timeline_events.append(_convert_to_timeline_event(e, current_date, timeline))

    if world.tick_counter % 24 == 0:
        tier6_events = process_tier6_countries(world, world.tick_counter)
        events.extend(tier6_events)
        for e in tier6_events:
            if timeline:
                timeline_events.append(_convert_to_timeline_event(e, current_date, timeline))

    # Increment tick counter
    world.tick_counter = (world.tick_counter + 1) % 60  # Cycle every 60 months (5 years)

    # Phase 11: Bloc Economic Bonuses (quarterly)
    if world.month % 3 == 0:
        bloc_events, bloc_timeline = _process_blocs_monthly(world, current_date, timeline)
        events.extend(bloc_events)
        timeline_events.extend(bloc_timeline)

    # Phase 12: Periodic Summits (check each month)
    summit_events, summit_timeline = _process_summits_monthly(world, current_date, timeline)
    events.extend(summit_events)
    timeline_events.extend(summit_timeline)

    # Phase 13: Special Events (annual check in December)
    if world.month == 12:
        special_events, special_timeline = _process_special_events_monthly(world, current_date, timeline)
        events.extend(special_events)
        timeline_events.extend(special_timeline)

    # Phase 14: Nuclear DEFCON updates (monthly)
    nuclear_events = nuclear_manager.update_defcon(world)
    events.extend(nuclear_events)
    for e in nuclear_events:
        if timeline:
            timeline_events.append(_convert_to_timeline_event(e, current_date, timeline))

    # Phase 15: Historical Events (check each month)
    historical_events = historical_events_manager.check_events(world)
    events.extend(historical_events)
    for e in historical_events:
        if timeline:
            te = _convert_to_timeline_event(e, current_date, timeline, source=EventSource.HISTORICAL)
            timeline_events.append(te)

    # Check for nuclear war game end
    if world.defcon_level == 0:
        end_state = GameEndState(
            is_victory=False,
            reason=None,
            message="Nuclear war has devastated the world.",
            message_fr="Une guerre nucleaire a devaste le monde.",
            score=0
        )
        world.game_ended = True
        world.game_end_reason = "nuclear_annihilation"
        world.game_end_message = end_state.message
        world.game_end_message_fr = end_state.message_fr
        world.final_score = 0
        return events, timeline_events, end_state

    # Check for player defeat
    game_ended, end_state = victory_manager.check_game_end(world)
    if game_ended and end_state:
        world.game_ended = True
        world.game_end_reason = end_state.reason.value if end_state.reason else None
        world.game_end_message = end_state.message
        world.game_end_message_fr = end_state.message_fr
        world.final_score = end_state.score
        return events, timeline_events, end_state

    # Phase 17: Espionage (monthly)
    espionage_events = _process_espionage(world)
    events.extend(espionage_events)
    for e in espionage_events:
        if timeline:
            timeline_events.append(_convert_to_timeline_event(e, current_date, timeline))

    # Phase 18: Resource management (monthly)
    resource_events = _process_resources(world)
    events.extend(resource_events)
    for e in resource_events:
        if timeline:
            timeline_events.append(_convert_to_timeline_event(e, current_date, timeline))

    # Phase 19: Leaders (annual check in January, or random coups)
    if world.month == 1 or random.random() < 0.02:  # 2% coup chance per month
        leader_events = _process_leaders(world)
        events.extend(leader_events)
        for e in leader_events:
            if timeline:
                timeline_events.append(_convert_to_timeline_event(e, current_date, timeline))

    # Assign specific days to timeline events that don't have one
    if timeline:
        timeline.assign_day_to_events(timeline_events, world.year, world.month)
        # Add all events to timeline
        for te in timeline_events:
            timeline.add_event(te)
        # Process any delayed effects
        delayed = timeline.process_delayed_effects(current_date)
        for effect in delayed:
            _apply_delayed_effect(world, effect)

    # Store events in history (legacy)
    for event in events:
        world.add_event(event)

    # Advance to next month
    old_date = f"{world.month}/{world.year}"
    world.advance_month()
    new_date = f"{world.month}/{world.year}"

    # Record frame for replay if recording is active
    if _record_frame_callback is not None:
        try:
            _record_frame_callback([e.model_dump() if hasattr(e, 'model_dump') else vars(e) for e in events])
        except Exception as e:
            logger.warning(f"Failed to record replay frame: {e}")

    logger.info(f"Tick processed: {old_date} -> {new_date} ({len(timeline_events)} timeline events)")
    return events, timeline_events, None


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
    calculator = influence_manager.calculator

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

    # Check if a summit should occur this year
    summit = summit_manager.check_summit(world)
    if summit:
        summit_events = summit_manager.process_summit(world, summit)
        if summit_events:
            events.extend(summit_events)

    return events


def _process_special_events(world: World) -> List[Event]:
    """Phase 13: Process special events (World Cup, Olympics)"""
    # Simplified: no special events for now
    return []


def _process_espionage(world: World) -> List[Event]:
    """Phase 17: Process espionage missions and AI spy decisions"""
    # Use the proper method name
    return espionage_manager.process_espionage(world)


def _process_resources(world: World) -> List[Event]:
    """Phase 18: Process resource depletion, prices, and crises"""
    return resource_manager.process_resources(world)


def _process_leaders(world: World) -> List[Event]:
    """Phase 19: Process leader changes, elections, coups"""
    return leader_manager.process_leaders(world)


def _try_generate_ai_event(world: World, player: Country) -> Optional[Event]:
    """Try to generate an AI narrative event (sync wrapper for async generator)

    Returns None if:
    - AI is not available
    - Cooldown not elapsed
    - Random chance failed
    - Generation failed
    """
    import asyncio

    try:
        # Check if we should even try (fast sync check)
        if not ai_event_generator._should_generate(player.id, world.year):
            return None

        # Random chance check (30%)
        if random.random() > 0.30:
            return None

        # Run async generation in sync context
        loop = asyncio.new_event_loop()
        try:
            event = loop.run_until_complete(
                ai_event_generator.generate_narrative_event(
                    world=world,
                    player=player,
                    force=True  # We already did the checks above
                )
            )
            return event
        finally:
            loop.close()

    except Exception as e:
        logger.warning(f"AI event generation failed: {e}")
        return None


# =============================================================================
# MONTHLY PROCESSING FUNCTIONS (Timeline-aware)
# =============================================================================

def _convert_to_timeline_event(
    event: Event,
    date: GameDate,
    timeline: TimelineManager,
    source: EventSource = EventSource.PROCEDURAL
) -> TimelineEvent:
    """Convert a legacy Event to a TimelineEvent"""
    # Map event type to EventType enum
    type_mapping = {
        "economic": EventType.ECONOMIC,
        "military": EventType.MILITARY,
        "diplomatic": EventType.DIPLOMATIC,
        "political": EventType.POLITICAL,
        "decision": EventType.POLITICAL,
        "sanctions": EventType.ECONOMIC,
        "war": EventType.WAR,
        "peace": EventType.DIPLOMATIC,
        "influence_shift": EventType.POLITICAL,
        "zone_contested": EventType.POLITICAL,
        "dilemma": EventType.POLITICAL,
        "crisis": EventType.CRISIS,
        "technology": EventType.TECHNOLOGY,
        "internal": EventType.INTERNAL,
        "player_action": EventType.PLAYER_ACTION,
    }
    event_type = type_mapping.get(event.type, EventType.POLITICAL)

    # Calculate importance based on event type
    importance = 3
    if event.type in ["war", "peace", "crisis"]:
        importance = 5
    elif event.type in ["sanctions", "diplomatic"]:
        importance = 4
    elif event.type == "decision":
        importance = 2

    return TimelineEvent(
        id=timeline.generate_event_id(event_type.value[:3]),
        date=date,
        actor_country=event.country_id or "WORLD",
        target_countries=[event.target_id] if event.target_id else [],
        title=event.title,
        title_fr=event.title_fr,
        description=event.description,
        description_fr=event.description_fr,
        type=event_type,
        source=source,
        importance=importance,
        effects={}
    )


def _apply_delayed_effect(world: World, effect: Any) -> None:
    """Apply a delayed effect from the timeline"""
    country = world.get_country(effect.target_country)
    if not country:
        return

    for stat, delta in effect.effects.items():
        current = getattr(country, stat, None)
        if current is not None:
            new_value = max(0, min(100, current + delta))
            setattr(country, stat, new_value)
            logger.info(f"Delayed effect applied: {country.id}.{stat} += {delta}")


def _update_world_mood(
    world: World,
    timeline: Optional[TimelineManager],
    recent_events: List[TimelineEvent]
) -> None:
    """
    Update the world's collective mood based on recent events.
    This affects global gameplay modifiers for all countries.
    """
    mood = world.mood

    # Count active wars
    active_wars = len(world.active_conflicts)

    # War fatigue: increases with conflicts, decays slowly
    if active_wars > 0:
        mood.war_fatigue = min(100, mood.war_fatigue + active_wars * 3)
    else:
        mood.war_fatigue = max(0, mood.war_fatigue - 2)

    # Nuclear anxiety based on DEFCON level
    if world.defcon_level <= 2:
        mood.nuclear_anxiety = min(100, mood.nuclear_anxiety + 10)
    elif world.defcon_level == 3:
        mood.nuclear_anxiety = min(100, mood.nuclear_anxiety + 3)
    else:
        mood.nuclear_anxiety = max(0, mood.nuclear_anxiety - 2)

    # Market volatility based on global tension
    if world.global_tension > 70:
        mood.market_volatility = min(100, mood.market_volatility + 5)
    elif world.global_tension < 40:
        mood.market_volatility = max(10, mood.market_volatility - 3)

    # Analyze recent timeline events for mood indicators
    economic_crises = 0
    diplomatic_events = 0
    military_events = 0
    alliance_events = 0

    for event in recent_events:
        event_type = event.type.value if hasattr(event.type, 'value') else str(event.type)
        importance = event.importance

        if event_type == "economic" and importance >= 4:
            economic_crises += 1
        elif event_type == "diplomatic":
            diplomatic_events += 1
            if "alliance" in event.title.lower() or "treaty" in event.title.lower():
                alliance_events += 1
        elif event_type in ["military", "war"]:
            military_events += 1

    # Economic optimism
    if economic_crises > 0:
        mood.economic_optimism = max(0, mood.economic_optimism - economic_crises * 8)
    elif world.oil_price < 60:
        mood.economic_optimism = min(100, mood.economic_optimism + 2)
    else:
        mood.economic_optimism = min(100, mood.economic_optimism + 1)

    # Diplomatic openness
    if diplomatic_events > military_events:
        mood.diplomatic_openness = min(100, mood.diplomatic_openness + 3)
    elif military_events > diplomatic_events:
        mood.diplomatic_openness = max(0, mood.diplomatic_openness - 2)

    # Global confidence
    if mood.war_fatigue > 60 or mood.nuclear_anxiety > 60:
        mood.global_confidence = max(0, mood.global_confidence - 3)
    elif mood.economic_optimism > 60 and mood.war_fatigue < 30:
        mood.global_confidence = min(100, mood.global_confidence + 2)

    # Check for era transitions
    new_era = _check_era_transition(world, mood, timeline, alliance_events)
    if new_era and new_era != mood.current_era:
        logger.info(f"World era changed: {mood.current_era.value} -> {new_era.value}")
        mood.current_era = new_era
        mood.era_start_year = world.year
        mood.era_start_month = world.month
        mood.era_months_active = 0
        mood.era_strength = 50
    else:
        mood.era_months_active += 1
        # Era strength increases over time
        if mood.era_months_active > 6:
            mood.era_strength = min(100, mood.era_strength + 2)


def _check_era_transition(
    world: World,
    mood: Any,
    timeline: Optional[TimelineManager],
    alliance_events: int
) -> Optional[GeopoliticalEra]:
    """Check if conditions are met for an era transition"""

    # Crisis Mode: extreme tensions or DEFCON 2
    if world.global_tension > 80 and mood.nuclear_anxiety > 70:
        return GeopoliticalEra.CRISIS_MODE
    if world.defcon_level <= 2:
        return GeopoliticalEra.CRISIS_MODE

    # Detente: after exhausting wars, no active conflicts, low tensions
    if mood.war_fatigue > 70 and len(world.active_conflicts) == 0 and world.global_tension < 40:
        return GeopoliticalEra.DETENTE

    # Cold War: two superpowers at odds, bloc tension high
    usa = world.get_country("USA")
    chn = world.get_country("CHN")
    rus = world.get_country("RUS")
    if usa and chn:
        us_china_relations = usa.relations.get("CHN", 0)
        if us_china_relations < -50 and world.global_tension > 60:
            return GeopoliticalEra.COLD_WAR
    if usa and rus:
        us_russia_relations = usa.relations.get("RUS", 0)
        if us_russia_relations < -50 and world.global_tension > 60:
            return GeopoliticalEra.COLD_WAR

    # Alliance Building: many alliances being formed
    if alliance_events >= 2:
        return GeopoliticalEra.ALLIANCE_BUILDING

    # Military Buildup: high military spending events
    avg_military = sum(c.military for c in world.countries.values()) / max(1, len(world.countries))
    if avg_military > 70 and world.global_tension > 50:
        return GeopoliticalEra.MILITARY_BUILDUP

    # Sanctions Era: many sanctions active
    total_sanctions = sum(len(c.sanctions_on) for c in world.countries.values())
    if total_sanctions > 10:
        return GeopoliticalEra.SANCTIONS_ERA

    # Multipolar Shift: multiple strong powers emerging
    strong_powers = [c for c in world.countries.values() if c.power_score > 200]
    if len(strong_powers) >= 5:
        return GeopoliticalEra.MULTIPOLAR_SHIFT

    # No change - remain in equilibrium or current era
    return None


def _process_economy_monthly(
    world: World,
    date: GameDate,
    timeline: Optional[TimelineManager]
) -> Tuple[List[Event], List[TimelineEvent]]:
    """Monthly economic processing (effects scaled down from annual)"""
    events = []
    timeline_events = []

    # Oil price fluctuation (smaller monthly changes)
    oil_delta = random.randint(-3, 3)
    world.oil_price = max(30, min(150, world.oil_price + oil_delta))

    for country in world.countries.values():
        # Monthly growth is ~1/12 of annual
        growth = 0

        # Quarterly growth boost (every 3 months)
        if world.month % 3 == 0:
            if country.stability > 60:
                growth += 1
            if country.technology > 70:
                growth += 1
            if country.economy < 30:
                growth -= 1

        # Sanctions impact (monthly)
        sanctioners = [c for c in world.countries.values() if country.id in c.sanctions_on]
        if sanctioners:
            growth -= len(sanctioners)  # Reduced from *2

        # Resource-rich countries benefit from high oil (quarterly)
        if world.month % 3 == 0 and country.resources > 70 and world.oil_price > 100:
            growth += 1

        if growth != 0:
            country.economy = max(0, min(100, country.economy + growth))

        # Population growth (annual, only in December)
        if world.month == 12:
            pop_growth = 1 if country.stability > 50 else 0
            country.population = max(0, min(100, country.population + pop_growth))

    return events, timeline_events


def _process_technology_monthly(
    world: World,
    date: GameDate,
    timeline: Optional[TimelineManager]
) -> Tuple[List[Event], List[TimelineEvent]]:
    """Monthly technology processing"""
    events = []
    timeline_events = []

    # Tech only advances quarterly
    if world.month % 3 != 0:
        return events, timeline_events

    for country in world.countries.values():
        tech_growth = 0

        # Economy drives tech
        if country.economy > 70:
            tech_growth += 1

        # Tech transfers from allies (annual check)
        if world.month == 6:  # Mid-year
            for ally_id in country.allies:
                ally = world.get_country(ally_id)
                if ally and ally.technology > country.technology + 20:
                    tech_growth += 1
                    break

        if tech_growth > 0:
            country.technology = max(0, min(100, country.technology + tech_growth))

    return events, timeline_events


def _process_ai_decisions_monthly(
    world: World,
    date: GameDate,
    timeline: Optional[TimelineManager]
) -> Tuple[List[Event], List[TimelineEvent]]:
    """Monthly AI decision processing"""
    events = []
    timeline_events = []

    # Only ~30% of AI countries act each month
    for country in world.countries.values():
        if country.is_player:
            continue

        if random.random() > 0.3:
            continue

        decision = _make_ai_decision(country, world)
        if decision:
            events.append(decision)
            if timeline:
                te = _convert_to_timeline_event(decision, date, timeline)
                timeline_events.append(te)

    return events, timeline_events


def _process_conflicts_monthly(
    world: World,
    date: GameDate,
    timeline: Optional[TimelineManager]
) -> Tuple[List[Event], List[TimelineEvent]]:
    """Monthly conflict processing with attrition"""
    events = []
    timeline_events = []

    for conflict in world.active_conflicts[:]:
        conflict.duration += 1  # Duration now in months

        # Monthly war exhaustion (reduced from annual)
        for attacker_id in conflict.attackers:
            attacker = world.get_country(attacker_id)
            if attacker:
                attacker.economy = max(0, attacker.economy - 0.5)
                if random.random() < 0.2:  # 20% chance per month
                    attacker.stability = max(0, attacker.stability - 1)

        for defender_id in conflict.defenders:
            defender = world.get_country(defender_id)
            if defender:
                defender.economy = max(0, defender.economy - 0.8)
                if random.random() < 0.3:  # 30% chance per month
                    defender.stability = max(0, defender.stability - 1)

        # Peace chance after 12 months (was 3 years)
        if conflict.duration >= 12 and random.random() < 0.1:  # 10% per month after 1 year
            world.end_conflict(conflict.id)
            peace_event = Event(
                id=f"peace_{world.year}_{world.month}_{conflict.id}",
                year=world.year,
                type="peace",
                title="Peace Agreement",
                title_fr="Accord de paix",
                description=f"Peace agreement reached in {conflict.id}",
                description_fr=f"Accord de paix conclu dans {conflict.id}",
            )
            events.append(peace_event)
            if timeline:
                te = TimelineEvent(
                    id=timeline.generate_event_id("pea"),
                    date=date,
                    actor_country=conflict.attackers[0] if conflict.attackers else "WORLD",
                    target_countries=conflict.defenders,
                    title="Peace Agreement Signed",
                    title_fr="Accord de paix signe",
                    description=f"After {conflict.duration} months of conflict, a peace agreement has been reached.",
                    description_fr=f"Apres {conflict.duration} mois de conflit, un accord de paix a ete signe.",
                    type=EventType.DIPLOMATIC,
                    source=EventSource.SYSTEM,
                    importance=5
                )
                timeline_events.append(te)

    return events, timeline_events


def _process_influence_monthly(
    world: World,
    date: GameDate,
    timeline: Optional[TimelineManager]
) -> Tuple[List[Event], List[TimelineEvent]]:
    """Quarterly influence zone updates"""
    legacy_events = _process_influence(world)
    timeline_events = []

    if timeline:
        for e in legacy_events:
            timeline_events.append(_convert_to_timeline_event(e, date, timeline))

    return legacy_events, timeline_events


def _update_relations_monthly(world: World) -> None:
    """Monthly relation drift (smaller changes)"""
    for country in world.countries.values():
        for other_id, relation in list(country.relations.items()):
            other = world.get_country(other_id)
            if not other:
                continue

            # Same bloc improves relations (quarterly)
            if world.month % 3 == 0 and country.shares_bloc(other):
                country.modify_relation(other_id, 1)

            # Rivals drift apart (monthly)
            if other_id in country.rivals and random.random() < 0.3:
                country.modify_relation(other_id, -1)

            # Sanctions hurt relations (monthly)
            if other_id in country.sanctions_on:
                country.modify_relation(other_id, -2)


def _process_projects_monthly(
    world: World,
    date: GameDate,
    timeline: Optional[TimelineManager]
) -> Tuple[List[Event], List[TimelineEvent]]:
    """Monthly project progress"""
    legacy_events = _process_projects(world)
    timeline_events = []

    if timeline:
        for e in legacy_events:
            timeline_events.append(_convert_to_timeline_event(e, date, timeline))

    return legacy_events, timeline_events


def _detect_dilemmas_monthly(
    world: World,
    date: GameDate,
    timeline: Optional[TimelineManager]
) -> Tuple[List[Event], List[TimelineEvent]]:
    """Monthly dilemma detection (reduced frequency)"""
    events = []
    timeline_events = []

    # Only check dilemmas quarterly
    if world.month % 3 != 0:
        return events, timeline_events

    legacy_events = _detect_dilemmas(world)
    if timeline:
        for e in legacy_events:
            timeline_events.append(_convert_to_timeline_event(e, date, timeline))

    return legacy_events, timeline_events


def _process_blocs_monthly(
    world: World,
    date: GameDate,
    timeline: Optional[TimelineManager]
) -> Tuple[List[Event], List[TimelineEvent]]:
    """Quarterly bloc processing"""
    legacy_events = _process_blocs(world)
    timeline_events = []

    if timeline:
        for e in legacy_events:
            te = _convert_to_timeline_event(e, date, timeline)
            te.importance = 4  # Defense clause events are important
            timeline_events.append(te)

    return legacy_events, timeline_events


def _process_summits_monthly(
    world: World,
    date: GameDate,
    timeline: Optional[TimelineManager]
) -> Tuple[List[Event], List[TimelineEvent]]:
    """Monthly summit check"""
    legacy_events = _process_summits(world)
    timeline_events = []

    if timeline and legacy_events:
        for e in legacy_events:
            te = _convert_to_timeline_event(e, date, timeline)
            te.type = EventType.DIPLOMATIC
            te.importance = 4  # Summits are important
            timeline_events.append(te)

    return legacy_events, timeline_events


def _process_special_events_monthly(
    world: World,
    date: GameDate,
    timeline: Optional[TimelineManager]
) -> Tuple[List[Event], List[TimelineEvent]]:
    """Annual special events (Olympics, World Cup, etc.)"""
    events = []
    timeline_events = []

    # Olympics every 4 years (summer in even years, winter in odd)
    if world.year % 4 == 0:  # Summer Olympics
        host_candidates = [c for c in world.countries.values() if c.tier <= 3]
        if host_candidates:
            host = random.choice(host_candidates)
            event = Event(
                id=f"olympics_{world.year}",
                year=world.year,
                type="cultural",
                title=f"Summer Olympics in {host.name}",
                title_fr=f"Jeux Olympiques d'ete a {host.name_fr}",
                description=f"The {world.year} Summer Olympics are held in {host.name}",
                description_fr=f"Les Jeux Olympiques d'ete {world.year} se tiennent a {host.name_fr}",
                country_id=host.id
            )
            events.append(event)
            host.soft_power = min(100, host.soft_power + 5)

            if timeline:
                te = TimelineEvent(
                    id=timeline.generate_event_id("cul"),
                    date=GameDate(year=world.year, month=7, day=15),  # July
                    actor_country=host.id,
                    title=f"Summer Olympics Opening Ceremony",
                    title_fr=f"Ceremonie d'ouverture des Jeux Olympiques d'ete",
                    description=f"The {world.year} Summer Olympics officially begin in {host.name}, drawing athletes from around the world.",
                    description_fr=f"Les Jeux Olympiques d'ete {world.year} s'ouvrent officiellement a {host.name_fr}, attirant des athletes du monde entier.",
                    type=EventType.CULTURAL,
                    source=EventSource.SYSTEM,
                    importance=4
                )
                timeline_events.append(te)

    # World Cup every 4 years (2026, 2030, etc.)
    if world.year % 4 == 2:
        host_candidates = [c for c in world.countries.values() if c.tier <= 3]
        if host_candidates:
            host = random.choice(host_candidates)
            event = Event(
                id=f"worldcup_{world.year}",
                year=world.year,
                type="cultural",
                title=f"FIFA World Cup in {host.name}",
                title_fr=f"Coupe du Monde FIFA a {host.name_fr}",
                description=f"The {world.year} FIFA World Cup is held in {host.name}",
                description_fr=f"La Coupe du Monde FIFA {world.year} se tient a {host.name_fr}",
                country_id=host.id
            )
            events.append(event)
            host.soft_power = min(100, host.soft_power + 3)

            if timeline:
                te = TimelineEvent(
                    id=timeline.generate_event_id("cul"),
                    date=GameDate(year=world.year, month=6, day=10),  # June
                    actor_country=host.id,
                    title=f"FIFA World Cup Kicks Off",
                    title_fr=f"Coup d'envoi de la Coupe du Monde FIFA",
                    description=f"The {world.year} FIFA World Cup begins in {host.name}, with 32 nations competing for glory.",
                    description_fr=f"La Coupe du Monde FIFA {world.year} debute a {host.name_fr}, avec 32 nations en lice pour la gloire.",
                    type=EventType.CULTURAL,
                    source=EventSource.SYSTEM,
                    importance=3
                )
                timeline_events.append(te)

    return events, timeline_events


# =============================================================================
# BACKWARD COMPATIBILITY: Keep old annual process_tick available
# =============================================================================

def process_tick_legacy(world: World, event_pool: EventPool) -> Tuple[List[Event], Optional[GameEndState]]:
    """
    Legacy annual tick processing for backward compatibility.
    Processes 12 months in one call.
    """
    all_events = []
    all_timeline_events = []

    for _ in range(12):
        events, timeline_events, end_state = process_tick(world, event_pool, None)
        all_events.extend(events)
        if end_state:
            return all_events, end_state

    return all_events, None
