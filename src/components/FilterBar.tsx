'use client';

import React, { useState, useMemo } from 'react';
import { FilterOptionsResponse, OfferQueryParams } from '@/types/api';
import { Search, SlidersHorizontal, RotateCcw, ArrowUpDown, Zap, Check, Trash2, MapPin } from 'lucide-react';
import { DateRangePicker } from './DateRangePicker';
import { DestinationSelector } from './DestinationSelector';

interface FilterBarProps {
  filters: FilterOptionsResponse | null;
  params: OfferQueryParams;
  onChange: (newParams: OfferQueryParams) => void;
  onReset: () => void;
  onFetchLive?: () => void;
  fetchingLive?: boolean;
  onClearAll?: () => void;
}

const DEFAULT_PROVIDERS = ['itaka', 'tui', 'rainbow', 'wakacje_pl'];
const DEFAULT_COUNTRIES = [
  'Hiszpania',
  'Grecja',
  'Egipt',
  'Turcja',
  'Włochy',
  'Bułgaria',
  'Cypr',
  'Chorwacja',
  'Tunezja',
  'Dominikana',
  'Malediwy',
  'Meksyk',
];
const POPULAR_AIRPORTS = ['Warszawa', 'Katowice', 'Kraków', 'Poznań', 'Wrocław', 'Gdańsk'];

const MEAL_TYPES_CONFIG = [
  { label: 'All Inclusive', value: 'all_inclusive' },
  { label: 'Śniadania + Obiadokolacje (HB)', value: 'half_board' },
  { label: 'Śniadania (BB)', value: 'bed_and_breakfast' },
  { label: 'Trzy posiłki (FB)', value: 'full_board' },
  { label: 'Bez wyżywienia (OV)', value: 'self_catering' },
];

const HOTEL_STARS_CONFIG = [
  { label: '3 ★', value: 3 },
  { label: '4 ★', value: 4 },
  { label: '5 ★ (Luksus)', value: 5 },
];

