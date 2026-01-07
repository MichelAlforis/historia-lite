'use client';

/**
 * GameOverDebrief - Ecran de debrief narratif post-defaite
 *
 * Remplace le GameOverScreen basique par un debrief narratif complet.
 * Le joueur comprend POURQUOI il a perdu sans voir de chiffres.
 *
 * Structure:
 * 1. Titre dramatique
 * 2. Narrative principal
 * 3. Causes cles (narrativisees)
 * 4. Dialogue leader (optionnel)
 * 5. Headlines presse
 * 6. Bouton nouvelle partie
 */

import { useState, useEffect } from 'react';

// Types
interface DebriefCause {
  turn: number;
  category: string;
  zone: string | null;
  zone_name_fr: string | null;
  actor: string | null;
  narrative_fr: string;
  contributed_to: string;
  severity: string;
}

interface LeaderDialogue {
  speaker: string;
  title: string;
  tone: string;
  message: string;
  country: string | null;
}

interface PressHeadline {
  source: string;
  source_id: string;
  headline: string;
  excerpt: string;
  sentiment: string;
  bias: string;
  country: string;
  credibility: string;
}

interface AIStrategicError {
  turn: number;
  error_type: string;
  belief_fr: string;
  reality_fr: string;
  consequence_fr: string;
}

interface GameDebrief {
  end_reason: string;
  victory: boolean;
  title_fr: string;
  narrative_fr: string;
  causes: DebriefCause[];
  leader_dialogue: LeaderDialogue | null;
  press_headlines: PressHeadline[];
  final_state_summary: Record<string, string>;
  ai_errors?: AIStrategicError[];
}

interface GameOverDebriefProps {
  victory: boolean | null;
  endReason: string | null;
  onNewGame: () => void;
}

// =============================================================================
// SUB-COMPONENTS
// =============================================================================

function CauseCard({ cause, index }: { cause: DebriefCause; index: number }) {
  const severityColors: Record<string, string> = {
    critical: 'border-red-500/50 bg-red-950/30',
    high: 'border-orange-500/50 bg-orange-950/30',
    medium: 'border-yellow-500/50 bg-yellow-950/30',
    low: 'border-slate-500/50 bg-slate-900/30',
  };

  const categoryIcons: Record<string, string> = {
    silence: '...',
    escalation: '↑',
    provocation: '!',
    omission: '?',
    isolation: '○',
    instability: '~',
    miscalc: '×',
  };

  return (
    <div
      className={`p-4 border rounded ${severityColors[cause.severity] || severityColors.medium}`}
      style={{ animationDelay: `${index * 200}ms` }}
    >
      <div className="flex items-center gap-2 mb-2">
        <span className="text-xl font-mono text-slate-400">
          {categoryIcons[cause.category] || '•'}
        </span>
        {cause.turn > 0 && (
          <span className="text-xs font-mono text-slate-500">
            Tour {cause.turn}
          </span>
        )}
        {cause.zone_name_fr && (
          <span className="text-xs font-mono text-cyan-400/70">
            {cause.zone_name_fr}
          </span>
        )}
      </div>
      <p className="text-sm text-slate-300 font-mono leading-relaxed">
        {cause.narrative_fr}
      </p>
      {cause.actor && (
        <p className="mt-2 text-xs text-slate-500 italic">
          — {cause.actor}
        </p>
      )}
    </div>
  );
}

