'use client';

import { useState, useMemo } from 'react';
import {
  COUNTRY_FLAGS,
  InfluenceZone,
  Country,
} from '@/lib/types';
import {
  establishBase,
  launchCulturalProgram,
  signArmsDeal,
} from '@/lib/api';

interface ActionPanelProps {
  playerCountry: Country | null;
  zones: InfluenceZone[];
  allCountries: Country[];
  onActionComplete?: () => void;
}

type ActionTab = 'base' | 'cultural' | 'arms';

// Realistic military base types with detailed stats
const BASE_TYPES = [
  {
    id: 'air_base',
    name: 'Base aerienne',
    icon: '&#9992;',
    defaultPersonnel: 3000,
    costPerYear: 15,
    strategicValue: 40,
    description: 'Projection aerienne, frappe de precision, ravitaillement',
    realExamples: 'Ramstein (USA/DEU), Istres (FRA), Hmeimim (RUS/SYR)',
    effects: { military: 8, projection: 15, deterrence: 10 },
  },
  {
    id: 'naval_base',
    name: 'Base navale',
    icon: '&#9875;',
    defaultPersonnel: 2500,
    costPerYear: 20,
    strategicValue: 50,
    description: 'Controle maritime, projection navale, blocus potentiel',
    realExamples: 'Diego Garcia (USA), Tartous (RUS), Djibouti (FRA/CHN/USA)',
    effects: { military: 10, projection: 20, trade_control: 15 },
  },
  {
    id: 'army_base',
    name: 'Base terrestre',
    icon: '&#9881;',
    defaultPersonnel: 5000,
    costPerYear: 12,
    strategicValue: 35,
    description: 'Presence au sol, stabilisation, formation locale',
    realExamples: 'Camp Bondsteel (USA/KOS), Manbij (USA/SYR)',
    effects: { military: 12, stability: 10, local_influence: 15 },
  },
  {
    id: 'drone_base',
    name: 'Base de drones',
    icon: '&#128296;',
    defaultPersonnel: 500,
    costPerYear: 8,
    strategicValue: 30,
    description: 'Surveillance, frappes ciblees, faible empreinte',
    realExamples: 'Niamey (USA/NER), Agadez (USA/NER)',
    effects: { military: 5, surveillance: 20, precision_strike: 15 },
  },
  {
    id: 'listening_post',
    name: 'Poste d\'ecoute',
    icon: '&#128065;',
    defaultPersonnel: 200,
    costPerYear: 5,
    strategicValue: 25,
    description: 'SIGINT, surveillance, renseignement regional',
    realExamples: 'Menwith Hill (USA/GBR), Pine Gap (USA/AUS)',
    effects: { military: 2, intelligence: 25, diplomatic: 5 },
  },
  {
    id: 'logistics_hub',
    name: 'Hub logistique',
    icon: '&#128230;',
    defaultPersonnel: 1500,
    costPerYear: 10,
    strategicValue: 30,
    description: 'Ravitaillement, stockage, support operations',
    realExamples: 'Al Udeid (USA/QAT), Incirlik (USA/TUR)',
    effects: { military: 4, logistics: 20, projection: 10 },
  },
];