export const FilterBar: React.FC<FilterBarProps> = ({
  filters,
  params,
  onChange,
  onReset,
  onFetchLive,
  fetchingLive,
  onClearAll,
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const [regionSearch, setRegionSearch] = useState('');

  const handleInputChange = (key: keyof OfferQueryParams, value: any) => {
    onChange({
      ...params,
      [key]: value === '' ? undefined : value,
      page: 1, // reset page on filter change
    });
  };

  const toggleMultiSelect = (
    key: 'departure_city' | 'meal_type' | 'hotel_stars' | 'country' | 'region' | 'provider',
    itemValue: string | number
  ) => {
    const current = params[key] as (string | number)[] | string | number | undefined;
    let updated: (string | number)[];
    if (Array.isArray(current)) {
      if (current.includes(itemValue)) {
        updated = current.filter((x) => x !== itemValue);
      } else {
        updated = [...current, itemValue];
      }
    } else if (current !== undefined && current !== null && (current as any) !== '') {
      updated = current === itemValue ? [] : [current, itemValue];
    } else {
      updated = [itemValue];
    }

    // If country changed, also reset region selection if it no longer applies
    if (key === 'country') {
      onChange({
        ...params,
        country: updated.length > 0 ? (updated as string[]) : undefined,
        region: undefined,
        page: 1,
      });
      return;
    }

    handleInputChange(key, updated.length > 0 ? updated : undefined);
  };

  const isSelected = (
    key: 'departure_city' | 'meal_type' | 'hotel_stars' | 'country' | 'region' | 'provider',
    itemValue: string | number
  ) => {
    const current = params[key] as (string | number)[] | string | number | undefined;
    if (Array.isArray(current)) {
      return current.includes(itemValue);
    }
    return current === itemValue;
  };

  // Compute available providers (merge DB & default catalog)
  const availableProviders = useMemo(() => {
    const set = new Set<string>(filters?.providers || []);
    DEFAULT_PROVIDERS.forEach((p) => set.add(p));
    return Array.from(set).sort();
  }, [filters?.providers]);

  // Compute available countries (merge DB & default catalog)
  const availableCountries = useMemo(() => {
    const set = new Set<string>(filters?.countries || []);
    DEFAULT_COUNTRIES.forEach((c) => set.add(c));
    return Array.from(set).sort();
  }, [filters?.countries]);

  // Selected countries array
  const selectedCountries = useMemo(() => {
    if (!params.country) return [];
    return Array.isArray(params.country) ? params.country : [params.country];
  }, [params.country]);

  // Compute available regions linked specifically to selected countries
  const availableRegions = useMemo(() => {
    if (selectedCountries.length > 0) {
      if (!filters?.country_regions) return [];
      const crMap = filters.country_regions;
      const matched = selectedCountries.flatMap((c) => {
        if (!c) return [];
        const norm = String(c).trim().toLowerCase();
        for (const [key, val] of Object.entries(crMap)) {
          if (key.trim().toLowerCase() === norm) {
            return val;
          }
        }
        return crMap[c] || [];
      });
      return Array.from(new Set(matched)).sort();
    }
    return filters?.regions || [];
  }, [selectedCountries, filters?.country_regions, filters?.regions]);

  // Filtered regions by inner search input
  const filteredRegions = useMemo(() => {
    if (!regionSearch.trim()) return availableRegions;
    const query = regionSearch.toLowerCase().trim();
    return availableRegions.filter((r) => r.toLowerCase().includes(query));
  }, [availableRegions, regionSearch]);

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
        <div className="flex items-center gap-3 w-full md:w-auto justify-between md:justify-end flex-wrap">
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

          {onFetchLive && (
            <button
              onClick={onFetchLive}
              disabled={fetchingLive}
              className="flex items-center gap-1.5 px-3.5 py-2 rounded-xl text-xs font-bold bg-gradient-to-r from-amber-500 to-rose-500 text-white shadow-lg shadow-rose-500/20 hover:scale-105 transition-all disabled:opacity-50 disabled:scale-100"
              title="Pobierz najświeższe dane prosto z API biur podróży pod wybrane filtry"
            >
              <Zap className={`w-3.5 h-3.5 ${fetchingLive ? 'animate-spin' : ''}`} suppressHydrationWarning />
              <span>{fetchingLive ? 'Pobieranie...' : 'Pobierz na żywo z biur'}</span>
            </button>
          )}

          {onClearAll && (
            <button
              onClick={() => {
                if (window.confirm('Czy na pewno chcesz usunąć WSZYSTKIE oferty z bazy danych?')) {
                  onClearAll();
                }
              }}
              className="flex items-center gap-1.5 px-3 py-2 rounded-xl text-xs font-semibold bg-rose-950/70 hover:bg-rose-900 border border-rose-800 text-rose-300 transition-all"
              title="Wyczyść całą bazę ofert z bazy danych"
            >
              <Trash2 className="w-3.5 h-3.5" />
              <span>Wyczyść bazę ofert</span>
            </button>
          )}

          <button
            onClick={() => setIsOpen(!isOpen)}
            className={`flex items-center gap-2 px-3.5 py-2 rounded-xl text-xs font-semibold border transition-all ${
              isOpen
                ? 'bg-indigo-600 border-indigo-500 text-white shadow-lg shadow-indigo-600/20'
                : 'bg-slate-800 border-slate-700 text-slate-300 hover:bg-slate-700'
            }`}
          >
            <SlidersHorizontal className="w-3.5 h-3.5" />
            <span>Filtry (Multi-select)</span>
          </button>
        </div>
      </div>

      {/* Expandable Advanced Filters Drawer */}
      {isOpen && (
        <div className="pt-4 border-t border-slate-800/80 space-y-5 animate-fadeIn text-xs">
          {/* Top Filters Grid (Dates & Max Price) */}
          {/* Top Filters Grid (Destination, Dates, Travelers, Duration & Max Price) */}
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
            {/* Lastminuter-style Destination Selector */}
            <div className="lg:col-span-2">
              <DestinationSelector
                countriesCatalog={availableCountries}
                countryRegionsMap={filters?.country_regions || {}}
                selectedCountries={selectedCountries}
                selectedRegions={
                  Array.isArray(params.region)
                    ? params.region
                    : params.region
                    ? [params.region]
                    : []
                }
                onCountriesChange={(newCountries) => {
                  onChange({
                    ...params,
                    country: newCountries.length > 0 ? newCountries : undefined,
                    page: 1,
                  });
                }}
                onRegionsChange={(newRegions) => {
                  onChange({
                    ...params,
                    region: newRegions.length > 0 ? newRegions : undefined,
                    page: 1,
                  });
                }}
              />
            </div>

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

            {/* Max Price */}
            <div>
              <label className="block text-slate-400 font-semibold mb-1">Cena max / os. (PLN)</label>
              <input
                type="number"
                placeholder="np. 3000"
                value={params.price_max || ''}
                onChange={(e) => handleInputChange('price_max', e.target.value ? Number(e.target.value) : '')}
                className="w-full bg-slate-800 border border-slate-700 text-slate-200 p-2.5 rounded-xl focus:border-indigo-500"
              />
            </div>

            {/* Adults & Children Selection */}
            <div>
              <label className="block text-slate-400 font-semibold mb-1">Liczba osób (Uczestnicy)</label>
              <div className="grid grid-cols-2 gap-2">
                <div>
                  <select
                    value={params.adults ?? ''}
                    onChange={(e) => handleInputChange('adults', e.target.value ? Number(e.target.value) : '')}
                    className="w-full bg-slate-800 border border-slate-700 text-slate-200 p-2.5 rounded-xl focus:border-indigo-500"
                  >
                    <option value="">Dorosłych (dowolnie)</option>
                    <option value="1">1 dorosły</option>
                    <option value="2">2 dorosłych (domyślnie)</option>
                    <option value="3">3 dorosłych</option>
                    <option value="4">4 dorosłych</option>
                    <option value="5">5 dorosłych</option>
                  </select>
                </div>
                <div>
                  <select
                    value={params.children ?? ''}
                    onChange={(e) => handleInputChange('children', e.target.value !== '' ? Number(e.target.value) : '')}
                    className="w-full bg-slate-800 border border-slate-700 text-slate-200 p-2.5 rounded-xl focus:border-indigo-500"
                  >
                    <option value="">Dzieci (dowolnie)</option>
                    <option value="0">0 dzieci</option>
                    <option value="1">1 dziecko</option>
                    <option value="2">2 dzieci</option>
                    <option value="3">3 dzieci</option>
                  </select>
                </div>
              </div>
            </div>

            {/* Duration Range (Nights) */}
            <div>
              <label className="block text-slate-400 font-semibold mb-1">Długość pobytu (Liczba nocy)</label>
              <div className="grid grid-cols-2 gap-2">
                <input
                  type="number"
                  placeholder="Min nocy (np. 7)"
                  value={params.duration_min || ''}
                  onChange={(e) => handleInputChange('duration_min', e.target.value ? Number(e.target.value) : '')}
                  className="w-full bg-slate-800 border border-slate-700 text-slate-200 p-2.5 rounded-xl focus:border-indigo-500"
                />
                <input
                  type="number"
                  placeholder="Max nocy (np. 14)"
                  value={params.duration_max || ''}
                  onChange={(e) => handleInputChange('duration_max', e.target.value ? Number(e.target.value) : '')}
                  className="w-full bg-slate-800 border border-slate-700 text-slate-200 p-2.5 rounded-xl focus:border-indigo-500"
                />
              </div>
            </div>
          </div>

          {/* Multi-Select Sections */}
          <div className="space-y-4 pt-2 border-t border-slate-800/60">
            {/* Multi-select Provider */}
            <div>
              <label className="block text-slate-400 font-semibold mb-2">
                Biuro podróży / Operatorzy (zaznacz wiele):
              </label>
              <div className="flex flex-wrap gap-2">
                {availableProviders.map((p) => {
                  const active = isSelected('provider', p);
                  return (
                    <button
                      key={p}
                      type="button"
                      onClick={() => toggleMultiSelect('provider', p)}
                      className={`flex items-center gap-1.5 px-3 py-1.5 rounded-xl border text-xs font-semibold uppercase transition-all ${
                        active
                          ? 'bg-indigo-600 border-indigo-500 text-white shadow-md shadow-indigo-600/20'
                          : 'bg-slate-800/80 border-slate-700 text-slate-300 hover:bg-slate-700'
                      }`}
                    >
                      {active && <Check className="w-3.5 h-3.5" />}
                      <span>{p}</span>
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Multi-select Country */}
            <div>
              <label className="block text-slate-400 font-semibold mb-2">
                Kierunki / Kraje (zaznacz wiele):
              </label>
              <div className="flex flex-wrap gap-2">
                {availableCountries.map((c) => {
                  const active = isSelected('country', c);
                  return (
                    <button
                      key={c}
                      type="button"
                      onClick={() => toggleMultiSelect('country', c)}
                      className={`flex items-center gap-1.5 px-3 py-1.5 rounded-xl border text-xs font-semibold transition-all ${
                        active
                          ? 'bg-purple-600 border-purple-500 text-white shadow-md shadow-purple-600/20 font-bold'
                          : 'bg-slate-800/80 border-slate-700 text-slate-300 hover:bg-slate-700'
                      }`}
                    >
                      {active && <Check className="w-3.5 h-3.5" />}
                      <span>{c}</span>
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Multi-select Region (Hierarchical / Cascading for selected country) */}
            <div>
              <div className="flex items-center justify-between mb-2">
                <label className="text-slate-400 font-semibold flex items-center gap-1.5">
                  <MapPin className="w-3.5 h-3.5 text-teal-400" />
                  <span>
                    Regiony / Kurorty{' '}
                    {selectedCountries.length > 0 ? (
                      <span className="text-teal-300 font-bold">
                        (dla: {selectedCountries.join(', ')})
                      </span>
                    ) : (
                      '(wybierz kraj, aby zwęzić listę)'
                    )}
                    :
                  </span>
                </label>
                {availableRegions.length > 6 && (
                  <input
                    type="text"
                    placeholder="Szukaj regionu..."
                    value={regionSearch}
                    onChange={(e) => setRegionSearch(e.target.value)}
                    className="bg-slate-800 border border-slate-700 text-slate-200 px-2.5 py-1 rounded-lg text-xs w-40 focus:outline-none focus:border-teal-500"
                  />
                )}
              </div>

              {filteredRegions.length > 0 ? (
                <div className="flex flex-wrap gap-2 max-h-40 overflow-y-auto custom-scrollbar p-1 bg-slate-950/40 rounded-xl border border-slate-800/80">
                  {filteredRegions.map((r) => {
                    const active = isSelected('region', r);
                    return (
                      <button
                        key={r}
                        type="button"
                        onClick={() => toggleMultiSelect('region', r)}
                        className={`flex items-center gap-1.5 px-3 py-1.5 rounded-xl border text-xs font-semibold transition-all ${
                          active
                            ? 'bg-teal-600 border-teal-500 text-white shadow-md shadow-teal-600/20'
                            : 'bg-slate-800/80 border-slate-700 text-slate-300 hover:bg-slate-700'
                        }`}
                      >
                        {active && <Check className="w-3.5 h-3.5" />}
                        <span>{r}</span>
                      </button>
                    );
                  })}
                </div>
              ) : (
                <div className="p-3 rounded-xl bg-slate-950/30 border border-slate-800 text-slate-500 text-xs italic">
                  {selectedCountries.length > 0
                    ? `Brak zapisanych regionów w bazie dla wybranych krajów (${selectedCountries.join(', ')}). Uruchom import na żywo!`
                    : 'Brak dostępnych regionów.'}
                </div>
              )}
            </div>
          </div>

          {/* Multi-Select Sections */}
          <div className="space-y-4 pt-2 border-t border-slate-800/60">
            {/* Multi-select Departure Airports */}
            <div>
              <label className="block text-slate-400 font-semibold mb-2">
                Lotnisko wylotu (zaznacz kilka):
              </label>
              <div className="flex flex-wrap gap-2">
                {POPULAR_AIRPORTS.map((city) => {
                  const active = isSelected('departure_city', city);
                  return (
                    <button
                      key={city}
                      type="button"
                      onClick={() => toggleMultiSelect('departure_city', city)}
                      className={`flex items-center gap-1.5 px-3 py-1.5 rounded-xl border text-xs font-semibold transition-all ${
                        active
                          ? 'bg-indigo-600 border-indigo-500 text-white shadow-md shadow-indigo-600/20'
                          : 'bg-slate-800/80 border-slate-700 text-slate-300 hover:bg-slate-700'
                      }`}
                    >
                      {active && <Check className="w-3.5 h-3.5" />}
                      <span>{city}</span>
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Multi-select Meal Types */}
            <div>
              <label className="block text-slate-400 font-semibold mb-2">
                Wyżywienie (zaznacz kilka):
              </label>
              <div className="flex flex-wrap gap-2">
                {MEAL_TYPES_CONFIG.map((m) => {
                  const active = isSelected('meal_type', m.value);
                  return (
                    <button
                      key={m.value}
                      type="button"
                      onClick={() => toggleMultiSelect('meal_type', m.value)}
                      className={`flex items-center gap-1.5 px-3 py-1.5 rounded-xl border text-xs font-semibold transition-all ${
                        active
                          ? 'bg-indigo-600 border-indigo-500 text-white shadow-md shadow-indigo-600/20'
                          : 'bg-slate-800/80 border-slate-700 text-slate-300 hover:bg-slate-700'
                      }`}
                    >
                      {active && <Check className="w-3.5 h-3.5" />}
                      <span>{m.label}</span>
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Multi-select Hotel Stars */}
            <div>
              <label className="block text-slate-400 font-semibold mb-2">
                Gwiazdki hotelu (zaznacz kilka):
              </label>
              <div className="flex flex-wrap gap-2">
                {HOTEL_STARS_CONFIG.map((s) => {
                  const active = isSelected('hotel_stars', s.value);
                  return (
                    <button
                      key={s.value}
                      type="button"
                      onClick={() => toggleMultiSelect('hotel_stars', s.value)}
                      className={`flex items-center gap-1.5 px-3 py-1.5 rounded-xl border text-xs font-semibold transition-all ${
                        active
                          ? 'bg-amber-500/20 border-amber-500/50 text-amber-300 shadow-md shadow-amber-500/10 font-bold'
                          : 'bg-slate-800/80 border-slate-700 text-slate-300 hover:bg-slate-700'
                      }`}
                    >
                      {active && <Check className="w-3.5 h-3.5" />}
                      <span>{s.label}</span>
                    </button>
                  );
                })}
              </div>
            </div>
          </div>

          {/* Reset Action */}
          <div className="flex justify-end pt-2">
            <button
              onClick={onReset}
              className="flex items-center gap-2 px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-rose-400 border border-slate-700 transition-colors font-semibold"
            >
              <RotateCcw className="w-3.5 h-3.5" />
              <span>Resetuj wszystkie filtry</span>
            </button>
          </div>
        </div>
      )}
    </div>
  );
};
