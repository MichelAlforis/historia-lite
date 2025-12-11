# Historia Lite - Roadmap

## Vue d'ensemble

Historia Lite est un simulateur geopolitique avec 6 tiers de pays, carte mondiale interactive et systeme d'attaque par regions.

---

## Statut des Phases

| Phase | Nom | Status |
|-------|-----|--------|
| 1-9 | Fondations | COMPLETE |
| 10 | Carte Mondiale avec Regions | COMPLETE |
| 11.1 | Systeme d'Attaque (Critique) | COMPLETE |
| 11.2 | Ameliorations UX | COMPLETE |
| 11.3 | Performance Backend | COMPLETE |
| 11.4 | Accessibilite | COMPLETE |
| 12 | Unification Architecture | COMPLETE |
| 13 | Tick Unifie et Routes API | COMPLETE |
| 14 | Scenarios et Objectifs | COMPLETE |
| 15 | Frontend Victoire/Defaite | COMPLETE |
| 16 | Relations Diplomatiques | COMPLETE |
| 17 | Evenements Proceduraux | COMPLETE |

---

## PHASE 11.1 : Systeme d'Attaque - COMPLETE

| Tache | Status |
|-------|--------|
| POST /attack endpoint backend | DONE |
| `executeRegionAttack` dans api.ts | DONE |
| Action store `executeRegionAttack` | DONE |
| Connexion `handleAttack` dans page.tsx | DONE |
| Etat d'erreur GeoJSON | DONE |
| Throttle hover events (perf) | DONE |

---

## PHASE 11.2 : Ameliorations UX - COMPLETE

| Tache | Status |
|-------|--------|
| Systeme de toast notifications | DONE |
| Confirmation attaque capitale | DONE |
| Preview couts d'attaque | DONE |
| Integration toast dans map page | DONE |

---

## PHASE 11.3 : Performance Backend - COMPLETE

| Tache | Status |
|-------|--------|
| RegionCache avec TTL (5 min) | DONE |
| Index par pays (_by_country) | DONE |
| Index regions cotieres (_coastal) | DONE |
| Index capitales (_capital) | DONE |
| Index ressources (_with_resources) | DONE |
| Index par type (_by_type) | DONE |
| Optimiser GET /regions avec indexes | DONE |
| Optimiser GET /summary O(1) | DONE |
| Endpoints admin /cache/stats et /cache/reload | DONE |

### Implementation

```python
class RegionCache:
    """Cache with TTL and indexes"""
    def __init__(self, ttl_seconds: int = 300):
        self._cache: Dict[str, SubnationalRegion] = {}
        self._by_country: Dict[str, List[str]] = {}
        self._coastal: List[str] = []
        self._capital: List[str] = []
        # ...

    def get_by_country(self, country_id: str) -> List[SubnationalRegion]:
        """O(1) lookup instead of O(n) scan"""

    def get_stats(self) -> dict:
        """Monitoring endpoint"""
```

---

## PHASE 11.4 : Accessibilite - COMPLETE

| Tache | Status |
|-------|--------|
| Navigation clavier (fleches, Tab, Entree, Echap) | DONE |
| Attributs ARIA (role, aria-label, aria-live) | DONE |
| Focus visible sur regions (ring-2) | DONE |
| Instructions screen reader (.sr-only) | DONE |
| Annonces vocales dynamiques (aria-live) | DONE |

### Implementation

```typescript
// WorldMapGL.tsx - Navigation clavier
const handleKeyDown = useCallback((e: KeyboardEvent) => {
  if (KEYBOARD_KEYS.NEXT.includes(e.key)) {
    setFocusedRegionIndex(prev => (prev + 1) % countryRegions.length);
    announce(`Region ${region.name_fr}...`);
  }
  if (KEYBOARD_KEYS.SELECT.includes(e.key)) {
    onRegionClick?.(region.id);
  }
}, [...]);

// Attributs ARIA
<div role="application" aria-label="Carte mondiale interactive">
  <div role="listbox" aria-activedescendant={...}>
    <button role="option" aria-selected={...}>
```

### Touches clavier

| Touche | Action |
|--------|--------|
| Tab / Fleches | Naviguer entre regions |
| Entree / Espace | Selectionner region |
| Echap | Annuler selection |

---

## PHASE 12 : Unification Architecture - COMPLETE

