'use client';

import { useState, useEffect, useCallback } from 'react';
import {
  Newspaper,
  Globe,
  TrendingUp,
  TrendingDown,
  Minus,
  RefreshCw,
  ChevronRight,
  X,
  Filter,
} from 'lucide-react';

// Types for media comments
interface MediaComment {
  source: string;
  source_id?: string;
  source_country?: string;
  source_bias?: string;
  headline_fr: string;
  excerpt_fr: string;
  sentiment: 'positive' | 'negative' | 'neutral';
}

interface MediaFeedProps {
  countryId: string;
  isOpen: boolean;
  onClose: () => void;
}

// Bias labels and colors
const BIAS_INFO: Record<string, { label: string; color: string; bgColor: string }> = {
  pro_west: { label: 'Pro-Occident', color: 'text-blue-400', bgColor: 'bg-blue-500/20' },
  pro_east: { label: 'Pro-Est', color: 'text-red-400', bgColor: 'bg-red-500/20' },
  pro_authoritarian: { label: 'Officiel', color: 'text-amber-400', bgColor: 'bg-amber-500/20' },
  neutral: { label: 'Neutre', color: 'text-gray-400', bgColor: 'bg-gray-500/20' },
  liberal: { label: 'Liberal', color: 'text-sky-400', bgColor: 'bg-sky-500/20' },
  conservative: { label: 'Conservateur', color: 'text-orange-400', bgColor: 'bg-orange-500/20' },
  economic: { label: 'Economique', color: 'text-emerald-400', bgColor: 'bg-emerald-500/20' },
  sensationalist: { label: 'Tabloide', color: 'text-pink-400', bgColor: 'bg-pink-500/20' },
};

// Country flags for sources
const SOURCE_FLAGS: Record<string, string> = {
  USA: '🇺🇸',
  GBR: '🇬🇧',
  FRA: '🇫🇷',
  DEU: '🇩🇪',
  RUS: '🇷🇺',
  CHN: '🇨🇳',
  QAT: '🇶🇦',
  SAU: '🇸🇦',
  IRN: '🇮🇷',
  ISR: '🇮🇱',
  JPN: '🇯🇵',
  SGP: '🇸🇬',
  IND: '🇮🇳',
  BRA: '🇧🇷',
  VEN: '🇻🇪',
  HKG: '🇭🇰',
  COG: '🇨🇬',
};

// Sentiment icons and colors
function getSentimentInfo(sentiment: string) {
  switch (sentiment) {
    case 'positive':
      return {
        icon: <TrendingUp className="w-4 h-4" />,
        color: 'text-green-400',
        bgColor: 'bg-green-500/20',
        label: 'Positif',
      };
    case 'negative':
      return {
        icon: <TrendingDown className="w-4 h-4" />,
        color: 'text-red-400',
        bgColor: 'bg-red-500/20',
        label: 'Negatif',
      };
    default:
      return {
        icon: <Minus className="w-4 h-4" />,
        color: 'text-gray-400',
        bgColor: 'bg-gray-500/20',
        label: 'Neutre',
      };
  }
}

