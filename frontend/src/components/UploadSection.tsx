import React, { useState, useRef } from 'react';
import { Upload, Play, Clipboard, Trash2, RefreshCw, FileCode, Check } from 'lucide-react';
import { EngineMode } from '../types';

interface UploadSectionProps {
  currentProject: string | null;
  totalFiles: number;
  totalLines: number;
  isScanning: boolean;
  engineMode?: EngineMode;
  onPasteCode: (code: string) => Promise<void>;
  onUploadZip: (file: File) => Promise<void>;
  onClearCode: () => Promise<void>;
  onRunScan: () => Promise<void>;
}

export const UploadSection: React.FC<UploadSectionProps> = ({
  currentProject,
  totalFiles,
  totalLines,
  isScanning,
  engineMode = 'AST',
  onPasteCode,
  onUploadZip,
  onClearCode,
  onRunScan
}) => {
  const [mode, setMode] = useState<'paste' | 'upload'>('paste');
  const [pastedCode, setPastedCode] = useState<string>('');
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      onUploadZip(e.target.files[0]);
    }
  };

  const handlePasteSubmit = () => {
    if (pastedCode.trim()) {
      onPasteCode(pastedCode);
    }
  };

  const handleClear = async () => {
    setPastedCode('');
    await onClearCode();
  };

  return (
    <div className="rounded-2xl border border-slate-200/90 bg-white p-6 shadow-sm hover:shadow-md transition-shadow space-y-5">
      {/* Top Header: Mode Switcher Tabs + Clear Code + Status */}
      <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-100 pb-4">
        <div className="flex items-center gap-3">
          {/* Paste Tab Button */}
          <button
            onClick={() => setMode('paste')}
            className={`px-5 py-2.5 rounded-xl text-sm font-bold flex items-center gap-2 transition-all ${
              mode === 'paste'
                ? 'bg-indigo-600 text-white shadow-md shadow-indigo-100 scale-[1.02]'
                : 'bg-slate-100 text-slate-700 hover:bg-slate-200 hover:text-slate-900'
            }`}
          >
            <Clipboard className="w-4 h-4" />
            Paste Code
          </button>

          {/* Upload Tab Button */}
          <button
            onClick={() => setMode('upload')}
            className={`px-5 py-2.5 rounded-xl text-sm font-bold flex items-center gap-2 transition-all ${
              mode === 'upload'
                ? 'bg-indigo-600 text-white shadow-md shadow-indigo-100 scale-[1.02]'
                : 'bg-slate-100 text-slate-700 hover:bg-slate-200 hover:text-slate-900'
            }`}
          >
            <Upload className="w-4 h-4" />
            Upload File / .Zip
          </button>

          <span className="text-slate-200 hidden sm:inline">|</span>

          {/* Clear Code Button */}
          <button
            onClick={handleClear}
            disabled={isScanning || (!pastedCode && !currentProject)}
            className="px-4 py-2.5 rounded-xl text-sm font-semibold bg-slate-100 hover:bg-rose-50 hover:text-rose-700 hover:border-rose-200 text-slate-600 border border-slate-200 transition-all flex items-center gap-2 disabled:opacity-40 disabled:hover:bg-slate-100 disabled:hover:text-slate-600 active:scale-95"
            title="Clear all source code and reset workspace"
          >
            <Trash2 className="w-4 h-4 text-slate-500 group-hover:text-rose-600" />
            Clear Code
          </button>
        </div>

        {/* Workspace Info Pill */}
        <div className="flex items-center gap-2.5 px-4 py-2 rounded-xl bg-slate-50 border border-slate-200/80 text-xs font-mono text-slate-600">
          <span className={`w-2.5 h-2.5 rounded-full ${currentProject ? 'bg-emerald-500 animate-pulse' : 'bg-slate-300'}`}></span>
          <span className="font-semibold text-slate-800">{currentProject || 'Empty Workspace'}</span>
          <span className="text-slate-300">•</span>
          <span className="text-slate-500">{totalLines} lines</span>
          {totalFiles > 1 && (
            <>
              <span className="text-slate-300">•</span>
              <span className="text-slate-500">{totalFiles} files</span>
            </>
          )}
        </div>
      </div>

      {/* Mode 1: Paste Code Box */}
      {mode === 'paste' ? (
        <div className="space-y-4">
          <div className="relative rounded-2xl border border-slate-200 focus-within:border-indigo-500 focus-within:ring-4 focus-within:ring-indigo-500/10 transition-all overflow-hidden bg-slate-50/60">
            <textarea
              value={pastedCode}
              onChange={(e) => setPastedCode(e.target.value)}
              placeholder="Paste your code or upload a source file to begin analysis."
              rows={8}
              className="w-full p-4 text-xs font-mono bg-transparent text-slate-800 focus:outline-none resize-y placeholder:text-slate-400 placeholder:italic leading-relaxed"
            />
            {!pastedCode && (
              <div className="absolute inset-0 pointer-events-none flex flex-col items-center justify-center p-6 text-center space-y-2">
                <FileCode className="w-8 h-8 text-slate-300" />
                <span className="text-slate-400 text-sm font-medium">
                  Paste your code or upload a source file to begin analysis.
                </span>
                <span className="text-slate-400 text-xs">
                  Supports Python, Java, JavaScript, TypeScript, C/C++, and HTML.
                </span>
              </div>
            )}
          </div>

          {/* Bottom Bar: Engine Description + Large Visible Scan Button */}
          <div className="flex flex-col sm:flex-row items-center justify-between gap-3 pt-1">
            <div className="text-xs text-slate-500 flex items-center gap-2">
              <span className="font-bold text-slate-700">Active Engine:</span>
              <span>
                {engineMode === 'AST' && 'Pure Multi-Language AST Engine (Python, Java, JS syntax & scope analysis)'}
                {engineMode === 'LLM' && 'Google Gemini GenAI Engine (Cloud AI multi-language review & HTML markup validation)'}
                {engineMode === 'COMBINED' && 'Two-Stage Combined Pipeline (Deterministic AST ground truth + Gemini AI)'}
                {engineMode === 'SANDBOX' && 'Isolated Sandbox Engine (Test execution and regression validation)'}
              </span>
            </div>

            {/* Big Main Scan Button */}
            <button
              onClick={handlePasteSubmit}
              disabled={isScanning || !pastedCode.trim()}
              className="w-full sm:w-auto px-8 py-3 rounded-xl text-sm font-bold bg-indigo-600 hover:bg-indigo-700 active:scale-[0.98] text-white shadow-md shadow-indigo-200 hover:shadow-lg hover:shadow-indigo-300 transition-all flex items-center justify-center gap-2 disabled:opacity-40 disabled:cursor-not-allowed disabled:shadow-none"
            >
              {isScanning ? (
                <>
                  <RefreshCw className="w-4 h-4 animate-spin" />
                  Analyzing with {engineMode}...
                </>
              ) : (
                <>
                  <Play className="w-4 h-4 fill-white" />
                  Scan Code & Fix Bugs
                </>
              )}
            </button>
          </div>
        </div>
      ) : (
        /* Mode 2: Upload File / Zip */
        <div className="p-8 border-2 border-dashed border-slate-200 hover:border-indigo-400 rounded-2xl bg-slate-50/70 text-center space-y-4 transition-colors">
          <input
            type="file"
            ref={fileInputRef}
            onChange={handleFileChange}
            accept=".zip,.py,.java,.js,.ts,.html,.htm,.cpp,.c,.go,.json"
            className="hidden"
          />
          <div className="flex flex-col items-center justify-center gap-3">
            <div className="p-4 bg-white rounded-2xl border border-slate-200 shadow-sm text-indigo-600">
              <Upload className="w-7 h-7" />
            </div>
            <div>
              <div className="text-sm font-bold text-slate-800">
                Upload source file or project archive (.zip)
              </div>
              <p className="text-xs text-slate-500 mt-1">
                Drop your code files (.py, .java, .js, .html) or zipped repository here for automatic analysis.
              </p>
            </div>
          </div>
          <button
            onClick={() => fileInputRef.current?.click()}
            disabled={isScanning}
            className="px-6 py-2.5 rounded-xl text-sm font-bold bg-white hover:bg-slate-100 text-slate-800 border border-slate-200 shadow-sm hover:shadow transition-all"
          >
            Select File from Computer
          </button>
        </div>
      )}
    </div>
  );
};
