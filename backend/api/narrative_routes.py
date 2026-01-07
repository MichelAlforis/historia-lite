"""API Routes for Historia Narrative mode (PaxHistoria-style)

Endpoints for the narrative gameplay loop:

LEGACY (turn-by-turn):
1. /parse - Parse player text input
2. /actions - Generate actions from intentions
3. /confirm - Confirm and execute actions

PAXHISTORIA (new):
4. /queue-action - Add action to queue (POST)
5. /queue-action/{id} - Remove action from queue (DELETE)
6. /queue-preview - Get what-if preview (GET)
7. /jump-forward - Trigger jump forward (POST)
8. /event/next - Get next event in playback (POST)
9. /event/save - Save at current event (POST)
10. /event/intervene - Stop playback and intervene (POST)

COMMON:
- /state - Get current game state
- /diplomacy - Diplomatic interactions
- /zones - Get zones info
"""
import logging
from typing import List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from engine.narrative_state import (
    NarrativeWorldState,
    TurnPhase,
    GamePhase,
    PendingAction,
    create_initial_state,
)
from engine.action_queue import ActionQueue, QueuedAction, create_queued_action
from engine.jump_engine import JumpEngine, create_jump_engine
from engine.intent_parser import IntentParser, ParseResult, ParsedIntention
from engine.action_generator import ActionGenerator, GeneratedAction
from engine.adversary_ai import AdversaryAI, AIAction
from engine.stop_moment import get_stop_moment_for_reason
from engine.council_suggestions import detect_urgent_dossiers, UrgentDossier
from api.game_state import get_ollama, get_settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/narrative", tags=["narrative"])

# Global game state for narrative mode
_narrative_state: Optional[NarrativeWorldState] = None
_intent_parser: Optional[IntentParser] = None
_action_generator: Optional[ActionGenerator] = None
_adversary_ai: Optional[AdversaryAI] = None
_jump_engine: Optional[JumpEngine] = None


def get_narrative_state() -> NarrativeWorldState:
    """Get or create narrative game state"""
    global _narrative_state
    if _narrative_state is None:
        _narrative_state = create_initial_state()
    return _narrative_state


def get_intent_parser() -> IntentParser:
    """Get or create intent parser"""
    global _intent_parser
    if _intent_parser is None:
        ollama = get_ollama()
        _intent_parser = IntentParser(ollama)
    return _intent_parser


def get_action_generator() -> ActionGenerator:
    """Get or create action generator"""
    global _action_generator
    if _action_generator is None:
        _action_generator = ActionGenerator()
    return _action_generator


def get_adversary_ai() -> AdversaryAI:
    """Get or create adversary AI"""
    global _adversary_ai
    if _adversary_ai is None:
        ollama = get_ollama()
        _adversary_ai = AdversaryAI(ollama)
    return _adversary_ai


def get_jump_engine() -> JumpEngine:
    """Get or create jump engine"""
    global _jump_engine
    if _jump_engine is None:
        adversary_ai = get_adversary_ai()
        _jump_engine = create_jump_engine(adversary_ai)
    return _jump_engine


# =============================================================================
# REQUEST/RESPONSE MODELS
# =============================================================================

class ParseRequest(BaseModel):
    """Request to parse player input"""
    text: str
    use_ollama: bool = True


class ParseResponse(BaseModel):
    """Response with parsed intentions"""
    original_text: str
    intentions: List[dict]
    unrecognized: List[str]
    warnings: List[str]
    count: int


class ActionsRequest(BaseModel):
    """Request to generate actions from intentions"""
    intention_ids: List[str]


class ActionsResponse(BaseModel):
    """Response with generated actions"""
    actions: List[dict]
    total_cost: int
    warnings: List[str]


class ConfirmRequest(BaseModel):
    """Request to confirm actions"""
    action_ids: List[str]


class TurnResponse(BaseModel):
    """Response after processing a turn"""
    turn: int
    date_display: str
    player_actions_executed: List[dict]
    adversary_actions: List[dict]
    events: List[dict]
    state_changes: dict
    narrative_summary: str
    narrative_summary_fr: str
    game_over: bool
    victory: Optional[bool] = None
    end_reason: Optional[str] = None


class StateResponse(BaseModel):
    """Response with current game state"""
    state: dict


class NewGameRequest(BaseModel):
    """Request to start a new game"""
    scenario: str = "cuban_missile_crisis"
    difficulty: str = "normal"


class DiplomacyRequest(BaseModel):
    """Request for diplomatic action"""
    target: str
    message: str
    tone: str = "neutral"  # friendly, neutral, threatening


class DiplomacyResponse(BaseModel):
    """Response from diplomatic exchange"""
    accepted: bool
    response_message: str
    response_message_fr: str
    effects: dict


# =============================================================================
# PAXHISTORIA REQUEST/RESPONSE MODELS
# =============================================================================

class QueueActionRequest(BaseModel):
    """Request to add action to queue"""
    intention_type: str
    intention_id: str
    description_fr: str
    political_cost: int = 0
    risk_level: str = "low"
    target_zone: Optional[str] = None
    target_actor: Optional[str] = None
    predicted_effects: dict = Field(default_factory=dict)
    source_text: str = ""


