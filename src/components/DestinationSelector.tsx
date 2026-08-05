'use client';

import React, { useState, useMemo, useRef, useEffect } from 'react';
import { ChevronDown, ChevronRight, Search, X, Check, MapPin } from 'lucide-react';

interface DestinationSelectorProps {
  countriesCatalog?: string[];
  countryRegionsMap?: Record<string, string[]>;
  selectedCountries: string[];
  selectedRegions: string[];
  onCountriesChange: (countries: string[]) => void;
  onRegionsChange: (regions: string[]) => void;
}

interface CategoryGroup {
  name: string;
  countries: string[];
}

const CATEGORY_GROUPS: CategoryGroup[] = [
  {
    name: 'TOP 5',
    countries: ['Egipt', 'Grecja', 'Hiszpania', 'Portugalia', 'Turcja'],
  },
  {
    name: 'TOP Egzotyka',
    countries: [
      'Dominikana',
      'Meksyk',
      'Malediwy',
      'Sri Lanka',
      'Tanzania',
      'Tajlandia',
      'Zielony Przylądek',
    ],
  },
  {
    name: 'Popularne',
    countries: [
      'Albania',
      'Bułgaria',
      'Chorwacja',
      'Cypr',
      'Czarnogóra',
      'Gruzja',
      'Francja',
      'Macedonia',
      'Malta',
      'Maroko',
      'Tunezja',
      'Włochy',
    ],
  },
];

