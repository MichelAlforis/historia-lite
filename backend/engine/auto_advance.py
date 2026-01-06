"""Auto-advance engine for Historia Lite - Time progression system"""
import logging
from typing import List, Tuple, Optional, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field

from .world import World, GameDate
from .events import Event
from .timeline import TimelineManager, TimelineEvent

logger = logging.getLogger(__name__)


class PauseReason(str, Enum):
    """Reasons for pausing auto-advance"""
    WAR_DECLARED = "war_declared"
    WAR_ENDED = "war_ended"
    CRISIS_STARTED = "crisis_started"
    CRISIS_ESCALATED = "crisis_escalated"
    DEFCON_CHANGED = "defcon_changed"
    NUCLEAR_EVENT = "nuclear_event"
    PLAYER_ATTACKED = "player_attacked"
    PLAYER_MENTIONED = "player_mentioned"
    IMPORTANT_EVENT = "important_event"
    WATCHED_COUNTRY = "watched_country"
    GOAL_CONFLICT = "goal_conflict"
    MAX_DAYS_REACHED = "max_days_reached"
    MANUAL_PAUSE = "manual_pause"


class AutoAdvanceConfig(BaseModel):
    """Configuration for auto-advance behavior"""
    # Pause conditions
    pause_on_war: bool = True
    pause_on_crisis: bool = True
    pause_on_defcon_change: bool = True
    pause_on_nuclear: bool = True
    pause_on_player_attacked: bool = True
    pause_on_player_mentioned: bool = True

    # Event importance threshold (1-5, pause if >= this)
    min_event_importance: int = Field(default=4, ge=1, le=5)

    # Countries to watch specifically
    watch_countries: List[str] = Field(default_factory=list)

    # Speed settings
    days_per_batch: int = Field(default=7, ge=1, le=30)  # Days to process at once
    max_days: int = Field(default=180, ge=1, le=365)  # Max days before forced pause


class AutoAdvanceResult(BaseModel):
    """Result of an auto-advance operation"""
    days_advanced: int
    paused: bool
    pause_reason: Optional[PauseReason] = None
    pause_message: Optional[str] = None
    pause_message_fr: Optional[str] = None
    events: List[Dict[str, Any]] = Field(default_factory=list)
    timeline_events: List[Dict[str, Any]] = Field(default_factory=list)
    final_date: str
    final_date_fr: str
    game_ended: bool = False
    game_end_reason: Optional[str] = None


