# Historia Lite

Simulateur geopolitique moderne modelisant les relations internationales, conflits, zones d'influence et interactions entre pays.

## Stack Technique

- **Frontend**: Next.js 14 + React 18 + Zustand + Tailwind CSS
- **Backend**: FastAPI + Pydantic
- **AI**: Ollama (qwen2.5:3b) pour decisions avancees

## Installation

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate   # Windows
pip install -r requirements.txt
```

### Frontend

```bash
cd frontend
npm install
```

## Configuration

Creer un fichier `.env` dans `backend/`:

```env
# API Configuration
API_HOST=0.0.0.0
API_PORT=8001
API_RELOAD=true
LOG_LEVEL=INFO

# Ollama Configuration (optionnel)
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=qwen2.5:3b

# CORS (separer par virgule pour plusieurs origines)
CORS_ORIGINS=["http://localhost:3001"]
```

## Demarrage

### Backend

```bash
cd backend
source .venv/bin/activate
python main.py
# ou
uvicorn main:app --reload --port 8001
```

### Frontend

```bash
cd frontend
npm run dev
```

L'application sera accessible sur:
- Frontend: http://localhost:3001
- Backend API: http://localhost:8001
- Documentation API: http://localhost:8001/docs

## Architecture

```
historia-lite/
├── backend/
│   ├── main.py              # Point d'entree FastAPI
│   ├── config.py            # Configuration centralisee
│   ├── api/                 # Routes API
│   │   ├── routes.py        # Routes principales
│   │   ├── currency_routes.py
│   │   └── influence_routes.py
│   ├── engine/              # Moteur de simulation
│   │   ├── world.py         # Etat du monde
│   │   ├── country.py       # Modele pays
│   │   ├── tick.py          # Processeur de tour
│   │   └── ...
│   ├── ai/                  # IA/LLM
│   │   └── ollama_ai.py     # Integration Ollama
│   ├── schemas/             # Schemas Pydantic
│   └── data/                # Donnees JSON
│       ├── countries.json
│       └── ...
└── frontend/
    ├── app/                 # Next.js app router
    ├── components/          # Composants React
    ├── stores/              # Zustand stores
    └── lib/                 # Utilitaires
```

## Fonctionnalites

- Simulation annee par annee
- 195+ pays repartis en 4 tiers
- 8 types d'influence (militaire, economique, culturelle, etc.)
- Systeme de conflits et guerres
- Decisions IA (algorithmique ou LLM)
- Dilemmes interactifs
- Sommets diplomatiques
- Blocs et alliances

## API Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /api/state` | Etat actuel du monde |
| `POST /api/tick` | Avancer d'un tour |
| `POST /api/reset` | Reinitialiser |
| `GET /api/country/{id}` | Details d'un pays |
| `GET /api/events` | Evenements recents |
| `GET /api/influence-zones` | Zones d'influence |
| `GET /api/blocs` | Blocs geopolitiques |

Documentation complete: http://localhost:8001/docs

## Ollama (IA)

Pour utiliser l'IA avancee:

1. Installer Ollama: https://ollama.ai
2. Telecharger le modele: `ollama pull qwen2.5:3b`
3. Configurer `OLLAMA_URL` dans `.env`

Pour developpement local avec Ollama distant:
```bash
ssh -L 11434:localhost:11434 root@<server-ip>
```

## Deploiement

### Production (Hetzner)

```bash
# Local
git add . && git commit -m "description" && git push

# Serveur
ssh -i ~/.ssh/id_rsa_hetzner root@159.69.108.234
cd /srv/crm-alforis/historia-lite
git pull
cd backend && pip install -r requirements.txt
# Redemarrer le service
```

---

## Roadmap

### Phase 1: Core Engine (COMPLETE)
- [x] Systeme de pays (195 pays, 4 tiers)
- [x] Moteur de simulation par ticks (annees)
- [x] Relations diplomatiques (allies, rivaux, guerres)
- [x] Systeme economique et militaire de base
- [x] Evenements aleatoires et crises
- [x] Integration IA Ollama (decisions avancees)

