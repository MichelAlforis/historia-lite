// Historia Lite - Multiplayer State Store (Zustand)
import { create } from 'zustand';

// Types
export interface PlayerInfo {
  id: string;
  name: string;
  country_id: string | null;
  is_ready: boolean;
  is_host: boolean;
  connected_at: string;
}

export interface ChatMessage {
  id: string;
  player_id: string;
  player_name: string;
  content: string;
  timestamp: string;
  is_private: boolean;
  recipient_id?: string;
}

export interface LobbyInfo {
  id: string;
  name: string;
  host_id: string;
  max_players: number;
  game_mode: 'simultaneous' | 'turn_based';
  turn_timer: number;
  status: 'waiting' | 'in_progress' | 'finished';
  players: PlayerInfo[];
  created_at: string;
  scenario_id?: string;
}

export interface GameAction {
  type: string;
  player_id: string;
  data: Record<string, unknown>;
  year: number;
}

export type WebSocketMessage =
  | { type: 'player_joined'; player: PlayerInfo }
  | { type: 'player_left'; player_id: string }
  | { type: 'player_ready'; player_id: string; is_ready: boolean }
  | { type: 'country_selected'; player_id: string; country_id: string }
  | { type: 'game_started'; start_year: number }
  | { type: 'chat_message'; message: ChatMessage }
  | { type: 'game_action'; action: GameAction }
  | { type: 'turn_ended'; player_id: string; year: number }
  | { type: 'all_turns_complete'; year: number }
  | { type: 'world_state_update'; world_state: Record<string, unknown> }
  | { type: 'game_over'; winner_id: string; reason: string }
  | { type: 'diplomacy_request'; from_player: string; request_type: string; data: Record<string, unknown> }
  | { type: 'diplomacy_response'; request_id: string; accepted: boolean }
  | { type: 'error'; message: string };

interface MultiplayerStore {
  // Connection state
  socket: WebSocket | null;
  connected: boolean;
  connectionError: string | null;

  // Player state
  playerId: string | null;
  playerName: string | null;

  // Lobby state
  currentLobby: LobbyInfo | null;
  availableLobbies: LobbyInfo[];

  // Game state
  isGameStarted: boolean;
  currentTurn: number;
  myTurnComplete: boolean;
  turnTimer: number | null;

  // Chat state
  chatMessages: ChatMessage[];
  unreadMessages: number;

  // Actions
  setPlayerId: (id: string) => void;
  setPlayerName: (name: string) => void;

  // Connection actions
  connect: (lobbyId: string, playerId: string) => void;
  disconnect: () => void;

  // Lobby actions
  fetchLobbies: () => Promise<void>;
  createLobby: (name: string, maxPlayers: number, gameMode: 'simultaneous' | 'turn_based', turnTimer: number) => Promise<LobbyInfo | null>;
  joinLobby: (lobbyId: string) => Promise<boolean>;
  leaveLobby: () => Promise<void>;
  selectCountry: (countryId: string) => Promise<void>;
  toggleReady: () => Promise<void>;
  startGame: () => Promise<void>;

  // Game actions
  sendGameAction: (actionType: string, data: Record<string, unknown>) => void;
  endTurn: () => void;

  // Chat actions
  sendChatMessage: (content: string, recipientId?: string) => void;
  markMessagesRead: () => void;

  // Diplomacy actions
  sendDiplomacyRequest: (targetPlayerId: string, requestType: string, data: Record<string, unknown>) => void;
  respondToDiplomacy: (requestId: string, accepted: boolean) => void;

  // Internal
  handleMessage: (message: WebSocketMessage) => void;
  clearError: () => void;
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001/api';
const WS_BASE = API_BASE.replace('http', 'ws').replace('/api', '');

export const useMultiplayerStore = create<MultiplayerStore>((set, get) => ({
  // Initial state
  socket: null,
  connected: false,
  connectionError: null,
  playerId: null,
  playerName: null,
  currentLobby: null,
  availableLobbies: [],
  isGameStarted: false,
  currentTurn: 0,
  myTurnComplete: false,
  turnTimer: null,
  chatMessages: [],
  unreadMessages: 0,

  setPlayerId: (id) => set({ playerId: id }),
  setPlayerName: (name) => set({ playerName: name }),

  // Connect to lobby WebSocket
  connect: (lobbyId, playerId) => {
    const { socket } = get();
    if (socket) {
      socket.close();
    }

    const ws = new WebSocket(`${WS_BASE}/api/multiplayer/ws/${lobbyId}/${playerId}`);

    ws.onopen = () => {
      set({ socket: ws, connected: true, connectionError: null });
    };

    ws.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data) as WebSocketMessage;
        get().handleMessage(message);
      } catch (error) {
        console.error('Failed to parse WebSocket message:', error);
      }
    };

    ws.onerror = () => {
      set({ connectionError: 'Erreur de connexion WebSocket' });
    };

    ws.onclose = () => {
      set({ socket: null, connected: false });
    };
  },

