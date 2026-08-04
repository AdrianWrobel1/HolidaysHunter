'use client';

import React from 'react';
import { OfferResponse } from '@/types/api';
import { TravelScoreBadge } from './TravelScoreBadge';
import {
  MapPin,
  Calendar,
  Moon,
  Plane,
  Utensils,
  ExternalLink,
  Star,
  Eye,
} from 'lucide-react';

import { resolveOfferBookingUrl } from '@/lib/urlUtils';

interface OfferCardProps {
  offer: OfferResponse;
  onSelect: (offer: OfferResponse) => void;
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

export const OfferCard: React.FC<OfferCardProps> = ({ offer, onSelect }) => {
  const providerInfo = PROVIDER_NAMES[offer.provider] || {
    label: offer.provider,
    bg: 'bg-slate-800 text-slate-300 border-slate-700',
  };

  const mealText = MEAL_LABELS[offer.meal_type] || offer.meal_type;

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
          <span
            className={`px-2.5 py-1 rounded-full text-xs font-bold border backdrop-blur-md shadow-md ${providerInfo.bg}`}
          >
            {providerInfo.label}
          </span>
          <div className="pointer-events-auto">
            <TravelScoreBadge score={offer.travel_score} size="sm" />
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
          {/* Stars & Rating */}
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
                Ocena {offer.hotel_rating}/10
              </span>
            )}
          </div>

          {/* Departure & Nights */}
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
              <Plane className="w-3.5 h-3.5 text-indigo-400 shrink-0" />
              <span className="truncate">Z: {offer.departure_city}</span>
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
            <button
              onClick={() => onSelect(offer)}
              className="p-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 transition-colors border border-slate-700"
              title="Szczegóły & Historia Cen"
            >
              <Eye className="w-4 h-4" />
            </button>
            <a
              href={resolveOfferBookingUrl(offer)}
              target="_blank"
              rel="noopener noreferrer"
              onClick={(e) => e.stopPropagation()}
              className="inline-flex items-center gap-1.5 px-3 py-2 rounded-xl bg-gradient-to-r from-indigo-600 to-indigo-500 hover:from-indigo-500 hover:to-indigo-400 text-white font-medium text-xs shadow-lg shadow-indigo-600/20 transition-all hover:scale-105"
            >
              <span>Rezerwuj</span>
              <ExternalLink className="w-3.5 h-3.5" />
            </a>
          </div>
        </div>
      </div>
    </div>
  );
};