// Enhanced cultural programs with real-world equivalents
const CULTURAL_PROGRAMS = [
  {
    id: 'language_institute',
    name: 'Institut linguistique',
    icon: '&#128218;',
    description: 'Diffusion de la langue et culture via education',
    realExamples: [
      { power: 'FRA', name: 'Alliance Francaise', reach: 130 },
      { power: 'CHN', name: 'Institut Confucius', reach: 500 },
      { power: 'DEU', name: 'Goethe-Institut', reach: 150 },
      { power: 'GBR', name: 'British Council', reach: 100 },
      { power: 'ESP', name: 'Instituto Cervantes', reach: 80 },
    ],
    baseCost: 30,
    effects: { cultural: 15, soft_power: 10, language_spread: 20 },
    duration: 'Long terme (10+ ans)',
  },
  {
    id: 'media_network',
    name: 'Reseau mediatique',
    icon: '&#128250;',
    description: 'Chaines TV internationales, narratif mediatique',
    realExamples: [
      { power: 'USA', name: 'CNN/Voice of America', reach: 'Global' },
      { power: 'GBR', name: 'BBC World', reach: 'Global' },
      { power: 'RUS', name: 'RT (Russia Today)', reach: '100+ pays' },
      { power: 'CHN', name: 'CGTN', reach: '160+ pays' },
      { power: 'FRA', name: 'France 24', reach: '350M foyers' },
      { power: 'QAT', name: 'Al Jazeera', reach: 'MENA + Global' },
    ],
    baseCost: 50,
    effects: { cultural: 10, narrative_control: 25, soft_power: 15 },
    duration: 'Moyen terme (3-5 ans)',
  },
  {
    id: 'education_program',
    name: 'Programme educatif',
    icon: '&#127891;',
    description: 'Bourses, echanges universitaires, formation elites',
    realExamples: [
      { power: 'USA', name: 'Fulbright Program', reach: '160 pays' },
      { power: 'GBR', name: 'Chevening/Commonwealth', reach: '50 000+/an' },
      { power: 'FRA', name: 'Campus France', reach: '370 000/an' },
      { power: 'CHN', name: 'CSC Scholarships', reach: '60 000+/an' },
      { power: 'TUR', name: 'Turkiye Burslari', reach: '20 000+/an' },
    ],
    baseCost: 40,
    effects: { cultural: 20, elite_formation: 25, long_term_loyalty: 15 },
    duration: 'Tres long terme (generation)',
  },
  {
    id: 'cultural_center',
    name: 'Centre culturel',
    icon: '&#127917;',
    description: 'Presence culturelle, expositions, evenements',
    realExamples: [
      { power: 'USA', name: 'American Centers', reach: '50+ pays' },
      { power: 'FRA', name: 'Instituts Francais', reach: '96 pays' },
      { power: 'IRN', name: 'Centres culturels iraniens', reach: 'MENA' },
    ],
    baseCost: 25,
    effects: { cultural: 12, local_presence: 15, soft_power: 8 },
    duration: 'Court terme (1-2 ans visible)',
  },
  {
    id: 'religious_outreach',
    name: 'Influence religieuse',
    icon: '&#128591;',
    description: 'Financement religieux, construction lieux de culte',
    realExamples: [
      { power: 'SAU', name: 'Wahhabisme mondial', reach: 'Global' },
      { power: 'IRN', name: 'Chiisme/Hezbollah', reach: 'Croissant chiite' },
      { power: 'TUR', name: 'Diyanet/mosquees', reach: 'Europe + Balkans' },
      { power: 'RUS', name: 'Orthodoxie (Patriarcat)', reach: 'Europe Est' },
    ],
    baseCost: 35,
    effects: { religious: 25, cultural: 10, local_loyalty: 20 },
    duration: 'Generationnel',
  },
  {
    id: 'development_aid',
    name: 'Aide au developpement',
    icon: '&#127968;',
    description: 'Infrastructures, hopitaux, ecoles - influence par la dette',
    realExamples: [
      { power: 'CHN', name: 'Belt & Road (BRI)', reach: '140+ pays, 1T$' },
      { power: 'USA', name: 'USAID', reach: '100+ pays, 50Md$/an' },
      { power: 'JPN', name: 'JICA', reach: '150 pays, 15Md$/an' },
      { power: 'FRA', name: 'AFD', reach: 'Afrique, 12Md$/an' },
    ],
    baseCost: 60,
    effects: { economic: 15, infrastructure: 20, debt_trap: 25 },
    duration: 'Long terme (decennies)',
  },
];

// Real arms deals data for context
const ARMS_CATEGORIES = [
  {
    id: 'fighter_jets',
    name: 'Avions de combat',
    icon: '&#9992;',
    examples: 'F-35, Rafale, Su-35, J-10',
    valueRange: [40, 100],
    militaryBoost: 15,
    dependencyLevel: 'Haute',
  },
  {
    id: 'tanks_armor',
    name: 'Blindes & Chars',
    icon: '&#128661;',
    examples: 'Leopard 2, Abrams, T-90, Leclerc',
    valueRange: [20, 60],
    militaryBoost: 10,
    dependencyLevel: 'Moyenne',
  },
  {
    id: 'naval_vessels',
    name: 'Navires de guerre',
    icon: '&#9875;',
    examples: 'Frigates, Corvettes, Sous-marins',
    valueRange: [30, 80],
    militaryBoost: 12,
    dependencyLevel: 'Haute',
  },
  {
    id: 'missiles_defense',
    name: 'Missiles & Defense',
    icon: '&#127919;',
    examples: 'S-400, Patriot, THAAD, Iron Dome',
    valueRange: [50, 100],
    militaryBoost: 18,
    dependencyLevel: 'Tres haute',
  },
  {
    id: 'small_arms',
    name: 'Armes legeres',
    icon: '&#128299;',
    examples: 'Fusils, munitions, equipements',
    valueRange: [10, 30],
    militaryBoost: 5,
    dependencyLevel: 'Faible',
  },
  {
    id: 'drones_uav',
    name: 'Drones militaires',
    icon: '&#128296;',
    examples: 'TB2, Reaper, Wing Loong',
    valueRange: [20, 50],
    militaryBoost: 8,
    dependencyLevel: 'Moyenne',
  },
];

