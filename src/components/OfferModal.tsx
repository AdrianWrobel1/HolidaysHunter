'use client';

import React, { useEffect, useState } from 'react';
import { OfferDetailResponse, OfferResponse } from '@/types/api';
import { fetchOfferDetail } from '@/lib/api';
import { resolveOfferBookingUrl } from '@/lib/urlUtils';
import { PriceHistoryChart } from './PriceHistoryChart';
import { TravelScoreBadge } from './TravelScoreBadge';
import {
  X,
  MapPin,
  Calendar,
  Moon,
  Plane,
  Utensils,
  ExternalLink,
  Users,
  Clock,
  Building,
  CheckCircle2,
} from 'lucide-react';

interface OfferModalProps {
  offer: OfferResponse | null;
  onClose: () => void;
}

export const OfferModal: React.FC<OfferModalProps> = ({ offer, onClose }) => {
  const [detail, setDetail] = useState<OfferDetailResponse | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!offer) {
      setDetail(null);
      return;
    }

    setLoading(true);
    fetchOfferDetail(offer.id)
      .then(setDetail)
      .catch((err) => {
        console.error('Error fetching detail:', err);
      })
      .finally(() => setLoading(false));
  }, [offer]);

  if (!offer) return null;

  const current = detail || offer;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-md animate-fadeIn">
      <div
        className="relative w-full max-w-3xl max-h-[90vh] overflow-y-auto rounded-3xl bg-slate-900 border border-slate-800 shadow-2xl custom-scrollbar text-slate-100"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Close Button */}
        <button
          onClick={onClose}
          className="absolute top-4 right-4 z-10 p-2.5 rounded-full bg-slate-950/60 text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
        >
          <X className="w-5 h-5" />
        </button>

        {/* Hero Image & Header */}
        <div className="relative h-64 w-full bg-slate-800 overflow-hidden">
          {current.image_url ? (
            <img
              src={current.image_url}
              alt={current.hotel_name}
              className="w-full h-full object-cover"
            />
          ) : (
            <div className="w-full h-full flex items-center justify-center bg-indigo-950 text-indigo-400">
              <Building className="w-16 h-16 stroke-[1.5]" />
            </div>
          )}
          <div className="absolute inset-0 bg-gradient-to-t from-slate-900 via-slate-900/40 to-transparent" />

          <div className="absolute bottom-6 left-6 right-6 flex flex-col md:flex-row md:items-end justify-between gap-4">
            <div>
              <div className="flex items-center gap-2 text-emerald-400 text-xs font-bold uppercase tracking-wider mb-1">
                <MapPin className="w-4 h-4" />
                <span>
                  {current.country} {current.region ? `• ${current.region}` : ''} {current.city ? `(${current.city})` : ''}
                </span>
              </div>
              <h2 className="text-2xl md:text-3xl font-black text-white">{current.hotel_name}</h2>
            </div>
            <TravelScoreBadge score={current.travel_score} size="lg" />
          </div>
        </div>

        {/* Modal Body Content */}
        <div className="p-6 space-y-6">
          {/* Key Specs Grid */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            <div className="p-3 rounded-xl bg-slate-800/50 border border-slate-800 flex items-center gap-3">
              <Calendar className="w-5 h-5 text-indigo-400 shrink-0" />
              <div>
                <div className="text-[10px] text-slate-500 font-medium">Termin</div>
                <div className="text-xs font-semibold">{current.departure_date}</div>
              </div>
            </div>

            <div className="p-3 rounded-xl bg-slate-800/50 border border-slate-800 flex items-center gap-3">
              <Moon className="w-5 h-5 text-indigo-400 shrink-0" />
              <div>
                <div className="text-[10px] text-slate-500 font-medium">Długość</div>
                <div className="text-xs font-semibold">{current.duration_nights} nocy</div>
              </div>
            </div>

            <div className="p-3 rounded-xl bg-slate-800/50 border border-slate-800 flex items-center gap-3">
              <Plane className="w-5 h-5 text-indigo-400 shrink-0" />
              <div>
                <div className="text-[10px] text-slate-500 font-medium">Wylot z</div>
                <div className="text-xs font-semibold">{current.departure_city}</div>
              </div>
            </div>

            <div className="p-3 rounded-xl bg-slate-800/50 border border-slate-800 flex items-center gap-3">
              <Users className="w-5 h-5 text-indigo-400 shrink-0" />
              <div>
                <div className="text-[10px] text-slate-500 font-medium">Uczestnicy</div>
                <div className="text-xs font-semibold">
                  {current.adults} dorosłych {current.children ? `, ${current.children} dzieci` : ''}
                </div>
              </div>
            </div>
          </div>

          {/* Additional details */}
          <div className="flex flex-wrap gap-4 text-xs text-slate-300 border-t border-b border-slate-800/80 py-4">
            <div className="flex items-center gap-1.5">
              <Utensils className="w-4 h-4 text-indigo-400" />
              <span>Wyżywienie: <strong>{current.meal_type}</strong></span>
            </div>
            <div className="flex items-center gap-1.5">
              <CheckCircle2 className="w-4 h-4 text-indigo-400" />
              <span>Operator: <strong className="uppercase">{current.provider}</strong></span>
            </div>
            {detail?.days_available !== undefined && (
              <div className="flex items-center gap-1.5">
                <Clock className="w-4 h-4 text-indigo-400" />
                <span>Dostępna w systemie od: <strong>{detail.days_available} dni</strong></span>
              </div>
            )}
          </div>

          {/* Price History */}
          {loading ? (
            <div className="p-6 text-center text-slate-400 text-sm animate-pulse">
              Ładowanie historii cen...
            </div>
          ) : (
            <PriceHistoryChart
              history={detail?.price_history || []}
              currentPrice={current.price_per_person}
            />
          )}

          {/* Footer Action Bar */}
          <div className="pt-4 border-t border-slate-800 flex items-center justify-between">
            <div>
              <div className="text-xs text-slate-400">Łączna cena za wyjazd</div>
              <div className="text-2xl font-black text-emerald-400">
                {current.price_total} <span className="text-sm font-normal text-slate-400">{current.currency}</span>
              </div>
              <div className="text-xs text-slate-400">({current.price_per_person} PLN / os.)</div>
            </div>

            <a
              href={resolveOfferBookingUrl(current)}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-2 px-6 py-3 rounded-2xl bg-gradient-to-r from-indigo-600 via-indigo-500 to-indigo-600 text-white font-bold text-sm shadow-xl shadow-indigo-600/30 hover:scale-105 transition-all"
            >
              <span>Przejdź do oferty na {current.provider.toUpperCase()}</span>
              <ExternalLink className="w-4 h-4" />
            </a>
          </div>
        </div>
      </div>
    </div>
  );
};
