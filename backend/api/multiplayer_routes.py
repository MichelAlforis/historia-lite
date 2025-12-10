"""Multiplayer WebSocket routes for Historia Lite"""
import logging
import json
import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Set
from enum import Enum
from uuid import uuid4

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException
from pydantic import BaseModel

from .game_state import get_world, reset_world

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/multiplayer", tags=["multiplayer"])


# =============================================================================
# MODELS
# =============================================================================

class GameMode(str, Enum):
    SIMULTANEOUS = "simultaneous"  # All players act at same time
    TURN_BASED = "turn_based"      # Players take turns


class LobbyStatus(str, Enum):
    WAITING = "waiting"
    STARTING = "starting"
    IN_GAME = "in_game"
    FINISHED = "finished"


class PlayerInfo(BaseModel):
    id: str
    name: str
    country_id: Optional[str] = None
    is_ready: bool = False
    is_host: bool = False
    connected: bool = True


class LobbyInfo(BaseModel):
    id: str
    name: str
    host_id: str
    max_players: int = 8
    game_mode: GameMode = GameMode.SIMULTANEOUS
    turn_timer: int = 60  # seconds per turn (0 = no limit)
    status: LobbyStatus = LobbyStatus.WAITING
    players: List[PlayerInfo] = []
    created_at: str
    current_year: int = 2025
    current_turn_player: Optional[str] = None  # For turn-based mode


class ChatMessage(BaseModel):
    id: str
    lobby_id: str
    sender_id: str
    sender_name: str
    content: str
    is_diplomatic: bool = False  # Private diplomatic message
    recipient_id: Optional[str] = None  # For private messages
    timestamp: str


class GameAction(BaseModel):
    type: str  # "tick", "negotiate", "action", "vote", etc.
    player_id: str
    data: dict = {}


# =============================================================================
# CONNECTION MANAGER
# =============================================================================

class ConnectionManager:
    """Manages WebSocket connections for multiplayer games"""

    def __init__(self):
        # lobby_id -> {player_id -> WebSocket}
        self.connections: Dict[str, Dict[str, WebSocket]] = {}
        # All lobbies
        self.lobbies: Dict[str, LobbyInfo] = {}
        # player_id -> lobby_id mapping
        self.player_lobbies: Dict[str, str] = {}
        # Chat history per lobby (keep last 100 messages)
        self.chat_history: Dict[str, List[ChatMessage]] = {}
        # Turn submissions for simultaneous mode
        self.turn_submissions: Dict[str, Set[str]] = {}
        # Pending actions per lobby
        self.pending_actions: Dict[str, List[GameAction]] = {}

    async def connect(self, websocket: WebSocket, lobby_id: str, player_id: str):
        """Connect a player to a lobby"""
        await websocket.accept()

        if lobby_id not in self.connections:
            self.connections[lobby_id] = {}

        self.connections[lobby_id][player_id] = websocket
        self.player_lobbies[player_id] = lobby_id

        # Update player connected status
        if lobby_id in self.lobbies:
            for player in self.lobbies[lobby_id].players:
                if player.id == player_id:
                    player.connected = True
                    break

        logger.info(f"Player {player_id} connected to lobby {lobby_id}")

    def disconnect(self, lobby_id: str, player_id: str):
        """Disconnect a player from a lobby"""
        if lobby_id in self.connections and player_id in self.connections[lobby_id]:
            del self.connections[lobby_id][player_id]

            # Update player connected status
            if lobby_id in self.lobbies:
                for player in self.lobbies[lobby_id].players:
                    if player.id == player_id:
                        player.connected = False
                        break

            if player_id in self.player_lobbies:
                del self.player_lobbies[player_id]

            # Clean up empty lobbies
            if not self.connections[lobby_id]:
                del self.connections[lobby_id]
                if lobby_id in self.lobbies:
                    del self.lobbies[lobby_id]
                if lobby_id in self.chat_history:
                    del self.chat_history[lobby_id]

        logger.info(f"Player {player_id} disconnected from lobby {lobby_id}")

    async def broadcast_to_lobby(self, lobby_id: str, message: dict, exclude: Optional[str] = None):
        """Broadcast message to all players in a lobby"""
        if lobby_id not in self.connections:
            return

        disconnected = []
        for player_id, websocket in self.connections[lobby_id].items():
            if exclude and player_id == exclude:
                continue
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.error(f"Error sending to {player_id}: {e}")
                disconnected.append(player_id)

        # Clean up disconnected players
        for player_id in disconnected:
            self.disconnect(lobby_id, player_id)

    async def send_to_player(self, lobby_id: str, player_id: str, message: dict):
        """Send message to a specific player"""
        if lobby_id in self.connections and player_id in self.connections[lobby_id]:
            try:
                await self.connections[lobby_id][player_id].send_json(message)
            except Exception as e:
                logger.error(f"Error sending to {player_id}: {e}")
                self.disconnect(lobby_id, player_id)


