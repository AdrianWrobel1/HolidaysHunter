'use client';

import React, { useState } from 'react';
import { MultiOfferCompareReport, OfferAnalysisReport, SimilarOfferItem } from '@/types/api';
import {
  addWorkspaceItem,
  analyzeOffer,
  compareWorkspaceOffers,
  createWorkspaceSession,
  fetchWorkspaceSessions,
} from '@/lib/api';
import {
  Search,
  Sparkles,
  BarChart3,
  CheckCircle2,
  AlertTriangle,
  Zap,
  Hotel,
  Calendar,
  MapPin,
  ExternalLink,
  ShieldCheck,
  Award,
  Layers,
  Loader2,
  Check,
  HelpCircle,
  Car,
  Plane,
  Bus,
  X,
  Code,
  RefreshCw,
  BarChart2,
} from 'lucide-react';

const PRESET_URLS = [
  { label: 'Itaka - Egipt', url: 'https://www.itaka.pl/wczasy/egipt/hurghada/hotel-sunrise-grand,1234.html' },
  { label: 'TUI - Teneryfa', url: 'https://www.tui.pl/wypoczynek/hiszpania/teneryfa/hotel-bahia-principe' },
  { label: 'Rainbow - Grecja', url: 'https://r.pl/grecja/kreta/hotel-chania-palace' },
  { label: 'Wakacje.pl - Turcja', url: 'https://www.wakacje.pl/oferty/turcja/alanya/hotel-grand-sun,9988.html' },
];

interface OfferAnalyzerViewProps {
  initialReport?: OfferAnalysisReport | null;
}

