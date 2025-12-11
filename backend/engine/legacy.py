"""
Historical Legacy System for Historia Lite (Phase 2 - Axe 6)

Long-term effects that manifest 5-15 years after major events.
These are subtle influences that shape countries over time.

Examples:
- Post-war baby boom (demographic boost 1-10 years after major conflict ends)
- Post-embargo reindustrialization (economic boost 3-8 years after sanctions lifted)
- Treaty integration effects (stability boost 5-15 years after major treaty)
- War trauma (military doctrine shift, population effects)
"""

import logging
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from .world import GameDate

logger = logging.getLogger(__name__)


class LegacyType(str, Enum):
    """Types of historical legacies"""
    DEMOGRAPHIC = "demographic"     # Population changes (baby boom, emigration)
    ECONOMIC = "economic"           # Reindustrialization, debt effects
    POLITICAL = "political"         # Regime changes, political shifts
    CULTURAL = "cultural"           # Collective memory, national identity
    MILITARY = "military"           # Doctrine changes, veteran effects
    DIPLOMATIC = "diplomatic"       # Long-term alliance effects
    TECHNOLOGICAL = "technological" # Tech advancement or setback


class HistoricalLegacy(BaseModel):
    """
    A long-term effect from a past event that manifests years later.

    Legacies are "dormant" until their activation_date, then become "active"
    and apply effects until their expiry_date.
    """

    id: str

    # Source event
    source_event_id: str
    source_event_title: str
    source_event_title_fr: str
    source_event_date: GameDate

    # Legacy metadata
    legacy_type: LegacyType
    affected_country: str  # Country code

    # Timing
    delay_years: int          # Years after source event before effect starts
    duration_years: int       # How many years the effect lasts
    activation_date: GameDate # When the effect starts (calculated)
    expiry_date: GameDate     # When the effect ends (calculated)

    # Effect
    effect_stat: str          # economy, stability, military, population, etc.
    effect_value: int         # Annual change (+/-)
    effect_description: str
    effect_description_fr: str

    # State
    active: bool = False
    expired: bool = False
    years_applied: int = 0
    total_effect_applied: int = 0

    # Notification flags
    activation_notified: bool = False
    expiry_notified: bool = False


# =============================================================================
# LEGACY TEMPLATES
# Predefined legacy types that can be spawned from events
# =============================================================================

