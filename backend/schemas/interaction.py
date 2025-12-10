"""Pydantic schemas for player interactions: Commands, Projects, Dilemmas"""
from typing import Dict, List, Optional
from pydantic import BaseModel, Field
from enum import Enum


# =============================================================================
# COMMAND SYSTEM - Player orders in natural language
# =============================================================================

class CommandCategory(str, Enum):
    """Categories of player commands"""
    MILITARY = "military"
    DIPLOMATIC = "diplomatic"
    ECONOMIC = "economic"
    PROJECT = "project"
    INTERNAL = "internal"


class CommandAction(str, Enum):
    """Specific actions within categories"""
    # Military
    ATTACK = "attack"
    DEFEND = "defend"
    MOBILIZE = "mobilize"
    DEMOBILIZE = "demobilize"
    # Diplomatic
    PROPOSE_ALLIANCE = "propose_alliance"
    DECLARE_WAR = "declare_war"
    PEACE_OFFER = "peace_offer"
    SANCTIONS = "sanctions"
    LIFT_SANCTIONS = "lift_sanctions"
    # Economic
    TAX_INCREASE = "tax_increase"
    TAX_DECREASE = "tax_decrease"
    INVEST = "invest"
    EMBARGO = "embargo"
    # Project
    START_PROJECT = "start_project"
    CANCEL_PROJECT = "cancel_project"
    ACCELERATE_PROJECT = "accelerate_project"
    # Internal
    REFORM = "reform"
    PROPAGANDA = "propaganda"
    SUPPRESS = "suppress"
    ELECTION = "election"


class CommandRequest(BaseModel):
    """Request to execute a player command"""
    command: str = Field(..., description="Natural language command from player")
    player_country_id: str = Field(..., description="ID of the player's country")


class CommandInterpretation(BaseModel):
    """Result of interpreting a natural language command"""
    category: CommandCategory
    action: CommandAction
    target_country_id: Optional[str] = None
    target_project_id: Optional[str] = None
    parameters: Dict = Field(default_factory=dict)
    confidence: float = Field(default=1.0, ge=0, le=1)


class CommandCost(BaseModel):
    """Costs associated with executing a command"""
    economy: int = 0
    military: int = 0
    stability: int = 0
    soft_power: int = 0
    technology: int = 0


class CommandResponse(BaseModel):
    """Response after interpreting a command"""
    command_id: str
    original_command: str
    interpreted_as: str
    interpretation: CommandInterpretation
    feasible: bool
    feasibility_reason: Optional[str] = None
    cost: CommandCost
    requires_confirmation: bool = True
    confirmation_message: str = ""
    confirmation_message_fr: str = ""
    executed: bool = False
    events: List[Dict] = Field(default_factory=list)


class CommandConfirmRequest(BaseModel):
    """Request to confirm and execute a pending command"""
    command_id: str
    player_country_id: str


# =============================================================================
# PROJECT SYSTEM - Long-term objectives
# =============================================================================

class ProjectType(str, Enum):
    """Types of long-term projects"""
    SPACE = "space"
    NUCLEAR = "nuclear"
    MILITARY = "military"
    ECONOMIC = "economic"
    INFRASTRUCTURE = "infrastructure"
    TECHNOLOGY = "technology"
    SOCIAL = "social"


class SocialTag(str, Enum):
    """Social sensitivity tags for projects that may cause reactions"""
    LGBTQ_RIGHTS = "lgbtq_rights"      # Same-sex marriage, anti-discrimination
    SECULAR = "secular"                 # Separation of religion and state
    PROGRESSIVE = "progressive"         # Progressive social policies
    CONSERVATIVE = "conservative"       # Traditional values
    RELIGIOUS = "religious"             # Religious-based policies
    WOMEN_RIGHTS = "women_rights"       # Gender equality, abortion rights
    IMMIGRATION = "immigration"         # Open immigration policies
    NATIONALIST = "nationalist"         # Nationalist/protectionist policies
    ENVIRONMENTAL = "environmental"     # Green policies that may hurt economy
    MILITARY_BUILDUP = "military_buildup"  # May concern neighbors


class ProjectMilestone(BaseModel):
    """Milestone within a project"""
    at_progress: int = Field(..., ge=0, le=100, description="Progress percentage to trigger")
    event_type: str
    title: str
    title_fr: str
    description: str
    description_fr: str