### Implementation realisee

| Tache | Status |
|-------|--------|
| Creer BaseCountry unifie | DONE |
| Fusionner 4 JSON en countries_all.json | DONE |
| Implementer TierManager | DONE |
| Creer UnifiedWorld | DONE |
| Adapter game_state.py | DONE |
| Mode legacy + unified coexistent | DONE |

### Fichiers crees

| Fichier | Description |
|---------|-------------|
| `engine/base_country.py` | Modele unifie BaseCountry pour tous les tiers |
| `engine/tier_manager.py` | Gestion promotion/retrogradation dynamique |
| `engine/world_unified.py` | UnifiedWorld avec un seul dict de pays |
| `data/countries_all.json` | 218 pays fusionnes (tous tiers) |

### Utilisation

```python
# Activer le mode unifie
from api.game_state import set_unified_mode, get_world

set_unified_mode(True)
world = get_world()  # Retourne UnifiedWorld

# Requetes unifiees
world.get_country('USA')          # Fonctionne pour tous les tiers
world.get_countries_by_tier(4)    # Remplace get_tier4_countries_list()
world.get_tier_stats()            # {1: 3, 2: 12, 3: 21, 4: 53, 5: 77, 6: 52}
```

---

### 7.1 Probleme resolu : Multiplication des modeles

**Situation actuelle (risquee):**
- Country (T1-3) → countries.json
- Tier4Country → countries_tier4.json
- Tier5Country → countries_tier5.json
- Tier6Country → countries_tier6.json
- SubnationalRegion → regions.json

**Risque majeur:** Desynchronisation entre pays/zones/protecteurs/regions

### 7.2 Solution : Modele unifie BaseCountry

```python
class BaseCountry(BaseModel):
    """Modele unifie pour TOUS les pays"""
    id: str                          # ISO3
    name: str
    name_fr: str
    tier: int = Field(ge=1, le=6)    # Dynamique, peut changer

    # Stats de base (presentes pour tous)
    economy: int = Field(default=50, ge=0, le=100)
    stability: int = Field(default=50, ge=0, le=100)
    population: int = Field(default=10, ge=0)

    # Stats optionnelles (selon tier)
    military: Optional[int] = None    # Tier 1-4 seulement
    nuclear: Optional[int] = None     # Tier 1-2 seulement
    technology: Optional[int] = None  # Tier 1-3 seulement
    soft_power: Optional[int] = None  # Tier 1-2 seulement
    resources: Optional[int] = None   # Tier 1-3 seulement

    # Relations (optionnelles selon tier)
    alignment: Optional[int] = None   # -100 a +100 (Tier 4-6)
    protector: Optional[str] = None   # ISO3 (Tier 5-6)
    allies: List[str] = []            # Tier 1-3
    rivals: List[str] = []            # Tier 1-3

    # Region et zone
    region: str = "unknown"           # Tous
    influence_zone: Optional[str] = None

    # IA - niveau de traitement
    ai_level: str = "minimal"         # "full", "standard", "simplified", "minimal", "passive"
    process_frequency: int = 1        # 1 = chaque tick, 2 = /2 ticks, etc.
```

### 7.3 Un seul fichier JSON

```json
// countries_all.json - TOUS les pays
[
  {
    "id": "USA",
    "tier": 1,
    "economy": 95,
    "military": 100,
    "nuclear": 100,
    "ai_level": "full",
    "process_frequency": 1
  },
  {
    "id": "MCO",
    "tier": 6,
    "economy": 85,
    "stability": 95,
    "protector": "FRA",
    "ai_level": "passive",
    "process_frequency": 5
  }
]
```

### 7.4 Tiers dynamiques avec TierManager

```python
class TierManager:
    TIER_THRESHOLDS = {
        1: {"min_power": 90, "min_military": 80, "nuclear_required": True},
        2: {"min_power": 70, "min_military": 60},
        3: {"min_power": 50, "min_military": 40},
        4: {"min_power": 30, "min_military": 20},
        5: {"min_power": 15, "min_military": 0},
        6: {"min_power": 0, "min_military": 0},
    }

    @staticmethod
    def calculate_natural_tier(country: BaseCountry) -> int:
        """Calcule le tier base sur les stats actuelles"""
        # Promotion/retrogradation dynamique

    @staticmethod
    def check_tier_change(country: BaseCountry) -> Optional[int]:
        """Hysteresis: 3 ticks pour promotion, 5 pour retrogradation"""
```

