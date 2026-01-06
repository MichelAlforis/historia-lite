"""
Nation Agenda System for Historia Lite

Each nation has strategic goals that they actively pursue.
When goals CONFLICT between nations, tension rises automatically.
This creates emergent drama without scripted events.
"""
import json
import logging
import random
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Tuple, TYPE_CHECKING

from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from engine.world import World
    from engine.country import Country

logger = logging.getLogger(__name__)


class GoalType(str, Enum):
    """Types of strategic goals nations can pursue"""
    TERRITORIAL = "territorial"       # Annex/reunify territory (Taiwan, Kashmir)
    HEGEMONY = "hegemony"            # Regional/global dominance
    NUCLEAR = "nuclear"              # Become/remain nuclear power
    ECONOMIC = "economic"            # Economic dominance (trade, resources)
    ALLIANCE = "alliance"            # Build/maintain alliance bloc
    REVENGE = "revenge"              # Avenge historical humiliation
    DEFENSE = "defense"              # Protect self/ally from threat
    IDEOLOGY = "ideology"            # Spread regime type/ideology
    RESOURCE = "resource"            # Control strategic resources (oil, chips)
    STABILITY = "stability"          # Internal consolidation


class GoalStatus(str, Enum):
    """Status of a strategic goal"""
    DORMANT = "dormant"              # Not actively pursued
    ACTIVE = "active"                # Being actively pursued
    BLOCKED = "blocked"              # Cannot progress (external factor)
    ACHIEVED = "achieved"            # Goal completed
    ABANDONED = "abandoned"          # Given up on goal


class ConflictIntensity(str, Enum):
    """How severely two goals conflict"""
    NONE = "none"                    # No conflict
    MINOR = "minor"                  # Diplomatic friction
    MODERATE = "moderate"            # Active opposition
    MAJOR = "major"                  # Near-war tension
    EXISTENTIAL = "existential"      # One must destroy the other


class StrategicGoal(BaseModel):
    """A single strategic goal for a nation"""
    id: str
    type: GoalType
    name: str
    name_fr: str
    description: str = ""
    description_fr: str = ""

    # Progress tracking
    progress: int = Field(default=0, ge=0, le=100)
    status: GoalStatus = GoalStatus.ACTIVE
    priority: int = Field(default=3, ge=1, le=5)  # 5 = highest

    # Target specification
    target_countries: List[str] = Field(default_factory=list)
    target_regions: List[str] = Field(default_factory=list)
    target_resources: List[str] = Field(default_factory=list)

    # Requirements and blockers
    required_stats: Dict[str, int] = Field(default_factory=dict)
    blocking_goals: List[str] = Field(default_factory=list)  # Goal IDs that block this
    enabling_goals: List[str] = Field(default_factory=list)  # Goals that help this

    # Tension generation
    tension_per_progress: float = 0.5  # Tension added per progress point
    visibility: int = Field(default=50, ge=0, le=100)  # How visible is this goal

    # Timeline
    deadline_year: Optional[int] = None
    created_year: int = 2025
    created_month: int = 1

    # Era validity
    valid_from_year: int = 1900
    valid_to_year: int = 2100


class GoalConflict(BaseModel):
    """Represents a conflict between two nations' goals"""
    id: str
    goal1_id: str
    goal2_id: str
    country1_id: str
    country2_id: str
    intensity: ConflictIntensity
    tension_level: int = Field(default=0, ge=0, le=100)
    description_fr: str = ""
    flash_point: Optional[str] = None  # e.g., "Taiwan", "Kashmir"

    # Escalation tracking
    incidents_count: int = 0
    last_incident_day: int = 0
    escalation_risk: int = Field(default=10, ge=0, le=100)


class NationAgenda(BaseModel):
    """Complete agenda for a nation"""
    country_id: str
    goals: List[StrategicGoal] = Field(default_factory=list)

    # Behavior modifiers
    patience: int = Field(default=50, ge=0, le=100)      # How long before acting
    opportunism: int = Field(default=50, ge=0, le=100)   # Exploit weakness tendency
    risk_tolerance: int = Field(default=50, ge=0, le=100)
    secrecy: int = Field(default=50, ge=0, le=100)       # Hide goals tendency

    # Historical context
    historical_traumas: List[str] = Field(default_factory=list)
    historical_glories: List[str] = Field(default_factory=list)
    irredentist_claims: List[str] = Field(default_factory=list)

    def get_active_goals(self) -> List[StrategicGoal]:
        """Get all currently active goals"""
        return [g for g in self.goals if g.status == GoalStatus.ACTIVE]

    def get_highest_priority_goal(self) -> Optional[StrategicGoal]:
        """Get the most important active goal"""
        active = self.get_active_goals()
        if not active:
            return None
        return max(active, key=lambda g: g.priority)

    def get_goals_targeting(self, country_id: str) -> List[StrategicGoal]:
        """Get goals that target a specific country"""
        return [g for g in self.goals if country_id in g.target_countries]


