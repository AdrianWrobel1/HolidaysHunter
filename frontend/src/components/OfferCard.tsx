'use client';

import React from 'react';
import { OfferResponse } from '@/types/api';
import {
  MapPin,
  Calendar,
  Moon,
  Plane,
  Car,
  Bus,
  Train,
  Ship,
  Utensils,
  ExternalLink,
  Star,
  Eye,
  Trash2,
  Zap,
} from 'lucide-react';

import { resolveOfferBookingUrl } from '@/lib/urlUtils';

interface OfferCardProps {
  offer: OfferResponse;
  onSelect: (offer: OfferResponse) => void;
  onDelete?: (id: string) => void;
}

const PROVIDER_NAMES: Record<string, { label: string; bg: string }> = {
  itaka: { label: 'Itaka', bg: 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30' },
  tui: { label: 'TUI', bg: 'bg-red-500/20 text-red-400 border-red-500/30' },
  rainbow: { label: 'Rainbow', bg: 'bg-blue-500/20 text-blue-400 border-blue-500/30' },
  wakacje_pl: { label: 'Wakacje.pl', bg: 'bg-teal-500/20 text-teal-400 border-teal-500/30' },
};

const MEAL_LABELS: Record<string, string> = {
  all_inclusive: 'All Inclusive',
  full_board: 'Pełne Wyżywienie (FB)',
  half_board: 'Śniadania i Kolacje (HB)',
  bed_and_breakfast: 'Śniadania (BB)',
  self_catering: 'We własnym zakresie (OV)',
};

export const OfferCard: React.FC<OfferCardProps> = ({ offer, onSelect, onDelete }) => {
  const providerInfo = PROVIDER_NAMES[offer.provider] || {
    label: offer.provider,
    bg: 'bg-slate-800 text-slate-300 border-slate-700',
  };

  const mealText = MEAL_LABELS[offer.meal_type] || offer.meal_type;

  // Transport Icon & Label resolution
  const renderTransportIcon = () => {
    const t = String(offer.transport_type || 'flight').toLowerCase();
    if (t === 'self_transport' || t === 'own') {
      return (
        <span className="flex items-center gap-1 text-amber-300">
          <Car className="w-3.5 h-3.5" />
          <span className="truncate">Dojazd własny</span>
        </span>
      );
    }
    if (t === 'bus') {
      return (
        <span className="flex items-center gap-1 text-sky-300">
          <Bus className="w-3.5 h-3.5" />
          <span className="truncate">Autokar</span>
        </span>
      );
    }
    if (t === 'train') {
      return (
        <span className="flex items-center gap-1 text-emerald-300">
          <Train className="w-3.5 h-3.5" />
          <span className="truncate">Pociąg</span>
        </span>
      );
    }
    if (t === 'cruise') {
      return (
        <span className="flex items-center gap-1 text-purple-300">
          <Ship className="w-3.5 h-3.5" />
          <span className="truncate">Rejs</span>
        </span>
      );
    }
    return (
      <span className="flex items-center gap-1 text-indigo-300">
        <Plane className="w-3.5 h-3.5" />
        <span className="truncate">Z: {offer.departure_city}</span>
      </span>
    );
  };

  const dealScoreVal = offer.travel_score || 75;

  return (
    <div className="group relative flex flex-col rounded-2xl bg-slate-900/60 border border-slate-800/80 backdrop-blur-md overflow-hidden hover:border-slate-700 hover:shadow-2xl hover:shadow-indigo-500/10 transition-all duration-300">
      {/* Image Container */}
      <div className="relative h-48 w-full bg-slate-800 overflow-hidden">
        {offer.image_url ? (
          <img
            src={offer.image_url}
            alt={offer.hotel_name}
            className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
            loading="lazy"
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center bg-gradient-to-br from-slate-800 to-indigo-950 text-slate-600">
            <MapPin className="w-12 h-12 stroke-[1.5]" />
          </div>
        )}

        {/* Gradient Overlay */}
        <div className="absolute inset-0 bg-gradient-to-t from-slate-950 via-transparent to-black/30" />

        {/* Top Badges */}
        <div className="absolute top-3 left-3 right-3 flex items-center justify-between pointer-events-none">
          <div className="flex items-center gap-1.5">
            <span
              className={`px-2.5 py-1 rounded-full text-xs font-bold border backdrop-blur-md shadow-md ${providerInfo.bg}`}
            >
              {providerInfo.label}
            </span>
            <span className="px-2.5 py-1 rounded-full text-xs font-bold border border-slate-700 bg-slate-900/90 backdrop-blur-md shadow-md">
              {renderTransportIcon()}
            </span>
          </div>
          
          {/* Primary Metric: Deal Score */}
          <div className="pointer-events-auto flex items-center gap-1.5 px-3 py-1 rounded-full bg-purple-950/80 border border-purple-500/40 text-purple-200 text-xs font-black shadow-lg backdrop-blur-md">
            <Zap className="w-3.5 h-3.5 text-amber-400 fill-amber-400" />
            <span>Deal Score {dealScoreVal}</span>
          </div>
        </div>

        {/* Location & Title overlay */}
        <div className="absolute bottom-3 left-3 right-3">
          <div className="flex items-center gap-1.5 text-emerald-400 text-xs font-semibold uppercase tracking-wider mb-1">
            <MapPin className="w-3.5 h-3.5" />
            <span>
              {offer.country} {offer.region ? `• ${offer.region}` : ''}
            </span>
          </div>
          <h3 className="text-base font-bold text-white line-clamp-1 group-hover:text-indigo-300 transition-colors">
            {offer.hotel_name}
          </h3>
        </div>
      </div>

      {/* Details Body */}
      <div className="p-4 flex-1 flex flex-col justify-between space-y-4">
        <div className="space-y-2.5 text-xs text-slate-300">
          {/* Stars & Explicit Guest/Hotel Rating */}
          <div className="flex items-center justify-between border-b border-slate-800/60 pb-2.5">
            <div className="flex items-center gap-1 text-amber-400">
              {offer.hotel_stars ? (
                <>
                  <Star className="w-3.5 h-3.5 fill-amber-400" />
                  <span className="font-semibold text-slate-200">{offer.hotel_stars} / 5</span>
                </>
              ) : (
                <span className="text-slate-500">Brak gwiazdek</span>
              )}
            </div>
            {offer.hotel_rating && (
              <span className="px-2 py-0.5 rounded bg-indigo-500/20 text-indigo-300 font-bold border border-indigo-500/30">
                Hotel Rating {offer.hotel_rating}/10
              </span>
            )}
          </div>

          {/* Departure, Nights, Transport, Meal */}
          <div className="grid grid-cols-2 gap-2 text-slate-400">
            <div className="flex items-center gap-1.5">
              <Calendar className="w-3.5 h-3.5 text-indigo-400 shrink-0" />
              <span className="truncate">{offer.departure_date}</span>
            </div>
            <div className="flex items-center gap-1.5">
              <Moon className="w-3.5 h-3.5 text-indigo-400 shrink-0" />
              <span>{offer.duration_nights} nocy</span>
            </div>
            <div className="flex items-center gap-1.5">
              {renderTransportIcon()}
            </div>
            <div className="flex items-center gap-1.5">
              <Utensils className="w-3.5 h-3.5 text-indigo-400 shrink-0" />
              <span className="truncate">{mealText}</span>
            </div>
          </div>
        </div>

        {/* Pricing Footer & Actions */}
        <div className="pt-3 border-t border-slate-800 flex items-center justify-between">
          <div>
            <div className="text-[10px] uppercase text-slate-500 font-medium">Cena za osobę</div>
            <div className="text-xl font-black text-emerald-400 tracking-tight">
              {offer.price_per_person} <span className="text-xs font-normal text-emerald-500">{offer.currency}</span>
            </div>
          </div>

          <div className="flex items-center gap-2">
            {onDelete && (
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  onDelete(offer.id);
                }}
                className="p-2 rounded-xl bg-slate-800 hover:bg-rose-900/40 text-slate-400 hover:text-rose-300 transition-colors border border-slate-700 hover:border-rose-700/50"
                title="Usuń tę ofertę z bazy"
              >
                <Trash2 className="w-4 h-4" />
              </button>
            )}
            <button
              onClick={() => onSelect(offer)}
              className="p-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 transition-colors border border-slate-700"
              title="Szczegóły & Historia Cen"
            >
              <Eye className="w-4 h-4" />
            </button>
            {(() => {
              const bookingUrl = resolveOfferBookingUrl(offer);
              return bookingUrl ? (
                <a
                  href={bookingUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  onClick={(e) => e.stopPropagation()}
                  className="inline-flex items-center gap-1.5 px-3 py-2 rounded-xl bg-gradient-to-r from-indigo-600 to-indigo-500 hover:from-indigo-500 hover:to-indigo-400 text-white font-medium text-xs shadow-lg shadow-indigo-600/20 transition-all hover:scale-105"
                >
                  <span>Rezerwuj</span>
                  <ExternalLink className="w-3.5 h-3.5" />
                </a>
              ) : (
                <span
                  onClick={(e) => e.stopPropagation()}
                  className="inline-flex items-center gap-1.5 px-3 py-2 rounded-xl bg-slate-800 text-slate-500 font-medium text-xs cursor-not-allowed opacity-60"
                  title="Brak bezpośredniego linku do oferty u operatora"
                >
                  <span>Brak linku</span>
                </span>
              );
            })()}
          </div>
        </div>
      </div>
    </div>
  );
};
