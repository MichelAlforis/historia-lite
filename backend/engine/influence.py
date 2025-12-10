"""Influence Zone Management System

Handles multi-factor influence calculations:
- Military (bases, presence)
- Economic (trade, investments)
- Monetary (currency zones, debt)
- Cultural (language, media, education)
- Religious (shared religion)
- Petro (oil agreements)
- Colonial (historical ties)
- Diplomatic (alliances, blocs)
"""
import json
import logging
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING, Dict, List, Optional, Tuple

from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from engine.world import World
    from engine.region import InfluenceZone

logger = logging.getLogger(__name__)


class InfluenceType(str, Enum):
    """Types of influence a power can exert"""
    MILITARY = "military"
    ECONOMIC = "economic"
    MONETARY = "monetary"
    CULTURAL = "cultural"
    RELIGIOUS = "religious"
    PETRO = "petro"
    COLONIAL = "colonial"
    DIPLOMATIC = "diplomatic"


class MilitaryBase(BaseModel):
    """A military base"""
    id: str
    name: str
    name_fr: str
    owner: str
    host_country: str
    zone: str
    type: str  # air_base, naval_base, army_base, paramilitary
    personnel: int
    strategic_value: int


class MilitaryBaseManager:
    """Manages military bases globally"""

    def __init__(self):
        self.bases: Dict[str, MilitaryBase] = {}
        self._load_bases()

    def _load_bases(self):
        """Load bases from JSON"""
        data_path = Path(__file__).parent.parent / "data" / "military_bases.json"
        if not data_path.exists():
            logger.warning("military_bases.json not found")
            return

        with open(data_path, "r", encoding="utf-8") as f:
            bases_data = json.load(f)

        for base_data in bases_data:
            base = MilitaryBase(**base_data)
            self.bases[base.id] = base

        logger.info(f"Loaded {len(self.bases)} military bases")

    def get_bases_in_zone(self, zone_id: str) -> List[MilitaryBase]:
        """Get all bases in a zone"""
        return [b for b in self.bases.values() if b.zone == zone_id]

    def get_bases_by_owner(self, owner_id: str) -> List[MilitaryBase]:
        """Get all bases owned by a country"""
        return [b for b in self.bases.values() if b.owner == owner_id]

    def get_power_bases_in_zone(self, zone_id: str, power_id: str) -> List[MilitaryBase]:
        """Get bases of a specific power in a zone"""
        return [b for b in self.bases.values()
                if b.zone == zone_id and b.owner == power_id]

    def calculate_military_presence(self, zone_id: str, power_id: str) -> int:
        """Calculate military presence score for a power in a zone"""
        bases = self.get_power_bases_in_zone(zone_id, power_id)
        if not bases:
            return 0

        score = 0
        for base in bases:
            # Personnel-based scoring
            if base.personnel >= 5000:
                score += 25  # Major base
            elif base.personnel >= 1000:
                score += 15  # Medium base
            else:
                score += 8   # Minor base

            # Strategic value bonus
            score += base.strategic_value // 20

        return min(score, 50)  # Cap at 50

    def add_base(
        self,
        base_id: str,
        name: str,
        owner: str,
        host_country: str,
        zone: str,
        base_type: str,
        personnel: int,
        strategic_value: int
    ) -> MilitaryBase:
        """Add a new military base"""
        base = MilitaryBase(
            id=base_id,
            name=name,
            name_fr=name,
            owner=owner,
            host_country=host_country,
            zone=zone,
            type=base_type,
            personnel=personnel,
            strategic_value=strategic_value
        )
        self.bases[base_id] = base
        logger.info(f"New base established: {name} by {owner} in {zone}")
        return base

    def remove_base(self, base_id: str) -> bool:
        """Remove a military base"""
        if base_id in self.bases:
            base = self.bases.pop(base_id)
            logger.info(f"Base closed: {base.name}")
            return True
        return False