# ============================================================================
# GOAL CONFLICT DETECTION - This is where the magic happens
# ============================================================================

# Pre-defined conflicting goal pairs
CONFLICTING_GOAL_TYPES: List[Tuple[str, str, ConflictIntensity]] = [
    # Territorial conflicts
    ("CHN_reunify_taiwan", "USA_defend_taiwan", ConflictIntensity.EXISTENTIAL),
    ("CHN_reunify_taiwan", "JPN_taiwan_security", ConflictIntensity.MAJOR),
    ("RUS_ukraine_sphere", "USA_nato_expansion", ConflictIntensity.MAJOR),
    ("RUS_ukraine_sphere", "UKR_sovereignty", ConflictIntensity.EXISTENTIAL),
    ("IND_kashmir", "PAK_kashmir", ConflictIntensity.EXISTENTIAL),
    ("ISR_security", "IRN_destroy_israel", ConflictIntensity.EXISTENTIAL),
    ("IRN_regional_hegemony", "SAU_regional_hegemony", ConflictIntensity.MAJOR),
    ("TUR_neo_ottoman", "GRC_aegean", ConflictIntensity.MODERATE),
    ("PRK_reunification", "KOR_reunification", ConflictIntensity.MAJOR),

    # Resource conflicts
    ("CHN_south_china_sea", "VNM_maritime_rights", ConflictIntensity.MODERATE),
    ("CHN_south_china_sea", "PHL_maritime_rights", ConflictIntensity.MODERATE),
    ("EGY_nile_water", "ETH_renaissance_dam", ConflictIntensity.MAJOR),

    # Hegemony conflicts
    ("USA_global_hegemony", "CHN_global_power", ConflictIntensity.MAJOR),
    ("USA_indo_pacific", "CHN_belt_road", ConflictIntensity.MODERATE),
    ("RUS_arctic_control", "USA_arctic_presence", ConflictIntensity.MODERATE),

    # Alliance conflicts
    ("RUS_destabilize_nato", "USA_strengthen_nato", ConflictIntensity.MAJOR),
    ("CHN_break_quad", "USA_strengthen_quad", ConflictIntensity.MODERATE),
]


