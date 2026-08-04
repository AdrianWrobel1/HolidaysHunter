'use client';

import React, { useState, useEffect, useRef } from 'react';
import { Calendar as CalendarIcon, ChevronLeft, ChevronRight, X, Check } from 'lucide-react';

interface DateRangePickerProps {
  dateFrom?: string;
  dateTo?: string;
  onChange: (dateFrom?: string, dateTo?: string) => void;
}

const MONTH_NAMES = [
  'Styczeń', 'Luty', 'Marzec', 'Kwiecień', 'Maj', 'Czerwiec',
  'Lipiec', 'Sierpień', 'Wrzesień', 'Październik', 'Listopad', 'Grudzień'
];

const DAYS_OF_WEEK = ['Pn', 'Wt', 'Śr', 'Cz', 'Pt', 'So', 'Nd'];

export const DateRangePicker: React.FC<DateRangePickerProps> = ({
  dateFrom,
  dateTo,
  onChange,
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  // Active view date for calendar navigation
  const initialDate = dateFrom ? new Date(dateFrom) : new Date();
  const [currentYear, setCurrentYear] = useState(initialDate.getFullYear());
  const [currentMonth, setCurrentMonth] = useState(initialDate.getMonth());

  // Transient selection state
  const [tempFrom, setTempFrom] = useState<string | undefined>(dateFrom);
  const [tempTo, setTempTo] = useState<string | undefined>(dateTo);

  useEffect(() => {
    setTempFrom(dateFrom);
    setTempTo(dateTo);
  }, [dateFrom, dateTo]);

  // Close popover when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const formatDateLabel = (dFrom?: string, dTo?: string) => {
    if (!dFrom && !dTo) return 'Wszystkie terminy (Kalendarz)';
    if (dFrom && !dTo) return `Od ${dFrom}`;
    if (!dFrom && dTo) return `Do ${dTo}`;
    return `${dFrom} — ${dTo}`;
  };

  const handlePrevMonth = () => {
    if (currentMonth === 0) {
      setCurrentMonth(11);
      setCurrentYear(currentYear - 1);
    } else {
      setCurrentMonth(currentMonth - 1);
    }
  };

  const handleNextMonth = () => {
    if (currentMonth === 11) {
      setCurrentMonth(0);
      setCurrentYear(currentYear + 1);
    } else {
      setCurrentMonth(currentMonth + 1);
    }
  };

  const handleDayClick = (dayStr: string) => {
    if (!tempFrom || (tempFrom && tempTo)) {
      setTempFrom(dayStr);
      setTempTo(undefined);
    } else {
      if (dayStr < tempFrom) {
        setTempFrom(dayStr);
        setTempTo(tempFrom);
      } else {
        setTempTo(dayStr);
      }
    }
  };

  const applyPreset = (from?: string, to?: string) => {
    setTempFrom(from);
    setTempTo(to);
    onChange(from, to);
    setIsOpen(false);
  };

  const handleApply = () => {
    onChange(tempFrom, tempTo);
    setIsOpen(false);
  };

  const handleClear = () => {
    setTempFrom(undefined);
    setTempTo(undefined);
    onChange(undefined, undefined);
    setIsOpen(false);
  };

  // Generate calendar days for currentMonth & currentYear
  const getDaysArray = () => {
    const firstDay = new Date(currentYear, currentMonth, 1);
    const lastDay = new Date(currentYear, currentMonth + 1, 0);

    // Monday-based indexing: 0 = Mon, ..., 6 = Sun
    let startingDay = firstDay.getDay() - 1;
    if (startingDay === -1) startingDay = 6;

    const days: Array<{ dateStr: string; dayNumber: number; isCurrentMonth: boolean }> = [];

    // Previous month padding
    const prevMonthLastDay = new Date(currentYear, currentMonth, 0).getDate();
    for (let i = startingDay - 1; i >= 0; i--) {
      const d = prevMonthLastDay - i;
      const prevM = currentMonth === 0 ? 11 : currentMonth - 1;
      const prevY = currentMonth === 0 ? currentYear - 1 : currentYear;
      const mStr = String(prevM + 1).padStart(2, '0');
      const dStr = String(d).padStart(2, '0');
      days.push({ dateStr: `${prevY}-${mStr}-${dStr}`, dayNumber: d, isCurrentMonth: false });
    }

    // Current month days
    for (let d = 1; d <= lastDay.getDate(); d++) {
      const mStr = String(currentMonth + 1).padStart(2, '0');
      const dStr = String(d).padStart(2, '0');
      days.push({ dateStr: `${currentYear}-${mStr}-${dStr}`, dayNumber: d, isCurrentMonth: true });
    }

    return days;
  };

  const days = getDaysArray();

  return (
    <div className="relative w-full" ref={containerRef}>
      <label className="block text-slate-400 text-xs font-medium mb-1">Termin wyjazdu</label>
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className={`w-full flex items-center justify-between gap-2 p-2.5 rounded-xl border text-xs text-left transition-all ${
          tempFrom || tempTo
            ? 'bg-indigo-950/40 border-indigo-500/80 text-indigo-200 font-semibold'
            : 'bg-slate-800 border-slate-700 text-slate-200 hover:bg-slate-700/80'
        }`}
      >
        <div className="flex items-center gap-2 truncate">
          <CalendarIcon className="w-4 h-4 text-indigo-400 shrink-0" />
          <span className="truncate">{formatDateLabel(tempFrom, tempTo)}</span>
        </div>
        {(tempFrom || tempTo) && (
          <span
            onClick={(e) => {
              e.stopPropagation();
              handleClear();
            }}
            className="p-1 hover:bg-rose-500/20 hover:text-rose-400 rounded-full transition-colors text-slate-400"
            title="Wyczyść daty"
          >
            <X className="w-3.5 h-3.5" />
          </span>
        )}
      </button>

      {/* Popover Calendar Dropdown */}
      {isOpen && (
        <div className="absolute top-full left-0 mt-2 z-50 w-full sm:w-[360px] bg-slate-900 border border-slate-800 rounded-2xl shadow-2xl p-4 space-y-4 animate-fadeIn text-xs">
          {/* Quick Presets */}
          <div className="space-y-1.5">
            <span className="text-[10px] uppercase font-bold text-slate-500 tracking-wider">
              Szybkie wybory
            </span>
            <div className="flex flex-wrap gap-1.5">
              <button
                type="button"
                onClick={() => applyPreset(undefined, undefined)}
                className="px-2.5 py-1 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-[11px]"
              >
                Dowolny termin
              </button>
              <button
                type="button"
                onClick={() => {
                  const today = new Date();
                  const nextMonth = new Date(today);
                  nextMonth.setDate(today.getDate() + 30);
                  applyPreset(today.toISOString().split('T')[0], nextMonth.toISOString().split('T')[0]);
                }}
                className="px-2.5 py-1 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-[11px]"
              >
                Najbliższe 30 dni
              </button>
              <button
                type="button"
                onClick={() => applyPreset('2026-07-01', '2026-08-31')}
                className="px-2.5 py-1 rounded-lg bg-indigo-950/60 border border-indigo-500/40 text-indigo-300 text-[11px] font-semibold"
              >
                Lato 2026
              </button>
              <button
                type="button"
                onClick={() => applyPreset('2026-09-01', '2026-11-30')}
                className="px-2.5 py-1 rounded-lg bg-amber-950/60 border border-amber-500/40 text-amber-300 text-[11px] font-semibold"
              >
                Jesień 2026
              </button>
            </div>
          </div>

          {/* Date Input Pickers */}
          <div className="grid grid-cols-2 gap-2 pt-2 border-t border-slate-800">
            <div>
              <label className="text-[10px] text-slate-400">Wylot od</label>
              <input
                type="date"
                value={tempFrom || ''}
                onChange={(e) => setTempFrom(e.target.value || undefined)}
                className="w-full bg-slate-800 border border-slate-700 text-slate-200 p-1.5 rounded-lg text-xs"
              />
            </div>
            <div>
              <label className="text-[10px] text-slate-400">Wylot do</label>
              <input
                type="date"
                value={tempTo || ''}
                onChange={(e) => setTempTo(e.target.value || undefined)}
                className="w-full bg-slate-800 border border-slate-700 text-slate-200 p-1.5 rounded-lg text-xs"
              />
            </div>
          </div>

          {/* Month Header Navigation */}
          <div className="flex items-center justify-between pt-2 border-t border-slate-800">
            <button
              type="button"
              onClick={handlePrevMonth}
              className="p-1 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300"
            >
              <ChevronLeft className="w-4 h-4" />
            </button>
            <span className="font-bold text-slate-200">
              {MONTH_NAMES[currentMonth]} {currentYear}
            </span>
            <button
              type="button"
              onClick={handleNextMonth}
              className="p-1 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300"
            >
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>

          {/* Calendar Grid */}
          <div>
            {/* Days Header */}
            <div className="grid grid-cols-7 gap-1 text-center text-[10px] font-bold text-slate-500 mb-1">
              {DAYS_OF_WEEK.map((d) => (
                <div key={d}>{d}</div>
              ))}
            </div>

            {/* Days Cells */}
            <div className="grid grid-cols-7 gap-1 text-center text-xs">
              {days.map(({ dateStr, dayNumber, isCurrentMonth }, idx) => {
                const isSelectedFrom = tempFrom === dateStr;
                const isSelectedTo = tempTo === dateStr;
                const isInRange =
                  tempFrom && tempTo && dateStr >= tempFrom && dateStr <= tempTo;

                let cellBg = 'hover:bg-slate-800 text-slate-300';
                if (!isCurrentMonth) cellBg = 'text-slate-600 hover:bg-slate-800/40';

                if (isSelectedFrom || isSelectedTo) {
                  cellBg = 'bg-indigo-600 text-white font-bold rounded-lg shadow-md';
                } else if (isInRange) {
                  cellBg = 'bg-indigo-950/80 text-indigo-200 font-medium';
                }

                return (
                  <button
                    key={idx}
                    type="button"
                    onClick={() => handleDayClick(dateStr)}
                    className={`py-1.5 rounded-lg transition-colors ${cellBg}`}
                  >
                    {dayNumber}
                  </button>
                );
              })}
            </div>
          </div>

          {/* Actions */}
          <div className="flex items-center justify-between pt-3 border-t border-slate-800 gap-2">
            <button
              type="button"
              onClick={handleClear}
              className="px-3 py-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-slate-200 transition-colors font-medium text-xs"
            >
              Wyczyść
            </button>
            <button
              type="button"
              onClick={handleApply}
              className="flex items-center gap-1.5 px-4 py-1.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-bold text-xs shadow-lg shadow-indigo-600/30 transition-all"
            >
              <Check className="w-3.5 h-3.5" />
              <span>Zastosuj daty</span>
            </button>
          </div>
        </div>
      )}
    </div>
  );
};
