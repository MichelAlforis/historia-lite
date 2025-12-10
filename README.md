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
