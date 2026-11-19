import React, { useState } from 'react';
import { BugReport } from '../types';
import { DiffViewer } from './DiffViewer';
import { TestResultsView } from './TestResultsView';
import {
  AlertTriangle,
  Bug,
  CheckCircle,
  XCircle,
  FileCode,
  Copy,
  Check,
  CheckCircle2,
  AlertOctagon,
  ShieldCheck,
  Sparkles
} from 'lucide-react';

interface BugInspectorProps {
  bug: BugReport | null;
  onAccept: (bugId: string, comment?: string) => Promise<void>;
  onReject: (bugId: string, comment?: string) => Promise<void>;
  isProcessing: boolean;
}

export const BugInspector: React.FC<BugInspectorProps> = ({
  bug,
  onAccept,
  onReject,
  isProcessing
}) => {
  const [comment, setComment] = useState('');
  const [activeTab, setActiveTab] = useState<'diff' | 'tests'>('diff');
  const [copied, setCopied] = useState(false);

  if (!bug) {
    return (
      <div className="h-full min-h-[500px] flex flex-col items-center justify-center p-12 text-center border border-slate-200/90 rounded-2xl bg-white shadow-sm space-y-4">
        <div className="p-5 rounded-2xl bg-indigo-50 border border-indigo-100 text-indigo-600 shadow-sm">
          <Bug className="w-10 h-10 animate-bounce" />
        </div>
        <div className="space-y-1 max-w-sm">
          <h3 className="text-lg font-bold text-slate-800">No Bug Selected</h3>
          <p className="text-xs text-slate-500 leading-relaxed">
            Paste code in the workspace and click <span className="font-semibold text-indigo-600">Scan Code & Fix Bugs</span> to inspect detected flaws, root cause breakdowns, and verified patches.
          </p>
        </div>
      </div>
    );
  }

  const handleCopyCode = () => {
    const codeToCopy = bug.composed_code || bug.patched_code;
    navigator.clipboard.writeText(codeToCopy);
    setCopied(true);
    setTimeout(() => setCopied(false), 2500);
  };

  const getSeverityBadge = (severity: string) => {
    const s = severity.toUpperCase();
    if (s === 'ERROR' || s === 'CRITICAL') {
      return 'bg-red-50 text-red-700 border-red-300';
    } else if (s === 'WARNING' || s === 'HIGH' || s === 'MEDIUM') {
      return 'bg-amber-50 text-amber-800 border-amber-300';
    } else {
      return 'bg-blue-50 text-blue-800 border-blue-300';
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'Accepted':
        return 'bg-emerald-50 text-emerald-800 border-emerald-300 font-bold';
      case 'Rejected':
        return 'bg-rose-50 text-rose-800 border-rose-300 font-bold';
      default:
        return 'bg-amber-50 text-amber-800 border-amber-300 font-medium';
    }
  };

  return (
    <div className="h-full flex flex-col space-y-4">
      {/* Top Header Card */}
      <div className="p-5 rounded-2xl border border-slate-200/90 bg-white shadow-sm space-y-3">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-2 flex-wrap">
            <span className={`px-3 py-1 rounded-lg text-xs font-bold border uppercase tracking-wider ${getSeverityBadge(bug.severity)}`}>
              {bug.severity} Severity
            </span>
            <span className="px-3 py-1 rounded-lg text-xs font-semibold bg-indigo-50 text-indigo-700 border border-indigo-200">
              {bug.confidence}% Confidence
            </span>
            <span className={`px-3 py-1 rounded-lg text-xs border ${getStatusBadge(bug.status)}`}>
              Status: {bug.status}
            </span>
          </div>

          <div className="flex items-center gap-2.5">
            {/* Big Prominent Copy Fixed Code Button */}
            <button
              onClick={handleCopyCode}
              className="px-4 py-2 rounded-xl text-xs sm:text-sm font-bold bg-indigo-50 hover:bg-indigo-100 text-indigo-700 border border-indigo-200 shadow-sm transition-all flex items-center gap-2 active:scale-95 hover:shadow"
              title="Copy the complete patched code to clipboard"
            >
              {copied ? (
                <>
                  <Check className="w-4 h-4 text-emerald-600 stroke-[3]" />
                  <span className="text-emerald-700 font-extrabold">Copied Fixed Code!</span>
                </>
              ) : (
                <>
                  <Copy className="w-4 h-4 text-indigo-600" />
                  <span>Copy Fixed Code</span>
                </>
              )}
            </button>

            {/* File Path Pill */}
            <div className="flex items-center gap-1.5 text-xs font-mono text-slate-700 bg-slate-50 px-3 py-2 rounded-xl border border-slate-200">
              <FileCode className="w-4 h-4 text-indigo-600" />
              <span className="font-bold text-slate-900 truncate max-w-[150px]">{bug.file_path}</span>
              <span className="text-slate-400 font-semibold">:L{bug.line_start}</span>
            </div>
          </div>
        </div>

        {/* Bug Title */}
        <div>
          <h2 className="text-base sm:text-lg font-bold text-slate-900 flex items-center gap-2.5">
            <AlertTriangle className="w-5 h-5 text-amber-500 shrink-0" />
            <span>{bug.title}</span>
          </h2>
        </div>
      </div>

      {/* Side-by-Side Clarity: Error (Red) vs Fix (Green) */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Error Box (Red) */}
        <div className="p-4 rounded-2xl border border-red-200/90 bg-red-50/70 shadow-sm space-y-2.5">
          <div className="flex items-center gap-2 text-xs font-extrabold uppercase tracking-wider text-red-800">
            <AlertOctagon className="w-4 h-4 text-red-600 shrink-0" />
            What was the Error?
          </div>
          <p className="text-xs sm:text-[13px] text-red-950 leading-relaxed font-sans font-medium">
            {bug.root_cause}
          </p>
          <div className="mt-2 pt-2 border-t border-red-200 text-xs font-mono text-red-800">
            <span className="font-bold">Failure Trigger: </span>
            <span>{bug.trigger_input_or_state}</span>
          </div>
        </div>

        {/* Fix Box (Green) */}
        <div className="p-4 rounded-2xl border border-emerald-200/90 bg-emerald-50/70 shadow-sm space-y-2.5">
          <div className="flex items-center gap-2 text-xs font-extrabold uppercase tracking-wider text-emerald-800">
            <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
            How was it Repaired?
          </div>
          <div className="text-xs sm:text-[13px] text-emerald-950 leading-relaxed font-sans whitespace-pre-line font-medium">
            {bug.repair_summary || 'Applied targeted fix to resolve the error.'}
          </div>
          <div className="mt-2 pt-2 border-t border-emerald-200 text-xs font-mono text-emerald-800 flex items-center gap-1.5">
            <Sparkles className="w-3.5 h-3.5 text-emerald-600 shrink-0" />
            <span>Minimal targeted patch applied without regressions.</span>
          </div>
        </div>
      </div>

      {/* Tab Switcher: Diff vs Sandboxed Tests */}
      <div className="flex items-center gap-2.5 border-b border-slate-200 pb-2">
        <button
          onClick={() => setActiveTab('diff')}
          className={`px-5 py-2.5 rounded-xl text-xs sm:text-sm font-bold flex items-center gap-2 transition-all ${
            activeTab === 'diff'
              ? 'bg-indigo-600 text-white shadow-sm'
              : 'bg-white text-slate-700 hover:bg-slate-100 border border-slate-200'
          }`}
        >
          <FileCode className="w-4 h-4" />
          Code Diff (Before vs After)
        </button>
        <button
          onClick={() => setActiveTab('tests')}
          className={`px-5 py-2.5 rounded-xl text-xs sm:text-sm font-bold flex items-center gap-2 transition-all ${
            activeTab === 'tests'
              ? 'bg-indigo-600 text-white shadow-sm'
              : 'bg-white text-slate-700 hover:bg-slate-100 border border-slate-200'
          }`}
        >
          <ShieldCheck className="w-4 h-4" />
          Sandboxed Test Verification
        </button>
      </div>

      {/* Main Tab Content */}
      <div className="flex-1">
        {activeTab === 'diff' ? (
          <DiffViewer
            originalCode={bug.original_code}
            patchedCode={bug.patched_code}
            filePath={bug.file_path}
          />
        ) : (
          <TestResultsView validation={bug.validation} />
        )}
      </div>

      {/* Human Review & Decision Bar with Bigger Buttons */}
      <div className="p-5 rounded-2xl border border-slate-200/90 bg-white shadow-sm space-y-3.5">
        <div className="flex items-center justify-between">
          <span className="text-xs font-bold uppercase tracking-wider text-slate-700">
            Apply or Reject Repair
          </span>
          {bug.status !== 'Needs Review' && (
            <span className={`text-xs px-3 py-1 rounded-lg border ${getStatusBadge(bug.status)}`}>
              Decision: {bug.status}
            </span>
          )}
        </div>

        <div className="flex flex-col sm:flex-row items-center gap-3">
          <input
            type="text"
            value={comment}
            onChange={(e) => setComment(e.target.value)}
            placeholder="Add optional review comment..."
            className="w-full sm:flex-1 px-4 py-2.5 text-xs sm:text-sm rounded-xl bg-slate-50 border border-slate-200 text-slate-800 placeholder-slate-400 focus:outline-none focus:border-indigo-500 focus:bg-white transition-all"
          />

          {/* Big Action Buttons */}
          <div className="flex items-center gap-2.5 w-full sm:w-auto justify-end">
            <button
              onClick={() => onReject(bug.id, comment)}
              disabled={isProcessing || bug.status === 'Rejected'}
              className="px-5 py-2.5 rounded-xl text-sm font-bold border border-rose-300 text-rose-700 hover:bg-rose-50 active:scale-[0.98] disabled:opacity-40 transition-all flex items-center gap-2"
            >
              <XCircle className="w-4 h-4 text-rose-600" />
              Reject Fix
            </button>
            <button
              onClick={() => onAccept(bug.id, comment)}
              disabled={isProcessing || bug.status === 'Accepted'}
              className="px-7 py-2.5 rounded-xl text-sm font-bold bg-emerald-600 hover:bg-emerald-700 active:scale-[0.98] text-white shadow-md shadow-emerald-200 hover:shadow-lg disabled:opacity-40 transition-all flex items-center gap-2"
            >
              <CheckCircle className="w-4 h-4 text-white" />
              Accept Fix
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
