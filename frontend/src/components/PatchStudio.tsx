import React, { useState } from 'react';
import {
  BugReport,
  SandboxedValidation
} from '../types';
import { DiffViewer } from './DiffViewer';
import {
  Check,
  X,
  RotateCcw,
  Copy,
  Download,
  AlertTriangle,
  ShieldCheck,
  Terminal,
  Clock,
  Sparkles,
  FileCode,
  CheckCircle2,
  ExternalLink
} from 'lucide-react';

interface PatchStudioProps {
  bugs: BugReport[];
  selectedBug: BugReport | null;
  onSelectBug: (bug: BugReport) => void;
  onReviewAction: (bugId: string, action: 'ACCEPTED' | 'REJECTED' | 'REVERT') => Promise<void>;
  isProcessingAction: boolean;
  showNotification: (msg: string, type: 'success' | 'info' | 'error') => void;
  onExportZip: () => void;
}

export const PatchStudio: React.FC<PatchStudioProps> = ({
  bugs,
  selectedBug,
  onSelectBug,
  onReviewAction,
  isProcessingAction,
  showNotification,
  onExportZip
}) => {
  const [filterSeverity, setFilterSeverity] = useState<string>('ALL');
  const [filterFile, setFilterFile] = useState<string>('ALL');
  const [isCopied, setIsCopied] = useState<boolean>(false);

  // Unique files for dropdown filter
  const uniqueFiles = Array.from(new Set(bugs.map((b) => b.file_path)));

  const filteredBugs = bugs.filter((b) => {
    const matchSev = filterSeverity === 'ALL' || b.severity.toUpperCase() === filterSeverity.toUpperCase();
    const matchFile = filterFile === 'ALL' || b.file_path === filterFile;
    return matchSev && matchFile;
  });

  const activeBug = selectedBug || filteredBugs[0] || null;

  const handleCopyCode = () => {
    if (!activeBug) return;
    const code = activeBug.composed_code || activeBug.patched_code;
    navigator.clipboard.writeText(code);
    setIsCopied(true);
    showNotification('Fixed code copied to clipboard!', 'success');
    setTimeout(() => setIsCopied(false), 2000);
  };

  if (bugs.length === 0) {
    return (
      <div className="bg-white border border-slate-200 rounded-2xl p-12 text-center shadow-xs">
        <div className="w-16 h-16 mx-auto mb-4 bg-emerald-50 text-emerald-600 rounded-2xl flex items-center justify-center border border-emerald-100">
          <ShieldCheck className="w-8 h-8" />
        </div>
        <h3 className="text-lg font-bold text-slate-900 mb-2">No Active Defects Detected</h3>
        <p className="text-slate-500 text-sm max-w-md mx-auto">
          The uploaded project has 0 critical syntax or semantic defects. All parsed source code conforms cleanly to language standards.
        </p>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
      {/* Left Column: Bug List & Filters (4 Cols) */}
      <div className="lg:col-span-4 bg-white border border-slate-200 rounded-2xl p-4 flex flex-col h-[760px] shadow-xs">
        {/* Filter Bar */}
        <div className="space-y-2 pb-3 border-b border-slate-100">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-slate-800 uppercase tracking-wider">
              Defects ({filteredBugs.length})
            </span>
            <button
              onClick={onExportZip}
              className="flex items-center gap-1 text-[11px] font-semibold text-indigo-600 hover:text-indigo-700 transition-colors"
            >
              <Download className="w-3.5 h-3.5" />
              <span>Export ZIP</span>
            </button>
          </div>

          <div className="grid grid-cols-2 gap-2">
            <select
              value={filterSeverity}
              onChange={(e) => setFilterSeverity(e.target.value)}
              className="bg-slate-50 border border-slate-200 text-slate-800 text-xs rounded-lg px-2.5 py-1.5 focus:outline-none focus:border-indigo-600"
            >
              <option value="ALL">All Severities</option>
              <option value="ERROR">Error / Critical</option>
              <option value="WARNING">Warning</option>
            </select>

            <select
              value={filterFile}
              onChange={(e) => setFilterFile(e.target.value)}
              className="bg-slate-50 border border-slate-200 text-slate-800 text-xs rounded-lg px-2.5 py-1.5 focus:outline-none focus:border-indigo-600 truncate"
            >
              <option value="ALL">All Files</option>
              {uniqueFiles.map((f) => (
                <option key={f} value={f}>
                  {f}
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Bug Items Scrollable List */}
        <div className="flex-1 overflow-y-auto space-y-2 pt-3 pr-1 scrollbar-thin">
          {filteredBugs.map((bug) => {
            const isSelected = activeBug?.id === bug.id;
            const isAccepted = bug.status === 'Accepted';
            const isRejected = bug.status === 'Rejected';

            return (
              <div
                key={bug.id}
                onClick={() => onSelectBug(bug)}
                className={`p-3.5 rounded-xl border cursor-pointer transition-all ${
                  isSelected
                    ? 'bg-indigo-50/60 border-indigo-600 shadow-xs'
                    : 'bg-white border-slate-200 hover:border-slate-300 hover:bg-slate-50/50'
                }`}
              >
                <div className="flex items-center justify-between gap-2 mb-1.5">
                  <span
                    className={`text-[10px] font-bold px-2 py-0.5 rounded ${
                      bug.severity.toUpperCase().includes('ERROR') || bug.severity.toUpperCase().includes('CRITICAL')
                        ? 'bg-rose-50 text-rose-700 border border-rose-100'
                        : 'bg-amber-50 text-amber-700 border border-amber-100'
                    }`}
                  >
                    {bug.severity}
                  </span>

                  <span
                    className={`text-[10px] font-semibold px-2 py-0.5 rounded ${
                      isAccepted
                        ? 'bg-emerald-50 text-emerald-700 border border-emerald-100'
                        : isRejected
                        ? 'bg-rose-50 text-rose-700 border border-rose-100'
                        : 'bg-slate-100 text-slate-600'
                    }`}
                  >
                    {bug.status}
                  </span>
                </div>

                <h4 className="text-xs font-semibold text-slate-900 line-clamp-1">{bug.title}</h4>
                <div className="text-[11px] text-slate-500 mt-1 flex items-center justify-between font-mono">
                  <span className="truncate">{bug.file_path}</span>
                  <span className="text-slate-400 shrink-0">L{bug.line_start}</span>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Right Column: Detailed Inspector, Diff & Sandbox Validation (8 Cols) */}
      <div className="lg:col-span-8 bg-white border border-slate-200 rounded-2xl p-6 flex flex-col h-[760px] overflow-y-auto scrollbar-thin shadow-xs">
        {activeBug ? (
          <div className="space-y-6">
            {/* Header with Title and Action Buttons */}
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-100">
              <div>
                <div className="flex items-center gap-2 mb-1 text-xs">
                  <span className="font-mono text-indigo-700 font-semibold">{activeBug.file_path}</span>
                  <span className="text-slate-400">•</span>
                  <span className="text-slate-500">Line {activeBug.line_start}</span>
                  <span className="text-slate-400">•</span>
                  <span className="text-emerald-700 font-semibold">{activeBug.confidence}% Confidence</span>
                </div>
                <h2 className="text-lg sm:text-xl font-bold text-slate-900">{activeBug.title}</h2>
              </div>

              {/* Action Buttons */}
              <div className="flex items-center gap-2 shrink-0">
                <button
                  onClick={handleCopyCode}
                  className="flex items-center gap-1.5 px-3 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-xl text-xs font-semibold transition-colors border border-slate-200"
                >
                  <Copy className="w-3.5 h-3.5 text-slate-600" />
                  <span>{isCopied ? 'Copied!' : 'Copy Fix'}</span>
                </button>

                {activeBug.status === 'Accepted' ? (
                  <button
                    onClick={() => onReviewAction(activeBug.id, 'REVERT')}
                    disabled={isProcessingAction}
                    className="flex items-center gap-1.5 px-3.5 py-2 bg-amber-600 hover:bg-amber-700 text-white rounded-xl text-xs font-semibold shadow-xs transition-colors disabled:opacity-50"
                  >
                    <RotateCcw className="w-3.5 h-3.5" />
                    <span>Revert Fix</span>
                  </button>
                ) : (
                  <>
                    <button
                      onClick={() => onReviewAction(activeBug.id, 'ACCEPTED')}
                      disabled={isProcessingAction}
                      className="flex items-center gap-1.5 px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl text-xs font-semibold shadow-xs transition-colors disabled:opacity-50"
                    >
                      <Check className="w-3.5 h-3.5" />
                      <span>Accept Patch</span>
                    </button>

                    <button
                      onClick={() => onReviewAction(activeBug.id, 'REJECTED')}
                      disabled={isProcessingAction}
                      className="flex items-center gap-1.5 px-3 py-2 bg-white hover:bg-rose-50 text-slate-600 hover:text-rose-700 border border-slate-200 rounded-xl text-xs font-semibold transition-colors disabled:opacity-50"
                    >
                      <X className="w-3.5 h-3.5" />
                      <span>Reject</span>
                    </button>
                  </>
                )}
              </div>
            </div>

            {/* Root-Cause Explanation Cards */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
              <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-200">
                <div className="text-slate-700 font-bold mb-1 flex items-center gap-1.5">
                  <AlertTriangle className="w-3.5 h-3.5 text-amber-600" /> Root Cause Analysis
                </div>
                <div className="text-slate-600 leading-relaxed">{activeBug.root_cause}</div>
              </div>

              <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-200">
                <div className="text-slate-700 font-bold mb-1 flex items-center gap-1.5">
                  <Terminal className="w-3.5 h-3.5 text-indigo-600" /> Trigger Input / Execution State
                </div>
                <div className="text-slate-600 leading-relaxed">{activeBug.trigger_input_or_state}</div>
              </div>
            </div>

            {/* Diff Viewer */}
            <div>
              <div className="text-xs font-bold text-slate-700 uppercase tracking-wider mb-2">
                Unified Code Difference (Side-by-Side)
              </div>
              <DiffViewer
                originalCode={activeBug.original_code}
                patchedCode={activeBug.patched_code}
                filePath={activeBug.file_path}
              />
            </div>

            {/* Sandboxed Validation Results */}
            {activeBug.validation && (
              <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <div
                      className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold ${
                        activeBug.validation.verified
                          ? 'bg-emerald-100 text-emerald-800'
                          : 'bg-amber-100 text-amber-800'
                      }`}
                    >
                      {activeBug.validation.verified ? '✓' : '!'}
                    </div>
                    <span className="text-xs font-bold text-slate-900">
                      Sandbox Execution & Integrity Verification
                    </span>
                  </div>

                  <span
                    className={`text-[10px] font-bold px-2 py-0.5 rounded ${
                      activeBug.validation.verified
                        ? 'bg-emerald-100 text-emerald-800 border border-emerald-200'
                        : 'bg-amber-100 text-amber-800 border border-amber-200'
                    }`}
                  >
                    {activeBug.validation.verified ? 'VERIFIED PASSED' : 'CHECK REQUIRED'}
                  </span>
                </div>

                <div className="text-xs font-mono text-slate-800 bg-white p-3 rounded-lg border border-slate-200 whitespace-pre-wrap">
                  {activeBug.validation.details}
                </div>

                {activeBug.validation.before_tests && activeBug.validation.before_tests.length > 0 && (
                  <div className="pt-2 border-t border-slate-200 grid grid-cols-2 gap-2 text-xs">
                    <div className="text-slate-600">
                      Before Fix Tests:{' '}
                      <span className="text-rose-700 font-bold">
                        {activeBug.validation.before_failed} Failed
                      </span>
                    </div>
                    <div className="text-slate-600">
                      After Fix Tests:{' '}
                      <span className="text-emerald-700 font-bold">
                        {activeBug.validation.after_passed} Passed
                      </span>
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        ) : (
          <div className="text-center py-20 text-slate-400 text-xs">
            Select a defect from the left list to review its diff and sandbox results.
          </div>
        )}
      </div>
    </div>
  );
};
