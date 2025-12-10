'use client';

import { useState, useEffect, useCallback, useRef, useMemo } from 'react';
import { COUNTRY_FLAGS, InfluenceZone, GameEvent } from '@/lib/types';

interface NotificationCenterProps {
  events: GameEvent[];
  zones: InfluenceZone[];
  previousZones?: InfluenceZone[];
  currentYear?: number;
  playerPower?: string;
}

interface Notification {
  id: string;
  type: NotificationType;
  title: string;
  message: string;
  timestamp: number;
  priority: 'critical' | 'high' | 'medium' | 'low';
  zone?: string;
  zoneName?: string;
  countries?: string[];
  read: boolean;
  dismissed: boolean;
  details?: NotificationDetails;
}

interface NotificationDetails {
  previousPower?: string;
  newPower?: string;
  influenceChange?: number;
  affectedCountries?: string[];
  strategicImplications?: string[];
}

type NotificationType =
  | 'domination_change'
  | 'new_contestation'
  | 'contestation_resolved'
  | 'war_declared'
  | 'war_escalation'
  | 'ceasefire'
  | 'peace_treaty'
  | 'crisis_outbreak'
  | 'crisis_resolved'
  | 'nuclear_threat'
  | 'nuclear_test'
  | 'coup_attempt'
  | 'regime_change'
  | 'alliance_formed'
  | 'alliance_broken'
  | 'sanctions_imposed'
  | 'sanctions_lifted'
  | 'influence_surge'
  | 'influence_collapse'
  | 'military_buildup'
  | 'base_established'
  | 'humanitarian_crisis'
  | 'economic_crisis'
  | 'election_result'
  | 'diplomatic_incident';

// Notification configuration with icons, colors, and sounds
const NOTIFICATION_CONFIG: Record<NotificationType, {
  icon: string;
  label: string;
  defaultPriority: Notification['priority'];
  sound?: 'critical' | 'alert' | 'info';
  animate?: boolean;
}> = {
  domination_change: { icon: '👑', label: 'Changement de domination', defaultPriority: 'high', sound: 'alert', animate: true },
  new_contestation: { icon: '⚔️', label: 'Nouvelle contestation', defaultPriority: 'medium', sound: 'info' },
  contestation_resolved: { icon: '✓', label: 'Contestation resolue', defaultPriority: 'low' },
  war_declared: { icon: '🔥', label: 'Declaration de guerre', defaultPriority: 'critical', sound: 'critical', animate: true },
  war_escalation: { icon: '💥', label: 'Escalade militaire', defaultPriority: 'critical', sound: 'critical', animate: true },
  ceasefire: { icon: '🕊️', label: 'Cessez-le-feu', defaultPriority: 'high', sound: 'info' },
  peace_treaty: { icon: '🤝', label: 'Traite de paix', defaultPriority: 'high', sound: 'info' },
  crisis_outbreak: { icon: '⚠️', label: 'Crise declenchee', defaultPriority: 'high', sound: 'alert', animate: true },
  crisis_resolved: { icon: '✅', label: 'Crise resolue', defaultPriority: 'medium' },
  nuclear_threat: { icon: '☢️', label: 'Menace nucleaire', defaultPriority: 'critical', sound: 'critical', animate: true },
  nuclear_test: { icon: '💣', label: 'Test nucleaire', defaultPriority: 'critical', sound: 'critical', animate: true },
  coup_attempt: { icon: '🎖️', label: 'Tentative de coup', defaultPriority: 'high', sound: 'alert', animate: true },
  regime_change: { icon: '🏛️', label: 'Changement de regime', defaultPriority: 'high', sound: 'alert' },
  alliance_formed: { icon: '🤜🤛', label: 'Alliance formee', defaultPriority: 'medium', sound: 'info' },
  alliance_broken: { icon: '💔', label: 'Alliance rompue', defaultPriority: 'high', sound: 'alert' },
  sanctions_imposed: { icon: '🚫', label: 'Sanctions imposees', defaultPriority: 'medium', sound: 'info' },
  sanctions_lifted: { icon: '✨', label: 'Sanctions levees', defaultPriority: 'low' },
  influence_surge: { icon: '📈', label: 'Montee en influence', defaultPriority: 'medium' },
  influence_collapse: { icon: '📉', label: 'Effondrement influence', defaultPriority: 'high', sound: 'alert' },
  military_buildup: { icon: '🛡️', label: 'Renforcement militaire', defaultPriority: 'medium' },
  base_established: { icon: '🏴', label: 'Base etablie', defaultPriority: 'medium' },
  humanitarian_crisis: { icon: '🆘', label: 'Crise humanitaire', defaultPriority: 'high', sound: 'alert' },
  economic_crisis: { icon: '💸', label: 'Crise economique', defaultPriority: 'high', sound: 'alert' },
  election_result: { icon: '🗳️', label: 'Resultat electoral', defaultPriority: 'medium' },
  diplomatic_incident: { icon: '🎭', label: 'Incident diplomatique', defaultPriority: 'medium', sound: 'info' },
};

