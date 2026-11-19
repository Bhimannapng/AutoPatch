import React, { useState } from 'react';
import {
  Layers,
  FolderTree,
  FileCode,
  Cpu,
  ShieldAlert,
  Bug,
  Clock,
  HardDrive,
  Info,
  ChevronRight,
  Terminal,
  Activity
} from 'lucide-react';
import { ProjectAnalysisSummary, FileNode } from '../types';

interface ProjectOverviewDashboardProps {
  summary: ProjectAnalysisSummary;
  onSelectFile?: (filePath: string) => void;
}

export const ProjectOverviewDashboard: React.FC<ProjectOverviewDashboardProps> = ({
  summary,
  onSelectFile
}) => {
  const [showExcludedModal, setShowExcludedModal] = useState(false);
  const { capacity_metrics: metrics } = summary;

  // File tree recursive node renderer
  const renderFileNode = (node: FileNode, depth = 0) => {
    const isDir = node.is_dir;
    return (
      <div key={node.path} style={{ paddingLeft: `${depth * 14}px` }} className="text-xs">
        <div
          onClick={() => !isDir && onSelectFile?.(node.path)}
          className={`flex items-center gap-1.5 py-1 px-2 rounded hover:bg-slate-100 cursor-pointer transition-colors ${
            !isDir ? 'text-slate-700 hover:text-indigo-600' : 'text-slate-800 font-semibold'
          }`}
        >
          {isDir ? (
            <FolderTree className="w-3.5 h-3.5 text-indigo-600 shrink-0" />
          ) : (
            <FileCode className="w-3.5 h-3.5 text-emerald-600 shrink-0" />
          )}
          <span className="truncate">{node.name}</span>
          {!isDir && node.size > 0 && (
            <span className="text-[10px] text-slate-400 ml-auto font-mono">
              {Math.round(node.size / 1024)} KB
            </span>
          )}
        </div>
        {node.children && node.children.map((child) => renderFileNode(child, depth + 1))}
      </div>
    );
  };

  return (
    <div className="space-y-6">
      {/* Top Banner: Project Title & Ecosystem Badges */}
      <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-xs">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="px-2.5 py-0.5 bg-indigo-50 border border-indigo-100 text-indigo-700 rounded-full text-xs font-semibold">
                {summary.project_type}
              </span>
              <span className="text-xs text-slate-400">•</span>
              <span className="text-xs text-slate-500 flex items-center gap-1">
                <Clock className="w-3 h-3 text-slate-400" /> {metrics.analysis_duration_ms} ms
              </span>
            </div>
            <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">
              {summary.project_name}
            </h1>
          </div>

          {/* Languages & Frameworks */}
          <div className="flex flex-wrap items-center gap-2">
            {summary.detected_languages.map((lang) => (
              <span
                key={lang}
                className="px-3 py-1 bg-emerald-50 border border-emerald-100 text-emerald-700 text-xs font-semibold rounded-lg"
              >
                {lang}
              </span>
            ))}
            {summary.detected_frameworks.map((fw) => (
              <span
                key={fw}
                className="px-3 py-1 bg-cyan-50 border border-cyan-100 text-cyan-700 text-xs font-semibold rounded-lg"
              >
                {fw}
              </span>
            ))}
          </div>
        </div>

        {/* Entry points */}
        {summary.entry_points && summary.entry_points.length > 0 && (
          <div className="mt-4 pt-4 border-t border-slate-100 flex flex-wrap items-center gap-2 text-xs">
            <span className="text-slate-600 font-semibold flex items-center gap-1">
              <Terminal className="w-3.5 h-3.5 text-indigo-600" /> Main Entry Points:
            </span>
            {summary.entry_points.map((ep) => (
              <span key={ep} className="bg-slate-100 text-slate-800 px-2.5 py-0.5 rounded font-mono">
                {ep}
              </span>
            ))}
          </div>
        )}
      </div>

      {/* Capacity & Processing Metrics Bar */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
        <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-xs">
          <div className="text-slate-500 text-xs font-medium">Source Files</div>
          <div className="text-xl sm:text-2xl font-bold text-slate-900 mt-1">
            {metrics.relevant_source_files}
          </div>
          <div className="text-[11px] text-slate-400 mt-0.5">
            of {metrics.total_files_discovered} discovered
          </div>
        </div>

        <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-xs">
          <div className="text-slate-500 text-xs font-medium">Lines of Code</div>
          <div className="text-xl sm:text-2xl font-bold text-emerald-600 mt-1">
            {metrics.total_lines_of_code.toLocaleString()}
          </div>
          <div className="text-[11px] text-slate-400 mt-0.5">Fully Parsed</div>
        </div>

        <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-xs">
          <div className="text-slate-500 text-xs font-medium">Analysis Time</div>
          <div className="text-xl sm:text-2xl font-bold text-cyan-600 mt-1">
            {(metrics.analysis_duration_ms / 1000).toFixed(2)}s
          </div>
          <div className="text-[11px] text-slate-400 mt-0.5">Sub-second AST</div>
        </div>

        <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-xs">
          <div className="text-slate-500 text-xs font-medium">RAM Consumed</div>
          <div className="text-xl sm:text-2xl font-bold text-amber-600 mt-1">
            {metrics.ram_consumed_mb} MB
          </div>
          <div className="text-[11px] text-slate-400 mt-0.5">Measured Overhead</div>
        </div>

        <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-xs">
          <div className="text-slate-500 text-xs font-medium">Project Size</div>
          <div className="text-xl sm:text-2xl font-bold text-indigo-600 mt-1">
            {Math.round(metrics.extracted_size_bytes / 1024)} KB
          </div>
          <div className="text-[11px] text-slate-400 mt-0.5">Extracted Footprint</div>
        </div>

        <div
          onClick={() => setShowExcludedModal(true)}
          className="bg-white border border-slate-200 hover:border-indigo-300 rounded-xl p-4 cursor-pointer transition-colors shadow-xs"
        >
          <div className="text-slate-500 text-xs font-medium flex items-center justify-between">
            <span>Excluded Items</span>
            <Info className="w-3.5 h-3.5 text-slate-400" />
          </div>
          <div className="text-xl sm:text-2xl font-bold text-slate-800 mt-1">
            {metrics.files_excluded.length}
          </div>
          <div className="text-[11px] text-indigo-600 mt-0.5 hover:underline">
            View rules
          </div>
        </div>
      </div>

      {/* Main Grid: Tree Explorer + Domain Cards */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: Project File Tree */}
        <div className="bg-white border border-slate-200 rounded-2xl p-5 flex flex-col h-[480px] shadow-xs">
          <div className="flex items-center justify-between pb-3 border-b border-slate-100 mb-3">
            <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
              <FolderTree className="w-4 h-4 text-indigo-600" /> Project Structure
            </h3>
            <span className="text-xs text-slate-400 font-mono">
              {metrics.relevant_source_files} files
            </span>
          </div>

          <div className="flex-1 overflow-y-auto space-y-0.5 pr-1 scrollbar-thin">
            {summary.file_tree && summary.file_tree.length > 0 ? (
              summary.file_tree.map((node) => renderFileNode(node))
            ) : (
              <div className="text-xs text-slate-400 text-center py-10">No directory tree available</div>
            )}
          </div>
        </div>

        {/* Right 2 Columns: Multi-Domain Health & Findings */}
        <div className="lg:col-span-2 space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            {/* 1. Defects & Bugs Card */}
            <div className="bg-white border border-rose-200/90 rounded-2xl p-5 shadow-xs">
              <div className="flex items-center justify-between mb-3">
                <div className="w-10 h-10 rounded-xl bg-rose-50 border border-rose-100 flex items-center justify-center text-rose-600">
                  <Bug className="w-5 h-5" />
                </div>
                <span className="text-2xl font-bold text-slate-900">{summary.bugs.length}</span>
              </div>
              <h4 className="text-sm font-bold text-slate-900">Code Defects</h4>
              <p className="text-xs text-slate-500 mt-1">
                Syntax, semantic, and logical errors with verified patches.
              </p>
            </div>

            {/* 2. RAM & Performance Card */}
            <div className="bg-white border border-amber-200/90 rounded-2xl p-5 shadow-xs">
              <div className="flex items-center justify-between mb-3">
                <div className="w-10 h-10 rounded-xl bg-amber-50 border border-amber-100 flex items-center justify-center text-amber-600">
                  <Cpu className="w-5 h-5" />
                </div>
                <span className="text-2xl font-bold text-slate-900">{summary.optimizations.length}</span>
              </div>
              <h4 className="text-sm font-bold text-slate-900">RAM & Performance</h4>
              <p className="text-xs text-slate-500 mt-1">
                O(N²) loops, memory leak risks, and heap allocation bottlenecks.
              </p>
            </div>

            {/* 3. Security & Quality Card */}
            <div className="bg-white border border-purple-200/90 rounded-2xl p-5 shadow-xs">
              <div className="flex items-center justify-between mb-3">
                <div className="w-10 h-10 rounded-xl bg-purple-50 border border-purple-100 flex items-center justify-center text-purple-600">
                  <ShieldAlert className="w-5 h-5" />
                </div>
                <span className="text-2xl font-bold text-slate-900">
                  {summary.security_findings.length + summary.architecture_findings.length}
                </span>
              </div>
              <h4 className="text-sm font-bold text-slate-900">Security & Arch</h4>
              <p className="text-xs text-slate-500 mt-1">
                OWASP credentials exposure, SQL injection, and broken modules.
              </p>
            </div>
          </div>

          {/* Module Dependencies & Cross-File Graph */}
          <div className="bg-white border border-slate-200 rounded-2xl p-5 shadow-xs">
            <div className="flex items-center justify-between mb-3 pb-2 border-b border-slate-100">
              <h4 className="text-sm font-bold text-slate-900 flex items-center gap-2">
                <Activity className="w-4 h-4 text-cyan-600" /> Module Dependency Connections
              </h4>
              <span className="text-xs text-slate-400">
                {summary.dependencies?.length || 0} mapped relations
              </span>
            </div>

            <div className="max-h-56 overflow-y-auto space-y-2 pr-1 scrollbar-thin">
              {summary.dependencies && summary.dependencies.length > 0 ? (
                summary.dependencies.slice(0, 15).map((dep, idx) => (
                  <div
                    key={idx}
                    className="flex items-center justify-between text-xs p-2.5 rounded-lg bg-slate-50 border border-slate-200/70"
                  >
                    <div className="flex items-center gap-2 truncate">
                      <span className="text-slate-800 font-mono truncate">{dep.source_file}</span>
                      <ChevronRight className="w-3.5 h-3.5 text-slate-400 shrink-0" />
                      <span className={`font-mono truncate font-semibold ${dep.is_external ? 'text-cyan-700' : 'text-emerald-700'}`}>
                        {dep.target}
                      </span>
                    </div>
                    <span className="text-[10px] text-slate-500 shrink-0 px-2 py-0.5 rounded bg-white border border-slate-200">
                      {dep.is_external ? 'Third-Party' : 'Internal Module'}
                    </span>
                  </div>
                ))
              ) : (
                <div className="text-xs text-slate-400 text-center py-6">
                  No cross-file import relationships found in this snippet.
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Modal: Excluded Files and Reasons */}
      {showExcludedModal && (
        <div className="fixed inset-0 z-50 bg-slate-900/40 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white border border-slate-200 rounded-2xl max-w-xl w-full p-6 shadow-xl">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100 mb-4">
              <h3 className="text-base font-bold text-slate-900 flex items-center gap-2">
                <Info className="w-4 h-4 text-indigo-600" /> Intelligent Exclusions & Capacity Rules
              </h3>
              <button
                onClick={() => setShowExcludedModal(false)}
                className="text-slate-400 hover:text-slate-700 text-sm"
              >
                ✕
              </button>
            </div>
            <p className="text-xs text-slate-600 mb-4">
              AutoPatch excludes binary artifacts, IDE metadata, and vendor dependency trees to conserve RAM and eliminate token waste while preserving complete source code:
            </p>
            <div className="max-h-72 overflow-y-auto space-y-2 pr-1 scrollbar-thin text-xs">
              {metrics.files_excluded.map((item, idx) => (
                <div key={idx} className="p-2.5 rounded-lg bg-slate-50 border border-slate-200 flex items-start justify-between gap-2">
                  <span className="font-mono text-slate-800 truncate">{item.file}</span>
                  <span className="text-[11px] text-slate-500 shrink-0">{item.reason}</span>
                </div>
              ))}
            </div>
            <div className="mt-5 flex justify-end">
              <button
                onClick={() => setShowExcludedModal(false)}
                className="px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-lg text-xs font-semibold"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
