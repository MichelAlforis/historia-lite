/**
 * Zone Visual System - Historia-lite
 *
 * Design document: docs/VISUAL_DESIGN_ZONES.md
 *
 * Principe: Le joueur RESSENT avant de comprendre.
 * La carte EST le score.
 */

import { InfluenceZone } from './types';

// =============================================================================
// TYPES
// =============================================================================

export type ZoneVisualState =
  | 'neutral'      // Gris bleute, instable
  | 'controlled'   // Bleu profond, stable
  | 'adverse'      // Rouge sombre, menacant
  | 'reconquered'; // Bleu + cicatrice

export type ZoneTransitionType =
  | 'none'
  | 'micro_gain'      // 80% - pas d'interruption
  | 'significant_gain' // 15-20% - bref accent
  | 'historic_gain'    // 1-5% - moment iconique
  | 'brutal_loss'      // < 1s - choc
  | 'insidious_loss'   // 2-3 tours - poison
  | 'reconquest';      // victoire + regret

export interface ZoneHistory {
  zoneId: string;
  wasControlled: boolean;      // A ete controlee par le joueur
  wasLost: boolean;            // A ete perdue
  wasReconquered: boolean;     // A ete reconquise
  lostAt?: number;             // Tour de la perte
  reconqueredAt?: number;      // Tour de la reconquete
  previousOwner?: string;      // Ancien proprietaire
}

export interface ZoneVisualConfig {
  state: ZoneVisualState;
  transition: ZoneTransitionType;
  hasScar: boolean;            // Cicatrice visible (reconquete)
  isContested: boolean;        // Zone disputee
  degradationLevel: number;    // 0-3 pour perte insidieuse
}

// =============================================================================
// COULEURS - Palette Cold War
// =============================================================================

export const ZONE_COLORS = {
  // Etats de base
  neutral: {
    fill: 'rgba(100, 116, 139, 0.45)',      // Gris bleute
    stroke: 'rgba(148, 163, 184, 0.3)',
    glow: 'none',
  },
  controlled: {
    fill: 'rgba(30, 58, 138, 0.65)',        // Bleu profond stable
    stroke: 'rgba(59, 130, 246, 0.5)',
    glow: 'drop-shadow(0 0 3px rgba(59, 130, 246, 0.3))',
  },
  adverse: {
    fill: 'rgba(127, 29, 29, 0.65)',        // Rouge sombre
    stroke: 'rgba(185, 28, 28, 0.6)',
    glow: 'none',
  },
  reconquered: {
    fill: 'rgba(30, 58, 138, 0.55)',        // Bleu moins vif
    stroke: 'rgba(59, 130, 246, 0.4)',
    glow: 'none',
    scarPattern: 'url(#scar-pattern)',       // Pattern de cicatrice
  },
  contested: {
    fill: 'rgba(113, 113, 122, 0.5)',       // Gris instable
    stroke: 'rgba(234, 179, 8, 0.5)',
    strokeDasharray: '2,1',
  },

  // Degradation (perte insidieuse)
  degradation: [
    'rgba(30, 58, 138, 0.55)',   // Niveau 0 - normal
    'rgba(55, 65, 81, 0.55)',    // Niveau 1 - ternit
    'rgba(75, 85, 99, 0.5)',     // Niveau 2 - instable
    'rgba(107, 114, 128, 0.45)', // Niveau 3 - pre-bascule
  ],
} as const;

// =============================================================================
// TRANSITIONS - Durees en ms
// =============================================================================

export const ZONE_TRANSITIONS = {
  micro_gain: {
    duration: 300,
    easing: 'ease-out',
    delay: 0,
    pauseGame: false,
  },
  significant_gain: {
    duration: 500,
    easing: 'ease-in-out',
    delay: 0,
    pauseGame: false,
    dimWorld: 0.1,  // Leger assombrissement
  },
  historic_gain: {
    duration: 2000,
    easing: 'ease-in-out',
    delay: 200,
    pauseGame: true,
    dimWorld: 0.3,
    silenceAudio: true,
    phases: [
      { at: 0, action: 'dim_world' },
      { at: 200, action: 'focus_zone' },
      { at: 600, action: 'color_transition' },
      { at: 1100, action: 'breathing_start' },
      { at: 1500, action: 'restore_world' },
      { at: 2000, action: 'complete' },
    ],
  },
  brutal_loss: {
    duration: 800,
    easing: 'ease-out',
    delay: 0,
    pauseGame: false,
    flash: true,
    silenceAfter: 500,
  },
  insidious_loss: {
    duration: 0, // Se deroule sur plusieurs tours
    degradationPerTurn: 1,
    maxDegradation: 3,
  },
  reconquest: {
    duration: 1200,
    easing: 'ease-out',
    delay: 0,
    pauseGame: false,
    addScar: true,
  },
} as const;

// =============================================================================
// FONCTIONS UTILITAIRES
// =============================================================================

/**
 * Determine l'etat visuel d'une zone
 */
export function getZoneVisualState(
  zone: InfluenceZone,
  playerPower: string,
  history: ZoneHistory | undefined
): ZoneVisualState {
  const isPlayerControlled = zone.dominant_power === playerPower;
  const isContested = zone.contested_by.length > 0;

  // Zone reconquise (cicatrice)
  if (history?.wasReconquered && isPlayerControlled) {
    return 'reconquered';
  }

  // Zone controlee par le joueur
  if (isPlayerControlled) {
    return 'controlled';
  }

  // Zone controlee par l'adversaire
  if (zone.dominant_power && zone.dominant_power !== playerPower) {
    return 'adverse';
  }

  // Zone neutre/contestee
  return 'neutral';
}

