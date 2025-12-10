'use client';

import { useState, useEffect, useCallback } from 'react';
import { COUNTRY_FLAGS, InfluenceZone, GameEvent } from '@/lib/types';

interface NotificationCenterProps {
  events: GameEvent[];
  zones: InfluenceZone[];
  previousZones?: InfluenceZone[];
}

interface Notification {
  id: string;
  type: 'domination_change' | 'new_contestation' | 'war' | 'peace' | 'crisis' | 'nuclear' | 'influence_shift';
  title: string;
  message: string;
  timestamp: number;
  priority: 'critical' | 'high' | 'medium' | 'low';
  zone?: string;
  countries?: string[];
  read: boolean;
}

const NOTIFICATION_ICONS: Record<string, string> = {
  domination_change: '&#127760;',
  new_contestation: '&#9876;',
  war: '&#128481;',
  peace: '&#128330;',
  crisis: '&#9888;',
  nuclear: '&#9762;',
  influence_shift: '&#128200;',
};

const PRIORITY_COLORS: Record<string, string> = {
  critical: 'border-red-500 bg-red-900/30',
  high: 'border-orange-500 bg-orange-900/30',
  medium: 'border-yellow-500 bg-yellow-900/30',
  low: 'border-blue-500 bg-blue-900/30',
};

const PRIORITY_BADGE_COLORS: Record<string, string> = {
  critical: 'bg-red-500',
  high: 'bg-orange-500',
  medium: 'bg-yellow-500',
  low: 'bg-blue-500',
};