manager = ConnectionManager()


# =============================================================================
# REST API ENDPOINTS
# =============================================================================

@router.get("/lobbies")
async def list_lobbies():
    """List all available lobbies"""
    return {
        "lobbies": [
            {
                "id": lobby.id,
                "name": lobby.name,
                "players": len(lobby.players),
                "max_players": lobby.max_players,
                "status": lobby.status,
                "game_mode": lobby.game_mode,
                "host": next((p.name for p in lobby.players if p.is_host), "Unknown")
            }
            for lobby in manager.lobbies.values()
            if lobby.status == LobbyStatus.WAITING
        ]
    }


@router.post("/lobbies")
async def create_lobby(
    name: str,
    host_name: str,
    max_players: int = 8,
    game_mode: GameMode = GameMode.SIMULTANEOUS,
    turn_timer: int = 60
):
    """Create a new multiplayer lobby"""
    lobby_id = str(uuid4())[:8]
    host_id = str(uuid4())[:8]

    host = PlayerInfo(
        id=host_id,
        name=host_name,
        is_host=True,
        is_ready=True
    )

    lobby = LobbyInfo(
        id=lobby_id,
        name=name,
        host_id=host_id,
        max_players=max_players,
        game_mode=game_mode,
        turn_timer=turn_timer,
        players=[host],
        created_at=datetime.utcnow().isoformat()
    )

    manager.lobbies[lobby_id] = lobby
    manager.chat_history[lobby_id] = []
    manager.turn_submissions[lobby_id] = set()
    manager.pending_actions[lobby_id] = []

    logger.info(f"Lobby {lobby_id} created by {host_name}")

    return {
        "lobby": lobby.model_dump(),
        "player_id": host_id
    }


@router.post("/lobbies/{lobby_id}/join")
async def join_lobby(lobby_id: str, player_name: str):
    """Join an existing lobby"""
    if lobby_id not in manager.lobbies:
        raise HTTPException(status_code=404, detail="Lobby not found")

    lobby = manager.lobbies[lobby_id]

    if lobby.status != LobbyStatus.WAITING:
        raise HTTPException(status_code=400, detail="Game already started")

    if len(lobby.players) >= lobby.max_players:
        raise HTTPException(status_code=400, detail="Lobby is full")

    player_id = str(uuid4())[:8]
    player = PlayerInfo(
        id=player_id,
        name=player_name,
        is_host=False
    )

    lobby.players.append(player)

    # Notify other players
    await manager.broadcast_to_lobby(lobby_id, {
        "type": "player_joined",
        "player": player.model_dump()
    })

    logger.info(f"Player {player_name} joined lobby {lobby_id}")

    return {
        "lobby": lobby.model_dump(),
        "player_id": player_id
    }