// Priority styling
const PRIORITY_STYLES: Record<Notification['priority'], {
  border: string;
  bg: string;
  badge: string;
  glow: string;
}> = {
  critical: {
    border: 'border-red-500',
    bg: 'bg-red-900/40',
    badge: 'bg-red-500',
    glow: 'shadow-red-500/30',
  },
  high: {
    border: 'border-orange-500',
    bg: 'bg-orange-900/30',
    badge: 'bg-orange-500',
    glow: 'shadow-orange-500/20',
  },
  medium: {
    border: 'border-yellow-500',
    bg: 'bg-yellow-900/20',
    badge: 'bg-yellow-500',
    glow: '',
  },
  low: {
    border: 'border-blue-500',
    bg: 'bg-blue-900/20',
    badge: 'bg-blue-500',
    glow: '',
  },
};

// Real-world geopolitical event templates for simulation
const GEOPOLITICAL_EVENTS: Array<{
  type: NotificationType;
  title: string;
  message: string;
  zones: string[];
  countries: string[];
}> = [
  {
    type: 'war_escalation',
    title: 'Escalade Ukraine-Russie',
    message: 'Intensification des combats sur le front Est. Nouveaux bombardements sur les infrastructures.',
    zones: ['eastern_europe'],
    countries: ['RUS', 'UKR'],
  },
  {
    type: 'nuclear_threat',
    title: 'Tensions nucleaires Coree',
    message: 'La Coree du Nord menace de tests nucleaires. Le Conseil de securite convoque en urgence.',
    zones: ['east_asia'],
    countries: ['PRK', 'USA', 'KOR', 'JPN'],
  },
  {
    type: 'coup_attempt',
    title: 'Coup d\'Etat au Sahel',
    message: 'Tentative de putsch militaire. L\'Union Africaine condamne et appelle au calme.',
    zones: ['west_africa'],
    countries: ['FRA', 'RUS'],
  },
  {
    type: 'crisis_outbreak',
    title: 'Crise Taiwan',
    message: 'Exercices militaires chinois dans le detroit. Washington renforce sa presence navale.',
    zones: ['east_asia', 'southeast_asia'],
    countries: ['CHN', 'USA', 'TWN', 'JPN'],
  },
  {
    type: 'sanctions_imposed',
    title: 'Nouvelles sanctions contre l\'Iran',
    message: 'Les Etats-Unis imposent de nouvelles sanctions sur le programme nucleaire iranien.',
    zones: ['middle_east_gulf'],
    countries: ['USA', 'IRN', 'ISR'],
  },
  {
    type: 'alliance_formed',
    title: 'Renforcement AUKUS',
    message: 'Australie, UK et USA annoncent de nouveaux accords de cooperation militaire.',
    zones: ['oceania', 'southeast_asia'],
    countries: ['AUS', 'GBR', 'USA'],
  },
  {
    type: 'humanitarian_crisis',
    title: 'Famine au Soudan',
    message: 'L\'ONU alerte sur la situation humanitaire catastrophique. Appel aux dons internationaux.',
    zones: ['east_africa'],
    countries: ['SDN'],
  },
  {
    type: 'military_buildup',
    title: 'Renforcement OTAN Est',
    message: 'Deploiement de nouvelles forces sur le flanc Est de l\'Alliance atlantique.',
    zones: ['eastern_europe'],
    countries: ['USA', 'DEU', 'POL'],
  },
];