### 7.5 Plan de migration

| Etape | Description |
|-------|-------------|
| 1 | Creer BaseCountry avec champs optionnels |
| 2 | Fusionner les 4 JSON en countries_all.json |
| 3 | Implementer TierManager |
| 4 | Supprimer anciens modeles |

---

## Architecture 6 Tiers

| Tier | Nom | Pays | IA | Frequence | Stats |
|------|-----|------|----|-----------| ------|
| 1 | Superpuissances | 3 | Complete | Chaque tick | 8 |
| 2 | Puissances majeures | 15 | Complete | Chaque tick | 8 |
| 3 | Puissances regionales | 20 | Standard | Chaque tick | 8 |
| 4 | Nations actives | 50 | Simplifiee | /2 ticks | 5 |
| 5 | Petits pays | 80 | Minimale | /3 ticks | 4 |
| 6 | Micro-nations | 50+ | Passive | /5 ticks | 3 |

### Repartition des pays

**TIER 1 (3):** USA, CHN, RUS

**TIER 2 (15):** FRA, DEU, GBR, JPN, IND, ITA, KOR, BRA, SAU, TUR, IRN, ISR, AUS, CAN, PAK

**TIER 3 (20):** EGY, POL, UKR, IDN, VNM, TWN, PRK, NGA, ZAF, MEX, ARG, ESP, NLD, SWE, ARE, THA, ETH, MAR, MYS, PHL

**TIER 4 (50):** Europe + Moyen-Orient + Asie + Afrique + Ameriques actifs

**TIER 5 (80):** Petites nations sans influence majeure

**TIER 6 (50+):** Micro-etats, iles, territoires

---

## Systeme de Protection

### Principe
Attaquer un petit pays = attaquer son protecteur

### Cascades de consequences

1. **Reaction du protecteur** - Defense automatique ou sanctions
2. **Reaction de la zone d'influence** - Leader reagit
3. **Reaction des voisins** - Relations -20, stabilite -5
4. **Tension mondiale** - +10, soft_power -5 si micro-etat

### Protection par Tier

| Tier | Protection |
|------|------------|
| 6 | Protecteur defend automatiquement |
| 5 | Sanctions automatiques, guerre si agression > 60 |
| 4 | Zone reagit, protecteur evalue |

---

## Zones d'Influence

```python
INFLUENCE_ZONES = {
    "north_america": {"leader": "USA"},
    "south_america": {"leader": "BRA"},
    "western_europe": {"leader": "DEU", "co_leader": "FRA"},
    "eastern_europe": {"leader": "POL"},
    "russia_sphere": {"leader": "RUS"},
    "middle_east_gulf": {"leader": "SAU"},
    "south_asia": {"leader": "IND"},
    "southeast_asia": {"leader": "IDN"},
    "east_asia": {"leader": "CHN"},
    "pacific": {"leader": "AUS", "co_leader": "NZL"},
    "west_africa": {"leader": "NGA"},
    "east_africa": {"leader": "ETH", "co_leader": "KEN"},
    "southern_africa": {"leader": "ZAF"},
}
```

---

## Visualisation Carte

### Couleurs par power_score
- Rouge (80-100) → Orange → Jaune → Vert → Bleu → Gris (0-20)

### Halos d'influence par grande puissance
- USA: Bleu royal `#4169E1`
- CHN: Rouge crimson `#DC143C`
- RUS: Violet `#8B008B`
- FRA: Bleu France `#0055A4`
- DEU: Or `#FFCE00`

### Zoom adaptatif
| Zoom | Affichage |
|------|-----------|
| 0-3 | Pays + halos |
| 4-6 | Frontieres regions |
| 7+ | Detail regions + lignes connexion |

---

## Fichiers Cles

### Backend
- `engine/country.py` - Modeles pays (a unifier)
- `engine/region.py` - SubnationalRegion
- `engine/world.py` - Etat du monde
- `api/regions_routes.py` - Endpoints regions + attaques
- `data/regions.json` - 50 regions

### Frontend
- `components/map/WorldMapGL.tsx` - Carte MapLibre
- `components/map/RegionAttackPanel.tsx` - Panel attaque
- `components/ui/Toast.tsx` - Notifications
- `stores/gameStore.ts` - Etat Zustand
- `lib/types.ts` - Types TypeScript
- `lib/api.ts` - Client API

