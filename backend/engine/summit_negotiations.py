"""Summit Negotiations System

Handles:
- Pre-summit negotiations and lobbying
- Coalition building between countries
- Vote trading (quid pro quo)
- Resolution proposals
- Diplomatic consequences of votes
"""
import logging
import random
from typing import TYPE_CHECKING, Dict, List, Optional, Tuple
from enum import Enum
from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from engine.world import World
    from engine.country import Country

logger = logging.getLogger(__name__)


class VotePosition(str, Enum):
    """Possible vote positions"""
    STRONGLY_FOR = "strongly_for"
    FOR = "for"
    ABSTAIN = "abstain"
    AGAINST = "against"
    STRONGLY_AGAINST = "strongly_against"


class ResolutionTopic(str, Enum):
    """Topics for summit resolutions"""
    CLIMATE = "climate"
    TRADE = "trade"
    SANCTIONS = "sanctions"
    MILITARY = "military"
    HUMAN_RIGHTS = "human_rights"
    ECONOMIC_AID = "economic_aid"
    NUCLEAR = "nuclear"
    TERRORISM = "terrorism"
    MIGRATION = "migration"
    TECHNOLOGY = "technology"


class Resolution(BaseModel):
    """A resolution to be voted on at a summit"""
    id: str
    title: str
    title_fr: str
    description: str
    description_fr: str
    topic: ResolutionTopic
    proposer_country: str
    target_country: Optional[str] = None  # For sanctions, aid, etc.
    vote_type: str = "majority"  # majority, supermajority, unanimity
    effects_if_passed: Dict = Field(default_factory=dict)
    effects_if_failed: Dict = Field(default_factory=dict)


class VoteDeal(BaseModel):
    """A vote trading deal between countries"""
    id: str
    proposer: str  # Country proposing the deal
    target: str  # Country receiving the proposal
    resolution_id: str
    requested_vote: VotePosition
    offered_compensation: Dict = Field(default_factory=dict)
    # Compensation can be: relation_boost, economic_aid, vote_promise, tech_share
    status: str = "pending"  # pending, accepted, rejected, fulfilled
    year_proposed: int = 0


class Coalition(BaseModel):
    """A temporary coalition for a specific summit/issue"""
    id: str
    name: str
    name_fr: str
    leader: str
    members: List[str] = Field(default_factory=list)
    target_resolution: Optional[str] = None
    position: VotePosition = VotePosition.FOR
    summit_id: str
    year_formed: int = 0
    is_active: bool = True


class CountryVoteIntent(BaseModel):
    """A country's voting intention for a resolution"""
    country_id: str
    resolution_id: str
    initial_position: VotePosition
    current_position: VotePosition
    lobbied_by: List[str] = Field(default_factory=list)
    deals_accepted: List[str] = Field(default_factory=list)
    position_strength: int = 50  # 0-100, how firmly they hold their position