### Phase 2: Systeme Monetaire (COMPLETE)
- [x] 15+ monnaies avec reserves
- [x] Zones monetaires (USD, EUR, CFA, etc.)
- [x] Petro-accords (petro-dollar, petro-yuan)
- [x] Imposition de monnaie (coloniale, debt trap)
- [x] Impact economique des changes

### Phase 3: Blocs et Alliances (COMPLETE)
- [x] 12 blocs geopolitiques (OTAN, BRICS, UE, etc.)
- [x] Adhesion/retrait dynamique
- [x] Effets economiques et militaires des blocs
- [x] Sommets periodiques (G7, G20, ONU)

### Phase 4: Zones d'Influence Avancees (COMPLETE)
- [x] 19 zones geographiques mondiales
- [x] 8 facteurs d'influence:
  - Militaire (bases, presence)
  - Economique (commerce, investissements)
  - Monetaire (zone monnaie, dette)
  - Culturel (langue, media, education)
  - Religieux (religion partagee)
  - Petrolier (accords petroliers)
  - Colonial (heritage historique)
  - Diplomatique (alliances, blocs)
- [x] 37 bases militaires reelles
- [x] 12 religions, 20 cultures
- [x] Calcul dynamique de domination/contestation

### Phase 5: Frontend Influence (COMPLETE)
- [x] InfluencePanel - Liste des zones avec filtres
- [x] ZoneDetailModal - Details complets par zone
- [x] MilitaryBasesPanel - Gestion des bases
- [x] InfluenceBreakdownChart - Visualisation 8 facteurs
- [x] Skeleton loaders et animations

### Phase 6: UX Polish (COMPLETE)
- [x] Design responsive (mobile/tablette/desktop)
- [x] Animations CSS (fadeIn, slideUp, scaleIn, etc.)
- [x] Filtres et recherche avances
- [x] Gradients et icones coherents

### Phase 7: Fonctionnalites Avancees (COMPLETE)
- [x] **ActionPanel** - Actions strategiques joueur:
  - Etablir bases militaires
  - Lancer programmes culturels (Alliance Francaise, Confucius, etc.)
  - Ventes d'armes
- [x] **WorldMap** - Carte mondiale SVG interactive:
  - 4 modes: Dominance, Tensions, Ressources, Influence
  - Donnees geopolitiques reelles 2025
  - Conflits actifs, bases militaires, enjeux strategiques
- [x] **InfluenceHistory** - Historique et statistiques:
  - Evolution 10 ans avec tendances reelles
  - Stats detaillees par puissance
  - Classement Top 10 mondial avec podium
- [x] **NotificationCenter** - Alertes temps reel:
  - Detection changements de domination
  - Evenements critiques (guerres, crises)
  - Toasts flottants pour alertes urgentes

### Phase 8: UX Avancee (COMPLETE)
- [x] **PlayerSelector** - Selection pays joueur persistante
- [x] **Raccourcis clavier**:
  - Espace: Avancer d'un tour
  - P: Play/Pause auto-play
  - Echap: Fermer modals
  - Alt+fleches: Navigation onglets
- [x] Modal d'aide raccourcis

### Phase 9: Persistence et Sauvegarde (COMPLETE)
- [x] **SaveLoadPanel** - Interface sauvegarde/chargement:
  - Liste des sauvegardes avec preview
  - Creation de nouvelle sauvegarde
  - Chargement avec confirmation
  - Suppression avec confirmation
  - Export JSON
- [x] **Backend API** - Persistence des parties:
  - `GET /saves` - Liste des sauvegardes
  - `POST /saves` - Creer sauvegarde
  - `GET /saves/{id}` - Charger sauvegarde
  - `DELETE /saves/{id}` - Supprimer
  - `GET /saves/{id}/export` - Export JSON
