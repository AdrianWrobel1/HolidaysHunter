'use client';

import React, { useState, useEffect } from 'react';
import { fetchSeasonalTrends, fetchFilterOptions } from '@/lib/api';
import { FilterOptionsResponse } from '@/types/api';
import { Calendar, TrendingUp, Sun, Snowflake, CloudRain, Sparkles, MapPin, DollarSign } from 'lucide-react';

interface TrendItem {
  country: string;
  region: string;
  month: number;
  month_name: string;
  season: string;
  avg_price: number;
  min_price: number;
  max_price: number;
  offer_count: number;
}

export const SeasonalAnalyticsView: React.FC = () => {
  const [trends, setTrends] = useState<TrendItem[]>([]);
  const [filters, setFilters] = useState<FilterOptionsResponse | null>(null);
  const [selectedCountry, setSelectedCountry] = useState<string>('');
  const [selectedRegion, setSelectedRegion] = useState<string>('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchFilterOptions()
      .then((f) => {
        setFilters(f);
        if (f.countries && f.countries.length > 0) {
          setSelectedCountry(f.countries[0]);
        }
      })
      .catch((err) => console.warn('Failed to load countries:', err));
  }, []);

  useEffect(() => {
    setLoading(true);
    fetchSeasonalTrends(selectedCountry || undefined, selectedRegion || undefined)
      .then(setTrends)
      .catch((err) => console.error('Failed to load seasonal trends:', err))
      .finally(() => setLoading(false));
  }, [selectedCountry, selectedRegion]);

  // Compute stats
  const minTrend = trends.length > 0
    ? [...trends].sort((a, b) => a.min_price - b.min_price)[0]
    : null;

  const maxTrend = trends.length > 0
    ? [...trends].sort((a, b) => b.avg_price - a.avg_price)[0]
    : null;

  const maxPriceGlobal = Math.max(...trends.map((t) => t.max_price), 5000);

  return (
    <div className="space-y-6 animate-fadeIn">
      {/* Header Banner */}
      <div className="relative overflow-hidden rounded-3xl bg-gradient-to-r from-purple-950 via-slate-900 to-indigo-950 border border-slate-800 p-8 shadow-2xl">
        <div className="absolute top-0 right-0 w-96 h-96 bg-purple-500/10 rounded-full blur-3xl pointer-events-none" />
        <div className="relative z-10 space-y-3">
          <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-purple-500/20 text-purple-300 border border-purple-500/30">
            <TrendingUp className="w-3.5 h-3.5" />
            <span>Sezonowość Cen i Trendów Wakacyjnych</span>
          </div>
          <h2 className="text-3xl sm:text-4xl font-black text-white tracking-tight">
            Analiza Sezonowa Cen (Seasonal Price Analytics)
          </h2>
          <p className="text-sm text-slate-300 max-w-2xl leading-relaxed">
            Sprawdź, jak ceny wycieczek zmieniają się w poszczególnych miesiącach i porach roku w zależności od kraju i regionu (np. Barcelona, Costa Brava, Majorka).
          </p>
        </div>
      </div>

      {/* Country & Region Selectors */}
      <div className="flex flex-col md:flex-row items-center justify-between gap-4 p-6 rounded-2xl bg-slate-900/60 border border-slate-800 backdrop-blur-md">
        <div className="flex flex-wrap items-center gap-4 w-full md:w-auto">
          <div className="flex items-center gap-2">
            <MapPin className="w-5 h-5 text-indigo-400 shrink-0" />
            <label className="text-xs font-semibold text-slate-200 shrink-0">Kraj:</label>
            <select
              value={selectedCountry}
              onChange={(e) => {
                setSelectedCountry(e.target.value);
                setSelectedRegion('');
              }}
              className="bg-slate-800 border border-slate-700 text-xs text-white px-3 py-2 rounded-xl focus:border-indigo-500 cursor-pointer font-semibold"
            >
              <option value="">Wszystkie kraje</option>
              {filters?.countries.map((c) => (
                <option key={c} value={c}>
                  {c}
                </option>
              ))}
            </select>
          </div>

          <div className="flex items-center gap-2">
            <label className="text-xs font-semibold text-slate-200 shrink-0">Region / Miasto:</label>
            <select
              value={selectedRegion}
              onChange={(e) => setSelectedRegion(e.target.value)}
              className="bg-slate-800 border border-slate-700 text-xs text-white px-3 py-2 rounded-xl focus:border-indigo-500 cursor-pointer font-semibold"
            >
              <option value="">Wszystkie regiony</option>
              {filters?.regions.map((r) => (
                <option key={r} value={r}>
                  {r}
                </option>
              ))}
            </select>
          </div>
        </div>

        <div className="text-xs text-slate-400">
          Kraj: <strong className="text-indigo-400">{selectedCountry || 'Wszystkie'}</strong>
          {selectedRegion && <> • Region: <strong className="text-purple-400">{selectedRegion}</strong></>}
        </div>
      </div>

      {/* Key Metric Summary Cards */}
      {minTrend && maxTrend && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {/* Best Price Month */}
          <div className="p-5 rounded-2xl bg-slate-900/80 border border-emerald-500/30 backdrop-blur-md space-y-2">
            <div className="flex items-center justify-between text-xs text-emerald-400 font-bold uppercase tracking-wider">
              <span>Najtańszy Miesiąc</span>
              <Sparkles className="w-4 h-4 text-emerald-400" />
            </div>
            <div className="text-2xl font-black text-white">{minTrend.month_name} ({minTrend.season})</div>
            <div className="text-xs text-slate-300">
              Minimalna cena od <strong className="text-emerald-400">{minTrend.min_price.toFixed(0)} PLN/os.</strong> (śr. {minTrend.avg_price.toFixed(0)} PLN)
            </div>
          </div>

          {/* Peak Season Month */}
          <div className="p-5 rounded-2xl bg-slate-900/80 border border-amber-500/30 backdrop-blur-md space-y-2">
            <div className="flex items-center justify-between text-xs text-amber-400 font-bold uppercase tracking-wider">
              <span>Szczyt Sezonu (Najdroższy)</span>
              <Sun className="w-4 h-4 text-amber-400" />
            </div>
            <div className="text-2xl font-black text-white">{maxTrend.month_name} ({maxTrend.season})</div>
            <div className="text-xs text-slate-300">
              Średnia cena sięga <strong className="text-amber-400">{maxTrend.avg_price.toFixed(0)} PLN/os.</strong>
            </div>
          </div>

          {/* Total Offers Analyzed */}
          <div className="p-5 rounded-2xl bg-slate-900/80 border border-indigo-500/30 backdrop-blur-md space-y-2">
            <div className="flex items-center justify-between text-xs text-indigo-400 font-bold uppercase tracking-wider">
              <span>Baza Danych Trendów</span>
              <Calendar className="w-4 h-4 text-indigo-400" />
            </div>
            <div className="text-2xl font-black text-white">
              {trends.reduce((acc, t) => acc + t.offer_count, 0)} ofert
            </div>
            <div className="text-xs text-slate-300">
              Przeanalizowano dla 12 miesięcy roku
            </div>
          </div>
        </div>
      )}

      {/* Monthly Breakdown List */}
      {loading ? (
        <div className="p-12 text-center text-slate-400 animate-pulse text-sm">
          Ładowanie analizy sezonowej cen...
        </div>
      ) : trends.length === 0 ? (
        <div className="p-12 text-center rounded-2xl bg-slate-900/40 border border-slate-800 space-y-3">
          <Calendar className="w-12 h-12 text-slate-600 mx-auto" />
          <h3 className="text-base font-semibold text-slate-300">Brak danych sezonowych</h3>
          <p className="text-xs text-slate-500">
            Zmień wybrany kraj lub pobierz świeże oferty przyciskiem w wyszukiwarce.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {trends.map((t) => {
            const barWidthPct = Math.min(100, Math.max(15, (t.avg_price / maxPriceGlobal) * 100));

            return (
              <div
                key={`${t.country}-${t.month}`}
                className="p-5 rounded-2xl bg-slate-900/90 border border-slate-800 hover:border-slate-700 transition-all space-y-4 shadow-lg"
              >
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="text-lg font-bold text-white flex items-center gap-2">
                      <span>{t.month_name}</span>
                    </h3>
                    <span className="text-xs text-slate-400">{t.country} {t.region ? `• ${t.region}` : ''} ({t.offer_count} ofert)</span>
                  </div>
                  <span className="px-2.5 py-1 rounded-full text-xs font-bold bg-slate-800 border border-slate-700 text-indigo-300">
                    {t.season}
                  </span>
                </div>

                {/* Price Range Bar */}
                <div className="space-y-1.5">
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-slate-400">Średnia cena:</span>
                    <span className="font-bold text-white text-sm">{t.avg_price.toFixed(0)} PLN / os.</span>
                  </div>

                  <div className="w-full h-3 rounded-full bg-slate-800 overflow-hidden p-0.5 border border-slate-700/50">
                    <div
                      className="h-full rounded-full bg-gradient-to-r from-indigo-500 via-purple-500 to-amber-500 transition-all duration-500"
                      style={{ width: `${barWidthPct}%` }}
                    />
                  </div>

                  <div className="flex items-center justify-between text-[11px] text-slate-400 pt-1">
                    <span>Min: <strong className="text-emerald-400">{t.min_price.toFixed(0)} PLN</strong></span>
                    <span>Max: <strong className="text-rose-400">{t.max_price.toFixed(0)} PLN</strong></span>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
