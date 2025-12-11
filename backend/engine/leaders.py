"""Leader management system for Historia Lite"""
import json
import logging
import os
from typing import List, Optional, Dict, Any
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class LeaderTrait(BaseModel):
    """A leader's personality trait"""
    id: str
    name_fr: str
    description_fr: str
    effects: Dict[str, int] = {}


class Leader(BaseModel):
    """A country's leader"""
    country_id: str
    name: str
    title: str
    title_fr: str
    start_year: int
    traits: List[str] = []
    traits_data: List[LeaderTrait] = []
    portrait: str = "default"
    ideology: str = "unknown"
    approval_rating: int = 50  # 0-100
    years_in_power: int = 0


class LeaderManager:
    """Manages country leaders with traits and personalities"""

    def __init__(self):
        self.leaders: Dict[str, Leader] = {}
        self.traits_data: Dict[str, Dict] = {}
        self._load_leaders_data()

    def _load_leaders_data(self):
        """Load leaders and traits from JSON file"""
        data_path = os.path.join(
            os.path.dirname(__file__), '..', 'data', 'leaders.json'
        )
        try:
            with open(data_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.traits_data = data.get('traits', {})
                leaders_data = data.get('leaders', {})

                for country_id, leader_info in leaders_data.items():
                    # Build traits data
                    traits_data = []
                    for trait_id in leader_info.get('traits', []):
                        if trait_id in self.traits_data:
                            trait_info = self.traits_data[trait_id]
                            traits_data.append(LeaderTrait(
                                id=trait_id,
                                name_fr=trait_info.get('name_fr', trait_id),
                                description_fr=trait_info.get('description_fr', ''),
                                effects=trait_info.get('effects', {})
                            ))

                    self.leaders[country_id] = Leader(
                        country_id=country_id,
                        name=leader_info['name'],
                        title=leader_info['title'],
                        title_fr=leader_info.get('title_fr', leader_info['title']),
                        start_year=leader_info['start_year'],
                        traits=leader_info.get('traits', []),
                        traits_data=traits_data,
                        portrait=leader_info.get('portrait', 'default'),
                        ideology=leader_info.get('ideology', 'unknown')
                    )
                logger.info(f"Loaded {len(self.leaders)} leaders with traits")
        except FileNotFoundError:
            logger.warning(f"Leaders data file not found: {data_path}")
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing leaders.json: {e}")

    def get_leader(self, country_id: str) -> Optional[Leader]:
        """Get the current leader of a country"""
        return self.leaders.get(country_id)

    def get_leader_dict(self, country_id: str) -> Optional[Dict[str, Any]]:
        """Get leader as dictionary for API responses"""
        leader = self.get_leader(country_id)
        if not leader:
            return None
        return {
            "name": leader.name,
            "title": leader.title,
            "title_fr": leader.title_fr,
            "start_year": leader.start_year,
            "traits": leader.traits,
            "traits_data": [
                {
                    "id": t.id,
                    "name_fr": t.name_fr,
                    "description_fr": t.description_fr,
                    "effects": t.effects
                }
                for t in leader.traits_data
            ],
            "portrait": leader.portrait,
            "ideology": leader.ideology,
            "approval_rating": leader.approval_rating,
            "years_in_power": leader.years_in_power
        }

    def get_all_leaders(self) -> Dict[str, Dict[str, Any]]:
        """Get all leaders as dictionary"""
        return {
            country_id: self.get_leader_dict(country_id)
            for country_id in self.leaders
        }

    def get_leader_traits_effects(self, country_id: str) -> Dict[str, int]:
        """Get combined effects of all leader traits"""
        leader = self.get_leader(country_id)
        if not leader:
            return {}

        combined_effects: Dict[str, int] = {}
        for trait in leader.traits_data:
            for effect_name, effect_value in trait.effects.items():
                combined_effects[effect_name] = combined_effects.get(effect_name, 0) + effect_value

        return combined_effects

    def update_leader_tenure(self, world) -> None:
        """Update years in power for all leaders based on current year"""
        for country_id, leader in self.leaders.items():
            leader.years_in_power = world.year - leader.start_year

    def process_leaders(self, world) -> List:
        """Process leader events (coups, elections, deaths)"""
        events = []
        self.update_leader_tenure(world)

        # Future: Add random events for leadership changes
        # - Coups in unstable countries
        # - Elections in democracies
        # - Health events for long-serving leaders

        return events

    def get_leader_reaction(self, country_id: str, event_type: str) -> Optional[str]:
        """Generate a contextual reaction from a leader based on their traits"""
        leader = self.get_leader(country_id)
        if not leader:
            return None

        # Map traits to reaction styles
        reaction_templates = {
            "war": {
                "militarist": f"{leader.name} approuve l'action militaire decisive",
                "diplomatic": f"{leader.name} appelle a la retenue et au dialogue",
                "hawkish": f"{leader.name} exige une reponse forte et immediate",
                "cautious": f"{leader.name} recommande la prudence",
                "default": f"{leader.name} observe les developpements avec attention"
            },
            "alliance": {
                "multilateral": f"{leader.name} salue ce renforcement de la cooperation",
                "nationalist": f"{leader.name} reste sceptique sur les alliances",
                "pro_western": f"{leader.name} celebre ce rapprochement avec l'Occident",
                "anti_western": f"{leader.name} denonce cette alliance hostile",
                "default": f"{leader.name} prend note de cette evolution"
            },
            "crisis": {
                "authoritarian": f"{leader.name} appelle au calme et a l'unite nationale",
                "populist": f"{leader.name} pointe du doigt les responsables",
                "pragmatic": f"{leader.name} propose des solutions concretes",
                "default": f"{leader.name} suit la situation de pres"
            },
            "nuclear": {
                "nuclear_obsessed": f"{leader.name} brandit la menace nucleaire",
                "cautious": f"{leader.name} appelle a la desescalade immediate",
                "hawkish": f"{leader.name} affirme etre pret a toute eventualite",
                "default": f"{leader.name} exprime sa vive inquietude"
            }
        }

        event_reactions = reaction_templates.get(event_type, {})

        # Find first matching trait
        for trait in leader.traits:
            if trait in event_reactions:
                return event_reactions[trait]

        return event_reactions.get("default")

    def reset(self):
        """Reset leader state (reload from JSON)"""
        self._load_leaders_data()


# Global instance
leader_manager = LeaderManager()