class NegotiationManager:
    """Manages pre-summit negotiations"""

    def __init__(self):
        self.active_resolutions: Dict[str, Resolution] = {}
        self.vote_intents: Dict[str, Dict[str, CountryVoteIntent]] = {}  # resolution_id -> {country_id -> intent}
        self.pending_deals: Dict[str, VoteDeal] = {}
        self.active_coalitions: Dict[str, Coalition] = {}
        self.deal_history: List[VoteDeal] = []

    def propose_resolution(
        self,
        summit_id: str,
        proposer: "Country",
        topic: ResolutionTopic,
        title: str,
        title_fr: str,
        description: str,
        description_fr: str,
        target_country: Optional[str] = None,
        effects: Dict = None,
        vote_type: str = "majority"
    ) -> Resolution:
        """Propose a new resolution for a summit"""
        resolution_id = f"{summit_id}_{proposer.id}_{topic.value}_{random.randint(1000, 9999)}"

        resolution = Resolution(
            id=resolution_id,
            title=title,
            title_fr=title_fr,
            description=description,
            description_fr=description_fr,
            topic=topic,
            proposer_country=proposer.id,
            target_country=target_country,
            vote_type=vote_type,
            effects_if_passed=effects or {}
        )

        self.active_resolutions[resolution_id] = resolution
        logger.info(f"{proposer.id} proposed resolution: {title}")
        return resolution

    def calculate_initial_position(
        self,
        country: "Country",
        resolution: Resolution,
        world: "World"
    ) -> Tuple[VotePosition, int]:
        """Calculate a country's initial voting position based on interests"""
        base_support = 50
        strength = 50

        # Topic-based adjustments
        topic_modifiers = self._get_topic_modifiers(country, resolution.topic)
        base_support += topic_modifiers["support"]
        strength += topic_modifiers["strength"]

        # Relation with proposer
        if resolution.proposer_country in country.relations:
            relation = country.relations[resolution.proposer_country]
            base_support += (relation - 50) // 5  # -10 to +10

        # Relation with target (if sanctions/etc)
        if resolution.target_country:
            if resolution.target_country in country.relations:
                target_relation = country.relations[resolution.target_country]
                # Good relation with target = oppose sanctions
                if resolution.topic == ResolutionTopic.SANCTIONS:
                    base_support -= (target_relation - 50) // 3
                # Good relation = support aid
                elif resolution.topic == ResolutionTopic.ECONOMIC_AID:
                    base_support += (target_relation - 50) // 3

        # Bloc alignment
        from engine.bloc import bloc_manager
        proposer_blocs = set(bloc_manager.get_country_blocs(resolution.proposer_country))
        country_blocs = set(bloc_manager.get_country_blocs(country.id))
        shared_blocs = proposer_blocs & country_blocs

        if shared_blocs:
            # Check for vote coordination
            for bloc_id in shared_blocs:
                bloc = bloc_manager.blocs.get(bloc_id)
                if bloc and bloc.vote_coordination:
                    base_support += 15
                    strength += 10

        # Personality adjustments
        if hasattr(country, 'personality'):
            if country.personality == "aggressive" and resolution.topic == ResolutionTopic.MILITARY:
                base_support += 15
            elif country.personality == "diplomatic" and resolution.topic in [
                ResolutionTopic.HUMAN_RIGHTS, ResolutionTopic.CLIMATE
            ]:
                base_support += 10
            elif country.personality == "isolationist":
                base_support -= 10  # Generally less supportive

        # Convert to position
        position = self._support_to_position(base_support)
        strength = max(10, min(90, strength))

        return position, strength

    def _get_topic_modifiers(self, country: "Country", topic: ResolutionTopic) -> Dict:
        """Get support modifiers based on topic and country characteristics"""
        modifiers = {"support": 0, "strength": 0}

        if topic == ResolutionTopic.CLIMATE:
            # Rich countries more supportive, resource exporters less
            if country.economy > 70:
                modifiers["support"] += 10
            if country.resources > 70:
                modifiers["support"] -= 15
                modifiers["strength"] += 20

        elif topic == ResolutionTopic.TRADE:
            # Export-oriented economies more supportive
            if country.economy > 60:
                modifiers["support"] += 10

        elif topic == ResolutionTopic.SANCTIONS:
            # Depends heavily on target, handled elsewhere
            modifiers["strength"] += 10

        elif topic == ResolutionTopic.MILITARY:
            # Military powers more supportive of military resolutions
            if country.military > 70:
                modifiers["support"] += 15
            modifiers["strength"] += 15

        elif topic == ResolutionTopic.HUMAN_RIGHTS:
            # Democracies more supportive
            if hasattr(country, 'regime') and country.regime in ["democracy", "constitutional_monarchy"]:
                modifiers["support"] += 20
            else:
                modifiers["support"] -= 10
                modifiers["strength"] += 20

        elif topic == ResolutionTopic.NUCLEAR:
            # Nuclear powers defensive about nuclear issues
            if hasattr(country, 'nuclear') and country.nuclear > 0:
                modifiers["support"] -= 10
                modifiers["strength"] += 30

        return modifiers

    def _support_to_position(self, support: int) -> VotePosition:
        """Convert support score to vote position"""
        if support >= 80:
            return VotePosition.STRONGLY_FOR
        elif support >= 60:
            return VotePosition.FOR
        elif support >= 40:
            return VotePosition.ABSTAIN
        elif support >= 20:
            return VotePosition.AGAINST
        else:
            return VotePosition.STRONGLY_AGAINST

    def initialize_vote_intents(
        self,
        resolution: Resolution,
        participants: List[str],
        world: "World"
    ):
        """Initialize voting intentions for all participants"""
        self.vote_intents[resolution.id] = {}

        for country_id in participants:
            country = world.get_country(country_id)
            if not country:
                continue

            position, strength = self.calculate_initial_position(country, resolution, world)

            intent = CountryVoteIntent(
                country_id=country_id,
                resolution_id=resolution.id,
                initial_position=position,
                current_position=position,
                position_strength=strength
            )
            self.vote_intents[resolution.id][country_id] = intent

    def lobby_country(
        self,
        lobbyer: "Country",
        target: "Country",
        resolution_id: str,
        desired_position: VotePosition,
        soft_power_cost: int = 5
    ) -> Tuple[bool, str]:
        """Attempt to influence a country's vote through lobbying"""
        if resolution_id not in self.vote_intents:
            return False, "Resolution non trouvee"

        if target.id not in self.vote_intents[resolution_id]:
            return False, "Pays non participant"

        intent = self.vote_intents[resolution_id][target.id]

        # Check if already lobbied by this country
        if lobbyer.id in intent.lobbied_by:
            return False, "Deja fait du lobbying aupres de ce pays"

        # Calculate success chance
        success_chance = self._calculate_lobby_success(lobbyer, target, intent, desired_position)

        # Apply soft power cost
        lobbyer.soft_power = max(0, lobbyer.soft_power - soft_power_cost)

        # Roll for success
        roll = random.randint(1, 100)
        intent.lobbied_by.append(lobbyer.id)

        if roll <= success_chance:
            # Shift position towards desired
            old_position = intent.current_position
            intent.current_position = self._shift_position(
                intent.current_position, desired_position
            )
            intent.position_strength = max(20, intent.position_strength - 10)

            logger.info(f"{lobbyer.id} successfully lobbied {target.id}: {old_position} -> {intent.current_position}")
            return True, f"Lobbying reussi: {target.name_fr} passe de {old_position.value} a {intent.current_position.value}"
        else:
            logger.info(f"{lobbyer.id} failed to lobby {target.id}")
            return False, f"Lobbying echoue: {target.name_fr} maintient sa position"

    def _calculate_lobby_success(
        self,
        lobbyer: "Country",
        target: "Country",
        intent: CountryVoteIntent,
        desired_position: VotePosition
    ) -> int:
        """Calculate chance of successful lobbying"""
        base_chance = 30

        # Soft power influence
        base_chance += (lobbyer.soft_power - 50) // 2

        # Relation bonus
        if target.id in lobbyer.relations:
            relation = lobbyer.relations.get(target.id, 50)
            base_chance += (relation - 50) // 3

        # Position strength penalty
        base_chance -= intent.position_strength // 3

        # Same bloc bonus
        from engine.bloc import bloc_manager
        lobbyer_blocs = set(bloc_manager.get_country_blocs(lobbyer.id))
        target_blocs = set(bloc_manager.get_country_blocs(target.id))
        if lobbyer_blocs & target_blocs:
            base_chance += 15

        # Distance from desired position (harder to flip completely)
        position_distance = abs(
            self._position_to_int(intent.current_position) -
            self._position_to_int(desired_position)
        )
        base_chance -= position_distance * 5

        return max(5, min(85, base_chance))

    def _position_to_int(self, position: VotePosition) -> int:
        """Convert position to integer for comparison"""
        mapping = {
            VotePosition.STRONGLY_FOR: 2,
            VotePosition.FOR: 1,
            VotePosition.ABSTAIN: 0,
            VotePosition.AGAINST: -1,
            VotePosition.STRONGLY_AGAINST: -2
        }
        return mapping[position]

    def _shift_position(self, current: VotePosition, desired: VotePosition) -> VotePosition:
        """Shift position one step towards desired"""
        current_int = self._position_to_int(current)
        desired_int = self._position_to_int(desired)

        if current_int < desired_int:
            new_int = current_int + 1
        elif current_int > desired_int:
            new_int = current_int - 1
        else:
            return current

        reverse_mapping = {
            2: VotePosition.STRONGLY_FOR,
            1: VotePosition.FOR,
            0: VotePosition.ABSTAIN,
            -1: VotePosition.AGAINST,
            -2: VotePosition.STRONGLY_AGAINST
        }
        return reverse_mapping[new_int]

    def propose_vote_deal(
        self,
        proposer: "Country",
        target: "Country",
        resolution_id: str,
        requested_vote: VotePosition,
        compensation: Dict,
        year: int
    ) -> VoteDeal:
        """Propose a vote trading deal"""
        deal_id = f"deal_{proposer.id}_{target.id}_{resolution_id}_{random.randint(1000, 9999)}"

        deal = VoteDeal(
            id=deal_id,
            proposer=proposer.id,
            target=target.id,
            resolution_id=resolution_id,
            requested_vote=requested_vote,
            offered_compensation=compensation,
            year_proposed=year
        )

        self.pending_deals[deal_id] = deal
        logger.info(f"{proposer.id} proposed vote deal to {target.id}")
        return deal

    def evaluate_deal(
        self,
        deal: VoteDeal,
        target: "Country",
        world: "World"
    ) -> Tuple[bool, str]:
        """AI evaluation of a vote deal"""
        if deal.resolution_id not in self.vote_intents:
            return False, "Resolution non trouvee"

        intent = self.vote_intents[deal.resolution_id].get(target.id)
        if not intent:
            return False, "Intention de vote non trouvee"

        # Calculate deal value
        deal_value = 0
        compensation = deal.offered_compensation

        if "relation_boost" in compensation:
            deal_value += compensation["relation_boost"] * 2
        if "economic_aid" in compensation:
            deal_value += compensation["economic_aid"] * 3
        if "tech_share" in compensation:
            deal_value += compensation["tech_share"] * 4
        if "vote_promise" in compensation:
            deal_value += 20  # Future vote promise

        # Calculate cost of changing position
        position_distance = abs(
            self._position_to_int(intent.current_position) -
            self._position_to_int(deal.requested_vote)
        )
        position_cost = position_distance * 15 + intent.position_strength // 2

        # Decision
        accept_threshold = position_cost - deal_value

        # Personality adjustment
        if hasattr(target, 'personality'):
            if target.personality == "pragmatic":
                accept_threshold -= 20
            elif target.personality == "principled":
                accept_threshold += 30

        roll = random.randint(1, 100)
        if roll > accept_threshold:
            return True, "Accord accepte"
        else:
            return False, "Accord refuse - compensation insuffisante"

    def accept_deal(self, deal_id: str, world: "World") -> bool:
        """Accept a vote deal and apply its effects"""
        deal = self.pending_deals.get(deal_id)
        if not deal:
            return False

        # Update vote intent
        if deal.resolution_id in self.vote_intents:
            intent = self.vote_intents[deal.resolution_id].get(deal.target)
            if intent:
                intent.current_position = deal.requested_vote
                intent.deals_accepted.append(deal_id)

        # Apply immediate compensation
        target = world.get_country(deal.target)
        proposer = world.get_country(deal.proposer)

        if target and proposer:
            comp = deal.offered_compensation
            if "relation_boost" in comp:
                if deal.proposer not in target.relations:
                    target.relations[deal.proposer] = 50
                target.relations[deal.proposer] = min(
                    100, target.relations[deal.proposer] + comp["relation_boost"]
                )
            if "economic_aid" in comp:
                target.economy = min(100, target.economy + comp["economic_aid"])
            if "tech_share" in comp:
                target.technology = min(100, target.technology + comp["tech_share"])

        deal.status = "accepted"
        self.deal_history.append(deal)
        del self.pending_deals[deal_id]

        logger.info(f"Deal {deal_id} accepted")
        return True

    def reject_deal(self, deal_id: str) -> bool:
        """Reject a vote deal"""
        deal = self.pending_deals.get(deal_id)
        if not deal:
            return False

        deal.status = "rejected"
        self.deal_history.append(deal)
        del self.pending_deals[deal_id]

        logger.info(f"Deal {deal_id} rejected")
        return True

    def form_coalition(
        self,
        leader: "Country",
        resolution_id: str,
        position: VotePosition,
        summit_id: str,
        year: int,
        name: str = None,
        name_fr: str = None
    ) -> Coalition:
        """Form a coalition for a specific resolution"""
        coalition_id = f"coalition_{leader.id}_{resolution_id}_{random.randint(1000, 9999)}"

        if not name:
            name = f"{leader.name} Coalition"
        if not name_fr:
            name_fr = f"Coalition {leader.name_fr}"

        coalition = Coalition(
            id=coalition_id,
            name=name,
            name_fr=name_fr,
            leader=leader.id,
            members=[leader.id],
            target_resolution=resolution_id,
            position=position,
            summit_id=summit_id,
            year_formed=year
        )

        self.active_coalitions[coalition_id] = coalition
        logger.info(f"Coalition formed: {name}")
        return coalition

    def join_coalition(
        self,
        country: "Country",
        coalition_id: str
    ) -> Tuple[bool, str]:
        """Join an existing coalition"""
        coalition = self.active_coalitions.get(coalition_id)
        if not coalition:
            return False, "Coalition non trouvee"

        if country.id in coalition.members:
            return False, "Deja membre"

        coalition.members.append(country.id)

        # Update vote intent to match coalition position
        if coalition.target_resolution in self.vote_intents:
            intent = self.vote_intents[coalition.target_resolution].get(country.id)
            if intent:
                intent.current_position = coalition.position

        logger.info(f"{country.id} joined coalition {coalition.name}")
        return True, f"Rejoint la coalition {coalition.name_fr}"

    def skip_negotiations(
        self,
        resolution: Resolution,
        participants: List[str],
        world: "World",
        reason: str = "time_constraint"
    ) -> Tuple[bool, Dict]:
        """Skip the negotiation phase and go directly to vote

        Reasons for skipping:
        - time_constraint: Player doesn't have time
        - different_objective: Player has other priorities
        - no_interest: Resolution doesn't affect player
        - auto_vote: AI plays the negotiation automatically

        This initializes vote positions and conducts vote immediately.
        """
        # Initialize all vote positions based on country interests
        for country_id in participants:
            country = world.get_country(country_id)
            if not country:
                continue

            # Calculate initial position
            position, strength = self.calculate_initial_position(country, resolution, world)

            # Store the intent
            if resolution.id not in self.vote_intents:
                self.vote_intents[resolution.id] = {}

            self.vote_intents[resolution.id][country_id] = CountryVoteIntent(
                country_id=country_id,
                resolution_id=resolution.id,
                initial_position=position,
                current_position=position,  # No lobbying, so same as initial
                position_strength=strength,
            )

        # Conduct the vote
        passed, results = self.conduct_vote(resolution, participants, world)

        # Add skip info to results
        results["skipped_negotiations"] = True
        results["skip_reason"] = reason

        logger.info(f"Negotiations skipped for {resolution.id} (reason: {reason})")

        return passed, results

    def auto_negotiate(
        self,
        resolution: Resolution,
        player_country_id: str,
        participants: List[str],
        world: "World",
        rounds: int = 3
    ) -> Dict:
        """Auto-negotiate on behalf of the player (AI plays)

        Simulates multiple rounds of AI negotiation.
        Returns a summary of what happened.
        """
        summary = {
            "lobbying_done": [],
            "deals_proposed": [],
            "deals_accepted": [],
            "coalitions_formed": [],
            "position_changes": [],
        }

        player = world.get_country(player_country_id)
        if not player:
            return summary

        # Initialize positions first
        for country_id in participants:
            country = world.get_country(country_id)
            if not country:
                continue

            position, strength = self.calculate_initial_position(country, resolution, world)

            if resolution.id not in self.vote_intents:
                self.vote_intents[resolution.id] = {}

            self.vote_intents[resolution.id][country_id] = CountryVoteIntent(
                country_id=country_id,
                resolution_id=resolution.id,
                initial_position=position,
                current_position=position,
                position_strength=strength,
            )

        # Get player's position
        player_intent = self.vote_intents[resolution.id].get(player_country_id)
        if not player_intent:
            return summary

        player_position = player_intent.current_position

        # Simulate negotiation rounds
        for round_num in range(rounds):
            # Find countries to lobby (those against player's position)
            for country_id in participants:
                if country_id == player_country_id:
                    continue

                intent = self.vote_intents[resolution.id].get(country_id)
                if not intent:
                    continue

                # Lobby if opposing position and weak
                should_lobby = False
                if player_position in [VotePosition.FOR, VotePosition.STRONGLY_FOR]:
                    if intent.current_position in [VotePosition.AGAINST, VotePosition.STRONGLY_AGAINST]:
                        should_lobby = intent.position_strength < 60
                elif player_position in [VotePosition.AGAINST, VotePosition.STRONGLY_AGAINST]:
                    if intent.current_position in [VotePosition.FOR, VotePosition.STRONGLY_FOR]:
                        should_lobby = intent.position_strength < 60

                if should_lobby and player.soft_power >= 5:
                    # Attempt lobby
                    success, msg = self.lobby_country(
                        player,
                        world.get_country(country_id),
                        resolution,
                        player_position,
                        world
                    )
                    summary["lobbying_done"].append({
                        "target": country_id,
                        "success": success,
                        "message": msg,
                    })

                    if success:
                        summary["position_changes"].append(country_id)

        return summary

    def conduct_vote(
        self,
        resolution: Resolution,
        participants: List[str],
        world: "World"
    ) -> Tuple[bool, Dict]:
        """Conduct the final vote on a resolution"""
        results = {
            "resolution_id": resolution.id,
            "votes": {},
            "for": 0,
            "against": 0,
            "abstain": 0,
            "passed": False,
            "vote_type": resolution.vote_type
        }

        intents = self.vote_intents.get(resolution.id, {})

        for country_id in participants:
            intent = intents.get(country_id)
            if intent:
                position = intent.current_position
            else:
                # Default to abstain if no intent calculated
                position = VotePosition.ABSTAIN

            results["votes"][country_id] = position.value

            if position in [VotePosition.STRONGLY_FOR, VotePosition.FOR]:
                results["for"] += 1
            elif position in [VotePosition.STRONGLY_AGAINST, VotePosition.AGAINST]:
                results["against"] += 1
            else:
                results["abstain"] += 1

        # Determine if passed
        total_voting = results["for"] + results["against"]
        if total_voting == 0:
            results["passed"] = False
        elif resolution.vote_type == "majority":
            results["passed"] = results["for"] > results["against"]
        elif resolution.vote_type == "supermajority":
            results["passed"] = results["for"] >= (total_voting * 2 / 3)
        elif resolution.vote_type == "unanimity":
            results["passed"] = results["against"] == 0

        logger.info(f"Resolution {resolution.id}: {'PASSED' if results['passed'] else 'FAILED'}")
        return results["passed"], results

    def apply_vote_consequences(
        self,
        resolution: Resolution,
        vote_results: Dict,
        world: "World"
    ):
        """Apply diplomatic consequences based on votes"""
        proposer = world.get_country(resolution.proposer_country)
        if not proposer:
            return

        for country_id, vote in vote_results["votes"].items():
            if country_id == resolution.proposer_country:
                continue

            country = world.get_country(country_id)
            if not country:
                continue

            # Update relations based on vote
            if country_id not in proposer.relations:
                proposer.relations[country_id] = 50

            if vote in ["strongly_for", "for"]:
                proposer.relations[country_id] = min(100, proposer.relations[country_id] + 5)
            elif vote in ["strongly_against", "against"]:
                proposer.relations[country_id] = max(0, proposer.relations[country_id] - 8)

        # Apply resolution effects if passed
        if vote_results["passed"]:
            self._apply_resolution_effects(resolution, world)

    def _apply_resolution_effects(self, resolution: Resolution, world: "World"):
        """Apply effects of a passed resolution"""
        effects = resolution.effects_if_passed

        if resolution.target_country:
            target = world.get_country(resolution.target_country)
            if target:
                for effect_key, value in effects.items():
                    if hasattr(target, effect_key):
                        current = getattr(target, effect_key)
                        setattr(target, effect_key, max(0, min(100, current + value)))

        # Global effects
        if "global_tension" in effects:
            world.global_tension = max(0, min(100, world.global_tension + effects["global_tension"]))
        if "oil_price" in effects:
            world.oil_price = max(20, min(200, world.oil_price + effects["oil_price"]))

    def get_vote_prediction(self, resolution_id: str) -> Dict:
        """Get current vote prediction for a resolution"""
        if resolution_id not in self.vote_intents:
            return {"error": "Resolution not found"}

        prediction = {"for": 0, "against": 0, "abstain": 0, "details": {}}

        for country_id, intent in self.vote_intents[resolution_id].items():
            position = intent.current_position
            prediction["details"][country_id] = {
                "position": position.value,
                "strength": intent.position_strength,
                "lobbied_by": intent.lobbied_by
            }

            if position in [VotePosition.STRONGLY_FOR, VotePosition.FOR]:
                prediction["for"] += 1
            elif position in [VotePosition.STRONGLY_AGAINST, VotePosition.AGAINST]:
                prediction["against"] += 1
            else:
                prediction["abstain"] += 1

        return prediction

    def clear_summit_data(self, summit_id: str):
        """Clear negotiation data for a completed summit"""
        # Remove resolutions for this summit
        to_remove = [
            rid for rid in self.active_resolutions
            if rid.startswith(summit_id)
        ]
        for rid in to_remove:
            del self.active_resolutions[rid]
            if rid in self.vote_intents:
                del self.vote_intents[rid]

        # Deactivate coalitions
        for coalition in self.active_coalitions.values():
            if coalition.summit_id == summit_id:
                coalition.is_active = False


# Global instance
negotiation_manager = NegotiationManager()