---

## PHASE 13 : Tick Unifie et Routes API - COMPLETE

### Implementation realisee

| Tache | Status |
|-------|--------|
| Creer tick_unified.py | DONE |
| Integrer TierManager dans tick | DONE |
| Exporter process_unified_tick | DONE |
| Routes API unified-mode | DONE |
| Route API tier-stats | DONE |
| Auto-select tick type | DONE |

### Fichiers crees/modifies

| Fichier | Description |
|---------|-------------|
| `engine/tick_unified.py` | Tick processor pour UnifiedWorld |
| `engine/__init__.py` | Export process_unified_tick |
| `api/game_state.py` | + is_unified_mode() |
| `api/game_routes.py` | + routes unified-mode, tier-stats |

### Utilisation

```bash
# Activer le mode unifie
POST /api/unified-mode?enabled=true

# Verifier le statut
GET /api/unified-mode
# => {"unified_mode": true, "world_type": "UnifiedWorld", "tier_stats": {...}}

# Voir distribution des tiers
GET /api/tier-stats
# => {"distribution": {1: 3, 2: 12, ...}, "countries_by_tier": {...}}

# Tick auto-selectionne le bon processor
POST /api/tick
# => Utilise process_unified_tick si mode unifie
```

### process_unified_tick Features

```python
def process_unified_tick(world: UnifiedWorld, event_pool: EventPool):
    """
    - Process countries by tier frequency (T1-3: every tick, T4: /2, T5: /3, T6: /5)
    - AI decisions based on ai_level (passive, minimal, simplified, standard, full)
    - Tier promotion/demotion every 5 ticks via TierManager
    - DEFCON escalation
    - Global updates (oil_price, global_tension)
    """
```

---

## PHASE 14 : Scenarios et Objectifs - COMPLETE

### Implementation realisee

| Tache | Status |
|-------|--------|
| Creer ScenarioManager | DONE |
| Modeles Pydantic (Scenario, ActiveObjective, etc.) | DONE |
| Integration avec scenarios.json existant | DONE |
| Routes API scenarios avancees | DONE |
| Gestion scenario en cours (status, check, end) | DONE |

### Fichiers crees/modifies

| Fichier | Description |
|---------|-------------|
| `engine/scenario.py` | ScenarioManager avec gestion objectifs |
| `api/scenarios_routes.py` | + routes /current/status, check-objectives, end |

### Architecture

```python
# engine/scenario.py
class ObjectiveStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"

class ScenarioManager:
    """Gere le chargement, demarrage et suivi des scenarios"""
    def load_scenarios(data_dir) -> Dict[str, Scenario]
    def start_scenario(scenario_id, world, player_country) -> bool
    def check_objectives(world) -> List[dict]  # Changes detectees
    def get_scenario_score(world) -> int
    def is_scenario_complete(world) -> bool
    def is_scenario_failed(world) -> bool

# Types d'objectifs supportes:
# - survival: Maintenir stabilite au-dessus d'un seuil
# - alliance: Maintenir un bloc avec X membres
# - influence: Controler X zones d'influence
# - territorial: Annexer ou controler un pays
# - economic: Atteindre X partenariats economiques
# - power: Avoir le plus haut power_score
# - technology: Depasser un pays en technologie
# - defense: Proteger l'independance d'un pays
```

### Routes API

```bash
# Lister tous les scenarios disponibles
GET /api/scenarios/
# => {"scenarios": [...], "total": 5}

# Details d'un scenario
GET /api/scenarios/{scenario_id}

# Demarrer un scenario (mode unifie = application directe)
POST /api/scenarios/start
# Body: {"scenario_id": "cold_war", "player_country": "USA"}
# => {"success": true, "unified_mode": true, "objectives": [...]}

# Statut du scenario en cours
GET /api/scenarios/current/status
# => {"active": true, "scenario_id": "cold_war", "objectives": [...], "total_score": 250}

# Verifier manuellement les objectifs
POST /api/scenarios/current/check-objectives
# => {"checked": true, "changes": [...], "is_complete": false}

# Terminer le scenario
POST /api/scenarios/current/end
# => {"ended": true, "outcome": "victory", "final_score": 500}

# Catalogue des objectifs
GET /api/scenarios/objectives/catalog

# Modificateurs de difficulte
GET /api/scenarios/difficulty/modifiers
```