class QueueActionResponse(BaseModel):
    """Response after adding action to queue"""
    success: bool
    message: str
    action_id: Optional[str] = None
    queue_summary: dict


class QueuePreviewResponse(BaseModel):
    """Response with queue preview state"""
    queue_summary: dict
    predicted_effects: dict
    available_capital: int


class JumpForwardRequest(BaseModel):
    """Request to trigger jump forward"""
    duration: str = "month"  # week, month, quarter, year, next_event


class JumpForwardResponse(BaseModel):
    """Response after jump forward"""
    success: bool
    events_count: int
    first_event: Optional[dict] = None
    game_phase: str
    # "Moment de Verite" - pourquoi le monde s'est arrete
    stop_reason: Optional[str] = None
    stop_moment: Optional[dict] = None


class EventResponse(BaseModel):
    """Response with current event"""
    event: Optional[dict]
    index: int
    total: int
    remaining: int
    can_save: bool
    can_intervene: bool


class InterveneResponse(BaseModel):
    """Response after intervening during playback"""
    success: bool
    cancelled_events_count: int
    game_phase: str


class CouncilSuggestionsResponse(BaseModel):
    """Response with council suggestions (urgent dossiers)"""
    dossiers: List[dict]
    count: int
    has_critical: bool
    game_phase: str


# =============================================================================
# ENDPOINTS
# =============================================================================

@router.post("/new", response_model=StateResponse)
async def new_game(request: NewGameRequest):
    """Start a new narrative game"""
    global _narrative_state

    _narrative_state = create_initial_state()
    logger.info(f"New narrative game started: {request.scenario}")

    return StateResponse(state=_narrative_state.get_visible_state())


@router.get("/state", response_model=StateResponse)
async def get_state():
    """Get current game state"""
    state = get_narrative_state()
    return StateResponse(state=state.get_visible_state())


@router.post("/parse", response_model=ParseResponse)
async def parse_input(request: ParseRequest):
    """Parse player's natural language input into intentions"""
    state = get_narrative_state()
    parser = get_intent_parser()
    settings = get_settings()

    use_ollama = request.use_ollama and settings.ai_mode == "ollama"

    result = await parser.parse(request.text, use_ollama=use_ollama)

    # Store parsed intentions in state for later use
    state.current_phase = TurnPhase.INTENT_REVIEW

    return ParseResponse(
        original_text=result.original_text,
        intentions=[i.to_dict() for i in result.intentions],
        unrecognized=result.unrecognized,
        warnings=result.warnings,
        count=len(result.intentions),
    )


@router.post("/actions", response_model=ActionsResponse)
async def generate_actions(request: ActionsRequest):
    """Generate concrete actions from intentions"""
    state = get_narrative_state()
    parser = get_intent_parser()
    generator = get_action_generator()

    # Get intentions from parser cache or rebuild
    # For now, parse again if needed
    all_actions = []
    total_cost = 0
    warnings = []

    # Generate action for each intention
    for intent_id in request.intention_ids:
        # Find intention (in real impl, cache these)
        for pending in state.pending_actions:
            if pending.intention_id == intent_id:
                # Already have action
                all_actions.append({
                    "id": pending.id,
                    "type": pending.intention_type,
                    "description_fr": pending.description_fr,
                    "political_cost": pending.political_cost,
                    "risk_level": pending.risk_level,
                })
                total_cost += pending.political_cost

    # Check capacity
    if total_cost > state.player.political_capital:
        warnings.append(f"Capital politique insuffisant ({state.player.political_capital}/{total_cost})")

    state.current_phase = TurnPhase.ACTION_CONFIRM

    return ActionsResponse(
        actions=all_actions,
        total_cost=total_cost,
        warnings=warnings,
    )


@router.post("/confirm", response_model=TurnResponse)
async def confirm_actions(request: ConfirmRequest):
    """Confirm actions and process the turn"""
    state = get_narrative_state()
    adversary_ai = get_adversary_ai()
    settings = get_settings()

    use_ollama = settings.ai_mode == "ollama"

    # Mark actions as confirmed
    player_actions = []
    for action_id in request.action_ids:
        for pending in state.pending_actions:
            if pending.id == action_id:
                pending.confirmed = True
                player_actions.append(pending)

    # Execute player actions
    executed_actions = []
    state_changes = {}

    for action in player_actions:
        result = _execute_player_action(action, state)
        executed_actions.append(result)
        _merge_state_changes(state_changes, result.get("changes", {}))

    # Adversary turn
    state.current_phase = TurnPhase.ADVERSARY_TURN
    adversary_actions = await adversary_ai.decide_turn(state, use_ollama=use_ollama)

    adversary_results = []
    for ai_action in adversary_actions:
        result = _execute_adversary_action(ai_action, state)
        adversary_results.append(result)
        _merge_state_changes(state_changes, result.get("changes", {}))

    # Resolution phase
    state.current_phase = TurnPhase.RESOLUTION
    events = _resolve_turn(state)

    # Check victory conditions
    end_condition = state.check_victory_conditions()

    # Generate narrative summary
    narrative = _generate_narrative_summary(
        executed_actions, adversary_results, events, state
    )

    # Advance to next turn
    if not state.game_over:
        state.next_turn()

    return TurnResponse(
        turn=state.turn,
        date_display=state.get_date_display("fr"),
        player_actions_executed=[
            {"id": a.id, "type": a.intention_type, "result": "executed"}
            for a in player_actions
        ],
        adversary_actions=[
            {
                "type": a.action_type.value,
                "target": a.target_zone or a.target_country,
                "visible": a.visible_to_player,
                "description_fr": a.reason_fr if a.visible_to_player else "Action secrete",
            }
            for a in adversary_actions
        ],
        events=events,
        state_changes=state_changes,
        narrative_summary=narrative.get("en", ""),
        narrative_summary_fr=narrative.get("fr", ""),
        game_over=state.game_over,
        victory=state.victory if state.game_over else None,
        end_reason=state.end_reason,
    )


