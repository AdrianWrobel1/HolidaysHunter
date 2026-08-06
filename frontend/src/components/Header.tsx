import React, { useState, useEffect } from 'react';
import { Compass, ShieldCheck, Bell, Sparkles, TrendingUp, Send, CheckCircle2, XCircle, BarChart3, FolderKanban } from 'lucide-react';
import { fetchTelegramStatus, toggleTelegramNotifications } from '@/lib/api';

interface HeaderProps {
  activeTab: 'explorer' | 'profiles' | 'alerts' | 'seasonal' | 'analyzer' | 'workspace';
  onTabChange: (tab: 'explorer' | 'profiles' | 'alerts' | 'seasonal' | 'analyzer' | 'workspace') => void;
  unreadAlertsCount: number;
}

export const Header: React.FC<HeaderProps> = ({
  activeTab,
  onTabChange,
  unreadAlertsCount,
}) => {
  const [telegramEnabled, setTelegramEnabled] = useState(true);
  const [telegramConfigured, setTelegramConfigured] = useState(false);
  const [toggling, setToggling] = useState(false);

  useEffect(() => {
    fetchTelegramStatus()
      .then((res) => {
        setTelegramEnabled(res.enabled);
        setTelegramConfigured(res.configured);
      })
      .catch((err) => console.warn('Could not fetch Telegram status:', err));
  }, []);

  const handleToggleTelegram = async () => {
    try {
      setToggling(true);
      const nextState = !telegramEnabled;
      const res = await toggleTelegramNotifications(nextState);
      setTelegramEnabled(res.enabled);
    } catch (err) {
      console.error('Error toggling Telegram:', err);
    } finally {
      setToggling(false);
    }
  };

  return (
    <header className="sticky top-0 z-40 w-full bg-slate-950/80 backdrop-blur-xl border-b border-slate-800/80">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-20 flex items-center justify-between gap-4">
        {/* Logo & Platform Name */}
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-2xl bg-gradient-to-tr from-amber-500 via-rose-500 to-indigo-600 p-0.5 shadow-lg shadow-indigo-500/20">
            <div className="w-full h-full bg-slate-950 rounded-[14px] flex items-center justify-center" suppressHydrationWarning>
              <Sparkles className="w-5 h-5 text-amber-400" suppressHydrationWarning />
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

        {/* Telegram Toggle & Navigation */}
        <div className="flex items-center gap-3">
          {/* Telegram Toggle Button */}
          <button
            onClick={handleToggleTelegram}
            disabled={toggling}
            className={`hidden md:flex items-center gap-2 px-3 py-1.5 rounded-xl border text-xs font-bold transition-all ${
              telegramEnabled
                ? 'bg-sky-500/10 border-sky-500/30 text-sky-300 hover:bg-sky-500/20'
                : 'bg-slate-900 border-slate-800 text-slate-500 hover:text-slate-300'
            }`}
            title="Włącz/Wyłącz powiadomienia Telegram z powiadomieniami o nowych okazjach"
          >
            <Send className="w-3.5 h-3.5" />
            <span>Telegram:</span>
            {telegramEnabled ? (
              <span className="text-emerald-400 font-extrabold flex items-center gap-1">
                <CheckCircle2 className="w-3 h-3" /> WŁĄCZONE
              </span>
            ) : (
              <span className="text-slate-500 flex items-center gap-1">
                <XCircle className="w-3 h-3" /> WYŁĄCZONE
              </span>
            )}
          </button>

          {/* Navigation Tabs */}
          <nav className="flex items-center gap-1 bg-slate-900/80 p-1.5 rounded-2xl border border-slate-800 text-xs font-semibold">
            <button
              onClick={() => onTabChange('explorer')}
              className={`flex items-center gap-2 px-3 sm:px-4 py-2 rounded-xl transition-all ${
                activeTab === 'explorer'
                  ? 'bg-gradient-to-r from-indigo-600 to-indigo-500 text-white shadow-lg shadow-indigo-600/30 font-bold'
                  : 'text-slate-400 hover:text-white hover:bg-slate-800/60'
              }`}
            >
              <Compass className="w-4 h-4" suppressHydrationWarning />
              <span className="hidden sm:inline">Explorer</span>
            </button>

            <button
              onClick={() => onTabChange('workspace')}
              className={`flex items-center gap-2 px-3 sm:px-4 py-2 rounded-xl transition-all ${
                activeTab === 'workspace'
                  ? 'bg-gradient-to-r from-purple-600 to-indigo-600 text-white shadow-lg shadow-purple-600/30 font-bold'
                  : 'text-slate-400 hover:text-white hover:bg-slate-800/60'
              }`}
            >
              <FolderKanban className="w-4 h-4 text-indigo-400" suppressHydrationWarning />
              <span className="hidden sm:inline">Research Workspace</span>
            </button>

            <button
              onClick={() => onTabChange('profiles')}
              className={`flex items-center gap-2 px-3 sm:px-4 py-2 rounded-xl transition-all ${
                activeTab === 'profiles'
                  ? 'bg-gradient-to-r from-indigo-600 to-indigo-500 text-white shadow-lg shadow-indigo-600/30 font-bold'
                  : 'text-slate-400 hover:text-white hover:bg-slate-800/60'
              }`}
            >
              <ShieldCheck className="w-4 h-4" suppressHydrationWarning />
              <span className="hidden sm:inline">Profili</span>
            </button>

            <button
              onClick={() => onTabChange('alerts')}
              className={`relative flex items-center gap-2 px-3 sm:px-4 py-2 rounded-xl transition-all ${
                activeTab === 'alerts'
                  ? 'bg-gradient-to-r from-indigo-600 to-indigo-500 text-white shadow-lg shadow-indigo-600/30 font-bold'
                  : 'text-slate-400 hover:text-white hover:bg-slate-800/60'
              }`}
            >
              <Bell className="w-4 h-4" suppressHydrationWarning />
              <span className="hidden sm:inline">Alerts</span>
              {unreadAlertsCount > 0 && (
                <span className="px-1.5 py-0.5 text-[10px] font-black rounded-full bg-rose-500 text-white animate-bounce shadow-md">
                  {unreadAlertsCount}
                </span>
              )}
            </button>

            <button
              onClick={() => onTabChange('seasonal')}
              className={`flex items-center gap-2 px-3 sm:px-4 py-2 rounded-xl transition-all ${
                activeTab === 'seasonal'
                  ? 'bg-gradient-to-r from-purple-600 to-indigo-600 text-white shadow-lg shadow-purple-600/30 font-bold'
                  : 'text-slate-400 hover:text-white hover:bg-slate-800/60'
              }`}
            >
              <TrendingUp className="w-4 h-4 text-purple-400" suppressHydrationWarning />
              <span className="hidden sm:inline">Sezonowość</span>
            </button>
          </nav>
        </div>
      </div>
    </header>
  );
};