class AutoAdvanceEngine:
    """Engine for auto-advancing time until an important event occurs"""

    def __init__(self):
        self._previous_defcon: int = 5
        self._previous_wars: set = set()
        self._previous_crises: set = set()

    def reset(self) -> None:
        """Reset engine state for new game"""
        self._previous_defcon = 5
        self._previous_wars = set()
        self._previous_crises = set()

    def should_pause(
        self,
        events: List[Event],
        timeline_events: List[TimelineEvent],
        world: World,
        config: AutoAdvanceConfig,
        player_id: Optional[str] = None
    ) -> Tuple[bool, Optional[PauseReason], Optional[str], Optional[str]]:
        """
        Determine if auto-advance should pause.
        Returns: (should_pause, reason, message_en, message_fr)
        """
        # Get player country if available
        player = world.get_player_country() if player_id is None else world.get_country(player_id)
        player_id = player.id if player else None

        # Check DEFCON change
        if config.pause_on_defcon_change and hasattr(world, 'defcon'):
            if world.defcon != self._previous_defcon:
                old_defcon = self._previous_defcon
                self._previous_defcon = world.defcon
                if world.defcon < old_defcon:  # Escalation
                    return (
                        True,
                        PauseReason.DEFCON_CHANGED,
                        f"DEFCON raised to {world.defcon}!",
                        f"DEFCON eleve a {world.defcon}!"
                    )

        # Check for new wars
        if config.pause_on_war:
            current_wars = set()
            for country in world.countries.values():
                for enemy in country.at_war:
                    war_key = tuple(sorted([country.id, enemy]))
                    current_wars.add(war_key)

            new_wars = current_wars - self._previous_wars
            ended_wars = self._previous_wars - current_wars
            self._previous_wars = current_wars

            if new_wars:
                parties = list(new_wars)[0]
                return (
                    True,
                    PauseReason.WAR_DECLARED,
                    f"War declared between {parties[0]} and {parties[1]}!",
                    f"Guerre declaree entre {parties[0]} et {parties[1]}!"
                )

            if ended_wars:
                parties = list(ended_wars)[0]
                return (
                    True,
                    PauseReason.WAR_ENDED,
                    f"War ended between {parties[0]} and {parties[1]}",
                    f"Guerre terminee entre {parties[0]} et {parties[1]}"
                )

        # Check for player attacked
        if config.pause_on_player_attacked and player_id:
            for event in events:
                if event.target_id == player_id and event.type in ("attack", "war", "incident", "sanctions"):
                    actor = world.get_country(event.country_id)
                    actor_name = actor.name_fr if actor else event.country_id
                    return (
                        True,
                        PauseReason.PLAYER_ATTACKED,
                        f"Your country has been targeted by {actor_name}!",
                        f"Votre pays a ete vise par {actor_name}!"
                    )

        # Check for player mentioned in events
        if config.pause_on_player_mentioned and player_id:
            for event in events:
                if event.country_id == player_id or event.target_id == player_id:
                    return (
                        True,
                        PauseReason.PLAYER_MENTIONED,
                        f"Event involving your country: {event.title_fr}",
                        f"Evenement concernant votre pays: {event.title_fr}"
                    )

        # Check for nuclear events
        if config.pause_on_nuclear:
            for event in events:
                if event.type in ("nuclear", "nuclear_test", "nuclear_threat"):
                    return (
                        True,
                        PauseReason.NUCLEAR_EVENT,
                        event.title,
                        event.title_fr
                    )

        # Check for crisis events
        if config.pause_on_crisis:
            for event in events:
                if event.type in ("crisis", "crisis_escalation"):
                    return (
                        True,
                        PauseReason.CRISIS_STARTED,
                        event.title,
                        event.title_fr
                    )

        # Check watched countries
        if config.watch_countries:
            for event in events:
                if event.country_id in config.watch_countries:
                    country = world.get_country(event.country_id)
                    country_name = country.name_fr if country else event.country_id
                    return (
                        True,
                        PauseReason.WATCHED_COUNTRY,
                        f"Event in watched country {country_name}: {event.title}",
                        f"Evenement dans le pays surveille {country_name}: {event.title_fr}"
                    )

        # Check event importance
        for te in timeline_events:
            if te.importance >= config.min_event_importance:
                return (
                    True,
                    PauseReason.IMPORTANT_EVENT,
                    f"Important event: {te.title}",
                    f"Evenement important: {te.title_fr}"
                )

        # Check for goal conflicts (from agenda system)
        for event in events:
            if event.type == "goal_conflict" and hasattr(event, 'metadata'):
                if event.metadata and event.metadata.get('intensity') in ('major', 'existential'):
                    return (
                        True,
                        PauseReason.GOAL_CONFLICT,
                        event.title,
                        event.title_fr
                    )

        return (False, None, None, None)

    def advance_days(
        self,
        world: World,
        config: AutoAdvanceConfig,
        process_tick_fn,
        timeline: Optional[TimelineManager] = None,
        event_pool = None,
        player_id: Optional[str] = None
    ) -> AutoAdvanceResult:
        """
        Advance the world by multiple days until a pause condition is met.

        Args:
            world: The game world
            config: Auto-advance configuration
            process_tick_fn: Function to process a single day tick
            timeline: Timeline manager (optional)
            event_pool: Event pool (optional)
            player_id: Player's country ID (optional)

        Returns:
            AutoAdvanceResult with all events and final state
        """
        all_events = []
        all_timeline_events = []
        days_advanced = 0
        paused = False
        pause_reason = None
        pause_message = None
        pause_message_fr = None

        while days_advanced < config.max_days:
            # Process one day
            try:
                day_events, day_timeline, game_end = process_tick_fn(
                    world, event_pool, timeline
                )
            except Exception as e:
                logger.error(f"Error processing tick: {e}")
                break

            # Collect events
            all_events.extend(day_events)
            all_timeline_events.extend(day_timeline)
            days_advanced += 1

            # Check if game ended
            if game_end:
                return AutoAdvanceResult(
                    days_advanced=days_advanced,
                    paused=True,
                    pause_reason=PauseReason.MANUAL_PAUSE,
                    pause_message="Game ended",
                    pause_message_fr="Partie terminee",
                    events=[self._event_to_dict(e) for e in all_events],
                    timeline_events=[self._timeline_event_to_dict(te) for te in all_timeline_events],
                    final_date=world.date_display_full,
                    final_date_fr=world.date_display_full,
                    game_ended=True,
                    game_end_reason=game_end.reason.value if game_end.reason else None
                )

            # Check pause conditions
            should_pause, reason, msg, msg_fr = self.should_pause(
                day_events, day_timeline, world, config, player_id
            )

            if should_pause:
                paused = True
                pause_reason = reason
                pause_message = msg
                pause_message_fr = msg_fr
                break

            # Batch processing - pause every N days to update UI
            if days_advanced % config.days_per_batch == 0:
                # Don't pause, just continue - this is for performance
                pass

        # Check max days
        if days_advanced >= config.max_days and not paused:
            paused = True
            pause_reason = PauseReason.MAX_DAYS_REACHED
            pause_message = f"Reached maximum of {config.max_days} days"
            pause_message_fr = f"Atteint le maximum de {config.max_days} jours"

        return AutoAdvanceResult(
            days_advanced=days_advanced,
            paused=paused,
            pause_reason=pause_reason,
            pause_message=pause_message,
            pause_message_fr=pause_message_fr,
            events=[self._event_to_dict(e) for e in all_events],
            timeline_events=[self._timeline_event_to_dict(te) for te in all_timeline_events],
            final_date=world.date_display_full,
            final_date_fr=world.date_display_full,
            game_ended=False
        )

    def advance_to_next_event(
        self,
        world: World,
        process_tick_fn,
        timeline: Optional[TimelineManager] = None,
        event_pool = None,
        player_id: Optional[str] = None,
        max_days: int = 365
    ) -> AutoAdvanceResult:
        """
        Advance until any significant event occurs.
        Uses more aggressive auto-advance settings.
        """
        config = AutoAdvanceConfig(
            pause_on_war=True,
            pause_on_crisis=True,
            pause_on_defcon_change=True,
            pause_on_nuclear=True,
            pause_on_player_attacked=True,
            pause_on_player_mentioned=True,
            min_event_importance=3,  # Lower threshold
            watch_countries=[],
            days_per_batch=7,
            max_days=max_days
        )
        return self.advance_days(
            world, config, process_tick_fn, timeline, event_pool, player_id
        )

    def advance_week(
        self,
        world: World,
        process_tick_fn,
        timeline: Optional[TimelineManager] = None,
        event_pool = None,
        player_id: Optional[str] = None
    ) -> AutoAdvanceResult:
        """Advance exactly one week (7 days)"""
        config = AutoAdvanceConfig(
            pause_on_war=True,
            pause_on_crisis=True,
            pause_on_defcon_change=True,
            pause_on_nuclear=True,
            pause_on_player_attacked=True,
            pause_on_player_mentioned=False,
            min_event_importance=5,  # Only critical events
            watch_countries=[],
            days_per_batch=7,
            max_days=7  # Exactly one week
        )
        return self.advance_days(
            world, config, process_tick_fn, timeline, event_pool, player_id
        )

    def advance_month(
        self,
        world: World,
        process_tick_fn,
        timeline: Optional[TimelineManager] = None,
        event_pool = None,
        player_id: Optional[str] = None
    ) -> AutoAdvanceResult:
        """Advance approximately one month (30 days)"""
        config = AutoAdvanceConfig(
            pause_on_war=True,
            pause_on_crisis=True,
            pause_on_defcon_change=True,
            pause_on_nuclear=True,
            pause_on_player_attacked=True,
            pause_on_player_mentioned=False,
            min_event_importance=4,
            watch_countries=[],
            days_per_batch=7,
            max_days=30
        )
        return self.advance_days(
            world, config, process_tick_fn, timeline, event_pool, player_id
        )

    def _event_to_dict(self, event: Event) -> Dict[str, Any]:
        """Convert Event to dictionary"""
        return {
            "id": event.id,
            "type": event.type,
            "title": event.title,
            "title_fr": event.title_fr,
            "description": event.description,
            "description_fr": event.description_fr,
            "country_id": event.country_id,
            "target_id": event.target_id,
            "year": event.year,
        }

    def _timeline_event_to_dict(self, te: TimelineEvent) -> Dict[str, Any]:
        """Convert TimelineEvent to dictionary"""
        return {
            "id": te.id,
            "date": te.date.to_display_day("en") if te.date else "",
            "date_fr": te.date.to_display_day("fr") if te.date else "",
            "type": te.type.value if te.type else "",
            "title": te.title,
            "title_fr": te.title_fr,
            "actor_country": te.actor_country,
            "importance": te.importance,
        }


# Global auto-advance engine instance
auto_advance_engine = AutoAdvanceEngine()