@router.post("/diplomacy", response_model=DiplomacyResponse)
async def diplomatic_exchange(request: DiplomacyRequest):
    """Engage in diplomatic exchange with another country"""
    state = get_narrative_state()
    adversary_ai = get_adversary_ai()

    target = request.target.upper()
    if target not in ["USSR", "CHN", "GBR", "FRA"]:
        raise HTTPException(status_code=400, detail=f"Invalid diplomatic target: {target}")

    # Get diplomacy profile
    diplo = state.player.get_diplomacy_with(target)

    # Determine response based on tone and current relations
    if request.tone == "threatening":
        # Update diplomacy
        diplo.update_from_action("threat", True)
        accepted = False
        response = "L'URSS rejette categoriquement cette provocation."

    elif request.tone == "friendly":
        # More likely to accept
        acceptance_chance = 0.5 + (diplo.trust / 200) + (diplo.respect / 200)
        accepted = acceptance_chance > 0.5
        if accepted:
            diplo.update_from_action("promise_kept", True)
            response = "L'URSS est disposee a poursuivre le dialogue."
        else:
            response = "L'URSS reste mefiante mais n'exclut pas de futures discussions."

    else:
        # Neutral
        accepted = diplo.trust > 40
        response = "L'URSS prend note de cette communication."

    # AI might react
    if request.tone == "threatening":
        reaction = adversary_ai.react_to_player_action("threat", target, state)
        if reaction:
            state.events_queue.append({
                "type": "adversary_reaction",
                "action": reaction.action_type.value,
                "description_fr": reaction.reason_fr,
            })

    return DiplomacyResponse(
        accepted=accepted,
        response_message=response,
        response_message_fr=response,
        effects={
            "trust": diplo.trust,
            "fear": diplo.fear,
            "respect": diplo.respect,
            "leverage": diplo.leverage,
        },
    )


@router.get("/zones")
async def get_zones():
    """Get all zones with current state"""
    state = get_narrative_state()
    zones = []

    for zone_id, zone in state.zones.items():
        zones.append({
            "id": zone.id,
            "name_fr": zone.name_fr,
            "name_en": zone.name_en,
            "influence_us": zone.influence_us,
            "influence_ussr": zone.influence_ussr,
            "control_us": zone.control_us,
            "control_ussr": zone.control_ussr,
            "stability": zone.stability,
            "strategic_value": zone.strategic_value,
            "dominant": zone.get_dominant_power(),
            "instability_risk": zone.get_instability_risk(),
            "has_crisis": zone.has_crisis,
            "crisis_type": zone.crisis_type,
        })

    return {"zones": zones}


@router.get("/adversary")
async def get_adversary_info():
    """Get visible adversary information (based on intel)"""
    state = get_narrative_state()
    return state._get_adversary_visible()


@router.post("/intel/{target}")
async def collect_intel(target: str, depth: str = "surface"):
    """Collect intelligence on a target"""
    state = get_narrative_state()

    # Calculate exposure cost
    depth_costs = {"surface": 5, "detailed": 15, "deep": 30}
    exposure_cost = depth_costs.get(depth, 10)

    # Update player exposure
    state.player.intel_exposure = min(100, state.player.intel_exposure + exposure_cost)

    # Improve intel level
    current_level = state.intel.intel_levels.get(target, 0)
    gain = {"surface": 10, "detailed": 20, "deep": 35}.get(depth, 10)
    new_level = min(100, current_level + gain)
    state.intel.intel_levels[target] = new_level

    return {
        "target": target,
        "previous_level": current_level,
        "new_level": new_level,
        "exposure_cost": exposure_cost,
        "total_exposure": state.player.intel_exposure,
    }


# =============================================================================
# PAXHISTORIA ENDPOINTS
# =============================================================================