### Integration avec UnifiedWorld

```python
# UnifiedWorld a les attributs pour les scenarios
class UnifiedWorld(BaseModel):
    scenario_id: Optional[str] = None
    scenario_end_year: Optional[int] = None
    active_objectives: List[dict] = Field(default_factory=list)
    player_country_id: Optional[str] = None
```

### Verification des objectifs dans le tick

```python
# Dans tick_unified.py - les objectifs sont verifies automatiquement
from engine.scenario import scenario_manager

def process_unified_tick(world, event_pool):
    # ... traitement pays ...

    # Verifier objectifs si scenario actif
    if world.scenario_id:
        objective_changes = scenario_manager.check_objectives(world)
        for change in objective_changes:
            # Generer evenement si objectif complete/echoue
            if change["new_status"] in ("completed", "failed"):
                events.append(Event(...))
```

---

## PHASE 15 : Frontend Victoire/Defaite - COMPLETE

### Implementation realisee

| Tache | Status |
|-------|--------|
| Creer VictoryScreen.tsx | DONE |
| Creer DefeatScreen.tsx | DONE |
| Integration API ScenarioStatus | DONE |
| Optimisation videos (compression) | DONE |
| UX polish (videos subtiles en fond) | DONE |

### Fichiers crees/modifies

| Fichier | Description |
|---------|-------------|
| `components/game/VictoryScreen.tsx` | Ecran victoire avec video fond, score, etoiles, objectifs |
| `components/game/DefeatScreen.tsx` | Ecran defaite avec video fond, cause, score, objectifs |
| `lib/api.ts` | + ScenarioStatus interface, getScenarioStatus() |
| `app/pax/page.tsx` | Integration detection victoire/defaite |
| `public/video/victory.mp4` | Video optimisee (2.5MB -> 111KB, -96%) |
| `public/video/defeat.mp4` | Video optimisee (3.3MB -> 129KB, -96%) |

### Composant VictoryScreen

```typescript
interface VictoryScreenProps {
  scenarioName: string;
  finalScore: number;
  maxScore: number;
  yearsPlayed: number;
  objectives: { id: string; name: string; status: string; points: number; }[];
  onRestart: () => void;
  onMainMenu: () => void;
}

// Features:
// - Video fond subtile (opacity 20%, loop)
// - Systeme 3 etoiles selon % score
// - Liste objectifs completes/manques
// - Rang: Parfait > Excellent > Bien > Correct > Insuffisant
```

### Composant DefeatScreen

```typescript
interface DefeatScreenProps {
  scenarioName: string;
  finalScore: number;
  maxScore: number;
  yearsPlayed: number;
  reason: string;
  reasonFr?: string;
  objectives: { id: string; name: string; status: string; points: number; }[];
  onRestart: () => void;
  onMainMenu: () => void;
}

// Features:
// - Video fond subtile (opacity 15%, loop)
// - Cause de defaite mise en evidence
// - Liste objectifs avec statut (completed/failed/pending)
```

### API Integration

```typescript
// lib/api.ts
export interface ScenarioStatus {
  active: boolean;
  scenario_id: string | null;
  scenario_name: string | null;
  player_country: string | null;
  current_year: number;
  end_year: number | null;
  objectives: {
    id: string;
    name: string;
    status: 'pending' | 'in_progress' | 'completed' | 'failed';
    points: number;
  }[];
  total_score: number;
  max_possible_score: number;
  is_complete: boolean;
  is_failed: boolean;
}

export async function getScenarioStatus(): Promise<ScenarioStatus>
```

### Optimisation Videos

```bash
# Compression ffmpeg appliquee
ffmpeg -y -i input.mp4 \
  -c:v libx264 -preset slow -crf 28 \
  -vf "scale=480:-1" \
  -an \
  -movflags +faststart \
  output.mp4

# Resultats:
# victory.mp4: 2.5MB -> 111KB (-96%)
# defeat.mp4: 3.3MB -> 129KB (-96%)
```

### UX Design

- **Videos en fond subtil**: opacity 15-20%, loop automatique
- **Contenu visible immediatement**: pas d'animations de delai
- **Layout compact**: score principal + stats + objectifs
- **Boutons clairs**: Rejouer / Reessayer + Menu

