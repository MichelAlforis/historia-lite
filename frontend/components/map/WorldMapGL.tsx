'use client';

import { useState, useCallback, useMemo, useEffect, useRef, KeyboardEvent } from 'react';
import Map, { Source, Layer, Popup, NavigationControl } from 'react-map-gl/maplibre';
import type { MapRef, MapLayerMouseEvent } from 'react-map-gl/maplibre';
import type { FeatureCollection, Feature, Geometry } from 'geojson';
import 'maplibre-gl/dist/maplibre-gl.css';

// Keyboard navigation keys
const KEYBOARD_KEYS = {
  NEXT: ['Tab', 'ArrowRight', 'ArrowDown'] as string[],
  PREV: ['ArrowLeft', 'ArrowUp'] as string[],
  SELECT: ['Enter', ' '] as string[],
  ESCAPE: ['Escape'] as string[],
};

import {
  Country,
  Tier4Country,
  Tier5Country,
  Tier6Country,
  SubnationalRegion,
  getPowerScoreColor,
  INFLUENCE_POWER_COLORS,
  COUNTRY_FLAGS,
} from '@/lib/types';

// Simple throttle function to limit hover updates
function throttle<T extends (...args: any[]) => void>(func: T, limit: number): T {
  let lastCall = 0;
  return ((...args: Parameters<T>) => {
    const now = Date.now();
    if (now - lastCall >= limit) {
      lastCall = now;
      func(...args);
    }
  }) as T;
}

// Map style - light pastel background (ocean)
const MAP_STYLE = {
  version: 8 as const,
  name: 'Historia Lite',
  sources: {
    'ocean': {
      type: 'geojson' as const,
      data: {
        type: 'Feature' as const,
        geometry: {
          type: 'Polygon' as const,
          coordinates: [[[-180, -90], [180, -90], [180, 90], [-180, 90], [-180, -90]]],
        },
        properties: {},
      },
    },
  },
  layers: [
    {
      id: 'ocean-background',
      type: 'fill' as const,
      source: 'ocean',
      paint: {
        'fill-color': '#bae6fd', // sky-200 - light blue ocean
      },
    },
  ],
};

// Country code to ISO3 mapping for GeoJSON (Natural Earth uses ISO_A3)
const ISO2_TO_ISO3: Record<string, string> = {
  US: 'USA', CN: 'CHN', RU: 'RUS', FR: 'FRA', DE: 'DEU', GB: 'GBR',
  JP: 'JPN', IN: 'IND', BR: 'BRA', KR: 'KOR', IT: 'ITA', CA: 'CAN',
  AU: 'AUS', ES: 'ESP', MX: 'MEX', ID: 'IDN', NL: 'NLD', SA: 'SAU',
  TR: 'TUR', CH: 'CHE', PL: 'POL', SE: 'SWE', BE: 'BEL', TH: 'THA',
  AT: 'AUT', NO: 'NOR', AE: 'ARE', IL: 'ISR', IE: 'IRL', SG: 'SGP',
  HK: 'HKG', DK: 'DNK', MY: 'MYS', PH: 'PHL', ZA: 'ZAF', FI: 'FIN',
  CL: 'CHL', EG: 'EGY', PK: 'PAK', PT: 'PRT', CZ: 'CZE', RO: 'ROU',
  NZ: 'NZL', PE: 'PER', GR: 'GRC', IQ: 'IRQ', KZ: 'KAZ', QA: 'QAT',
  HU: 'HUN', KW: 'KWT', CO: 'COL', UA: 'UKR', NG: 'NGA', MA: 'MAR',
  BD: 'BGD', VN: 'VNM', IR: 'IRN', TW: 'TWN', KP: 'PRK',
  AR: 'ARG', VE: 'VEN', ET: 'ETH', MM: 'MMR', AF: 'AFG', DZ: 'DZA',
};