@router.post("/queue-action", response_model=QueueActionResponse)
async def queue_action(request: QueueActionRequest):
    """Add action to the queue (PaxHistoria-style)

    Actions are accumulated before Jump Forward, not immediately executed.
    Political capital is reserved when queueing.
    """
    state = get_narrative_state()

    # Check game phase
    if state.game_phase != GamePhase.ACCUMULATING:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot queue actions in phase: {state.game_phase.value}"
        )

    # Create queued action
    action = create_queued_action(
        intention_type=request.intention_type,
        intention_id=request.intention_id,
        description_fr=request.description_fr,
        political_cost=request.political_cost,
        risk_level=request.risk_level,
        target_zone=request.target_zone,
        target_actor=request.target_actor,
        predicted_effects=request.predicted_effects,
        source_text=request.source_text,
    )

    # Add to queue
    success, message = state.queue_action(action.model_dump())

    queue = state.get_action_queue()

    return QueueActionResponse(
        success=success,
        message=message,
        action_id=action.id if success else None,
        queue_summary=queue.get_queue_summary(),
    )


@router.delete("/queue-action/{action_id}", response_model=QueueActionResponse)
async def remove_queued_action(action_id: str):
    """Remove action from queue"""
    state = get_narrative_state()

    if state.game_phase != GamePhase.ACCUMULATING:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot modify queue in phase: {state.game_phase.value}"
        )

    success, message = state.remove_queued_action(action_id)
    queue = state.get_action_queue()

    return QueueActionResponse(
        success=success,
        message=message,
        action_id=action_id if success else None,
        queue_summary=queue.get_queue_summary(),
    )


@router.get("/queue-preview", response_model=QueuePreviewResponse)
async def get_queue_preview():
    """Get preview of what would happen if Jump Forward is triggered now"""
    state = get_narrative_state()
    preview = state.get_queue_preview()

    return QueuePreviewResponse(
        queue_summary=preview["queue_summary"],
        predicted_effects=preview["predicted_effects"],
        available_capital=preview["available_capital"],
    )


@router.get("/council-suggestions", response_model=CouncilSuggestionsResponse)
async def get_council_suggestions():
    """Get council suggestions - urgent dossiers to address BEFORE jump

    Le "Conseil des urgences" presente les dossiers brulants:
    - Crises actives (zones instables)
    - Opportunites (zones contestees)
    - Pressions internes (domestic stability basse)
    - Sommets possibles (diplomatie)
    - Menaces imminentes (DEFCON bas)

    Chaque dossier propose 2-3 suggestions d'actions.
    Cliquer une suggestion = pre-remplir la queue (pas executer).

    Philosophie: "Le joueur prepare ses decisions pendant que
    le monde prepare ses consequences."
    """
    state = get_narrative_state()

    # Seulement en phase ACCUMULATING
    if state.game_phase != GamePhase.ACCUMULATING:
        return CouncilSuggestionsResponse(
            dossiers=[],
            count=0,
            has_critical=False,
            game_phase=state.game_phase.value,
        )

    # Detecter les dossiers urgents
    dossiers = detect_urgent_dossiers(state)

    # Convertir en dict pour la reponse
    dossiers_dict = [d.to_dict() for d in dossiers]

    # Verifier s'il y a des dossiers critiques
    has_critical = any(d.urgency.value == "critical" for d in dossiers)

    return CouncilSuggestionsResponse(
        dossiers=dossiers_dict,
        count=len(dossiers),
        has_critical=has_critical,
        game_phase=state.game_phase.value,
    )


@router.post("/jump-forward", response_model=JumpForwardResponse)
async def jump_forward(request: JumpForwardRequest):
    """Trigger Jump Forward - resolve all queued actions and generate events

    This is the core PaxHistoria mechanic:
    1. Player accumulates actions in queue
    2. Player clicks Jump Forward
    3. All actions (player + adversary) are resolved
    4. Events are generated
    5. Player reads events one by one (Save/Intervene)

    Le "Moment de Verite" est genere en analysant POURQUOI le jeu s'arrete:
    - Guerre declaree? "Le premier coup de feu a ete tire."
    - Crise? "Le telephone rouge sonne."
    - DEFCON change? "Les silos s'ouvrent."

    SILENCE MECHANICS:
    - Queue vide = le joueur n'a rien fait = le monde avance sans lui
    - Les acteurs autonomes (Politburo, Pentagon...) peuvent agir
    - "L'Histoire n'attend pas que le chef d'Etat soit inspire"
    """
    state = get_narrative_state()
    jump_engine = get_jump_engine()

    if state.game_phase != GamePhase.ACCUMULATING:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot jump forward in phase: {state.game_phase.value}"
        )

    queue = state.get_action_queue()
    action_count = len(queue.get_active_actions())

    # SILENCE MECHANICS: Tracker l'activite du joueur
    # Queue vide = le joueur n'a rien fait = le monde avance sans lui
    # Queue non-vide = reset du silence_streak
    silence_events = []
    silence_events_objs = state.check_silence_consequences(
        action_count=action_count,
        ignored_dossier_ids=[]  # TODO: tracker les dossiers ignores
    )

    # Convertir en dicts pour l'affichage
    for se in silence_events_objs:
        silence_events.append({
            "type": "silence_consequence",
            "category": "autonomous_action",
            "title_fr": se.title_fr,
            "description_fr": se.description_fr,
            "actor": se.actor.value if hasattr(se, 'actor') and se.actor else None,
            "event_type": se.type.value,
            "effects": se.effects,
            "importance": "major" if se.type.value in ["fait_accompli", "loss_of_control"] else "normal",
        })

    if silence_events:
        logger.info(f"Silence mechanics: {len(silence_events)} events from player inactivity")

    # Ensure adversary has planned
    adversary_ai = get_adversary_ai()
    if not state.adversary_planned:
        await adversary_ai.plan_turn(state, use_ollama=False)

    # Start jump
    state.start_jump(request.duration)

    # Execute jump and generate events using JumpEngine
    jump_events = await jump_engine.execute_jump(state, request.duration)

    # Convert to dicts for storage
    events = [e.to_dict() for e in jump_events]

    # Ajouter les evenements de silence AU DEBUT (ils se sont passes pendant l'inaction)
    if silence_events:
        events = silence_events + events

    # Determiner la raison d'arret principale (pour le "Moment de Verite")
    stop_reason = _determine_stop_reason(events, state)
    stop_moment = None
    if stop_reason:
        stop_moment = get_stop_moment_for_reason(
            stop_reason,
            context={
                "defcon": state.defcon,
                "tension": state.world_tension,
                "year": state.year,
                "month": state.month,
            }
        )

    # Start playback
    state.start_playback(events)

    return JumpForwardResponse(
        success=True,
        events_count=len(events),
        first_event=events[0] if events else None,
        game_phase=state.game_phase.value,
        stop_reason=stop_reason,
        stop_moment=stop_moment,
    )


