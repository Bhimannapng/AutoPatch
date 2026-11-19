import React from 'react';
import { ChangeHistoryEntry } from '../types';
import { X, History, CheckCircle2, XCircle, Download, FileCode, Clock, Trash2 } from 'lucide-react';

interface HistoryModalProps {
  isOpen: boolean;
  onClose: () => void;
  history: ChangeHistoryEntry[];
  onExportZip: () => void;
  onClearAllHistory: () => Promise<void>;
  onDeleteEntry: (entryId: string) => Promise<void>;
}

export const HistoryModal: React.FC<HistoryModalProps> = ({
  isOpen,
  onClose,
  history,
  onExportZip,
  onClearAllHistory,
  onDeleteEntry
}) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/40 backdrop-blur-sm animate-fade-in">
      <div className="w-full max-w-3xl max-h-[85vh] rounded-2xl border border-slate-200/90 bg-white shadow-2xl flex flex-col overflow-hidden animate-scale-up">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-100 bg-slate-50/70">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-xl bg-indigo-50 text-indigo-600 border border-indigo-100 shadow-sm">
              <History className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-base font-bold text-slate-900">Change History</h2>
              <p className="text-xs text-slate-500">Audit log of all accepted and rejected code fixes.</p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            {/* Clear All History Button */}
            {history.length > 0 && (
              <button
                onClick={onClearAllHistory}
                className="px-3.5 py-2 rounded-xl text-xs font-semibold text-rose-700 bg-rose-50 hover:bg-rose-100 border border-rose-200 transition-all flex items-center gap-1.5 active:scale-95"
                title="Delete all history entries"
              >
                <Trash2 className="w-3.5 h-3.5 text-rose-600" />
                <span>Clear History</span>
              </button>
            )}

            {/* Download Patched Project Zip */}
            <button
              onClick={onExportZip}
              className="px-4 py-2 rounded-xl text-xs sm:text-sm font-bold bg-emerald-600 hover:bg-emerald-500 text-white shadow-sm transition-all flex items-center gap-2 active:scale-95"
            >
              <Download className="w-4 h-4" />
              <span>Download Fixed Project (.zip)</span>
            </button>

            {/* Close Button */}
            <button
              onClick={onClose}
              className="p-2 rounded-xl text-slate-400 hover:text-slate-700 hover:bg-slate-100 transition-colors ml-1"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Content list */}
        <div className="p-6 overflow-y-auto space-y-3 flex-1">
          {history.length === 0 ? (
            <div className="p-16 text-center text-slate-400 text-sm space-y-2">
              <div className="w-12 h-12 mx-auto rounded-full bg-slate-100 flex items-center justify-center text-slate-400">
                <History className="w-6 h-6" />
              </div>
              <p className="font-semibold text-slate-600">No review decisions yet.</p>
              <p className="text-xs text-slate-400 max-w-sm mx-auto">
                Decisions to accept or reject code fixes will be recorded here with timestamps.
              </p>
            </div>
          ) : (
            history.map((entry) => (
              <div
                key={entry.id}
                className="p-4 rounded-xl border border-slate-200/80 bg-slate-50/50 hover:bg-white hover:shadow-sm transition-all space-y-2.5 group"
              >
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <div className="flex items-center gap-2.5">
                    <span className={`px-2.5 py-1 rounded-lg text-xs font-bold border flex items-center gap-1.5 ${
                      entry.action === 'ACCEPTED'
                        ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                        : 'bg-rose-50 text-rose-700 border-rose-200'
                    }`}>
                      {entry.action === 'ACCEPTED' ? (
                        <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600 stroke-[2.5]" />
                      ) : (
                        <XCircle className="w-3.5 h-3.5 text-rose-600 stroke-[2.5]" />
                      )}
                      {entry.action}
                    </span>
                    <span className="font-bold text-xs sm:text-sm text-slate-900">{entry.bug_title}</span>
                  </div>

                  <div className="flex items-center gap-3">
                    <div className="flex items-center gap-1.5 text-xs font-mono text-slate-400">
                      <Clock className="w-3.5 h-3.5 text-slate-400" />
                      <span>{entry.timestamp}</span>
                    </div>

                    {/* Delete Individual Entry Button */}
                    <button
                      onClick={() => onDeleteEntry(entry.id)}
                      className="p-1.5 rounded-lg text-slate-400 hover:text-rose-600 hover:bg-rose-50 opacity-70 group-hover:opacity-100 transition-all"
                      title="Delete this history record"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </div>

                <div className="flex items-center gap-2 text-xs font-mono text-slate-500">
                  <FileCode className="w-3.5 h-3.5 text-indigo-500" />
                  <span className="text-slate-700 font-semibold">{entry.file_path}</span>
                </div>

                {entry.comment && (
                  <div className="text-xs text-slate-700 bg-white p-2.5 rounded-xl border border-slate-200/70 italic font-sans">
                    "{entry.comment}"
                  </div>
                )}
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
};
