'use client';

import React, { useState, useEffect } from 'react';
import { AlertEvent } from '@/types/api';
import { fetchAlerts, markAlertRead, markAllAlertsRead } from '@/lib/api';
import { Bell, CheckCheck, Flame, TrendingDown, Star, RefreshCw, Sparkles } from 'lucide-react';

interface AlertsViewProps {
  onSelectOffer?: (offerId: string) => void;
}

export const AlertsView: React.FC<AlertsViewProps> = ({ onSelectOffer }) => {
  const [alerts, setAlerts] = useState<AlertEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [unreadOnly, setUnreadOnly] = useState(false);

  const loadAlerts = async () => {
    try {
      setLoading(true);
      const res = await fetchAlerts(unreadOnly);
      setAlerts(res.alerts);
    } catch (err) {
      console.error('Failed to load alerts:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAlerts();
  }, [unreadOnly]);

  const handleMarkRead = async (id: string) => {
    try {
      await markAlertRead(id);
      loadAlerts();
    } catch (err) {
      console.error('Error marking read:', err);
    }
  };

  const handleMarkAllRead = async () => {
    try {
      await markAllAlertsRead();
      loadAlerts();
    } catch (err) {
      console.error('Error marking all read:', err);
    }
  };

  const getAlertBadge = (type: string) => {
    switch (type) {
      case 'price_drop':
        return {
          icon: TrendingDown,
          bg: 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30',
          label: 'Spadek Ceny',
        };
      case 'high_score':
        return {
          icon: Flame,
          bg: 'bg-amber-500/20 text-amber-400 border-amber-500/30',
          label: 'High Score',
        };
      case 'lowest_price':
        return {
          icon: Star,
          bg: 'bg-purple-500/20 text-purple-400 border-purple-500/30',
          label: 'Najniższa Cena',
        };
      case 'reappeared':
        return {
          icon: RefreshCw,
          bg: 'bg-blue-500/20 text-blue-400 border-blue-500/30',
          label: 'Oferta Powróciła',
        };
      default:
        return {
          icon: Sparkles,
          bg: 'bg-indigo-500/20 text-indigo-400 border-indigo-500/30',
          label: 'Dopasowanie Profilu',
        };
    }
  };

  return (
    <div className="space-y-6">
      {/* Header & Controls */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 p-6 rounded-2xl bg-slate-900/60 border border-slate-800 backdrop-blur-md">
        <div>
          <h2 className="text-xl font-bold text-white flex items-center gap-2">
            <Bell className="w-5 h-5 text-indigo-400" />
            Smart Alerts (Powiadomienia Systemowe)
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Historia powiadomień i wyjątkowych zdarzeń wykrytych przez silnik analityczny HolidaysHunter.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <label className="flex items-center gap-2 text-xs text-slate-300 cursor-pointer">
            <input
              type="checkbox"
              checked={unreadOnly}
              onChange={(e) => setUnreadOnly(e.target.checked)}
              className="rounded bg-slate-800 border-slate-700 text-indigo-600 focus:ring-0"
            />
            <span>Tylko nieprzeczytane</span>
          </label>

          <button
            onClick={handleMarkAllRead}
            className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 font-semibold text-xs border border-slate-700 transition-colors"
          >
            <CheckCheck className="w-4 h-4 text-emerald-400" />
            <span>Oznacz wszystkie jako przeczytane</span>
          </button>
        </div>
      </div>

      {/* Alerts List */}
      {loading ? (
        <div className="p-8 text-center text-slate-400 animate-pulse text-sm">
          Ładowanie powiadomień...
        </div>
      ) : alerts.length === 0 ? (
        <div className="p-12 text-center rounded-2xl bg-slate-900/40 border border-slate-800 space-y-3">
          <Bell className="w-12 h-12 text-slate-600 mx-auto stroke-[1.5]" />
          <h3 className="text-base font-semibold text-slate-300">Brak powiadomień</h3>
          <p className="text-xs text-slate-500">
            Wszystkie powiadomienia zostały przeczytane lub nie odnotowano nowych alertów.
          </p>
        </div>
      ) : (
        <div className="space-y-3">
          {alerts.map((alert) => {
            const badge = getAlertBadge(alert.alert_type);
            const Icon = badge.icon;
            const timeStr = new Date(alert.triggered_at).toLocaleString('pl-PL', {
              day: 'numeric',
              month: 'short',
              hour: '2-digit',
              minute: '2-digit',
            });

            return (
              <div
                key={alert.id}
                className={`p-5 rounded-2xl border transition-all flex flex-col md:flex-row md:items-center justify-between gap-4 ${
                  alert.is_read
                    ? 'bg-slate-900/40 border-slate-800/80 opacity-80'
                    : 'bg-slate-900/90 border-slate-700/80 shadow-lg shadow-indigo-500/5'
                }`}
              >
                <div className="flex items-start gap-3.5 flex-1">
                  <div className={`p-2.5 rounded-xl border shrink-0 ${badge.bg}`}>
                    <Icon className="w-5 h-5" />
                  </div>

                  <div className="space-y-1.5">
                    <div className="flex items-center gap-2">
                      <span className={`px-2 py-0.5 rounded text-[10px] uppercase font-bold border ${badge.bg}`}>
                        {badge.label}
                      </span>
                      <span className="text-xs text-slate-500">{timeStr}</span>
                    </div>

                    <p className="text-sm font-semibold text-slate-100">{alert.message}</p>
                  </div>
                </div>

                {/* Actions (Open Offer Modal / External Link / Mark Read) */}
                <div className="flex items-center gap-2 shrink-0 flex-wrap md:flex-nowrap pt-2 md:pt-0 border-t md:border-t-0 border-slate-800">
                  {alert.offer_id && onSelectOffer && (
                    <button
                      onClick={() => onSelectOffer(alert.offer_id)}
                      className="px-3.5 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-bold shadow-md shadow-indigo-600/20 transition-all"
                    >
                      👁️ Zobacz ofertę
                    </button>
                  )}

                  {!alert.is_read && (
                    <button
                      onClick={() => handleMarkRead(alert.id)}
                      className="px-3 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold border border-slate-700 transition-colors"
                    >
                      Przeczytane
                    </button>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