export const OfferAnalyzerView: React.FC<OfferAnalyzerViewProps> = ({ initialReport = null }) => {
  const [inputUrl, setInputUrl] = useState(initialReport?.target_offer.offer_url || '');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [tableError, setTableError] = useState<string | null>(null);
  const [report, setReport] = useState<OfferAnalysisReport | null>(initialReport);
  
  // Interactive row & compare state
  const [loadingOfferUrl, setLoadingOfferUrl] = useState<string | null>(null);
  const [comparingOfferUrl, setComparingOfferUrl] = useState<string | null>(null);
  const [comparisonReport, setComparisonReport] = useState<MultiOfferCompareReport | null>(null);

  // In-memory report caching
  const [reportCache, setReportCache] = useState<Record<string, OfferAnalysisReport>>(() => {
    if (initialReport) {
      const key = initialReport.target_offer.offer_url || initialReport.target_offer.external_id;
      return { [key]: initialReport };
    }
    return {};
  });

  // Progressive disclosure modal & dev mode states
  const [isScoreModalOpen, setIsScoreModalOpen] = useState(false);
  const [devMode, setDevMode] = useState(false);

  const getOfferUrlOrFallback = (item: SimilarOfferItem): string => {
    if (item.offer_url && item.offer_url.trim()) {
      return item.offer_url.trim();
    }
    const cleanCountry = (item.country || 'hiszpania').toLowerCase().replace(/\s+/g, '-');
    const cleanHotel = (item.hotel_name || 'hotel').toLowerCase().replace(/\s+/g, '-');
    return `https://www.itaka.pl/wczasy/${cleanCountry}/${cleanHotel},${item.external_id}.html`;
  };

  const handleAnalyze = async (urlToAnalyze?: string, forceRefresh: boolean = false) => {
    const targetUrl = (urlToAnalyze || inputUrl).trim();
    if (!targetUrl) {
      setError('Wprowadź poprawny adres URL oferty.');
      return;
    }

    // Check in-memory cache if not forcing refresh
    if (!forceRefresh && reportCache[targetUrl]) {
      setReport(reportCache[targetUrl]);
      setInputUrl(reportCache[targetUrl].target_offer.offer_url || targetUrl);
      window.scrollTo({ top: 0, behavior: 'smooth' });
      return;
    }

    setLoading(true);
    if (urlToAnalyze) {
      setLoadingOfferUrl(targetUrl);
    }
    setError(null);
    setTableError(null);

    try {
      const data = await analyzeOffer(targetUrl);
      setReport(data);
      const finalUrl = data.target_offer.offer_url || targetUrl;
      setInputUrl(finalUrl);

      setReportCache((prev) => ({
        ...prev,
        [targetUrl]: data,
        [finalUrl]: data,
        [data.target_offer.external_id]: data,
      }));

      window.scrollTo({ top: 0, behavior: 'smooth' });
    } catch (err: any) {
      console.error('Error analyzing offer:', err);
      const msg = err.message || 'Wystąpił błąd podczas analizy oferty.';
      if (urlToAnalyze) {
        setTableError(msg);
      } else {
        setError(msg);
      }
    } finally {
      setLoading(false);
      setLoadingOfferUrl(null);
    }
  };

  const handleCompareOffer = async (item: SimilarOfferItem) => {
    const currentUrl = report?.target_offer.offer_url || inputUrl;
    const targetUrl = getOfferUrlOrFallback(item);

    if (!currentUrl) {
      setTableError('Brak aktywnej oferty do porównania.');
      return;
    }

    setComparingOfferUrl(targetUrl);
    setTableError(null);

    try {
      let sessions = await fetchWorkspaceSessions();
      let sessionId = sessions[0]?.id;
      if (!sessionId) {
        const newSession = await createWorkspaceSession('Analiza Porównawcza');
        sessionId = newSession.id;
      }

      const res1 = await addWorkspaceItem(sessionId, currentUrl, ['Observe'], [], true);
      const res2 = await addWorkspaceItem(sessionId, targetUrl, ['Observe'], [], true);

      const id1 = res1.item?.id;
      const id2 = res2.item?.id;

      if (!id1 || !id2) {
        throw new Error('Nie udało się przygotować ofert do porównania w sesji.');
      }

      const compReport = await compareWorkspaceOffers([id1, id2]);
      setComparisonReport(compReport);
    } catch (err: any) {
      console.error('Error comparing offers:', err);
      setTableError(err.message || 'Wystąpił błąd podczas porównywania ofert.');
    } finally {
      setComparingOfferUrl(null);
    }
  };

  const renderTransportLabel = (transportType?: string) => {
    const t = String(transportType || 'flight').toLowerCase();
    if (t === 'self_transport' || t === 'own') {
      return (
        <span className="flex items-center gap-1.5 px-2.5 py-1 rounded-xl bg-amber-500/20 text-amber-300 font-bold border border-amber-500/30 text-xs">
          <Car className="w-3.5 h-3.5" />
          <span>Dojazd własny</span>
        </span>
      );
    }
    if (t === 'bus') {
      return (
        <span className="flex items-center gap-1.5 px-2.5 py-1 rounded-xl bg-sky-500/20 text-sky-300 font-bold border border-sky-500/30 text-xs">
          <Bus className="w-3.5 h-3.5" />
          <span>Autokar</span>
        </span>
      );
    }
    return (
      <span className="flex items-center gap-1.5 px-2.5 py-1 rounded-xl bg-indigo-500/20 text-indigo-300 font-bold border border-indigo-500/30 text-xs">
        <Plane className="w-3.5 h-3.5" />
        <span>Przelot samolotem</span>
      </span>
    );
  };

  return (
    <div className="space-y-8 animate-fadeIn">
      {/* Header Banner */}
      <div className="relative overflow-hidden rounded-3xl bg-gradient-to-r from-indigo-950 via-slate-900 to-purple-950 border border-slate-800 p-8 shadow-2xl">
        <div className="absolute top-0 right-0 w-96 h-96 bg-purple-500/10 rounded-full blur-3xl pointer-events-none" />
        <div className="relative z-10 max-w-3xl space-y-3">
          <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full text-xs font-bold bg-purple-500/20 text-purple-300 border border-purple-500/30">
            <Zap className="w-3.5 h-3.5 text-amber-400 fill-amber-400" />
            <span>Universal Analysis Framework Client</span>
          </div>
          <h2 className="text-3xl sm:text-4xl font-black text-white tracking-tight">
            Offer Analyzer Dashboard
          </h2>
          <p className="text-sm text-slate-300 leading-relaxed">
            Wklej odnośnik do dowolnej oferty (Itaka, TUI, Rainbow, Wakacje.pl), a system automatycznie rozpozna operatora, znormalizuje dane i uruchomi modułowy silnik analityczny.
          </p>
        </div>
      </div>

      {/* Input Search Card */}
      <div className="p-6 rounded-3xl bg-slate-900/80 border border-slate-800 backdrop-blur-xl shadow-xl space-y-4">
        <label className="block text-xs font-bold text-slate-300 uppercase tracking-wider">
          Adres URL oferty turystycznej
        </label>

        <div className="flex flex-col sm:flex-row items-center gap-3">
          <div className="relative flex-1 w-full">
            <input
              type="text"
              value={inputUrl}
              onChange={(e) => setInputUrl(e.target.value)}
              placeholder="np. https://www.itaka.pl/wczasy/hiszpania/teneryfa/hotel..."
              className="w-full pl-11 pr-4 py-3.5 rounded-2xl bg-slate-950 border border-slate-800 text-slate-100 placeholder-slate-500 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 text-sm transition-all shadow-inner"
            />
            <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
          </div>

          <button
            onClick={() => handleAnalyze()}
            disabled={loading}
            className="w-full sm:w-auto px-7 py-3.5 rounded-2xl bg-gradient-to-r from-indigo-600 via-indigo-500 to-purple-600 hover:from-indigo-500 hover:to-purple-500 text-white font-bold text-sm shadow-xl shadow-indigo-600/25 transition-all hover:scale-105 active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2 shrink-0"
          >
            {loading ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin text-white" />
                <span>Analizowanie...</span>
              </>
            ) : (
              <>
                <Sparkles className="w-4 h-4 text-amber-300" />
                <span>Przeanalizuj Ofertę</span>
              </>
            )}
          </button>
        </div>

        {/* Preset Links */}
        <div className="flex flex-wrap items-center gap-2 pt-2">
          <span className="text-xs font-medium text-slate-400 mr-1">Przykłady testowe:</span>
          {PRESET_URLS.map((preset, idx) => (
            <button
              key={idx}
              onClick={() => {
                setInputUrl(preset.url);
                handleAnalyze(preset.url);
              }}
              className="px-3 py-1.5 rounded-xl bg-slate-800/80 hover:bg-slate-800 text-slate-300 hover:text-indigo-300 border border-slate-700/60 text-xs font-medium transition-all"
            >
              {preset.label}
            </button>
          ))}
        </div>

        {error && (
          <div className="p-4 rounded-2xl bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs flex items-center gap-3">
            <AlertTriangle className="w-4 h-4 text-rose-400 shrink-0" />
            <span>{error}</span>
          </div>
        )}
      </div>

      {/* Analysis Results Display */}
      {report && (
        <div className="space-y-8 animate-fadeIn">
          {/* Main Top Grid: Target Offer & Deal Score Banner */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Offer Summary Card */}
            <div className="lg:col-span-2 p-6 rounded-3xl bg-slate-900/80 border border-slate-800 backdrop-blur-xl shadow-xl space-y-4">
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="px-3 py-1 rounded-full text-xs font-bold bg-indigo-500/20 text-indigo-300 border border-indigo-500/30 uppercase tracking-wider">
                      {report.target_offer.provider}
                    </span>
                    <span className="text-xs text-slate-400">ID: {report.target_offer.external_id}</span>
                  </div>

                  <button
                    onClick={() => handleAnalyze(report.target_offer.offer_url || inputUrl, true)}
                    disabled={loading}
                    className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white text-xs font-semibold border border-slate-700 transition-all disabled:opacity-50"
                    title="Wymuś ponowne wykonanie pełnej analizy dla tej oferty"
                  >
                    <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin text-indigo-400' : 'text-slate-400'}`} />
                    <span>Odśwież analizę</span>
                  </button>
                </div>

                <h3 className="text-2xl font-black text-white tracking-tight">
                  {report.target_offer.title}
                </h3>

                <div className="flex flex-wrap items-center gap-3 text-xs text-slate-300">
                  {report.target_offer.hotel_stars && (
                    <span className="px-2.5 py-1 rounded-xl bg-amber-500/10 border border-amber-500/30 text-amber-300 font-bold">
                      ★ {report.target_offer.hotel_stars} / 5
                    </span>
                  )}
                  {report.target_offer.hotel_rating && (
                    <span className="px-2.5 py-1 rounded-xl bg-indigo-500/10 border border-indigo-500/30 text-indigo-300 font-bold">
                      Guest Rating {report.target_offer.hotel_rating} / 10
                    </span>
                  )}
                  {renderTransportLabel(report.target_offer.transport_type)}
                  <span className="flex items-center gap-1">
                    <Calendar className="w-3.5 h-3.5 text-slate-400" />
                    {report.target_offer.departure_date} ({report.target_offer.duration_nights} dni)
                  </span>
                  <span className="px-2.5 py-1 rounded-xl bg-slate-800 text-slate-300 font-semibold">
                    {report.target_offer.meal_type}
                  </span>
                </div>

                <div className="pt-2 flex items-baseline gap-3">
                  <span className="text-3xl font-black text-emerald-400">
                    {report.target_offer.price_per_person} PLN
                  </span>
                  <span className="text-xs text-slate-400">za osobę / łącznie {report.target_offer.price_total} PLN</span>
                </div>

                {report.target_offer.offer_url && (
                  <div className="pt-2">
                    <a
                      href={report.target_offer.offer_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center gap-1.5 text-xs font-bold text-indigo-400 hover:text-indigo-300 transition-colors"
                    >
                      <span>Zobacz bezpośrednią ofertę u operatora</span>
                      <ExternalLink className="w-3.5 h-3.5" />
                    </a>
                  </div>
                )}
              </div>
            </div>

            {/* Deal Score & Recommendation Card (Clickable for Progressive Disclosure Modal) */}
            <div
              onClick={() => setIsScoreModalOpen(true)}
              className="p-6 rounded-3xl bg-slate-900/80 border border-slate-800 backdrop-blur-xl shadow-xl flex flex-col justify-between space-y-4 hover:border-indigo-500/50 hover:shadow-indigo-500/10 transition-all cursor-pointer group"
            >
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
                  <Award className="w-4 h-4 text-amber-400" />
                  Deal Score
                </span>
                <div className={`px-3 py-1 rounded-full text-xs font-black tracking-wider uppercase bg-${report.recommendation.verdict_color}-500/20 text-${report.recommendation.verdict_color}-400 border border-${report.recommendation.verdict_color}-500/30`}>
                  {report.recommendation.verdict_badge}
                </div>
              </div>

              <div className="flex items-center justify-center gap-4 py-2">
                <div className="relative w-28 h-28 rounded-full border-4 border-indigo-500/30 bg-slate-950 flex flex-col items-center justify-center shadow-inner group-hover:scale-105 transition-transform">
                  <span className="text-4xl font-black text-white">{report.deal_score.total_score}</span>
                  <span className="text-[10px] font-bold text-slate-400 uppercase">/ 100</span>
                </div>
              </div>

              <div className="space-y-2 text-center">
                <h4 className="text-sm font-bold text-slate-200">{report.recommendation.title}</h4>
                <p className="text-xs text-slate-400 leading-relaxed">{report.deal_score.summary}</p>
                <div className="pt-1 flex items-center justify-center gap-1 text-xs font-bold text-indigo-400 group-hover:text-indigo-300">
                  <HelpCircle className="w-3.5 h-3.5" />
                  <span>Kliknij, aby zobaczyć breakdown i diagnostykę</span>
                </div>
              </div>
            </div>
          </div>

          {/* Key Takeaways & Quality Highlights */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="p-6 rounded-3xl bg-slate-900/80 border border-slate-800 backdrop-blur-xl shadow-xl space-y-3">
              <h4 className="text-xs font-bold text-slate-300 uppercase tracking-wider flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                Rekomendacja i Wnioski
              </h4>
              <ul className="space-y-2">
                {report.recommendation.takeaways.map((t, idx) => (
                  <li key={idx} className="flex items-start gap-2.5 text-xs text-slate-300">
                    <Check className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
                    <span>{t}</span>
                  </li>
                ))}
              </ul>
            </div>

            <div className="p-6 rounded-3xl bg-slate-900/80 border border-slate-800 backdrop-blur-xl shadow-xl space-y-3">
              <h4 className="text-xs font-bold text-slate-300 uppercase tracking-wider flex items-center gap-2">
                <ShieldCheck className="w-4 h-4 text-indigo-400" />
                Jakość Oferty ({report.offer_quality.quality_score.toFixed(0)}/100)
              </h4>
              <ul className="space-y-2">
                {report.offer_quality.highlights.map((h, idx) => (
                  <li key={idx} className="flex items-center gap-2.5 text-xs text-slate-300">
                    <span className="w-1.5 h-1.5 rounded-full bg-indigo-400 shrink-0" />
                    <span>{h}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>

          {/* Metrics Grid */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            <div className="p-5 rounded-2xl bg-slate-900/80 border border-slate-800 text-center space-y-1">
              <span className="text-[11px] font-semibold text-slate-400 uppercase">Pozycja Rynkowa</span>
              <p className="text-xl font-black text-indigo-400">
                {report.market_position.cheaper_than_pct.toFixed(0)}%
              </p>
              <span className="text-[10px] text-slate-500">Tańsza niż reszta ofert</span>
            </div>

            <div className="p-5 rounded-2xl bg-slate-900/80 border border-slate-800 text-center space-y-1">
              <span className="text-[11px] font-semibold text-slate-400 uppercase">Średnia Cenowa</span>
              <p className="text-xl font-black text-slate-200">
                {report.statistics.mean_price.toFixed(0)} PLN
              </p>
              <span className="text-[10px] text-slate-500">Różnica: {report.statistics.price_diff_pct > 0 ? '+' : ''}{report.statistics.price_diff_pct.toFixed(1)}%</span>
            </div>

            <div className="p-5 rounded-2xl bg-slate-900/80 border border-slate-800 text-center space-y-1">
              <span className="text-[11px] font-semibold text-slate-400 uppercase">Stawka Dzienna</span>
              <p className="text-xl font-black text-emerald-400">
                {report.price_efficiency.person_daily_rate.toFixed(0)} PLN
              </p>
              <span className="text-[10px] text-slate-500">Za osobę / dzień</span>
            </div>

            <div className="p-5 rounded-2xl bg-slate-900/80 border border-slate-800 text-center space-y-1">
              <span className="text-[11px] font-semibold text-slate-400 uppercase">Zakres Cenowy</span>
              <p className="text-xl font-black text-slate-200">
                {report.statistics.min_price.toFixed(0)} - {report.statistics.max_price.toFixed(0)} PLN
              </p>
              <span className="text-[10px] text-slate-500">Min - Max rynkowe</span>
            </div>
          </div>

          {/* Charts Section */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Price Histogram */}
            <div className="p-6 rounded-3xl bg-slate-900/80 border border-slate-800 backdrop-blur-xl shadow-xl space-y-4">
              <h4 className="text-sm font-bold text-slate-200 flex items-center gap-2">
                <BarChart3 className="w-4 h-4 text-indigo-400" />
                Histogram Cen Podobnych Ofert
              </h4>
              <p className="text-xs text-slate-400">
                Rozkład częstotliwości cen w grupie porównawczej z zaznaczoną pozycją analizowanej oferty.
              </p>

              <div className="space-y-3 pt-2">
                {report.charts.histogram_bins.map((bin, i) => {
                  const maxCount = Math.max(...report.charts.histogram_bins.map((b) => b.count), 1);
                  const pctWidth = Math.max(8, (bin.count / maxCount) * 100);

                  return (
                    <div key={i} className="space-y-1">
                      <div className="flex justify-between text-xs font-medium text-slate-300">
                        <span className="flex items-center gap-1.5">
                          {bin.bin_label}
                          {bin.is_target_bin && (
                            <span className="px-1.5 py-0.5 text-[9px] font-bold rounded bg-indigo-500 text-white uppercase">
                              Twoja oferta
                            </span>
                          )}
                        </span>
                        <span>{bin.count} ofert</span>
                      </div>

                      <div className="w-full h-3 rounded-full bg-slate-800 overflow-hidden">
                        <div
                          className={`h-full rounded-full transition-all ${
                            bin.is_target_bin
                              ? 'bg-gradient-to-r from-amber-400 to-indigo-500 shadow-md shadow-indigo-500/50'
                              : 'bg-slate-700'
                          }`}
                          style={{ width: `${pctWidth}%` }}
                        />
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Box Plot Visualization */}
            <div className="p-6 rounded-3xl bg-slate-900/80 border border-slate-800 backdrop-blur-xl shadow-xl space-y-4 flex flex-col justify-between">
              <div>
                <h4 className="text-sm font-bold text-slate-200 flex items-center gap-2">
                  <Layers className="w-4 h-4 text-purple-400" />
                  Box Plot — Statystyczna Pozycja Ceny
                </h4>
                <p className="text-xs text-slate-400">
                  Wykreślone percentyle Q1, mediana, Q3 oraz cena Twojej oferty.
                </p>
              </div>

              <div className="space-y-4 py-4">
                <div className="grid grid-cols-5 gap-2 text-center text-xs">
                  <div className="p-2 rounded-xl bg-slate-800/40 border border-slate-700/40">
                    <span className="block text-[10px] text-slate-500 uppercase">Min</span>
                    <span className="font-bold text-slate-300">{report.charts.box_plot.min_val.toFixed(0)}</span>
                  </div>
                  <div className="p-2 rounded-xl bg-slate-800/40 border border-slate-700/40">
                    <span className="block text-[10px] text-slate-500 uppercase">Q1 (25%)</span>
                    <span className="font-bold text-slate-300">{report.charts.box_plot.q1.toFixed(0)}</span>
                  </div>
                  <div className="p-2 rounded-xl bg-indigo-500/10 border border-indigo-500/30">
                    <span className="block text-[10px] text-indigo-400 uppercase">Mediana</span>
                    <span className="font-bold text-indigo-300">{report.charts.box_plot.median.toFixed(0)}</span>
                  </div>
                  <div className="p-2 rounded-xl bg-slate-800/40 border border-slate-700/40">
                    <span className="block text-[10px] text-slate-500 uppercase">Q3 (75%)</span>
                    <span className="font-bold text-slate-300">{report.charts.box_plot.q3.toFixed(0)}</span>
                  </div>
                  <div className="p-2 rounded-xl bg-slate-800/40 border border-slate-700/40">
                    <span className="block text-[10px] text-slate-500 uppercase">Max</span>
                    <span className="font-bold text-slate-300">{report.charts.box_plot.max_val.toFixed(0)}</span>
                  </div>
                </div>

                <div className="p-4 rounded-2xl bg-indigo-600/10 border border-indigo-500/30 flex items-center justify-between text-xs">
                  <span className="font-semibold text-slate-300">Cena Twojej Oferty:</span>
                  <span className="text-base font-black text-amber-400">{report.charts.box_plot.target_val.toFixed(0)} PLN</span>
                </div>
              </div>

              <p className="text-[11px] text-slate-500 italic text-center">
                {report.statistics.position_summary}
              </p>
            </div>
          </div>

          {/* Similar Offers Table */}
          <div className="p-6 rounded-3xl bg-slate-900/80 border border-slate-800 backdrop-blur-xl shadow-xl space-y-4">
            <div className="flex items-center justify-between">
              <h4 className="text-base font-bold text-slate-100 flex items-center gap-2">
                <Hotel className="w-5 h-5 text-indigo-400" />
                Najbardziej Podobne Oferty w Bazie ({report.similarity.top_matches.length})
              </h4>
              <span className="text-xs text-slate-400">Posortowane według Similarity Score</span>
            </div>

            {tableError && (
              <div className="p-4 rounded-2xl bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs flex items-center justify-between gap-3 animate-fadeIn">
                <div className="flex items-center gap-2">
                  <AlertTriangle className="w-4 h-4 text-rose-400 shrink-0" />
                  <span>{tableError}</span>
                </div>
                <button
                  onClick={() => {
                    setTableError(null);
                    if (inputUrl) handleAnalyze(inputUrl, true);
                  }}
                  className="px-3 py-1 rounded-xl bg-rose-600/30 hover:bg-rose-600 text-white font-bold text-xs transition-colors shrink-0"
                >
                  Spróbuj ponownie
                </button>
              </div>
            )}

            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse text-xs">
                <thead>
                  <tr className="border-b border-slate-800 text-slate-400 font-semibold uppercase text-[10px] tracking-wider">
                    <th className="py-3 px-4">Podobieństwo</th>
                    <th className="py-3 px-4">Hotel / Kraj</th>
                    <th className="py-3 px-4">Termin / Dni</th>
                    <th className="py-3 px-4">Wyżywienie</th>
                    <th className="py-3 px-4">Cena/os</th>
                    <th className="py-3 px-4">Uzasadnienie Wyboru / Akcje</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60">
                  {report.similarity.top_matches.map((item, idx) => {
                    const targetUrl = getOfferUrlOrFallback(item);
                    const isRowAnalyzing = loadingOfferUrl === targetUrl;
                    const isRowComparing = comparingOfferUrl === targetUrl;
                    const isRowBusy = isRowAnalyzing || isRowComparing;

                    return (
                      <tr
                        key={idx}
                        className={`hover:bg-slate-800/40 transition-colors cursor-pointer group ${
                          isRowBusy ? 'opacity-60 cursor-wait' : ''
                        }`}
                        onClick={() => {
                          if (!isRowBusy) {
                            handleAnalyze(targetUrl);
                          }
                        }}
                      >
                        <td className="py-3 px-4 font-bold text-indigo-400">
                          <span className="px-2.5 py-1 rounded-full bg-indigo-500/10 border border-indigo-500/30">
                            {item.similarity_score}%
                          </span>
                        </td>
                        <td className="py-3 px-4">
                          <div className="font-bold text-slate-200 group-hover:text-indigo-300 transition-colors">{item.hotel_name}</div>
                          <div className="text-[10px] text-slate-400">{item.country} {item.region ? `• ${item.region}` : ''}</div>
                        </td>
                        <td className="py-3 px-4 text-slate-300">
                          <div>{item.departure_date}</div>
                          <div className="text-[10px] text-slate-500">{item.duration_nights} dni</div>
                        </td>
                        <td className="py-3 px-4 text-slate-300">{item.meal_type}</td>
                        <td className="py-3 px-4 font-bold text-emerald-400">
                          {item.price_per_person} PLN
                        </td>
                        <td className="py-3 px-4">
                          <div className="flex flex-wrap items-center gap-1.5">
                            {item.explanations.map((exp, eIdx) => (
                              <span
                                key={eIdx}
                                className="px-2 py-0.5 rounded text-[10px] font-semibold bg-emerald-500/10 text-emerald-300 border border-emerald-500/20"
                              >
                                {exp}
                              </span>
                            ))}
                            <div className="ml-auto flex items-center gap-1.5 shrink-0">
                              <button
                                onClick={(e) => {
                                  e.stopPropagation();
                                  handleAnalyze(targetUrl);
                                }}
                                disabled={isRowBusy}
                                className="px-2.5 py-1 rounded-lg bg-indigo-600/20 hover:bg-indigo-600 text-indigo-300 hover:text-white border border-indigo-500/30 text-[10px] font-bold transition-all disabled:opacity-50 flex items-center gap-1"
                              >
                                {isRowAnalyzing ? (
                                  <>
                                    <Loader2 className="w-3 h-3 animate-spin text-white" />
                                    <span>Analizowanie...</span>
                                  </>
                                ) : (
                                  <span>Przeanalizuj tę ofertę</span>
                                )}
                              </button>

                              <button
                                onClick={(e) => {
                                  e.stopPropagation();
                                  handleCompareOffer(item);
                                }}
                                disabled={isRowBusy}
                                className="px-2.5 py-1 rounded-lg bg-purple-600/20 hover:bg-purple-600 text-purple-300 hover:text-white border border-purple-500/30 text-[10px] font-bold transition-all disabled:opacity-50 flex items-center gap-1"
                              >
                                {isRowComparing ? (
                                  <>
                                    <Loader2 className="w-3 h-3 animate-spin text-white" />
                                    <span>Ładowanie...</span>
                                  </>
                                ) : (
                                  <>
                                    <BarChart2 className="w-3 h-3 text-purple-400" />
                                    <span>Porównaj</span>
                                  </>
                                )}
                              </button>
                            </div>
                          </div>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* Progressive Disclosure Modal for Scoring Diagnostics */}
      {isScoreModalOpen && report && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md animate-fadeIn">
          <div className="relative w-full max-w-3xl max-h-[90vh] overflow-y-auto rounded-3xl bg-slate-900 border border-slate-800 p-6 sm:p-8 shadow-2xl space-y-6">
            {/* Modal Header */}
            <div className="flex items-center justify-between border-b border-slate-800 pb-4">
              <div className="flex items-center gap-3">
                <div className="p-2.5 rounded-2xl bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
                  <Award className="w-6 h-6 text-amber-400" />
                </div>
                <div>
                  <h3 className="text-xl font-bold text-white">Diagnostyka Deal Score & Value Engine</h3>
                  <p className="text-xs text-slate-400">Szczegółowy breakdown komponentów, wag oraz pewności wyliczeń</p>
                </div>
              </div>

              <button
                onClick={() => setIsScoreModalOpen(false)}
                className="p-2 rounded-xl bg-slate-800 text-slate-400 hover:text-white transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Scores Overview Row */}
            <div className="grid grid-cols-3 gap-4 text-center">
              <div className="p-4 rounded-2xl bg-purple-950/60 border border-purple-500/30 space-y-1">
                <span className="text-[10px] font-bold uppercase text-purple-300">Deal Score</span>
                <p className="text-3xl font-black text-white">{report.deal_score.total_score}</p>
                <span className="text-[10px] text-purple-400 font-medium">Zakup TERAZ</span>
              </div>

              <div className="p-4 rounded-2xl bg-emerald-950/60 border border-emerald-500/30 space-y-1">
                <span className="text-[10px] font-bold uppercase text-emerald-300">Value Score</span>
                <p className="text-3xl font-black text-emerald-400">{report.deal_score.value_score || 85}</p>
                <span className="text-[10px] text-emerald-400 font-medium">Jakość vs Cena</span>
              </div>

              <div className="p-4 rounded-2xl bg-indigo-950/60 border border-indigo-500/30 space-y-1">
                <span className="text-[10px] font-bold uppercase text-indigo-300">Confidence</span>
                <p className="text-3xl font-black text-indigo-400">{report.deal_score.confidence?.score || 90}%</p>
                <span className="text-[10px] text-indigo-400 font-medium">Wiarygodność danych</span>
              </div>
            </div>

            {/* Explainability Engine Section */}
            <div className="p-5 rounded-2xl bg-slate-950/80 border border-slate-800 space-y-3">
              <h4 className="text-xs font-bold text-indigo-400 uppercase tracking-wider flex items-center gap-2">
                <Zap className="w-4 h-4 text-amber-400 fill-amber-400" />
                Wyjaśnienie Deterministyczne (Explainability Engine)
              </h4>
              <ul className="space-y-2">
                {(report.deal_score.explanations || []).map((exp, idx) => (
                  <li key={idx} className="flex items-start gap-2 text-xs text-slate-300">
                    <span className="w-1.5 h-1.5 rounded-full bg-indigo-400 shrink-0 mt-1.5" />
                    <span>{exp}</span>
                  </li>
                ))}
              </ul>
            </div>

            {/* Components Breakdown Table */}
            <div className="space-y-3">
              <h4 className="text-xs font-bold text-slate-300 uppercase tracking-wider">
                Składniki Wyniku (Component Breakdown & Impact)
              </h4>
              <div className="overflow-x-auto">
                <table className="w-full text-left border-collapse text-xs">
                  <thead>
                    <tr className="border-b border-slate-800 text-slate-400 font-semibold uppercase text-[10px]">
                      <th className="py-2 px-3">Komponent</th>
                      <th className="py-2 px-3">Punkty</th>
                      <th className="py-2 px-3">Waga</th>
                      <th className="py-2 px-3">Wpływ (Impact)</th>
                      <th className="py-2 px-3">Opis</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60">
                    {report.deal_score.components.map((comp, idx) => (
                      <tr key={idx} className="hover:bg-slate-800/40">
                        <td className="py-2.5 px-3 font-bold text-slate-200">{comp.name}</td>
                        <td className="py-2.5 px-3 font-bold text-indigo-400">{comp.score.toFixed(0)}/100</td>
                        <td className="py-2.5 px-3 text-slate-400">{(comp.weight * 100).toFixed(0)}%</td>
                        <td className={`py-2.5 px-3 font-bold ${ (comp.impact || 0) >= 0 ? 'text-emerald-400' : 'text-rose-400' }`}>
                          {(comp.impact || 0) >= 0 ? '+' : ''}{(comp.impact || 0).toFixed(1)} pkt
                        </td>
                        <td className="py-2.5 px-3 text-slate-300 text-[11px]">{comp.explanation}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Developer Mode Toggle */}
            <div className="pt-4 border-t border-slate-800 flex items-center justify-between">
              <button
                onClick={() => setDevMode(!devMode)}
                className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-bold border border-slate-700 transition-colors"
              >
                <Code className="w-3.5 h-3.5 text-purple-400" />
                <span>{devMode ? 'Ukryj Developer Mode' : 'Włącz Developer Mode'}</span>
              </button>

              <button
                onClick={() => setIsScoreModalOpen(false)}
                className="px-5 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-bold text-xs transition-colors"
              >
                Zamknij
              </button>
            </div>

            {/* Developer Mode Technical JSON Output */}
            {devMode && (
              <div className="p-4 rounded-2xl bg-black border border-purple-500/30 text-purple-300 font-mono text-[11px] space-y-2">
                <span className="block text-[10px] uppercase font-bold text-purple-400">Surowe Dane Diagnostyczne (JSON):</span>
                <pre className="overflow-x-auto whitespace-pre-wrap max-h-48">
                  {JSON.stringify(
                    {
                      analysis_id: report.analysis_id,
                      duration_ms: report.duration_ms,
                      cache_used: report.cache_used,
                      deal_score: report.deal_score,
                    },
                    null,
                    2
                  )}
                </pre>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Comparison Engine View Modal */}
      {comparisonReport && (
        <div className="fixed inset-0 z-50 bg-slate-950/90 backdrop-blur-md overflow-y-auto p-4 sm:p-8 animate-fadeIn">
          <div className="max-w-6xl mx-auto space-y-6 relative">
            <button
              onClick={() => setComparisonReport(null)}
              className="fixed top-6 right-6 z-50 p-3 rounded-2xl bg-slate-900 border border-slate-700 text-white font-bold hover:bg-slate-800 shadow-2xl flex items-center gap-2"
            >
              <X className="w-5 h-5" />
              <span>Zamknij Porównanie</span>
            </button>

            <div className="p-6 sm:p-8 rounded-3xl bg-slate-900 border border-slate-800 space-y-6 shadow-2xl">
              <div className="space-y-2">
                <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-bold bg-purple-500/20 text-purple-300 border border-purple-500/30">
                  <BarChart2 className="w-3.5 h-3.5" />
                  <span>Comparison Engine Matrix</span>
                </div>
                <h3 className="text-2xl font-black text-white">Porównanie Ofert ({comparisonReport.items.length})</h3>
                <p className="text-xs text-slate-300 leading-relaxed">{comparisonReport.upgrade_recommendation}</p>
              </div>

              {/* Highlights Badges */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
                <div className="p-3 rounded-2xl bg-amber-500/10 border border-amber-500/30">
                  <span className="block text-[10px] text-amber-400 font-bold uppercase">Najlepsza Ogólnie</span>
                  <span className="font-bold text-white">Oferta #{comparisonReport.best_overall_index + 1}</span>
                </div>
                <div className="p-3 rounded-2xl bg-emerald-500/10 border border-emerald-500/30">
                  <span className="block text-[10px] text-emerald-400 font-bold uppercase">Najlepszy Stosunek</span>
                  <span className="font-bold text-white">Oferta #{comparisonReport.best_value_index + 1}</span>
                </div>
                <div className="p-3 rounded-2xl bg-sky-500/10 border border-sky-500/30">
                  <span className="block text-[10px] text-sky-400 font-bold uppercase">Najtańsza</span>
                  <span className="font-bold text-white">Oferta #{comparisonReport.cheapest_index + 1}</span>
                </div>
                <div className="p-3 rounded-2xl bg-purple-500/10 border border-purple-500/30">
                  <span className="block text-[10px] text-purple-400 font-bold uppercase">Najwyższy Standard</span>
                  <span className="font-bold text-white">Oferta #{comparisonReport.highest_standard_index + 1}</span>
                </div>
              </div>

              {/* Matrix Table */}
              <div className="overflow-x-auto pt-2">
                <table className="w-full text-left border-collapse text-xs">
                  <thead>
                    <tr className="border-b border-slate-800 text-slate-400 uppercase text-[10px]">
                      <th className="py-3 px-4">Kryterium</th>
                      {comparisonReport.items.map((item, idx) => {
                        const offer = item.latest_report?.target_offer;
                        return (
                          <th key={idx} className="py-3 px-4">
                            <div className="font-bold text-slate-200">{offer?.title ?? offer?.hotel_name ?? `Oferta ${idx + 1}`}</div>
                            <div className="text-[10px] text-slate-500">
                              {offer?.provider ?? '—'} • {offer?.price_per_person ?? '—'} PLN
                            </div>
                          </th>
                        );
                      })}
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60">
                    {Object.entries(comparisonReport.matrix).map(([rowKey, rowData]) => (
                      <tr key={rowKey} className="hover:bg-slate-800/30">
                        <td className="py-3 px-4 font-bold text-slate-300 capitalize">{rowKey.replace(/_/g, ' ')}</td>
                        {rowData.values.map((val, idx) => (
                          <td
                            key={idx}
                            className={`py-3 px-4 text-slate-200 ${
                              rowData.best_indices.includes(idx) ? 'font-bold text-emerald-400' : ''
                            }`}
                          >
                            {String(val ?? '-')}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