- [x] Raccourci Ctrl+S pour sauvegarde rapide
- [x] Autosave optionnel

### Phase 10: Negociations Diplomatiques (COMPLETE)
- [x] Interface de negociation interactive (DiplomaticNegotiations.tsx)
- [x] 8 types d'accords:
  - Traites de paix (met fin aux conflits)
  - Accords commerciaux (boost economique)
  - Alliances defensives (protection mutuelle)
  - Accords petroliers (acces ressources)
  - Programmes de developpement (aide economique)
  - Pactes de non-agression (prevention)
  - Transferts technologiques (partage tech)
  - Acces militaire (bases/transit)
- [x] Systeme de conditions:
  - Offres (aide economique, ventes d'armes, vote ONU, etc.)
  - Demandes (ressources, acces, soutien diplomatique, etc.)
  - Equilibre offre/demande avec indicateur visuel
- [x] Calcul probabilite acceptation base sur:
  - Relations bilaterales
  - Equilibre des conditions
  - Difference de puissance
  - Personnalite du pays cible
- [x] Onglets: Nouvelle negoce / Accords actifs / Historique
- [x] Interface 3 etapes: Selection pays > Type accord > Conditions

### Phase 11: Scenarios et Objectifs (COMPLETE)
- [x] **6 scenarios predefinis**:
  - Monde Moderne 2025 (situation actuelle)
  - Guerre Froide 1962 (Crise de Cuba)
  - WW3 2027 (invasion Taiwan)
  - Monde Multipolaire 2040 (BRICS dominants)
  - Effondrement Climatique 2050 (crise globale)
  - Mode Bac a Sable (libre)
- [x] **18+ objectifs** avec systeme de points:
  - Objectifs d'alliance (maintenir OTAN, etc.)
  - Objectifs territoriaux (reunification Taiwan, etc.)
  - Objectifs economiques (hegemonie monetaire, etc.)
  - Objectifs de survie (eviter guerre nucleaire, etc.)
- [x] **ScenarioSelector** - Interface selection scenario:
  - Selection du scenario avec preview
  - Choix du pays joueur recommande
  - Preview des objectifs
  - Mode observateur disponible
- [x] **Niveaux de difficulte**: easy, normal, hard, extreme, custom
- [x] Modificateurs de difficulte (bonus joueur, penalite IA)

### Phase 12: Multijoueur (COMPLETE)
- [x] **WebSocket temps reel** (FastAPI WebSocket)
- [x] **Systeme de lobbies**:
  - Creation/gestion de salons
  - Limite joueurs configurable (2-8)
  - Selection de pays avant partie
  - Statut pret/pas pret
- [x] **Chat diplomatique**:
  - Messages publics dans le salon
  - Messages prives entre joueurs
  - Historique des conversations
- [x] **Modes de jeu**:
  - Mode simultane (tous jouent en meme temps)
  - Mode tour par tour (timer configurable)
- [x] **Synchronisation**:
  - Etat du monde partage
  - Actions en temps reel
  - Detection fin de tour collective
- [x] **Interface frontend**:
  - MultiplayerPanel - Ecran principal
  - LobbyList - Liste des salons
  - LobbyRoom - Salle d'attente
  - ChatPanel - Chat diplomatique
  - CreateLobbyModal - Creation salon

### Phase 13: Ameliorations Futures (PLANIFIE)
- [ ] **Carte geographique reelle** (Leaflet/MapLibre)
- [ ] **Graphiques temporels avances** (Chart.js/Recharts)
- [ ] **Mode comparaison** pays cote-a-cote
- [ ] **Replay de parties** sauvegardees
- [ ] **IA Ollama avancee** pour decisions strategiques
- [ ] **Evenements historiques** scripts
- [ ] **Tutoriel interactif** pour nouveaux joueurs

---

## Captures d'ecran

*A venir*

## Contributeurs

- Claude Code (Anthropic) - Developpement initial
- [Votre nom] - Conception et direction

## License

MIT
