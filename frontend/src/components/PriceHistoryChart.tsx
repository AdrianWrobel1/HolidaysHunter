'use client';

import React from 'react';
import { PriceHistoryResponse } from '@/types/api';
import { TrendingDown, TrendingUp, Minus, Calendar, DollarSign } from 'lucide-react';

interface PriceHistoryChartProps {
  history: PriceHistoryResponse[];
  currentPrice: string;
}

export const PriceHistoryChart: React.FC<PriceHistoryChartProps> = ({ history, currentPrice }) => {
  if (!history || history.length === 0) {
    return (
      <div className="p-4 rounded-xl bg-slate-900/50 border border-slate-800 text-center text-slate-400 text-sm">
        Brak zarejestrowanej historii zmian ceny.
      </div>
    );
  }

  // Sort history chronologically
  const sorted = [...history].sort(
    (a, b) => new Date(a.recorded_at).getTime() - new Date(b.recorded_at).getTime()
  );

  const prices = sorted.map((item) => parseFloat(item.price_per_person));
  const minPrice = Math.min(...prices);
  const maxPrice = Math.max(...prices);
  const firstPrice = prices[0];
  const lastPrice = prices[prices.length - 1];
  const priceDiff = lastPrice - firstPrice;
  const pctChange = firstPrice > 0 ? ((priceDiff / firstPrice) * 100).toFixed(1) : 0;

  return (
    <div className="p-5 rounded-2xl bg-slate-900/80 border border-slate-800 backdrop-blur-xl shadow-xl space-y-4">
      <div className="flex items-center justify-between">
        <h4 className="text-sm font-semibold text-slate-200 flex items-center gap-2">
          <DollarSign className="w-4 h-4 text-emerald-400" />
          Historia zmian ceny (za osobę)
        </h4>

        {sorted.length > 1 && (
          <div
            className={`inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-semibold ${
              priceDiff < 0
                ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                : priceDiff > 0
                ? 'bg-rose-500/20 text-rose-400 border border-rose-500/30'
                : 'bg-slate-800 text-slate-400'
            }`}
          >
            {priceDiff < 0 ? (
              <>
                <TrendingDown className="w-3.5 h-3.5" />
                <span>-{Math.abs(Number(pctChange))}%</span>
              </>
            ) : priceDiff > 0 ? (
              <>
                <TrendingUp className="w-3.5 h-3.5" />
                <span>+{pctChange}%</span>
              </>
            ) : (
              <>
                <Minus className="w-3.5 h-3.5" />
                <span>Bez zmian</span>
              </>
            )}
          </div>
        )}
      </div>

      {/* Mini timeline table */}
      <div className="space-y-2 max-h-48 overflow-y-auto pr-1 custom-scrollbar">
        {sorted.map((item, idx) => {
          const priceNum = parseFloat(item.price_per_person);
          const isMin = priceNum === minPrice && sorted.length > 1;
          const dateStr = new Date(item.recorded_at).toLocaleDateString('pl-PL', {
            day: 'numeric',
            month: 'short',
            hour: '2-digit',
            minute: '2-digit',
          });

          return (
            <div
              key={item.id || idx}
              className={`flex items-center justify-between p-2.5 rounded-lg text-xs transition-colors ${
                isMin ? 'bg-emerald-500/10 border border-emerald-500/30' : 'bg-slate-800/40 hover:bg-slate-800/80'
              }`}
            >
              <div className="flex items-center gap-2 text-slate-400">
                <Calendar className="w-3.5 h-3.5 text-slate-500" />
                <span>{dateStr}</span>
              </div>
              <div className="flex items-center gap-2">
                {isMin && (
                  <span className="text-[10px] uppercase tracking-wider font-bold px-1.5 py-0.5 rounded bg-emerald-500/20 text-emerald-400">
                    Najtaniej
                  </span>
                )}
                <span className="font-semibold text-slate-100">{item.price_per_person} PLN</span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
