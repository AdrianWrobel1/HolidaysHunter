'use client';

import React, { useState } from 'react';
import { FilterOptionsResponse, OfferQueryParams } from '@/types/api';
import { Search, SlidersHorizontal, RotateCcw, ArrowUpDown } from 'lucide-react';
import { DateRangePicker } from './DateRangePicker';

interface FilterBarProps {
  filters: FilterOptionsResponse | null;
  params: OfferQueryParams;
  onChange: (newParams: OfferQueryParams) => void;
  onReset: () => void;
}

export const FilterBar: React.FC<FilterBarProps> = ({
  filters,
  params,
  onChange,
  onReset,
}) => {
  const [isOpen, setIsOpen] = useState(false);

  const handleInputChange = (key: keyof OfferQueryParams, value: any) => {
    onChange({
      ...params,
      [key]: value === '' ? undefined : value,
      page: 1, // reset page on filter change
    });
  };

  return (
    <div className="w-full bg-slate-900/80 border border-slate-800 backdrop-blur-xl rounded-2xl p-4 shadow-xl space-y-4">
      {/* Primary Bar (Search input + Sort + Filter Toggle) */}
      <div className="flex flex-col md:flex-row gap-3 items-center justify-between">
        {/* Search Field */}
        <div className="relative flex-1 w-full">
          <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
          <input
            type="text"
            placeholder="Szukaj po nazwie hotelu, kraju, regionie..."
            value={params.search || ''}
            onChange={(e) => handleInputChange('search', e.target.value)}
            className="w-full pl-10 pr-4 py-2.5 rounded-xl bg-slate-800/80 border border-slate-700/80 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-indigo-500 transition-colors"
          />
        </div>

        {/* Sort & Quick Controls */}
        <div className="flex items-center gap-3 w-full md:w-auto justify-between md:justify-end">
          <div className="flex items-center gap-2">
            <ArrowUpDown className="w-4 h-4 text-slate-400" />
            <select
              value={params.sort_by || 'price_per_person'}
              onChange={(e) => handleInputChange('sort_by', e.target.value)}
              className="bg-slate-800/80 border border-slate-700/80 text-xs text-slate-200 px-3 py-2 rounded-xl focus:outline-none focus:border-indigo-500 cursor-pointer"
            >
              <option value="price_per_person">Cena (od najniższej)</option>
              <option value="travel_score">Travel Score (najwyższy)</option>
              <option value="departure_date">Data wylotu</option>
              <option value="hotel_stars">Gwiazdki hotelu</option>
              <option value="duration_nights">Długość wyjazdu</option>
            </select>

            <select
              value={params.sort_order || 'asc'}
              onChange={(e) => handleInputChange('sort_order', e.target.value as 'asc' | 'desc')}
              className="bg-slate-800/80 border border-slate-700/80 text-xs text-slate-200 px-3 py-2 rounded-xl focus:outline-none focus:border-indigo-500 cursor-pointer"
            >
              <option value="asc">Rosnąco</option>
              <option value="desc">Malejąco</option>
            </select>
          </div>

          <button
            onClick={() => setIsOpen(!isOpen)}
            className={`flex items-center gap-2 px-3.5 py-2 rounded-xl text-xs font-semibold border transition-all ${
              isOpen
                ? 'bg-indigo-600 border-indigo-500 text-white shadow-lg shadow-indigo-600/20'
                : 'bg-slate-800 border-slate-700 text-slate-300 hover:bg-slate-700'
            }`}
          >
            <SlidersHorizontal className="w-3.5 h-3.5" />
            <span>Filtry</span>
          </button>
        </div>
      </div>

      {/* Expandable Advanced Filters Drawer */}
      {isOpen && (
        <div className="pt-4 border-t border-slate-800/80 grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-4 animate-fadeIn text-xs">
          {/* Date Range Picker */}
          <div>
            <DateRangePicker
              dateFrom={params.date_from}
              dateTo={params.date_to}
              onChange={(df, dt) => {
                onChange({
                  ...params,
                  date_from: df,
                  date_to: dt,
                  page: 1,
                });
              }}
            />
          </div>

          {/* Country */}
          <div>
            <label className="block text-slate-400 font-medium mb-1">Kraj</label>
            <select
              value={params.country || ''}
              onChange={(e) => handleInputChange('country', e.target.value)}
              className="w-full bg-slate-800 border border-slate-700 text-slate-200 p-2.5 rounded-xl focus:border-indigo-500"
            >
              <option value="">Wszystkie kraje</option>
              {filters?.countries.map((c) => (
                <option key={c} value={c}>
                  {c}
                </option>
              ))}
            </select>
          </div>

          {/* Departure City */}
          <div>
            <label className="block text-slate-400 font-medium mb-1">Wylot z</label>
            <select
              value={params.departure_city || ''}
              onChange={(e) => handleInputChange('departure_city', e.target.value)}
              className="w-full bg-slate-800 border border-slate-700 text-slate-200 p-2.5 rounded-xl focus:border-indigo-500"
            >
              <option value="">Wszystkie miasta</option>
              {filters?.departure_cities.map((city) => (
                <option key={city} value={city}>
                  {city}
                </option>
              ))}
            </select>
          </div>

          {/* Provider */}
          <div>
            <label className="block text-slate-400 font-medium mb-1">Biuro podróży</label>
            <select
              value={params.provider || ''}
              onChange={(e) => handleInputChange('provider', e.target.value)}
              className="w-full bg-slate-800 border border-slate-700 text-slate-200 p-2.5 rounded-xl focus:border-indigo-500"
            >
              <option value="">Wzyscy operatorzy</option>
              {filters?.providers.map((p) => (
                <option key={p} value={p}>
                  {p.toUpperCase()}
                </option>
              ))}
            </select>
          </div>

          {/* Meal Type */}
          <div>
            <label className="block text-slate-400 font-medium mb-1">Wyżywienie</label>
            <select
              value={params.meal_type || ''}
              onChange={(e) => handleInputChange('meal_type', e.target.value)}
              className="w-full bg-slate-800 border border-slate-700 text-slate-200 p-2.5 rounded-xl focus:border-indigo-500"
            >
              <option value="">Wszystkie opcje</option>
              {filters?.meal_types.map((m) => (
                <option key={m} value={m}>
                  {m}
                </option>
              ))}
            </select>
          </div>

          {/* Max Price */}
          <div>
            <label className="block text-slate-400 font-medium mb-1">Cena max / os. (PLN)</label>
            <input
              type="number"
              placeholder="np. 3000"
              value={params.price_max || ''}
              onChange={(e) => handleInputChange('price_max', e.target.value ? Number(e.target.value) : '')}
              className="w-full bg-slate-800 border border-slate-700 text-slate-200 p-2.5 rounded-xl focus:border-indigo-500"
            />
          </div>

          {/* Min Stars */}
          <div>
            <label className="block text-slate-400 font-medium mb-1">Min. gwiazdki hotelu</label>
            <select
              value={params.hotel_stars_min || ''}
              onChange={(e) => handleInputChange('hotel_stars_min', e.target.value ? Number(e.target.value) : '')}
              className="w-full bg-slate-800 border border-slate-700 text-slate-200 p-2.5 rounded-xl focus:border-indigo-500"
            >
              <option value="">Dowolne</option>
              <option value="3">3 ★ i więcej</option>
              <option value="4">4 ★ i więcej</option>
              <option value="5">5 ★ (Luksus)</option>
            </select>
          </div>

          {/* Min / Max Nights */}
          <div>
            <label className="block text-slate-400 font-medium mb-1">Długość (noce)</label>
            <div className="flex items-center gap-2">
              <input
                type="number"
                placeholder="Od"
                value={params.duration_min || ''}
                onChange={(e) => handleInputChange('duration_min', e.target.value ? Number(e.target.value) : '')}
                className="w-1/2 bg-slate-800 border border-slate-700 text-slate-200 p-2.5 rounded-xl focus:border-indigo-500"
              />
              <input
                type="number"
                placeholder="Do"
                value={params.duration_max || ''}
                onChange={(e) => handleInputChange('duration_max', e.target.value ? Number(e.target.value) : '')}
                className="w-1/2 bg-slate-800 border border-slate-700 text-slate-200 p-2.5 rounded-xl focus:border-indigo-500"
              />
            </div>
          </div>

          {/* Reset Action */}
          <div className="flex items-end">
            <button
              onClick={onReset}
              className="w-full flex items-center justify-center gap-2 p-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-rose-400 border border-slate-700 transition-colors font-semibold"
            >
              <RotateCcw className="w-3.5 h-3.5" />
              <span>Resetuj filtry</span>
            </button>
          </div>
        </div>
      )}
    </div>
  );
};
