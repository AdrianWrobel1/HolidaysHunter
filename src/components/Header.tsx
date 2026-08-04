'use client';

import React from 'react';
import { Compass, ShieldCheck, Bell, Activity, Sparkles } from 'lucide-react';

interface HeaderProps {
  activeTab: 'explorer' | 'profiles' | 'alerts';
  onTabChange: (tab: 'explorer' | 'profiles' | 'alerts') => void;
  unreadAlertsCount: number;
}

export const Header: React.FC<HeaderProps> = ({
  activeTab,
  onTabChange,
  unreadAlertsCount,
}) => {
  return (
    <header className="sticky top-0 z-40 w-full bg-slate-950/80 backdrop-blur-xl border-b border-slate-800/80">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-20 flex items-center justify-between gap-4">
        {/* Logo & Platform Name */}
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-2xl bg-gradient-to-tr from-amber-500 via-rose-500 to-indigo-600 p-0.5 shadow-lg shadow-indigo-500/20">
            <div className="w-full h-full bg-slate-950 rounded-[14px] flex items-center justify-center">
              <Sparkles className="w-5 h-5 text-amber-400" />
            </div>
          </div>
          <div>
            <h1 className="text-lg font-black tracking-tight text-white flex items-center gap-2">
              Holidays<span className="text-transparent bg-clip-text bg-gradient-to-r from-amber-400 to-indigo-400">Hunter</span>
            </h1>
            <div className="flex items-center gap-1.5 text-[10px] text-slate-400 font-medium">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
              <span>Backend Monitoring 24/7 Active</span>
            </div>
          </div>
        </div>

        {/* Navigation Tabs */}
        <nav className="flex items-center gap-1.5 bg-slate-900/80 p-1.5 rounded-2xl border border-slate-800 text-xs font-semibold">
          <button
            onClick={() => onTabChange('explorer')}
            className={`flex items-center gap-2 px-4 py-2 rounded-xl transition-all ${
              activeTab === 'explorer'
                ? 'bg-gradient-to-r from-indigo-600 to-indigo-500 text-white shadow-lg shadow-indigo-600/30 font-bold'
                : 'text-slate-400 hover:text-white hover:bg-slate-800/60'
            }`}
          >
            <Compass className="w-4 h-4" />
            <span className="hidden sm:inline">Explorer</span>
          </button>

          <button
            onClick={() => onTabChange('profiles')}
            className={`flex items-center gap-2 px-4 py-2 rounded-xl transition-all ${
              activeTab === 'profiles'
                ? 'bg-gradient-to-r from-indigo-600 to-indigo-500 text-white shadow-lg shadow-indigo-600/30 font-bold'
                : 'text-slate-400 hover:text-white hover:bg-slate-800/60'
            }`}
          >
            <ShieldCheck className="w-4 h-4" />
            <span className="hidden sm:inline">Profili Podróży</span>
          </button>

          <button
            onClick={() => onTabChange('alerts')}
            className={`relative flex items-center gap-2 px-4 py-2 rounded-xl transition-all ${
              activeTab === 'alerts'
                ? 'bg-gradient-to-r from-indigo-600 to-indigo-500 text-white shadow-lg shadow-indigo-600/30 font-bold'
                : 'text-slate-400 hover:text-white hover:bg-slate-800/60'
            }`}
          >
            <Bell className="w-4 h-4" />
            <span className="hidden sm:inline">Smart Alerts</span>
            {unreadAlertsCount > 0 && (
              <span className="px-1.5 py-0.5 text-[10px] font-black rounded-full bg-rose-500 text-white animate-bounce shadow-md">
                {unreadAlertsCount}
              </span>
            )}
          </button>
        </nav>
      </div>
    </header>
  );
};
