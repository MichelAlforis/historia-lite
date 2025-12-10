'use client';

import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { Country, COUNTRY_FLAGS } from '@/lib/types';

// ============================================================================
// TYPES (simplifiés)
// ============================================================================

type AgreementType =
  | 'peace_treaty'
  | 'trade_agreement'
  | 'defensive_alliance'
  | 'oil_agreement'
  | 'development_program'
  | 'non_aggression_pact'
  | 'technology_transfer'
  | 'military_access';

interface AgreementCondition {
  id: string;
  type: 'demand' | 'offer';
  category: string;
  label: string;
  label_fr: string;
  value: number;
}

interface DiplomaticAgreement {
  id: string;
  type: AgreementType;
  initiator: string;
  target: string;
  status: string;
  year_proposed: number;
  year_expires?: number;
  conditions_offered: AgreementCondition[];
  conditions_demanded: AgreementCondition[];
  acceptance_probability: number;
  accepted?: boolean;
  message_fr?: string;
}

interface NegotiationHistory {
  id: string;
  year: number;
  action: string;
  actor: string;
  details_fr: string;
}

// ============================================================================
// CONFIGURATION SIMPLIFIÉE
// ============================================================================

const AGREEMENT_TYPES: Record<AgreementType, {
  label_fr: string;
  icon: string;
  color: string;
  description_fr: string;
  min_relation: number;
  common: boolean; // Types courants affichés par défaut
}> = {
  peace_treaty: {
    label_fr: 'Traité de paix',
    icon: '🕊️',
    color: '#10b981',
    description_fr: 'Met fin à un conflit',
    min_relation: -100,
    common: true,
  },
  trade_agreement: {
    label_fr: 'Accord commercial',
    icon: '📦',
    color: '#3b82f6',
    description_fr: 'Augmente les échanges économiques',
    min_relation: 0,
    common: true,
  },
  defensive_alliance: {
    label_fr: 'Alliance défensive',
    icon: '🛡️',
    color: '#8b5cf6',
    description_fr: 'Protection mutuelle contre les agressions',
    min_relation: 30,
    common: true,
  },
  non_aggression_pact: {
    label_fr: 'Pacte de non-agression',
    icon: '🤝',
    color: '#6366f1',
    description_fr: 'Engagement à ne pas attaquer',
    min_relation: -20,
    common: true,
  },
  oil_agreement: {
    label_fr: 'Accord pétrolier',
    icon: '🛢️',
    color: '#f59e0b',
    description_fr: 'Accès privilégié aux ressources',
    min_relation: 10,
    common: false,
  },
  development_program: {
    label_fr: 'Programme de développement',
    icon: '🏗️',
    color: '#14b8a6',
    description_fr: 'Aide au développement économique',
    min_relation: 20,
    common: false,
  },
  technology_transfer: {
    label_fr: 'Transfert technologique',
    icon: '🔬',
    color: '#ec4899',
    description_fr: 'Partage de technologies',
    min_relation: 40,
    common: false,
  },
  military_access: {
    label_fr: 'Accès militaire',
    icon: '🎖️',
    color: '#ef4444',
    description_fr: 'Autorisation de transit/bases',
    min_relation: 50,
    common: false,
  },
};

// Conditions simplifiées - seulement les plus courantes
const QUICK_CONDITIONS = {
  offers: [
    { category: 'economic', label_fr: 'Aide économique', baseValue: 10 },
    { category: 'military', label_fr: 'Ventes d\'armes', baseValue: 5 },
    { category: 'diplomatic', label_fr: 'Soutien ONU', baseValue: 3 },
    { category: 'resource', label_fr: 'Accès ressources', baseValue: 8 },
  ],
  demands: [
    { category: 'economic', label_fr: 'Tarifs préférentiels', baseValue: 10 },
    { category: 'military', label_fr: 'Accès bases', baseValue: 5 },
    { category: 'diplomatic', label_fr: 'Alignement votes', baseValue: 3 },
    { category: 'resource', label_fr: 'Accès pétrole', baseValue: 8 },
  ],
};

