'use client';

import { useState, useEffect } from 'react';
import {
  Trophy,
  Star,
  Lock,
  CheckCircle,
  X,
  Award,
  Sparkles,
  Shield,
  Sword,
  Eye,
  Crown,
  TrendingUp,
  Atom,
  Handshake,
  Clock,
  Flame,
  Skull,
  Heart,
  Cpu,
  Scale,
} from 'lucide-react';

interface AchievementProgress {
  achievement_id: string;
  current_value: number;
  target_value: number;
  progress_percent: number;
  unlocked: boolean;
  unlocked_at: string | null;
}

interface Achievement {
  id: string;
  name: string;
  name_fr: string;
  description: string;
  description_fr: string;
  icon: string;
  category: string;
  rarity: string;
  points: number;
  progress?: AchievementProgress;
  unlocked: boolean;
}

interface AchievementsSummary {
  total: number;
  unlocked: number;
  locked: number;
  completion_percent: number;
  points: number;
  max_points: number;
  by_rarity: Record<string, { total: number; unlocked: number }>;
}

interface AchievementsPanelProps {
  isOpen: boolean;
  onClose: () => void;
}

// Icon mapping
function getAchievementIcon(iconName: string) {
  const iconClass = "w-6 h-6";
  const icons: Record<string, JSX.Element> = {
    dove: <Heart className={iconClass} />,
    balance: <Scale className={iconClass} />,
    eye: <Eye className={iconClass} />,
    crown: <Crown className={iconClass} />,
    shield: <Shield className={iconClass} />,
    chart: <TrendingUp className={iconClass} />,
    wall: <Shield className={iconClass} />,
    handshake: <Handshake className={iconClass} />,
    atom: <Atom className={iconClass} />,
    star: <Star className={iconClass} />,
    skull: <Skull className={iconClass} />,
    cpu: <Cpu className={iconClass} />,
    fire: <Flame className={iconClass} />,
    sword: <Sword className={iconClass} />,
    clock: <Clock className={iconClass} />,
  };
  return icons[iconName] || <Trophy className={iconClass} />;
}

// Rarity colors
function getRarityColors(rarity: string) {
  const colors: Record<string, { bg: string; border: string; text: string; glow: string }> = {
    bronze: {
      bg: 'bg-amber-900/20',
      border: 'border-amber-600',
      text: 'text-amber-500',
      glow: 'shadow-amber-500/20',
    },
    silver: {
      bg: 'bg-gray-400/20',
      border: 'border-gray-400',
      text: 'text-gray-300',
      glow: 'shadow-gray-400/20',
    },
    gold: {
      bg: 'bg-yellow-500/20',
      border: 'border-yellow-500',
      text: 'text-yellow-400',
      glow: 'shadow-yellow-500/30',
    },
    platinum: {
      bg: 'bg-purple-400/20',
      border: 'border-purple-400',
      text: 'text-purple-300',
      glow: 'shadow-purple-400/30',
    },
  };
  return colors[rarity] || colors.bronze;
}

// Category colors
function getCategoryColor(category: string): string {
  const colors: Record<string, string> = {
    diplomacy: 'text-blue-400',
    military: 'text-red-400',
    economy: 'text-emerald-400',
    espionage: 'text-violet-400',
    expansion: 'text-amber-400',
    stability: 'text-cyan-400',
    reputation: 'text-pink-400',
    technology: 'text-indigo-400',
    resilience: 'text-lime-400',
    persistence: 'text-purple-400',
  };
  return colors[category] || 'text-gray-400';
}

