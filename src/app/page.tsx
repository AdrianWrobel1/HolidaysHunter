'use client';

import React, { useState, useEffect } from 'react';
import {
  FilterOptionsResponse,
  OfferQueryParams,
  OfferResponse,
  OffersListResponse,
} from '@/types/api';
import { fetchFilterOptions, fetchOffers, fetchAlerts } from '@/lib/api';
import { Header } from '@/components/Header';
import { FilterBar } from '@/components/FilterBar';
import { OfferCard } from '@/components/OfferCard';
import { OfferModal } from '@/components/OfferModal';
import { ProfilesView } from '@/components/ProfilesView';
import { AlertsView } from '@/components/AlertsView';
import { Compass, ChevronLeft, ChevronRight, Sparkles, AlertCircle } from 'lucide-react';

export default function Home() {
  const [activeTab, setActiveTab] = useState<'explorer' | 'profiles' | 'alerts'>('explorer');

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
  };

  const handlePageChange = (newPage: number) => {
    setQueryParams((prev) => ({ ...prev, page: newPage }));
    window.scrollTo({ top: 0, behavior: 'smooth' });
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
                  System automatycznie agreguje i normalizuje oferty z biur Itaka, TUI, Rainbow i Wakacje.pl. Przeglądaj, filtruj i sprawdzaj historię cen!
                </p>
              </div>
            </div>

            {/* Filter Bar */}
            <FilterBar
              filters={filterOptions}
              params={queryParams}
              onChange={setQueryParams}
              onReset={handleResetFilters}
            />

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
                    />
                  ))}
                </div>

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
                    Zmień parametry wyszukiwania lub zresetuj filtry. Jeżeli baza jest pusta, uruchom skrypt importu ofert w backendzie.
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
            <AlertsView />
          </div>
        )}
      </main>

      {/* Offer Details Modal */}
      <OfferModal
        offer={selectedOffer}
        onClose={() => setSelectedOffer(null)}
      />
    </div>
  );
}
