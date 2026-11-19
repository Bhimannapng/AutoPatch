import React from 'react';
import {
  ShieldAlert,
  Lock,
  Layers,
  AlertOctagon,
  CheckCircle2,
  FileCode,
  ArrowRight,
  ShieldCheck,
  Activity
} from 'lucide-react';
import { SecurityFinding, ArchitectureFinding } from '../types';

interface SecurityArchViewProps {
  securityFindings: SecurityFinding[];
  architectureFindings: ArchitectureFinding[];
}

export const SecurityArchView: React.FC<SecurityArchViewProps> = ({
  securityFindings,
  architectureFindings
}) => {
  return (
    <div className="space-y-8">
      {/* 1. OWASP & Code Security Flaws */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-purple-50 border border-purple-100 flex items-center justify-center text-purple-600">
              <Lock className="w-4 h-4" />
            </div>
            <div>
              <h3 className="text-base font-bold text-slate-900">Security Vulnerabilities & Secrets</h3>
              <p className="text-xs text-slate-500">
                OWASP injection risks, exposed credentials, and unsafe execution patterns.
              </p>
            </div>
          </div>
          <span className="text-xs font-semibold px-2.5 py-1 rounded-full bg-purple-50 text-purple-700 border border-purple-200">
            {securityFindings.length} Detected
          </span>
        </div>

        {securityFindings.length === 0 ? (
          <div className="bg-white border border-slate-200 rounded-2xl p-8 text-center shadow-xs">
            <ShieldCheck className="w-8 h-8 text-emerald-600 mx-auto mb-2" />
            <div className="text-sm font-bold text-slate-900">No Security Vulnerabilities Detected</div>
            <div className="text-xs text-slate-500 mt-0.5">
              Source files do not contain hardcoded credentials or obvious SQL/command injections.
            </div>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {securityFindings.map((sec) => (
              <div
                key={sec.id}
                className="bg-white border border-purple-200 rounded-2xl p-5 shadow-xs flex flex-col justify-between"
              >
                <div>
                  <div className="flex items-center justify-between gap-2 mb-2">
                    <span className="px-2.5 py-0.5 rounded text-[10px] font-bold bg-purple-50 text-purple-700 border border-purple-100 uppercase">
                      {sec.vulnerability_type}
                    </span>
                    <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-rose-50 text-rose-700 border border-rose-100">
                      {sec.severity}
                    </span>
                  </div>

                  <h4 className="text-sm font-bold text-slate-900 mb-1">{sec.title}</h4>
                  <div className="text-xs text-slate-500 font-mono mb-3">
                    {sec.file_path}:{sec.line_start}
                  </div>

                  <div className="text-xs text-slate-700 bg-slate-50 p-3 rounded-xl border border-slate-200 mb-3 leading-relaxed">
                    {sec.description}
                  </div>
                </div>

                <div className="p-3 rounded-xl bg-purple-50/70 border border-purple-200 text-purple-900 text-xs">
                  <div className="font-semibold text-purple-800 mb-0.5">Recommended Remediation:</div>
                  <div>{sec.remediation}</div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* 2. Modularity & Architecture Consistency */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-cyan-50 border border-cyan-100 flex items-center justify-center text-cyan-600">
              <Activity className="w-4 h-4" />
            </div>
            <div>
              <h3 className="text-base font-bold text-slate-900">Architecture & Modularity Consistency</h3>
              <p className="text-xs text-slate-500">
                Cross-file references, broken imports, and frontend/backend endpoint alignment.
              </p>
            </div>
          </div>
          <span className="text-xs font-semibold px-2.5 py-1 rounded-full bg-cyan-50 text-cyan-700 border border-cyan-200">
            {architectureFindings.length} Notices
          </span>
        </div>

        {architectureFindings.length === 0 ? (
          <div className="bg-white border border-slate-200 rounded-2xl p-8 text-center shadow-xs">
            <CheckCircle2 className="w-8 h-8 text-emerald-600 mx-auto mb-2" />
            <div className="text-sm font-bold text-slate-900">Clean Architectural Modularity</div>
            <div className="text-xs text-slate-500 mt-0.5">
              All internal module imports and API routes resolve cleanly without dangling endpoints.
            </div>
          </div>
        ) : (
          <div className="space-y-3">
            {architectureFindings.map((arch) => (
              <div
                key={arch.id}
                className="bg-white border border-slate-200 rounded-2xl p-5 shadow-xs flex flex-col sm:flex-row sm:items-center justify-between gap-4"
              >
                <div>
                  <div className="flex items-center gap-2 mb-1">
                    <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-cyan-50 text-cyan-700 border border-cyan-100 uppercase">
                      {arch.category}
                    </span>
                    <span className="text-xs font-mono text-slate-500">
                      {arch.affected_files.join(', ')}
                    </span>
                  </div>
                  <h4 className="text-sm font-bold text-slate-900">{arch.title}</h4>
                  <p className="text-xs text-slate-600 mt-1 max-w-2xl">{arch.description}</p>
                </div>

                <div className="text-xs bg-slate-50 p-3 rounded-xl border border-slate-200 text-cyan-900 sm:max-w-xs shrink-0">
                  <div className="font-semibold text-cyan-800 mb-0.5">Recommendation:</div>
                  <div>{arch.recommendation}</div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
