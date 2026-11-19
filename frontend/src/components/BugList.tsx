import React, { useState } from 'react';
import { BugReport } from '../types';
import { CheckCircle2, XCircle, Clock, ShieldAlert, Filter } from 'lucide-react';

interface BugListProps {
  bugs: BugReport[];
  selectedBugId: string | null;
  onSelectBug: (bug: BugReport) => void;
}

export const BugList: React.FC<BugListProps> = ({ bugs, selectedBugId, onSelectBug }) => {
  const [filterCategory, setFilterCategory] = useState<string>('ALL');

  const getSeverityBadge = (severity: string) => {
    const s = severity.toUpperCase();
    if (s === 'ERROR' || s === 'CRITICAL') {
      return 'bg-red-50 text-red-700 border-red-200';
    } else if (s === 'WARNING' || s === 'HIGH' || s === 'MEDIUM') {
      return 'bg-amber-50 text-amber-700 border-amber-200';
    } else {
      return 'bg-blue-50 text-blue-700 border-blue-200';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'Accepted':
        return <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />;
      case 'Rejected':
        return <XCircle className="w-4 h-4 text-rose-600 shrink-0" />;
      default:
        return <Clock className="w-4 h-4 text-amber-600 shrink-0" />;
    }
  };

  const filteredBugs = bugs.filter((bug) => {
    if (filterCategory === 'ALL') return true;
    return bug.category.toUpperCase().includes(filterCategory);
  });

  return (
    <div className="h-full flex flex-col space-y-3">
      {/* Header */}
      <div className="flex items-center justify-between px-1">
        <div className="flex items-center gap-2">
          <ShieldAlert className="w-4 h-4 text-indigo-600" />
          <h3 className="text-xs font-bold uppercase tracking-wider text-slate-700">
            Detected Issues ({filteredBugs.length})
          </h3>
        </div>
        <span className="text-[11px] text-slate-400 font-mono">Ranked by Priority</span>
      </div>

      {/* Category Filter Pills */}
      {bugs.length > 0 && (
        <div className="flex items-center gap-1 overflow-x-auto pb-1 text-[11px]">
          {['ALL', 'SYNTAX', 'VARIABLE', 'FUNCTION', 'LOGIC', 'STRUCTUR'].map((cat) => (
            <button
              key={cat}
              onClick={() => setFilterCategory(cat)}
              className={`px-2 py-0.5 rounded-md font-medium whitespace-nowrap transition-all ${
                filterCategory === cat
                  ? 'bg-slate-900 text-white shadow-sm'
                  : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
              }`}
            >
              {cat === 'STRUCTUR' ? 'STRUCTURE' : cat}
            </button>
          ))}
        </div>
      )}

      {/* Bug List */}
      {bugs.length === 0 ? (
        <div className="p-8 text-center rounded-2xl border border-slate-200 bg-white text-slate-400 text-xs">
          No bugs found. Paste code or upload a file and run scan.
        </div>
      ) : filteredBugs.length === 0 ? (
        <div className="p-8 text-center rounded-2xl border border-slate-200 bg-white text-slate-400 text-xs">
          No issues matching category filter "{filterCategory}".
        </div>
      ) : (
        <div className="space-y-2 overflow-y-auto pr-1 max-h-[calc(100vh-280px)]">
          {filteredBugs.map((bug) => {
            const isSelected = bug.id === selectedBugId;
            return (
              <div
                key={bug.id}
                onClick={() => onSelectBug(bug)}
                className={`p-3.5 rounded-xl border text-left cursor-pointer transition-all duration-150 ${
                  isSelected
                    ? 'bg-indigo-50/70 border-indigo-400 shadow-sm ring-1 ring-indigo-400'
                    : 'bg-white border-slate-200 hover:bg-slate-50'
                }`}
              >
                <div className="flex items-start justify-between gap-2 mb-1.5">
                  <div className="flex items-center gap-1.5 flex-wrap">
                    <span className={`px-2 py-0.5 rounded text-[10px] font-bold border uppercase tracking-wider ${getSeverityBadge(bug.severity)}`}>
                      {bug.severity}
                    </span>
                    <span className="text-[10px] text-slate-600 bg-slate-100 px-1.5 py-0.5 rounded font-medium border border-slate-200 truncate max-w-[130px]">
                      {bug.category}
                    </span>
                    <span className="text-[10px] font-mono text-indigo-700 bg-indigo-50 px-1.5 py-0.5 rounded border border-indigo-200">
                      {bug.confidence}%
                    </span>
                  </div>
                  <div className="flex items-center gap-1 text-[11px]">
                    {getStatusIcon(bug.status)}
                    <span className="text-slate-600 font-medium">{bug.status}</span>
                  </div>
                </div>

                <div className="font-semibold text-xs text-slate-900 line-clamp-2 mb-1.5">
                  {bug.title}
                </div>

                <div className="flex items-center justify-between text-[11px] text-slate-500 font-mono pt-1 border-t border-slate-100">
                  <span className="truncate max-w-[180px] text-slate-700">{bug.file_path}</span>
                  <span className="text-slate-400">L{bug.line_start}-{bug.line_end}</span>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
