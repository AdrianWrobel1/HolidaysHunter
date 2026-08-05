'use client';

import React, { useState, useEffect } from 'react';
import {
  FilterOptionsResponse,
  OfferQueryParams,
  OfferResponse,
  OffersListResponse,
} from '@/types/api';
import { fetchFilterOptions, fetchOffers, fetchAlerts, fetchLiveOffers, fetchOfferDetail, deleteOffer, clearAllOffers } from '@/lib/api';
import { Header } from '@/components/Header';
import { FilterBar } from '@/components/FilterBar';
import { OfferCard } from '@/components/OfferCard';
import { OfferModal } from '@/components/OfferModal';
import { ProfilesView } from '@/components/ProfilesView';
import { AlertsView } from '@/components/AlertsView';
import { SeasonalAnalyticsView } from '@/components/SeasonalAnalyticsView';
import { Compass, ChevronLeft, ChevronRight, Sparkles, AlertCircle, CheckCircle2 } from 'lucide-react';

export default function Home() {
  const [activeTab, setActiveTab] = useState<'explorer' | 'profiles' | 'alerts' | 'seasonal'>('explorer');

  // Explorer Data State
  const [offersData, setOffersData] = useState<OffersListResponse | null>(null);
  const [filterOptions, setFilterOptions] = useState<FilterOptionsResponse | null>(null);
  const [queryParams, setQueryParams] = useState<OfferQueryParams>({
    page: 1,
    page_size: 12,
    sort_by: 'price_per_person',
    sort_order: 'asc',
  });
  const [loadingOffers, setLoadingOffers] = useState(false);
  const [fetchingLive, setFetchingLive] = useState(false);
  const [liveMessage, setLiveMessage] = useState<{ text: string; type: 'success' | 'info' } | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Selected Offer for Modal
  const [selectedOffer, setSelectedOffer] = useState<OfferResponse | null>(null);

  // Unread Alerts Count
  const [unreadCount, setUnreadCount] = useState(0);

  // Load Filter Options & Unread Alerts on mount
  useEffect(() => {
    fetchFilterOptions()
      .then(setFilterOptions)
      .catch((err) => console.warn('Could not load filter options:', err));

    fetchAlerts(true)
      .then((res) => setUnreadCount(res.total))
      .catch((err) => console.warn('Could not load unread alerts:', err));
  }, []);

  // Fetch offer by ID to open modal
  const handleSelectOfferById = async (offerId: string) => {
    try {
      const detail = await fetchOfferDetail(offerId);
      setSelectedOffer(detail);
    } catch (err) {
      console.error('Failed to load offer details:', err);
    }
  };

  const handleDeleteSingleOffer = async (offerId: string) => {
    try {
      await deleteOffer(offerId);
      setLiveMessage({ text: 'Oferta została pomyślnie usunięta z bazy danych.', type: 'success' });
      if (selectedOffer?.id === offerId) {
        setSelectedOffer(null);
      }
      const updated = await fetchOffers(queryParams);
      setOffersData(updated);
    } catch (err) {
      console.error('Failed to delete offer:', err);
      setError('Błąd podczas usuwania oferty.');
    }
  };

  const handleClearAllOffers = async () => {
    try {
      const res = await clearAllOffers();
      setLiveMessage({ text: res.message, type: 'success' });
      setSelectedOffer(null);
      const updated = await fetchOffers(queryParams);
      setOffersData(updated);
      const updatedFilters = await fetchFilterOptions();
      setFilterOptions(updatedFilters);
    } catch (err) {
      console.error('Failed to clear all offers:', err);
      setError('Błąd podczas czyszczenia bazy ofert.');
    }
  };

  // Load Offers when params change or tab switches to explorer
  useEffect(() => {
    if (activeTab !== 'explorer') return;

    setLoadingOffers(true);
    setError(null);

    fetchOffers(queryParams)
      .then((data) => {
        setOffersData(data);
      })
      .catch((err) => {
        console.error('Error fetching offers:', err);
        setError('Nie udało się połączyć z backendem API. Upewnij się, że backend uruchomiono na http://localhost:8000.');
      })
      .finally(() => setLoadingOffers(false));
  }, [queryParams, activeTab]);

  const handleResetFilters = () => {
    setQueryParams({
      page: 1,
      page_size: 12,
      sort_by: 'price_per_person',
      sort_order: 'asc',
    });
    setLiveMessage(null);
  };

  const handlePageChange = (newPage: number) => {
    setQueryParams((prev) => ({ ...prev, page: newPage }));
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const handleLoadMore = () => {
    if (offersData && offersData.page < offersData.total_pages) {
      setQueryParams((prev) => ({
        ...prev,
        page_size: (prev.page_size || 12) + 12,
      }));
    }
  };

  const handleFetchLive = async () => {
    try {
      setFetchingLive(true);
      setError(null);
      setLiveMessage(null);
      const res = await fetchLiveOffers(queryParams);
      const isInfo = res.status === 'info' || res.count === 0;
      setLiveMessage({ text: res.message, type: isInfo ? 'info' : 'success' });

      // Refresh list and filters
      const updatedOffers = await fetchOffers(queryParams);
      setOffersData(updatedOffers);

      const updatedFilters = await fetchFilterOptions();
      setFilterOptions(updatedFilters);
    } catch (err) {
      console.error('Error fetching live offers:', err);
      setError('Nie udało się pobrać danych na żywo z biur podróży.');
    } finally {
      setFetchingLive(false);
    }
  };

  return (
    <div className="min-h-screen flex flex-col bg-[#0b0f19] text-slate-100">
      <Header
        activeTab={activeTab}
        onTabChange={setActiveTab}
        unreadAlertsCount={unreadCount}
      />

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
        {activeTab === 'explorer' && (
          <div className="space-y-8 animate-fadeIn">
            {/* Hero Banner */}
            <div className="relative overflow-hidden rounded-3xl bg-gradient-to-r from-indigo-950 via-slate-900 to-slate-950 border border-slate-800 p-8 shadow-2xl">
              <div className="absolute top-0 right-0 w-96 h-96 bg-indigo-500/10 rounded-full blur-3xl pointer-events-none" />
              <div className="relative z-10 max-w-2xl space-y-3">
                <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
                  <Sparkles className="w-3.5 h-3.5" />
                  <span>Inteligentna Wyszukiwarka Okazji</span>
                </div>
                <h2 className="text-3xl sm:text-4xl font-black text-white tracking-tight">
                  Znajdź najlepsze wakacje przed wszystkimi.
                </h2>
                <p className="text-sm text-slate-300 leading-relaxed">
                  System automatycznie agreguje i normalizuje oferty z biur Itaka, TUI, Rainbow i Wakacje.pl. Przeglądaj, filtruj po kraju i regionie oraz sprawdzaj historię cen!
                </p>
              </div>
            </div>

            {/* Filter Bar */}
            <FilterBar
              filters={filterOptions}
              params={queryParams}
              onChange={setQueryParams}
              onReset={handleResetFilters}
              onFetchLive={handleFetchLive}
              fetchingLive={fetchingLive}
              onClearAll={handleClearAllOffers}
            />

            {/* Live Fetch Success / Info Banner */}
            {liveMessage && (
              <div
                className={`p-4 rounded-2xl border text-xs flex items-center gap-3 animate-fadeIn ${
                  liveMessage.type === 'info'
                    ? 'bg-amber-500/10 border-amber-500/30 text-amber-300'
                    : 'bg-emerald-500/10 border-emerald-500/30 text-emerald-300'
                }`}
              >
                {liveMessage.type === 'info' ? (
                  <AlertCircle className="w-5 h-5 shrink-0 text-amber-400" />
                ) : (
                  <CheckCircle2 className="w-5 h-5 shrink-0 text-emerald-400" />
                )}
                <span>{liveMessage.text}</span>
              </div>
            )}

            {/* Error Display */}
            {error && (
              <div className="p-4 rounded-2xl bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs flex items-center gap-3">
                <AlertCircle className="w-5 h-5 shrink-0" />
                <span>{error}</span>
              </div>
            )}

            {/* Loading Grid State */}
            {loadingOffers ? (
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
                {[...Array(6)].map((_, i) => (
                  <div
                    key={i}
                    className="h-80 rounded-2xl bg-slate-900/60 border border-slate-800 animate-pulse"
                  />
                ))}
              </div>
            ) : offersData && offersData.offers.length > 0 ? (
              <>
                {/* Results Header Info */}
                <div className="flex items-center justify-between text-xs text-slate-400">
                  <span>
                    Znaleziono <strong>{offersData.total}</strong> ofert wakacyjnych
                  </span>
                  <span>
                    Strona {offersData.page} z {offersData.total_pages}
                  </span>
                </div>

                {/* Offers Grid */}
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
                  {offersData.offers.map((offer) => (
                    <OfferCard
                      key={offer.id}
                      offer={offer}
                      onSelect={setSelectedOffer}
                      onDelete={handleDeleteSingleOffer}
                    />
                  ))}
                </div>

                {/* Load More Button */}
                {offersData.page < offersData.total_pages && (
                  <div className="flex justify-center pt-2">
                    <button
                      onClick={handleLoadMore}
                      className="px-6 py-3 rounded-2xl bg-indigo-600/90 hover:bg-indigo-500 text-white text-xs font-bold shadow-lg shadow-indigo-600/20 hover:scale-105 transition-all flex items-center gap-2"
                    >
                      <Sparkles className="w-4 h-4 text-amber-300" suppressHydrationWarning />
                      <span>Pokaż więcej ofert (+12)</span>
                    </button>
                  </div>
                )}

                {/* Pagination Controls */}
                {offersData.total_pages > 1 && (
                  <div className="flex items-center justify-center gap-3 pt-6 border-t border-slate-800">
                    <button
                      disabled={offersData.page <= 1}
                      onClick={() => handlePageChange(offersData.page - 1)}
                      className="flex items-center gap-1 px-4 py-2.5 rounded-xl bg-slate-900 border border-slate-800 text-slate-300 text-xs font-semibold hover:bg-slate-800 disabled:opacity-40 disabled:cursor-not-allowed transition-all"
                    >
                      <ChevronLeft className="w-4 h-4" />
                      <span>Poprzednia</span>
                    </button>

                    <span className="text-xs font-bold text-slate-300 px-3">
                      {offersData.page} / {offersData.total_pages}
                    </span>

                    <button
                      disabled={offersData.page >= offersData.total_pages}
                      onClick={() => handlePageChange(offersData.page + 1)}
                      className="flex items-center gap-1 px-4 py-2.5 rounded-xl bg-slate-900 border border-slate-800 text-slate-300 text-xs font-semibold hover:bg-slate-800 disabled:opacity-40 disabled:cursor-not-allowed transition-all"
                    >
                      <span>Następna</span>
                      <ChevronRight className="w-4 h-4" />
                    </button>
                  </div>
                )}
              </>
            ) : (
              !loadingOffers &&
              !error && (
                <div className="p-12 text-center rounded-3xl bg-slate-900/40 border border-slate-800 space-y-4">
                  <Compass className="w-12 h-12 text-slate-600 mx-auto stroke-[1.5]" />
                  <h3 className="text-lg font-bold text-slate-200">Brak ofert spełniających kryteria</h3>
                  <p className="text-xs text-slate-400 max-w-md mx-auto">
                    Zmień parametry wyszukiwania lub zresetuj filtry. Jeżeli baza jest pusta, kliknij "Pobierz na żywo z biur" lub uruchom import ofert.
                  </p>
                  <button
                    onClick={handleResetFilters}
                    className="px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-semibold text-xs transition-colors shadow-lg shadow-indigo-600/30"
                  >
                    Resetuj filtry
                  </button>
                </div>
              )
            )}
          </div>
        )}

        {activeTab === 'profiles' && (
          <div className="animate-fadeIn">
            <ProfilesView filterOptions={filterOptions} />
          </div>
        )}

        {activeTab === 'alerts' && (
          <div className="animate-fadeIn">
            <AlertsView onSelectOffer={handleSelectOfferById} />
          </div>
        )}

        {activeTab === 'seasonal' && (
          <div className="animate-fadeIn">
            <SeasonalAnalyticsView />
          </div>
        )}
      </main>

      {/* Offer Details Modal */}
      <OfferModal
        offer={selectedOffer}
        onClose={() => setSelectedOffer(null)}
        onDelete={handleDeleteSingleOffer}
      />
    </div>
  );
}