function LeaderDialogueCard({ dialogue }: { dialogue: LeaderDialogue }) {
  const toneColors: Record<string, string> = {
    angry: 'border-red-500/30 text-red-400',
    threatening: 'border-orange-500/30 text-orange-400',
    bitter: 'border-purple-500/30 text-purple-400',
    cold: 'border-blue-500/30 text-blue-400',
    devastated: 'border-slate-500/30 text-slate-400',
    triumphant: 'border-cyan-500/30 text-cyan-400',
    resigned: 'border-slate-500/30 text-slate-400',
    solemn: 'border-slate-500/30 text-slate-300',
  };

  const toneClass = toneColors[dialogue.tone] || toneColors.cold;

  return (
    <div className={`p-4 border-l-2 ${toneClass} bg-slate-900/50`}>
      <div className="flex items-center gap-3 mb-3">
        <div className="w-10 h-10 rounded-full bg-slate-800 flex items-center justify-center text-lg">
          {dialogue.country === 'USSR' ? '☭' : dialogue.country === 'USA' ? '★' : '◆'}
        </div>
        <div>
          <p className="font-mono text-sm font-semibold">{dialogue.speaker}</p>
          <p className="text-xs text-slate-500">{dialogue.title}</p>
        </div>
      </div>
      <blockquote className="text-slate-300 italic font-mono text-sm leading-relaxed pl-4">
        "{dialogue.message}"
      </blockquote>
    </div>
  );
}

function PressHeadlinesCard({ headlines }: { headlines: PressHeadline[] }) {
  if (!headlines || headlines.length === 0) return null;

  return (
    <div className="space-y-2">
      <h3 className="text-xs font-mono text-slate-500 uppercase tracking-wider mb-3">
        La Presse Mondiale
      </h3>
      {headlines.map((headline, idx) => (
        <div
          key={idx}
          className="p-3 bg-slate-900/50 border border-slate-700/50 rounded"
        >
          <div className="flex items-center justify-between mb-1">
            <span className="text-xs font-mono text-slate-400 font-semibold">
              {headline.source}
            </span>
            <span className="text-[10px] text-slate-600 uppercase">
              {headline.country}
            </span>
          </div>
          <p className="font-mono text-sm text-slate-200 font-bold">
            {headline.headline}
          </p>
          {headline.excerpt && (
            <p className="text-xs text-slate-500 mt-1 italic">
              {headline.excerpt}
            </p>
          )}
        </div>
      ))}
    </div>
  );
}