// ============================================================================
// COMPOSANT PRINCIPAL
// ============================================================================

interface DiplomaticNegotiationsProps {
  countries: Country[];
  playerCountryId: string | null;
  currentYear: number;
}

export default function DiplomaticNegotiations({
  countries,
  playerCountryId,
  currentYear,
}: DiplomaticNegotiationsProps) {
  // États simplifiés
  const [step, setStep] = useState<'select' | 'negotiate'>('select');
  const [selectedCountry, setSelectedCountry] = useState<Country | null>(null);
  const [selectedType, setSelectedType] = useState<AgreementType | null>(null);
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');

  // Conditions de négociation
  const [offers, setOffers] = useState<AgreementCondition[]>([]);
  const [demands, setDemands] = useState<AgreementCondition[]>([]);

  // Données
  const [activeAgreements, setActiveAgreements] = useState<DiplomaticAgreement[]>([]);
  const [history, setHistory] = useState<NegotiationHistory[]>([]);
  const [showHistory, setShowHistory] = useState(false);

  // UI
  const [isLoading, setIsLoading] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error' | 'info'; text: string } | null>(null);

  // Pays du joueur
  const playerCountry = useMemo(() =>
    countries.find(c => c.id === playerCountryId),
    [countries, playerCountryId]
  );

  // Filtrer les pays pour la sélection
  const filteredCountries = useMemo(() => {
    if (!playerCountryId) return [];
    return countries
      .filter(c => c.id !== playerCountryId)
      .filter(c => {
        if (!searchTerm) return true;
        const search = searchTerm.toLowerCase();
        return c.name.toLowerCase().includes(search) ||
               c.name_fr.toLowerCase().includes(search);
      })
      .sort((a, b) => {
        // Prioriser par tier puis par relation
        if (a.tier !== b.tier) return a.tier - b.tier;
        const relA = a.relations?.[playerCountryId] || 0;
        const relB = b.relations?.[playerCountryId] || 0;
        return relB - relA;
      })
      .slice(0, 20); // Limiter à 20 pays visibles
  }, [countries, playerCountryId, searchTerm]);

  // Suggestions intelligentes basées sur la relation
  const suggestedAgreements = useMemo(() => {
    if (!selectedCountry || !playerCountryId) return [];

    const relation = selectedCountry.relations?.[playerCountryId] || 0;
    const isAtWar = selectedCountry.at_war?.includes(playerCountryId);
    const suggestions: { type: AgreementType; reason: string }[] = [];

    if (isAtWar) {
      suggestions.push({ type: 'peace_treaty', reason: 'Mettre fin au conflit actuel' });
    } else if (relation < 0) {
      suggestions.push({ type: 'non_aggression_pact', reason: 'Stabiliser une relation tendue' });
    } else if (relation >= 0 && relation < 30) {
      suggestions.push({ type: 'trade_agreement', reason: 'Renforcer les liens économiques' });
    } else if (relation >= 30) {
      suggestions.push({ type: 'defensive_alliance', reason: 'Formaliser une relation solide' });
    }

    // Ajouter une suggestion basée sur les ressources
    if (selectedCountry.resources && selectedCountry.resources > 50) {
      suggestions.push({ type: 'oil_agreement', reason: 'Accéder à leurs ressources pétrolières' });
    }

    return suggestions.slice(0, 2); // Max 2 suggestions
  }, [selectedCountry, playerCountryId]);

  // Calculer la probabilité d'acceptation
  const acceptanceProbability = useMemo(() => {
    if (!selectedCountry || !selectedType || !playerCountryId) return 0;

    const relation = selectedCountry.relations?.[playerCountryId] || 0;
    const typeConfig = AGREEMENT_TYPES[selectedType];

    // Base: relation normalisée
    let prob = Math.max(0, Math.min(100, (relation + 100) / 2));

    // Bonus/malus selon équilibre offres/demandes
    const offerValue = offers.reduce((sum, o) => sum + o.value, 0);
    const demandValue = demands.reduce((sum, d) => sum + d.value, 0);
    const balance = offerValue - demandValue;

    prob += balance * 2; // Chaque point d'écart = 2% de probabilité

    // Malus si relation insuffisante
    if (relation < typeConfig.min_relation) {
      prob -= (typeConfig.min_relation - relation);
    }

    return Math.max(5, Math.min(95, Math.round(prob)));
  }, [selectedCountry, selectedType, playerCountryId, offers, demands]);

  // Charger les accords actifs
  useEffect(() => {
    if (!playerCountryId) return;

    const loadAgreements = async () => {
      try {
        const response = await fetch(
          `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001/api'}/diplomacy/agreements/${playerCountryId}`
        );
        if (response.ok) {
          const data = await response.json();
          setActiveAgreements(data.agreements || []);
        }
      } catch (error) {
        console.error('Erreur chargement accords:', error);
      }
    };

    loadAgreements();
  }, [playerCountryId]);

  // Charger l'historique
  useEffect(() => {
    if (!playerCountryId) return;

    const loadHistory = async () => {
      try {
        const response = await fetch(
          `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001/api'}/diplomacy/history/${playerCountryId}`
        );
        if (response.ok) {
          const data = await response.json();
          setHistory(data.history || []);
        }
      } catch (error) {
        console.error('Erreur chargement historique:', error);
      }
    };

    loadHistory();
  }, [playerCountryId]);

  // Sélectionner un pays
  const handleSelectCountry = useCallback((country: Country) => {
    setSelectedCountry(country);
    setSelectedType(null);
    setOffers([]);
    setDemands([]);
    setStep('negotiate');
  }, []);

  // Sélectionner un type d'accord
  const handleSelectType = useCallback((type: AgreementType) => {
    setSelectedType(type);
    // Ajouter des conditions par défaut équilibrées
    const defaultOffer: AgreementCondition = {
      id: `offer-${Date.now()}`,
      type: 'offer',
      category: 'economic',
      label: 'Economic Aid',
      label_fr: 'Aide économique',
      value: 5,
    };
    const defaultDemand: AgreementCondition = {
      id: `demand-${Date.now()}`,
      type: 'demand',
      category: 'diplomatic',
      label: 'UN Support',
      label_fr: 'Soutien ONU',
      value: 3,
    };
    setOffers([defaultOffer]);
    setDemands([defaultDemand]);
  }, []);

  // Ajouter une condition
  const addCondition = useCallback((
    conditionType: 'offer' | 'demand',
    category: string,
    label_fr: string,
    baseValue: number
  ) => {
    const condition: AgreementCondition = {
      id: `${conditionType}-${Date.now()}-${Math.random()}`,
      type: conditionType,
      category,
      label: label_fr,
      label_fr,
      value: baseValue,
    };

    if (conditionType === 'offer') {
      setOffers(prev => [...prev, condition]);
    } else {
      setDemands(prev => [...prev, condition]);
    }
  }, []);

  // Modifier la valeur d'une condition
  const updateConditionValue = useCallback((id: string, delta: number, isOffer: boolean) => {
    const setter = isOffer ? setOffers : setDemands;
    setter(prev => prev.map(c =>
      c.id === id ? { ...c, value: Math.max(1, Math.min(20, c.value + delta)) } : c
    ));
  }, []);

  // Supprimer une condition
  const removeCondition = useCallback((id: string, isOffer: boolean) => {
    const setter = isOffer ? setOffers : setDemands;
    setter(prev => prev.filter(c => c.id !== id));
  }, []);

  // Proposer l'accord
  const handlePropose = useCallback(async () => {
    if (!selectedCountry || !selectedType || !playerCountryId) return;

    setIsLoading(true);
    setMessage(null);

    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001/api'}/diplomacy/propose`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            initiator_id: playerCountryId,
            target_id: selectedCountry.id,
            agreement_type: selectedType,
            conditions_offered: offers,
            conditions_demanded: demands,
          }),
        }
      );

      const data = await response.json();

      if (data.accepted) {
        setMessage({ type: 'success', text: data.message_fr || 'Accord accepté !' });
        setActiveAgreements(prev => [...prev, data]);
      } else {
        setMessage({
          type: 'error',
          text: data.message_fr || data.rejection_reason || 'Accord refusé'
        });
      }

      // Retour à la sélection
      setTimeout(() => {
        setStep('select');
        setSelectedCountry(null);
        setSelectedType(null);
        setOffers([]);
        setDemands([]);
        setMessage(null);
      }, 3000);

    } catch (error) {
      console.error('Erreur proposition:', error);
      setMessage({ type: 'error', text: 'Erreur de connexion' });
    } finally {
      setIsLoading(false);
    }
  }, [selectedCountry, selectedType, playerCountryId, offers, demands]);

  // Annuler et revenir
  const handleBack = useCallback(() => {
    setStep('select');
    setSelectedCountry(null);
    setSelectedType(null);
    setOffers([]);
    setDemands([]);
    setMessage(null);
  }, []);

  // Résilier un accord
  const handleTerminate = useCallback(async (agreementId: string) => {
    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001/api'}/diplomacy/terminate/${agreementId}`,
        { method: 'POST' }
      );

      if (response.ok) {
        setActiveAgreements(prev => prev.filter(a => a.id !== agreementId));
        setMessage({ type: 'info', text: 'Accord résilié' });
      }
    } catch (error) {
      console.error('Erreur résiliation:', error);
    }
  }, []);

  // Si pas de pays joueur
  if (!playerCountryId || !playerCountry) {
    return (
      <div className="diplomatic-panel">
        <div className="empty-state">
          <span className="empty-icon">🏛️</span>
          <h3>Sélectionnez un pays</h3>
          <p>Choisissez un pays à contrôler pour accéder aux négociations diplomatiques</p>
        </div>
      </div>
    );
  }

  return (
    <div className="diplomatic-panel">
      {/* Header */}
      <div className="panel-header">
        <div className="header-title">
          <span className="header-icon">🏛️</span>
          <h2>Diplomatie</h2>
          <span className="player-badge">
            {COUNTRY_FLAGS[playerCountry.id] || '🏳️'} {playerCountry.name_fr}
          </span>
        </div>

        <div className="header-tabs">
          <button
            className={`tab ${!showHistory ? 'active' : ''}`}
            onClick={() => setShowHistory(false)}
          >
            Négocier
          </button>
          <button
            className={`tab ${showHistory ? 'active' : ''}`}
            onClick={() => setShowHistory(true)}
          >
            Accords ({activeAgreements.length})
          </button>
        </div>
      </div>

      {/* Message */}
      {message && (
        <div className={`message message-${message.type}`}>
          {message.text}
        </div>
      )}

      {/* Contenu principal */}
      {!showHistory ? (
        <div className="negotiation-content">
          {step === 'select' ? (
            // ÉTAPE 1: Sélection du pays
            <div className="step-select">
              <h3>Avec qui négocier ?</h3>

              <input
                type="text"
                className="search-input"
                placeholder="Rechercher un pays..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
              />

              <div className="countries-list">
                {filteredCountries.map(country => {
                  const relation = country.relations?.[playerCountryId] || 0;
                  const relationClass = relation > 20 ? 'positive' : relation < -20 ? 'negative' : 'neutral';
                  const isAtWar = country.at_war?.includes(playerCountryId);

                  return (
                    <button
                      key={country.id}
                      className={`country-card ${isAtWar ? 'at-war' : ''}`}
                      onClick={() => handleSelectCountry(country)}
                    >
                      <span className="country-flag">
                        {COUNTRY_FLAGS[country.id] || '🏳️'}
                      </span>
                      <div className="country-info">
                        <span className="country-name">{country.name_fr}</span>
                        <span className="country-tier">Tier {country.tier}</span>
                      </div>
                      <div className={`relation-badge ${relationClass}`}>
                        {isAtWar ? '⚔️ Guerre' : `${relation > 0 ? '+' : ''}${relation}`}
                      </div>
                    </button>
                  );
                })}
              </div>
            </div>
          ) : (
            // ÉTAPE 2: Négociation
            <div className="step-negotiate">
              {/* Pays cible */}
              <div className="target-header">
                <button className="back-btn" onClick={handleBack}>
                  ← Retour
                </button>
                <div className="target-info">
                  <span className="target-flag">
                    {selectedCountry && COUNTRY_FLAGS[selectedCountry.id]}
                  </span>
                  <span className="target-name">{selectedCountry?.name_fr}</span>
                  <span className={`target-relation ${
                    (selectedCountry?.relations?.[playerCountryId] || 0) > 0 ? 'positive' :
                    (selectedCountry?.relations?.[playerCountryId] || 0) < 0 ? 'negative' : 'neutral'
                  }`}>
                    Relations: {selectedCountry?.relations?.[playerCountryId] || 0}
                  </span>
                </div>
              </div>

              {/* Suggestions intelligentes */}
              {!selectedType && suggestedAgreements.length > 0 && (
                <div className="suggestions">
                  <h4>Suggestions</h4>
                  {suggestedAgreements.map(({ type, reason }) => (
                    <button
                      key={type}
                      className="suggestion-card"
                      onClick={() => handleSelectType(type)}
                      style={{ borderColor: AGREEMENT_TYPES[type].color }}
                    >
                      <span className="suggestion-icon">{AGREEMENT_TYPES[type].icon}</span>
                      <div className="suggestion-info">
                        <span className="suggestion-name">{AGREEMENT_TYPES[type].label_fr}</span>
                        <span className="suggestion-reason">{reason}</span>
                      </div>
                    </button>
                  ))}
                </div>
              )}

              {/* Types d'accords */}
              {!selectedType && (
                <div className="agreement-types">
                  <h4>Type d'accord</h4>
                  <div className="types-grid">
                    {Object.entries(AGREEMENT_TYPES)
                      .filter(([, config]) => showAdvanced || config.common)
                      .map(([type, config]) => {
                        const relation = selectedCountry?.relations?.[playerCountryId] || 0;
                        const disabled = relation < config.min_relation;

                        return (
                          <button
                            key={type}
                            className={`type-btn ${disabled ? 'disabled' : ''}`}
                            onClick={() => !disabled && handleSelectType(type as AgreementType)}
                            style={{
                              borderColor: disabled ? '#4b5563' : config.color,
                              opacity: disabled ? 0.5 : 1
                            }}
                            disabled={disabled}
                            title={disabled ? `Relation minimale: ${config.min_relation}` : config.description_fr}
                          >
                            <span className="type-icon">{config.icon}</span>
                            <span className="type-name">{config.label_fr}</span>
                          </button>
                        );
                      })}
                  </div>

                  {!showAdvanced && (
                    <button
                      className="show-more-btn"
                      onClick={() => setShowAdvanced(true)}
                    >
                      Voir tous les types d'accords
                    </button>
                  )}
                </div>
              )}

              {/* Conditions de l'accord */}
              {selectedType && (
                <div className="conditions-section">
                  <div className="selected-type">
                    <span className="type-icon">{AGREEMENT_TYPES[selectedType].icon}</span>
                    <span className="type-name">{AGREEMENT_TYPES[selectedType].label_fr}</span>
                    <button
                      className="change-type-btn"
                      onClick={() => setSelectedType(null)}
                    >
                      Changer
                    </button>
                  </div>

                  {/* Nos offres */}
                  <div className="conditions-block offers-block">
                    <h4>Ce que nous offrons</h4>
                    <div className="conditions-list">
                      {offers.map(offer => (
                        <div key={offer.id} className="condition-item">
                          <span className="condition-label">{offer.label_fr}</span>
                          <div className="condition-controls">
                            <button onClick={() => updateConditionValue(offer.id, -1, true)}>−</button>
                            <span className="condition-value">{offer.value}</span>
                            <button onClick={() => updateConditionValue(offer.id, 1, true)}>+</button>
                            <button
                              className="remove-btn"
                              onClick={() => removeCondition(offer.id, true)}
                            >×</button>
                          </div>
                        </div>
                      ))}
                    </div>
                    <div className="add-condition">
                      {QUICK_CONDITIONS.offers.map(cond => (
                        <button
                          key={cond.label_fr}
                          className="add-btn"
                          onClick={() => addCondition('offer', cond.category, cond.label_fr, cond.baseValue)}
                        >
                          + {cond.label_fr}
                        </button>
                      ))}
                    </div>
                  </div>

                  {/* Nos demandes */}
                  <div className="conditions-block demands-block">
                    <h4>Ce que nous demandons</h4>
                    <div className="conditions-list">
                      {demands.map(demand => (
                        <div key={demand.id} className="condition-item">
                          <span className="condition-label">{demand.label_fr}</span>
                          <div className="condition-controls">
                            <button onClick={() => updateConditionValue(demand.id, -1, false)}>−</button>
                            <span className="condition-value">{demand.value}</span>
                            <button onClick={() => updateConditionValue(demand.id, 1, false)}>+</button>
                            <button
                              className="remove-btn"
                              onClick={() => removeCondition(demand.id, false)}
                            >×</button>
                          </div>
                        </div>
                      ))}
                    </div>
                    <div className="add-condition">
                      {QUICK_CONDITIONS.demands.map(cond => (
                        <button
                          key={cond.label_fr}
                          className="add-btn"
                          onClick={() => addCondition('demand', cond.category, cond.label_fr, cond.baseValue)}
                        >
                          + {cond.label_fr}
                        </button>
                      ))}
                    </div>
                  </div>

                  {/* Probabilité et action */}
                  <div className="proposal-footer">
                    <div className="probability-bar">
                      <span className="probability-label">Chance d'acceptation</span>
                      <div className="probability-track">
                        <div
                          className="probability-fill"
                          style={{
                            width: `${acceptanceProbability}%`,
                            backgroundColor: acceptanceProbability > 60 ? '#10b981' :
                                           acceptanceProbability > 30 ? '#f59e0b' : '#ef4444'
                          }}
                        />
                      </div>
                      <span className="probability-value">{acceptanceProbability}%</span>
                    </div>

                    <button
                      className="propose-btn"
                      onClick={handlePropose}
                      disabled={isLoading}
                    >
                      {isLoading ? 'Envoi...' : 'Proposer l\'accord'}
                    </button>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      ) : (
        // Vue des accords actifs et historique
        <div className="agreements-view">
          {activeAgreements.length === 0 ? (
            <div className="empty-agreements">
              <span>📜</span>
              <p>Aucun accord actif</p>
            </div>
          ) : (
            <div className="agreements-list">
              {activeAgreements.map(agreement => {
                const typeConfig = AGREEMENT_TYPES[agreement.type as AgreementType];
                const targetCountry = countries.find(c =>
                  c.id === (agreement.initiator === playerCountryId ? agreement.target : agreement.initiator)
                );

                return (
                  <div key={agreement.id} className="agreement-card">
                    <div className="agreement-header">
                      <span className="agreement-icon">{typeConfig?.icon}</span>
                      <div className="agreement-info">
                        <span className="agreement-type">{typeConfig?.label_fr}</span>
                        <span className="agreement-target">
                          avec {targetCountry?.name_fr}
                        </span>
                      </div>
                      <span className="agreement-year">
                        Depuis {agreement.year_proposed}
                        {agreement.year_expires && ` (exp. ${agreement.year_expires})`}
                      </span>
                    </div>
                    <button
                      className="terminate-btn"
                      onClick={() => handleTerminate(agreement.id)}
                    >
                      Résilier
                    </button>
                  </div>
                );
              })}
            </div>
          )}

          {/* Historique récent */}
          {history.length > 0 && (
            <div className="history-section">
              <h4>Historique récent</h4>
              <div className="history-list">
                {history.slice(0, 5).map(entry => (
                  <div key={entry.id} className="history-item">
                    <span className="history-year">{entry.year}</span>
                    <span className="history-text">{entry.details_fr}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

    </div>
  );
}