LEGACY_TEMPLATES: Dict[str, Dict[str, Any]] = {
    # Post-war effects
    "post_war_baby_boom": {
        "legacy_type": LegacyType.DEMOGRAPHIC,
        "delay_years": 1,
        "duration_years": 10,
        "effect_stat": "population",
        "effect_value": 2,
        "effect_description": "Post-war baby boom increases population growth",
        "effect_description_fr": "Baby boom d'apres-guerre augmente la croissance demographique"
    },
    "post_war_reconstruction": {
        "legacy_type": LegacyType.ECONOMIC,
        "delay_years": 2,
        "duration_years": 8,
        "effect_stat": "economy",
        "effect_value": 3,
        "effect_description": "Post-war reconstruction drives economic growth",
        "effect_description_fr": "Reconstruction d'apres-guerre stimule la croissance economique"
    },
    "war_trauma": {
        "legacy_type": LegacyType.CULTURAL,
        "delay_years": 0,
        "duration_years": 15,
        "effect_stat": "stability",
        "effect_value": -1,
        "effect_description": "War trauma affects national psyche",
        "effect_description_fr": "Le traumatisme de guerre affecte la psyche nationale"
    },
    "veteran_influence": {
        "legacy_type": LegacyType.MILITARY,
        "delay_years": 5,
        "duration_years": 20,
        "effect_stat": "military",
        "effect_value": 2,
        "effect_description": "War veterans shape military doctrine",
        "effect_description_fr": "Les veterans de guerre faconnent la doctrine militaire"
    },

    # Economic sanctions effects
    "post_embargo_reindustrialization": {
        "legacy_type": LegacyType.ECONOMIC,
        "delay_years": 3,
        "duration_years": 8,
        "effect_stat": "economy",
        "effect_value": 3,
        "effect_description": "Post-embargo reindustrialization boosts economy",
        "effect_description_fr": "Reindustrialisation post-embargo stimule l'economie"
    },
    "sanctions_resilience": {
        "legacy_type": LegacyType.ECONOMIC,
        "delay_years": 2,
        "duration_years": 10,
        "effect_stat": "economy",
        "effect_value": 1,
        "effect_description": "Experience with sanctions builds economic resilience",
        "effect_description_fr": "L'experience des sanctions renforce la resilience economique"
    },

    # Treaty effects
    "treaty_integration": {
        "legacy_type": LegacyType.POLITICAL,
        "delay_years": 5,
        "duration_years": 15,
        "effect_stat": "stability",
        "effect_value": 2,
        "effect_description": "Progressive integration from treaty",
        "effect_description_fr": "Integration progressive suite au traite"
    },
    "alliance_stability": {
        "legacy_type": LegacyType.DIPLOMATIC,
        "delay_years": 3,
        "duration_years": 12,
        "effect_stat": "stability",
        "effect_value": 1,
        "effect_description": "Alliance membership provides long-term stability",
        "effect_description_fr": "L'appartenance a l'alliance assure une stabilite a long terme"
    },

    # Political changes
    "regime_consolidation": {
        "legacy_type": LegacyType.POLITICAL,
        "delay_years": 2,
        "duration_years": 10,
        "effect_stat": "stability",
        "effect_value": 2,
        "effect_description": "New regime consolidates power",
        "effect_description_fr": "Le nouveau regime consolide son pouvoir"
    },
    "democratic_transition": {
        "legacy_type": LegacyType.POLITICAL,
        "delay_years": 3,
        "duration_years": 15,
        "effect_stat": "stability",
        "effect_value": -1,  # Initial instability, then positive
        "effect_description": "Democratic transition causes initial instability",
        "effect_description_fr": "La transition democratique cause une instabilite initiale"
    },

    # Technology effects
    "tech_boom": {
        "legacy_type": LegacyType.TECHNOLOGICAL,
        "delay_years": 2,
        "duration_years": 10,
        "effect_stat": "economy",
        "effect_value": 4,
        "effect_description": "Technological breakthrough drives growth",
        "effect_description_fr": "Une percee technologique stimule la croissance"
    },
    "brain_drain": {
        "legacy_type": LegacyType.TECHNOLOGICAL,
        "delay_years": 1,
        "duration_years": 15,
        "effect_stat": "economy",
        "effect_value": -2,
        "effect_description": "Brain drain hampers development",
        "effect_description_fr": "La fuite des cerveaux freine le developpement"
    },

    # Crisis effects
    "crisis_recovery": {
        "legacy_type": LegacyType.ECONOMIC,
        "delay_years": 2,
        "duration_years": 6,
        "effect_stat": "economy",
        "effect_value": 2,
        "effect_description": "Post-crisis recovery boost",
        "effect_description_fr": "Rebond economique post-crise"
    },
    "pandemic_aftermath": {
        "legacy_type": LegacyType.DEMOGRAPHIC,
        "delay_years": 1,
        "duration_years": 5,
        "effect_stat": "stability",
        "effect_value": -2,
        "effect_description": "Pandemic aftermath affects society",
        "effect_description_fr": "Les sequelles de la pandemie affectent la societe"
    }
}


# =============================================================================
# EVENT TO LEGACY MAPPING
# Maps event types/keywords to potential legacy templates
# =============================================================================

EVENT_LEGACY_TRIGGERS: Dict[str, List[str]] = {
    # Keywords in event titles/types -> legacy template keys
    "war": ["post_war_baby_boom", "post_war_reconstruction", "war_trauma", "veteran_influence"],
    "conflict": ["war_trauma", "veteran_influence"],
    "peace": ["post_war_reconstruction", "treaty_integration"],
    "treaty": ["treaty_integration", "alliance_stability"],
    "alliance": ["alliance_stability"],
    "sanctions": ["sanctions_resilience"],
    "embargo": ["post_embargo_reindustrialization", "sanctions_resilience"],
    "regime": ["regime_consolidation"],
    "revolution": ["democratic_transition", "regime_consolidation"],
    "coup": ["regime_consolidation"],
    "technology": ["tech_boom"],
    "innovation": ["tech_boom"],
    "crisis": ["crisis_recovery"],
    "pandemic": ["pandemic_aftermath"],
    "emigration": ["brain_drain"],
}