class ProjectTemplate(BaseModel):
    """Template for a project type"""
    id: str
    name: str
    name_fr: str
    type: ProjectType
    total_years: int = Field(..., ge=1, le=20)
    economy_cost_per_year: int = Field(..., ge=0, le=20)
    technology_required: int = Field(default=0, ge=0, le=100)
    completion_effects: Dict[str, int] = Field(default_factory=dict)
    milestones: List[ProjectMilestone] = Field(default_factory=list)
    description: str = ""
    description_fr: str = ""
    # Social sensitivity tags - can cause internal/external reactions
    social_tags: List[SocialTag] = Field(default_factory=list)


class ActiveProject(BaseModel):
    """An active project being worked on by a country"""
    id: str
    template_id: str
    name: str
    name_fr: str
    type: ProjectType
    country_id: str

    # Progress
    progress: int = Field(default=0, ge=0, le=100)
    years_active: int = 0
    total_years: int

    # Costs
    economy_cost_per_year: int
    total_invested: int = 0

    # Status
    status: str = "active"  # active, paused, completed, cancelled, sabotaged
    sabotaged: bool = False
    accelerated: bool = False

    # Milestones reached
    milestones_reached: List[int] = Field(default_factory=list)

    # Completion effects
    completion_effects: Dict[str, int] = Field(default_factory=dict)

    # Social tags for reactions
    social_tags: List[SocialTag] = Field(default_factory=list)


class ProjectResponse(BaseModel):
    """Response with project details"""
    project: ActiveProject
    next_milestone: Optional[ProjectMilestone] = None
    years_remaining: int
    completion_year: int


class ProjectListResponse(BaseModel):
    """List of projects for a country"""
    country_id: str
    active_projects: List[ActiveProject]
    available_projects: List[ProjectTemplate]


class CustomProjectRequest(BaseModel):
    """Request to create a custom player-defined project"""
    name: str = Field(..., min_length=3, max_length=100, description="Project name in English")
    name_fr: str = Field(..., min_length=3, max_length=100, description="Project name in French")
    description: str = Field(..., min_length=10, max_length=500, description="Description in English")
    description_fr: str = Field(..., min_length=10, max_length=500, description="Description in French")
    project_type: ProjectType = Field(..., description="Type of project (social, economic, etc.)")
    total_years: int = Field(..., ge=1, le=15, description="Duration in years (1-15)")
    economy_cost_per_year: int = Field(..., ge=1, le=10, description="Annual cost (1-10)")
    completion_effects: Dict[str, int] = Field(
        ...,
        description="Effects when completed. Keys: economy, military, stability, soft_power, technology, resources, nuclear. Values: -20 to +30"
    )
    technology_required: int = Field(default=0, ge=0, le=80, description="Minimum technology level required")
    social_tags: List[SocialTag] = Field(
        default_factory=list,
        description="Social sensitivity tags that may cause reactions. Examples: lgbtq_rights, women_rights, religious, secular"
    )


# =============================================================================
# DILEMMA SYSTEM - Critical decisions with 3 choices
# =============================================================================

class DilemmaType(str, Enum):
    """Types of dilemmas that can occur"""
    # Economic
    ECONOMIC_CRISIS = "economic_crisis"
    BUDGET_SHORTAGE = "budget_shortage"
    # Military
    WAR_DECLARATION = "war_declaration"
    ALLY_ATTACKED = "ally_attacked"
    NUCLEAR_THREAT = "nuclear_threat"
    # Stability
    REVOLUTION_RISK = "revolution_risk"
    COUP_ATTEMPT = "coup_attempt"
    # Diplomatic
    ULTIMATUM_RECEIVED = "ultimatum_received"
    ALLIANCE_REQUEST = "alliance_request"
    SANCTIONS_IMPOSED = "sanctions_imposed"
    # Project
    PROJECT_MILESTONE = "project_milestone"
    PROJECT_SABOTAGE = "project_sabotage"