class InfluenceCalculator:
    """Calculates multi-factor influence for powers in zones"""

    def __init__(self, base_manager: MilitaryBaseManager):
        self.base_manager = base_manager
        self._load_reference_data()

    def _load_reference_data(self):
        """Load religions and cultures data"""
        data_dir = Path(__file__).parent.parent / "data"

        self.religions = {}
        religions_path = data_dir / "religions.json"
        if religions_path.exists():
            with open(religions_path, "r", encoding="utf-8") as f:
                for r in json.load(f):
                    self.religions[r["id"]] = r

        self.cultures = {}
        cultures_path = data_dir / "cultures.json"
        if cultures_path.exists():
            with open(cultures_path, "r", encoding="utf-8") as f:
                for c in json.load(f):
                    self.cultures[c["id"]] = c

    def calculate_total_influence(
        self,
        zone: "InfluenceZone",
        power_id: str,
        world: "World"
    ) -> Dict[str, int]:
        """Calculate breakdown of influence by type"""
        power = world.get_country(power_id)
        if not power:
            return {}

        breakdown = {
            InfluenceType.MILITARY.value: self._calc_military(zone, power_id, world),
            InfluenceType.ECONOMIC.value: self._calc_economic(zone, power_id, world),
            InfluenceType.MONETARY.value: self._calc_monetary(zone, power_id, world),
            InfluenceType.CULTURAL.value: self._calc_cultural(zone, power_id, world),
            InfluenceType.RELIGIOUS.value: self._calc_religious(zone, power_id, world),
            InfluenceType.PETRO.value: self._calc_petro(zone, power_id, world),
            InfluenceType.COLONIAL.value: self._calc_colonial(zone, power_id, world),
            InfluenceType.DIPLOMATIC.value: self._calc_diplomatic(zone, power_id, world),
        }

        return breakdown

    def _calc_military(
        self,
        zone: "InfluenceZone",
        power_id: str,
        world: "World"
    ) -> int:
        """Calculate military influence"""
        score = 0

        # Base presence
        base_score = self.base_manager.calculate_military_presence(zone.id, power_id)
        score += base_score

        # Direct military power if country is in zone or adjacent
        power = world.get_country(power_id)
        if power and power_id in zone.countries_in_zone:
            score += power.military // 5

        return min(score, 50)

    def _calc_economic(
        self,
        zone: "InfluenceZone",
        power_id: str,
        world: "World"
    ) -> int:
        """Calculate economic influence"""
        power = world.get_country(power_id)
        if not power:
            return 0

        score = 0

        # Economic power translates to investment capacity
        if power.economy >= 80:
            score += 15
        elif power.economy >= 60:
            score += 10
        elif power.economy >= 40:
            score += 5

        # Trade relations with countries in zone
        for country_id in zone.countries_in_zone:
            country = world.get_country(country_id)
            if country:
                relation = power.relations.get(country_id, 0)
                if relation > 30:
                    score += 5
                elif relation > 0:
                    score += 2

        # Major economic powers have broader reach
        if power.tier == 1:
            score += 10
        elif power.tier == 2:
            score += 5

        return min(score, 30)

    def _calc_monetary(
        self,
        zone: "InfluenceZone",
        power_id: str,
        world: "World"
    ) -> int:
        """Calculate monetary/currency influence"""
        from engine.currency import currency_manager

        power = world.get_country(power_id)
        if not power:
            return 0

        score = 0

        # Check if power controls a currency used in zone
        power_currency = currency_manager.get_country_currency(power_id)
        if not power_currency:
            return 0

        currency = currency_manager.get_currency(power_currency)
        if not currency:
            return 0

        # Is this power the controller?
        if currency.controller != power_id:
            return 0

        # Check zone countries using this currency
        for country_id in zone.countries_in_zone:
            country_currency = currency_manager.get_country_currency(country_id)
            if country_currency == power_currency:
                score += 10  # Direct currency user

            # Check if in currency zone (CFA, etc.)
            if currency.members and country_id in currency.members:
                score += 15  # Currency zone member

        # Check monetary status
        for country_id in zone.countries_in_zone:
            status = currency_manager.country_status.get(country_id)
            if status and status.currency_id == power_currency:
                if status.dependency.value == "dollarized":
                    score += 20
                elif status.dependency.value == "hard_peg":
                    score += 10
                elif status.dependency.value == "soft_peg":
                    score += 5

        return min(score, 35)

    def _calc_cultural(
        self,
        zone: "InfluenceZone",
        power_id: str,
        world: "World"
    ) -> int:
        """Calculate cultural/linguistic influence"""
        power = world.get_country(power_id)
        if not power:
            return 0

        score = 0

        # Get power's culture and language
        power_culture = getattr(power, 'culture', None)
        power_language = getattr(power, 'language', None)

        # Language match with zone
        if power_language and zone.dominant_language == power_language:
            score += 15

        # Culture match with zone
        if power_culture and zone.dominant_culture == power_culture:
            score += 10

        # Soft power bonus
        if power.soft_power >= 70:
            score += 10
        elif power.soft_power >= 50:
            score += 5

        # Check cultural match with countries in zone
        for country_id in zone.countries_in_zone:
            country = world.get_country(country_id)
            if country:
                country_culture = getattr(country, 'culture', None)
                country_language = getattr(country, 'language', None)

                if country_culture == power_culture:
                    score += 3
                if country_language == power_language:
                    score += 3

        return min(score, 25)

    def _calc_religious(
        self,
        zone: "InfluenceZone",
        power_id: str,
        world: "World"
    ) -> int:
        """Calculate religious influence"""
        power = world.get_country(power_id)
        if not power:
            return 0

        score = 0
        power_religion = getattr(power, 'religion', None)

        if not power_religion:
            return 0

        # Match with zone's dominant religion
        if zone.dominant_religion == power_religion:
            score += 15

        # Check if power is the influence_power for this religion
        religion_data = self.religions.get(power_religion)
        if religion_data and religion_data.get("influence_power") == power_id:
            score += 10

        # Match with countries in zone
        for country_id in zone.countries_in_zone:
            country = world.get_country(country_id)
            if country:
                country_religion = getattr(country, 'religion', None)
                if country_religion == power_religion:
                    score += 3

        return min(score, 25)

    def _calc_petro(
        self,
        zone: "InfluenceZone",
        power_id: str,
        world: "World"
    ) -> int:
        """Calculate petro-currency influence"""
        from engine.currency import currency_manager

        if not zone.has_oil:
            return 0

        score = 0

        # Check petro agreements with oil producers in zone
        for agreement in currency_manager.petro_agreements.values():
            if not agreement.is_active:
                continue

            # Is the oil exporter in this zone?
            exporter_in_zone = (
                agreement.oil_exporter in zone.countries_in_zone or
                agreement.oil_exporter == zone.dominant_power
            )

            if exporter_in_zone and agreement.controller == power_id:
                score += 20

        return min(score, 30)

    def _calc_colonial(
        self,
        zone: "InfluenceZone",
        power_id: str,
        world: "World"
    ) -> int:
        """Calculate colonial/historical influence"""
        score = 0

        # Former colonial power of the zone
        if zone.former_colonial_power == power_id:
            score += 10

        # Check countries in zone
        for country_id in zone.countries_in_zone:
            country = world.get_country(country_id)
            if country:
                colonial_history = getattr(country, 'colonial_history', None)
                if colonial_history == power_id:
                    score += 5

        return min(score, 15)

    def _calc_diplomatic(
        self,
        zone: "InfluenceZone",
        power_id: str,
        world: "World"
    ) -> int:
        """Calculate diplomatic/alliance influence"""
        power = world.get_country(power_id)
        if not power:
            return 0

        score = 0

        # Alliances with countries in zone
        for country_id in zone.countries_in_zone:
            if country_id in power.allies:
                score += 10

            # Shared blocs
            country = world.get_country(country_id)
            if country and power.shares_bloc(country):
                score += 5

        # Relations with zone countries
        for country_id in zone.countries_in_zone:
            relation = power.relations.get(country_id, 0)
            if relation > 50:
                score += 5
            elif relation > 20:
                score += 2
            elif relation < -30:
                score -= 3

        return min(max(score, 0), 25)