class LegacyManager:
    """
    Manages historical legacies for all countries.

    Legacies are created from major events and then "dormant" until
    their activation date. Once active, they apply annual effects.
    """

    def __init__(self):
        self.pending_legacies: List[HistoricalLegacy] = []   # Not yet active
        self.active_legacies: List[HistoricalLegacy] = []    # Currently applying effects
        self.expired_legacies: List[HistoricalLegacy] = []   # Historical record

    def create_legacy_from_event(
        self,
        event_id: str,
        event_title: str,
        event_title_fr: str,
        event_date: GameDate,
        affected_country: str,
        template_key: str,
        importance_multiplier: float = 1.0
    ) -> Optional[HistoricalLegacy]:
        """
        Create a legacy from an event using a template.

        Args:
            event_id: ID of the source event
            event_title: English title
            event_title_fr: French title
            event_date: When the event occurred
            affected_country: Country code
            template_key: Key from LEGACY_TEMPLATES
            importance_multiplier: Scales effect_value (default 1.0)

        Returns:
            Created legacy or None if template not found
        """
        template = LEGACY_TEMPLATES.get(template_key)
        if not template:
            logger.warning(f"Legacy template not found: {template_key}")
            return None

        # Calculate activation and expiry dates
        activation_date = self._add_years(event_date, template["delay_years"])
        expiry_date = self._add_years(activation_date, template["duration_years"])

        # Scale effect value by importance
        effect_value = int(template["effect_value"] * importance_multiplier)

        legacy = HistoricalLegacy(
            id=f"legacy_{event_id}_{template_key}",
            source_event_id=event_id,
            source_event_title=event_title,
            source_event_title_fr=event_title_fr,
            source_event_date=event_date,
            legacy_type=template["legacy_type"],
            affected_country=affected_country,
            delay_years=template["delay_years"],
            duration_years=template["duration_years"],
            activation_date=activation_date,
            expiry_date=expiry_date,
            effect_stat=template["effect_stat"],
            effect_value=effect_value,
            effect_description=template["effect_description"],
            effect_description_fr=template["effect_description_fr"]
        )

        self.pending_legacies.append(legacy)
        logger.info(
            f"Created legacy '{template_key}' for {affected_country} "
            f"(activates {activation_date}, expires {expiry_date})"
        )

        return legacy

    def create_legacies_from_event_auto(
        self,
        event_id: str,
        event_title: str,
        event_title_fr: str,
        event_date: GameDate,
        affected_country: str,
        event_type: str,
        importance: int
    ) -> List[HistoricalLegacy]:
        """
        Automatically create appropriate legacies from an event
        based on its type and title keywords.

        Only creates legacies for important events (importance >= 4).
        """
        if importance < 4:
            return []

        created = []
        title_lower = (event_title + " " + event_title_fr).lower()

        # Find matching legacy templates
        matched_templates = set()
        for keyword, templates in EVENT_LEGACY_TRIGGERS.items():
            if keyword in title_lower or keyword == event_type.lower():
                matched_templates.update(templates)

        # Create legacies (max 2 per event to avoid spam)
        for template_key in list(matched_templates)[:2]:
            # Skip if already have this legacy type for this country
            if self._has_similar_legacy(affected_country, template_key):
                continue

            importance_mult = 0.8 + (importance - 4) * 0.2  # 4->0.8, 5->1.0
            legacy = self.create_legacy_from_event(
                event_id=event_id,
                event_title=event_title,
                event_title_fr=event_title_fr,
                event_date=event_date,
                affected_country=affected_country,
                template_key=template_key,
                importance_multiplier=importance_mult
            )
            if legacy:
                created.append(legacy)

        return created

    def _has_similar_legacy(self, country: str, template_key: str) -> bool:
        """Check if country already has a similar pending/active legacy"""
        template = LEGACY_TEMPLATES.get(template_key)
        if not template:
            return False

        legacy_type = template["legacy_type"]
        effect_stat = template["effect_stat"]

        for legacy in self.pending_legacies + self.active_legacies:
            if (legacy.affected_country == country and
                legacy.legacy_type == legacy_type and
                legacy.effect_stat == effect_stat):
                return True
        return False

    def process_yearly(self, world, current_date: GameDate) -> List[str]:
        """
        Process legacies yearly (call in January of each year).

        - Activates pending legacies whose time has come
        - Applies effects from active legacies
        - Expires legacies that have run their course

        Returns list of notification messages.
        """
        messages = []

        # 1. Activate pending legacies
        newly_active = []
        for legacy in self.pending_legacies[:]:
            if current_date >= legacy.activation_date:
                legacy.active = True
                newly_active.append(legacy)
                self.pending_legacies.remove(legacy)
                self.active_legacies.append(legacy)

                if not legacy.activation_notified:
                    messages.append(
                        f"Effet a long terme: {legacy.effect_description_fr} "
                        f"({legacy.affected_country})"
                    )
                    legacy.activation_notified = True
                    logger.info(f"Legacy {legacy.id} activated for {legacy.affected_country}")

        # 2. Apply effects from active legacies
        expired = []
        for legacy in self.active_legacies:
            # Check if expired
            if current_date >= legacy.expiry_date:
                legacy.expired = True
                expired.append(legacy)

                if not legacy.expiry_notified:
                    messages.append(
                        f"Effet termine: {legacy.effect_description_fr} "
                        f"({legacy.affected_country}) - Total applique: {legacy.total_effect_applied}"
                    )
                    legacy.expiry_notified = True
                continue

            # Apply annual effect
            country = self._get_country(world, legacy.affected_country)
            if country:
                self._apply_effect(country, legacy.effect_stat, legacy.effect_value)
                legacy.years_applied += 1
                legacy.total_effect_applied += legacy.effect_value
                logger.debug(
                    f"Legacy {legacy.id}: applied {legacy.effect_value} to "
                    f"{legacy.affected_country}.{legacy.effect_stat}"
                )

        # 3. Move expired to historical
        for legacy in expired:
            self.active_legacies.remove(legacy)
            self.expired_legacies.append(legacy)

        # Keep only last 50 expired legacies
        if len(self.expired_legacies) > 50:
            self.expired_legacies = self.expired_legacies[-50:]

        return messages

    def process_monthly(self, world, current_date: GameDate) -> List[str]:
        """
        Monthly check - only activates legacies, doesn't apply effects.
        Effects are applied yearly to avoid too much granularity.
        """
        messages = []

        # Activate pending legacies that have reached their time
        for legacy in self.pending_legacies[:]:
            if current_date >= legacy.activation_date and not legacy.active:
                legacy.active = True
                self.pending_legacies.remove(legacy)
                self.active_legacies.append(legacy)

                if not legacy.activation_notified:
                    messages.append(
                        f"Nouvel effet historique: {legacy.effect_description_fr}"
                    )
                    legacy.activation_notified = True

        return messages

    def _apply_effect(self, country, stat_name: str, value: int) -> None:
        """Apply an effect to a country stat"""
        if hasattr(country, stat_name):
            current = getattr(country, stat_name, 0)
            setattr(country, stat_name, current + value)
        elif hasattr(country, 'stats') and isinstance(country.stats, dict):
            if stat_name in country.stats:
                country.stats[stat_name] += value
        elif hasattr(country, 'stats') and hasattr(country.stats, stat_name):
            current = getattr(country.stats, stat_name, 0)
            setattr(country.stats, stat_name, current + value)

    def _get_country(self, world, country_id: str):
        """Get a country from the world by ID"""
        if hasattr(world, 'get_any_country'):
            return world.get_any_country(country_id)
        if hasattr(world, 'countries') and country_id in world.countries:
            return world.countries[country_id]
        if hasattr(world, 'tier4_countries') and country_id in world.tier4_countries:
            return world.tier4_countries[country_id]
        return None

    def _add_years(self, date: GameDate, years: int) -> GameDate:
        """Add years to a GameDate"""
        return GameDate(
            year=date.year + years,
            month=date.month,
            day=date.day
        )

    def get_legacies_for_country(self, country_id: str) -> Dict[str, List[HistoricalLegacy]]:
        """Get all legacies (pending, active, expired) for a country"""
        return {
            "pending": [l for l in self.pending_legacies if l.affected_country == country_id],
            "active": [l for l in self.active_legacies if l.affected_country == country_id],
            "expired": [l for l in self.expired_legacies if l.affected_country == country_id]
        }

    def get_summary(self) -> Dict[str, Any]:
        """Get summary of legacy system state"""
        return {
            "pending_count": len(self.pending_legacies),
            "active_count": len(self.active_legacies),
            "expired_count": len(self.expired_legacies),
            "active_legacies": [
                {
                    "id": l.id,
                    "country": l.affected_country,
                    "type": l.legacy_type.value,
                    "description_fr": l.effect_description_fr,
                    "years_remaining": l.duration_years - l.years_applied,
                    "effect": f"{l.effect_value:+d} {l.effect_stat}/year"
                }
                for l in self.active_legacies
            ],
            "pending_legacies": [
                {
                    "id": l.id,
                    "country": l.affected_country,
                    "activates": str(l.activation_date),
                    "description_fr": l.effect_description_fr
                }
                for l in self.pending_legacies[:10]  # Show first 10
            ]
        }

    def to_dict(self) -> Dict[str, Any]:
        """Serialize for storage"""
        return {
            "pending_legacies": [l.model_dump() for l in self.pending_legacies],
            "active_legacies": [l.model_dump() for l in self.active_legacies],
            "expired_legacies": [l.model_dump() for l in self.expired_legacies[-20:]]  # Keep last 20
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "LegacyManager":
        """Deserialize from storage"""
        manager = cls()
        manager.pending_legacies = [
            HistoricalLegacy(**l) for l in data.get("pending_legacies", [])
        ]
        manager.active_legacies = [
            HistoricalLegacy(**l) for l in data.get("active_legacies", [])
        ]
        manager.expired_legacies = [
            HistoricalLegacy(**l) for l in data.get("expired_legacies", [])
        ]
        return manager