@router.post("/event/next", response_model=EventResponse)
async def next_event():
    """Get next event in playback sequence"""
    state = get_narrative_state()

    if state.game_phase != GamePhase.PLAYBACK:
        raise HTTPException(
            status_code=400,
            detail=f"Not in playback mode (current: {state.game_phase.value})"
        )

    playback = state.get_playback_state()

    # Check if more events
    if playback["remaining"] <= 0:
        # End playback
        state.end_playback()
        return EventResponse(
            event=None,
            index=playback["current_index"],
            total=playback["total_events"],
            remaining=0,
            can_save=False,
            can_intervene=False,
        )

    # Get next event
    event = state.next_event()
    playback = state.get_playback_state()

    return EventResponse(
        event=event,
        index=playback["current_index"],
        total=playback["total_events"],
        remaining=playback["remaining"],
        can_save=True,
        can_intervene=playback["remaining"] > 0,
    )


@router.post("/event/save")
async def save_at_event():
    """Save game at current event during playback"""
    state = get_narrative_state()

    if state.game_phase != GamePhase.PLAYBACK:
        raise HTTPException(
            status_code=400,
            detail=f"Not in playback mode (current: {state.game_phase.value})"
        )

    state.save_here()

    return {
        "success": True,
        "saved_at_event": state.saved_at_event,
        "message": f"Partie sauvegardee a l'evenement {state.saved_at_event}",
    }


@router.post("/event/intervene", response_model=InterveneResponse)
async def intervene():
    """Stop playback and intervene - allows player to react immediately"""
    state = get_narrative_state()

    if state.game_phase != GamePhase.PLAYBACK:
        raise HTTPException(
            status_code=400,
            detail=f"Not in playback mode (current: {state.game_phase.value})"
        )

    cancelled = state.intervene()

    return InterveneResponse(
        success=True,
        cancelled_events_count=len(cancelled),
        game_phase=state.game_phase.value,
    )


