/**
 * Zone History Store - Historia-lite
 *
 * Tracks zone ownership changes to enable visual memory (scars, reconquests).
 * Design document: docs/VISUAL_DESIGN_ZONES.md
 */

import { create } from 'zustand';
import { InfluenceZone } from '@/lib/types';
import {
  ZoneHistory,
  ZoneVisualState,
  ZoneTransitionType,
  getZoneVisualState,
  getTransitionType,
  calculateChangeImportance,
} from '@/lib/zoneVisuals';

// =============================================================================
// TYPES
// =============================================================================

interface PendingTransition {
  zoneId: string;
  type: ZoneTransitionType;
  previousState: ZoneVisualState;
  newState: ZoneVisualState;
  timestamp: number;
}

interface ZoneHistoryStore {
  // State
  playerPower: string;
  zoneHistories: Record<string, ZoneHistory>;
  zoneDegradations: Record<string, number>;  // zoneId -> niveau 0-3
  pendingTransitions: PendingTransition[];
  activeTransition: PendingTransition | null;
  currentTurn: number;

  // Actions
  setPlayerPower: (power: string) => void;
  updateZones: (zones: InfluenceZone[], currentTurn: number) => void;
  getZoneHistory: (zoneId: string) => ZoneHistory | undefined;
  getZoneDegradation: (zoneId: string) => number;
  consumeNextTransition: () => PendingTransition | null;
  completeActiveTransition: () => void;
  startInsidiousLoss: (zoneId: string) => void;
  advanceDegradation: (zoneId: string) => boolean; // returns true if zone flips
  resetHistory: () => void;
}

// =============================================================================
// STORE
// =============================================================================

export const useZoneHistoryStore = create<ZoneHistoryStore>((set, get) => ({
  // Initial state
  playerPower: 'USA',
  zoneHistories: {},
  zoneDegradations: {},
  pendingTransitions: [],
  activeTransition: null,
  currentTurn: 0,

  // Set player power (USA or USSR typically)
  setPlayerPower: (power: string) => {
    set({ playerPower: power });
  },

  // Update zones and detect transitions
  updateZones: (zones: InfluenceZone[], currentTurn: number) => {
    const { playerPower, zoneHistories, zoneDegradations, pendingTransitions } = get();
    const newHistories = { ...zoneHistories };
    const newTransitions: PendingTransition[] = [...pendingTransitions];

    zones.forEach(zone => {
      const history = newHistories[zone.id];
      const previousOwner = history?.previousOwner;
      const wasControlled = history?.wasControlled || false;
      const isNowControlled = zone.dominant_power === playerPower;
      const wasLost = history?.wasLost || false;

      // Determine previous and new visual states
      const previousState = history
        ? getZoneVisualState(
            { ...zone, dominant_power: previousOwner || null } as InfluenceZone,
            playerPower,
            history
          )
        : 'neutral';
      const newState = getZoneVisualState(zone, playerPower, history);

      // Detect state change
      if (previousState !== newState || (wasControlled && !isNowControlled) || (!wasControlled && isNowControlled)) {
        // Update history
        if (isNowControlled && !wasControlled) {
          // Gained control
          const isReconquest = wasLost;
          newHistories[zone.id] = {
            zoneId: zone.id,
            wasControlled: true,
            wasLost: wasLost,
            wasReconquered: isReconquest,
            reconqueredAt: isReconquest ? currentTurn : undefined,
            previousOwner: zone.dominant_power || undefined,
          };

          // Determine transition importance
          const importance = calculateChangeImportance(
            zone,
            previousOwner || null,
            playerPower,
            [] // TODO: pass active crisis IDs
          );

          let transitionType: ZoneTransitionType = 'micro_gain';
          if (isReconquest) {
            transitionType = 'reconquest';
          } else if (importance === 'historic') {
            transitionType = 'historic_gain';
          } else if (importance === 'significant') {
            transitionType = 'significant_gain';
          }

          newTransitions.push({
            zoneId: zone.id,
            type: transitionType,
            previousState,
            newState: isReconquest ? 'reconquered' : 'controlled',
            timestamp: Date.now(),
          });

        } else if (!isNowControlled && wasControlled) {
          // Lost control
          newHistories[zone.id] = {
            ...history!,
            wasLost: true,
            lostAt: currentTurn,
            previousOwner: zone.dominant_power || undefined,
          };

          // Check if this was an insidious loss (degradation was building)
          const degradation = zoneDegradations[zone.id] || 0;
          const transitionType: ZoneTransitionType = degradation >= 2 ? 'insidious_loss' : 'brutal_loss';

          newTransitions.push({
            zoneId: zone.id,
            type: transitionType,
            previousState,
            newState: zone.dominant_power ? 'adverse' : 'neutral',
            timestamp: Date.now(),
          });

          // Clear degradation
          delete zoneDegradations[zone.id];
        }
      }

      // Track current owner for next comparison
      if (!newHistories[zone.id]) {
        newHistories[zone.id] = {
          zoneId: zone.id,
          wasControlled: isNowControlled,
          wasLost: false,
          wasReconquered: false,
          previousOwner: zone.dominant_power || undefined,
        };
      } else {
        newHistories[zone.id].previousOwner = zone.dominant_power || undefined;
      }
    });

    set({
      zoneHistories: newHistories,
      pendingTransitions: newTransitions,
      currentTurn,
    });
  },

  // Get zone history
  getZoneHistory: (zoneId: string) => {
    return get().zoneHistories[zoneId];
  },

  // Get zone degradation level
  getZoneDegradation: (zoneId: string) => {
    return get().zoneDegradations[zoneId] || 0;
  },

  // Get and remove next pending transition
  consumeNextTransition: () => {
    const { pendingTransitions } = get();
    if (pendingTransitions.length === 0) return null;

    const [next, ...rest] = pendingTransitions;
    set({
      pendingTransitions: rest,
      activeTransition: next,
    });
    return next;
  },

  // Complete active transition
  completeActiveTransition: () => {
    set({ activeTransition: null });
  },

  // Start insidious loss (soft power erosion)
  startInsidiousLoss: (zoneId: string) => {
    const { zoneDegradations } = get();
    set({
      zoneDegradations: {
        ...zoneDegradations,
        [zoneId]: 1,
      },
    });
  },

  // Advance degradation level
  advanceDegradation: (zoneId: string) => {
    const { zoneDegradations } = get();
    const current = zoneDegradations[zoneId] || 0;
    const newLevel = Math.min(current + 1, 3);

    set({
      zoneDegradations: {
        ...zoneDegradations,
        [zoneId]: newLevel,
      },
    });

    // Return true if max degradation reached (zone will flip)
    return newLevel >= 3;
  },

  // Reset all history
  resetHistory: () => {
    set({
      zoneHistories: {},
      zoneDegradations: {},
      pendingTransitions: [],
      activeTransition: null,
      currentTurn: 0,
    });
  },
}));