class AgendaManager:
    """Manages all nation agendas and detects conflicts"""

    def __init__(self):
        self.agendas: Dict[str, NationAgenda] = {}
        self.active_conflicts: Dict[str, GoalConflict] = {}
        self._conflict_definitions = {
            (pair[0], pair[1]): pair[2] for pair in CONFLICTING_GOAL_TYPES
        }

    def load_agendas(self, data_path: Path) -> None:
        """Load nation agendas from JSON file"""
        agenda_file = data_path / "nation_agendas.json"
        if not agenda_file.exists():
            logger.warning(f"Nation agendas file not found: {agenda_file}")
            return

        with open(agenda_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        for agenda_data in data.get("agendas", []):
            country_id = agenda_data.get("country_id")
            if not country_id:
                continue

            goals = []
            for goal_data in agenda_data.get("goals", []):
                goal = StrategicGoal(**goal_data)
                goals.append(goal)

            agenda = NationAgenda(
                country_id=country_id,
                goals=goals,
                patience=agenda_data.get("patience", 50),
                opportunism=agenda_data.get("opportunism", 50),
                risk_tolerance=agenda_data.get("risk_tolerance", 50),
                secrecy=agenda_data.get("secrecy", 50),
                historical_traumas=agenda_data.get("historical_traumas", []),
                historical_glories=agenda_data.get("historical_glories", []),
                irredentist_claims=agenda_data.get("irredentist_claims", []),
            )
            self.agendas[country_id] = agenda

        logger.info(f"Loaded {len(self.agendas)} nation agendas")

    def get_agenda(self, country_id: str) -> Optional[NationAgenda]:
        """Get agenda for a country"""
        return self.agendas.get(country_id)

    def detect_all_conflicts(self, world: "World") -> List[GoalConflict]:
        """Detect all active goal conflicts between nations"""
        conflicts = []

        # Check all known conflicting pairs
        for (goal1_id, goal2_id), intensity in self._conflict_definitions.items():
            country1_id = goal1_id.split("_")[0]
            country2_id = goal2_id.split("_")[0]

            agenda1 = self.agendas.get(country1_id)
            agenda2 = self.agendas.get(country2_id)

            if not agenda1 or not agenda2:
                continue

            # Find the actual goals
            goal1 = next((g for g in agenda1.goals if g.id == goal1_id), None)
            goal2 = next((g for g in agenda2.goals if g.id == goal2_id), None)

            if not goal1 or not goal2:
                continue

            # Only count if both goals are active
            if goal1.status != GoalStatus.ACTIVE or goal2.status != GoalStatus.ACTIVE:
                continue

            # Calculate tension based on progress
            tension = self._calculate_conflict_tension(goal1, goal2, intensity, world)

            conflict_id = f"{goal1_id}_vs_{goal2_id}"
            conflict = GoalConflict(
                id=conflict_id,
                goal1_id=goal1_id,
                goal2_id=goal2_id,
                country1_id=country1_id,
                country2_id=country2_id,
                intensity=intensity,
                tension_level=tension,
                description_fr=self._generate_conflict_description(goal1, goal2, intensity),
                flash_point=self._identify_flash_point(goal1, goal2),
            )
            conflicts.append(conflict)

        return conflicts

    def _calculate_conflict_tension(
        self,
        goal1: StrategicGoal,
        goal2: StrategicGoal,
        intensity: ConflictIntensity,
        world: "World"
    ) -> int:
        """Calculate tension level from conflicting goals"""
        # Base tension from intensity
        base_tension = {
            ConflictIntensity.NONE: 0,
            ConflictIntensity.MINOR: 15,
            ConflictIntensity.MODERATE: 35,
            ConflictIntensity.MAJOR: 55,
            ConflictIntensity.EXISTENTIAL: 75,
        }[intensity]

        # Add tension from goal progress (both sides pushing = more tension)
        progress_tension = (goal1.progress + goal2.progress) // 4

        # Add tension from priority (high priority = more commitment)
        priority_tension = (goal1.priority + goal2.priority) * 2

        # World tension multiplier
        world_multiplier = 1.0 + (world.global_tension - 50) / 100

        total = int((base_tension + progress_tension + priority_tension) * world_multiplier)
        return min(100, max(0, total))

    def _generate_conflict_description(
        self,
        goal1: StrategicGoal,
        goal2: StrategicGoal,
        intensity: ConflictIntensity
    ) -> str:
        """Generate a description of the conflict"""
        intensity_words = {
            ConflictIntensity.MINOR: "friction diplomatique",
            ConflictIntensity.MODERATE: "opposition active",
            ConflictIntensity.MAJOR: "tensions graves",
            ConflictIntensity.EXISTENTIAL: "conflit existentiel",
        }
        word = intensity_words.get(intensity, "tensions")
        return f"{word} - {goal1.name_fr} vs {goal2.name_fr}"

    def _identify_flash_point(
        self,
        goal1: StrategicGoal,
        goal2: StrategicGoal
    ) -> Optional[str]:
        """Identify the geographic/thematic flash point"""
        # Check for common targets
        common_countries = set(goal1.target_countries) & set(goal2.target_countries)
        if common_countries:
            return list(common_countries)[0]

        common_regions = set(goal1.target_regions) & set(goal2.target_regions)
        if common_regions:
            return list(common_regions)[0]

        return None

    def process_conflicts(self, world: "World") -> List[dict]:
        """Process all conflicts and generate events/tensions"""
        events = []
        conflicts = self.detect_all_conflicts(world)

        for conflict in conflicts:
            # Update global tension
            tension_contribution = conflict.tension_level // 10
            world.global_tension = min(100, world.global_tension + tension_contribution // 30)

            # Check for incident generation
            if self._should_generate_incident(conflict, world):
                event = self._generate_conflict_incident(conflict, world)
                if event:
                    events.append(event)
                    conflict.incidents_count += 1
                    conflict.last_incident_day = world.total_days_elapsed

            # Store/update conflict
            self.active_conflicts[conflict.id] = conflict

        return events

    def _should_generate_incident(self, conflict: GoalConflict, world: "World") -> bool:
        """Determine if a conflict should generate an incident"""
        # More tension = more likely
        base_chance = conflict.tension_level / 1000  # 0-10% base

        # Time since last incident
        days_since = world.total_days_elapsed - conflict.last_incident_day
        time_factor = min(2.0, days_since / 30)  # Up to 2x after 30 days

        # Intensity multiplier
        intensity_mult = {
            ConflictIntensity.MINOR: 0.5,
            ConflictIntensity.MODERATE: 1.0,
            ConflictIntensity.MAJOR: 1.5,
            ConflictIntensity.EXISTENTIAL: 2.0,
        }.get(conflict.intensity, 1.0)

        final_chance = base_chance * time_factor * intensity_mult

        return random.random() < final_chance

    def _generate_conflict_incident(
        self,
        conflict: GoalConflict,
        world: "World"
    ) -> Optional[dict]:
        """Generate an incident event from a conflict"""
        incident_types = {
            ConflictIntensity.MINOR: [
                "diplomatic_note", "media_criticism", "trade_friction"
            ],
            ConflictIntensity.MODERATE: [
                "ambassador_recalled", "sanctions_threat", "military_exercise"
            ],
            ConflictIntensity.MAJOR: [
                "border_incident", "cyber_attack", "proxy_clash"
            ],
            ConflictIntensity.EXISTENTIAL: [
                "military_mobilization", "ultimatum", "skirmish"
            ],
        }

        types = incident_types.get(conflict.intensity, ["diplomatic_tension"])
        incident_type = random.choice(types)

        # Update escalation risk
        conflict.escalation_risk = min(100, conflict.escalation_risk + 5)

        return {
            "type": "goal_conflict_incident",
            "incident_type": incident_type,
            "conflict_id": conflict.id,
            "country1": conflict.country1_id,
            "country2": conflict.country2_id,
            "flash_point": conflict.flash_point,
            "tension_level": conflict.tension_level,
            "escalation_risk": conflict.escalation_risk,
            "date": world.current_date.model_dump(),
        }

    def progress_goal(
        self,
        country_id: str,
        goal_id: str,
        amount: int,
        world: "World"
    ) -> List[dict]:
        """Progress a goal and check for cascade effects"""
        events = []
        agenda = self.agendas.get(country_id)
        if not agenda:
            return events

        goal = next((g for g in agenda.goals if g.id == goal_id), None)
        if not goal:
            return events

        old_progress = goal.progress
        goal.progress = min(100, max(0, goal.progress + amount))

        # Check if this triggers tension with conflicting goals
        for conflict in self.active_conflicts.values():
            if conflict.goal1_id == goal_id or conflict.goal2_id == goal_id:
                # Increase tension
                tension_increase = int(amount * goal.tension_per_progress)
                conflict.tension_level = min(100, conflict.tension_level + tension_increase)

                # Log tension increase
                events.append({
                    "type": "goal_progress_tension",
                    "country_id": country_id,
                    "goal_id": goal_id,
                    "old_progress": old_progress,
                    "new_progress": goal.progress,
                    "conflict_id": conflict.id,
                    "tension_increase": tension_increase,
                    "new_tension": conflict.tension_level,
                })

        # Check for goal completion
        if goal.progress >= 100 and old_progress < 100:
            goal.status = GoalStatus.ACHIEVED
            events.append({
                "type": "goal_achieved",
                "country_id": country_id,
                "goal_id": goal_id,
                "goal_name_fr": goal.name_fr,
            })

        return events


# ============================================================================
# CHAIN REACTION SYSTEM - Actions trigger consequences
# ============================================================================

class ChainReaction(BaseModel):
    """A chain of events triggered by an action"""
    id: str
    trigger_action: str              # What started this chain
    trigger_country: str
    target_country: Optional[str] = None

    # Chain of events
    events: List[dict] = Field(default_factory=list)
    current_step: int = 0
    total_steps: int = 0

    # Timing
    days_between_steps: int = 3
    next_step_day: int = 0

    # State
    is_active: bool = True
    outcome: Optional[str] = None


class ChainReactionManager:
    """Manages chain reactions from major actions"""

    def __init__(self):
        self.active_chains: Dict[str, ChainReaction] = {}
        self._chain_templates = self._load_chain_templates()

    def _load_chain_templates(self) -> Dict[str, List[dict]]:
        """Define chain reaction templates"""
        return {
            "attack_country": [
                {"step": 1, "type": "defender_mobilizes", "days": 1},
                {"step": 2, "type": "allies_decide", "days": 3},
                {"step": 3, "type": "world_reacts", "days": 5},
                {"step": 4, "type": "war_or_retreat", "days": 7},
            ],
            "nuclear_test": [
                {"step": 1, "type": "world_condemns", "days": 1},
                {"step": 2, "type": "sanctions_proposed", "days": 3},
                {"step": 3, "type": "regional_tension", "days": 5},
                {"step": 4, "type": "arms_race_risk", "days": 10},
            ],
            "alliance_betrayal": [
                {"step": 1, "type": "shock_betrayed_ally", "days": 1},
                {"step": 2, "type": "reputation_damage", "days": 2},
                {"step": 3, "type": "other_allies_doubt", "days": 5},
                {"step": 4, "type": "new_alignments", "days": 10},
            ],
            "economic_sanction": [
                {"step": 1, "type": "target_protests", "days": 1},
                {"step": 2, "type": "target_retaliates", "days": 3},
                {"step": 3, "type": "third_parties_choose", "days": 7},
                {"step": 4, "type": "economic_damage", "days": 14},
            ],
            "covert_operation": [
                {"step": 1, "type": "operation_executed", "days": 1},
                {"step": 2, "type": "discovery_risk", "days": 7},
                {"step": 3, "type": "blame_assigned", "days": 10},
                {"step": 4, "type": "diplomatic_fallout", "days": 14},
            ],
        }

    def trigger_chain(
        self,
        action_type: str,
        trigger_country: str,
        target_country: Optional[str],
        world: "World"
    ) -> Optional[ChainReaction]:
        """Trigger a chain reaction from an action"""
        template = self._chain_templates.get(action_type)
        if not template:
            return None

        chain_id = f"{action_type}_{trigger_country}_{world.year}_{world.month}_{world.day}"
        chain = ChainReaction(
            id=chain_id,
            trigger_action=action_type,
            trigger_country=trigger_country,
            target_country=target_country,
            events=template.copy(),
            total_steps=len(template),
            next_step_day=world.total_days_elapsed + template[0].get("days", 1),
        )

        self.active_chains[chain_id] = chain
        logger.info(f"Chain reaction triggered: {chain_id}")
        return chain

    def process_chains(self, world: "World") -> List[dict]:
        """Process all active chains and generate events"""
        events = []
        current_day = world.total_days_elapsed

        for chain_id, chain in list(self.active_chains.items()):
            if not chain.is_active:
                continue

            if current_day < chain.next_step_day:
                continue

            if chain.current_step >= chain.total_steps:
                chain.is_active = False
                chain.outcome = "completed"
                continue

            # Execute current step
            step = chain.events[chain.current_step]
            event = self._execute_chain_step(chain, step, world)
            if event:
                events.append(event)

            # Move to next step
            chain.current_step += 1
            if chain.current_step < chain.total_steps:
                next_days = chain.events[chain.current_step].get("days", 3)
                chain.next_step_day = current_day + next_days

        return events

    def _execute_chain_step(
        self,
        chain: ChainReaction,
        step: dict,
        world: "World"
    ) -> Optional[dict]:
        """Execute a single step in a chain reaction"""
        step_type = step.get("type", "unknown")

        event = {
            "type": "chain_reaction_step",
            "chain_id": chain.id,
            "step": chain.current_step + 1,
            "total_steps": chain.total_steps,
            "step_type": step_type,
            "trigger_country": chain.trigger_country,
            "target_country": chain.target_country,
            "date": world.current_date.model_dump(),
        }

        # Add step-specific effects
        if step_type == "defender_mobilizes":
            event["description_fr"] = f"{chain.target_country} mobilise ses forces"
        elif step_type == "allies_decide":
            event["description_fr"] = "Les allies evaluent leur reponse"
        elif step_type == "world_condemns":
            event["description_fr"] = "Condamnation internationale"
        elif step_type == "sanctions_proposed":
            event["description_fr"] = "Sanctions en discussion au Conseil de Securite"

        return event


# Global instances
agenda_manager = AgendaManager()
chain_manager = ChainReactionManager()


def initialize_agendas(data_path: Path) -> None:
    """Initialize the agenda system"""
    agenda_manager.load_agendas(data_path)


def get_nation_agenda(country_id: str) -> Optional[NationAgenda]:
    """Get agenda for a country"""
    return agenda_manager.get_agenda(country_id)


def process_agenda_tick(world: "World") -> List[dict]:
    """Process all agendas for one tick"""
    events = []

    # Process goal conflicts
    conflict_events = agenda_manager.process_conflicts(world)
    events.extend(conflict_events)

    # Process chain reactions
    chain_events = chain_manager.process_chains(world)
    events.extend(chain_events)

    return events


def trigger_action_chain(
    action_type: str,
    trigger_country: str,
    target_country: Optional[str],
    world: "World"
) -> Optional[ChainReaction]:
    """Trigger a chain reaction from a player/AI action"""
    return chain_manager.trigger_chain(action_type, trigger_country, target_country, world)