export default function NotificationCenter({
  events,
  zones,
  previousZones,
  currentYear = 2025,
  playerPower,
}: NotificationCenterProps) {
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [expanded, setExpanded] = useState(false);
  const [filter, setFilter] = useState<'all' | 'important' | 'unread'>('all');
  const [toasts, setToasts] = useState<Notification[]>([]);
  const [bellAnimating, setBellAnimating] = useState(false);
  const processedEventIds = useRef<Set<string>>(new Set());
  const previousZonesRef = useRef<InfluenceZone[]>([]);

  // Detect zone changes and generate notifications
  const detectZoneChanges = useCallback(() => {
    if (!previousZonesRef.current.length || !zones.length) return [];

    const newNotifications: Notification[] = [];

    zones.forEach(zone => {
      const prevZone = previousZonesRef.current.find(z => z.id === zone.id);
      if (!prevZone) return;

      // Domination change detection
      if (prevZone.dominant_power !== zone.dominant_power) {
        const config = NOTIFICATION_CONFIG.domination_change;
        newNotifications.push({
          id: `dom-${zone.id}-${Date.now()}`,
          type: 'domination_change',
          title: `${zone.name_fr}: Changement de controle`,
          message: zone.dominant_power
            ? `${COUNTRY_FLAGS[zone.dominant_power]} ${zone.dominant_power} prend le controle, deplacant ${prevZone.dominant_power ? `${COUNTRY_FLAGS[prevZone.dominant_power]} ${prevZone.dominant_power}` : 'l\'ancien regime'}`
            : `${zone.name_fr} devient une zone contestee sans puissance dominante`,
          timestamp: Date.now(),
          priority: config.defaultPriority,
          zone: zone.id,
          zoneName: zone.name_fr,
          countries: [zone.dominant_power, prevZone.dominant_power].filter(Boolean) as string[],
          read: false,
          dismissed: false,
          details: {
            previousPower: prevZone.dominant_power || undefined,
            newPower: zone.dominant_power || undefined,
            strategicImplications: getStrategicImplications(zone),
          },
        });
      }

      // New contestation detection
      const newContesters = zone.contested_by.filter(c => !prevZone.contested_by.includes(c));
      if (newContesters.length > 0) {
        const config = NOTIFICATION_CONFIG.new_contestation;
        newNotifications.push({
          id: `contest-${zone.id}-${newContesters.join('-')}-${Date.now()}`,
          type: 'new_contestation',
          title: `${zone.name_fr}: Nouvelle rivalite`,
          message: `${newContesters.map(c => `${COUNTRY_FLAGS[c]} ${c}`).join(', ')} ${newContesters.length > 1 ? 'contestent' : 'conteste'} l'influence de ${zone.dominant_power ? `${COUNTRY_FLAGS[zone.dominant_power]} ${zone.dominant_power}` : 'la region'}`,
          timestamp: Date.now(),
          priority: config.defaultPriority,
          zone: zone.id,
          zoneName: zone.name_fr,
          countries: [...newContesters, zone.dominant_power].filter(Boolean) as string[],
          read: false,
          dismissed: false,
        });
      }

      // Contestation resolved
      const resolvedContesters = prevZone.contested_by.filter(c => !zone.contested_by.includes(c));
      if (resolvedContesters.length > 0 && zone.dominant_power) {
        newNotifications.push({
          id: `resolved-${zone.id}-${resolvedContesters.join('-')}-${Date.now()}`,
          type: 'contestation_resolved',
          title: `${zone.name_fr}: Stabilisation`,
          message: `${resolvedContesters.map(c => `${COUNTRY_FLAGS[c]} ${c}`).join(', ')} ${resolvedContesters.length > 1 ? 'abandonnent' : 'abandonne'} la contestation`,
          timestamp: Date.now(),
          priority: 'low',
          zone: zone.id,
          zoneName: zone.name_fr,
          countries: resolvedContesters,
          read: false,
          dismissed: false,
        });
      }

      // Major influence shift detection
      Object.entries(zone.influence_levels).forEach(([power, level]) => {
        const prevLevel = prevZone.influence_levels[power] || 0;
        const change = level - prevLevel;

        if (change >= 15) {
          newNotifications.push({
            id: `surge-${zone.id}-${power}-${Date.now()}`,
            type: 'influence_surge',
            title: `${zone.name_fr}: Montee de ${power}`,
            message: `${COUNTRY_FLAGS[power]} ${power} gagne ${change} points d'influence (+${Math.round((change / prevLevel) * 100)}%)`,
            timestamp: Date.now(),
            priority: 'medium',
            zone: zone.id,
            zoneName: zone.name_fr,
            countries: [power],
            read: false,
            dismissed: false,
            details: { influenceChange: change },
          });
        } else if (change <= -15) {
          newNotifications.push({
            id: `collapse-${zone.id}-${power}-${Date.now()}`,
            type: 'influence_collapse',
            title: `${zone.name_fr}: Recul de ${power}`,
            message: `${COUNTRY_FLAGS[power]} ${power} perd ${Math.abs(change)} points d'influence`,
            timestamp: Date.now(),
            priority: power === playerPower ? 'high' : 'medium',
            zone: zone.id,
            zoneName: zone.name_fr,
            countries: [power],
            read: false,
            dismissed: false,
            details: { influenceChange: change },
          });
        }
      });
    });

    return newNotifications;
  }, [zones, playerPower]);

  // Get strategic implications for a zone
  const getStrategicImplications = (zone: InfluenceZone): string[] => {
    const implications: string[] = [];
    if (zone.has_oil) implications.push('Controle des ressources petrolieres');
    if (zone.has_strategic_resources) implications.push('Acces aux minerais strategiques');
    if (zone.contested_by.length > 2) implications.push('Zone hautement disputee');
    return implications;
  };

  // Process game events
  useEffect(() => {
    if (!events.length) return;

    const newNotifications: Notification[] = [];

    events.forEach(event => {
      if (processedEventIds.current.has(event.id)) return;
      processedEventIds.current.add(event.id);

      let type: NotificationType = 'diplomatic_incident';
      let priority: Notification['priority'] = 'medium';

      // Map event types to notification types
      switch (event.type) {
        case 'war':
          type = 'war_declared';
          priority = 'critical';
          break;
        case 'peace':
          type = 'peace_treaty';
          priority = 'high';
          break;
        case 'crisis':
          type = 'crisis_outbreak';
          priority = 'high';
          break;
        case 'coup':
          type = 'coup_attempt';
          priority = 'high';
          break;
        case 'nuclear':
          type = 'nuclear_threat';
          priority = 'critical';
          break;
        default:
          return; // Skip unimportant events
      }

      newNotifications.push({
        id: `event-${event.id}`,
        type,
        title: event.title_fr,
        message: event.description_fr,
        timestamp: Date.now(),
        priority,
        read: false,
        dismissed: false,
      });
    });

    if (newNotifications.length > 0) {
      addNotifications(newNotifications);
    }
  }, [events]);

  // Detect zone changes when zones update
  useEffect(() => {
    if (previousZonesRef.current.length > 0) {
      const zoneNotifications = detectZoneChanges();
      if (zoneNotifications.length > 0) {
        addNotifications(zoneNotifications);
      }
    }
    previousZonesRef.current = [...zones];
  }, [zones, detectZoneChanges]);

  // Use provided previousZones on first load
  useEffect(() => {
    if (previousZones && previousZones.length > 0 && previousZonesRef.current.length === 0) {
      previousZonesRef.current = previousZones;
    }
  }, [previousZones]);

  // Add notifications with animations
  const addNotifications = useCallback((newNotifs: Notification[]) => {
    setNotifications(prev => {
      const combined = [...newNotifs, ...prev].slice(0, 100);
      return combined;
    });

    // Trigger bell animation
    setBellAnimating(true);
    setTimeout(() => setBellAnimating(false), 1000);

    // Show critical notifications as toasts
    const criticalNotifs = newNotifs.filter(n =>
      n.priority === 'critical' || (n.priority === 'high' && NOTIFICATION_CONFIG[n.type]?.sound)
    );

    if (criticalNotifs.length > 0) {
      setToasts(prev => [...criticalNotifs, ...prev].slice(0, 5));

      // Auto-dismiss toasts after 8 seconds
      criticalNotifs.forEach(notif => {
        setTimeout(() => {
          setToasts(prev => prev.filter(t => t.id !== notif.id));
        }, 8000);
      });
    }
  }, []);

  // Mark notification as read
  const markAsRead = useCallback((id: string) => {
    setNotifications(prev =>
      prev.map(n => n.id === id ? { ...n, read: true } : n)
    );
  }, []);

  // Mark all as read
  const markAllAsRead = useCallback(() => {
    setNotifications(prev => prev.map(n => ({ ...n, read: true })));
  }, []);

  // Dismiss toast
  const dismissToast = useCallback((id: string) => {
    setToasts(prev => prev.filter(t => t.id !== id));
    markAsRead(id);
  }, [markAsRead]);

  // Clear all notifications
  const clearAll = useCallback(() => {
    setNotifications([]);
    setToasts([]);
  }, []);

  // Filter notifications
  const filteredNotifications = useMemo(() => {
    return notifications.filter(n => {
      if (n.dismissed) return false;
      if (filter === 'important') return n.priority === 'critical' || n.priority === 'high';
      if (filter === 'unread') return !n.read;
      return true;
    });
  }, [notifications, filter]);

  // Counts
  const unreadCount = useMemo(() =>
    notifications.filter(n => !n.read && !n.dismissed).length
  , [notifications]);

  const criticalCount = useMemo(() =>
    notifications.filter(n => !n.read && !n.dismissed && (n.priority === 'critical' || n.priority === 'high')).length
  , [notifications]);

  // Format timestamp
  const formatTime = (timestamp: number) => {
    const diff = Date.now() - timestamp;
    if (diff < 60000) return 'A l\'instant';
    if (diff < 3600000) return `${Math.floor(diff / 60000)} min`;
    if (diff < 86400000) return `${Math.floor(diff / 3600000)} h`;
    return `${Math.floor(diff / 86400000)} j`;
  };

  // Get priority label
  const getPriorityLabel = (priority: Notification['priority']) => {
    switch (priority) {
      case 'critical': return 'URGENT';
      case 'high': return 'Important';
      case 'medium': return 'Info';
      case 'low': return 'Mineur';
    }
  };

  return (
    <>
      <div className="relative">
        {/* Notification bell button with animated badge */}
        <button
          onClick={() => setExpanded(!expanded)}
          className={`relative p-2.5 rounded-xl transition-all duration-300 ${
            expanded
              ? 'bg-amber-600 text-white shadow-lg shadow-amber-600/30'
              : 'bg-gray-700 text-gray-300 hover:bg-gray-600 hover:text-white'
          } ${bellAnimating ? 'animate-shake' : ''}`}
        >
          {/* Bell icon */}
          <span className={`text-xl block transition-transform ${bellAnimating ? 'animate-ring' : ''}`}>
            {'🔔'}
          </span>

          {/* Animated unread badge */}
          {unreadCount > 0 && (
            <span
              className={`absolute -top-1.5 -right-1.5 min-w-6 h-6 flex items-center justify-center text-xs font-bold rounded-full transform transition-all duration-300 ${
                criticalCount > 0
                  ? 'bg-red-500 animate-pulse shadow-lg shadow-red-500/50'
                  : 'bg-amber-500'
              }`}
              style={{
                animation: bellAnimating ? 'bounce 0.5s ease-in-out' : undefined,
              }}
            >
              {unreadCount > 99 ? '99+' : unreadCount}
            </span>
          )}

          {/* Critical indicator ring */}
          {criticalCount > 0 && (
            <span className="absolute inset-0 rounded-xl border-2 border-red-500 animate-ping opacity-30" />
          )}
        </button>

        {/* Expanded notification panel */}
        {expanded && (
          <div
            className="absolute right-0 top-14 w-[420px] bg-gray-800 rounded-xl shadow-2xl border border-gray-700 z-50 overflow-hidden"
            style={{
              animation: 'slideDown 0.2s ease-out',
            }}
          >
            {/* Header */}
            <div className="px-4 py-3 bg-gradient-to-r from-amber-900/60 to-gray-800 flex items-center justify-between border-b border-gray-700">
              <div className="flex items-center gap-3">
                <span className="text-xl">{'🔔'}</span>
                <div>
                  <span className="font-bold text-lg">Notifications</span>
                  <div className="text-xs text-gray-400">
                    Annee {currentYear} | Alertes geopolitiques
                  </div>
                </div>
              </div>
              <div className="flex gap-2">
                {unreadCount > 0 && (
                  <button
                    onClick={markAllAsRead}
                    className="px-2.5 py-1.5 text-xs bg-gray-700 hover:bg-gray-600 rounded-lg transition-colors flex items-center gap-1"
                    title="Tout marquer comme lu"
                  >
                    {'✓'} Lu
                  </button>
                )}
                <button
                  onClick={clearAll}
                  className="px-2.5 py-1.5 text-xs bg-gray-700 hover:bg-red-600 rounded-lg transition-colors"
                  title="Effacer tout"
                >
                  {'🗑️'}
                </button>
              </div>
            </div>

            {/* Filter tabs */}
            <div className="flex border-b border-gray-700">
              {([
                { key: 'all', label: 'Toutes', count: notifications.filter(n => !n.dismissed).length, highlight: false },
                { key: 'important', label: 'Importantes', count: criticalCount, highlight: criticalCount > 0 },
                { key: 'unread', label: 'Non lues', count: unreadCount, highlight: false },
              ] as const).map(({ key, label, count, highlight }) => (
                <button
                  key={key}
                  onClick={() => setFilter(key)}
                  className={`flex-1 px-3 py-2.5 text-sm font-medium transition-all flex items-center justify-center gap-2 ${
                    filter === key
                      ? 'bg-amber-600/30 text-amber-400 border-b-2 border-amber-500'
                      : 'text-gray-400 hover:bg-gray-700/50 hover:text-white'
                  }`}
                >
                  {label}
                  {count > 0 && (
                    <span className={`px-1.5 py-0.5 rounded-full text-xs ${
                      highlight && filter !== key ? 'bg-red-500 text-white animate-pulse' : 'bg-gray-600 text-gray-300'
                    }`}>
                      {count}
                    </span>
                  )}
                </button>
              ))}
            </div>

            {/* Notifications list */}
            <div className="max-h-[450px] overflow-y-auto">
              {filteredNotifications.length === 0 ? (
                <div className="px-4 py-12 text-center text-gray-500">
                  <span className="text-4xl block mb-3">{'🔕'}</span>
                  <div className="font-medium">Aucune notification</div>
                  <div className="text-xs mt-1">Les alertes apparaitront ici</div>
                </div>
              ) : (
                <div className="divide-y divide-gray-700/50">
                  {filteredNotifications.map((notif, index) => {
                    const config = NOTIFICATION_CONFIG[notif.type];
                    const styles = PRIORITY_STYLES[notif.priority];

                    return (
                      <div
                        key={notif.id}
                        className={`px-4 py-3 border-l-4 cursor-pointer transition-all hover:bg-gray-700/30 ${
                          styles.border
                        } ${styles.bg} ${notif.read ? 'opacity-60' : ''}`}
                        onClick={() => markAsRead(notif.id)}
                        style={{
                          animation: `fadeInLeft 0.3s ease-out ${index * 50}ms both`,
                        }}
                      >
                        <div className="flex items-start gap-3">
                          {/* Icon with priority badge */}
                          <div className="relative flex-shrink-0">
                            <div className={`w-10 h-10 rounded-full flex items-center justify-center ${styles.badge} ${styles.glow} shadow-lg`}>
                              <span className="text-lg">{config?.icon || '📢'}</span>
                            </div>
                            {config?.animate && !notif.read && (
                              <span className="absolute -inset-1 rounded-full border-2 border-current animate-ping opacity-30" />
                            )}
                          </div>

                          {/* Content */}
                          <div className="flex-1 min-w-0">
                            <div className="flex items-start justify-between gap-2">
                              <div className="flex items-center gap-2">
                                <span className={`font-medium text-sm ${notif.read ? 'text-gray-400' : 'text-white'}`}>
                                  {notif.title}
                                </span>
                                {!notif.read && (
                                  <span className="w-2 h-2 rounded-full bg-amber-500 animate-pulse" />
                                )}
                              </div>
                            </div>

                            <p className="text-xs text-gray-400 mt-1 line-clamp-2">
                              {notif.message}
                            </p>

                            {/* Meta info */}
                            <div className="flex items-center gap-3 mt-2">
                              <span className="text-xs text-gray-500 flex items-center gap-1">
                                {'🕐'} {formatTime(notif.timestamp)}
                              </span>

                              <span className={`text-[10px] px-1.5 py-0.5 rounded ${styles.badge} text-white font-medium`}>
                                {getPriorityLabel(notif.priority)}
                              </span>

                              {notif.countries && notif.countries.length > 0 && (
                                <div className="flex items-center gap-1">
                                  {notif.countries.slice(0, 4).map(c => (
                                    <span key={c} className="text-sm" title={c}>
                                      {COUNTRY_FLAGS[c] || c}
                                    </span>
                                  ))}
                                  {notif.countries.length > 4 && (
                                    <span className="text-xs text-gray-500">+{notif.countries.length - 4}</span>
                                  )}
                                </div>
                              )}

                              {notif.zoneName && (
                                <span className="text-xs text-gray-500">
                                  {'📍'} {notif.zoneName}
                                </span>
                              )}
                            </div>

                            {/* Strategic implications */}
                            {notif.details?.strategicImplications && notif.details.strategicImplications.length > 0 && (
                              <div className="mt-2 flex flex-wrap gap-1">
                                {notif.details.strategicImplications.map((imp, i) => (
                                  <span key={i} className="text-[10px] px-1.5 py-0.5 bg-gray-700 rounded text-gray-400">
                                    {imp}
                                  </span>
                                ))}
                              </div>
                            )}
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>

            {/* Footer stats */}
            {notifications.length > 0 && (
              <div className="px-4 py-2.5 bg-gray-750 border-t border-gray-700 flex items-center justify-between text-xs text-gray-500">
                <span>{filteredNotifications.length} notification{filteredNotifications.length > 1 ? 's' : ''}</span>
                <div className="flex items-center gap-3">
                  {criticalCount > 0 && (
                    <span className="flex items-center gap-1 text-red-400">
                      {'⚠️'} {criticalCount} urgente{criticalCount > 1 ? 's' : ''}
                    </span>
                  )}
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Toast notifications for critical alerts */}
      <div className="fixed bottom-6 right-6 z-[100] space-y-3 pointer-events-none">
        {toasts.map((toast, index) => {
          const config = NOTIFICATION_CONFIG[toast.type];
          const styles = PRIORITY_STYLES[toast.priority];

          return (
            <div
              key={toast.id}
              className={`pointer-events-auto max-w-md ${styles.bg} ${styles.border} border-2 rounded-xl p-4 shadow-2xl ${styles.glow} backdrop-blur-sm`}
              style={{
                animation: `slideInRight 0.4s ease-out ${index * 100}ms both`,
              }}
            >
              <div className="flex items-start gap-3">
                {/* Animated icon */}
                <div className={`w-12 h-12 rounded-full flex items-center justify-center ${styles.badge} shadow-lg relative`}>
                  <span className="text-2xl">{config?.icon || '⚠️'}</span>
                  {config?.animate && (
                    <span className="absolute inset-0 rounded-full border-2 border-white/50 animate-ping" />
                  )}
                </div>

                {/* Content */}
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-1">
                    <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${styles.badge} text-white`}>
                      {getPriorityLabel(toast.priority)}
                    </span>
                    {toast.zoneName && (
                      <span className="text-xs text-gray-400">{'📍'} {toast.zoneName}</span>
                    )}
                  </div>

                  <div className="font-bold text-white">{toast.title}</div>
                  <p className="text-sm text-gray-300 mt-1">{toast.message}</p>

                  {toast.countries && toast.countries.length > 0 && (
                    <div className="flex items-center gap-2 mt-2">
                      {toast.countries.map(c => (
                        <span key={c} className="flex items-center gap-1 text-sm">
                          {COUNTRY_FLAGS[c]} <span className="text-xs text-gray-400">{c}</span>
                        </span>
                      ))}
                    </div>
                  )}
                </div>

                {/* Dismiss button */}
                <button
                  onClick={() => dismissToast(toast.id)}
                  className="text-gray-400 hover:text-white p-1 rounded-full hover:bg-gray-700/50 transition-colors"
                >
                  {'✕'}
                </button>
              </div>

              {/* Auto-dismiss progress bar */}
              <div className="mt-3 h-1 bg-gray-700 rounded-full overflow-hidden">
                <div
                  className={`h-full ${styles.badge} rounded-full`}
                  style={{
                    animation: 'shrink 8s linear forwards',
                    width: '100%',
                  }}
                />
              </div>
            </div>
          );
        })}
      </div>

    </>
  );
}
