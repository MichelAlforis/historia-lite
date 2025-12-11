"""Achievement system for Historia Lite"""
import json
import logging
import os
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, field
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class AchievementProgress:
    """Progress tracking for an achievement"""
    achievement_id: str
    current_value: int = 0
    target_value: int = 0
    unlocked: bool = False
    unlocked_at: Optional[str] = None  # ISO date string

    @property
    def progress_percent(self) -> float:
        if self.target_value == 0:
            return 100.0 if self.unlocked else 0.0
        return min(100.0, (self.current_value / self.target_value) * 100)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "achievement_id": self.achievement_id,
            "current_value": self.current_value,
            "target_value": self.target_value,
            "progress_percent": self.progress_percent,
            "unlocked": self.unlocked,
            "unlocked_at": self.unlocked_at
        }


@dataclass
class Achievement:
    """An achievement definition"""
    id: str
    name: str
    name_fr: str
    description: str
    description_fr: str
    icon: str
    category: str
    rarity: str
    points: int
    condition: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "name_fr": self.name_fr,
            "description": self.description,
            "description_fr": self.description_fr,
            "icon": self.icon,
            "category": self.category,
            "rarity": self.rarity,
            "points": self.points,
            "condition": self.condition
        }


class AchievementManager:
    """Manages achievements and progress tracking"""

    def __init__(self):
        self.achievements: Dict[str, Achievement] = {}
        self.categories: Dict[str, Dict] = {}
        self.rarities: Dict[str, Dict] = {}
        self.progress: Dict[str, AchievementProgress] = {}
        self.unlocked_ids: Set[str] = set()

        # Tracking variables for condition checking
        self.years_without_war: int = 0
        self.defcon_3_months: int = 0
        self.wars_won: int = 0
        self.crises_survived: int = 0
        self.start_year: int = 2025

        self._load_achievements()

    def _load_achievements(self):
        """Load achievements from JSON file"""
        data_path = os.path.join(
            os.path.dirname(__file__), '..', 'data', 'achievements.json'
        )
        try:
            with open(data_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

                # Load achievements
                for ach_data in data.get('achievements', []):
                    achievement = Achievement(
                        id=ach_data['id'],
                        name=ach_data['name'],
                        name_fr=ach_data['name_fr'],
                        description=ach_data['description'],
                        description_fr=ach_data['description_fr'],
                        icon=ach_data['icon'],
                        category=ach_data['category'],
                        rarity=ach_data['rarity'],
                        points=ach_data['points'],
                        condition=ach_data['condition']
                    )
                    self.achievements[achievement.id] = achievement

                    # Initialize progress
                    self.progress[achievement.id] = AchievementProgress(
                        achievement_id=achievement.id,
                        target_value=self._get_target_value(achievement.condition)
                    )

                # Load categories and rarities
                self.categories = data.get('categories', {})
                self.rarities = data.get('rarities', {})

                logger.info(f"Loaded {len(self.achievements)} achievements")

        except FileNotFoundError:
            logger.warning(f"Achievements data file not found: {data_path}")
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing achievements.json: {e}")

    def _get_target_value(self, condition: Dict[str, Any]) -> int:
        """Extract target value from condition"""
        cond_type = condition.get('type', '')
        if cond_type == 'years_without_war':
            return condition.get('value', 20)
        if cond_type == 'defcon_maintained':
            return condition.get('years', 10) * 12  # Convert to months
        if cond_type == 'years_played':
            return condition.get('value', 50) * 12  # Convert to months
        if cond_type in ['intel_perfect', 'influence_zones', 'hostile_relations',
                         'ally_count', 'crises_survived', 'wars_won']:
            return condition.get('count', 1)
        if cond_type in ['stat_threshold', 'reputation_threshold']:
            return condition.get('value', 100)
        return 1

    def check_achievements(self, world: Any) -> List[str]:
        """Check all achievements and return newly unlocked ones"""
        newly_unlocked = []

        # Find player country
        player_country = None
        for country in world.countries.values():
            if country.is_player:
                player_country = country
                break

        if not player_country:
            return newly_unlocked

        for ach_id, achievement in self.achievements.items():
            if ach_id in self.unlocked_ids:
                continue

            progress = self.progress[ach_id]
            condition = achievement.condition
            cond_type = condition.get('type', '')

            # Update progress based on condition type
            if cond_type == 'stat_threshold':
                stat = condition.get('stat', 'economy')
                value = getattr(player_country, stat, 0)
                threshold = condition.get('value', 100)
                progress.current_value = value
                if value >= threshold:
                    self._unlock_achievement(ach_id)
                    newly_unlocked.append(ach_id)

            elif cond_type == 'reputation_threshold':
                threshold = condition.get('value', 80)
                direction = condition.get('direction', 'above')
                rep = world.player_reputation
                progress.current_value = rep
                if direction == 'below' and rep <= threshold:
                    self._unlock_achievement(ach_id)
                    newly_unlocked.append(ach_id)
                elif direction == 'above' and rep >= threshold:
                    self._unlock_achievement(ach_id)
                    newly_unlocked.append(ach_id)

            elif cond_type == 'ally_count':
                count = len(player_country.allies)
                progress.current_value = count
                if count >= condition.get('count', 10):
                    self._unlock_achievement(ach_id)
                    newly_unlocked.append(ach_id)

            elif cond_type == 'hostile_relations':
                threshold = condition.get('threshold', -80)
                target_count = condition.get('count', 5)
                hostile_count = sum(1 for r in player_country.relations.values() if r <= threshold)
                progress.current_value = hostile_count
                if hostile_count >= target_count:
                    self._unlock_achievement(ach_id)
                    newly_unlocked.append(ach_id)

            elif cond_type == 'influence_zones':
                zones_dominated = len(player_country.sphere_of_influence)
                progress.current_value = zones_dominated
                if zones_dominated >= condition.get('count', 5):
                    self._unlock_achievement(ach_id)
                    newly_unlocked.append(ach_id)

            elif cond_type == 'years_played':
                years = world.year - self.start_year
                progress.current_value = years * 12
                if years >= condition.get('value', 50):
                    self._unlock_achievement(ach_id)
                    newly_unlocked.append(ach_id)

            elif cond_type == 'years_without_war':
                progress.current_value = self.years_without_war
                if self.years_without_war >= condition.get('value', 20):
                    self._unlock_achievement(ach_id)
                    newly_unlocked.append(ach_id)

            elif cond_type == 'defcon_maintained':
                progress.current_value = self.defcon_3_months
                if self.defcon_3_months >= condition.get('years', 10) * 12:
                    self._unlock_achievement(ach_id)
                    newly_unlocked.append(ach_id)

            elif cond_type == 'wars_won':
                progress.current_value = self.wars_won
                if self.wars_won >= condition.get('count', 1):
                    self._unlock_achievement(ach_id)
                    newly_unlocked.append(ach_id)

            elif cond_type == 'crises_survived':
                progress.current_value = self.crises_survived
                if self.crises_survived >= condition.get('count', 3):
                    self._unlock_achievement(ach_id)
                    newly_unlocked.append(ach_id)

        return newly_unlocked

    def update_trackers(self, world: Any):
        """Update tracking variables based on current state"""
        # Find player
        player_country = None
        for country in world.countries.values():
            if country.is_player:
                player_country = country
                break

        if not player_country:
            return

        # Track years without war
        if player_country.at_war:
            self.years_without_war = 0
        else:
            # Increment by 1/12 for monthly ticks
            if world.month == 1:  # Count years at start of each year
                self.years_without_war += 1

        # Track DEFCON 3 maintenance
        if world.defcon_level == 3:
            self.defcon_3_months += 1
        else:
            self.defcon_3_months = 0  # Reset if DEFCON changes

    def record_war_won(self):
        """Record a war victory"""
        self.wars_won += 1
        logger.info(f"War won recorded. Total: {self.wars_won}")

    def record_crisis_survived(self):
        """Record a survived crisis"""
        self.crises_survived += 1
        logger.info(f"Crisis survived recorded. Total: {self.crises_survived}")

    def _unlock_achievement(self, achievement_id: str):
        """Mark an achievement as unlocked"""
        if achievement_id in self.unlocked_ids:
            return

        self.unlocked_ids.add(achievement_id)
        progress = self.progress.get(achievement_id)
        if progress:
            progress.unlocked = True
            progress.unlocked_at = datetime.now().isoformat()

        achievement = self.achievements.get(achievement_id)
        if achievement:
            logger.info(f"Achievement unlocked: {achievement.name_fr} ({achievement.points} pts)")

    def get_all_achievements(self) -> List[Dict[str, Any]]:
        """Get all achievements with their progress"""
        result = []
        for ach_id, achievement in self.achievements.items():
            ach_dict = achievement.to_dict()
            progress = self.progress.get(ach_id)
            if progress:
                ach_dict['progress'] = progress.to_dict()
            ach_dict['unlocked'] = ach_id in self.unlocked_ids
            result.append(ach_dict)
        return result

    def get_unlocked_achievements(self) -> List[Dict[str, Any]]:
        """Get only unlocked achievements"""
        return [
            {**self.achievements[ach_id].to_dict(), 'progress': self.progress[ach_id].to_dict()}
            for ach_id in self.unlocked_ids
            if ach_id in self.achievements
        ]

    def get_total_points(self) -> int:
        """Get total points from unlocked achievements"""
        return sum(
            self.achievements[ach_id].points
            for ach_id in self.unlocked_ids
            if ach_id in self.achievements
        )

    def get_summary(self) -> Dict[str, Any]:
        """Get achievement summary"""
        total = len(self.achievements)
        unlocked = len(self.unlocked_ids)
        points = self.get_total_points()
        max_points = sum(a.points for a in self.achievements.values())

        # Count by rarity
        by_rarity = {}
        for rarity in self.rarities:
            total_r = sum(1 for a in self.achievements.values() if a.rarity == rarity)
            unlocked_r = sum(1 for ach_id in self.unlocked_ids
                            if ach_id in self.achievements and self.achievements[ach_id].rarity == rarity)
            by_rarity[rarity] = {"total": total_r, "unlocked": unlocked_r}

        return {
            "total": total,
            "unlocked": unlocked,
            "locked": total - unlocked,
            "completion_percent": (unlocked / total * 100) if total > 0 else 0,
            "points": points,
            "max_points": max_points,
            "by_rarity": by_rarity
        }

    def reset(self):
        """Reset all progress"""
        self.unlocked_ids.clear()
        self.years_without_war = 0
        self.defcon_3_months = 0
        self.wars_won = 0
        self.crises_survived = 0
        self.start_year = 2025

        # Reset progress
        for ach_id in self.progress:
            self.progress[ach_id].current_value = 0
            self.progress[ach_id].unlocked = False
            self.progress[ach_id].unlocked_at = None

        logger.info("Achievement progress reset")


# Global instance
achievement_manager = AchievementManager()