@router.post("/lobbies/{lobby_id}/leave")
async def leave_lobby(lobby_id: str, player_id: str):
    """Leave a lobby"""
    if lobby_id not in manager.lobbies:
        raise HTTPException(status_code=404, detail="Lobby not found")

    lobby = manager.lobbies[lobby_id]

    # Remove player
    lobby.players = [p for p in lobby.players if p.id != player_id]

    # If host left, assign new host or delete lobby
    if player_id == lobby.host_id:
        if lobby.players:
            new_host = lobby.players[0]
            new_host.is_host = True
            lobby.host_id = new_host.id
        else:
            del manager.lobbies[lobby_id]
            return {"message": "Lobby deleted"}

    # Disconnect WebSocket
    manager.disconnect(lobby_id, player_id)

    # Notify others
    await manager.broadcast_to_lobby(lobby_id, {
        "type": "player_left",
        "player_id": player_id
    })

    return {"message": "Left lobby"}


@router.post("/lobbies/{lobby_id}/select-country")
async def select_country(lobby_id: str, player_id: str, country_id: str):
    """Select a country to play as"""
    if lobby_id not in manager.lobbies:
        raise HTTPException(status_code=404, detail="Lobby not found")

    lobby = manager.lobbies[lobby_id]

    # Check country not already taken
    for player in lobby.players:
        if player.country_id == country_id and player.id != player_id:
            raise HTTPException(status_code=400, detail="Country already taken")

    # Update player's country
    for player in lobby.players:
        if player.id == player_id:
            player.country_id = country_id
            break

    # Notify others
    await manager.broadcast_to_lobby(lobby_id, {
        "type": "country_selected",
        "player_id": player_id,
        "country_id": country_id
    })

    return {"message": "Country selected"}


@router.post("/lobbies/{lobby_id}/ready")
async def toggle_ready(lobby_id: str, player_id: str):
    """Toggle ready status"""
    if lobby_id not in manager.lobbies:
        raise HTTPException(status_code=404, detail="Lobby not found")

    lobby = manager.lobbies[lobby_id]

    for player in lobby.players:
        if player.id == player_id:
            player.is_ready = not player.is_ready
            break

    # Notify others
    await manager.broadcast_to_lobby(lobby_id, {
        "type": "player_ready",
        "player_id": player_id,
        "is_ready": player.is_ready
    })

    return {"is_ready": player.is_ready}


@router.post("/lobbies/{lobby_id}/start")
async def start_game(lobby_id: str, player_id: str):
    """Start the game (host only)"""
    if lobby_id not in manager.lobbies:
        raise HTTPException(status_code=404, detail="Lobby not found")

    lobby = manager.lobbies[lobby_id]

    if player_id != lobby.host_id:
        raise HTTPException(status_code=403, detail="Only host can start the game")

    # Check all players ready and have countries
    for player in lobby.players:
        if not player.is_ready:
            raise HTTPException(status_code=400, detail=f"{player.name} is not ready")
        if not player.country_id:
            raise HTTPException(status_code=400, detail=f"{player.name} hasn't selected a country")

    lobby.status = LobbyStatus.IN_GAME

    # Initialize game world
    reset_world()

    # For turn-based, set first player
    if lobby.game_mode == GameMode.TURN_BASED:
        lobby.current_turn_player = lobby.players[0].id

    # Notify all players
    await manager.broadcast_to_lobby(lobby_id, {
        "type": "game_started",
        "game_mode": lobby.game_mode,
        "turn_timer": lobby.turn_timer,
        "current_turn_player": lobby.current_turn_player,
        "world_state": get_world().to_dict()
    })

    logger.info(f"Game started in lobby {lobby_id}")

    return {"message": "Game started"}


@router.get("/lobbies/{lobby_id}")
async def get_lobby(lobby_id: str):
    """Get lobby details"""
    if lobby_id not in manager.lobbies:
        raise HTTPException(status_code=404, detail="Lobby not found")

    return manager.lobbies[lobby_id].model_dump()


@router.get("/lobbies/{lobby_id}/chat")
async def get_chat_history(lobby_id: str, limit: int = 50):
    """Get chat history for a lobby"""
    if lobby_id not in manager.chat_history:
        return {"messages": []}

    messages = manager.chat_history[lobby_id][-limit:]
    return {"messages": [m.model_dump() for m in messages]}


# =============================================================================
# WEBSOCKET ENDPOINT
# =============================================================================

