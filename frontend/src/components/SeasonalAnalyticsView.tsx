'use client';

import React, { useState, useEffect } from 'react';
import {
  fetchSeasonalAnalytics,
  fetchFilterOptions,
  fetchLiveOffers,
  createSeasonalWorkspaceSession,
} from '@/lib/api';
import {
  FilterOptionsResponse,
  OfferQueryParams,
  SeasonalAnalyticsResponse,
  SeasonalQueryParams,
} from '@/types/api';
import {
  TrendingUp,
  Calendar,
  Sparkles,
  Filter,
  DollarSign,
  Award,
  Zap,
  ArrowDownRight,
  ArrowUpRight,
  ChevronDown,
  ChevronUp,
  RotateCcw,
  Plane,
  Car,
  Layers,
  MapPin,
  Building2,
  FolderKanban,
  CheckCircle2,
  AlertTriangle,
  Info,
  Clock,
  Compass,
  LineChart,
  BarChart3,
  TrendingDown,
} from 'lucide-react';

interface SeasonalAnalyticsViewProps {
  onNavigateExplorer?: (params: OfferQueryParams) => void;
  onNavigateWorkspace?: () => void;
}

export const SeasonalAnalyticsView: React.FC<SeasonalAnalyticsViewProps> = ({
  onNavigateExplorer,
  onNavigateWorkspace,
}) => {
  const [data, setData] = useState<SeasonalAnalyticsResponse | null>(null);
  const [filterOptions, setFilterOptions] = useState<FilterOptionsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [workspaceMessage, setWorkspaceMessage] = useState<string | null>(null);
  const [creatingWorkspace, setCreatingWorkspace] = useState(false);
  const [fetchingLive, setFetchingLive] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Filter Panel State
  const [filterPanelOpen, setFilterPanelOpen] = useState(true);
  const [params, setParams] = useState<SeasonalQueryParams>({
    country: undefined,
    region: undefined,
    departure_month: undefined,
    travel_length: 'Any',
    transport_type: undefined,
    meal_type: undefined,
    hotel_stars_min: undefined,
    provider: undefined,
    price_min: undefined,
    price_max: undefined,
    deal_score_min: undefined,
    is_last_minute: undefined,
    is_first_minute: undefined,
  });

  // Price Trend Chart Metric State
  const [selectedMetric, setSelectedMetric] = useState<
    'avg' | 'median' | 'min' | 'max' | 'p10' | 'p25' | 'p75' | 'p90'
  >('avg');

  // Load Filter Options
  useEffect(() => {
    fetchFilterOptions()
      .then(setFilterOptions)
      .catch((err) => console.warn('Could not load filter options:', err));
  }, []);

  // Load Analytics Data when Params Change
  useEffect(() => {
    loadAnalytics();
  }, [params]);

  const loadAnalytics = async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await fetchSeasonalAnalytics(params);
      setData(res);
    } catch (err: any) {
      console.error('Error fetching seasonal analytics:', err);
      setError('Nie udało się załadować analizy sezonowej.');
    } finally {
      setLoading(false);
    }
  };

  const handleResetFilters = () => {
    setParams({
      country: undefined,
      region: undefined,
      departure_month: undefined,
      travel_length: 'Any',
      transport_type: undefined,
      meal_type: undefined,
      hotel_stars_min: undefined,
      provider: undefined,
      price_min: undefined,
      price_max: undefined,
      deal_score_min: undefined,
      is_last_minute: undefined,
      is_first_minute: undefined,
    });
    setWorkspaceMessage(null);
  };

  const handleCreateWorkspaceSession = async () => {
    try {
      setCreatingWorkspace(true);
      setWorkspaceMessage(null);
      const res = await createSeasonalWorkspaceSession(params);
      setWorkspaceMessage(res.message);
      if (onNavigateWorkspace) {
        setTimeout(() => {
          onNavigateWorkspace();
        }, 1200);
      }
    } catch (err: any) {
      console.error('Failed to create workspace session:', err);
      setError('Błąd podczas tworzenia sesji w Research Workspace.');
    } finally {
      setCreatingWorkspace(false);
    }
  };

  const handleFetchLiveForSeasonal = async () => {
    try {
      setFetchingLive(true);
      await fetchLiveOffers(params as OfferQueryParams);
      await loadAnalytics();
    } catch (err) {
      console.error('Failed to fetch live offers:', err);
    } finally {
      setFetchingLive(false);
    }
  };

  const handleNavigateExplorerWithParams = (overrideParams: Partial<OfferQueryParams> = {}) => {
    if (!onNavigateExplorer) return;
    const finalParams: OfferQueryParams = {
      country: params.country,
      region: params.region,
      transport_type: typeof params.transport_type === 'string' ? params.transport_type : undefined,
      provider: params.provider,
      meal_type: params.meal_type,
      price_max: params.price_max,
      sort_by: 'price_per_person',
      sort_order: 'asc',
      ...overrideParams,
    };
    onNavigateExplorer(finalParams);
  };

  // Compute Heatmap Range
  const maxHeatmapPrice = data && data.monthly_heatmap.length > 0
    ? Math.max(...data.monthly_heatmap.map((h) => h.avg_price), 5000)
    : 5000;

  return (
    <div className="space-y-8 animate-fadeIn pb-24">
      {/* Hero Header */}
      <div className="relative overflow-hidden rounded-3xl bg-gradient-to-r from-purple-950 via-slate-900 to-indigo-950 border border-slate-800 p-8 shadow-2xl">
        <div className="absolute top-0 right-0 w-96 h-96 bg-purple-500/10 rounded-full blur-3xl pointer-events-none" />
        <div className="relative z-10 flex flex-col lg:flex-row lg:items-center justify-between gap-6">
          <div className="space-y-3 max-w-2xl">
            <div className="inline-flex items-center gap-1.5 px-3.5 py-1 rounded-full text-xs font-bold bg-purple-500/20 text-purple-300 border border-purple-500/30">
              <TrendingUp className="w-4 h-4 text-purple-400" />
              <span>Seasonal Price Analytics V2 — Decision Support Dashboard</span>
            </div>
            <h2 className="text-3xl sm:text-4xl font-black text-white tracking-tight">
              Analiza Sezonowa i Prognoza Cenowa
            </h2>
            <p className="text-sm text-slate-300 leading-relaxed">
              Podejmuj decyzje na podstawie danych rynkowych: sprawdzaj najtańsze miesiące wyjazdu i zakupu, wskaźniki sezonowości, rozkład cen oraz izolowaną analizę przelotów i dojazdu własnego.
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-3 shrink-0">
            <button
              onClick={handleCreateWorkspaceSession}
              disabled={creatingWorkspace}
              className="px-5 py-3 rounded-2xl bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-500 hover:to-indigo-500 text-white text-xs font-bold shadow-lg shadow-purple-600/30 flex items-center gap-2 transition-all hover:scale-105"
            >
              <FolderKanban className="w-4 h-4 text-amber-300" />
              <span>{creatingWorkspace ? 'Tworzenie sesji...' : 'Przeanalizuj w Research Workspace ("Analyze this season")'}</span>
            </button>
          </div>
        </div>

        {workspaceMessage && (
          <div className="mt-4 p-3 rounded-2xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 text-xs flex items-center gap-2 animate-fadeIn">
            <CheckCircle2 className="w-4 h-4 shrink-0 text-emerald-400" />
            <span>{workspaceMessage}</span>
          </div>
        )}
      </div>

      {/* 1. Filter Panel (Collapsible Drawer) */}
      <div className="rounded-3xl bg-slate-900/90 border border-slate-800 backdrop-blur-xl shadow-xl overflow-hidden">
        <div
          onClick={() => setFilterPanelOpen(!filterPanelOpen)}
          className="p-6 flex items-center justify-between cursor-pointer hover:bg-slate-800/30 transition-colors"
        >
          <div className="flex items-center gap-3">
            <Filter className="w-5 h-5 text-indigo-400" />
            <h3 className="text-base font-bold text-white">Zaawansowany Panel Filtrów Sezonowych</h3>
            {data && (
              <span className="px-3 py-1 rounded-full text-xs font-extrabold bg-indigo-500/10 border border-indigo-500/30 text-indigo-300">
                {data.total_offers_analyzed} ofert w analizie
              </span>
            )}
          </div>

          <div className="flex items-center gap-3 text-xs text-slate-400 font-bold">
            <button
              onClick={(e) => {
                e.stopPropagation();
                handleResetFilters();
              }}
              className="px-3 py-1 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 flex items-center gap-1.5 transition-colors"
            >
              <RotateCcw className="w-3.5 h-3.5" />
              <span>Resetuj</span>
            </button>
            {filterPanelOpen ? <ChevronUp className="w-5 h-5" /> : <ChevronDown className="w-5 h-5" />}
          </div>
        </div>

        {filterPanelOpen && (
          <div className="p-6 pt-0 border-t border-slate-800/60 space-y-6">
            {/* Quick Toggle Flags Row */}
            <div className="space-y-2 pt-4">
              <span className="text-[10px] font-extrabold uppercase tracking-wider text-slate-400">
                Szybkie Tagi & Typy Ofert:
              </span>
              <div className="flex flex-wrap items-center gap-2">
                <button
                  onClick={() => setParams({ ...params, meal_type: params.meal_type === 'all_inclusive' ? undefined : 'all_inclusive' })}
                  className={`px-3 py-1.5 rounded-xl border text-xs font-bold transition-all ${
                    params.meal_type === 'all_inclusive'
                      ? 'bg-purple-600 border-purple-500 text-white shadow-md'
                      : 'bg-slate-800/40 border-slate-700/60 text-slate-400 hover:text-white'
                  }`}
                >
                  All Inclusive (AI)
                </button>

                <button
                  onClick={() => setParams({ ...params, meal_type: params.meal_type === 'half_board' ? undefined : 'half_board' })}
                  className={`px-3 py-1.5 rounded-xl border text-xs font-bold transition-all ${
                    params.meal_type === 'half_board'
                      ? 'bg-purple-600 border-purple-500 text-white shadow-md'
                      : 'bg-slate-800/40 border-slate-700/60 text-slate-400 hover:text-white'
                  }`}
                >
                  Half Board (HB)
                </button>

                <button
                  onClick={() => setParams({ ...params, meal_type: params.meal_type === 'bed_and_breakfast' ? undefined : 'bed_and_breakfast' })}
                  className={`px-3 py-1.5 rounded-xl border text-xs font-bold transition-all ${
                    params.meal_type === 'bed_and_breakfast'
                      ? 'bg-purple-600 border-purple-500 text-white shadow-md'
                      : 'bg-slate-800/40 border-slate-700/60 text-slate-400 hover:text-white'
                  }`}
                >
                  Bed & Breakfast (BB)
                </button>

                <button
                  onClick={() => setParams({ ...params, meal_type: params.meal_type === 'self_catering' ? undefined : 'self_catering' })}
                  className={`px-3 py-1.5 rounded-xl border text-xs font-bold transition-all ${
                    params.meal_type === 'self_catering'
                      ? 'bg-purple-600 border-purple-500 text-white shadow-md'
                      : 'bg-slate-800/40 border-slate-700/60 text-slate-400 hover:text-white'
                  }`}
                >
                  Self Catering
                </button>

                <span className="h-4 w-px bg-slate-800 mx-1" />

                <button
                  onClick={() => setParams({ ...params, transport_type: params.transport_type === 'flight' ? undefined : 'flight' })}
                  className={`px-3 py-1.5 rounded-xl border text-xs font-bold flex items-center gap-1.5 transition-all ${
                    params.transport_type === 'flight'
                      ? 'bg-indigo-600 border-indigo-500 text-white shadow-md'
                      : 'bg-slate-800/40 border-slate-700/60 text-slate-400 hover:text-white'
                  }`}
                >
                  <Plane className="w-3.5 h-3.5" />
                  <span>Only Flight</span>
                </button>

                <button
                  onClick={() => setParams({ ...params, transport_type: params.transport_type === 'self_transport' ? undefined : 'self_transport' })}
                  className={`px-3 py-1.5 rounded-xl border text-xs font-bold flex items-center gap-1.5 transition-all ${
                    params.transport_type === 'self_transport'
                      ? 'bg-emerald-600 border-emerald-500 text-white shadow-md'
                      : 'bg-slate-800/40 border-slate-700/60 text-slate-400 hover:text-white'
                  }`}
                >
                  <Car className="w-3.5 h-3.5" />
                  <span>Only Self Transport</span>
                </button>

                <span className="h-4 w-px bg-slate-800 mx-1" />

                <button
                  onClick={() => setParams({ ...params, is_last_minute: !params.is_last_minute, is_first_minute: false })}
                  className={`px-3 py-1.5 rounded-xl border text-xs font-bold transition-all ${
                    params.is_last_minute
                      ? 'bg-amber-500 border-amber-400 text-slate-950 font-black shadow-md'
                      : 'bg-slate-800/40 border-slate-700/60 text-slate-400 hover:text-white'
                  }`}
                >
                  🔥 Last Minute
                </button>

                <button
                  onClick={() => setParams({ ...params, is_first_minute: !params.is_first_minute, is_last_minute: false })}
                  className={`px-3 py-1.5 rounded-xl border text-xs font-bold transition-all ${
                    params.is_first_minute
                      ? 'bg-sky-500 border-sky-400 text-slate-950 font-black shadow-md'
                      : 'bg-slate-800/40 border-slate-700/60 text-slate-400 hover:text-white'
                  }`}
                >
                  ⭐ First Minute
                </button>
              </div>
            </div>

            {/* Form Fields Grid */}
            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4 text-xs font-semibold">
              {/* Country */}
              <div className="space-y-1.5">
                <label className="text-slate-400">Kraj Docelowy:</label>
                <select
                  value={typeof params.country === 'string' ? params.country : ''}
                  onChange={(e) => setParams({ ...params, country: e.target.value || undefined, region: undefined })}
                  className="w-full px-3 py-2.5 rounded-xl bg-slate-950 border border-slate-800 text-white focus:border-indigo-500 cursor-pointer"
                >
                  <option value="">Wszystkie Kraje</option>
                  {filterOptions?.countries.map((c) => (
                    <option key={c} value={c}>
                      {c}
                    </option>
                  ))}
                </select>
              </div>

              {/* Region */}
              <div className="space-y-1.5">
                <label className="text-slate-400">Region / Miasto:</label>
                <select
                  value={typeof params.region === 'string' ? params.region : ''}
                  onChange={(e) => setParams({ ...params, region: e.target.value || undefined })}
                  className="w-full px-3 py-2.5 rounded-xl bg-slate-950 border border-slate-800 text-white focus:border-indigo-500 cursor-pointer"
                >
                  <option value="">Wszystkie Regiony</option>
                  {(params.country && typeof params.country === 'string' && filterOptions?.country_regions?.[params.country]
                    ? filterOptions.country_regions[params.country]
                    : filterOptions?.regions || []
                  ).map((r) => (
                    <option key={r} value={r}>
                      {r}
                    </option>
                  ))}
                </select>
              </div>

              {/* Departure Month */}
              <div className="space-y-1.5">
                <label className="text-slate-400">Miesiąc Wyjazdu:</label>
                <select
                  value={Array.isArray(params.departure_month) ? params.departure_month[0] : (params.departure_month || '')}
                  onChange={(e) => setParams({ ...params, departure_month: e.target.value ? Number(e.target.value) : undefined })}
                  className="w-full px-3 py-2.5 rounded-xl bg-slate-950 border border-slate-800 text-white focus:border-indigo-500 cursor-pointer"
                >
                  <option value="">Wszystkie Miesiące (Cały Rok)</option>
                  <option value="1">Styczeń</option>
                  <option value="2">Luty</option>
                  <option value="3">Marzec</option>
                  <option value="4">Kwiecień</option>
                  <option value="5">Maj</option>
                  <option value="6">Czerwiec</option>
                  <option value="7">Lipiec</option>
                  <option value="8">Sierpień</option>
                  <option value="9">Wrzesień</option>
                  <option value="10">Październik</option>
                  <option value="11">Listopad</option>
                  <option value="12">Grudzień</option>
                </select>
              </div>

              {/* Duration Toggle */}
              <div className="space-y-1.5">
                <label className="text-slate-400">Długość Pobytu (Dni):</label>
                <div className="flex items-center gap-1">
                  {['7', '10', '14', 'Any'].map((len) => (
                    <button
                      key={len}
                      onClick={() => setParams({ ...params, travel_length: len })}
                      className={`flex-1 py-2 rounded-xl border text-xs font-bold transition-all ${
                        String(params.travel_length) === len
                          ? 'bg-indigo-600 border-indigo-500 text-white'
                          : 'bg-slate-950 border-slate-800 text-slate-400 hover:text-white'
                      }`}
                    >
                      {len === 'Any' ? 'Dowolna' : `${len}d`}
                    </button>
                  ))}
                </div>
              </div>

              {/* Provider */}
              <div className="space-y-1.5">
                <label className="text-slate-400">Biuro Podróży / Organizator:</label>
                <select
                  value={typeof params.provider === 'string' ? params.provider : ''}
                  onChange={(e) => setParams({ ...params, provider: e.target.value || undefined })}
                  className="w-full px-3 py-2.5 rounded-xl bg-slate-950 border border-slate-800 text-white focus:border-indigo-500 cursor-pointer"
                >
                  <option value="">Wzyscy Organizatorzy</option>
                  {filterOptions?.providers.map((p) => (
                    <option key={p} value={p}>
                      {p.toUpperCase()}
                    </option>
                  ))}
                </select>
              </div>

              {/* Departure Airport */}
              <div className="space-y-1.5">
                <label className="text-slate-400">Lotnisko Wylotu:</label>
                <select
                  value={typeof params.departure_city === 'string' ? params.departure_city : ''}
                  onChange={(e) => setParams({ ...params, departure_city: e.target.value || undefined })}
                  className="w-full px-3 py-2.5 rounded-xl bg-slate-950 border border-slate-800 text-white focus:border-indigo-500 cursor-pointer"
                >
                  <option value="">Wszystkie Lotniska</option>
                  {filterOptions?.departure_cities.map((c) => (
                    <option key={c} value={c}>
                      {c}
                    </option>
                  ))}
                </select>
              </div>

              {/* Hotel Stars Min */}
              <div className="space-y-1.5">
                <label className="text-slate-400">Standard Hotelu (Min. Gwiazdki):</label>
                <select
                  value={params.hotel_stars_min || ''}
                  onChange={(e) => setParams({ ...params, hotel_stars_min: e.target.value ? Number(e.target.value) : undefined })}
                  className="w-full px-3 py-2.5 rounded-xl bg-slate-950 border border-slate-800 text-white focus:border-indigo-500 cursor-pointer"
                >
                  <option value="">Wszystkie (1-5★)</option>
                  <option value="3">Min. 3★</option>
                  <option value="4">Min. 4★</option>
                  <option value="4.5">Min. 4.5★</option>
                  <option value="5">Tylko Luksusowe 5★</option>
                </select>
              </div>

              {/* Price Max */}
              <div className="space-y-1.5">
                <label className="text-slate-400">Maks. Budżet (PLN/os.):</label>
                <input
                  type="number"
                  placeholder="np. 4500"
                  value={params.price_max || ''}
                  onChange={(e) => setParams({ ...params, price_max: e.target.value ? Number(e.target.value) : undefined })}
                  className="w-full px-3 py-2.5 rounded-xl bg-slate-950 border border-slate-800 text-white placeholder-slate-500 focus:border-indigo-500"
                />
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Loading State */}
      {loading ? (
        <div className="p-16 text-center rounded-3xl bg-slate-900/60 border border-slate-800 space-y-4 animate-pulse">
          <div className="w-12 h-12 rounded-full border-4 border-indigo-500 border-t-transparent animate-spin mx-auto" />
          <p className="text-sm font-semibold text-slate-400">Przetwarzanie agregacji danych sezonowych w bazie SQL...</p>
        </div>
      ) : error ? (
        <div className="p-6 rounded-3xl bg-rose-500/10 border border-rose-500/30 text-rose-300 text-sm flex items-center gap-3">
          <AlertTriangle className="w-6 h-6 shrink-0 text-rose-400" />
          <span>{error}</span>
        </div>
      ) : data && !data.diagnostics.has_data ? (
        /* 16. Empty State Diagnostics */
        <div className="p-12 text-center rounded-3xl bg-slate-900/80 border border-amber-500/30 backdrop-blur-xl space-y-6">
          <div className="w-16 h-16 rounded-full bg-amber-500/10 border border-amber-500/30 flex items-center justify-center mx-auto">
            <Compass className="w-8 h-8 text-amber-400" />
          </div>

          <div className="space-y-2 max-w-lg mx-auto">
            <h3 className="text-xl font-black text-white">Brak danych dla zdefiniowanych filtrów</h3>
            <p className="text-xs text-slate-300 leading-relaxed">
              {data.diagnostics.reason || 'Żadna oferta z bazy danych nie spełnia zdefiniowanych kryteriów wyszukiwania.'}
            </p>
          </div>

          {data.diagnostics.conflicting_filters.length > 0 && (
            <div className="p-4 rounded-2xl bg-slate-950/80 border border-slate-800 max-w-md mx-auto space-y-2 text-left">
              <span className="text-[10px] font-bold text-amber-400 uppercase tracking-wider">
                Filtry wykluczające wyniki:
              </span>
              <ul className="text-xs text-slate-300 space-y-1 list-disc list-inside">
                {data.diagnostics.conflicting_filters.map((f) => (
                  <li key={f} className="capitalize">{f}</li>
                ))}
              </ul>
            </div>
          )}

          {data.diagnostics.suggested_countries.length > 0 && (
            <div className="space-y-2 pt-2">
              <span className="text-xs text-slate-400">Sugerowane popularne kierunki z dostępnymi ofertami:</span>
              <div className="flex flex-wrap items-center justify-center gap-2">
                {data.diagnostics.suggested_countries.map((c) => (
                  <button
                    key={c}
                    onClick={() => setParams({ ...params, country: c })}
                    className="px-3.5 py-1.5 rounded-xl bg-slate-800 border border-slate-700 text-indigo-300 text-xs font-bold hover:bg-slate-700 transition-all"
                  >
                    {c}
                  </button>
                ))}
              </div>
            </div>
          )}

          <div className="flex flex-wrap items-center justify-center gap-4 pt-4">
            <button
              onClick={handleResetFilters}
              className="px-5 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-white text-xs font-bold transition-all border border-slate-700"
            >
              Resetuj wszystkie filtry
            </button>

            <button
              onClick={handleFetchLiveForSeasonal}
              disabled={fetchingLive}
              className="px-6 py-2.5 rounded-xl bg-gradient-to-r from-indigo-600 to-purple-600 text-white text-xs font-bold shadow-lg flex items-center gap-2 hover:scale-105 transition-all"
            >
              <Sparkles className="w-4 h-4 text-amber-300" />
              <span>{fetchingLive ? 'Pobieranie ofert...' : 'Pobierz świeże oferty na żywo'}</span>
            </button>
          </div>
        </div>
      ) : data ? (
        <>
          {/* 2. Executive Summary */}
          {data.executive_summary && (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              {/* Cheapest Month */}
              {data.executive_summary.cheapest_month && (
                <div
                  onClick={() => setParams({ ...params, departure_month: data.executive_summary.cheapest_month?.month })}
                  className="p-5 rounded-3xl bg-slate-900/90 border border-emerald-500/40 backdrop-blur-xl space-y-3 cursor-pointer hover:border-emerald-400 transition-all group"
                >
                  <div className="flex items-center justify-between text-xs text-emerald-400 font-bold uppercase tracking-wider">
                    <span>Najtańszy Miesiąc</span>
                    <TrendingDown className="w-4 h-4 text-emerald-400" />
                  </div>

                  <div className="space-y-0.5">
                    <div className="text-2xl font-black text-white group-hover:text-emerald-300 transition-colors">
                      {data.executive_summary.cheapest_month.name} ({data.executive_summary.cheapest_month.season})
                    </div>
                    <p className="text-xs text-slate-300">
                      Średnia cena od <strong className="text-emerald-400">{data.executive_summary.cheapest_month.avg_price.toFixed(0)} PLN</strong>
                    </p>
                  </div>
                </div>
              )}

              {/* Peak Season */}
              {data.executive_summary.most_expensive_month && (
                <div
                  onClick={() => setParams({ ...params, departure_month: data.executive_summary.most_expensive_month?.month })}
                  className="p-5 rounded-3xl bg-slate-900/90 border border-amber-500/40 backdrop-blur-xl space-y-3 cursor-pointer hover:border-amber-400 transition-all group"
                >
                  <div className="flex items-center justify-between text-xs text-amber-400 font-bold uppercase tracking-wider">
                    <span>Szczyt Sezonu (Najdroższy)</span>
                    <TrendingUp className="w-4 h-4 text-amber-400" />
                  </div>

                  <div className="space-y-0.5">
                    <div className="text-2xl font-black text-white group-hover:text-amber-300 transition-colors">
                      {data.executive_summary.most_expensive_month.name} ({data.executive_summary.most_expensive_month.season})
                    </div>
                    <p className="text-xs text-slate-300">
                      Średnia cena sięga <strong className="text-amber-400">{data.executive_summary.most_expensive_month.avg_price.toFixed(0)} PLN</strong>
                    </p>
                  </div>
                </div>
              )}

              {/* Potential Savings */}
              {data.executive_summary.potential_savings && (
                <div className="p-5 rounded-3xl bg-slate-900/90 border border-indigo-500/40 backdrop-blur-xl space-y-3">
                  <div className="flex items-center justify-between text-xs text-indigo-400 font-bold uppercase tracking-wider">
                    <span>Możesz Zaoszczędzić</span>
                    <DollarSign className="w-4 h-4 text-indigo-400" />
                  </div>

                  <div className="space-y-0.5">
                    <div className="text-2xl font-black text-white">
                      {data.executive_summary.potential_savings.amount.toFixed(0)} PLN
                    </div>
                    <p className="text-xs text-slate-300">
                      Aż <strong className="text-emerald-400">{data.executive_summary.potential_savings.percentage.toFixed(0)}% oszczędności</strong> przy zmianie terminu
                    </p>
                  </div>
                </div>
              )}

              {/* Best Value Month */}
              {data.executive_summary.best_value_month && (
                <div
                  onClick={() => setParams({ ...params, departure_month: data.executive_summary.best_value_month?.month })}
                  className="p-5 rounded-3xl bg-slate-900/90 border border-purple-500/40 backdrop-blur-xl space-y-3 cursor-pointer hover:border-purple-400 transition-all group"
                >
                  <div className="flex items-center justify-between text-xs text-purple-400 font-bold uppercase tracking-wider">
                    <span>Stosunek Jakość / Cena</span>
                    <Award className="w-4 h-4 text-purple-400" />
                  </div>

                  <div className="space-y-0.5">
                    <div className="text-2xl font-black text-white group-hover:text-purple-300 transition-colors">
                      {data.executive_summary.best_value_month.name}
                    </div>
                    <p className="text-xs text-slate-300">
                      Value Score: <strong className="text-purple-400">{data.executive_summary.best_value_month.value_score} / 100</strong>
                    </p>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* 3. Interactive Price Calendar (12-Month Heatmap) */}
          <div className="p-6 rounded-3xl bg-slate-900/90 border border-slate-800 backdrop-blur-xl space-y-6 shadow-xl">
            <div className="flex flex-wrap items-center justify-between gap-4">
              <div className="space-y-1">
                <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-bold bg-indigo-500/10 text-indigo-300 border border-indigo-500/30">
                  <Calendar className="w-3.5 h-3.5" />
                  <span>12-Month Price Heatmap</span>
                </div>
                <h3 className="text-xl font-black text-white">Kalendarz Cenowy i Poziomy Sezonowe</h3>
              </div>

              <div className="flex items-center gap-4 text-xs font-semibold">
                <span className="flex items-center gap-1.5 text-emerald-400">
                  <span className="w-3 h-3 rounded-full bg-emerald-500" /> Niska Cena
                </span>
                <span className="flex items-center gap-1.5 text-amber-400">
                  <span className="w-3 h-3 rounded-full bg-amber-500" /> Średnia Cena
                </span>
                <span className="flex items-center gap-1.5 text-rose-400">
                  <span className="w-3 h-3 rounded-full bg-rose-500" /> Szczyt Sezonu
                </span>
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
              {data.monthly_heatmap.map((m) => {
                const isSelected = params.departure_month === m.month;
                const barWidthPct = Math.min(100, Math.max(15, (m.avg_price / maxHeatmapPrice) * 100));

                return (
                  <div
                    key={m.month}
                    onClick={() =>
                      setParams({
                        ...params,
                        departure_month: isSelected ? undefined : m.month,
                      })
                    }
                    className={`p-5 rounded-2xl border transition-all duration-200 space-y-3 cursor-pointer relative ${
                      isSelected
                        ? 'bg-indigo-950/80 border-indigo-500 shadow-xl scale-[1.02]'
                        : m.price_level === 'low'
                        ? 'bg-slate-900/90 border-emerald-500/40 hover:border-emerald-400'
                        : m.price_level === 'medium'
                        ? 'bg-slate-900/90 border-amber-500/40 hover:border-amber-400'
                        : 'bg-slate-900/90 border-rose-500/40 hover:border-rose-400'
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <span className="text-lg font-black text-white">{m.month_name}</span>
                        <span className="text-xs text-slate-400">({m.season})</span>
                      </div>

                      <span className="text-[10px] font-extrabold px-2 py-0.5 rounded-full bg-slate-800 text-slate-300 border border-slate-700">
                        {m.offer_count} ofert
                      </span>
                    </div>

                    <div className="space-y-1">
                      <div className="flex items-baseline justify-between">
                        <span className="text-xs text-slate-400">Średnia cena:</span>
                        <span className="text-lg font-black text-white">{m.avg_price.toFixed(0)} PLN</span>
                      </div>

                      <div className="w-full h-2 rounded-full bg-slate-950 overflow-hidden border border-slate-800">
                        <div
                          className={`h-full rounded-full transition-all duration-500 ${
                            m.price_level === 'low'
                              ? 'bg-gradient-to-r from-emerald-500 to-teal-400'
                              : m.price_level === 'medium'
                              ? 'bg-gradient-to-r from-amber-500 to-yellow-400'
                              : 'bg-gradient-to-r from-rose-500 to-amber-500'
                          }`}
                          style={{ width: `${barWidthPct}%` }}
                        />
                      </div>
                    </div>

                    <div className="grid grid-cols-2 gap-2 text-[11px] pt-1 border-t border-slate-800/60">
                      <div>
                        <span className="text-slate-500 block">Min / P10:</span>
                        <span className="font-bold text-emerald-400">{m.min_price.toFixed(0)} PLN</span>
                      </div>

                      <div className="text-right">
                        <span className="text-slate-500 block">Value Score:</span>
                        <span className="font-bold text-purple-300">{m.avg_value_score} / 100</span>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* 4. Price Trend Line Chart */}
          <div className="p-6 rounded-3xl bg-slate-900/90 border border-slate-800 backdrop-blur-xl space-y-6 shadow-xl">
            <div className="flex flex-wrap items-center justify-between gap-4">
              <div className="space-y-1">
                <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-bold bg-indigo-500/10 text-indigo-300 border border-indigo-500/30">
                  <LineChart className="w-3.5 h-3.5" />
                  <span>Interactive Multi-Quantile Trend Chart</span>
                </div>
                <h3 className="text-xl font-black text-white">Wykres Trendu Cenowego dla Miesięcy</h3>
              </div>

              {/* Metric Selector Tabs */}
              <div className="flex items-center gap-1 p-1 rounded-2xl bg-slate-950 border border-slate-800 text-xs font-bold">
                {[
                  { id: 'avg', label: 'Średnia' },
                  { id: 'median', label: 'Mediana' },
                  { id: 'min', label: 'Minimum' },
                  { id: 'max', label: 'Maksimum' },
                  { id: 'p10', label: 'P10 (Okazje)' },
                  { id: 'p25', label: 'P25' },
                  { id: 'p75', label: 'P75' },
                  { id: 'p90', label: 'P90' },
                ].map((metric) => (
                  <button
                    key={metric.id}
                    onClick={() => setSelectedMetric(metric.id as any)}
                    className={`px-3 py-1.5 rounded-xl transition-all ${
                      selectedMetric === metric.id
                        ? 'bg-indigo-600 text-white shadow-md'
                        : 'text-slate-400 hover:text-white'
                    }`}
                  >
                    {metric.label}
                  </button>
                ))}
              </div>
            </div>

            {/* Custom Interactive SVG Line Chart */}
            <div className="h-64 w-full relative pt-6">
              {data.price_trends.length > 0 && (
                <svg className="w-full h-full overflow-visible" viewBox="0 0 800 200" preserveAspectRatio="none">
                  {/* Grid Lines */}
                  {[0, 50, 100, 150, 200].map((y) => (
                    <line key={y} x1="0" y1={y} x2="800" y2={y} stroke="#1e293b" strokeDasharray="4 4" strokeWidth="1" />
                  ))}

                  {/* Chart Line Path */}
                  {(() => {
                    const values = data.price_trends.map((pt) => pt[selectedMetric] || pt.avg);
                    const minV = Math.min(...values, 1000);
                    const maxV = Math.max(...values, 5000);
                    const vRange = Math.max(maxV - minV, 100);

                    const points = data.price_trends.map((pt, idx) => {
                      const x = (idx / Math.max(data.price_trends.length - 1, 1)) * 760 + 20;
                      const val = pt[selectedMetric] || pt.avg;
                      const y = 180 - ((val - minV) / vRange) * 160;
                      return { x, y, val, monthName: pt.month_name };
                    });

                    const pathD = points.reduce((acc, p, idx) => (idx === 0 ? `M ${p.x} ${p.y}` : `${acc} L ${p.x} ${p.y}`), '');

                    return (
                      <>
                        <path d={pathD} fill="none" stroke="#6366f1" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" />

                        {points.map((p, idx) => (
                          <g key={idx} className="group cursor-pointer">
                            <circle cx={p.x} cy={p.y} r="5" fill="#818cf8" stroke="#0f172a" strokeWidth="2" className="transition-transform group-hover:scale-150" />

                            <text x={p.x} y={p.y - 12} textAnchor="middle" fill="#94a3b8" fontSize="10" className="font-bold">
                              {p.val.toFixed(0)} PLN
                            </text>

                            <text x={p.x} y="198" textAnchor="middle" fill="#64748b" fontSize="10" className="font-semibold">
                              {p.monthName.slice(0, 3)}
                            </text>
                          </g>
                        ))}
                      </>
                    );
                  })()}
                </svg>
              )}
            </div>
          </div>

          {/* 5. Price Distribution & 6. Seasonality Score (Side by Side) */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Price Distribution Histogram & Box Plot */}
            <div className="lg:col-span-2 p-6 rounded-3xl bg-slate-900/90 border border-slate-800 backdrop-blur-xl space-y-6 shadow-xl">
              <div className="space-y-1">
                <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-bold bg-indigo-500/10 text-indigo-300 border border-indigo-500/30">
                  <BarChart3 className="w-3.5 h-3.5" />
                  <span>Price Distribution & Box Plot</span>
                </div>
                <h3 className="text-xl font-black text-white">Rozkład Cen i Przedziały Okazji</h3>
              </div>

              {/* Histogram Bins */}
              <div className="space-y-2">
                <span className="text-xs font-bold text-slate-400">Histogram Ofert w Przedziałach Cenowych:</span>
                <div className="grid grid-cols-5 sm:grid-cols-10 gap-1.5 h-32 items-end pt-4 border-b border-slate-800 pb-2">
                  {data.price_distribution.buckets.map((b, bIdx) => {
                    const maxCnt = Math.max(...data.price_distribution.buckets.map((bk) => bk.count), 1);
                    const heightPct = Math.min(100, Math.max(10, (b.count / maxCnt) * 100));

                    return (
                      <div key={bIdx} className="flex flex-col items-center gap-1 group h-full justify-end">
                        <span className="text-[9px] text-slate-400 font-bold opacity-0 group-hover:opacity-100 transition-opacity">
                          {b.count}
                        </span>
                        <div
                          className="w-full rounded-t-lg bg-indigo-600/80 group-hover:bg-indigo-500 transition-all"
                          style={{ height: `${heightPct}%` }}
                        />
                        <span className="text-[8px] text-slate-500 truncate w-full text-center">{b.range_min}</span>
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* Box Plot Key Quantiles */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 pt-2 text-xs">
                <div className="p-3 rounded-2xl bg-slate-950 border border-slate-800 text-center space-y-0.5">
                  <span className="text-[10px] font-bold uppercase text-emerald-400">Najtańsze 10% (P10)</span>
                  <p className="text-sm font-black text-white">{data.price_distribution.best_deals_threshold.toFixed(0)} PLN</p>
                </div>

                <div className="p-3 rounded-2xl bg-slate-950 border border-slate-800 text-center space-y-0.5">
                  <span className="text-[10px] font-bold uppercase text-slate-400">Mediana Rynkowa</span>
                  <p className="text-sm font-black text-white">{data.price_distribution.market_median.toFixed(0)} PLN</p>
                </div>

                <div className="p-3 rounded-2xl bg-slate-950 border border-slate-800 text-center space-y-0.5">
                  <span className="text-[10px] font-bold uppercase text-slate-400">Kwartyl 1 (P25)</span>
                  <p className="text-sm font-black text-white">{data.price_distribution.box_plot.p25.toFixed(0)} PLN</p>
                </div>

                <div className="p-3 rounded-2xl bg-slate-950 border border-slate-800 text-center space-y-0.5">
                  <span className="text-[10px] font-bold uppercase text-slate-400">Kwartyl 3 (P75)</span>
                  <p className="text-sm font-black text-white">{data.price_distribution.box_plot.p75.toFixed(0)} PLN</p>
                </div>
              </div>
            </div>

            {/* 6. Seasonality Score Card */}
            <div className="p-6 rounded-3xl bg-slate-900/90 border border-slate-800 backdrop-blur-xl space-y-6 shadow-xl flex flex-col justify-between">
              <div className="space-y-3">
                <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-bold bg-amber-500/10 text-amber-300 border border-amber-500/30">
                  <Zap className="w-3.5 h-3.5" />
                  <span>Seasonality Score Index</span>
                </div>

                <h3 className="text-xl font-black text-white">Wskaźnik Sezonowości</h3>

                <div className="py-4 text-center space-y-2">
                  <div className="text-5xl font-black text-transparent bg-clip-text bg-gradient-to-r from-amber-400 to-rose-400">
                    {data.seasonality_score.score} <span className="text-xl text-slate-500 font-normal">/ 100</span>
                  </div>

                  <span className="inline-block px-3 py-1 rounded-full text-xs font-extrabold bg-amber-500/20 text-amber-300 border border-amber-500/30">
                    {data.seasonality_score.level}
                  </span>
                </div>

                <p className="text-xs text-slate-300 leading-relaxed bg-slate-950/60 p-4 rounded-2xl border border-slate-800">
                  {data.seasonality_score.description}
                </p>
              </div>

              {/* Comparative Benchmarks */}
              <div className="space-y-2 pt-2 border-t border-slate-800 text-[11px] text-slate-400">
                <span className="font-bold text-slate-300 block">Przykłady Porównawcze:</span>
                <div className="flex justify-between">
                  <span>Malta (Całoroczna):</span> <strong className="text-emerald-400">12 / 100</strong>
                </div>
                <div className="flex justify-between">
                  <span>Egipt (Stabilny):</span> <strong className="text-emerald-400">18 / 100</strong>
                </div>
                <div className="flex justify-between">
                  <span>Hiszpania Costa Brava:</span> <strong className="text-amber-400">79 / 100</strong>
                </div>
                <div className="flex justify-between">
                  <span>Chorwacja (Wysoce Sezonowa):</span> <strong className="text-rose-400">86 / 100</strong>
                </div>
              </div>
            </div>
          </div>

          {/* 7. Best Time To Buy Card */}
          {data.best_time_to_buy && (
            <div className="p-6 rounded-3xl bg-slate-900/90 border border-indigo-500/30 backdrop-blur-xl space-y-6 shadow-xl">
              <div className="flex flex-wrap items-center justify-between gap-4">
                <div className="space-y-1">
                  <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-bold bg-emerald-500/10 text-emerald-300 border border-emerald-500/30">
                    <Clock className="w-3.5 h-3.5" />
                    <span>Best Time To Buy Decision Engine</span>
                  </div>
                  <h3 className="text-xl font-black text-white">Rekomendacja Zakupu & Okno Czasowe</h3>
                </div>

                <span
                  className={`px-4 py-2 rounded-2xl text-xs font-extrabold uppercase border shadow-lg ${
                    data.best_time_to_buy.recommendation === 'BUY_NOW'
                      ? 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40'
                      : 'bg-amber-500/20 text-amber-300 border-amber-500/40'
                  }`}
                >
                  {data.best_time_to_buy.title}
                </span>
              </div>

              <p className="text-sm text-slate-300 leading-relaxed max-w-3xl">
                {data.best_time_to_buy.explanation}
              </p>

              {/* Lead Time Breakdown */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-2">
                {data.best_time_to_buy.lead_time_breakdown.map((lt, idx) => (
                  <div key={idx} className="p-4 rounded-2xl bg-slate-950 border border-slate-800 space-y-1">
                    <span className="text-[10px] font-bold uppercase text-slate-400">{lt.window}</span>
                    <p className="text-lg font-black text-white">{lt.avg_price.toFixed(0)} PLN / os.</p>
                    <span className="text-[11px] text-slate-500 block">{lt.count} ofert w tym oknie</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* 10. Transport Analysis (Flight vs Self Transport completely separated) */}
          <div className="p-6 rounded-3xl bg-slate-900/90 border border-slate-800 backdrop-blur-xl space-y-6 shadow-xl">
            <div className="flex flex-wrap items-center justify-between gap-4">
              <div className="space-y-1">
                <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-bold bg-sky-500/10 text-sky-300 border border-sky-500/30">
                  <Plane className="w-3.5 h-3.5" />
                  <span>Isolated Transport Split Engine</span>
                </div>
                <h3 className="text-xl font-black text-white">Analiza Transportu: Samolot vs Dojazd Własny</h3>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="p-5 rounded-2xl bg-slate-950 border border-slate-800 space-y-2">
                <span className="text-xs font-bold text-sky-400 flex items-center gap-1.5">
                  <Plane className="w-4 h-4" /> Średnia Cena Przelotu Samolotem
                </span>
                <p className="text-2xl font-black text-white">
                  {data.transport_analysis.flight_avg_price ? `${data.transport_analysis.flight_avg_price.toFixed(0)} PLN` : 'Brak danych'}
                </p>
              </div>

              <div className="p-5 rounded-2xl bg-slate-950 border border-slate-800 space-y-2">
                <span className="text-xs font-bold text-emerald-400 flex items-center gap-1.5">
                  <Car className="w-4 h-4" /> Średnia Cena Dojazdu Własnego
                </span>
                <p className="text-2xl font-black text-white">
                  {data.transport_analysis.self_transport_avg_price ? `${data.transport_analysis.self_transport_avg_price.toFixed(0)} PLN` : 'Brak danych'}
                </p>
              </div>

              <div className="p-5 rounded-2xl bg-slate-950 border border-indigo-500/30 space-y-2">
                <span className="text-xs font-bold text-indigo-400 uppercase tracking-wider">
                  Dopłata do Lotu (Flight Premium)
                </span>
                <p className="text-2xl font-black text-white">
                  {data.transport_analysis.flight_premium ? `+${data.transport_analysis.flight_premium.toFixed(0)} PLN` : 'N/A'}
                </p>
              </div>
            </div>
          </div>

          {/* 8. Regional Comparison & 9. Provider Comparison (Side by Side) */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Regional Comparison Table */}
            <div className="p-6 rounded-3xl bg-slate-900/90 border border-slate-800 backdrop-blur-xl space-y-4 shadow-xl overflow-hidden">
              <div className="space-y-1">
                <h3 className="text-lg font-black text-white flex items-center gap-2">
                  <MapPin className="w-5 h-5 text-indigo-400" />
                  Porównanie Regionów i Krajów
                </h3>
              </div>

              <div className="overflow-x-auto">
                <table className="w-full border-collapse text-xs text-left">
                  <thead>
                    <tr className="border-b border-slate-800 text-slate-400 uppercase text-[10px]">
                      <th className="py-2.5 px-3">Kraj / Region</th>
                      <th className="py-2.5 px-3">Śr. Cena</th>
                      <th className="py-2.5 px-3">Najtańszy M-c</th>
                      <th className="py-2.5 px-3">Sezonowość</th>
                      <th className="py-2.5 px-3 text-right">Ofert</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60 font-semibold">
                    {data.regional_comparison.map((r, rIdx) => (
                      <tr
                        key={rIdx}
                        onClick={() => handleNavigateExplorerWithParams({ country: r.country, region: r.region || undefined })}
                        className="hover:bg-slate-800/40 transition-colors cursor-pointer"
                      >
                        <td className="py-2.5 px-3 text-white">
                          <div>{r.country}</div>
                          <div className="text-[10px] text-slate-400">{r.region}</div>
                        </td>
                        <td className="py-2.5 px-3 text-emerald-400 font-bold">{r.avg_price.toFixed(0)} PLN</td>
                        <td className="py-2.5 px-3 text-slate-300">{r.cheapest_month_name}</td>
                        <td className="py-2.5 px-3">
                          <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-slate-800 text-amber-400">
                            {r.seasonality_score}/100
                          </span>
                        </td>
                        <td className="py-2.5 px-3 text-right text-slate-400">{r.offer_count}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Provider Comparison */}
            <div className="p-6 rounded-3xl bg-slate-900/90 border border-slate-800 backdrop-blur-xl space-y-4 shadow-xl">
              <div className="space-y-1">
                <h3 className="text-lg font-black text-white flex items-center gap-2">
                  <Building2 className="w-5 h-5 text-purple-400" />
                  Porównanie Organizatorów
                </h3>
              </div>

              <div className="space-y-3">
                {data.provider_comparison.map((p, pIdx) => (
                  <div
                    key={pIdx}
                    onClick={() => handleNavigateExplorerWithParams({ provider: p.provider })}
                    className="p-4 rounded-2xl bg-slate-950 border border-slate-800 hover:border-indigo-500/60 transition-all cursor-pointer flex items-center justify-between gap-4"
                  >
                    <div className="space-y-0.5">
                      <span className="text-sm font-black text-white uppercase">{p.provider}</span>
                      <p className="text-xs text-slate-400">
                        Najtańszy miesiąc: <strong className="text-slate-200">{p.cheapest_month_name}</strong> ({p.offer_count} ofert)
                      </p>
                    </div>

                    <div className="text-right space-y-0.5">
                      <div className="text-base font-black text-emerald-400">{p.avg_price.toFixed(0)} PLN / os.</div>
                      <span className="text-[10px] text-purple-300 font-bold block">
                        Value Score: {p.avg_value_score}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* 11. Price Forecast & 12. Smart Insights (Side by Side) */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Price Forecast */}
            <div className="p-6 rounded-3xl bg-slate-900/90 border border-slate-800 backdrop-blur-xl space-y-4 shadow-xl">
              <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-bold bg-purple-500/10 text-purple-300 border border-purple-500/30">
                <Sparkles className="w-3.5 h-3.5 text-amber-300" />
                <span>Deterministic Price Forecast (Experimental)</span>
              </div>

              <h3 className="text-xl font-black text-white">Prognoza Cen na Przyszły Miesiąc</h3>

              <div className="p-5 rounded-2xl bg-slate-950 border border-slate-800 flex items-center justify-between">
                <div>
                  <span className="text-xs text-slate-400">Oczekiwana cena w: <strong className="text-white">{data.price_forecast.next_month_name}</strong></span>
                  <p className="text-3xl font-black text-emerald-400">{data.price_forecast.expected_price.toFixed(0)} PLN</p>
                </div>

                <div className="text-right space-y-1">
                  <span className="text-2xl font-black text-amber-400">{data.price_forecast.trend_direction}</span>
                  <span className="text-[10px] text-slate-500 block">Pewność: {data.price_forecast.confidence_pct}%</span>
                </div>
              </div>

              <p className="text-xs text-slate-300 leading-relaxed">{data.price_forecast.summary}</p>
            </div>

            {/* Smart Insights */}
            <div className="p-6 rounded-3xl bg-slate-900/90 border border-slate-800 backdrop-blur-xl space-y-4 shadow-xl">
              <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-bold bg-indigo-500/10 text-indigo-300 border border-indigo-500/30">
                <Info className="w-3.5 h-3.5" />
                <span>Smart Deterministic Insights</span>
              </div>

              <h3 className="text-xl font-black text-white">Wnioski i Spostrzeżenia Rynkowe</h3>

              <ul className="space-y-2.5">
                {data.smart_insights.map((insight, iIdx) => (
                  <li key={iIdx} className="p-3 rounded-2xl bg-slate-950 border border-slate-800 text-xs text-slate-200 flex items-start gap-2.5">
                    <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
                    <span className="leading-relaxed">{insight}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </>
      ) : null}
    </div>
  );
};
