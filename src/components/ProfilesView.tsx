'use client';

import React, { useState, useEffect } from 'react';
import { TravelProfile, TravelProfileCreate, FilterOptionsResponse } from '@/types/api';
import { fetchTravelProfiles, createTravelProfile, deleteTravelProfile } from '@/lib/api';
import { Plus, Trash2, ShieldCheck, MapPin, Calendar, DollarSign, Check, X } from 'lucide-react';

interface ProfilesViewProps {
  filterOptions: FilterOptionsResponse | null;
}

export const ProfilesView: React.FC<ProfilesViewProps> = ({ filterOptions }) => {
  const [profiles, setProfiles] = useState<TravelProfile[]>([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);

  // Form state for creating new profile
  const [name, setName] = useState('');
  const [selectedCountry, setSelectedCountry] = useState('');
  const [selectedCity, setSelectedCity] = useState('');
  const [budgetMax, setBudgetMax] = useState('');
  const [durationMin, setDurationMin] = useState('7');
  const [hotelStarsMin, setHotelStarsMin] = useState('3');

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

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) return;

    const payload: TravelProfileCreate = {
      name,
      countries: selectedCountry ? [selectedCountry] : undefined,
      departure_cities: selectedCity ? [selectedCity] : undefined,
      budget_max: budgetMax ? Number(budgetMax) : undefined,
      duration_min: durationMin ? Number(durationMin) : undefined,
      hotel_stars_min: hotelStarsMin ? Number(hotelStarsMin) : undefined,
    };

    try {
      await createTravelProfile(payload);
      setShowModal(false);
      setName('');
      setSelectedCountry('');
      setSelectedCity('');
      setBudgetMax('');
      loadProfiles();
    } catch (err) {
      console.error('Error creating profile:', err);
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
            Profili Podróży (Automatyczny Monitoring)
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Zdefiniuj preferencje wakacyjne. Backend 24/7 analizuje spływające oferty i natychmiast wysyła powiadomienie na Telegram, gdy wykryje nową okazję!
          </p>
        </div>

        <button
          onClick={() => setShowModal(true)}
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
                <button
                  onClick={() => handleDelete(profile.id)}
                  className="p-1.5 rounded-lg bg-slate-800 text-slate-500 hover:text-rose-400 hover:bg-slate-700 transition-colors"
                  title="Usuń profil"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>

              {/* Criteria details */}
              <div className="space-y-2 text-xs text-slate-300">
                <div className="flex items-center gap-2">
                  <MapPin className="w-3.5 h-3.5 text-indigo-400" />
                  <span>Kraj: <strong>{profile.countries?.join(', ') || 'Wszystkie'}</strong></span>
                </div>
                <div className="flex items-center gap-2">
                  <Calendar className="w-3.5 h-3.5 text-indigo-400" />
                  <span>Wylot z: <strong>{profile.departure_cities?.join(', ') || 'Dowolne'}</strong></span>
                </div>
                <div className="flex items-center gap-2">
                  <DollarSign className="w-3.5 h-3.5 text-indigo-400" />
                  <span>Budżet max: <strong>{profile.budget_max ? `${profile.budget_max} PLN` : 'Brak limitu'}</strong></span>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Create Modal */}
      {showModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-md">
          <div className="w-full max-w-md rounded-3xl bg-slate-900 border border-slate-800 p-6 space-y-5 text-slate-100 shadow-2xl">
            <div className="flex items-center justify-between border-b border-slate-800 pb-4">
              <h3 className="text-lg font-bold">Nowy Profil Podróży</h3>
              <button
                onClick={() => setShowModal(false)}
                className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleCreate} className="space-y-4 text-xs">
              <div>
                <label className="block text-slate-400 font-semibold mb-1">Nazwa profilu *</label>
                <input
                  type="text"
                  required
                  placeholder="np. Greckie wakacje Lato 2026"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  className="w-full bg-slate-800 border border-slate-700 p-2.5 rounded-xl text-slate-100 focus:border-indigo-500"
                />
              </div>

              <div>
                <label className="block text-slate-400 font-semibold mb-1">Docelowy Kraj</label>
                <select
                  value={selectedCountry}
                  onChange={(e) => setSelectedCountry(e.target.value)}
                  className="w-full bg-slate-800 border border-slate-700 p-2.5 rounded-xl text-slate-100 focus:border-indigo-500"
                >
                  <option value="">Wszystkie kraje</option>
                  {filterOptions?.countries.map((c) => (
                    <option key={c} value={c}>{c}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-slate-400 font-semibold mb-1">Miasto Wylotu</label>
                <select
                  value={selectedCity}
                  onChange={(e) => setSelectedCity(e.target.value)}
                  className="w-full bg-slate-800 border border-slate-700 p-2.5 rounded-xl text-slate-100 focus:border-indigo-500"
                >
                  <option value="">Dowolne miasto</option>
                  {filterOptions?.departure_cities.map((city) => (
                    <option key={city} value={city}>{city}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-slate-400 font-semibold mb-1">Budżet Maksymalny / os. (PLN)</label>
                <input
                  type="number"
                  placeholder="np. 3500"
                  value={budgetMax}
                  onChange={(e) => setBudgetMax(e.target.value)}
                  className="w-full bg-slate-800 border border-slate-700 p-2.5 rounded-xl text-slate-100 focus:border-indigo-500"
                />
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
                  Zapisz Profil
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