class DilemmaChoice(BaseModel):
    """One of the 3 choices for a dilemma"""
    id: int = Field(..., ge=1, le=3)
    label: str
    label_fr: str
    description: str
    description_fr: str

    # Effects
    effects: Dict[str, int] = Field(default_factory=dict)
    relation_effects: Dict[str, int] = Field(default_factory=dict)

    # Consequences
    triggers_event: Optional[str] = None
    starts_project: Optional[str] = None
    ends_war: bool = False
    declares_war: Optional[str] = None


class DilemmaTemplate(BaseModel):
    """Template for a dilemma"""
    id: str
    type: DilemmaType
    title: str
    title_fr: str
    description: str
    description_fr: str
    choices: List[DilemmaChoice] = Field(..., min_length=3, max_length=3)

    # Trigger conditions (stored as strings for flexibility)
    trigger_condition: str = ""

    # Optional expiration
    expires_after_years: Optional[int] = None
    auto_choice: Optional[int] = None


class ActiveDilemma(BaseModel):
    """An active dilemma awaiting player decision"""
    id: str
    template_id: str
    type: DilemmaType
    title: str
    title_fr: str
    description: str
    description_fr: str
    country_id: str
    year_triggered: int

    # Context data
    trigger_data: Dict = Field(default_factory=dict)
    related_country_id: Optional[str] = None
    related_project_id: Optional[str] = None

    # Choices
    choices: List[DilemmaChoice]

    # Expiration
    expires_at_year: Optional[int] = None
    auto_choice: Optional[int] = None

    # Status
    status: str = "pending"  # pending, resolved, expired
    chosen_option: Optional[int] = None


class DilemmaResolveRequest(BaseModel):
    """Request to resolve a dilemma"""
    dilemma_id: str
    player_country_id: str
    choice_id: int = Field(..., ge=1, le=3)


class DilemmaResolveResponse(BaseModel):
    """Response after resolving a dilemma"""
    dilemma_id: str
    choice_made: DilemmaChoice
    effects_applied: Dict[str, int]
    relation_changes: Dict[str, int]
    events_triggered: List[Dict]
    message: str
    message_fr: str


class PendingDilemmasResponse(BaseModel):
    """List of pending dilemmas for a country"""
    country_id: str
    pending_dilemmas: List[ActiveDilemma]
    count: int


class DilemmaHistoryResponse(BaseModel):
    """History of resolved dilemmas"""
    country_id: str
    resolved_dilemmas: List[ActiveDilemma]
    total: int


# =============================================================================
# SUMMIT SYSTEM - Multi-country negotiations
# =============================================================================

class SummitType(str, Enum):
    """Types of international summits"""
    BILATERAL = "bilateral"
    REGIONAL = "regional"
    ALLIANCE = "alliance"
    PEACE = "peace"
    ECONOMIC = "economic"


class SummitProposal(BaseModel):
    """A proposal within a summit"""
    id: str
    proposer_id: str
    type: str
    title: str
    title_fr: str
    details: Dict = Field(default_factory=dict)
    supporters: List[str] = Field(default_factory=list)
    opponents: List[str] = Field(default_factory=list)
    required_majority: float = 0.5


class SecretDeal(BaseModel):
    """A secret agreement between countries"""
    id: str
    parties: List[str]
    type: str  # vote_together, share_intel, mutual_support
    public: bool = False
    discovery_chance: float = 0.1
    effects: Dict = Field(default_factory=dict)
    scandal_effects: Dict = Field(default_factory=dict)


class Summit(BaseModel):
    """An international summit"""
    id: str
    type: SummitType
    host_country_id: str
    participants: List[str]
    agenda: List[str] = Field(default_factory=list)

    # State
    status: str = "proposed"  # proposed, accepted, in_progress, concluded, failed
    current_round: int = 0
    max_rounds: int = 3

    # Proposals and votes
    proposals: List[SummitProposal] = Field(default_factory=list)
    votes: Dict[str, Dict[str, str]] = Field(default_factory=dict)

    # Secret deals
    secret_deals: List[SecretDeal] = Field(default_factory=list)

    # Year
    year_started: int = 0


class SummitCreateRequest(BaseModel):
    """Request to create a new summit"""
    host_country_id: str
    type: SummitType
    participants: List[str]
    agenda: List[str] = Field(default_factory=list)


class SummitResponse(BaseModel):
    """Response with summit details"""
    summit: Summit
    player_proposals: List[str]
    available_actions: List[str]