async def _generate_jump_events(
    state: NarrativeWorldState,
    duration: str
) -> List[dict]:
    """Generate events for jump forward (stub - will be expanded in jump_engine.py)

    This is a placeholder that creates basic events.
    The full implementation will be in engine/jump_engine.py
    """
    events = []

    queue = state.get_action_queue()
    adversary_ai = get_adversary_ai()
    settings = get_settings()

    # Process player actions
    for action in queue.get_active_actions():
        events.append({
            "type": "player_action",
            "category": action.intention_type.split("_")[0],
            "title_fr": action.description_fr,
            "description_fr": f"Vous avez execute: {action.description_fr}",
            "effects": action.predicted_effects,
            "risk_level": action.risk_level,
            "target_zone": action.target_zone,
            "target_actor": action.target_actor,
        })

    # Get adversary actions
    use_ollama = settings.ai_mode == "ollama"
    adversary_actions = await adversary_ai.decide_turn(state, use_ollama=use_ollama)

    for ai_action in adversary_actions:
        if ai_action.visible_to_player:
            events.append({
                "type": "adversary_action",
                "category": ai_action.action_type.value,
                "title_fr": ai_action.reason_fr,
                "description_fr": f"L'URSS a agi: {ai_action.reason_fr}",
                "effects": ai_action.effects,
                "target_zone": ai_action.target_zone,
            })

    # Add time progression event
    duration_labels = {
        "week": "Une semaine s'ecoule",
        "month": "Un mois s'ecoule",
        "quarter": "Un trimestre s'ecoule",
        "year": "Une annee s'ecoule",
        "next_event": "Le temps avance jusqu'au prochain evenement majeur",
    }

    events.append({
        "type": "time_passage",
        "category": "narrative",
        "title_fr": duration_labels.get(duration, "Le temps passe"),
        "description_fr": f"{duration_labels.get(duration, 'Le temps passe')}...",
        "effects": {},
    })

    # Check for world events
    world_events = _resolve_turn(state)
    for we in world_events:
        events.append({
            "type": "world_event",
            "category": we.get("type", "event"),
            "title_fr": we.get("description_fr", "Evenement"),
            "description_fr": we.get("description_fr", ""),
            "effects": {},
        })

    return events


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def _execute_player_action(action: PendingAction, state: NarrativeWorldState) -> dict:
    """Execute a confirmed player action"""
    result = {
        "id": action.id,
        "type": action.intention_type,
        "success": True,
        "changes": {},
    }

    # Spend political capital
    state.player.spend_capital(action.political_cost)
    result["changes"]["political_capital"] = -action.political_cost

    # Apply zone effects if applicable
    if action.target_zone and action.target_zone in state.zones:
        zone = state.zones[action.target_zone]

        # Simple effect application based on action type
        if "REINFORCE" in action.intention_type:
            zone.control_us = min(100, zone.control_us + 15)
            zone.influence_us = min(100, zone.influence_us + 5)
            state.world_tension = min(100, state.world_tension + 10)

        elif "WITHDRAW" in action.intention_type:
            zone.control_us = max(0, zone.control_us - 15)
            state.world_tension = max(0, state.world_tension - 10)

        elif "DESTAB" in action.intention_type:
            zone.stability = max(0, zone.stability - 15)
            zone.influence_ussr = max(0, zone.influence_ussr - 10)

        elif "PROPAGANDA" in action.intention_type:
            zone.influence_us = min(100, zone.influence_us + 5)
            zone.influence_ussr = max(0, zone.influence_ussr - 5)

        result["changes"]["zone_" + action.target_zone] = "modified"

    # Apply diplomacy effects if applicable
    if action.target_actor and action.target_actor in ["USSR", "CHN", "GBR", "FRA"]:
        diplo = state.player.get_diplomacy_with(action.target_actor)

        if "THREAT" in action.intention_type:
            diplo.update_from_action("threat", True)
        elif "NEGOTIATE" in action.intention_type:
            diplo.update_from_action("promise_kept", True)
        elif "SANCTION" in action.intention_type:
            diplo.update_from_action("sanction", True)

    return result


def _execute_adversary_action(action: AIAction, state: NarrativeWorldState) -> dict:
    """Execute an adversary AI action"""
    result = {
        "type": action.action_type.value,
        "target": action.target_zone or action.target_country,
        "visible": action.visible_to_player,
        "changes": {},
    }

    # Apply effects
    for effect_name, delta in action.effects.items():
        if "influence_ussr" in effect_name and action.target_zone:
            zone = state.zones.get(action.target_zone)
            if zone:
                zone.influence_ussr = max(0, min(100, zone.influence_ussr + delta))

        elif "influence_us" in effect_name and action.target_zone:
            zone = state.zones.get(action.target_zone)
            if zone:
                zone.influence_us = max(0, min(100, zone.influence_us + delta))

        elif "control_ussr" in effect_name and action.target_zone:
            zone = state.zones.get(action.target_zone)
            if zone:
                zone.control_ussr = max(0, min(100, zone.control_ussr + delta))

        elif "stability" in effect_name and action.target_zone:
            zone = state.zones.get(action.target_zone)
            if zone:
                zone.stability = max(0, min(100, zone.stability + delta))

        elif "world_tension" in effect_name:
            state.world_tension = max(0, min(100, state.world_tension + delta))

        elif "defcon" in effect_name:
            state.defcon = max(1, min(5, state.defcon + delta))

        elif "fear_usa" in effect_name:
            diplo = state.player.get_diplomacy_with("USSR")
            diplo.fear = max(0, min(100, diplo.fear + delta))

        elif "trust_usa" in effect_name:
            diplo = state.player.get_diplomacy_with("USSR")
            diplo.trust = max(0, min(100, diplo.trust + delta))

        elif "pressure_" in effect_name:
            var = effect_name.replace("pressure_", "pressure_")
            if hasattr(state.adversary, var):
                current = getattr(state.adversary, var)
                setattr(state.adversary, var, max(0, min(100, current + delta)))

        result["changes"][effect_name] = delta

    return result


