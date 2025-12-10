"""Economic blocs management system

Handles:
- Loading and managing economic blocs (EU, NATO, BRICS, etc.)
- Calculating economic bonuses for bloc members
- Managing bloc membership (join, leave, apply)
- Defense clauses (NATO Article 5, etc.)
"""
import json
import logging
from pathlib import Path
from typing import TYPE_CHECKING, Dict, List, Optional, Tuple

from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from engine.world import World
    from engine.country import Country

logger = logging.getLogger(__name__)


class EconomicBloc(BaseModel):
    """An economic or political bloc"""
    id: str
    name: str
    name_fr: str
    type: str  # customs_union, free_trade, political, military_alliance, economic_organization
    members: List[str] = Field(default_factory=list)

    # Economic effects
    economy_bonus: int = 0  # Annual bonus for each member
    trade_bonus: int = 0    # Intra-bloc trade bonus
    tariff_external: int = 0  # Tariff on non-members

    # Political effects
    relation_bonus: int = 0   # Relation bonus between members
    vote_coordination: bool = False  # Coordinated voting at UN/summits

    # Leadership
    leader_country: Optional[str] = None
    rotating_presidency: bool = False

    # Military (for alliances)
    defense_clause: bool = False  # Attack on one = attack on all
    tech_sharing: bool = False    # Technology transfer between members

    # Resource control (for OPEC-like)
    controls_resource: Optional[str] = None
    resource_control_power: int = 0  # 0-100

    # Membership
    membership_requirements: Dict = Field(default_factory=dict)
    pending_applications: List[str] = Field(default_factory=list)

    description_fr: str = ""