class InfluenceManager:
    """High-level influence management"""

    def __init__(self):
        self.base_manager = MilitaryBaseManager()
        self.calculator = InfluenceCalculator(self.base_manager)

    @property
    def religions(self):
        """Access religions data from calculator"""
        return self.calculator.religions

    @property
    def cultures(self):
        """Access cultures data from calculator"""
        return self.calculator.cultures

    def update_zone_influence(
        self,
        zone: "InfluenceZone",
        world: "World"
    ) -> Dict[str, Dict[str, int]]:
        """Update influence for all major powers in a zone"""
        # Get major powers to calculate
        major_powers = [c.id for c in world.get_major_powers()]

        # Add current powers in zone
        for power_id in zone.influence_levels.keys():
            if power_id not in major_powers:
                major_powers.append(power_id)

        # Calculate for each power
        results = {}
        for power_id in major_powers:
            breakdown = self.calculator.calculate_total_influence(zone, power_id, world)
            results[power_id] = breakdown

            # Update zone influence level
            total = sum(breakdown.values())
            zone.influence_levels[power_id] = total

        # Update zone breakdown
        zone.influence_breakdown = results

        # Update dominant power
        if zone.influence_levels:
            zone.dominant_power = max(
                zone.influence_levels,
                key=zone.influence_levels.get
            )

            # Update contested_by
            dominant_level = zone.influence_levels[zone.dominant_power]
            zone.contested_by = [
                p for p, level in zone.influence_levels.items()
                if p != zone.dominant_power and level >= dominant_level * 0.6
            ]

        return results

    def establish_base(
        self,
        power_id: str,
        host_country_id: str,
        zone_id: str,
        base_type: str,
        personnel: int,
        world: "World"
    ) -> Tuple[bool, str, Dict]:
        """Establish a new military base"""
        power = world.get_country(power_id)
        host = world.get_country(host_country_id)

        if not power or not host:
            return False, "Pays invalide", {}

        # Check relations
        relation = power.relations.get(host_country_id, 0)
        if relation < 20:
            return False, "Relations insuffisantes avec le pays hote", {}

        # Check if host is in the zone
        zone = world.influence_zones.get(zone_id)
        if not zone:
            return False, "Zone invalide", {}

        if host_country_id not in zone.countries_in_zone and host_country_id != zone.dominant_power:
            return False, "Le pays hote n'est pas dans cette zone", {}

        # Cost (economy impact)
        effects = {
            "economy_power": -5,
            "military_power": 3,
            "relations": {host_country_id: 10},
        }

        # Strategic value based on base size
        strategic_value = min(80, 40 + personnel // 100)

        base_id = f"{power_id.lower()}_{host_country_id.lower()}_{len(self.base_manager.bases)}"
        base = self.base_manager.add_base(
            base_id=base_id,
            name=f"Base {power_id} au {host_country_id}",
            owner=power_id,
            host_country=host_country_id,
            zone=zone_id,
            base_type=base_type,
            personnel=personnel,
            strategic_value=strategic_value
        )

        return True, f"Base etablie: {base.name}", effects

    def close_base(
        self,
        base_id: str,
        world: "World"
    ) -> Tuple[bool, str, Dict]:
        """Close a military base"""
        base = self.base_manager.bases.get(base_id)
        if not base:
            return False, "Base non trouvee", {}

        effects = {
            "economy_power": 2,  # Savings
            "relations": {base.host_country: -10},  # Host unhappy
        }

        self.base_manager.remove_base(base_id)

        return True, f"Base fermee: {base.name}", effects

    def get_zone_breakdown(
        self,
        zone_id: str,
        world: "World"
    ) -> Optional[Dict]:
        """Get detailed influence breakdown for a zone"""
        zone = world.influence_zones.get(zone_id)
        if not zone:
            return None

        # Update first
        self.update_zone_influence(zone, world)

        return {
            "zone_id": zone.id,
            "zone_name_fr": zone.name_fr,
            "dominant_power": zone.dominant_power,
            "contested_by": zone.contested_by,
            "strength": zone.strength,
            "influence_breakdown": zone.influence_breakdown,
            "total_by_power": {
                power: sum(breakdown.values())
                for power, breakdown in zone.influence_breakdown.items()
            },
            "cultural_factors": {
                "dominant_religion": zone.dominant_religion,
                "dominant_culture": zone.dominant_culture,
                "dominant_language": zone.dominant_language,
            },
            "resources": {
                "has_oil": zone.has_oil,
                "has_strategic_resources": zone.has_strategic_resources,
            },
            "military_bases": [
                {
                    "id": b.id,
                    "name": b.name,
                    "owner": b.owner,
                    "personnel": b.personnel,
                    "type": b.type,
                }
                for b in self.base_manager.get_bases_in_zone(zone_id)
            ],
        }


# Global instances
influence_manager = InfluenceManager()
military_base_manager = influence_manager.base_manager
