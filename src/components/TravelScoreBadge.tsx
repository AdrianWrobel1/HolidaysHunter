'use client';

import React from 'react';
import { Award, Flame, Sparkles } from 'lucide-react';

interface TravelScoreBadgeProps {
  score: number | null;
  size?: 'sm' | 'md' | 'lg';
}

export const TravelScoreBadge: React.FC<TravelScoreBadgeProps> = ({ score, size = 'md' }) => {
  if (score === null || score === undefined) {
    return (
      <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-medium bg-slate-800/80 text-slate-400 border border-slate-700">
        Brak oceny
      </span>
    );
  }

  let colorClass = 'bg-slate-800 text-slate-300 border-slate-700';
  let Icon = Sparkles;
  let label = 'Standard';

  if (score >= 85) {
    colorClass = 'bg-gradient-to-r from-emerald-500/20 to-teal-500/20 text-emerald-400 border-emerald-500/40 shadow-lg shadow-emerald-500/10';
    Icon = Flame;
    label = 'Super Hit!';
  } else if (score >= 70) {
    colorClass = 'bg-gradient-to-r from-amber-500/20 to-orange-500/20 text-amber-400 border-amber-500/40';
    Icon = Award;
    label = 'Świetna cena';
  } else if (score >= 50) {
    colorClass = 'bg-indigo-500/20 text-indigo-300 border-indigo-500/30';
    Icon = Sparkles;
    label = 'Dobra oferta';
  }

  const sizeClasses = {
    sm: 'px-2 py-0.5 text-xs',
    md: 'px-2.5 py-1 text-xs',
    lg: 'px-3.5 py-1.5 text-sm font-semibold',
  };

  return (
    <div
      className={`inline-flex items-center gap-1.5 rounded-full border backdrop-blur-md font-medium transition-all ${colorClass} ${sizeClasses[size]}`}
      title={`Travel Score: ${score}/100 — ${label}`}
    >
      <Icon className={size === 'lg' ? 'w-4 h-4' : 'w-3.5 h-3.5'} />
      <span>Score: {score}</span>
      <span className="opacity-75 text-[10px] uppercase tracking-wider font-semibold">({label})</span>
    </div>
  );
};