  disconnect: () => {
    const { socket } = get();
    if (socket) {
      socket.close();
    }
    set({
      socket: null,
      connected: false,
      currentLobby: null,
      isGameStarted: false,
      chatMessages: [],
    });
  },

  // Fetch available lobbies
  fetchLobbies: async () => {
    try {
      const response = await fetch(`${API_BASE}/multiplayer/lobbies`);
      const data = await response.json();
      set({ availableLobbies: data.lobbies || [] });
    } catch (error) {
      console.error('Failed to fetch lobbies:', error);
    }
  },

  // Create a new lobby
  createLobby: async (name, maxPlayers, gameMode, turnTimer) => {
    const { playerId, playerName } = get();
    if (!playerId || !playerName) return null;

    try {
      const response = await fetch(`${API_BASE}/multiplayer/lobbies`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name,
          host_id: playerId,
          host_name: playerName,
          max_players: maxPlayers,
          game_mode: gameMode,
          turn_timer: turnTimer,
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to create lobby');
      }

      const lobby = await response.json();
      set({ currentLobby: lobby });

      // Connect to WebSocket
      get().connect(lobby.id, playerId);

      return lobby;
    } catch (error) {
      console.error('Failed to create lobby:', error);
      set({ connectionError: 'Impossible de creer le salon' });
      return null;
    }
  },

