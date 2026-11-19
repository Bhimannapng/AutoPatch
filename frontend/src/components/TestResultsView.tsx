import React from 'react';
import { SandboxedValidation } from '../types';
import { CheckCircle2, XCircle, AlertCircle, ShieldCheck } from 'lucide-react';

interface TestResultsViewProps {
  validation?: SandboxedValidation | null;
}

export const TestResultsView: React.FC<TestResultsViewProps> = ({ validation }) => {
  if (!validation) {
    return (
      <div className="p-4 rounded-xl border border-slate-200 bg-white text-slate-600 text-sm flex items-center gap-3">
        <AlertCircle className="w-5 h-5 text-amber-500 shrink-0" />
        <span>No test run recorded yet. Click "Scan & Fix" to run tests in the sandbox.</span>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Verification status header */}
      <div className={`p-4 rounded-xl border flex items-center justify-between ${
        validation.verified
          ? 'bg-emerald-50 border-emerald-200 text-emerald-900'
          : 'bg-amber-50 border-amber-200 text-amber-900'
      }`}>
        <div className="flex items-center gap-3">
          <ShieldCheck className={`w-6 h-6 ${validation.verified ? 'text-emerald-600' : 'text-amber-600'}`} />
          <div>
            <div className="font-bold text-sm">
              {validation.verified ? 'Sandboxed Test Verification Passed' : 'Tests Completed with Warnings'}
            </div>
            <div className="text-xs text-slate-600 mt-0.5">{validation.details}</div>
          </div>
        </div>
        <span className="px-2.5 py-1 rounded-full bg-white border border-slate-200 text-slate-700 text-xs font-mono font-medium shadow-sm">
          Isolated Sandbox Execution
        </span>
      </div>

      {/* Dual comparison before vs after */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Before Patch Card */}
        <div className="rounded-xl border border-slate-200 bg-white p-4 space-y-3 shadow-sm">
          <div className="flex items-center justify-between pb-2 border-b border-slate-100">
            <span className="text-xs font-bold text-rose-700 uppercase tracking-wider flex items-center gap-1.5">
              <XCircle className="w-4 h-4 text-rose-600" />
              Before Patch (Baseline)
            </span>
            <div className="flex items-center gap-2 text-xs">
              <span className="text-rose-600 font-bold">{validation.before_failed} Failed</span>
              <span className="text-slate-300">|</span>
              <span className="text-slate-600">{validation.before_passed} Passed</span>
            </div>
          </div>

          <div className="space-y-2 max-h-56 overflow-y-auto pr-1">
            {validation.before_tests.length > 0 ? (
              validation.before_tests.map((test, i) => (
                <div
                  key={i}
                  className={`p-2.5 rounded-lg text-xs border font-mono ${
                    test.status === 'PASSED'
                      ? 'bg-slate-50 border-slate-200 text-slate-700'
                      : 'bg-rose-50 border-rose-200 text-rose-900'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="truncate pr-2 font-medium">{test.name}</span>
                    <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                      test.status === 'PASSED' ? 'bg-emerald-100 text-emerald-800' : 'bg-rose-100 text-rose-800'
                    }`}>
                      {test.status}
                    </span>
                  </div>
                  {test.error_message && (
                    <div className="mt-1.5 text-[11px] text-rose-700 bg-white/80 p-2 rounded border border-rose-100 overflow-x-auto whitespace-pre font-mono">
                      {test.error_message}
                    </div>
                  )}
                </div>
              ))
            ) : (
              <div className="text-xs text-slate-400 italic py-2">No tests recorded.</div>
            )}
          </div>
        </div>

        {/* After Patch Card */}
        <div className="rounded-xl border border-slate-200 bg-white p-4 space-y-3 shadow-sm">
          <div className="flex items-center justify-between pb-2 border-b border-slate-100">
            <span className="text-xs font-bold text-emerald-700 uppercase tracking-wider flex items-center gap-1.5">
              <CheckCircle2 className="w-4 h-4 text-emerald-600" />
              After Patch (Sandboxed Execution)
            </span>
            <div className="flex items-center gap-2 text-xs">
              <span className="text-emerald-600 font-bold">{validation.after_passed} Passed</span>
              <span className="text-slate-300">|</span>
              <span className="text-slate-500">{validation.after_failed} Failed</span>
            </div>
          </div>

          <div className="space-y-2 max-h-56 overflow-y-auto pr-1">
            {validation.after_tests.length > 0 ? (
              validation.after_tests.map((test, i) => (
                <div
                  key={i}
                  className={`p-2.5 rounded-lg text-xs border font-mono ${
                    test.status === 'PASSED'
                      ? 'bg-emerald-50/70 border-emerald-200 text-emerald-950'
                      : 'bg-rose-50 border-rose-200 text-rose-900'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="truncate pr-2 font-medium">{test.name}</span>
                    <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                      test.status === 'PASSED' ? 'bg-emerald-100 text-emerald-800' : 'bg-rose-100 text-rose-800'
                    }`}>
                      {test.status}
                    </span>
                  </div>
                </div>
              ))
            ) : (
              <div className="text-xs text-slate-400 italic py-2">No tests recorded.</div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