export default function ActionPanel({
  playerCountry,
  zones,
  allCountries,
  onActionComplete,
}: ActionPanelProps) {
  const [activeTab, setActiveTab] = useState<ActionTab>('base');
  const [expanded, setExpanded] = useState(true);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<{ success: boolean; message: string } | null>(null);

  // Base establishment state
  const [selectedZone, setSelectedZone] = useState<string>('');
  const [selectedHostCountry, setSelectedHostCountry] = useState<string>('');
  const [selectedBaseType, setSelectedBaseType] = useState<string>('air_base');
  const [basePersonnel, setBasePersonnel] = useState<number>(1000);

  // Cultural program state
  const [culturalZone, setCulturalZone] = useState<string>('');
  const [culturalProgram, setCulturalProgram] = useState<string>('language_institute');
  const [culturalInvestment, setCulturalInvestment] = useState<number>(50);

  // Arms deal state
  const [armsBuyer, setArmsBuyer] = useState<string>('');
  const [armsCategory, setArmsCategory] = useState<string>('fighter_jets');
  const [armsValue, setArmsValue] = useState<number>(50);

  // Get the selected base type details
  const selectedBaseDetails = useMemo(() =>
    BASE_TYPES.find(t => t.id === selectedBaseType),
    [selectedBaseType]
  );

  // Get the selected cultural program details
  const selectedCulturalDetails = useMemo(() =>
    CULTURAL_PROGRAMS.find(p => p.id === culturalProgram),
    [culturalProgram]
  );

  // Get the selected arms category details
  const selectedArmsDetails = useMemo(() =>
    ARMS_CATEGORIES.find(c => c.id === armsCategory),
    [armsCategory]
  );

  if (!playerCountry) {
    return (
      <div className="bg-gray-800 rounded-lg p-4 text-center text-gray-500">
        <span className="text-2xl block mb-2">&#128101;</span>
        Selectionnez un pays joueur pour acceder aux actions
      </div>
    );
  }

  const handleEstablishBase = async () => {
    if (!selectedZone || !selectedHostCountry) {
      setResult({ success: false, message: 'Selectionnez une zone et un pays hote' });
      return;
    }

    setLoading(true);
    setResult(null);

    try {
      const response = await establishBase({
        owner_id: playerCountry.id,
        host_country_id: selectedHostCountry,
        zone_id: selectedZone,
        base_type: selectedBaseType,
        personnel: basePersonnel,
      });

      setResult({ success: true, message: response.message_fr });
      onActionComplete?.();
    } catch (error: unknown) {
      const message = error instanceof Error ? error.message : 'Erreur lors de l\'etablissement de la base';
      setResult({ success: false, message });
    } finally {
      setLoading(false);
    }
  };

  const handleLaunchCulturalProgram = async () => {
    if (!culturalZone) {
      setResult({ success: false, message: 'Selectionnez une zone cible' });
      return;
    }

    setLoading(true);
    setResult(null);

    try {
      const response = await launchCulturalProgram({
        power_id: playerCountry.id,
        zone_id: culturalZone,
        program_type: culturalProgram,
        investment: culturalInvestment,
      });

      setResult({ success: true, message: response.message_fr });
      onActionComplete?.();
    } catch (error: unknown) {
      const message = error instanceof Error ? error.message : 'Erreur lors du lancement du programme';
      setResult({ success: false, message });
    } finally {
      setLoading(false);
    }
  };

  const handleSignArmsDeal = async () => {
    if (!armsBuyer) {
      setResult({ success: false, message: 'Selectionnez un acheteur' });
      return;
    }

    setLoading(true);
    setResult(null);

    try {
      const response = await signArmsDeal({
        seller_id: playerCountry.id,
        buyer_id: armsBuyer,
        value: armsValue,
        category: armsCategory,
      });

      setResult({ success: true, message: response.message_fr });
      onActionComplete?.();
    } catch (error: unknown) {
      const message = error instanceof Error ? error.message : 'Erreur lors de la signature du contrat';
      setResult({ success: false, message });
    } finally {
      setLoading(false);
    }
  };

  // Get countries in selected zone for host selection
  const getZoneCountries = (zoneId: string) => {
    const zone = zones.find(z => z.id === zoneId);
    if (!zone) return [];
    return allCountries.filter(c =>
      zone.countries_in_zone.includes(c.id) &&
      c.id !== playerCountry.id
    );
  };

  // Get zone details for display
  const getZoneDetails = (zoneId: string) => {
    return zones.find(z => z.id === zoneId);
  };

  // Get host country details
  const getHostCountryDetails = (countryId: string) => {
    return allCountries.find(c => c.id === countryId);
  };

  // Calculate diplomatic feasibility for base
  const getBaseFeasibility = (hostId: string) => {
    const relation = playerCountry.relations[hostId] || 0;
    if (relation >= 50) return { level: 'high', label: 'Excellente', color: 'text-green-400' };
    if (relation >= 20) return { level: 'medium', label: 'Possible', color: 'text-yellow-400' };
    if (relation >= 0) return { level: 'low', label: 'Difficile', color: 'text-orange-400' };
    return { level: 'impossible', label: 'Impossible', color: 'text-red-400' };
  };

  // Get potential arms buyers (excluding self, prefer allies or neutrals)
  const potentialBuyers = useMemo(() => {
    return allCountries
      .filter(c =>
        c.id !== playerCountry.id &&
        c.tier >= 2 &&
        !playerCountry.at_war.includes(c.id)
      )
      .map(c => ({
        ...c,
        relation: playerCountry.relations[c.id] || 0,
        isAlly: playerCountry.allies.includes(c.id),
        isRival: playerCountry.rivals.includes(c.id),
      }))
      .sort((a, b) => b.relation - a.relation);
  }, [allCountries, playerCountry]);

  // Calculate estimated effects for arms deal
  const getArmsDealEffects = () => {
    const category = ARMS_CATEGORIES.find(c => c.id === armsCategory);
    if (!category) return null;

    const baseMultiplier = armsValue / 50;
    return {
      sellerEconomy: Math.floor(armsValue / 15 * baseMultiplier),
      buyerMilitary: Math.floor(category.militaryBoost * baseMultiplier),
      relationBoost: Math.floor(8 + armsValue / 10),
      dependency: category.dependencyLevel,
    };
  };

  return (
    <div className="bg-gray-800 rounded-lg overflow-hidden shadow-lg">
      {/* Header */}
      <div
        className="flex items-center justify-between px-4 py-3 bg-gradient-to-r from-emerald-900/50 to-gray-700 cursor-pointer hover:from-emerald-900/70 transition-all"
        onClick={() => setExpanded(!expanded)}
      >
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-full bg-emerald-600 flex items-center justify-center">
            <span className="text-sm">&#9889;</span>
          </div>
          <div>
            <span className="text-lg font-bold">Actions Strategiques</span>
            <div className="text-xs text-gray-400">
              {COUNTRY_FLAGS[playerCountry.id]} {playerCountry.name_fr} | Eco: {playerCountry.economy} | Mil: {playerCountry.military}
            </div>
          </div>
        </div>
        <button
          className="text-gray-400 hover:text-white transition-transform duration-200"
          style={{ transform: expanded ? 'rotate(0deg)' : 'rotate(180deg)' }}
        >
          &#9650;
        </button>
      </div>

      <div className={`transition-all duration-300 ease-in-out overflow-hidden ${expanded ? 'max-h-[800px] opacity-100' : 'max-h-0 opacity-0'}`}>
        {/* Tabs */}
        <div className="flex border-b border-gray-700">
          {([
            { key: 'base', label: 'Base militaire', icon: '&#9876;', color: 'emerald' },
            { key: 'cultural', label: 'Soft Power', icon: '&#127891;', color: 'purple' },
            { key: 'arms', label: 'Vente d\'armes', icon: '&#128296;', color: 'red' },
          ] as const).map(({ key, label, icon, color }) => (
            <button
              key={key}
              onClick={() => {
                setActiveTab(key);
                setResult(null);
              }}
              className={`flex-1 px-3 py-2.5 text-sm font-medium flex items-center justify-center gap-2 transition-all ${
                activeTab === key
                  ? `bg-${color}-600 text-white`
                  : 'bg-gray-750 text-gray-400 hover:bg-gray-700 hover:text-white'
              }`}
              style={activeTab === key ? {
                backgroundColor: color === 'emerald' ? '#059669' : color === 'purple' ? '#9333ea' : '#dc2626'
              } : {}}
            >
              <span dangerouslySetInnerHTML={{ __html: icon }} />
              {label}
            </button>
          ))}
        </div>

        {/* Content */}
        <div className="p-4 space-y-4 max-h-[550px] overflow-y-auto scrollbar-thin">

          {/* ============================================ */}
          {/* BASE MILITAIRE TAB - ENHANCED */}
          {/* ============================================ */}
          {activeTab === 'base' && (
            <>
              <div className="text-sm text-gray-400 mb-3 flex items-center gap-2">
                <span>&#127759;</span>
                Etablir une presence militaire pour projeter votre puissance
              </div>

              {/* Zone selection with details */}
              <div>
                <label className="block text-xs text-gray-500 mb-1">Zone strategique</label>
                <select
                  value={selectedZone}
                  onChange={(e) => {
                    setSelectedZone(e.target.value);
                    setSelectedHostCountry('');
                  }}
                  className="w-full bg-gray-700 text-white text-sm rounded-lg px-3 py-2 border border-gray-600 focus:outline-none focus:ring-2 focus:ring-emerald-500"
                >
                  <option value="">Choisir une zone...</option>
                  {zones.map(zone => (
                    <option key={zone.id} value={zone.id}>
                      {zone.name_fr} {zone.has_oil ? '(Petrole)' : ''} {zone.contested_by.length > 0 ? '(Contestee)' : ''}
                    </option>
                  ))}
                </select>
              </div>

              {/* Zone details card */}
              {selectedZone && (
                <div className="bg-gray-700/40 rounded-lg p-3 border border-gray-600">
                  {(() => {
                    const zone = getZoneDetails(selectedZone);
                    if (!zone) return null;
                    return (
                      <div className="text-xs space-y-2">
                        <div className="flex justify-between items-center">
                          <span className="font-medium text-white">{zone.name_fr}</span>
                          {zone.dominant_power && (
                            <span className="text-gray-400">
                              Domine par: {COUNTRY_FLAGS[zone.dominant_power]} {zone.dominant_power}
                            </span>
                          )}
                        </div>
                        <div className="flex flex-wrap gap-2">
                          {zone.has_oil && (
                            <span className="px-2 py-0.5 bg-yellow-900/50 rounded text-yellow-300">Petrole</span>
                          )}
                          {zone.has_strategic_resources && (
                            <span className="px-2 py-0.5 bg-blue-900/50 rounded text-blue-300">Strategique</span>
                          )}
                          {zone.contested_by.length > 0 && (
                            <span className="px-2 py-0.5 bg-red-900/50 rounded text-red-300">
                              Contestee ({zone.contested_by.join(', ')})
                            </span>
                          )}
                        </div>
                        <div className="text-gray-400">
                          Votre influence: <span className="text-emerald-400">{zone.influence_levels[playerCountry.id] || 0}%</span>
                        </div>
                      </div>
                    );
                  })()}
                </div>
              )}

              {/* Host country selection */}
              {selectedZone && (
                <div>
                  <label className="block text-xs text-gray-500 mb-1">Pays hote</label>
                  <select
                    value={selectedHostCountry}
                    onChange={(e) => setSelectedHostCountry(e.target.value)}
                    className="w-full bg-gray-700 text-white text-sm rounded-lg px-3 py-2 border border-gray-600 focus:outline-none focus:ring-2 focus:ring-emerald-500"
                  >
                    <option value="">Choisir un pays hote...</option>
                    {getZoneCountries(selectedZone).map(country => {
                      const feasibility = getBaseFeasibility(country.id);
                      return (
                        <option key={country.id} value={country.id}>
                          {COUNTRY_FLAGS[country.id] || ''} {country.name_fr} - Relations: {playerCountry.relations[country.id] || 0} ({feasibility.label})
                        </option>
                      );
                    })}
                  </select>
                </div>
              )}

              {/* Host country details */}
              {selectedHostCountry && (
                <div className="bg-gray-700/40 rounded-lg p-3 border border-gray-600">
                  {(() => {
                    const host = getHostCountryDetails(selectedHostCountry);
                    const feasibility = getBaseFeasibility(selectedHostCountry);
                    if (!host) return null;
                    return (
                      <div className="text-xs space-y-2">
                        <div className="flex items-center gap-2">
                          <span className="text-xl">{COUNTRY_FLAGS[host.id]}</span>
                          <div>
                            <div className="font-medium text-white">{host.name_fr}</div>
                            <div className="text-gray-400">Tier {host.tier} | {host.regime}</div>
                          </div>
                        </div>
                        <div className="grid grid-cols-3 gap-2 text-gray-400">
                          <div>
                            Relations: <span className={feasibility.color}>{playerCountry.relations[host.id] || 0}</span>
                          </div>
                          <div>
                            Stabilite: <span className="text-white">{host.stability}/100</span>
                          </div>
                          <div>
                            Faisabilite: <span className={feasibility.color}>{feasibility.label}</span>
                          </div>
                        </div>
                        {playerCountry.allies.includes(host.id) && (
                          <div className="text-green-400">&#10003; Pays allie - accord facilite</div>
                        )}
                      </div>
                    );
                  })()}
                </div>
              )}

              {/* Base type selection - Enhanced with details */}
              <div>
                <label className="block text-xs text-gray-500 mb-2">Type de base</label>
                <div className="grid grid-cols-2 gap-2">
                  {BASE_TYPES.map(type => (
                    <button
                      key={type.id}
                      onClick={() => {
                        setSelectedBaseType(type.id);
                        setBasePersonnel(type.defaultPersonnel);
                      }}
                      className={`p-2.5 rounded-lg text-left transition-all border ${
                        selectedBaseType === type.id
                          ? 'bg-emerald-600/30 border-emerald-500 text-white'
                          : 'bg-gray-700/50 border-gray-600 text-gray-300 hover:bg-gray-700'
                      }`}
                    >
                      <div className="flex items-center gap-2 mb-1">
                        <span dangerouslySetInnerHTML={{ __html: type.icon }} className="text-lg" />
                        <span className="font-medium text-sm">{type.name}</span>
                      </div>
                      <div className="text-xs text-gray-400">
                        {type.defaultPersonnel.toLocaleString()} pers. | -{type.costPerYear}/an
                      </div>
                    </button>
                  ))}
                </div>
              </div>

              {/* Selected base type details */}
              {selectedBaseDetails && (
                <div className="bg-emerald-900/20 rounded-lg p-3 border border-emerald-700/50">
                  <div className="text-xs space-y-2">
                    <div className="font-medium text-emerald-300">{selectedBaseDetails.name}</div>
                    <div className="text-gray-400">{selectedBaseDetails.description}</div>
                    <div className="text-gray-500 italic">Ex: {selectedBaseDetails.realExamples}</div>
                    <div className="flex flex-wrap gap-2 mt-2">
                      {Object.entries(selectedBaseDetails.effects).map(([key, val]) => (
                        <span key={key} className="px-2 py-0.5 bg-emerald-900/50 rounded text-emerald-300 text-xs">
                          {key.replace('_', ' ')}: +{val}
                        </span>
                      ))}
                    </div>
                  </div>
                </div>
              )}

              {/* Personnel slider */}
              <div>
                <label className="block text-xs text-gray-500 mb-1">
                  Personnel deploye: <span className="text-emerald-400 font-bold">{basePersonnel.toLocaleString()}</span>
                </label>
                <input
                  type="range"
                  min={200}
                  max={15000}
                  step={100}
                  value={basePersonnel}
                  onChange={(e) => setBasePersonnel(parseInt(e.target.value))}
                  className="w-full accent-emerald-500"
                />
                <div className="flex justify-between text-xs text-gray-500 mt-1">
                  <span>200 (minimal)</span>
                  <span>15,000 (majeur)</span>
                </div>
              </div>

              {/* Effects preview */}
              <div className="bg-gray-700/30 rounded-lg p-3 border border-gray-600">
                <div className="text-xs font-medium mb-2 text-gray-300">Effets estimes:</div>
                <div className="grid grid-cols-2 gap-2 text-xs">
                  <div className="flex justify-between">
                    <span className="text-gray-400">Cout economie:</span>
                    <span className="text-red-400">-{selectedBaseDetails?.costPerYear || 0}/an</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-400">Projection:</span>
                    <span className="text-emerald-400">+{Math.floor(basePersonnel / 500)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-400">Influence zone:</span>
                    <span className="text-blue-400">+{Math.floor(basePersonnel / 300)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-400">Relation hote:</span>
                    <span className="text-green-400">+5</span>
                  </div>
                </div>
              </div>

              {/* Submit button */}
              <button
                onClick={handleEstablishBase}
                disabled={loading || !selectedZone || !selectedHostCountry}
                className="w-full py-3 bg-emerald-600 hover:bg-emerald-500 disabled:bg-gray-600 disabled:cursor-not-allowed text-white rounded-lg font-medium transition-colors flex items-center justify-center gap-2"
              >
                {loading ? (
                  <>
                    <span className="animate-spin">&#9696;</span>
                    Etablissement en cours...
                  </>
                ) : (
                  <>
                    <span>&#9876;</span>
                    Etablir la base ({selectedBaseDetails?.name || ''})
                  </>
                )}
              </button>
            </>
          )}

          {/* ============================================ */}
          {/* CULTURAL PROGRAM TAB - ENHANCED */}
          {/* ============================================ */}
          {activeTab === 'cultural' && (
            <>
              <div className="text-sm text-gray-400 mb-3 flex items-center gap-2">
                <span>&#127758;</span>
                Projeter votre influence culturelle et votre soft power
              </div>

              {/* Zone selection */}
              <div>
                <label className="block text-xs text-gray-500 mb-1">Zone cible</label>
                <select
                  value={culturalZone}
                  onChange={(e) => setCulturalZone(e.target.value)}
                  className="w-full bg-gray-700 text-white text-sm rounded-lg px-3 py-2 border border-gray-600 focus:outline-none focus:ring-2 focus:ring-purple-500"
                >
                  <option value="">Choisir une zone...</option>
                  {zones.map(zone => (
                    <option key={zone.id} value={zone.id}>
                      {zone.name_fr} | Culture: {zone.dominant_culture || 'Mixte'} | Langue: {zone.dominant_language || 'Diverses'}
                    </option>
                  ))}
                </select>
              </div>

              {/* Zone cultural context */}
              {culturalZone && (
                <div className="bg-purple-900/20 rounded-lg p-3 border border-purple-700/50">
                  {(() => {
                    const zone = getZoneDetails(culturalZone);
                    if (!zone) return null;
                    return (
                      <div className="text-xs space-y-2">
                        <div className="font-medium text-purple-300">{zone.name_fr} - Contexte culturel</div>
                        <div className="grid grid-cols-2 gap-2 text-gray-400">
                          <div>Culture: <span className="text-white">{zone.dominant_culture || 'Diverse'}</span></div>
                          <div>Langue: <span className="text-white">{zone.dominant_language || 'Multiples'}</span></div>
                          <div>Religion: <span className="text-white">{zone.dominant_religion || 'Diverse'}</span></div>
                          <div>Ex-colonial: <span className="text-white">{zone.former_colonial_power ? `${COUNTRY_FLAGS[zone.former_colonial_power]} ${zone.former_colonial_power}` : 'Aucun'}</span></div>
                        </div>
                        {zone.former_colonial_power === playerCountry.id && (
                          <div className="text-yellow-400 mt-1">&#9733; Liens coloniaux - influence bonus</div>
                        )}
                      </div>
                    );
                  })()}
                </div>
              )}

              {/* Program type selection - Enhanced */}
              <div>
                <label className="block text-xs text-gray-500 mb-2">Type de programme</label>
                <div className="space-y-2">
                  {CULTURAL_PROGRAMS.map(program => (
                    <button
                      key={program.id}
                      onClick={() => setCulturalProgram(program.id)}
                      className={`w-full p-3 rounded-lg text-left transition-all border ${
                        culturalProgram === program.id
                          ? 'bg-purple-600/30 border-purple-500'
                          : 'bg-gray-700/50 border-gray-600 hover:bg-gray-700'
                      }`}
                    >
                      <div className="flex items-center gap-2 mb-1">
                        <span dangerouslySetInnerHTML={{ __html: program.icon }} className="text-lg" />
                        <span className="font-medium text-sm text-white">{program.name}</span>
                        <span className="text-xs text-gray-500 ml-auto">Cout: {program.baseCost}</span>
                      </div>
                      <div className="text-xs text-gray-400">{program.description}</div>
                    </button>
                  ))}
                </div>
              </div>

              {/* Selected program details with real examples */}
              {selectedCulturalDetails && (
                <div className="bg-purple-900/20 rounded-lg p-3 border border-purple-700/50">
                  <div className="text-xs space-y-2">
                    <div className="font-medium text-purple-300">Exemples reels dans le monde:</div>
                    <div className="space-y-1">
                      {selectedCulturalDetails.realExamples.map((ex, i) => (
                        <div key={i} className="flex items-center gap-2 text-gray-400">
                          <span>{COUNTRY_FLAGS[ex.power] || ex.power}</span>
                          <span className="text-white">{ex.name}</span>
                          <span className="text-gray-500 ml-auto">{ex.reach}</span>
                        </div>
                      ))}
                    </div>
                    <div className="text-gray-500 mt-2">Duree d'effet: {selectedCulturalDetails.duration}</div>
                    <div className="flex flex-wrap gap-2 mt-2">
                      {Object.entries(selectedCulturalDetails.effects).map(([key, val]) => (
                        <span key={key} className="px-2 py-0.5 bg-purple-900/50 rounded text-purple-300 text-xs">
                          {key.replace('_', ' ')}: +{val}
                        </span>
                      ))}
                    </div>
                  </div>
                </div>
              )}

              {/* Investment slider */}
              <div>
                <label className="block text-xs text-gray-500 mb-1">
                  Investissement: <span className="text-purple-400 font-bold">{culturalInvestment}</span>/100
                  <span className="text-gray-500 ml-2">(Cout eco: -{Math.floor(culturalInvestment / 5)}/an)</span>
                </label>
                <input
                  type="range"
                  min={10}
                  max={100}
                  step={10}
                  value={culturalInvestment}
                  onChange={(e) => setCulturalInvestment(parseInt(e.target.value))}
                  className="w-full accent-purple-500"
                />
                <div className="flex justify-between text-xs text-gray-500 mt-1">
                  <span>10 (symbolique)</span>
                  <span>100 (massif)</span>
                </div>
              </div>

              {/* Effects preview */}
              <div className="bg-gray-700/30 rounded-lg p-3 border border-gray-600">
                <div className="text-xs font-medium mb-2 text-gray-300">Effets estimes:</div>
                <div className="grid grid-cols-2 gap-2 text-xs">
                  <div className="flex justify-between">
                    <span className="text-gray-400">Influence culturelle:</span>
                    <span className="text-purple-400">+{Math.floor((selectedCulturalDetails?.effects.cultural || 0) * culturalInvestment / 50)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-400">Soft power global:</span>
                    <span className="text-blue-400">+{Math.floor(culturalInvestment / 10)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-400">Influence zone:</span>
                    <span className="text-green-400">+{Math.floor(culturalInvestment / 8)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-400">Temps d'effet:</span>
                    <span className="text-gray-300">{selectedCulturalDetails?.duration || 'Variable'}</span>
                  </div>
                </div>
              </div>

              {/* Submit button */}
              <button
                onClick={handleLaunchCulturalProgram}
                disabled={loading || !culturalZone}
                className="w-full py-3 bg-purple-600 hover:bg-purple-500 disabled:bg-gray-600 disabled:cursor-not-allowed text-white rounded-lg font-medium transition-colors flex items-center justify-center gap-2"
              >
                {loading ? (
                  <>
                    <span className="animate-spin">&#9696;</span>
                    Lancement en cours...
                  </>
                ) : (
                  <>
                    <span dangerouslySetInnerHTML={{ __html: selectedCulturalDetails?.icon || '&#127891;' }} />
                    Lancer {selectedCulturalDetails?.name || 'le programme'}
                  </>
                )}
              </button>
            </>
          )}

          {/* ============================================ */}
          {/* ARMS DEAL TAB - ENHANCED */}
          {/* ============================================ */}
          {activeTab === 'arms' && (
            <>
              <div className="text-sm text-gray-400 mb-3 flex items-center gap-2">
                <span>&#128296;</span>
                Vendre du materiel militaire - economie et influence
              </div>

              {/* Arms category selection */}
              <div>
                <label className="block text-xs text-gray-500 mb-2">Categorie d'armement</label>
                <div className="grid grid-cols-2 gap-2">
                  {ARMS_CATEGORIES.map(cat => (
                    <button
                      key={cat.id}
                      onClick={() => {
                        setArmsCategory(cat.id);
                        setArmsValue(cat.valueRange[0] + Math.floor((cat.valueRange[1] - cat.valueRange[0]) / 2));
                      }}
                      className={`p-2 rounded-lg text-left transition-all border ${
                        armsCategory === cat.id
                          ? 'bg-red-600/30 border-red-500'
                          : 'bg-gray-700/50 border-gray-600 hover:bg-gray-700'
                      }`}
                    >
                      <div className="flex items-center gap-2">
                        <span dangerouslySetInnerHTML={{ __html: cat.icon }} />
                        <span className="font-medium text-sm text-white">{cat.name}</span>
                      </div>
                      <div className="text-xs text-gray-500 mt-1">{cat.examples}</div>
                    </button>
                  ))}
                </div>
              </div>

              {/* Buyer selection */}
              <div>
                <label className="block text-xs text-gray-500 mb-1">Acheteur</label>
                <select
                  value={armsBuyer}
                  onChange={(e) => setArmsBuyer(e.target.value)}
                  className="w-full bg-gray-700 text-white text-sm rounded-lg px-3 py-2 border border-gray-600 focus:outline-none focus:ring-2 focus:ring-red-500"
                >
                  <option value="">Choisir un acheteur...</option>
                  <optgroup label="Allies et amis">
                    {potentialBuyers.filter(c => c.relation >= 30).map(country => (
                      <option key={country.id} value={country.id}>
                        {COUNTRY_FLAGS[country.id] || ''} {country.name_fr} | Rel: {country.relation} {country.isAlly ? '(Allie)' : ''}
                      </option>
                    ))}
                  </optgroup>
                  <optgroup label="Neutres et autres">
                    {potentialBuyers.filter(c => c.relation < 30 && !c.isRival).map(country => (
                      <option key={country.id} value={country.id}>
                        {COUNTRY_FLAGS[country.id] || ''} {country.name_fr} | Rel: {country.relation}
                      </option>
                    ))}
                  </optgroup>
                  <optgroup label="Relations tendues">
                    {potentialBuyers.filter(c => c.isRival).map(country => (
                      <option key={country.id} value={country.id}>
                        {COUNTRY_FLAGS[country.id] || ''} {country.name_fr} | Rel: {country.relation} (Rival)
                      </option>
                    ))}
                  </optgroup>
                </select>
              </div>

              {/* Buyer details */}
              {armsBuyer && (
                <div className="bg-gray-700/40 rounded-lg p-3 border border-gray-600">
                  {(() => {
                    const buyer = allCountries.find(c => c.id === armsBuyer);
                    if (!buyer) return null;
                    const isAlly = playerCountry.allies.includes(armsBuyer);
                    const isRival = playerCountry.rivals.includes(armsBuyer);
                    return (
                      <div className="text-xs space-y-2">
                        <div className="flex items-center gap-2">
                          <span className="text-2xl">{COUNTRY_FLAGS[buyer.id]}</span>
                          <div>
                            <div className="font-medium text-white">{buyer.name_fr}</div>
                            <div className="text-gray-400">Tier {buyer.tier} | {buyer.regime}</div>
                          </div>
                        </div>
                        <div className="grid grid-cols-3 gap-2 text-gray-400">
                          <div>Militaire: <span className="text-white">{buyer.military}/100</span></div>
                          <div>Economie: <span className="text-white">{buyer.economy}/100</span></div>
                          <div>Relations: <span className={isAlly ? 'text-green-400' : isRival ? 'text-red-400' : 'text-white'}>{playerCountry.relations[buyer.id] || 0}</span></div>
                        </div>
                        {isAlly && <div className="text-green-400">&#10003; Allie - prix preferentiel</div>}
                        {isRival && <div className="text-orange-400">&#9888; Rival - risque reputationnel</div>}
                        {buyer.at_war.length > 0 && <div className="text-red-400">&#9876; En guerre - demande urgente (+valeur)</div>}
                      </div>
                    );
                  })()}
                </div>
              )}

              {/* Selected arms details */}
              {selectedArmsDetails && (
                <div className="bg-red-900/20 rounded-lg p-3 border border-red-700/50">
                  <div className="text-xs space-y-2">
                    <div className="font-medium text-red-300">{selectedArmsDetails.name}</div>
                    <div className="text-gray-400">Exemples: {selectedArmsDetails.examples}</div>
                    <div className="grid grid-cols-2 gap-2 text-gray-400">
                      <div>Boost militaire acheteur: <span className="text-red-400">+{selectedArmsDetails.militaryBoost}</span></div>
                      <div>Niveau de dependance: <span className="text-yellow-400">{selectedArmsDetails.dependencyLevel}</span></div>
                    </div>
                  </div>
                </div>
              )}

              {/* Deal value slider */}
              <div>
                <label className="block text-xs text-gray-500 mb-1">
                  Valeur du contrat: <span className="text-red-400 font-bold">{armsValue}</span>
                  <span className="text-gray-500 ml-2">(~{armsValue * 100}M$ equivalent)</span>
                </label>
                <input
                  type="range"
                  min={selectedArmsDetails?.valueRange[0] || 10}
                  max={selectedArmsDetails?.valueRange[1] || 100}
                  step={5}
                  value={armsValue}
                  onChange={(e) => setArmsValue(parseInt(e.target.value))}
                  className="w-full accent-red-500"
                />
                <div className="flex justify-between text-xs text-gray-500 mt-1">
                  <span>{selectedArmsDetails?.valueRange[0] || 10} (Leger)</span>
                  <span>{selectedArmsDetails?.valueRange[1] || 100} (Massif)</span>
                </div>
              </div>

              {/* Effects preview - Enhanced */}
              {(() => {
                const effects = getArmsDealEffects();
                if (!effects) return null;
                return (
                  <div className="bg-gray-700/30 rounded-lg p-3 border border-gray-600">
                    <div className="text-xs font-medium mb-2 text-gray-300">Effets du contrat:</div>
                    <div className="grid grid-cols-2 gap-2 text-xs">
                      <div className="flex justify-between">
                        <span className="text-gray-400">Votre economie:</span>
                        <span className="text-green-400">+{effects.sellerEconomy}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-400">Leur militaire:</span>
                        <span className="text-red-400">+{effects.buyerMilitary}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-400">Relations:</span>
                        <span className="text-blue-400">+{effects.relationBoost}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-400">Dependance:</span>
                        <span className="text-yellow-400">{effects.dependency}</span>
                      </div>
                    </div>
                    <div className="mt-2 pt-2 border-t border-gray-600 text-gray-500">
                      <div className="flex items-center gap-1">
                        <span>&#9888;</span>
                        <span>L'acheteur deviendra dependant de vos pieces et maintenance</span>
                      </div>
                    </div>
                  </div>
                );
              })()}

              {/* Submit button */}
              <button
                onClick={handleSignArmsDeal}
                disabled={loading || !armsBuyer}
                className="w-full py-3 bg-red-600 hover:bg-red-500 disabled:bg-gray-600 disabled:cursor-not-allowed text-white rounded-lg font-medium transition-colors flex items-center justify-center gap-2"
              >
                {loading ? (
                  <>
                    <span className="animate-spin">&#9696;</span>
                    Signature en cours...
                  </>
                ) : (
                  <>
                    <span dangerouslySetInnerHTML={{ __html: selectedArmsDetails?.icon || '&#128296;' }} />
                    Signer le contrat ({selectedArmsDetails?.name || 'armes'})
                  </>
                )}
              </button>
            </>
          )}

          {/* Result message */}
          {result && (
            <div className={`p-3 rounded-lg ${result.success ? 'bg-green-900/50 border border-green-700' : 'bg-red-900/50 border border-red-700'}`}>
              <div className="flex items-center gap-2">
                <span>{result.success ? '&#9989;' : '&#10060;'}</span>
                <span className="text-sm">{result.message}</span>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