@router.websocket("/ws/{lobby_id}/{player_id}")
async def websocket_endpoint(websocket: WebSocket, lobby_id: str, player_id: str):
    """WebSocket connection for real-time multiplayer"""

    if lobby_id not in manager.lobbies:
        await websocket.close(code=4004, reason="Lobby not found")
        return

    lobby = manager.lobbies[lobby_id]
    player = next((p for p in lobby.players if p.id == player_id), None)

    if not player:
        await websocket.close(code=4004, reason="Player not in lobby")
        return

    await manager.connect(websocket, lobby_id, player_id)

    try:
        # Send current state
        await websocket.send_json({
            "type": "connected",
            "lobby": lobby.model_dump(),
            "chat_history": [m.model_dump() for m in manager.chat_history.get(lobby_id, [])[-50:]]
        })

        while True:
            data = await websocket.receive_json()
            await handle_websocket_message(lobby_id, player_id, data)

    except WebSocketDisconnect:
        manager.disconnect(lobby_id, player_id)

        # Notify others
        await manager.broadcast_to_lobby(lobby_id, {
            "type": "player_disconnected",
            "player_id": player_id
        })


async def handle_websocket_message(lobby_id: str, player_id: str, data: dict):
    """Handle incoming WebSocket messages"""
    msg_type = data.get("type")
    lobby = manager.lobbies.get(lobby_id)

    if not lobby:
        return

    player = next((p for p in lobby.players if p.id == player_id), None)
    if not player:
        return

    # -------------------------------------------------------------------------
    # CHAT MESSAGES
    # -------------------------------------------------------------------------
    if msg_type == "chat":
        message = ChatMessage(
            id=str(uuid4())[:8],
            lobby_id=lobby_id,
            sender_id=player_id,
            sender_name=player.name,
            content=data.get("content", ""),
            is_diplomatic=data.get("is_diplomatic", False),
            recipient_id=data.get("recipient_id"),
            timestamp=datetime.utcnow().isoformat()
        )

        # Store message
        if lobby_id not in manager.chat_history:
            manager.chat_history[lobby_id] = []
        manager.chat_history[lobby_id].append(message)

        # Keep only last 100 messages
        if len(manager.chat_history[lobby_id]) > 100:
            manager.chat_history[lobby_id] = manager.chat_history[lobby_id][-100:]

        # Send to recipient(s)
        if message.is_diplomatic and message.recipient_id:
            # Private diplomatic message
            await manager.send_to_player(lobby_id, player_id, {
                "type": "chat_message",
                "message": message.model_dump()
            })
            await manager.send_to_player(lobby_id, message.recipient_id, {
                "type": "chat_message",
                "message": message.model_dump()
            })
        else:
            # Public message
            await manager.broadcast_to_lobby(lobby_id, {
                "type": "chat_message",
                "message": message.model_dump()
            })

    # -------------------------------------------------------------------------
    # GAME ACTIONS
    # -------------------------------------------------------------------------
    elif msg_type == "game_action":
        if lobby.status != LobbyStatus.IN_GAME:
            return

        action = GameAction(
            type=data.get("action_type", "unknown"),
            player_id=player_id,
            data=data.get("action_data", {})
        )

        # In turn-based mode, only current player can act
        if lobby.game_mode == GameMode.TURN_BASED:
            if lobby.current_turn_player != player_id:
                await manager.send_to_player(lobby_id, player_id, {
                    "type": "error",
                    "message": "Not your turn"
                })
                return

        # Store action
        manager.pending_actions[lobby_id].append(action)

        # Broadcast action to all players
        await manager.broadcast_to_lobby(lobby_id, {
            "type": "game_action",
            "action": action.model_dump(),
            "player_name": player.name
        })

    # -------------------------------------------------------------------------
    # END TURN (for both modes)
    # -------------------------------------------------------------------------
    elif msg_type == "end_turn":
        if lobby.status != LobbyStatus.IN_GAME:
            return

        if lobby.game_mode == GameMode.TURN_BASED:
            # Move to next player
            current_idx = next(
                (i for i, p in enumerate(lobby.players) if p.id == lobby.current_turn_player),
                0
            )
            next_idx = (current_idx + 1) % len(lobby.players)

            # If we've gone full circle, process the tick
            if next_idx == 0:
                await process_game_tick(lobby_id)
            else:
                lobby.current_turn_player = lobby.players[next_idx].id
                await manager.broadcast_to_lobby(lobby_id, {
                    "type": "turn_changed",
                    "current_player_id": lobby.current_turn_player,
                    "current_player_name": lobby.players[next_idx].name
                })

        else:  # SIMULTANEOUS mode
            manager.turn_submissions[lobby_id].add(player_id)

            await manager.broadcast_to_lobby(lobby_id, {
                "type": "player_submitted_turn",
                "player_id": player_id,
                "player_name": player.name,
                "submitted_count": len(manager.turn_submissions[lobby_id]),
                "total_players": len(lobby.players)
            })

            # Check if all players submitted
            if len(manager.turn_submissions[lobby_id]) >= len(lobby.players):
                await process_game_tick(lobby_id)

    # -------------------------------------------------------------------------
    # DIPLOMACY REQUEST
    # -------------------------------------------------------------------------
    elif msg_type == "diplomacy_request":
        target_player_id = data.get("target_player_id")
        proposal = data.get("proposal", {})

        if target_player_id:
            await manager.send_to_player(lobby_id, target_player_id, {
                "type": "diplomacy_request",
                "from_player_id": player_id,
                "from_player_name": player.name,
                "from_country_id": player.country_id,
                "proposal": proposal
            })

    elif msg_type == "diplomacy_response":
        target_player_id = data.get("target_player_id")
        accepted = data.get("accepted", False)
        proposal = data.get("proposal", {})

        if target_player_id:
            await manager.send_to_player(lobby_id, target_player_id, {
                "type": "diplomacy_response",
                "from_player_id": player_id,
                "from_player_name": player.name,
                "accepted": accepted,
                "proposal": proposal
            })

            # If accepted, broadcast to all
            if accepted:
                await manager.broadcast_to_lobby(lobby_id, {
                    "type": "diplomacy_agreement",
                    "players": [player_id, target_player_id],
                    "proposal": proposal
                })


