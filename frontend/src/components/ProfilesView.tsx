'use client';

import React, { useState, useEffect } from 'react';
import { TravelProfile, TravelProfileCreate, FilterOptionsResponse } from '@/types/api';
import { fetchTravelProfiles, createTravelProfile, updateTravelProfile, deleteTravelProfile } from '@/lib/api';
import { Plus, Trash2, Pencil, ShieldCheck, MapPin, Calendar, DollarSign, Users, Moon, Check, X } from 'lucide-react';

interface ProfilesViewProps {
  filterOptions: FilterOptionsResponse | null;
}

const DEFAULT_POPULAR_COUNTRIES = [
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

const DEFAULT_AIRPORTS = ['Warszawa', 'Katowice', 'Kraków', 'Poznań', 'Wrocław', 'Gdańsk'];

export const ProfilesView: React.FC<ProfilesViewProps> = ({ filterOptions }) => {
  const [profiles, setProfiles] = useState<TravelProfile[]>([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [editingProfileId, setEditingProfileId] = useState<string | null>(null);

  // Form state
  const [name, setName] = useState('');
  const [selectedCountries, setSelectedCountries] = useState<string[]>([]);
  const [selectedCities, setSelectedCities] = useState<string[]>([]);
  const [selectedTransportTypes, setSelectedTransportTypes] = useState<string[]>([]);
  const [notificationPolicy, setNotificationPolicy] = useState<string>('HIGH_AND_MUST_SEE');
  const [adults, setAdults] = useState<number>(2);
  const [children, setChildren] = useState<number>(0);
  const [durationMin, setDurationMin] = useState<string>('7');
  const [durationMax, setDurationMax] = useState<string>('14');
  const [budgetMax, setBudgetMax] = useState<string>('');
  const [hotelStarsMin, setHotelStarsMin] = useState<string>('3');

  const loadProfiles = async () => {
    try {
      setLoading(true);
      const data = await fetchTravelProfiles();
      setProfiles(data);
    } catch (err) {
      console.error('Failed to load profiles:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadProfiles();
  }, []);

  const availableCountries = filterOptions?.countries || DEFAULT_POPULAR_COUNTRIES;
  const availableCities = filterOptions?.departure_cities || DEFAULT_AIRPORTS;
  const availableTransportTypes = [
    { label: '✈️ Przelot samolotem', value: 'flight' },
    { label: '🚗 Dojazd własny', value: 'self_transport' },
    { label: '🚌 Autokar', value: 'bus' },
    { label: '🚆 Pociąg', value: 'train' },
    { label: '🚢 Rejs', value: 'cruise' },
  ];

  const handleOpenCreateModal = () => {
    setEditingProfileId(null);
    setName('');
    setSelectedCountries([]);
    setSelectedCities([]);
    setSelectedTransportTypes([]);
    setNotificationPolicy('HIGH_AND_MUST_SEE');
    setAdults(2);
    setChildren(0);
    setDurationMin('7');
    setDurationMax('14');
    setBudgetMax('');
    setHotelStarsMin('3');
    setShowModal(true);
  };

  const handleOpenEditModal = (profile: TravelProfile) => {
    setEditingProfileId(profile.id);
    setName(profile.name);
    setSelectedCountries(profile.countries || []);
    setSelectedCities(profile.departure_cities || []);
    setSelectedTransportTypes(profile.transport_types || []);
    setNotificationPolicy(profile.notification_policy || 'HIGH_AND_MUST_SEE');
    setAdults(profile.adults ?? 2);
    setChildren(profile.children ?? 0);
    setDurationMin(profile.duration_min ? String(profile.duration_min) : '7');
    setDurationMax(profile.duration_max ? String(profile.duration_max) : '14');
    setBudgetMax(profile.budget_max ? String(profile.budget_max) : '');
    setHotelStarsMin(profile.hotel_stars_min ? String(profile.hotel_stars_min) : '3');
    setShowModal(true);
  };

  const toggleCountry = (country: string) => {
    if (selectedCountries.includes(country)) {
      setSelectedCountries(selectedCountries.filter((c) => c !== country));
    } else {
      setSelectedCountries([...selectedCountries, country]);
    }
  };

  const toggleTransportType = (tt: string) => {
    if (selectedTransportTypes.includes(tt)) {
      setSelectedTransportTypes(selectedTransportTypes.filter((x) => x !== tt));
    } else {
      setSelectedTransportTypes([...selectedTransportTypes, tt]);
    }
  };

  const toggleCity = (city: string) => {
    if (selectedCities.includes(city)) {
      setSelectedCities(selectedCities.filter((c) => c !== city));
    } else {
      setSelectedCities([...selectedCities, city]);
    }
  };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) return;

    const payload: TravelProfileCreate = {
      name,
      countries: selectedCountries.length > 0 ? selectedCountries : undefined,
      departure_cities: selectedCities.length > 0 ? selectedCities : undefined,
      transport_types: selectedTransportTypes.length > 0 ? selectedTransportTypes : undefined,
      notification_policy: notificationPolicy,
      adults: Number(adults),
      children: Number(children),
      duration_min: durationMin ? Number(durationMin) : undefined,
      duration_max: durationMax ? Number(durationMax) : undefined,
      budget_max: budgetMax ? Number(budgetMax) : undefined,
      hotel_stars_min: hotelStarsMin ? Number(hotelStarsMin) : undefined,
    };

    try {
      if (editingProfileId) {
        await updateTravelProfile(editingProfileId, payload);
      } else {
        await createTravelProfile(payload);
      }
      setShowModal(false);
      setEditingProfileId(null);
      loadProfiles();
    } catch (err) {
      console.error('Error saving profile:', err);
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm('Czy na pewno chcesz usunąć ten profil monitorowania?')) return;
    try {
      await deleteTravelProfile(id);
      loadProfiles();
    } catch (err) {
      console.error('Error deleting profile:', err);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header & Add Action */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 p-6 rounded-2xl bg-slate-900/60 border border-slate-800 backdrop-blur-md">
        <div>
          <h2 className="text-xl font-bold text-white flex items-center gap-2">
            <ShieldCheck className="w-5 h-5 text-indigo-400" />
            Profili Podróży (Automatyczny Monitoring 24/7)
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Zdefiniuj preferencje wakacyjne. Backend 24/7 analizuje spływające oferty i natychmiast wysyła powiadomienie na Telegram, gdy wykryje nową okazję!
          </p>
        </div>

        <button
          onClick={handleOpenCreateModal}
          className="inline-flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl bg-gradient-to-r from-indigo-600 to-indigo-500 hover:from-indigo-500 hover:to-indigo-400 text-white font-semibold text-xs shadow-lg shadow-indigo-600/20 transition-all hover:scale-105"
        >
          <Plus className="w-4 h-4" />
          <span>Nowy Profil</span>
        </button>
      </div>

      {/* Profiles Grid */}
      {loading ? (
        <div className="p-8 text-center text-slate-400 animate-pulse text-sm">
          Ładowanie zapisanych profili...
        </div>
      ) : profiles.length === 0 ? (
        <div className="p-12 text-center rounded-2xl bg-slate-900/40 border border-slate-800 space-y-3">
          <ShieldCheck className="w-12 h-12 text-slate-600 mx-auto stroke-[1.5]" />
          <h3 className="text-base font-semibold text-slate-300">Brak aktywnych profili</h3>
          <p className="text-xs text-slate-500 max-w-md mx-auto">
            Utwórz swój pierwszy profil podróży, aby automatycznie śledzić spadki cen i nowe oferty spełniające Twoje kryteria.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {profiles.map((profile) => (
            <div
              key={profile.id}
              className="p-5 rounded-2xl bg-slate-900/80 border border-slate-800 space-y-4 hover:border-slate-700 transition-all relative group"
            >
              <div className="flex items-start justify-between">
                <div>
                  <span className="inline-block px-2 py-0.5 rounded text-[10px] uppercase font-bold bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 mb-1.5">
                    Monitoring Aktywny
                  </span>
                  <h3 className="text-base font-bold text-white">{profile.name}</h3>
                </div>
                <div className="flex items-center gap-1">
                  <button
                    onClick={() => handleOpenEditModal(profile)}
                    className="p-1.5 rounded-lg bg-slate-800 text-slate-400 hover:text-indigo-400 hover:bg-slate-700 transition-colors"
                    title="Edytuj profil"
                  >
                    <Pencil className="w-4 h-4" />
                  </button>
                  <button
                    onClick={() => handleDelete(profile.id)}
                    className="p-1.5 rounded-lg bg-slate-800 text-slate-500 hover:text-rose-400 hover:bg-slate-700 transition-colors"
                    title="Usuń profil"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>

              {/* Criteria details */}
              <div className="space-y-2 text-xs text-slate-300">
                <div className="flex items-start gap-2">
                  <MapPin className="w-3.5 h-3.5 text-indigo-400 shrink-0 mt-0.5" />
                  <span>
                    Kraje: <strong>{profile.countries?.join(', ') || 'Wszystkie kraje'}</strong>
                  </span>
                </div>
                <div className="flex items-center gap-2">
                  <Calendar className="w-3.5 h-3.5 text-indigo-400 shrink-0" />
                  <span>
                    Wylot z: <strong>{profile.departure_cities?.join(', ') || 'Dowolne lotnisko'}</strong>
                  </span>
                </div>
                <div className="flex items-center gap-2">
                  <Users className="w-3.5 h-3.5 text-indigo-400 shrink-0" />
                  <span>
                    Osoby:{' '}
                    <strong>
                      {profile.adults ?? 2} dorosłych
                      {profile.children ? `, ${profile.children} dzieci` : ''}
                    </strong>
                  </span>
                </div>
                <div className="flex items-center gap-2">
                  <Moon className="w-3.5 h-3.5 text-indigo-400 shrink-0" />
                  <span>
                    Pobyt:{' '}
                    <strong>
                      {profile.duration_min || 1} - {profile.duration_max || 14} nocy
                    </strong>
                  </span>
                </div>
                <div className="flex items-center gap-2">
                  <DollarSign className="w-3.5 h-3.5 text-indigo-400 shrink-0" />
                  <span>
                    Budżet max:{' '}
                    <strong>
                      {profile.budget_max ? `${profile.budget_max} PLN / os.` : 'Bez limitu'}
                    </strong>
                  </span>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Create / Edit Modal */}
      {showModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-md overflow-y-auto">
          <div className="w-full max-w-lg rounded-3xl bg-slate-900 border border-slate-800 p-6 space-y-5 text-slate-100 shadow-2xl my-8">
            <div className="flex items-center justify-between border-b border-slate-800 pb-4">
              <h3 className="text-lg font-bold">
                {editingProfileId ? 'Edytuj Profil Podróży' : 'Nowy Profil Podróży'}
              </h3>
              <button
                onClick={() => setShowModal(false)}
                className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleSave} className="space-y-4 text-xs">
              <div>
                <label className="block text-slate-400 font-semibold mb-1">Nazwa profilu *</label>
                <input
                  type="text"
                  required
                  placeholder="np. Greckie wakacje 2+1 (7-10 dni)"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  className="w-full bg-slate-800 border border-slate-700 p-2.5 rounded-xl text-slate-100 focus:border-indigo-500"
                />
              </div>

              {/* Multi-Select Countries */}
              <div>
                <label className="block text-slate-400 font-semibold mb-1.5">
                  Docelowe Kraje (wybierz wiele lub pozostaw puste dla wszystkich):
                </label>
                <div className="flex flex-wrap gap-1.5 max-h-32 overflow-y-auto custom-scrollbar p-2 rounded-xl bg-slate-950/40 border border-slate-800">
                  {availableCountries.map((c) => {
                    const active = selectedCountries.includes(c);
                    return (
                      <button
                        key={c}
                        type="button"
                        onClick={() => toggleCountry(c)}
                        className={`flex items-center gap-1 px-2.5 py-1 rounded-lg border text-xs font-semibold transition-all ${
                          active
                            ? 'bg-purple-600 border-purple-500 text-white shadow-md shadow-purple-600/20'
                            : 'bg-slate-800 border-slate-700 text-slate-300 hover:bg-slate-700'
                        }`}
                      >
                        {active && <Check className="w-3 h-3 stroke-[3]" />}
                        <span>{c}</span>
                      </button>
                    );
                  })}
                </div>
              </div>

              {/* Multi-Select Departure Cities */}
              <div>
                <label className="block text-slate-400 font-semibold mb-1.5">
                  Lotniska wylotu (zaznacz interesujące Cię):
                </label>
                <div className="flex flex-wrap gap-1.5">
                  {availableCities.map((city) => {
                    const active = selectedCities.includes(city);
                    return (
                      <button
                        key={city}
                        type="button"
                        onClick={() => toggleCity(city)}
                        className={`flex items-center gap-1 px-2.5 py-1 rounded-lg border text-xs font-semibold transition-all ${
                          active
                            ? 'bg-indigo-600 border-indigo-500 text-white shadow-md shadow-indigo-600/20'
                            : 'bg-slate-800 border-slate-700 text-slate-300 hover:bg-slate-700'
                        }`}
                      >
                        {active && <Check className="w-3 h-3 stroke-[3]" />}
                        <span>{city}</span>
                      </button>
                    );
                  })}
                </div>
              </div>

              {/* Multi-Select Transport Types */}
              <div>
                <label className="block text-slate-400 font-semibold mb-1.5">
                  Rodzaje Transportu (zaznacz wiele lub pozostaw dla wszystkich):
                </label>
                <div className="flex flex-wrap gap-1.5">
                  {availableTransportTypes.map((tt) => {
                    const active = selectedTransportTypes.includes(tt.value);
                    return (
                      <button
                        key={tt.value}
                        type="button"
                        onClick={() => toggleTransportType(tt.value)}
                        className={`flex items-center gap-1 px-2.5 py-1 rounded-lg border text-xs font-semibold transition-all ${
                          active
                            ? 'bg-teal-600 border-teal-500 text-white shadow-md shadow-teal-600/20 font-bold'
                            : 'bg-slate-800 border-slate-700 text-slate-300 hover:bg-slate-700'
                        }`}
                      >
                        {active && <Check className="w-3 h-3 stroke-[3]" />}
                        <span>{tt.label}</span>
                      </button>
                    );
                  })}
                </div>
              </div>

              {/* Notification Policy Selection */}
              <div>
                <label className="block text-slate-400 font-semibold mb-1">Polityka powiadomień Telegram</label>
                <select
                  value={notificationPolicy}
                  onChange={(e) => setNotificationPolicy(e.target.value)}
                  className="w-full bg-slate-800 border border-slate-700 p-2.5 rounded-xl text-slate-100 focus:border-indigo-500"
                >
                  <option value="HIGH_AND_MUST_SEE">🔥 MUST SEE + HIGH (Domyślnie - wyważone)</option>
                  <option value="MUST_SEE_ONLY">🔥🔥🔥 Tylko MUST SEE (Score &gt;= 90)</option>
                  <option value="ALL_ALERTS">📌 Wszystkie alerty (Score &gt;= 50)</option>
                  <option value="DAILY_DIGEST">📰 Zbiorczy rapopt dzienny (Brak powiadomień natychmiastowych)</option>
                </select>
              </div>

              {/* Adults & Children */}
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-slate-400 font-semibold mb-1">Liczba dorosłych</label>
                  <select
                    value={adults}
                    onChange={(e) => setAdults(Number(e.target.value))}
                    className="w-full bg-slate-800 border border-slate-700 p-2.5 rounded-xl text-slate-100 focus:border-indigo-500"
                  >
                    <option value={1}>1 dorosły</option>
                    <option value={2}>2 dorosłych</option>
                    <option value={3}>3 dorosłych</option>
                    <option value={4}>4 dorosłych</option>
                  </select>
                </div>
                <div>
                  <label className="block text-slate-400 font-semibold mb-1">Liczba dzieci</label>
                  <select
                    value={children}
                    onChange={(e) => setChildren(Number(e.target.value))}
                    className="w-full bg-slate-800 border border-slate-700 p-2.5 rounded-xl text-slate-100 focus:border-indigo-500"
                  >
                    <option value={0}>0 dzieci</option>
                    <option value={1}>1 dziecko</option>
                    <option value={2}>2 dzieci</option>
                    <option value={3}>3 dzieci</option>
                  </select>
                </div>
              </div>

              {/* Duration Min / Max */}
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-slate-400 font-semibold mb-1">Min nocy</label>
                  <input
                    type="number"
                    placeholder="np. 7"
                    value={durationMin}
                    onChange={(e) => setDurationMin(e.target.value)}
                    className="w-full bg-slate-800 border border-slate-700 p-2.5 rounded-xl text-slate-100 focus:border-indigo-500"
                  />
                </div>
                <div>
                  <label className="block text-slate-400 font-semibold mb-1">Max nocy</label>
                  <input
                    type="number"
                    placeholder="np. 14"
                    value={durationMax}
                    onChange={(e) => setDurationMax(e.target.value)}
                    className="w-full bg-slate-800 border border-slate-700 p-2.5 rounded-xl text-slate-100 focus:border-indigo-500"
                  />
                </div>
              </div>

              {/* Budget & Hotel Stars */}
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-slate-400 font-semibold mb-1">Budżet max / os. (PLN)</label>
                  <input
                    type="number"
                    placeholder="np. 3500"
                    value={budgetMax}
                    onChange={(e) => setBudgetMax(e.target.value)}
                    className="w-full bg-slate-800 border border-slate-700 p-2.5 rounded-xl text-slate-100 focus:border-indigo-500"
                  />
                </div>
                <div>
                  <label className="block text-slate-400 font-semibold mb-1">Min gwiazdek hotelu</label>
                  <select
                    value={hotelStarsMin}
                    onChange={(e) => setHotelStarsMin(e.target.value)}
                    className="w-full bg-slate-800 border border-slate-700 p-2.5 rounded-xl text-slate-100 focus:border-indigo-500"
                  >
                    <option value="3">3 ★ i więcej</option>
                    <option value="4">4 ★ i więcej</option>
                    <option value="5">5 ★ (Luksus)</option>
                  </select>
                </div>
              </div>

              <div className="pt-3 flex justify-end gap-3 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setShowModal(false)}
                  className="px-4 py-2 rounded-xl bg-slate-800 text-slate-400 hover:text-white font-medium"
                >
                  Anuluj
                </button>
                <button
                  type="submit"
                  className="px-5 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-bold shadow-lg shadow-indigo-600/30"
                >
                  {editingProfileId ? 'Zapisz Zmiany' : 'Utwórz Profil'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
