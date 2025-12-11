# Historia Lite

Simulateur geopolitique moderne modelisant les relations internationales, conflits et zones d'influence.

## Stack Technique

- **Frontend**: Next.js 14 + React 18 + Zustand + Tailwind CSS
- **Backend**: FastAPI + Pydantic
- **AI**: Ollama (optionnel) pour decisions avancees

## Installation

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
pip install -r requirements.txt
```

### Frontend

```bash
cd frontend
npm install
```

## Demarrage

### Backend

```bash
cd backend
source .venv/bin/activate
python main.py
```

### Frontend

```bash
cd frontend
npm run dev
```

L'application sera accessible sur:
- Frontend: http://localhost:3001
- Backend API: http://localhost:8001

## Fonctionnalites

### Core
- Simulation annee par annee (2025+)
- 195+ pays repartis en 4 tiers de puissance
- Relations diplomatiques (allies, rivaux, guerres)
- Systeme economique et militaire

### Zones d'Influence
- 19 zones geographiques mondiales
- 8 facteurs: militaire, economique, monetaire, culturel, religieux, petrolier, colonial, diplomatique
- 37 bases militaires reelles

### Interface
- 2 onglets simples: Pays et Carte
- Sauvegarde/chargement de parties
- Raccourcis clavier (Espace: tour, P: auto-play, Echap: fermer)

## API Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /api/state` | Etat actuel du monde |
| `POST /api/tick` | Avancer d'un tour |
| `POST /api/reset` | Reinitialiser |
| `GET /api/country/{id}` | Details d'un pays |
| `GET /api/influence/zones` | Zones d'influence |
| `GET /api/saves` | Sauvegardes |

## Ollama (IA optionnelle)

```bash
# Installer Ollama: https://ollama.ai
ollama pull qwen2.5:3b
```

## License

MIT
