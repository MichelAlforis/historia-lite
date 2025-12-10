"""Project management for long-term objectives"""
import json
import logging
from pathlib import Path
from typing import TYPE_CHECKING, Dict, List, Optional

from schemas.interaction import (
    ActiveProject,
    ProjectMilestone,
    ProjectTemplate,
    ProjectType,
    SocialTag,
)
from engine.events import Event

if TYPE_CHECKING:
    from engine.world import World
    from engine.country import Country

logger = logging.getLogger(__name__)


class ProjectManager:
    """Manages long-term projects for countries"""

    def __init__(self):
        self.templates: Dict[str, ProjectTemplate] = {}
        self.custom_templates: Dict[str, ProjectTemplate] = {}  # Player-created projects
        self._load_default_templates()

    def _load_default_templates(self) -> None:
        """Load default project templates"""
        self.templates = {
            "mars_program": ProjectTemplate(
                id="mars_program",
                name="Mars Program",
                name_fr="Programme Mars",
                type=ProjectType.SPACE,
                total_years=10,
                economy_cost_per_year=5,
                technology_required=70,
                completion_effects={"technology": 15, "soft_power": 20},
                milestones=[
                    ProjectMilestone(
                        at_progress=30,
                        event_type="project_milestone",
                        title="First Rocket Test",
                        title_fr="Premier test de fusee",
                        description="Successfully tested first rocket prototype",
                        description_fr="Premier prototype de fusee teste avec succes"
                    ),
                    ProjectMilestone(
                        at_progress=60,
                        event_type="project_milestone",
                        title="Orbit Achieved",
                        title_fr="Orbite atteinte",
                        description="First satellite placed in Mars orbit",
                        description_fr="Premier satellite place en orbite martienne"
                    ),
                    ProjectMilestone(
                        at_progress=90,
                        event_type="project_milestone",
                        title="Landing Preparation",
                        title_fr="Preparation atterrissage",
                        description="Final preparations for Mars landing",
                        description_fr="Preparations finales pour l'atterrissage sur Mars"
                    ),
                ],
                description="Send humans to Mars within 10 years",
                description_fr="Envoyer des humains sur Mars en 10 ans"
            ),
            "space_program": ProjectTemplate(
                id="space_program",
                name="Space Program",
                name_fr="Programme Spatial",
                type=ProjectType.SPACE,
                total_years=5,
                economy_cost_per_year=3,
                technology_required=50,
                completion_effects={"technology": 10, "soft_power": 10},
                milestones=[
                    ProjectMilestone(
                        at_progress=50,
                        event_type="project_milestone",
                        title="First Launch",
                        title_fr="Premier lancement",
                        description="First successful orbital launch",
                        description_fr="Premier lancement orbital reussi"
                    ),
                ],
                description="Establish national space capabilities",
                description_fr="Etablir des capacites spatiales nationales"
            ),
            "nuclear_program": ProjectTemplate(
                id="nuclear_program",
                name="Nuclear Program",
                name_fr="Programme Nucleaire",
                type=ProjectType.NUCLEAR,
                total_years=8,
                economy_cost_per_year=6,
                technology_required=60,
                completion_effects={"nuclear": 30, "military": 15},
                milestones=[
                    ProjectMilestone(
                        at_progress=25,
                        event_type="project_milestone",
                        title="Enrichment Facility",
                        title_fr="Installation d'enrichissement",
                        description="Uranium enrichment facility operational",
                        description_fr="Installation d'enrichissement operationnelle"
                    ),
                    ProjectMilestone(
                        at_progress=75,
                        event_type="project_milestone",
                        title="First Test",
                        title_fr="Premier essai",
                        description="First nuclear test conducted",
                        description_fr="Premier essai nucleaire realise"
                    ),
                ],
                description="Develop nuclear weapons capability",
                description_fr="Developper une capacite nucleaire"
            ),
            "military_modernization": ProjectTemplate(
                id="military_modernization",
                name="Military Modernization",
                name_fr="Modernisation Militaire",
                type=ProjectType.MILITARY,
                total_years=5,
                economy_cost_per_year=4,
                technology_required=40,
                completion_effects={"military": 20, "technology": 5},
                milestones=[
                    ProjectMilestone(
                        at_progress=50,
                        event_type="project_milestone",
                        title="New Equipment",
                        title_fr="Nouvel equipement",
                        description="New military equipment deployed",
                        description_fr="Nouvel equipement militaire deploye"
                    ),
                ],
                description="Modernize armed forces",
                description_fr="Moderniser les forces armees"
            ),
            "economic_reform": ProjectTemplate(
                id="economic_reform",
                name="Economic Reform",
                name_fr="Reforme Economique",
                type=ProjectType.ECONOMIC,
                total_years=4,
                economy_cost_per_year=2,
                technology_required=30,
                completion_effects={"economy": 15, "stability": 5},
                milestones=[
                    ProjectMilestone(
                        at_progress=50,
                        event_type="project_milestone",
                        title="Reform Implementation",
                        title_fr="Mise en oeuvre",
                        description="Major reforms implemented",
                        description_fr="Reformes majeures mises en oeuvre"
                    ),
                ],
                description="Structural economic reforms",
                description_fr="Reformes economiques structurelles"
            ),
            "infrastructure": ProjectTemplate(
                id="infrastructure",
                name="Infrastructure Development",
                name_fr="Developpement Infrastructure",
                type=ProjectType.INFRASTRUCTURE,
                total_years=6,
                economy_cost_per_year=4,
                technology_required=20,
                completion_effects={"economy": 10, "stability": 10, "resources": 5},
                milestones=[
                    ProjectMilestone(
                        at_progress=33,
                        event_type="project_milestone",
                        title="Phase 1 Complete",
                        title_fr="Phase 1 terminee",
                        description="First infrastructure phase completed",
                        description_fr="Premiere phase d'infrastructure terminee"
                    ),
                    ProjectMilestone(
                        at_progress=66,
                        event_type="project_milestone",
                        title="Phase 2 Complete",
                        title_fr="Phase 2 terminee",
                        description="Second infrastructure phase completed",
                        description_fr="Deuxieme phase d'infrastructure terminee"
                    ),
                ],
                description="Major infrastructure development",
                description_fr="Developpement majeur d'infrastructure"
            ),
            "ai_research": ProjectTemplate(
                id="ai_research",
                name="AI Research Program",
                name_fr="Programme Recherche IA",
                type=ProjectType.TECHNOLOGY,
                total_years=7,
                economy_cost_per_year=5,
                technology_required=65,
                completion_effects={"technology": 20, "economy": 10, "military": 5},
                milestones=[
                    ProjectMilestone(
                        at_progress=40,
                        event_type="project_milestone",
                        title="AI Breakthrough",
                        title_fr="Percee IA",
                        description="Major AI research breakthrough",
                        description_fr="Percee majeure en recherche IA"
                    ),
                    ProjectMilestone(
                        at_progress=80,
                        event_type="project_milestone",
                        title="AI Deployment",
                        title_fr="Deploiement IA",
                        description="AI systems deployed across sectors",
                        description_fr="Systemes IA deployes dans tous les secteurs"
                    ),
                ],
                description="Advanced artificial intelligence research",
                description_fr="Recherche avancee en intelligence artificielle"
            ),
            "green_transition": ProjectTemplate(
                id="green_transition",
                name="Green Energy Transition",
                name_fr="Transition Energetique",
                type=ProjectType.ECONOMIC,
                total_years=8,
                economy_cost_per_year=4,
                technology_required=45,
                completion_effects={"resources": 15, "soft_power": 10, "stability": 5},
                milestones=[
                    ProjectMilestone(
                        at_progress=25,
                        event_type="project_milestone",
                        title="Solar Farms",
                        title_fr="Fermes solaires",
                        description="Large-scale solar farms operational",
                        description_fr="Grandes fermes solaires operationnelles"
                    ),
                    ProjectMilestone(
                        at_progress=50,
                        event_type="project_milestone",
                        title="Wind Power",
                        title_fr="Energie eolienne",
                        description="Wind power grid expanded",
                        description_fr="Reseau eolien etendu"
                    ),
                    ProjectMilestone(
                        at_progress=75,
                        event_type="project_milestone",
                        title="Grid Integration",
                        title_fr="Integration reseau",
                        description="Renewable grid fully integrated",
                        description_fr="Reseau renouvelable pleinement integre"
                    ),
                ],
                description="Transition to renewable energy",
                description_fr="Transition vers les energies renouvelables"
            ),
            "cyber_defense": ProjectTemplate(
                id="cyber_defense",
                name="Cyber Defense Program",
                name_fr="Programme Cyberdefense",
                type=ProjectType.MILITARY,
                total_years=4,
                economy_cost_per_year=3,
                technology_required=55,
                completion_effects={"technology": 10, "military": 10, "stability": 5},
                milestones=[
                    ProjectMilestone(
                        at_progress=50,
                        event_type="project_milestone",
                        title="Cyber Command",
                        title_fr="Commandement Cyber",
                        description="Cyber Command established",
                        description_fr="Commandement Cyber etabli"
                    ),
                ],
                description="Build cyber warfare capabilities",
                description_fr="Developper des capacites de cyberguerre"
            ),
            "social_programs": ProjectTemplate(
                id="social_programs",
                name="Social Programs",
                name_fr="Programmes Sociaux",
                type=ProjectType.SOCIAL,
                total_years=5,
                economy_cost_per_year=3,
                technology_required=20,
                completion_effects={"stability": 15, "soft_power": 5},
                milestones=[
                    ProjectMilestone(
                        at_progress=50,
                        event_type="project_milestone",
                        title="Programs Launched",
                        title_fr="Programmes lances",
                        description="Social programs launched nationwide",
                        description_fr="Programmes sociaux lances dans tout le pays"
                    ),
                ],
                description="Expand social welfare programs",
                description_fr="Etendre les programmes sociaux"
            ),
        }

    def load_templates_from_file(self, file_path: Path) -> None:
        """Load project templates from JSON file"""
        if not file_path.exists():
            logger.warning(f"Projects file not found: {file_path}")
            return

        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        for project_data in data.get("projects", []):
            template = ProjectTemplate(**project_data)
            self.templates[template.id] = template

        logger.info(f"Loaded {len(self.templates)} project templates")

    def get_available_projects(self, country: "Country") -> List[ProjectTemplate]:
        """Get projects available for a country (default + custom)"""
        available = []
        # Default templates
        for template in self.templates.values():
            if country.technology >= template.technology_required:
                available.append(template)
        # Custom templates (player-created)
        for template in self.custom_templates.values():
            if country.technology >= template.technology_required:
                available.append(template)
        return available

    def get_all_templates(self) -> Dict[str, ProjectTemplate]:
        """Get all templates (default + custom)"""
        all_templates = dict(self.templates)
        all_templates.update(self.custom_templates)
        return all_templates

    def create_custom_project(
        self,
        name: str,
        name_fr: str,
        description: str,
        description_fr: str,
        project_type: ProjectType,
        total_years: int,
        economy_cost_per_year: int,
        completion_effects: Dict[str, int],
        technology_required: int = 0,
        milestones: Optional[List[ProjectMilestone]] = None,
        social_tags: Optional[List[SocialTag]] = None
    ) -> ProjectTemplate:
        """Create a custom player-defined project"""
        import re
        # Generate ID from name
        project_id = f"custom_{re.sub(r'[^a-z0-9]', '_', name.lower())}"

        # Ensure unique ID
        counter = 1
        base_id = project_id
        while project_id in self.custom_templates or project_id in self.templates:
            project_id = f"{base_id}_{counter}"
            counter += 1

        # Auto-generate milestones if not provided
        if milestones is None:
            milestones = []
            if total_years >= 3:
                milestones.append(ProjectMilestone(
                    at_progress=50,
                    event_type="project_milestone",
                    title=f"{name} - Halfway",
                    title_fr=f"{name_fr} - Mi-parcours",
                    description=f"{name} has reached 50% completion",
                    description_fr=f"{name_fr} a atteint 50% d'avancement"
                ))

        # Auto-detect social tags if not provided
        if social_tags is None:
            from engine.social_reactions import detect_social_tags_from_description
            social_tags = detect_social_tags_from_description(description + " " + description_fr)

        template = ProjectTemplate(
            id=project_id,
            name=name,
            name_fr=name_fr,
            type=project_type,
            total_years=total_years,
            economy_cost_per_year=economy_cost_per_year,
            technology_required=technology_required,
            completion_effects=completion_effects,
            milestones=milestones,
            description=description,
            description_fr=description_fr,
            social_tags=social_tags
        )

        self.custom_templates[project_id] = template
        logger.info(f"Created custom project: {project_id} - {name} (tags: {social_tags})")

        return template

    def can_start_project(
        self,
        template_id: str,
        country: "Country",
        active_projects: List[ActiveProject]
    ) -> tuple[bool, str]:
        """Check if a country can start a project"""
        # Check both default and custom templates
        all_templates = self.get_all_templates()
        if template_id not in all_templates:
            return False, "Project template not found"

        template = all_templates[template_id]

        # Check technology requirement
        if country.technology < template.technology_required:
            return False, f"Requires technology level {template.technology_required}"

        # Check economy
        if country.economy < template.economy_cost_per_year * 2:
            return False, "Insufficient economy to sustain project"

        # Check if already running this project
        for project in active_projects:
            if project.template_id == template_id:
                return False, "Project already in progress"

        # Limit concurrent projects based on economy
        max_projects = 1 + country.economy // 30
        if len(active_projects) >= max_projects:
            return False, f"Maximum {max_projects} concurrent projects"

        return True, ""

    def start_project(
        self,
        template_id: str,
        country_id: str
    ) -> Optional[ActiveProject]:
        """Create a new active project"""
        all_templates = self.get_all_templates()
        if template_id not in all_templates:
            return None

        template = all_templates[template_id]

        return ActiveProject(
            id=f"{template_id}_{country_id}",
            template_id=template_id,
            name=template.name,
            name_fr=template.name_fr,
            type=template.type,
            country_id=country_id,
            progress=0,
            years_active=0,
            total_years=template.total_years,
            economy_cost_per_year=template.economy_cost_per_year,
            total_invested=0,
            status="active",
            completion_effects=template.completion_effects,
            social_tags=template.social_tags,
        )

    def process_projects(
        self,
        projects: List[ActiveProject],
        country: "Country",
        world: "World"
    ) -> tuple[List[ActiveProject], List[Event]]:
        """Process all active projects for a country (called each tick)"""
        events = []
        updated_projects = []

        for project in projects:
            if project.status != "active":
                updated_projects.append(project)
                continue

            # Pay annual cost
            if country.economy >= project.economy_cost_per_year:
                country.economy -= project.economy_cost_per_year
                project.total_invested += project.economy_cost_per_year
            else:
                # Insufficient funds - project stalls
                events.append(Event(
                    id=f"project_stall_{world.year}_{project.id}",
                    year=world.year,
                    type="project_milestone",
                    title="Project Stalled",
                    title_fr="Projet en difficulte",
                    description=f"{project.name} stalled due to lack of funding",
                    description_fr=f"{project.name_fr} bloque par manque de financement",
                    country_id=country.id
                ))
                updated_projects.append(project)
                continue

            # Progress
            project.years_active += 1
            base_progress = 100 // project.total_years
            bonus = 5 if project.accelerated else 0
            penalty = -10 if project.sabotaged else 0
            project.progress = min(100, project.progress + base_progress + bonus + penalty)

            # Reset sabotage flag
            project.sabotaged = False

            # Check milestones
            all_templates = self.get_all_templates()
            template = all_templates.get(project.template_id)
            if template:
                for milestone in template.milestones:
                    if (milestone.at_progress <= project.progress and
                            milestone.at_progress not in project.milestones_reached):
                        project.milestones_reached.append(milestone.at_progress)
                        events.append(Event(
                            id=f"milestone_{world.year}_{project.id}_{milestone.at_progress}",
                            year=world.year,
                            type=milestone.event_type,
                            title=milestone.title,
                            title_fr=milestone.title_fr,
                            description=milestone.description,
                            description_fr=milestone.description_fr,
                            country_id=country.id
                        ))

            # Check completion
            if project.progress >= 100:
                project.status = "completed"
                events.append(self._complete_project(project, country, world))
            else:
                updated_projects.append(project)

        return updated_projects, events

    def _complete_project(
        self,
        project: ActiveProject,
        country: "Country",
        world: "World"
    ) -> Event:
        """Complete a project and apply effects"""
        # Apply completion effects
        for stat, value in project.completion_effects.items():
            current = getattr(country, stat, None)
            if current is not None:
                setattr(country, stat, min(100, max(0, current + value)))

        return Event(
            id=f"project_complete_{world.year}_{project.id}",
            year=world.year,
            type="positive",
            title=f"{project.name} Complete",
            title_fr=f"{project.name_fr} termine",
            description=f"{country.name} has completed {project.name}",
            description_fr=f"{country.name_fr} a termine {project.name_fr}",
            country_id=country.id
        )

    def cancel_project(self, project: ActiveProject) -> None:
        """Cancel an active project"""
        project.status = "cancelled"

    def accelerate_project(self, project: ActiveProject, country: "Country") -> bool:
        """Accelerate a project (costs extra economy)"""
        extra_cost = project.economy_cost_per_year
        if country.economy >= extra_cost:
            country.economy -= extra_cost
            project.accelerated = True
            return True
        return False

    def sabotage_project(self, project: ActiveProject) -> None:
        """Sabotage a project (used by rivals)"""
        project.sabotaged = True


# Global project manager instance
project_manager = ProjectManager()