/**
 * Determine le type de transition entre deux etats
 */
export function getTransitionType(
  previousState: ZoneVisualState,
  newState: ZoneVisualState,
  zone: InfluenceZone,
  isStrategicZone: boolean,
  isCrisisResolution: boolean
): ZoneTransitionType {
  // Prise de zone
  if (newState === 'controlled' && previousState !== 'controlled') {
    if (previousState === 'adverse' || isCrisisResolution) {
      return 'historic_gain'; // 1-5%
    }
    if (isStrategicZone || zone.has_oil) {
      return 'significant_gain'; // 15-20%
    }
    return 'micro_gain'; // 80%
  }

  // Reconquete
  if (newState === 'reconquered') {
    return 'reconquest';
  }

  // Perte de zone
  if (previousState === 'controlled' && newState !== 'controlled') {
    // Pour l'instant, perte brutale par defaut
    // La perte insidieuse est geree par degradationLevel
    return 'brutal_loss';
  }

  return 'none';
}

/**
 * Obtient la configuration visuelle complete d'une zone
 */
export function getZoneVisualConfig(
  zone: InfluenceZone,
  playerPower: string,
  history: ZoneHistory | undefined,
  degradationLevel: number = 0
): ZoneVisualConfig {
  const state = getZoneVisualState(zone, playerPower, history);

  return {
    state,
    transition: 'none', // A determiner par comparaison avec etat precedent
    hasScar: history?.wasReconquered === true,
    isContested: zone.contested_by.length > 0,
    degradationLevel,
  };
}

/**
 * Obtient les styles SVG pour une zone
 */
export function getZoneSVGStyles(config: ZoneVisualConfig): {
  fill: string;
  stroke: string;
  strokeWidth: number;
  strokeDasharray: string;
  filter: string;
  opacity: number;
} {
  const colors = ZONE_COLORS[config.state] || ZONE_COLORS.neutral;

  // Appliquer la degradation si en cours
  let fill: string = colors.fill;
  if (config.degradationLevel > 0 && config.state === 'controlled') {
    fill = ZONE_COLORS.degradation[Math.min(config.degradationLevel, 3)] as string;
  }

  // Zone contestee = bordure en pointilles
  const strokeDasharray = config.isContested ? '2,1' : 'none';

  return {
    fill,
    stroke: colors.stroke,
    strokeWidth: config.hasScar ? 0.4 : 0.2,
    strokeDasharray,
    filter: 'glow' in colors ? colors.glow : 'none',
    opacity: 1,
  };
}

/**
 * Calcule le niveau d'importance d'un changement de zone
 * pour determiner si c'est un moment historique
 */
export function calculateChangeImportance(
  zone: InfluenceZone,
  previousOwner: string | null,
  newOwner: string,
  activeCrisisIds: string[]
): 'micro' | 'significant' | 'historic' {
  // Fin de crise majeure = historique
  // (A implementer avec les crises)

  // Zone strategique (petrole + ressources) = significatif
  if (zone.has_oil && zone.has_strategic_resources) {
    return 'significant';
  }

  // Renversement d'equilibre (prise sur l'adversaire) = historique
  if (previousOwner && previousOwner !== newOwner) {
    return 'historic';
  }

  // Zone avec petrole = significatif
  if (zone.has_oil) {
    return 'significant';
  }

  return 'micro';
}

// =============================================================================
// SVG PATTERNS (pour cicatrices et textures)
// =============================================================================

export const SVG_PATTERNS = `
  <!-- Cicatrice de reconquete -->
  <pattern id="scar-pattern" patternUnits="userSpaceOnUse" width="4" height="4">
    <line x1="0" y1="4" x2="4" y2="0" stroke="rgba(127, 29, 29, 0.15)" stroke-width="0.5"/>
  </pattern>

  <!-- Texture instable (zone neutre) -->
  <pattern id="unstable-pattern" patternUnits="userSpaceOnUse" width="3" height="3">
    <rect width="3" height="3" fill="rgba(0,0,0,0)"/>
    <circle cx="1.5" cy="1.5" r="0.3" fill="rgba(255,255,255,0.05)"/>
  </pattern>

  <!-- Grain de degradation -->
  <filter id="degradation-noise">
    <feTurbulence type="fractalNoise" baseFrequency="0.9" numOctaves="3" result="noise"/>
    <feDisplacementMap in="SourceGraphic" in2="noise" scale="1" xChannelSelector="R" yChannelSelector="G"/>
  </filter>
`;

// =============================================================================
// ANIMATIONS CSS (a ajouter dans globals.css si besoin)
// =============================================================================

export const ZONE_ANIMATIONS_CSS = `
  /* Respiration lente pour zones controlees */
  @keyframes zone-breathing {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.92; }
  }

  .zone-controlled {
    animation: zone-breathing 4s ease-in-out infinite;
  }

  /* Flash mat pour perte brutale */
  @keyframes zone-brutal-loss {
    0% { fill: rgba(30, 58, 138, 0.65); }
    15% { fill: rgba(127, 29, 29, 0.8); }
    100% { fill: rgba(127, 29, 29, 0.65); }
  }

  /* Transition historique */
  @keyframes zone-historic-gain {
    0% { opacity: 0.7; filter: brightness(0.8); }
    30% { opacity: 1; filter: brightness(1.1); }
    100% { opacity: 1; filter: brightness(1); }
  }

  /* Tremblement pour zone en degradation */
  @keyframes zone-trembling {
    0%, 100% { transform: translate(0, 0); }
    25% { transform: translate(0.1px, 0); }
    75% { transform: translate(-0.1px, 0); }
  }

  .zone-degrading {
    animation: zone-trembling 0.5s ease-in-out infinite;
  }
`;