export const DestinationSelector: React.FC<DestinationSelectorProps> = ({
  countriesCatalog = [],
  countryRegionsMap = {},
  selectedCountries,
  selectedRegions,
  onCountriesChange,
  onRegionsChange,
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const [search, setSearch] = useState('');
  const [expandedCountries, setExpandedCountries] = useState<Record<string, boolean>>({});
  const containerRef = useRef<HTMLDivElement>(null);

  // Close dropdown on click outside
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setIsOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const toggleExpand = (country: string, e: React.MouseEvent) => {
    e.stopPropagation();
    setExpandedCountries((prev) => ({
      ...prev,
      [country]: !prev[country],
    }));
  };

  const handleCountryToggle = (country: string) => {
    let nextCountries: string[];
    if (selectedCountries.includes(country)) {
      nextCountries = selectedCountries.filter((c) => c !== country);
      // Remove regions belonging to unselected country
      const knownRegions = countryRegionsMap[country] || [];
      if (knownRegions.length > 0) {
        onRegionsChange(selectedRegions.filter((r) => !knownRegions.includes(r)));
      }
    } else {
      nextCountries = [...selectedCountries, country];
    }
    onCountriesChange(nextCountries);
  };

  const handleRegionToggle = (country: string, region: string) => {
    let nextRegions: string[];
    if (selectedRegions.includes(region)) {
      nextRegions = selectedRegions.filter((r) => r !== region);
    } else {
      nextRegions = [...selectedRegions, region];
      // Automatically select parent country if not already selected
      if (!selectedCountries.includes(country)) {
        onCountriesChange([...selectedCountries, country]);
      }
    }
    onRegionsChange(nextRegions);
  };

  // Group all available countries
  const categorized = useMemo(() => {
    const assigned = new Set<string>();
    const result: { name: string; countries: string[] }[] = [];

    CATEGORY_GROUPS.forEach((group) => {
      const matched = group.countries.filter((c) => {
        const inCatalog = countriesCatalog.some((cat) => cat.toLowerCase() === c.toLowerCase());
        return inCatalog || group.countries.includes(c);
      });
      matched.forEach((m) => assigned.add(m.toLowerCase()));
      result.push({ name: group.name, countries: matched });
    });

    // Other remaining countries
    const others = countriesCatalog.filter((c) => !assigned.has(c.toLowerCase())).sort();
    if (others.length > 0) {
      result.push({ name: 'Pozostałe Kierunki', countries: others });
    }

    return result;
  }, [countriesCatalog]);

  // Filter categories by search term
  const filteredCategories = useMemo(() => {
    if (!search.trim()) return categorized;

    const q = search.toLowerCase().trim();
    return categorized
      .map((cat) => {
        const matchingCountries = cat.countries.filter((c) => {
          const countryMatch = c.toLowerCase().includes(q);
          const regions = countryRegionsMap[c] || [];
          const regionMatch = regions.some((r) => r.toLowerCase().includes(q));
          return countryMatch || regionMatch;
        });
        return { ...cat, countries: matchingCountries };
      })
      .filter((cat) => cat.countries.length > 0);
  }, [categorized, search, countryRegionsMap]);

  const totalSelectedCount = selectedCountries.length + selectedRegions.length;

  const triggerLabel = useMemo(() => {
    if (totalSelectedCount === 0) return 'Wybierz region';
    if (selectedCountries.length === 1 && selectedRegions.length === 0) return selectedCountries[0];
    return `Wybrano kierunki (${totalSelectedCount})`;
  }, [selectedCountries, selectedRegions, totalSelectedCount]);

  return (
    <div ref={containerRef} className="relative w-full text-xs">
      {/* Trigger Button */}
      <label className="block text-slate-400 font-semibold mb-1">Dokąd lecisz?</label>
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className={`w-full flex items-center justify-between px-3.5 py-2.5 rounded-xl border transition-all text-left font-medium ${
          totalSelectedCount > 0
            ? 'bg-slate-800 border-indigo-500 text-indigo-300 shadow-md shadow-indigo-500/10'
            : 'bg-slate-800/80 border-slate-700 text-slate-200 hover:bg-slate-700'
        }`}
      >
        <div className="flex items-center gap-2 truncate">
          <MapPin className="w-4 h-4 text-indigo-400 shrink-0" />
          <span className="truncate">{triggerLabel}</span>
        </div>
        <ChevronDown
          className={`w-4 h-4 text-slate-400 transition-transform shrink-0 ${
            isOpen ? 'rotate-180 text-indigo-400' : ''
          }`}
        />
      </button>

      {/* Dropdown Menu */}
      {isOpen && (
        <div className="absolute left-0 top-full mt-1.5 w-72 sm:w-80 max-h-96 z-50 rounded-2xl bg-slate-900 border border-slate-700 shadow-2xl backdrop-blur-xl flex flex-col overflow-hidden animate-fadeIn">
          {/* Inner Search Box */}
          <div className="p-2.5 border-b border-slate-800 flex items-center gap-2 bg-slate-950/60">
            <Search className="w-4 h-4 text-slate-400 shrink-0" />
            <input
              type="text"
              placeholder="Wpisz kierunek..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full bg-transparent text-slate-100 placeholder-slate-500 text-xs focus:outline-none"
              autoFocus
            />
            {search && (
              <button
                type="button"
                onClick={() => setSearch('')}
                className="p-1 hover:text-slate-200 text-slate-500"
              >
                <X className="w-3.5 h-3.5" />
              </button>
            )}
          </div>

          {/* Quick Clear Bar */}
          {totalSelectedCount > 0 && (
            <div className="px-3 py-1.5 bg-indigo-950/50 border-b border-indigo-900/50 flex items-center justify-between text-[11px]">
              <span className="text-indigo-300 font-semibold">Zaznaczone: {totalSelectedCount}</span>
              <button
                type="button"
                onClick={() => {
                  onCountriesChange([]);
                  onRegionsChange([]);
                }}
                className="text-rose-400 hover:text-rose-300 font-semibold"
              >
                Wyczyść wszystko
              </button>
            </div>
          )}

          {/* Scrollable Categories List */}
          <div className="flex-1 overflow-y-auto p-2 space-y-3 custom-scrollbar max-h-80">
            {filteredCategories.length === 0 ? (
              <div className="p-4 text-center text-slate-500 italic">Brak wyników dla "{search}"</div>
            ) : (
              filteredCategories.map((group) => (
                <div key={group.name} className="space-y-1">
                  <div className="px-2 py-1 text-[11px] font-bold text-indigo-400 uppercase tracking-wider">
                    {group.name}
                  </div>

                  {group.countries.map((c) => {
                    const isCountrySelected = selectedCountries.includes(c);
                    const regions = countryRegionsMap[c] || [];
                    const isExpanded = Boolean(expandedCountries[c] || search.trim());
                    const hasRegions = regions.length > 0;

                    return (
                      <div key={c} className="space-y-0.5">
                        {/* Country Item Row */}
                        <div
                          onClick={() => handleCountryToggle(c)}
                          className={`flex items-center justify-between px-2.5 py-1.5 rounded-lg cursor-pointer transition-colors ${
                            isCountrySelected
                              ? 'bg-indigo-950/60 text-indigo-200 font-semibold'
                              : 'hover:bg-slate-800 text-slate-300'
                          }`}
                        >
                          <div className="flex items-center gap-2 truncate">
                            <div
                              className={`w-4 h-4 rounded border flex items-center justify-center transition-colors ${
                                isCountrySelected
                                  ? 'bg-indigo-600 border-indigo-500 text-white'
                                  : 'border-slate-600 bg-slate-800'
                              }`}
                            >
                              {isCountrySelected && <Check className="w-3 h-3 stroke-[3]" />}
                            </div>
                            <span className="truncate">{c}</span>
                          </div>

                          {hasRegions && (
                            <button
                              type="button"
                              onClick={(e) => toggleExpand(c, e)}
                              className="p-1 text-slate-400 hover:text-slate-200 rounded"
                            >
                              {isExpanded ? (
                                <ChevronDown className="w-3.5 h-3.5 text-indigo-400" />
                              ) : (
                                <ChevronRight className="w-3.5 h-3.5" />
                              )}
                            </button>
                          )}
                        </div>

                        {/* Nested Sub-Regions */}
                        {hasRegions && isExpanded && (
                          <div className="pl-6 pr-1 space-y-0.5 border-l-2 border-slate-800 my-0.5">
                            {regions.map((r) => {
                              const isRegionSelected = selectedRegions.includes(r);
                              return (
                                <div
                                  key={r}
                                  onClick={() => handleRegionToggle(c, r)}
                                  className={`flex items-center gap-2 px-2 py-1 rounded cursor-pointer text-[11px] transition-colors ${
                                    isRegionSelected
                                      ? 'bg-teal-950/60 text-teal-300 font-semibold'
                                      : 'hover:bg-slate-800/80 text-slate-400'
                                  }`}
                                >
                                  <div
                                    className={`w-3.5 h-3.5 rounded border flex items-center justify-center transition-colors ${
                                      isRegionSelected
                                        ? 'bg-teal-600 border-teal-500 text-white'
                                        : 'border-slate-700 bg-slate-800'
                                    }`}
                                  >
                                    {isRegionSelected && <Check className="w-2.5 h-2.5 stroke-[3]" />}
                                  </div>
                                  <span className="truncate">{r}</span>
                                </div>
                              );
                            })}
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              ))
            )}
          </div>
        </div>
      )}
    </div>
  );
};