---

## PHASE 16 : Relations Diplomatiques et Polish - COMPLETE

### Objectif
Ajouter un systeme de relations diplomatiques visible et interactif, avec polish general de l'interface.

### Taches

| Tache | Status | Priorite |
|-------|--------|----------|
| Panel Relations diplomatiques (RelationsPanel) | DONE | HIGH |
| Integration bouton Relations dans header | DONE | HIGH |
| Stats relations (guerres, allies, rivaux) | DONE | HIGH |
| Liste triee par categorie | DONE | HIGH |
| Barre visuelle relation (-100 a +100) | DONE | HIGH |
| Matrice relations globale (RelationMatrix.tsx) | DONE | MEDIUM |
| Visualisation alliances/rivalites sur carte (viewMode relations) | DONE | MEDIUM |
| Actions diplomatiques (proposer alliance) | FUTUR | LOW |
| Tests E2E Playwright (e2e/relations.spec.ts) | DONE | MEDIUM |

### RelationsPanel - IMPLEMENTE

```typescript
// components/RelationsPanel.tsx - 368 lignes
// Features implementees:
// - Panel lateral avec liste des relations
// - Barres visuelles (-100 a +100) avec centre
// - Categories: En guerre / Allies / Rivaux / Autres
// - Stats resume: Guerres, Allies, Rivaux, Amicaux, Hostiles
// - Niveaux: Allie (70+), Amical (40+), Neutre (-20+), Tendu (-50+), Hostile
// - Badges visuels par statut (guerre, allie, rival)
```

### Integration pax/page.tsx

```typescript
// Bouton dans header
<button onClick={() => setShowRelations(true)} title="Relations diplomatiques">
  <Users className="w-5 h-5 text-stone-500" />
</button>

// State
const [showRelations, setShowRelations] = useState(false);

// Composant (a ajouter)
<RelationsPanel isOpen={showRelations} onClose={() => setShowRelations(false)} />
```

### Fichiers crees/modifies (Phase 16 finale)

| Fichier | Action | Description |
|---------|--------|-------------|
| `components/RelationMatrix.tsx` | CREE | Matrice NxN interactive avec filtres par tier |
| `components/map/WorldMapGL.tsx` | MODIFIE | Ajout viewMode 'relations' |
| `app/pax/page.tsx` | MODIFIE | Integration boutons matrice + toggle vue carte |
| `e2e/relations.spec.ts` | CREE | Tests E2E pour Phase 16 |

### RelationMatrix - IMPLEMENTE

```typescript
// components/RelationMatrix.tsx - ~280 lignes
// Features:
// - Grille NxN pays Tier 1-3 (38 pays max)
// - Filtrage par tier (1, 2, 3, tous)
// - Couleurs gradient rouge (-100) -> gris (0) -> vert (+100)
// - Icones: epee (guerre), bouclier (allie), cible (rival)
// - Tooltip au hover sur chaque cellule
// - Click sur ligne = selection pays sur carte
```

### WorldMapGL viewMode 'relations' - IMPLEMENTE

```typescript
// Mode relations dans WorldMapGL:
// - Pays joueur = or (#FFD700)
// - En guerre = rouge sombre (#991B1B)
// - Allie = emeraude (#10B981)
// - Rival = orange (#F97316)
// - Gradient relations: -100 rouge -> 0 gris -> +100 vert
```

### API Backend (futur)

```bash
GET /api/relations/{country_id}
# => Liste des relations pour un pays

GET /api/relations/matrix
# => Matrice complete des relations Tier 1-3

POST /api/relations/{country_id}/propose-alliance
# => Proposer alliance a un pays
```

---

## PHASE 17 : Evenements Proceduraux - COMPLETE

### Objectif
Ajouter des evenements contextuels/proceduraux qui rendent chaque partie unique en reagissant a l'etat du monde.

### Taches

| Tache | Status |
|-------|--------|
| Creer ProceduralEventGenerator | DONE |
| Creer procedural_events.json templates | DONE |
| Integrer dans tick.py (Phase 5b) | DONE |
| Ameliorer EventToast.tsx (icones/couleurs) | DONE |
| Animations evenements critiques | DONE |

### Fichiers crees/modifies