interface WorldMapGLProps {
  // Country data from all tiers
  countries: Country[];
  tier4Countries: Tier4Country[];
  tier5Countries: Tier5Country[];
  tier6Countries: Tier6Country[];
  regions: SubnationalRegion[];

  // Selection state
  selectedCountryId?: string | null;
  selectedRegionId?: string | null;
  highlightedInfluence?: string[];

  // Relations mode data
  playerCountryId?: string | null;
  playerRelations?: Record<string, number>;
  playerAllies?: string[];
  playerRivals?: string[];
  playerAtWar?: string[];

  // Callbacks
  onCountryClick?: (countryId: string) => void;
  onRegionClick?: (regionId: string) => void;
  onCountryHover?: (countryId: string | null) => void;

  // View options
  viewMode?: 'power' | 'alignment' | 'protector' | 'relations';
  showRegions?: boolean;
}

interface HoverInfo {
  longitude: number;
  latitude: number;
  countryId: string;
  countryName: string;
  tier: number;
  powerScore: number;
}

export default function WorldMapGL({
  countries,
  tier4Countries,
  tier5Countries,
  tier6Countries,
  regions,
  selectedCountryId,
  selectedRegionId,
  highlightedInfluence = [],
  playerCountryId,
  playerRelations = {},
  playerAllies = [],
  playerRivals = [],
  playerAtWar = [],
  onCountryClick,
  onRegionClick,
  onCountryHover,
  viewMode = 'power',
  showRegions = true,
}: WorldMapGLProps) {
  const mapRef = useRef<MapRef>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const [rawGeoData, setRawGeoData] = useState<FeatureCollection | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [hoverInfo, setHoverInfo] = useState<HoverInfo | null>(null);
  const [zoom, setZoom] = useState(1.5);

  // Accessibility state
  const [focusedRegionIndex, setFocusedRegionIndex] = useState<number>(-1);
  const [isMapFocused, setIsMapFocused] = useState(false);
  const [announceMessage, setAnnounceMessage] = useState<string>('');

  // Build a lookup of all countries by ID for quick access
  const countryLookup = useMemo(() => {
    const lookup: Record<string, { tier: number; powerScore: number; name: string; alignment?: number; protector?: string }> = {};

    // Tier 1-3
    countries.forEach(c => {
      const score = Math.round(
        (c.economy + c.military + (c.nuclear || 0) + c.technology + c.stability + c.soft_power + c.resources) / 7
      );
      lookup[c.id] = { tier: c.tier, powerScore: score, name: c.name_fr };
    });

    // Tier 4
    tier4Countries.forEach(c => {
      const score = Math.round((c.economy + c.military + c.stability) / 3);
      lookup[c.id] = { tier: 4, powerScore: score, name: c.name_fr, alignment: c.alignment };
    });

    // Tier 5
    tier5Countries.forEach(c => {
      const score = Math.round((c.economy + c.stability) / 2);
      lookup[c.id] = { tier: 5, powerScore: score, name: c.name_fr, alignment: c.alignment };
    });

    // Tier 6
    tier6Countries.forEach(c => {
      const score = Math.round((c.economy + c.stability) / 2);
      lookup[c.id] = { tier: 6, powerScore: score, name: c.name_fr, protector: c.protector };
    });

    return lookup;
  }, [countries, tier4Countries, tier5Countries, tier6Countries]);

  // Load GeoJSON data once
  useEffect(() => {
    fetch('/geo/countries.geojson')
      .then(res => {
        if (!res.ok) {
          throw new Error(`HTTP ${res.status}: ${res.statusText}`);
        }
        return res.json();
      })
      .then((data: FeatureCollection) => {
        setRawGeoData(data);
        setLoadError(null);
      })
      .catch(err => {
        setLoadError(err.message || 'Erreur de chargement de la carte');
      });
  }, []); // Only fetch once on mount

  // Enrich GeoJSON data with country info (separate from fetch to avoid re-fetching)
  const geoData = useMemo(() => {
    if (!rawGeoData) return null;

    return {
      ...rawGeoData,
      features: rawGeoData.features.map(feature => {
        // Support multiple GeoJSON formats: Natural Earth uses ISO_A3, others use ISO3166-1-Alpha-3
        const iso3 = feature.properties?.['ISO3166-1-Alpha-3']
          || feature.properties?.ISO_A3
          || feature.properties?.iso_a3;
        const countryInfo = countryLookup[iso3];

        // Relations mode data
        const relationValue = playerRelations[iso3] ?? 0;
        const isPlayerCountry = iso3 === playerCountryId;
        const isAlly = playerAllies.includes(iso3);
        const isRival = playerRivals.includes(iso3);
        const isAtWar = playerAtWar.includes(iso3);

        return {
          ...feature,
          properties: {
            ...feature.properties,
            iso3: iso3,
            tier: countryInfo?.tier || 7,
            powerScore: countryInfo?.powerScore || 10,
            countryName: countryInfo?.name || feature.properties?.name || feature.properties?.NAME || iso3,
            isSelected: iso3 === selectedCountryId,
            isHighlighted: highlightedInfluence.includes(iso3),
            // Relations properties
            relationValue: relationValue,
            isPlayerCountry: isPlayerCountry,
            isAlly: isAlly,
            isRival: isRival,
            isAtWar: isAtWar,
          },
        };
      }),
    } as FeatureCollection;
  }, [rawGeoData, countryLookup, selectedCountryId, highlightedInfluence, playerCountryId, playerRelations, playerAllies, playerRivals, playerAtWar]);

  // Generate fill color expression based on view mode
  const fillColorExpression = useMemo(() => {
    if (viewMode === 'power') {
      // Gradient based on power score
      return [
        'case',
        ['==', ['get', 'isSelected'], true],
        '#FFD700', // Gold for selected
        ['==', ['get', 'isHighlighted'], true],
        '#6495ED', // Cornflower blue for highlighted influence
        [
          'interpolate',
          ['linear'],
          ['get', 'powerScore'],
          0, '#6B7280',   // Gray for lowest
          20, '#60A5FA',  // Blue
          40, '#34D399',  // Green
          60, '#FBBF24',  // Yellow
          80, '#F97316',  // Orange
          100, '#EF4444', // Red for highest
        ],
      ];
    }

    if (viewMode === 'relations') {
      // Color based on relation with player country
      return [
        'case',
        // Player country = gold
        ['==', ['get', 'isPlayerCountry'], true],
        '#FFD700',
        // At war = dark red
        ['==', ['get', 'isAtWar'], true],
        '#991B1B',
        // Ally = emerald
        ['==', ['get', 'isAlly'], true],
        '#10B981',
        // Rival = orange
        ['==', ['get', 'isRival'], true],
        '#F97316',
        // Selected country
        ['==', ['get', 'isSelected'], true],
        '#A855F7',
        // Gradient based on relation value (-100 to +100)
        [
          'interpolate',
          ['linear'],
          ['get', 'relationValue'],
          -100, '#DC2626', // Red for hostile
          -50, '#F87171',  // Light red
          -20, '#FCA5A5',  // Very light red
          0, '#9CA3AF',    // Gray for neutral
          20, '#86EFAC',   // Very light green
          50, '#4ADE80',   // Light green
          100, '#22C55E',  // Green for friendly
        ],
      ];
    }

    // Default
    return '#4B5563';
  }, [viewMode]);

  // Handle hover - throttled to max 10 updates per second
  const handleHover = useCallback((event: MapLayerMouseEvent) => {
    const feature = event.features?.[0];
    if (feature && feature.properties) {
      const iso3 = feature.properties.iso3;
      setHoverInfo({
        longitude: event.lngLat.lng,
        latitude: event.lngLat.lat,
        countryId: iso3,
        countryName: feature.properties.countryName,
        tier: feature.properties.tier,
        powerScore: feature.properties.powerScore,
      });
      onCountryHover?.(iso3);
    } else {
      setHoverInfo(null);
      onCountryHover?.(null);
    }
  }, [onCountryHover]);

  // Throttled hover handler
  const onHover = useMemo(
    () => throttle(handleHover, 100), // Max 10 updates per second
    [handleHover]
  );

  // Handle click
  const onClick = useCallback((event: MapLayerMouseEvent) => {
    const feature = event.features?.[0];
    if (feature && feature.properties) {
      const iso3 = feature.properties.iso3;
      onCountryClick?.(iso3);
    }
  }, [onCountryClick]);

  // Handle zoom change
  const onZoomChange = useCallback(() => {
    if (mapRef.current) {
      setZoom(mapRef.current.getZoom());
    }
  }, []);

  // Regions for selected country
  const countryRegions = useMemo(() => {
    if (!selectedCountryId) return [];
    return regions.filter(r => r.country_id === selectedCountryId);
  }, [regions, selectedCountryId]);

  // Check if we should show regions (zoom level 4+)
  const shouldShowRegions = zoom >= 4 && showRegions && countryRegions.length > 0;

  // Announce message for screen readers
  const announce = useCallback((message: string) => {
    setAnnounceMessage(message);
    // Clear after announcement
    setTimeout(() => setAnnounceMessage(''), 1000);
  }, []);

  // Keyboard navigation handler
  const handleKeyDown = useCallback((e: KeyboardEvent<HTMLDivElement>) => {
    // Only handle keys when map is focused and country is selected
    if (!isMapFocused) return;

    const key = e.key;

    // Navigate between regions
    if (selectedCountryId && countryRegions.length > 0) {
      if (KEYBOARD_KEYS.NEXT.includes(key)) {
        e.preventDefault();
        const nextIndex = focusedRegionIndex < countryRegions.length - 1
          ? focusedRegionIndex + 1
          : 0;
        setFocusedRegionIndex(nextIndex);
        const region = countryRegions[nextIndex];
        announce(`Region ${region.name_fr}, score ${region.power_score}, valeur strategique ${region.strategic_value} sur 10`);
      } else if (KEYBOARD_KEYS.PREV.includes(key)) {
        e.preventDefault();
        const prevIndex = focusedRegionIndex > 0
          ? focusedRegionIndex - 1
          : countryRegions.length - 1;
        setFocusedRegionIndex(prevIndex);
        const region = countryRegions[prevIndex];
        announce(`Region ${region.name_fr}, score ${region.power_score}, valeur strategique ${region.strategic_value} sur 10`);
      } else if (KEYBOARD_KEYS.SELECT.includes(key)) {
        e.preventDefault();
        if (focusedRegionIndex >= 0 && focusedRegionIndex < countryRegions.length) {
          const region = countryRegions[focusedRegionIndex];
          onRegionClick?.(region.id);
          announce(`Region ${region.name_fr} selectionnee`);
        }
      }
    }

    // Escape to deselect
    if (KEYBOARD_KEYS.ESCAPE.includes(key)) {
      e.preventDefault();
      setFocusedRegionIndex(-1);
      announce('Selection annulee');
    }
  }, [isMapFocused, selectedCountryId, countryRegions, focusedRegionIndex, onRegionClick, announce]);

  // Reset focus index when country changes
  useEffect(() => {
    setFocusedRegionIndex(-1);
  }, [selectedCountryId]);

  // Error state
  if (loadError) {
    return (
      <div className="w-full h-full flex items-center justify-center bg-sky-100">
        <div className="text-center p-6 bg-white rounded-2xl shadow-lg max-w-md">
          <div className="text-rose-600 text-lg mb-2">Erreur de chargement</div>
          <div className="text-stone-500 text-sm mb-4">{loadError}</div>
          <button
            onClick={() => {
              setLoadError(null);
              window.location.reload();
            }}
            className="px-4 py-2 bg-sky-500 text-white rounded-xl hover:bg-sky-600 transition"
          >
            Recharger la page
          </button>
        </div>
      </div>
    );
  }

  // Loading state
  if (!geoData) {
    return (
      <div className="w-full h-full flex items-center justify-center bg-sky-100">
        <div className="flex items-center gap-3 text-stone-600">
          <div className="w-5 h-5 border-2 border-sky-500 border-t-transparent rounded-full animate-spin" />
          <span>Chargement de la carte...</span>
        </div>
      </div>
    );
  }

  return (
    <div
      ref={containerRef}
      className="relative w-full h-full"
      role="application"
      aria-label="Carte mondiale interactive des pays et regions"
      aria-describedby="map-instructions"
      tabIndex={0}
      onKeyDown={handleKeyDown}
      onFocus={() => setIsMapFocused(true)}
      onBlur={() => setIsMapFocused(false)}
    >
      {/* Screen reader instructions (visually hidden) */}
      <div id="map-instructions" className="sr-only">
        Carte interactive. Cliquez sur un pays pour voir ses details.
        {selectedCountryId && countryRegions.length > 0 && (
          ` Pays selectionne: ${countryLookup[selectedCountryId]?.name}.
          Utilisez les fleches ou Tab pour naviguer entre les ${countryRegions.length} regions.
          Appuyez sur Entree pour selectionner une region.
          Appuyez sur Echap pour annuler.`
        )}
      </div>

      {/* Live region for announcements */}
      <div
        role="status"
        aria-live="polite"
        aria-atomic="true"
        className="sr-only"
      >
        {announceMessage}
      </div>

      <Map
        ref={mapRef}
        initialViewState={{
          longitude: 10,
          latitude: 30,
          zoom: 1.5,
        }}
        style={{ width: '100%', height: '100%' }}
        mapStyle={MAP_STYLE}
        interactiveLayerIds={['countries-fill']}
        onMouseMove={onHover}
        onMouseLeave={() => setHoverInfo(null)}
        onClick={onClick}
        onZoom={onZoomChange}
        maxZoom={8}
        minZoom={1}
      >
        <NavigationControl position="top-right" />

        {/* Countries layer */}
        <Source id="countries" type="geojson" data={geoData}>
          {/* Fill layer */}
          <Layer
            id="countries-fill"
            type="fill"
            paint={{
              'fill-color': fillColorExpression as any,
              'fill-opacity': [
                'case',
                ['==', ['get', 'isSelected'], true],
                0.9,
                ['==', ['get', 'isHighlighted'], true],
                0.7,
                0.6,
              ],
            }}
          />

          {/* Border layer */}
          <Layer
            id="countries-border"
            type="line"
            paint={{
              'line-color': [
                'case',
                ['==', ['get', 'isSelected'], true],
                '#f59e0b', // amber-500 for selected
                '#94a3b8', // slate-400 for borders
              ],
              'line-width': [
                'case',
                ['==', ['get', 'isSelected'], true],
                2.5,
                0.8,
              ],
            }}
          />

          {/* Labels at higher zoom */}
          {zoom >= 3 && (
            <Layer
              id="countries-label"
              type="symbol"
              layout={{
                'text-field': ['get', 'iso3'],
                'text-size': 10,
                'text-anchor': 'center',
              }}
              paint={{
                'text-color': '#1e293b', // slate-800
                'text-halo-color': '#ffffff',
                'text-halo-width': 1.5,
              }}
            />
          )}
        </Source>

        {/* Hover popup */}
        {hoverInfo && (
          <Popup
            longitude={hoverInfo.longitude}
            latitude={hoverInfo.latitude}
            closeButton={false}
            closeOnClick={false}
            anchor="bottom"
            offset={10}
          >
            <div className="bg-white text-stone-800 p-2 rounded-xl shadow-lg text-sm">
              <div className="font-bold flex items-center gap-2">
                <span>{COUNTRY_FLAGS[hoverInfo.countryId] || ''}</span>
                <span>{hoverInfo.countryName}</span>
              </div>
              <div className="text-stone-500 text-xs mt-1">
                Tier {hoverInfo.tier} | Score: {hoverInfo.powerScore}
              </div>
            </div>
          </Popup>
        )}
      </Map>

      {/* Legend */}
      <div
        className="absolute bottom-4 left-4 bg-white/95 shadow-lg p-3 rounded-xl text-xs text-stone-700"
        role="img"
        aria-label="Legende: echelle de puissance de 0 (gris) a 100 (rouge)"
      >
        <div className="font-semibold mb-2 text-stone-800">Puissance</div>
        <div className="flex items-center gap-1">
          <div className="w-4 h-3 rounded" style={{ backgroundColor: '#EF4444' }} />
          <span>100</span>
        </div>
        <div className="flex items-center gap-1">
          <div className="w-4 h-3 rounded" style={{ backgroundColor: '#F97316' }} />
          <span>80</span>
        </div>
        <div className="flex items-center gap-1">
          <div className="w-4 h-3 rounded" style={{ backgroundColor: '#FBBF24' }} />
          <span>60</span>
        </div>
        <div className="flex items-center gap-1">
          <div className="w-4 h-3 rounded" style={{ backgroundColor: '#34D399' }} />
          <span>40</span>
        </div>
        <div className="flex items-center gap-1">
          <div className="w-4 h-3 rounded" style={{ backgroundColor: '#60A5FA' }} />
          <span>20</span>
        </div>
        <div className="flex items-center gap-1">
          <div className="w-4 h-3 rounded" style={{ backgroundColor: '#6B7280' }} />
          <span>0</span>
        </div>
      </div>

      {/* Zoom indicator */}
      <div className="absolute top-4 left-4 bg-white/95 shadow px-3 py-1 rounded-lg text-xs text-stone-600">
        Zoom: {zoom.toFixed(1)} {shouldShowRegions && '| Regions visibles'}
      </div>

      {/* Region info panel when a country with regions is selected */}
      {selectedCountryId && countryRegions.length > 0 && (
        <div
          className="absolute top-16 left-4 bg-white/95 shadow-lg p-3 rounded-xl text-sm text-stone-700 max-w-xs"
          role="region"
          aria-label={`Liste des regions de ${countryLookup[selectedCountryId]?.name}`}
        >
          <div className="font-semibold mb-2 flex items-center gap-2 text-stone-800">
            <span aria-hidden="true">{COUNTRY_FLAGS[selectedCountryId] || ''}</span>
            <span>Regions de {countryLookup[selectedCountryId]?.name}</span>
          </div>
          <div
            className="space-y-1 max-h-48 overflow-y-auto"
            role="listbox"
            aria-label="Regions disponibles"
            aria-activedescendant={focusedRegionIndex >= 0 ? `region-${countryRegions[focusedRegionIndex]?.id}` : undefined}
          >
            {countryRegions.map((region, index) => (
              <button
                key={region.id}
                id={`region-${region.id}`}
                role="option"
                aria-selected={selectedRegionId === region.id}
                onClick={() => onRegionClick?.(region.id)}
                className={`w-full text-left px-2 py-1 rounded-lg text-xs transition-colors
                  ${selectedRegionId === region.id ? 'bg-amber-100 text-amber-800' : 'bg-stone-50'}
                  ${focusedRegionIndex === index ? 'ring-2 ring-sky-500 ring-offset-1' : ''}
                  hover:bg-sky-50 focus:outline-none focus:ring-2 focus:ring-sky-500
                `}
              >
                <div className="font-medium">{region.name_fr}</div>
                <div className="text-stone-500 flex justify-between">
                  <span>Score: {region.power_score}</span>
                  <span>Strat: {region.strategic_value}/10</span>
                </div>
              </button>
            ))}
          </div>
          <div className="mt-2 text-xs text-stone-400">
            {isMapFocused ? (
              <span>Fleches pour naviguer, Entree pour selectionner</span>
            ) : (
              <span>Zoomez (4+) pour voir les regions sur la carte</span>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