export default function MediaFeed({ countryId, isOpen, onClose }: MediaFeedProps) {
  const [comments, setComments] = useState<MediaComment[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedBias, setSelectedBias] = useState<string | null>(null);
  const [showFilters, setShowFilters] = useState(false);

  // Fetch multiple media comments
  const fetchComments = useCallback(async () => {
    if (!countryId) return;

    setLoading(true);
    setError(null);

    try {
      const response = await fetch(
        `/api/ai-advisor/media/${countryId}/multiple?count=3`
      );
      const data = await response.json();

      if (data.success && data.comments) {
        setComments(data.comments);
      } else {
        setError(data.error || 'Impossible de charger les actualites');
      }
    } catch (err) {
      setError('Erreur de connexion');
    } finally {
      setLoading(false);
    }
  }, [countryId]);

  // Fetch single comment with specific bias
  const fetchWithBias = useCallback(async (bias: string) => {
    if (!countryId) return;

    setLoading(true);
    setError(null);

    try {
      const response = await fetch(
        `/api/ai-advisor/media/${countryId}?bias=${bias}`
      );
      const data = await response.json();

      if (data.success && data.comment) {
        setComments([data.comment]);
      } else {
        setError(data.error || 'Impossible de charger les actualites');
      }
    } catch (err) {
      setError('Erreur de connexion');
    } finally {
      setLoading(false);
    }
  }, [countryId]);

  // Initial load
  useEffect(() => {
    if (isOpen && countryId) {
      fetchComments();
    }
  }, [isOpen, countryId, fetchComments]);

  // Handle bias filter change
  const handleBiasFilter = (bias: string | null) => {
    setSelectedBias(bias);
    if (bias) {
      fetchWithBias(bias);
    } else {
      fetchComments();
    }
    setShowFilters(false);
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
      <div className="bg-slate-900 border border-slate-700 rounded-xl shadow-2xl w-full max-w-2xl max-h-[80vh] overflow-hidden">
        {/* Header */}
        <div className="bg-slate-800 px-4 py-3 border-b border-slate-700 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-sky-500/20 rounded-lg">
              <Newspaper className="w-5 h-5 text-sky-400" />
            </div>
            <div>
              <h2 className="font-bold text-lg text-white">Revue de Presse</h2>
              <p className="text-xs text-slate-400">Perspectives internationales</p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            {/* Filters button */}
            <div className="relative">
              <button
                onClick={() => setShowFilters(!showFilters)}
                className={`p-2 rounded-lg transition ${
                  selectedBias
                    ? 'bg-sky-500/20 text-sky-400'
                    : 'bg-slate-700 text-slate-400 hover:bg-slate-600'
                }`}
              >
                <Filter className="w-4 h-4" />
              </button>

              {/* Filter dropdown */}
              {showFilters && (
                <div className="absolute right-0 top-full mt-2 w-48 bg-slate-800 border border-slate-700 rounded-lg shadow-xl z-10">
                  <div className="p-2">
                    <button
                      onClick={() => handleBiasFilter(null)}
                      className={`w-full text-left px-3 py-2 rounded text-sm ${
                        !selectedBias ? 'bg-sky-500/20 text-sky-400' : 'text-slate-300 hover:bg-slate-700'
                      }`}
                    >
                      Tous les biais
                    </button>
                    {Object.entries(BIAS_INFO).map(([key, info]) => (
                      <button
                        key={key}
                        onClick={() => handleBiasFilter(key)}
                        className={`w-full text-left px-3 py-2 rounded text-sm flex items-center gap-2 ${
                          selectedBias === key ? info.bgColor + ' ' + info.color : 'text-slate-300 hover:bg-slate-700'
                        }`}
                      >
                        <span className={`w-2 h-2 rounded-full ${info.bgColor.replace('/20', '')}`} />
                        {info.label}
                      </button>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {/* Refresh button */}
            <button
              onClick={selectedBias ? () => fetchWithBias(selectedBias) : fetchComments}
              disabled={loading}
              className="p-2 bg-slate-700 text-slate-300 hover:bg-slate-600 rounded-lg transition disabled:opacity-50"
            >
              <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            </button>

            {/* Close button */}
            <button
              onClick={onClose}
              className="p-2 bg-slate-700 text-slate-300 hover:bg-slate-600 rounded-lg transition"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="p-4 overflow-y-auto max-h-[calc(80vh-80px)]">
          {loading && comments.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-12 text-slate-400">
              <RefreshCw className="w-8 h-8 animate-spin mb-3" />
              <p>Chargement des actualites...</p>
            </div>
          ) : error ? (
            <div className="flex flex-col items-center justify-center py-12 text-red-400">
              <p>{error}</p>
              <button
                onClick={fetchComments}
                className="mt-3 px-4 py-2 bg-slate-700 rounded-lg hover:bg-slate-600 transition text-sm"
              >
                Reessayer
              </button>
            </div>
          ) : comments.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-12 text-slate-400">
              <Newspaper className="w-8 h-8 mb-3 opacity-50" />
              <p>Aucune actualite disponible</p>
            </div>
          ) : (
            <div className="space-y-4">
              {comments.map((comment, index) => {
                const sentimentInfo = getSentimentInfo(comment.sentiment);
                const biasInfo = comment.source_bias ? BIAS_INFO[comment.source_bias] : null;
                const flag = comment.source_country ? SOURCE_FLAGS[comment.source_country] : '🌐';

                return (
                  <div
                    key={index}
                    className="bg-slate-800/50 border border-slate-700 rounded-lg overflow-hidden hover:border-slate-600 transition"
                  >
                    {/* Source header */}
                    <div className="px-4 py-2 bg-slate-800 border-b border-slate-700 flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <span className="text-lg">{flag}</span>
                        <span className="font-semibold text-white">{comment.source}</span>
                        {biasInfo && (
                          <span className={`text-xs px-2 py-0.5 rounded-full ${biasInfo.bgColor} ${biasInfo.color}`}>
                            {biasInfo.label}
                          </span>
                        )}
                      </div>
                      <div className={`flex items-center gap-1 ${sentimentInfo.color}`}>
                        {sentimentInfo.icon}
                        <span className="text-xs">{sentimentInfo.label}</span>
                      </div>
                    </div>

                    {/* Article content */}
                    <div className="p-4">
                      <h3 className="font-bold text-white text-lg leading-tight mb-2">
                        {comment.headline_fr}
                      </h3>
                      <p className="text-slate-300 text-sm leading-relaxed">
                        {comment.excerpt_fr}
                      </p>
                    </div>

                    {/* Footer */}
                    <div className="px-4 py-2 bg-slate-800/50 border-t border-slate-700/50 flex items-center justify-between">
                      <div className="flex items-center gap-2 text-xs text-slate-500">
                        <Globe className="w-3 h-3" />
                        <span>Perspective {biasInfo?.label.toLowerCase() || 'internationale'}</span>
                      </div>
                      <button className="flex items-center gap-1 text-xs text-sky-400 hover:text-sky-300 transition">
                        <span>Lire plus</span>
                        <ChevronRight className="w-3 h-3" />
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Footer info */}
        <div className="px-4 py-3 bg-slate-800/50 border-t border-slate-700 text-center text-xs text-slate-500">
          <Globe className="w-3 h-3 inline mr-1" />
          Sources: Reuters, Xinhua, Al Jazeera, RT, BBC et plus de 20 agences internationales
        </div>
      </div>
    </div>
  );
}