def _resolve_turn(state: NarrativeWorldState) -> List[dict]:
    """Resolve end-of-turn events"""
    events = []

    # Check for crisis escalation
    for zone_id, zone in state.zones.items():
        if zone.has_crisis and zone.stability < 30:
            events.append({
                "type": "crisis_escalation",
                "zone": zone_id,
                "description_fr": f"La crise en {zone.name_fr} s'intensifie",
            })
            zone.crisis_intensity = min(100, zone.crisis_intensity + 20)

    # Check DEFCON changes
    if state.world_tension > 80 and state.defcon > 2:
        state.defcon -= 1
        events.append({
            "type": "defcon_change",
            "new_level": state.defcon,
            "description_fr": f"DEFCON abaisse au niveau {state.defcon}",
        })

    elif state.world_tension < 40 and state.defcon < 5:
        state.defcon += 1
        events.append({
            "type": "defcon_change",
            "new_level": state.defcon,
            "description_fr": f"DEFCON releve au niveau {state.defcon}",
        })

    # Stability decay in unstable zones
    for zone_id, zone in state.zones.items():
        if zone.stability < 40 and not zone.has_crisis:
            if zone.stability < 25:
                zone.has_crisis = True
                zone.crisis_type = "instability"
                events.append({
                    "type": "new_crisis",
                    "zone": zone_id,
                    "description_fr": f"Crise d'instabilite en {zone.name_fr}",
                })

    return events


def _merge_state_changes(target: dict, source: dict):
    """Merge state changes dictionaries"""
    for key, value in source.items():
        if key in target and isinstance(value, (int, float)):
            target[key] = target[key] + value
        else:
            target[key] = value


def _generate_narrative_summary(
    player_actions: List,
    adversary_actions: List,
    events: List,
    state: NarrativeWorldState
) -> dict:
    """Generate narrative summary of the turn"""
    date = state.get_date_display("fr")

    # Build French summary
    lines_fr = [f"**{date}**", ""]

    if player_actions:
        lines_fr.append("*Actions americaines:*")
        for action in player_actions[:3]:
            lines_fr.append(f"- {action.get('description_fr', action.get('type', 'Action'))}")
        lines_fr.append("")

    visible_ai = [a for a in adversary_actions if a.get("visible", True)]
    if visible_ai:
        lines_fr.append("*Mouvements sovietiques:*")
        for action in visible_ai[:3]:
            lines_fr.append(f"- {action.get('description_fr', 'Activite detectee')}")
        lines_fr.append("")

    if events:
        lines_fr.append("*Evenements:*")
        for event in events[:3]:
            lines_fr.append(f"- {event.get('description_fr', 'Evenement')}")

    # DEFCON status
    defcon_status = {
        5: "Paix relative",
        4: "Tensions elevees",
        3: "Crise majeure",
        2: "Confrontation imminente",
        1: "Guerre imminente",
    }
    lines_fr.append("")
    lines_fr.append(f"**DEFCON {state.defcon}**: {defcon_status.get(state.defcon, 'Inconnu')}")

    return {
        "fr": "\n".join(lines_fr),
        "en": "",  # Could add English version
    }


def _determine_stop_reason(events: List[dict], state: NarrativeWorldState) -> Optional[str]:
    """
    Determine la raison d'arret principale pour le "Moment de Verite".

    Analyse les evenements generes et determine POURQUOI le monde s'arrete.
    Priorite: nucleaire > guerre > crise > DEFCON > evenement important

    Returns:
        Une cle de stop_reason (ex: "defcon_changed", "war_declared")
        ou None si aucun evenement majeur
    """
    # Priorite des raisons (du plus grave au moins grave)
    REASON_PRIORITY = [
        "nuclear_event",
        "war_declared",
        "player_attacked",
        "defcon_changed",
        "crisis_started",
        "crisis_escalated",
        "player_mentioned",
        "goal_conflict",
        "important_event",
    ]

    detected_reasons = set()

    for event in events:
        event_type = event.get("type", "").lower()
        category = event.get("category", "").lower()
        importance = event.get("importance", "normal")

        # Detecter les evenements nucleaires
        if "nuclear" in event_type or "nuclear" in category:
            detected_reasons.add("nuclear_event")

        # Detecter les guerres
        if "war" in event_type or event_type == "war_declared":
            detected_reasons.add("war_declared")

        # Detecter les attaques sur le joueur
        if "player_attacked" in event_type or (
            event.get("target_actor") == "USA" and "attack" in event_type
        ):
            detected_reasons.add("player_attacked")

        # Detecter les changements DEFCON
        if "defcon" in event_type or "defcon" in category:
            detected_reasons.add("defcon_changed")

        # Detecter les crises
        if "crisis" in event_type:
            if "escalat" in event_type:
                detected_reasons.add("crisis_escalated")
            else:
                detected_reasons.add("crisis_started")

        # Detecter les evenements importants
        if importance in ["critical", "major"]:
            detected_reasons.add("important_event")

    # Retourner la raison la plus prioritaire
    for reason in REASON_PRIORITY:
        if reason in detected_reasons:
            return reason

    # Si aucun evenement majeur, verifier l'etat du monde
    if state.defcon <= 2:
        return "defcon_changed"

    if state.world_tension > 80:
        return "important_event"

    # Fallback: evenement important generique si des evenements existent
    if events and len(events) > 1:
        return "important_event"

    return None


# =============================================================================
# GAME OVER DEBRIEF ENDPOINT
# =============================================================================

class GameOverDebriefResponse(BaseModel):
    """Response with game over debrief"""
    end_reason: str
    victory: bool
    title_fr: str
    narrative_fr: str
    causes: List[dict]
    leader_dialogue: Optional[dict] = None
    press_headlines: List[dict]
    final_state_summary: dict
    ai_errors: List[dict] = []  # Erreurs strategiques de l'IA adversaire