export default function AchievementsPanel({ isOpen, onClose }: AchievementsPanelProps) {
  const [achievements, setAchievements] = useState<Achievement[]>([]);
  const [summary, setSummary] = useState<AchievementsSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<'all' | 'unlocked' | 'locked'>('all');

  useEffect(() => {
    if (isOpen) {
      fetchAchievements();
    }
  }, [isOpen]);

  const fetchAchievements = async () => {
    setLoading(true);
    try {
      const API_BASE = process.env.NEXT_PUBLIC_HISTORIA_API_URL || 'http://localhost:8001/api';
      const response = await fetch(`${API_BASE}/achievements`);
      const data = await response.json();
      setAchievements(data.achievements || []);
      setSummary(data.summary || null);
    } catch (error) {
      console.error('Failed to fetch achievements:', error);
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  const filteredAchievements = achievements.filter(a => {
    if (filter === 'unlocked') return a.unlocked;
    if (filter === 'locked') return !a.unlocked;
    return true;
  });

  // Sort: unlocked first, then by rarity (platinum > gold > silver > bronze)
  const rarityOrder = { platinum: 0, gold: 1, silver: 2, bronze: 3 };
  const sortedAchievements = [...filteredAchievements].sort((a, b) => {
    if (a.unlocked !== b.unlocked) return a.unlocked ? -1 : 1;
    return (rarityOrder[a.rarity as keyof typeof rarityOrder] || 4) -
           (rarityOrder[b.rarity as keyof typeof rarityOrder] || 4);
  });

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
      <div className="bg-stone-900 rounded-2xl w-full max-w-3xl max-h-[85vh] overflow-hidden shadow-2xl border border-stone-700">
        {/* Header */}
        <div className="bg-gradient-to-r from-amber-600 to-yellow-500 px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Trophy className="w-8 h-8 text-white" />
              <div>
                <h2 className="text-xl font-bold text-white">Achievements</h2>
                {summary && (
                  <p className="text-amber-100 text-sm">
                    {summary.unlocked}/{summary.total} debloques - {summary.points} pts
                  </p>
                )}
              </div>
            </div>
            <button
              onClick={onClose}
              className="p-2 hover:bg-white/20 rounded-lg transition"
            >
              <X className="w-5 h-5 text-white" />
            </button>
          </div>

          {/* Progress bar */}
          {summary && (
            <div className="mt-3">
              <div className="h-2 bg-amber-800 rounded-full overflow-hidden">
                <div
                  className="h-full bg-white transition-all duration-500"
                  style={{ width: `${summary.completion_percent}%` }}
                />
              </div>
              <div className="flex justify-between mt-1 text-xs text-amber-100">
                <span>{Math.round(summary.completion_percent)}% complete</span>
                <span>{summary.points}/{summary.max_points} points</span>
              </div>
            </div>
          )}
        </div>

        {/* Filter tabs */}
        <div className="flex gap-2 px-6 py-3 border-b border-stone-700">
          {(['all', 'unlocked', 'locked'] as const).map((f) => (
            <button
              key={f}
              onClick={() => setFilter(f)}
              className={`px-4 py-1.5 rounded-lg text-sm font-medium transition ${
                filter === f
                  ? 'bg-amber-500 text-white'
                  : 'bg-stone-800 text-stone-400 hover:text-white'
              }`}
            >
              {f === 'all' ? 'Tous' : f === 'unlocked' ? 'Debloques' : 'Verrouilles'}
            </button>
          ))}
        </div>

        {/* Achievements list */}
        <div className="p-6 overflow-y-auto max-h-[calc(85vh-200px)]">
          {loading ? (
            <div className="flex items-center justify-center py-12">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-amber-500" />
            </div>
          ) : sortedAchievements.length === 0 ? (
            <div className="text-center py-12 text-stone-500">
              Aucun achievement dans cette categorie
            </div>
          ) : (
            <div className="grid gap-3">
              {sortedAchievements.map((achievement) => {
                const rarityColors = getRarityColors(achievement.rarity);
                const progress = achievement.progress;

                return (
                  <div
                    key={achievement.id}
                    className={`relative rounded-xl border ${rarityColors.border} ${rarityColors.bg} p-4 transition
                      ${achievement.unlocked ? `shadow-lg ${rarityColors.glow}` : 'opacity-60'}`}
                  >
                    <div className="flex items-start gap-4">
                      {/* Icon */}
                      <div className={`p-3 rounded-xl ${achievement.unlocked ? rarityColors.bg : 'bg-stone-800'} ${rarityColors.text}`}>
                        {achievement.unlocked ? (
                          getAchievementIcon(achievement.icon)
                        ) : (
                          <Lock className="w-6 h-6 text-stone-500" />
                        )}
                      </div>

                      {/* Content */}
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-1">
                          <h3 className={`font-bold ${achievement.unlocked ? 'text-white' : 'text-stone-400'}`}>
                            {achievement.name_fr}
                          </h3>
                          {achievement.unlocked && (
                            <CheckCircle className="w-4 h-4 text-emerald-400" />
                          )}
                          <span className={`text-xs px-2 py-0.5 rounded-full ${rarityColors.bg} ${rarityColors.text} border ${rarityColors.border}`}>
                            {achievement.rarity}
                          </span>
                        </div>

                        <p className="text-sm text-stone-400 mb-2">
                          {achievement.description_fr}
                        </p>

                        {/* Progress bar for locked achievements */}
                        {!achievement.unlocked && progress && progress.target_value > 0 && (
                          <div className="mt-2">
                            <div className="flex justify-between text-xs text-stone-500 mb-1">
                              <span>Progression</span>
                              <span>{Math.round(progress.progress_percent)}%</span>
                            </div>
                            <div className="h-1.5 bg-stone-700 rounded-full overflow-hidden">
                              <div
                                className={`h-full ${rarityColors.text.replace('text-', 'bg-')} transition-all`}
                                style={{ width: `${progress.progress_percent}%` }}
                              />
                            </div>
                          </div>
                        )}
                      </div>

                      {/* Points */}
                      <div className="text-right">
                        <div className={`flex items-center gap-1 ${rarityColors.text}`}>
                          <Award className="w-4 h-4" />
                          <span className="font-bold">{achievement.points}</span>
                        </div>
                        <span className={`text-xs ${getCategoryColor(achievement.category)}`}>
                          {achievement.category}
                        </span>
                      </div>
                    </div>

                    {/* Unlocked badge */}
                    {achievement.unlocked && (
                      <div className="absolute top-2 right-2">
                        <Sparkles className={`w-4 h-4 ${rarityColors.text} animate-pulse`} />
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