| Fichier | Action | Description |
|---------|--------|-------------|
| `backend/engine/procedural_events.py` | CREE | Generateur procedural ~480 lignes |
| `backend/data/procedural_events.json` | CREE | 20+ templates evenements |
| `backend/engine/tick.py` | MODIFIE | Ajout Phase 5b integration |
| `frontend/components/EventToast.tsx` | MODIFIE | Nouveaux types, icones, animations |
| `frontend/app/globals.css` | MODIFIE | Animations pulse-subtle, bounce-once |

### ProceduralEventGenerator - IMPLEMENTE

```python
# backend/engine/procedural_events.py
class ProceduralEventGenerator:
    """Genere des evenements contextuels bases sur l'etat du monde"""

    def generate_events(self, world, player_country_id) -> List[Event]:
        events = []
        events.extend(self._check_alliance_events(world, player))
        events.extend(self._check_regional_crisis_events(world, player))
        events.extend(self._check_economic_events(world, player))
        events.extend(self._check_political_events(world, player))
        events.extend(self._check_rivalry_events(world, player))
        events.extend(self._check_opportunity_events(world, player))
        return events

# Categories d'evenements:
# - alliance: Allie attaque, demande d'aide
# - regional_crisis: Instabilite zone, choc petrolier
# - economic: Boom economique, recession
# - political: Coup d'etat, mouvement reformiste
# - rivalry: Course aux armements, rival en hausse
# - opportunity: Proposition alliance, scandale diplomatique
```

### Templates Evenements (procedural_events.json)

```json
{
  "events": [
    {"id": "coup_attempt", "type": "political_crisis", "conditions": {"stability": {"max": 25}, "military": {"min": 50}}},
    {"id": "trade_deal", "type": "economic", "conditions": {"economy": {"min": 50}, "soft_power": {"min": 40}}},
    {"id": "refugee_crisis", "type": "humanitarian", "conditions": {"stability": {"min": 40}}},
    {"id": "tech_theft", "type": "espionage", "conditions": {"technology": {"min": 60}}},
    {"id": "cultural_renaissance", "type": "positive", "conditions": {"stability": {"min": 60}, "economy": {"min": 50}}},
    {"id": "natural_disaster", "type": "crisis", "probability": 0.08},
    {"id": "currency_crisis", "type": "economic_crisis", "conditions": {"economy": {"max": 40}}},
    // ... 20+ templates
  ],
  "event_chains": [
    {"id": "economic_collapse_chain", "trigger_event": "currency_crisis", "follow_up_events": ["brain_drain", "infrastructure_collapse"]}
  ]
}
```

### Integration tick.py

```python
# Phase 5b: Procedural Events
from .procedural_events import procedural_generator

player_id = None
for country in world.countries.values():
    if country.is_player:
        player_id = country.id
        break
procedural_events = procedural_generator.generate_events(world, player_id)
for event in procedural_events:
    _apply_event(world, event)
    events.append(event)
```

### EventToast Ameliore

```typescript
// Nouveaux types d'icones (Phase 17):
// - HeartHandshake: diplomatic_crisis, ally_under_attack
// - Sparkles: diplomatic_opportunity, alliance_offer
// - Crown: political_crisis, coup
// - Fuel: oil_crisis, energy
// - Eye: scandal, intelligence
// - Target: arms_race, rivalry
// - Scale: reform, political
// - Flame: regional_instability, crisis

// Animations CSS:
// - animate-pulse-subtle: evenements critiques (pulsation subtile)
// - animate-bounce-once: apparition evenements critiques (rebond)
```

---

## Prochaines Etapes

1. ~~**Phase 11.3** - Cache backend, indexes~~ COMPLETE
2. ~~**Phase 11.4** - Accessibilite clavier~~ COMPLETE
3. ~~**Phase 12** - Unification Architecture~~ COMPLETE
4. ~~**Phase 13** - Tick unifie et routes API~~ COMPLETE
5. ~~**Phase 14** - Scenarios et objectifs~~ COMPLETE
6. ~~**Phase 15** - Frontend victoire/defaite~~ COMPLETE
7. ~~**Phase 16** - Relations diplomatiques et polish~~ COMPLETE
8. ~~**Phase 17** - Evenements proceduraux~~ COMPLETE
9. **Phase 18** - Mode multijoueur local (FUTUR)