class BlocManager:
    """Manages all economic and political blocs"""

    def __init__(self):
        self.blocs: Dict[str, EconomicBloc] = {}
        self._load_blocs()

    def _load_blocs(self):
        """Load blocs from JSON file"""
        data_path = Path(__file__).parent.parent / "data" / "blocs.json"
        if not data_path.exists():
            logger.warning("blocs.json not found, using empty blocs")
            return

        with open(data_path, "r", encoding="utf-8") as f:
            blocs_data = json.load(f)

        for bloc_data in blocs_data:
            bloc = EconomicBloc(**bloc_data)
            self.blocs[bloc.id] = bloc

        logger.info(f"Loaded {len(self.blocs)} economic blocs")

    def get_bloc(self, bloc_id: str) -> Optional[EconomicBloc]:
        """Get a bloc by ID"""
        return self.blocs.get(bloc_id)

    def get_country_blocs(self, country_id: str) -> List[str]:
        """Get all bloc IDs a country belongs to"""
        return [bloc.id for bloc in self.blocs.values() if country_id in bloc.members]

    def get_bloc_members(self, bloc_id: str) -> List[str]:
        """Get all members of a bloc"""
        bloc = self.blocs.get(bloc_id)
        return bloc.members if bloc else []

    def calculate_economy_bonus(self, country_id: str) -> int:
        """Calculate total economy bonus from bloc memberships"""
        total = 0
        for bloc_id in self.get_country_blocs(country_id):
            bloc = self.blocs.get(bloc_id)
            if bloc:
                total += bloc.economy_bonus
        return total

    def calculate_trade_bonus(self, country_a: str, country_b: str) -> int:
        """Calculate trade bonus between two countries based on shared blocs"""
        bonus = 0
        blocs_a = set(self.get_country_blocs(country_a))
        blocs_b = set(self.get_country_blocs(country_b))
        shared = blocs_a & blocs_b

        for bloc_id in shared:
            bloc = self.blocs.get(bloc_id)
            if bloc:
                bonus += bloc.trade_bonus

        return bonus

    def has_defense_clause(self, country_id: str, country_b: str = None) -> bool:
        """Check if a country has defense clause protection.
        If country_b provided, checks if both are bound by a defense clause.
        """
        for bloc_id in self.get_country_blocs(country_id):
            bloc = self.blocs.get(bloc_id)
            if bloc and bloc.defense_clause:
                if country_b is None:
                    return True
                if country_b in bloc.members:
                    return True
        return False

    def get_defense_allies(self, country_id: str) -> List[str]:
        """Get all countries bound by defense clauses with this country"""
        allies = set()
        for bloc_id in self.get_country_blocs(country_id):
            bloc = self.blocs.get(bloc_id)
            if bloc and bloc.defense_clause:
                allies.update(bloc.members)
        allies.discard(country_id)
        return list(allies)

    def check_membership_eligible(
        self, bloc_id: str, country: "Country"
    ) -> Tuple[bool, str]:
        """Check if a country meets membership requirements for a bloc"""
        bloc = self.blocs.get(bloc_id)
        if not bloc:
            return False, "Bloc inexistant"

        if country.id in bloc.members:
            return False, "Deja membre"

        reqs = bloc.membership_requirements

        # Check economy requirement
        if "economy" in reqs and country.economy < reqs["economy"]:
            return False, f"Economie insuffisante ({country.economy}/{reqs['economy']})"

        # Check stability requirement
        if "stability" in reqs and country.stability < reqs["stability"]:
            return False, f"Stabilite insuffisante ({country.stability}/{reqs['stability']})"

        # Check regime requirement
        if "regime" in reqs and country.regime not in reqs["regime"]:
            return False, f"Regime incompatible ({country.regime})"

        # Check resources requirement (for OPEC)
        if "resources" in reqs and country.resources < reqs["resources"]:
            return False, f"Ressources insuffisantes ({country.resources}/{reqs['resources']})"

        return True, "Eligible"

    def apply_for_membership(
        self, bloc_id: str, country: "Country"
    ) -> Tuple[bool, str]:
        """Apply for bloc membership"""
        eligible, reason = self.check_membership_eligible(bloc_id, country)
        if not eligible:
            return False, reason

        bloc = self.blocs[bloc_id]
        if country.id not in bloc.pending_applications:
            bloc.pending_applications.append(country.id)
            logger.info(f"{country.id} applied for {bloc_id} membership")
            return True, "Candidature deposee"

        return False, "Candidature deja en cours"

    def approve_membership(self, bloc_id: str, country_id: str) -> bool:
        """Approve a pending membership application"""
        bloc = self.blocs.get(bloc_id)
        if not bloc:
            return False

        if country_id in bloc.pending_applications:
            bloc.pending_applications.remove(country_id)
            bloc.members.append(country_id)
            logger.info(f"{country_id} joined {bloc_id}")
            return True

        return False

    def leave_bloc(self, bloc_id: str, country_id: str) -> bool:
        """Remove a country from a bloc"""
        bloc = self.blocs.get(bloc_id)
        if not bloc:
            return False

        if country_id in bloc.members:
            bloc.members.remove(country_id)
            logger.info(f"{country_id} left {bloc_id}")
            return True

        return False

    def get_resource_controllers(self, resource: str) -> List[Tuple[str, int]]:
        """Get blocs that control a specific resource and their power"""
        controllers = []
        for bloc in self.blocs.values():
            if bloc.controls_resource == resource:
                controllers.append((bloc.id, bloc.resource_control_power))
        return controllers

    def calculate_oil_price_modifier(self) -> int:
        """Calculate oil price modifier based on OPEC decisions"""
        opec = self.blocs.get("OPEC")
        if not opec:
            return 0
        # Base modifier from OPEC power
        return opec.resource_control_power // 10


def apply_bloc_effects(country: "Country", manager: BlocManager) -> Dict[str, int]:
    """Apply annual bloc effects to a country

    Returns dict of stat changes applied
    """
    changes = {
        "economy": 0,
        "relations": {},
    }

    bloc_ids = manager.get_country_blocs(country.id)

    for bloc_id in bloc_ids:
        bloc = manager.blocs.get(bloc_id)
        if not bloc:
            continue
        # Economy bonus
        changes["economy"] += bloc.economy_bonus

        # Relation bonus with other members
        for member_id in bloc.members:
            if member_id != country.id:
                if member_id not in changes["relations"]:
                    changes["relations"][member_id] = 0
                changes["relations"][member_id] += bloc.relation_bonus

    return changes


# Global instance
bloc_manager = BlocManager()