function StateSummaryCard({ summary }: { summary: Record<string, string> }) {
  if (!summary || Object.keys(summary).length === 0) return null;

  const labels: Record<string, string> = {
    situation_mondiale: 'Situation Mondiale',
    situation_interieure: 'Situation Interieure',
    reputation: 'Reputation',
    equilibre_mondial: 'Equilibre Mondial',
  };

  return (
    <div className="p-4 bg-slate-900/30 border border-slate-700/30 rounded">
      <h3 className="text-xs font-mono text-slate-500 uppercase tracking-wider mb-3">
        Etat Final
      </h3>
      <div className="space-y-2">
        {Object.entries(summary).map(([key, value]) => (
          <div key={key} className="flex justify-between text-sm">
            <span className="text-slate-500 font-mono">
              {labels[key] || key}
            </span>
            <span className="text-slate-300 font-mono">{value}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

interface KremlinMisreadsCardProps {
  errors: AIStrategicError[];
  endReason?: string;
}

function KremlinMisreadsCard({ errors, endReason }: KremlinMisreadsCardProps) {
  if (!errors || errors.length === 0) return null;

  // Limiter a 2 erreurs max pour eviter le "debug screen"
  const topErrors = errors.slice(0, 2);

  // Tags de contexte selon le type d'erreur (vocabulaire coherent)
  const contextTags: Record<string, string> = {
    misread_player: 'Lecture politique',
    faction_conflict: 'Politique interne',
    underestimation: 'Renseignement',
    overestimation: 'Renseignement',
    stale_intel: 'Renseignement',
  };

  // Verdicts contextualises selon end_reason
  const verdictsByReason: Record<string, string[]> = {
    apocalypse: [
      'Leurs erreurs n\'ont pas declenche l\'apocalypse. Elles l\'ont rendue inevitable.',
      'Le Kremlin voyait un monde qui n\'existait plus.',
      'Quand la realite a rattrape Moscou, il etait trop tard.',
    ],
    coup_etat: [
      'Pendant que vous perdiez le controle, eux aussi.',
      'Le brouillard a trahi les deux camps.',
      'Moscou n\'a pas vu votre chute — elle preparait la sienne.',
    ],
    defeat_honorable: [
      'Meme victorieux, le Kremlin a joue avec des cartes incompletes.',
      'Leur victoire doit autant a vos erreurs qu\'aux leurs.',
      'Ils ont gagne sans vraiment comprendre pourquoi.',
    ],
  };
  const defaultVerdicts = [
    'Le brouillard a trahi Moscou.',
    'Le Kremlin a joue avec des cartes incompletes.',
    'Meme une superpuissance decide parfois a l\'aveugle.',
  ];
  const verdicts = verdictsByReason[endReason || ''] || defaultVerdicts;
  const verdict = verdicts[Math.floor(Math.random() * verdicts.length)];

  // Phrase de cloture in-universe (evite "partie" trop meta)
  const closingPhrases: Record<string, string> = {
    apocalypse: 'Ces erreurs n\'ont pas sauve le monde. Elles ont scelle son destin.',
    coup_etat: 'Ces erreurs n\'ont pas sauve le monde. Elles ont accelere sa chute.',
    defeat_honorable: 'Ces erreurs n\'ont pas change l\'issue. Elles ont change le prix.',
  };
  const closingPhrase = closingPhrases[endReason || ''] ||
    'Ces erreurs n\'ont pas sauve le monde. Elles ont change le cours des evenements.';

  return (
    <div className="p-4 bg-slate-900/40 border border-slate-700/40 rounded">
      <h3 className="text-xs font-mono text-slate-400 uppercase tracking-wider mb-2">
        Angles morts du Kremlin
      </h3>
      {/* Verdict en tete */}
      <p className="text-sm text-slate-500 font-mono italic mb-4">
        {verdict}
      </p>
      <div className="space-y-4">
        {topErrors.map((error, idx) => (
          <div key={idx} className="border-l-2 border-amber-500/30 pl-3">
            {/* Tag de contexte */}
            {contextTags[error.error_type] && (
              <span className="text-[10px] font-mono text-amber-500/50 uppercase tracking-wide">
                [{contextTags[error.error_type]}]
              </span>
            )}
            {/* Verdict en une phrase */}
            <p className="text-sm text-slate-300 font-mono leading-relaxed mt-1">
              {error.belief_fr}
            </p>
            {/* Consequence - le cout de l'erreur */}
            <p className="text-xs text-amber-400/60 font-mono mt-1 italic">
              {error.consequence_fr}
            </p>
          </div>
        ))}
      </div>
      {/* Phrase de cloture in-universe */}
      <p className="text-[11px] text-slate-500 font-mono mt-4 pt-3 border-t border-slate-700/30 italic">
        {closingPhrase}
      </p>
    </div>
  );
}

// =============================================================================
// MAIN COMPONENT
// =============================================================================

export default function GameOverDebrief({
  victory,
  endReason,
  onNewGame,
}: GameOverDebriefProps) {
  const [debrief, setDebrief] = useState<GameDebrief | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showCauses, setShowCauses] = useState(false);

  // Fetch debrief from API
  useEffect(() => {
    const fetchDebrief = async () => {
      try {
        const res = await fetch('/api/narrative/game-over-debrief');
        if (!res.ok) {
          // Fallback si l'API echoue
          throw new Error('Debrief non disponible');
        }
        const data = await res.json();
        setDebrief(data);
      } catch (err) {
        setError('Debrief non disponible');
        // Creer un debrief minimal de fallback
        setDebrief({
          end_reason: endReason || 'unknown',
          victory: victory || false,
          title_fr: victory ? 'Victoire' : 'Defaite',
          narrative_fr: 'La partie est terminee.',
          causes: [],
          leader_dialogue: null,
          press_headlines: [],
          final_state_summary: {},
        });
      } finally {
        setLoading(false);
        // Animer l'apparition des causes apres un delai
        setTimeout(() => setShowCauses(true), 1000);
      }
    };

    fetchDebrief();
  }, [endReason, victory]);

  if (loading) {
    return (
      <div className="min-h-screen bg-[#0a0e17] flex items-center justify-center">
        <div className="text-center">
          <div className="animate-pulse text-2xl font-mono text-slate-400">
            ...
          </div>
          <p className="text-sm text-slate-500 mt-2 font-mono">
            Analyse de la situation...
          </p>
        </div>
      </div>
    );
  }

  if (!debrief) {
    return (
      <div className="min-h-screen bg-[#0a0e17] flex items-center justify-center">
        <div className="text-center">
          <p className="text-slate-400">Erreur de chargement</p>
          <button
            onClick={onNewGame}
            className="mt-4 px-6 py-2 bg-cyan-500/10 border border-cyan-500/30 rounded text-cyan-400 font-mono text-sm"
          >
            Nouvelle Partie
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#0a0e17] overflow-y-auto">
      {/* Scanlines overlay */}
      <div className="fixed inset-0 pointer-events-none opacity-10 z-50">
        <div
          className="w-full h-full"
          style={{
            backgroundImage:
              'repeating-linear-gradient(0deg, transparent, transparent 1px, rgba(0,0,0,0.3) 2px, rgba(0,0,0,0.3) 3px)',
          }}
        />
      </div>

      <div className="max-w-2xl mx-auto px-6 py-12">
        {/* Title */}
        <div className="text-center mb-12">
          <div
            className={`text-5xl font-mono font-bold mb-4 ${
              debrief.victory ? 'text-cyan-400' : 'text-red-500'
            }`}
          >
            {debrief.victory ? 'VICTOIRE' : 'DEFAITE'}
          </div>
          <h1 className="text-xl font-mono text-slate-300 mb-4">
            {debrief.title_fr}
          </h1>
        </div>

        {/* Main Narrative */}
        <div className="mb-10">
          <p className="text-slate-400 font-mono text-sm leading-relaxed whitespace-pre-line">
            {debrief.narrative_fr}
          </p>
        </div>

        {/* Causes */}
        {debrief.causes && debrief.causes.length > 0 && (
          <div className={`mb-10 transition-opacity duration-1000 ${showCauses ? 'opacity-100' : 'opacity-0'}`}>
            <h2 className="text-xs font-mono text-slate-500 uppercase tracking-wider mb-4">
              Decisions Cles
            </h2>
            <div className="space-y-3">
              {debrief.causes.map((cause, idx) => (
                <CauseCard key={idx} cause={cause} index={idx} />
              ))}
            </div>
          </div>
        )}

        {/* Leader Dialogue */}
        {debrief.leader_dialogue && (
          <div className="mb-10">
            <LeaderDialogueCard dialogue={debrief.leader_dialogue} />
          </div>
        )}

        {/* Press Headlines */}
        {debrief.press_headlines && debrief.press_headlines.length > 0 && (
          <div className="mb-10">
            <PressHeadlinesCard headlines={debrief.press_headlines} />
          </div>
        )}

        {/* State Summary */}
        {debrief.final_state_summary &&
          Object.keys(debrief.final_state_summary).length > 0 && (
            <div className="mb-10">
              <StateSummaryCard summary={debrief.final_state_summary} />
            </div>
          )}

        {/* Kremlin Misreads - chapitre narratif, pas liste de bugs */}
        {debrief.ai_errors && debrief.ai_errors.length > 0 && (
          <div className="mb-10">
            <KremlinMisreadsCard errors={debrief.ai_errors} endReason={debrief.end_reason} />
          </div>
        )}

        {/* New Game Button */}
        <div className="text-center pt-8 border-t border-slate-800">
          <button
            onClick={onNewGame}
            className="px-8 py-3 bg-cyan-500/10 hover:bg-cyan-500/20 border border-cyan-500/30 rounded text-sm font-mono text-cyan-400 uppercase tracking-wider transition-colors"
          >
            Nouvelle Partie
          </button>
        </div>
      </div>
    </div>
  );
}
