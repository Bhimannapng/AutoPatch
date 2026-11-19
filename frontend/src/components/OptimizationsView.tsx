import React, { useState } from 'react';
import {
  Cpu,
  Layers,
  Zap,
  Trash2,
  AlertCircle,
  Clock,
  Sparkles,
  ArrowUpRight,
  TrendingDown
} from 'lucide-react';
import { OptimizationFinding } from '../types';

interface OptimizationsViewProps {
  optimizations: OptimizationFinding[];
}

export const OptimizationsView: React.FC<OptimizationsViewProps> = ({ optimizations }) => {
  const [filterCategory, setFilterCategory] = useState<string>('ALL');

  const filtered = optimizations.filter(
    (o) => filterCategory === 'ALL' || o.category === filterCategory
  );

  const categories = Array.from(new Set(optimizations.map((o) => o.category)));

  if (optimizations.length === 0) {
    return (
      <div className="bg-white border border-slate-200 rounded-2xl p-12 text-center shadow-xs">
        <div className="w-16 h-16 mx-auto mb-4 bg-emerald-50 text-emerald-600 border border-emerald-100 rounded-2xl flex items-center justify-center">
          <Zap className="w-8 h-8" />
        </div>
        <h3 className="text-lg font-bold text-slate-900 mb-2">Optimal RAM & CPU Architecture</h3>
        <p className="text-slate-500 text-sm max-w-md mx-auto">
          No nested quadratic loops or memory leak patterns were discovered in the analyzed source code. Heap allocations appear efficient.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Category Pills Filter */}
      <div className="flex flex-wrap items-center gap-2">
        <button
          onClick={() => setFilterCategory('ALL')}
          className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
            filterCategory === 'ALL'
              ? 'bg-amber-600 text-white shadow-xs'
              : 'bg-white text-slate-600 border border-slate-200 hover:text-slate-900'
          }`}
        >
          All Opportunities ({optimizations.length})
        </button>
        {categories.map((cat) => (
          <button
            key={cat}
            onClick={() => setFilterCategory(cat)}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
              filterCategory === cat
                ? 'bg-amber-600 text-white shadow-xs'
                : 'bg-white text-slate-600 border border-slate-200 hover:text-slate-900'
            }`}
          >
            {cat} ({optimizations.filter((o) => o.category === cat).length})
          </button>
        ))}
      </div>

      {/* Findings Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {filtered.map((item) => (
          <div
            key={item.id}
            className="bg-white border border-slate-200 hover:border-amber-300 rounded-2xl p-5 shadow-xs transition-all flex flex-col justify-between"
          >
            <div>
              <div className="flex items-center justify-between gap-2 mb-2">
                <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-amber-50 border border-amber-200 text-amber-700 uppercase tracking-wider">
                  {item.category}
                </span>

                <span
                  className={`text-[10px] font-semibold px-2 py-0.5 rounded ${
                    item.risk_level === 'Low'
                      ? 'bg-emerald-50 text-emerald-700 border border-emerald-100'
                      : 'bg-amber-50 text-amber-700 border border-amber-100'
                  }`}
                >
                  {item.risk_level} Risk
                </span>
              </div>

              <h3 className="text-base font-bold text-slate-900 mb-1">{item.title}</h3>
              <div className="text-xs text-slate-500 font-mono mb-3">
                {item.file_path}:{item.line_start}
              </div>

              <div className="space-y-2 text-xs">
                <div className="p-3 rounded-xl bg-slate-50 border border-slate-200">
                  <div className="text-slate-600 font-semibold mb-0.5">Problem & Bottleneck:</div>
                  <div className="text-slate-800">{item.problem}</div>
                </div>

                <div className="p-3 rounded-xl bg-slate-50 border border-slate-200">
                  <div className="text-slate-600 font-semibold mb-0.5">Why Inefficient:</div>
                  <div className="text-slate-700">{item.why_inefficient}</div>
                </div>

                <div className="p-3 rounded-xl bg-amber-50/70 border border-amber-200 text-amber-900">
                  <div className="font-semibold text-amber-800 mb-0.5 flex items-center gap-1">
                    <Sparkles className="w-3.5 h-3.5" /> Actionable Improvement:
                  </div>
                  <div>{item.suggested_improvement}</div>
                </div>
              </div>
            </div>

            <div className="mt-4 pt-3 border-t border-slate-100 flex items-center justify-between text-xs text-slate-500">
              <span className="flex items-center gap-1 text-emerald-700 font-semibold">
                <TrendingDown className="w-3.5 h-3.5" /> Expected: {item.expected_benefit}
              </span>
              <span className="text-[11px] text-slate-400 font-mono">
                {item.is_measured ? 'Measured in Sandbox' : 'Static Suspected'}
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