async def process_game_tick(lobby_id: str):
    """Process a game tick and advance the year"""
    lobby = manager.lobbies.get(lobby_id)
    if not lobby:
        return

    # Get world and process tick
    world = get_world()

    # Apply all pending actions
    for action in manager.pending_actions.get(lobby_id, []):
        # Here you would apply each action to the world
        # This is simplified - in practice, you'd call the appropriate engine functions
        pass

    # Process world tick
    from engine.tick import process_tick
    events = process_tick(world)

    lobby.current_year = world.year

    # Clear pending actions and submissions
    manager.pending_actions[lobby_id] = []
    manager.turn_submissions[lobby_id] = set()

    # Reset current turn player for turn-based
    if lobby.game_mode == GameMode.TURN_BASED:
        lobby.current_turn_player = lobby.players[0].id

    # Broadcast new state
    await manager.broadcast_to_lobby(lobby_id, {
        "type": "tick_processed",
        "year": world.year,
        "events": [e.to_dict() if hasattr(e, 'to_dict') else str(e) for e in events],
        "world_state": world.to_dict(),
        "current_turn_player": lobby.current_turn_player
    })

    # Check victory conditions
    await check_victory_conditions(lobby_id)


async def check_victory_conditions(lobby_id: str):
    """Check if any player has won"""
    lobby = manager.lobbies.get(lobby_id)
    if not lobby:
        return

    world = get_world()

    # Example victory conditions (customize based on scenarios)
    for player in lobby.players:
        if not player.country_id:
            continue

        country = world.get_country(player.country_id)
        if not country:
            continue

        # Example: Superpower victory (simplified)
        if country.tier == 1 and country.military > 90 and country.economy > 90:
            await manager.broadcast_to_lobby(lobby_id, {
                "type": "victory",
                "player_id": player.id,
                "player_name": player.name,
                "country_id": player.country_id,
                "victory_type": "superpower_dominance"
            })
            lobby.status = LobbyStatus.FINISHED
            return
