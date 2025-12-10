# Historia Lite

Simulateur geopolitique moderne modelisant les relations internationales, conflits, zones d'influence et interactions entre pays.

## Stack Technique

- **Frontend**: Next.js 15 + React 18 + Zustand + Tailwind CSS
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

### Phase 9: Persistence et Sauvegarde (EN COURS)
- [ ] Sauvegarde/chargement de parties
- [ ] Historique des evenements en base de donnees
- [ ] Export de parties (JSON)
- [ ] Replay de parties

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

### Phase 11: Scenarios et Objectifs (PLANIFIE)
- [ ] Scenarios historiques predefinis (Guerre Froide, etc.)
- [ ] Objectifs par pays (domination regionale, etc.)
- [ ] Conditions de victoire
- [ ] Mode campagne

### Phase 12: Multijoueur (FUTUR)
- [ ] WebSocket pour temps reel
- [ ] Parties multijoueurs
- [ ] Chat diplomatique
- [ ] Tours simultanes ou tour par tour

---

## Captures d'ecran

*A venir*

## Contributeurs

- Claude Code (Anthropic) - Developpement initial
- [Votre nom] - Conception et direction

## License

MIT