  // Join an existing lobby
  joinLobby: async (lobbyId) => {
    const { playerId, playerName } = get();
    if (!playerId || !playerName) return false;

    try {
      const response = await fetch(`${API_BASE}/multiplayer/lobbies/${lobbyId}/join`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          player_id: playerId,
          player_name: playerName,
        }),
      });

      if (!response.ok) {
        const error = await response.json();
        set({ connectionError: error.detail || 'Impossible de rejoindre le salon' });
        return false;
      }

      const lobby = await response.json();
      set({ currentLobby: lobby });

      // Connect to WebSocket
      get().connect(lobbyId, playerId);

      return true;
    } catch (error) {
      console.error('Failed to join lobby:', error);
      set({ connectionError: 'Impossible de rejoindre le salon' });
      return false;
    }
  },

  // Leave current lobby
  leaveLobby: async () => {
    const { currentLobby, playerId } = get();
    if (!currentLobby || !playerId) return;

    try {
      await fetch(`${API_BASE}/multiplayer/lobbies/${currentLobby.id}/leave`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ player_id: playerId }),
      });
    } catch (error) {
      console.error('Failed to leave lobby:', error);
    }

    get().disconnect();
  },

  // Select a country
  selectCountry: async (countryId) => {
    const { currentLobby, playerId } = get();
    if (!currentLobby || !playerId) return;

    try {
      const response = await fetch(`${API_BASE}/multiplayer/lobbies/${currentLobby.id}/select-country`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          player_id: playerId,
          country_id: countryId,
        }),
      });

      if (!response.ok) {
        const error = await response.json();
        set({ connectionError: error.detail });
      }
    } catch (error) {
      console.error('Failed to select country:', error);
    }
  },

  // Toggle ready status
  toggleReady: async () => {
    const { currentLobby, playerId } = get();
    if (!currentLobby || !playerId) return;

    try {
      await fetch(`${API_BASE}/multiplayer/lobbies/${currentLobby.id}/ready`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ player_id: playerId }),
      });
    } catch (error) {
      console.error('Failed to toggle ready:', error);
    }
  },

  // Start the game (host only)
  startGame: async () => {
    const { currentLobby, playerId } = get();
    if (!currentLobby || !playerId) return;

    try {
      const response = await fetch(`${API_BASE}/multiplayer/lobbies/${currentLobby.id}/start`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ host_id: playerId }),
      });

      if (!response.ok) {
        const error = await response.json();
        set({ connectionError: error.detail });
      }
    } catch (error) {
      console.error('Failed to start game:', error);
    }
  },

  // Send a game action
  sendGameAction: (actionType, data) => {
    const { socket, playerId, currentTurn } = get();
    if (!socket || socket.readyState !== WebSocket.OPEN || !playerId) return;

    socket.send(JSON.stringify({
      type: 'game_action',
      action_type: actionType,
      player_id: playerId,
      data,
      year: currentTurn,
    }));
  },

  // End current turn
  endTurn: () => {
    const { socket, playerId, currentTurn } = get();
    if (!socket || socket.readyState !== WebSocket.OPEN || !playerId) return;

    socket.send(JSON.stringify({
      type: 'end_turn',
      player_id: playerId,
      year: currentTurn,
    }));

    set({ myTurnComplete: true });
  },

  // Send chat message
  sendChatMessage: (content, recipientId) => {
    const { socket, playerId, playerName } = get();
    if (!socket || socket.readyState !== WebSocket.OPEN || !playerId || !playerName) return;

    socket.send(JSON.stringify({
      type: 'chat',
      player_id: playerId,
      player_name: playerName,
      content,
      is_private: !!recipientId,
      recipient_id: recipientId,
    }));
  },

  markMessagesRead: () => set({ unreadMessages: 0 }),

  // Diplomacy
  sendDiplomacyRequest: (targetPlayerId, requestType, data) => {
    const { socket, playerId } = get();
    if (!socket || socket.readyState !== WebSocket.OPEN || !playerId) return;

    socket.send(JSON.stringify({
      type: 'diplomacy_request',
      from_player: playerId,
      to_player: targetPlayerId,
      request_type: requestType,
      data,
    }));
  },

  respondToDiplomacy: (requestId, accepted) => {
    const { socket, playerId } = get();
    if (!socket || socket.readyState !== WebSocket.OPEN || !playerId) return;

    socket.send(JSON.stringify({
      type: 'diplomacy_response',
      request_id: requestId,
      player_id: playerId,
      accepted,
    }));
  },

  // Handle incoming WebSocket messages
  handleMessage: (message) => {
    const { currentLobby, chatMessages, playerId } = get();

    switch (message.type) {
      case 'player_joined':
        if (currentLobby) {
          set({
            currentLobby: {
              ...currentLobby,
              players: [...currentLobby.players, message.player],
            },
          });
        }
        break;

      case 'player_left':
        if (currentLobby) {
          set({
            currentLobby: {
              ...currentLobby,
              players: currentLobby.players.filter(p => p.id !== message.player_id),
            },
          });
        }
        break;

      case 'player_ready':
        if (currentLobby) {
          set({
            currentLobby: {
              ...currentLobby,
              players: currentLobby.players.map(p =>
                p.id === message.player_id ? { ...p, is_ready: message.is_ready } : p
              ),
            },
          });
        }
        break;

      case 'country_selected':
        if (currentLobby) {
          set({
            currentLobby: {
              ...currentLobby,
              players: currentLobby.players.map(p =>
                p.id === message.player_id ? { ...p, country_id: message.country_id } : p
              ),
            },
          });
        }
        break;

      case 'game_started':
        if (currentLobby) {
          set({
            isGameStarted: true,
            currentTurn: message.start_year,
            myTurnComplete: false,
            currentLobby: {
              ...currentLobby,
              status: 'in_progress',
            },
          });
        }
        break;

      case 'chat_message':
        set({
          chatMessages: [...chatMessages, message.message],
          unreadMessages: get().unreadMessages + 1,
        });
        break;

      case 'turn_ended':
        // Another player ended their turn
        break;

      case 'all_turns_complete':
        // All players finished, advance to next year
        set({
          currentTurn: message.year + 1,
          myTurnComplete: false,
        });
        break;

      case 'world_state_update':
        // World state updated - could integrate with gameStore
        break;

      case 'game_over':
        if (currentLobby) {
          set({
            currentLobby: {
              ...currentLobby,
              status: 'finished',
            },
          });
        }
        // Could show victory screen
        break;

      case 'error':
        set({ connectionError: message.message });
        break;
    }
  },

  clearError: () => set({ connectionError: null }),
}));