@router.get("/game-over-debrief", response_model=GameOverDebriefResponse)
async def get_game_over_debrief():
    """
    Get narrative debrief for game over.

    Explains WHY the player lost (or won) without showing numbers.
    Just a narrative reading of what happened.

    > "Votre silence sur Cuba a laisse l'armee agir.
    > Votre fermete a Berlin a isole vos allies.
    > Le monde a glisse."

    PHILOSOPHIE:
    - Pas de blame ("vous avez fait X erreurs")
    - Pas de chiffres ("stabilite -45")
    - Juste une lecture historique narrative
    - Le joueur comprend a posteriori, pas pendant

    Returns GameOverDebriefResponse with:
    - title_fr: Dramatic title
    - narrative_fr: Main narrative text
    - causes: List of key decisions that led to the outcome
    - leader_dialogue: Optional dialogue from a leader
    - press_headlines: World press reactions
    - final_state_summary: Narrativized state summary (no numbers!)
    - ai_errors: Strategic errors made by the adversary AI
    """
    state = get_narrative_state()

    if not state.game_over:
        raise HTTPException(
            status_code=400,
            detail="Game is not over yet. Cannot generate debrief."
        )

    # Import debrief generator
    from engine.game_debrief import generate_game_debrief

    # Get silence state for cause analysis
    silence_state = state.get_silence_state()

    # Get adversary AI for error extraction
    adversary_ai = get_adversary_ai()

    # Generate debrief (includes AI errors extraction)
    debrief = await generate_game_debrief(
        world_state=state,
        silence_state=silence_state,
        turn_history=state.turn_history,
        adversary_ai=adversary_ai,
    )

    return GameOverDebriefResponse(
        end_reason=debrief.get("end_reason", "unknown"),
        victory=debrief.get("victory", False),
        title_fr=debrief.get("title_fr", "Fin de partie"),
        narrative_fr=debrief.get("narrative_fr", ""),
        causes=debrief.get("causes", []),
        leader_dialogue=debrief.get("leader_dialogue"),
        press_headlines=debrief.get("press_headlines", []),
        final_state_summary=debrief.get("final_state_summary", {}),
        ai_errors=debrief.get("ai_errors", []),
    )


# =============================================================================
# FRONTS VIVANTS ENDPOINT (v2 - base sur les ACTIONS)
# =============================================================================

class FrontBeatResponse(BaseModel):
    """Beat response (dernier signe marquant)"""
    kind: str
    actor: str
    payload: str
    freshness: int


class FrontStateResponse(BaseModel):
    """Front state for a single zone"""
    zone_id: str
    zone_name_fr: str
    dominant_mode: str      # "soft", "hard", "covert", "standoff"
    tension_band: str       # "low", "medium", "high", "critical"
    spotlight: bool
    has_crisis: bool
    beat: Optional[FrontBeatResponse] = None
    surface_phrase: str
    omen: Optional[str] = None
    badge: Optional[str] = None


class FrontsResponse(BaseModel):
    """Response with all fronts for the FrontWall"""
    fronts: List[FrontStateResponse]
    count: int
    turn: int
    game_phase: str


@router.get("/fronts", response_model=FrontsResponse)
async def get_fronts(max_display: int = 6):
    """
    Get fronts for the FrontWall display.

    Fronts Vivants v2 - base sur les ACTIONS, pas les metriques.

    Chaque front affiche:
    - Beat: le dernier signe marquant (action loggee)
    - Mode dominant: soft/hard/covert/standoff (deduit des actions recentes)
    - Omen: signal faible avant la crise
    - Badge: etiquette visuelle (CRISE, OPERATION, SOMMET, RUMEUR)

    Selection dynamique:
    1. Toujours: fronts en crise
    2. Fronts avec spotlight (action recente joueur/IA)
    3. Completer avec zones strategiques

    Appele par le frontend pour rafraichir le FrontWall:
    - A chaque tour
    - Apres chaque beat du playback
    - Apres un TEST choice
    """
    state = get_narrative_state()

    # Import front_state functions
    from engine.front_state import get_display_fronts

    # Get fronts to display
    display_fronts = get_display_fronts(state, max_display)

    # Convert to response format
    fronts_response = []
    for f in display_fronts:
        beat_response = None
        if f.beat:
            beat_response = FrontBeatResponse(
                kind=f.beat.kind,
                actor=f.beat.actor,
                payload=f.beat.payload,
                freshness=f.beat.freshness,
            )

        fronts_response.append(FrontStateResponse(
            zone_id=f.zone_id,
            zone_name_fr=f.zone_name_fr,
            dominant_mode=f.dominant_mode,
            tension_band=f.tension_band.value,
            spotlight=f.spotlight,
            has_crisis=f.has_crisis,
            beat=beat_response,
            surface_phrase=f.surface_phrase,
            omen=f.omen,
            badge=f.badge,
        ))

    return FrontsResponse(
        fronts=fronts_response,
        count=len(fronts_response),
        turn=state.turn,
        game_phase=state.game_phase.value,
    )
