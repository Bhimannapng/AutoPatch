import React from 'react';

interface DiffViewerProps {
  originalCode: string;
  patchedCode: string;
  filePath: string;
}

export const DiffViewer: React.FC<DiffViewerProps> = ({ originalCode, patchedCode, filePath }) => {
  const origLines = originalCode.split('\n');
  const patchLines = patchedCode.split('\n');

  return (
    <div className="rounded-xl border border-slate-200 bg-white overflow-hidden shadow-sm">
      <div className="flex items-center justify-between px-4 py-2.5 bg-slate-50 border-b border-slate-200 text-xs font-mono text-slate-600">
        <div className="flex items-center gap-2">
          <span className="w-2.5 h-2.5 rounded-full bg-red-400"></span>
          <span className="w-2.5 h-2.5 rounded-full bg-amber-400"></span>
          <span className="w-2.5 h-2.5 rounded-full bg-emerald-400"></span>
          <span className="ml-2 font-medium text-slate-700">{filePath}</span>
        </div>
        <div className="flex items-center gap-4">
          <span className="flex items-center gap-1.5 text-rose-700 font-bold">
            <span className="w-2 h-2 rounded-full bg-rose-500"></span> Before (Original Error)
          </span>
          <span className="flex items-center gap-1.5 text-emerald-700 font-bold">
            <span className="w-2 h-2 rounded-full bg-emerald-500"></span> After (Fixed Code)
          </span>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 divide-y md:divide-y-0 md:divide-x divide-slate-200 text-xs font-mono max-h-[460px] overflow-y-auto">
        {/* Left: Original Code */}
        <div className="p-3 bg-rose-50/20">
          <div className="text-[11px] font-bold text-rose-700 uppercase tracking-wider mb-2 px-1">
            Before Patch (Original with Error)
          </div>
          <div className="space-y-0.5">
            {origLines.map((line, idx) => {
              const isDifferent = idx >= patchLines.length || patchLines[idx] !== line;
              return (
                <div
                  key={idx}
                  className={`flex px-1.5 py-0.5 rounded transition-colors ${
                    isDifferent
                      ? 'bg-rose-100/90 text-rose-950 font-semibold border-l-2 border-rose-500'
                      : 'text-slate-700 hover:bg-slate-100'
                  }`}
                >
                  <span className="w-8 text-right pr-3 select-none text-slate-400">
                    {idx + 1}
                  </span>
                  <span className="whitespace-pre overflow-x-auto flex-1">{line || ' '}</span>
                </div>
              );
            })}
          </div>
        </div>

        {/* Right: Patched Code */}
        <div className="p-3 bg-emerald-50/20">
          <div className="text-[11px] font-bold text-emerald-700 uppercase tracking-wider mb-2 px-1">
            After Patch (Targeted Minimal Fix)
          </div>
          <div className="space-y-0.5">
            {patchLines.map((line, idx) => {
              const isDifferent = idx >= origLines.length || origLines[idx] !== line;
              return (
                <div
                  key={idx}
                  className={`flex px-1.5 py-0.5 rounded transition-colors ${
                    isDifferent
                      ? 'bg-emerald-100/90 text-emerald-950 font-bold border-l-2 border-emerald-600'
                      : 'text-slate-800 hover:bg-slate-100'
                  }`}
                >
                  <span className="w-8 text-right pr-3 select-none text-slate-400">
                    {idx + 1}
                  </span>
                  <span className="whitespace-pre overflow-x-auto flex-1">{line || ' '}</span>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
};