export default function NotificationCenter({
  events,
  zones,
  previousZones,
}: NotificationCenterProps) {
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [expanded, setExpanded] = useState(false);
  const [filter, setFilter] = useState<'all' | 'critical' | 'unread'>('all');

  // Generate notifications from events
  useEffect(() => {
    const newNotifications: Notification[] = [];

    // Process recent events for war/peace/crisis notifications
    events.slice(0, 10).forEach((event, index) => {
      const notifId = `event-${event.id}`;

      // Skip if already processed
      if (notifications.some(n => n.id === notifId)) return;

      let type: Notification['type'] = 'influence_shift';
      let priority: Notification['priority'] = 'low';

      if (event.type === 'war') {
        type = 'war';
        priority = 'critical';
      } else if (event.type === 'peace') {
        type = 'peace';
        priority = 'high';
      } else if (event.type === 'crisis' || event.type === 'coup') {
        type = 'crisis';
        priority = 'high';
      } else if (event.type === 'nuclear') {
        type = 'nuclear';
        priority = 'critical';
      } else {
        // Skip non-important events
        if (index > 3) return;
        priority = 'medium';
      }

      newNotifications.push({
        id: notifId,
        type,
        title: event.title_fr,
        message: event.description_fr,
        timestamp: Date.now() - index * 60000,
        priority,
        read: false,
      });
    });

    // Detect zone domination changes
    if (previousZones && previousZones.length > 0) {
      zones.forEach(zone => {
        const prevZone = previousZones.find(z => z.id === zone.id);
        if (!prevZone) return;

        // Domination change
        if (prevZone.dominant_power !== zone.dominant_power) {
          const notifId = `dom-${zone.id}-${Date.now()}`;
          if (!notifications.some(n => n.id === notifId)) {
            newNotifications.push({
              id: notifId,
              type: 'domination_change',
              title: `Changement de domination: ${zone.name_fr}`,
              message: zone.dominant_power
                ? `${COUNTRY_FLAGS[zone.dominant_power]} ${zone.dominant_power} prend le controle de ${zone.name_fr}`
                : `${zone.name_fr} n'a plus de puissance dominante`,
              timestamp: Date.now(),
              priority: 'high',
              zone: zone.id,
              countries: zone.dominant_power ? [zone.dominant_power] : [],
              read: false,
            });
          }
        }

        // New contestation
        const newContesters = zone.contested_by.filter(
          c => !prevZone.contested_by.includes(c)
        );
        if (newContesters.length > 0) {
          const notifId = `contest-${zone.id}-${newContesters.join('-')}`;
          if (!notifications.some(n => n.id === notifId)) {
            newNotifications.push({
              id: notifId,
              type: 'new_contestation',
              title: `Nouvelle contestation: ${zone.name_fr}`,
              message: `${newContesters.map(c => `${COUNTRY_FLAGS[c]} ${c}`).join(', ')} conteste ${zone.name_fr}`,
              timestamp: Date.now(),
              priority: 'medium',
              zone: zone.id,
              countries: newContesters,
              read: false,
            });
          }
        }
      });
    }

    if (newNotifications.length > 0) {
      setNotifications(prev => [...newNotifications, ...prev].slice(0, 50));
    }
  }, [events, zones, previousZones]);

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

  // Clear all notifications
  const clearAll = useCallback(() => {
    setNotifications([]);
  }, []);

  // Filter notifications
  const filteredNotifications = notifications.filter(n => {
    if (filter === 'critical') return n.priority === 'critical' || n.priority === 'high';
    if (filter === 'unread') return !n.read;
    return true;
  });

  // Count unread
  const unreadCount = notifications.filter(n => !n.read).length;
  const criticalCount = notifications.filter(n => !n.read && (n.priority === 'critical' || n.priority === 'high')).length;

  // Format timestamp
  const formatTime = (timestamp: number) => {
    const diff = Date.now() - timestamp;
    if (diff < 60000) return 'A l\'instant';
    if (diff < 3600000) return `Il y a ${Math.floor(diff / 60000)} min`;
    if (diff < 86400000) return `Il y a ${Math.floor(diff / 3600000)} h`;
    return `Il y a ${Math.floor(diff / 86400000)} j`;
  };

  return (
    <div className="relative">
      {/* Notification bell button */}
      <button
        onClick={() => setExpanded(!expanded)}
        className={`relative p-2 rounded-lg transition-all ${
          expanded
            ? 'bg-amber-600 text-white'
            : 'bg-gray-700 text-gray-300 hover:bg-gray-600 hover:text-white'
        }`}
      >
        <span className="text-lg">&#128276;</span>

        {/* Unread badge */}
        {unreadCount > 0 && (
          <span className={`absolute -top-1 -right-1 min-w-5 h-5 flex items-center justify-center text-xs font-bold rounded-full ${
            criticalCount > 0 ? 'bg-red-500 animate-pulse' : 'bg-amber-500'
          }`}>
            {unreadCount > 99 ? '99+' : unreadCount}
          </span>
        )}
      </button>

      {/* Notification panel */}
      {expanded && (
        <div className="absolute right-0 top-12 w-96 bg-gray-800 rounded-lg shadow-2xl border border-gray-700 z-50 overflow-hidden animate-scaleIn">
          {/* Header */}
          <div className="px-4 py-3 bg-gradient-to-r from-amber-900/50 to-gray-700 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="text-lg">&#128276;</span>
              <span className="font-bold">Notifications</span>
              {unreadCount > 0 && (
                <span className="px-2 py-0.5 bg-amber-600 rounded-full text-xs">
                  {unreadCount} non lues
                </span>
              )}
            </div>
            <div className="flex gap-1">
              <button
                onClick={markAllAsRead}
                className="px-2 py-1 text-xs bg-gray-700 hover:bg-gray-600 rounded transition-colors"
                title="Tout marquer comme lu"
              >
                &#10003;
              </button>
              <button
                onClick={clearAll}
                className="px-2 py-1 text-xs bg-gray-700 hover:bg-gray-600 rounded transition-colors"
                title="Effacer tout"
              >
                &#128465;
              </button>
            </div>
          </div>

          {/* Filter tabs */}
          <div className="flex border-b border-gray-700">
            {([
              { key: 'all', label: 'Toutes' },
              { key: 'critical', label: 'Importantes' },
              { key: 'unread', label: 'Non lues' },
            ] as const).map(({ key, label }) => (
              <button
                key={key}
                onClick={() => setFilter(key)}
                className={`flex-1 px-3 py-2 text-xs font-medium transition-all ${
                  filter === key
                    ? 'bg-gray-700 text-white'
                    : 'text-gray-400 hover:bg-gray-750 hover:text-white'
                }`}
              >
                {label}
              </button>
            ))}
          </div>

          {/* Notifications list */}
          <div className="max-h-96 overflow-y-auto scrollbar-thin">
            {filteredNotifications.length === 0 ? (
              <div className="px-4 py-8 text-center text-gray-500">
                <span className="text-3xl block mb-2">&#128276;</span>
                Aucune notification
              </div>
            ) : (
              filteredNotifications.map((notif, index) => (
                <div
                  key={notif.id}
                  className={`px-4 py-3 border-l-4 border-b border-gray-700 last:border-b-0 cursor-pointer transition-all hover:bg-gray-700/50 ${
                    PRIORITY_COLORS[notif.priority]
                  } ${notif.read ? 'opacity-60' : ''}`}
                  onClick={() => markAsRead(notif.id)}
                  style={{ animationDelay: `${index * 30}ms` }}
                >
                  <div className="flex items-start gap-3">
                    {/* Icon */}
                    <div className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 ${PRIORITY_BADGE_COLORS[notif.priority]}`}>
                      <span
                        className="text-sm"
                        dangerouslySetInnerHTML={{ __html: NOTIFICATION_ICONS[notif.type] || '&#128196;' }}
                      />
                    </div>

                    {/* Content */}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-start justify-between gap-2">
                        <span className={`font-medium text-sm ${notif.read ? 'text-gray-400' : 'text-white'}`}>
                          {notif.title}
                        </span>
                        {!notif.read && (
                          <span className="w-2 h-2 rounded-full bg-amber-500 flex-shrink-0 mt-1.5" />
                        )}
                      </div>
                      <p className="text-xs text-gray-400 mt-0.5 line-clamp-2">
                        {notif.message}
                      </p>
                      <div className="flex items-center gap-2 mt-1.5">
                        <span className="text-xs text-gray-500">
                          {formatTime(notif.timestamp)}
                        </span>
                        {notif.countries && notif.countries.length > 0 && (
                          <div className="flex gap-0.5">
                            {notif.countries.slice(0, 3).map(c => (
                              <span key={c} className="text-sm">{COUNTRY_FLAGS[c]}</span>
                            ))}
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>

          {/* Footer */}
          {filteredNotifications.length > 0 && (
            <div className="px-4 py-2 bg-gray-750 border-t border-gray-700 text-xs text-gray-500 text-center">
              {filteredNotifications.length} notification{filteredNotifications.length > 1 ? 's' : ''}
            </div>
          )}
        </div>
      )}

      {/* Toast notifications for critical alerts */}
      <div className="fixed bottom-4 right-4 z-50 space-y-2">
        {notifications
          .filter(n => !n.read && n.priority === 'critical')
          .slice(0, 3)
          .map((notif, index) => (
            <div
              key={notif.id}
              className="bg-red-900 border border-red-700 rounded-lg p-3 shadow-xl max-w-sm animate-slideInLeft"
              style={{ animationDelay: `${index * 100}ms` }}
            >
              <div className="flex items-start gap-2">
                <span
                  className="text-lg"
                  dangerouslySetInnerHTML={{ __html: NOTIFICATION_ICONS[notif.type] || '&#9888;' }}
                />
                <div className="flex-1">
                  <div className="font-medium text-sm">{notif.title}</div>
                  <p className="text-xs text-gray-300 mt-0.5">{notif.message}</p>
                </div>
                <button
                  onClick={() => markAsRead(notif.id)}
                  className="text-gray-400 hover:text-white"
                >
                  &#10005;
                </button>
              </div>
            </div>
          ))}
      </div>
    </div>
  );
}
