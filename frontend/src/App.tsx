import React, { useState, useEffect } from 'react';
import {
  ProjectAnalysisSummary,
  BugReport,
  ChangeHistoryEntry,
  SystemHealth
} from './types';
import { ProjectUploadHub } from './components/ProjectUploadHub';
import { ProjectOverviewDashboard } from './components/ProjectOverviewDashboard';
import { AgentsPanel } from './components/AgentsPanel';
import { PatchStudio } from './components/PatchStudio';
import { OptimizationsView } from './components/OptimizationsView';
import { SecurityArchView } from './components/SecurityArchView';
import { HistoryModal } from './components/HistoryModal';
import {
  Shield,
  Layers,
  Bug,
  Cpu,
  ShieldAlert,
  Bot,
  History,
  Download,
  Key,
  FolderOpen,
  CheckCircle2,
  AlertCircle,
  Sparkles,
  Trash2,
  FileText,
  Cloud
} from 'lucide-react';
import { apiFetch, getApiUrl, getApiBaseUrl, setApiBaseUrl } from './apiConfig';

export const App: React.FC = () => {
  // Navigation View State
  const [activeView, setActiveView] = useState<
    'upload' | 'dashboard' | 'agents' | 'patches' | 'performance' | 'security'
  >('upload');

  // Project State
  const [projectSummary, setProjectSummary] = useState<ProjectAnalysisSummary | null>(null);
  const [selectedBug, setSelectedBug] = useState<BugReport | null>(null);
  const [isProcessing, setIsProcessing] = useState<boolean>(false);
  const [progressMessage, setProgressMessage] = useState<string>('');
  const [isProcessingAction, setIsProcessingAction] = useState<boolean>(false);

  // History & System Health
  const [history, setHistory] = useState<ChangeHistoryEntry[]>([]);
  const [isHistoryOpen, setIsHistoryOpen] = useState<boolean>(false);
  const [systemHealth, setSystemHealth] = useState<SystemHealth | null>(null);
  const [apiKeyConfigured, setApiKeyConfigured] = useState<boolean>(false);
  const [isApiKeyModalOpen, setIsApiKeyModalOpen] = useState<boolean>(false);
  const [apiKeyInput, setApiKeyInput] = useState<string>('');
  const [cloudBackendUrl, setCloudBackendUrl] = useState<string>(getApiBaseUrl());

  // Notification Toast
  const [notification, setNotification] = useState<{
    message: string;
    type: 'success' | 'info' | 'error';
  } | null>(null);

  const showNotification = (message: string, type: 'success' | 'info' | 'error' = 'info') => {
    setNotification({ message, type });
    setTimeout(() => setNotification(null), 3500);
  };

  const fetchHealth = async () => {
    try {
      const res = await apiFetch('/api/health');
      if (res.ok) {
        const data: SystemHealth = await res.json();
        setSystemHealth(data);
        if (typeof data.api_key_configured === 'boolean') setApiKeyConfigured(data.api_key_configured);
      }
    } catch (e) {
      console.error('Health check failed', e);
    }
  };

  const fetchHistory = async () => {
    try {
      const res = await apiFetch('/api/history');
      if (res.ok) {
        const data: ChangeHistoryEntry[] = await res.json();
        setHistory(data);
      }
    } catch (e) {
      console.error('History fetch failed', e);
    }
  };

  const fetchCurrentProjectSummary = async () => {
    try {
      const res = await apiFetch('/api/project/summary');
      if (res.ok) {
        const data = await res.json();
        if (data && data.project_name) {
          setProjectSummary(data);
          if (data.bugs && data.bugs.length > 0) {
            setSelectedBug(data.bugs[0]);
          }
        }
      }
    } catch (e) {
      console.error('Summary fetch failed', e);
    }
  };

  useEffect(() => {
    fetchHealth();
    fetchHistory();
    fetchCurrentProjectSummary();
  }, []);

  // When a project is loaded from Upload Hub
  const handleProjectLoaded = (summary: ProjectAnalysisSummary) => {
    setProjectSummary(summary);
    if (summary.bugs && summary.bugs.length > 0) {
      setSelectedBug(summary.bugs[0]);
    }
    setActiveView('dashboard');
    fetchHealth();
    fetchHistory();
  };

  // When a snippet is loaded via paste-code
  const handleSnippetLoaded = async (filename: string) => {
    await fetchCurrentProjectSummary();
    setActiveView('patches');
    fetchHealth();
    fetchHistory();
  };

  // Completely Delete Project & Reset Workspace
  const handleDeleteProject = async () => {
    try {
      const res = await apiFetch('/api/projects/clear', { method: 'POST' });
      if (res.ok) {
        setProjectSummary(null);
        setSelectedBug(null);
        setActiveView('upload');
        await fetchHealth();
        showNotification('Project and all analytics completely deleted.', 'info');
      }
    } catch (e) {
      console.error('Failed to clear workspace', e);
      showNotification('Error clearing project workspace', 'error');
    }
  };

  // Review Action: Accept, Reject, or Revert
  const handleReviewAction = async (bugId: string, action: 'ACCEPTED' | 'REJECTED' | 'REVERT') => {
    setIsProcessingAction(true);
    try {
      const res = await apiFetch('/api/patches/review', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ bug_id: bugId, action })
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: 'Action failed' }));
        throw new Error(err.detail || 'Review action failed');
      }

      await fetchCurrentProjectSummary();
      await fetchHistory();
      showNotification(`Patch ${action.toLowerCase()} successfully!`, 'success');
    } catch (err: any) {
      showNotification(err.message || 'Error processing patch action', 'error');
    } finally {
      setIsProcessingAction(false);
    }
  };

  // Export corrected project ZIP
  const handleExportZip = () => {
    window.location.href = getApiUrl('/api/projects/export');
  };

  // Export PDF Report
  const handleExportPdfReport = () => {
    window.open(getApiUrl('/api/projects/export-report-pdf'), '_blank');
  };

  // Clear all history
  const handleClearAllHistory = async () => {
    try {
      const res = await apiFetch('/api/history', { method: 'DELETE' });
      if (res.ok) {
        setHistory([]);
        showNotification('History cleared.', 'info');
      }
    } catch (e) {
      console.error(e);
    }
  };

  // Delete single history entry
  const handleDeleteEntry = async (entryId: string) => {
    try {
      const res = await apiFetch(`/api/history/${entryId}`, { method: 'DELETE' });
      if (res.ok) {
        setHistory((prev) => prev.filter((h) => h.id !== entryId));
        showNotification('History entry deleted.', 'info');
      }
    } catch (e) {
      console.error(e);
    }
  };

  // Save API Key & Cloud Backend URL
  const handleSaveApiKey = async (e: React.FormEvent) => {
    e.preventDefault();
    if (cloudBackendUrl !== getApiBaseUrl()) {
      setApiBaseUrl(cloudBackendUrl);
    }

    if (apiKeyInput.trim()) {
      try {
        const res = await apiFetch('/api/engine/api-key', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ api_key: apiKeyInput.trim() })
        });

        if (!res.ok) throw new Error('Failed to set API key');
        setApiKeyConfigured(true);
        showNotification('Gemini API key configured securely!', 'success');
      } catch (err: any) {
        showNotification(err.message || 'Error saving API key', 'error');
      }
    }

    setIsApiKeyModalOpen(false);
    fetchHealth();
    fetchCurrentProjectSummary();
  };

  return (
    <div className="min-h-screen bg-slate-50 text-slate-800 flex flex-col font-sans">
      {/* Toast Notification */}
      {notification && (
        <div
          className={`fixed bottom-6 right-6 z-50 px-4 py-3 rounded-xl shadow-xl flex items-center gap-2 text-xs font-semibold backdrop-blur border animate-in slide-in-from-bottom duration-200 ${
            notification.type === 'success'
              ? 'bg-emerald-50 border-emerald-300 text-emerald-800'
              : notification.type === 'error'
              ? 'bg-rose-50 border-rose-300 text-rose-800'
              : 'bg-indigo-50 border-indigo-300 text-indigo-800'
          }`}
        >
          {notification.type === 'success' && <CheckCircle2 className="w-4 h-4 text-emerald-600" />}
          {notification.type === 'error' && <AlertCircle className="w-4 h-4 text-rose-600" />}
          {notification.type === 'info' && <Sparkles className="w-4 h-4 text-indigo-600" />}
          <span>{notification.message}</span>
        </div>
      )}

      {/* TOP NAVIGATION BAR */}
      <header className="border-b border-slate-200 bg-white sticky top-0 z-40 shadow-xs">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 h-16 flex items-center justify-between gap-4">
          {/* Logo & Title */}
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-indigo-600 flex items-center justify-center text-white shadow-sm">
              <Shield className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-extrabold text-base sm:text-lg text-slate-900 tracking-tight">
                  AutoPatch
                </span>
                <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-indigo-50 text-indigo-700 border border-indigo-100">
                  AI Software Platform
                </span>
              </div>
              <div className="text-[11px] text-slate-500 hidden sm:block">
                Project Analysis, Autonomous Bug Repair & Multi-Agent Intelligence
              </div>
            </div>
          </div>

          {/* Action Buttons: Delete Project, API Key, History, Export */}
          <div className="flex items-center gap-2">
            {/* Delete / Clear Project Button (Prominent when project loaded) */}
            {projectSummary && (
              <button
                onClick={handleDeleteProject}
                className="px-3 py-1.5 rounded-xl border border-rose-200 bg-rose-50 hover:bg-rose-100 text-rose-700 transition-colors flex items-center gap-1.5 text-xs font-semibold"
                title="Completely delete current project and reset workspace"
              >
                <Trash2 className="w-3.5 h-3.5" />
                <span className="hidden sm:inline">Delete Project</span>
              </button>
            )}

            <button
              onClick={() => setIsApiKeyModalOpen(true)}
              className={`p-2 sm:px-3 sm:py-1.5 rounded-xl border text-xs font-semibold flex items-center gap-1.5 transition-colors ${
                apiKeyConfigured
                  ? 'bg-emerald-50 border-emerald-200 text-emerald-700'
                  : 'bg-white border-slate-200 text-slate-600 hover:text-slate-900'
              }`}
              title="Configure Gemini API Key"
            >
              <Key className="w-4 h-4 text-indigo-600" />
              <span className="hidden md:inline">{apiKeyConfigured ? 'API Connected' : 'Set Key'}</span>
            </button>

            <button
              onClick={() => setIsHistoryOpen(true)}
              className="p-2 sm:px-3 sm:py-1.5 rounded-xl bg-white border border-slate-200 text-slate-700 hover:bg-slate-50 transition-colors flex items-center gap-1.5 text-xs font-semibold"
              title="Audit & Rollback History"
            >
              <History className="w-4 h-4 text-slate-500" />
              <span className="hidden md:inline">History ({history.length})</span>
            </button>

            {projectSummary && (
              <>
                <button
                  onClick={handleExportPdfReport}
                  className="p-2 sm:px-3 sm:py-1.5 rounded-xl bg-purple-600 hover:bg-purple-700 text-white shadow-xs transition-colors flex items-center gap-1.5 text-xs font-semibold"
                  title="Export Complete Analysis Report as PDF"
                >
                  <FileText className="w-4 h-4" />
                  <span className="hidden sm:inline">Export Result</span>
                </button>

                <button
                  onClick={handleExportZip}
                  className="p-2 sm:px-3.5 sm:py-1.5 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white shadow-xs transition-colors flex items-center gap-1.5 text-xs font-semibold"
                  title="Export Fully Corrected Project as ZIP"
                >
                  <Download className="w-4 h-4" />
                  <span className="hidden sm:inline">Export Corrected</span>
                </button>
              </>
            )}
          </div>
        </div>
      </header>

      {/* SECONDARY VIEW NAVIGATION TABS (Strict Requested Order) */}
      <nav className="border-b border-slate-200 bg-white shadow-xs">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 flex items-center gap-1 overflow-x-auto py-2 scrollbar-none text-xs font-semibold">
          <button
            onClick={() => setActiveView('upload')}
            className={`flex items-center gap-2 py-2 px-3.5 rounded-lg transition-colors whitespace-nowrap ${
              activeView === 'upload'
                ? 'bg-indigo-50 text-indigo-700 font-bold'
                : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
            }`}
          >
            <FolderOpen className="w-3.5 h-3.5 text-indigo-600" />
            <span>Project Hub</span>
          </button>

          <button
            onClick={() => setActiveView('dashboard')}
            className={`flex items-center gap-2 py-2 px-3.5 rounded-lg transition-colors whitespace-nowrap ${
              activeView === 'dashboard'
                ? 'bg-indigo-50 text-indigo-700 font-bold'
                : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
            }`}
          >
            <Layers className="w-3.5 h-3.5 text-indigo-600" />
            <span>Architecture & Overview</span>
          </button>

          <button
            onClick={() => setActiveView('agents')}
            className={`flex items-center gap-2 py-2 px-3.5 rounded-lg transition-colors whitespace-nowrap ${
              activeView === 'agents'
                ? 'bg-indigo-50 text-indigo-700 font-bold'
                : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
            }`}
          >
            <Bot className="w-3.5 h-3.5 text-cyan-600" />
            <span>Three AI Specialists</span>
            <span className="px-1.5 py-0.2 rounded-full bg-cyan-100 text-cyan-800 text-[10px]">
              Active
            </span>
          </button>

          <button
            onClick={() => setActiveView('patches')}
            className={`flex items-center gap-2 py-2 px-3.5 rounded-lg transition-colors whitespace-nowrap ${
              activeView === 'patches'
                ? 'bg-indigo-50 text-indigo-700 font-bold'
                : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
            }`}
          >
            <Bug className="w-3.5 h-3.5 text-rose-600" />
            <span>Defects & Patches</span>
            {projectSummary && projectSummary.bugs.length > 0 && (
              <span className="px-1.5 py-0.2 rounded-full bg-rose-100 text-rose-800 text-[10px]">
                {projectSummary.bugs.length}
              </span>
            )}
          </button>

          <button
            onClick={() => setActiveView('performance')}
            className={`flex items-center gap-2 py-2 px-3.5 rounded-lg transition-colors whitespace-nowrap ${
              activeView === 'performance'
                ? 'bg-indigo-50 text-indigo-700 font-bold'
                : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
            }`}
          >
            <Cpu className="w-3.5 h-3.5 text-amber-600" />
            <span>RAM & Performance</span>
            {projectSummary && projectSummary.optimizations.length > 0 && (
              <span className="px-1.5 py-0.2 rounded-full bg-amber-100 text-amber-800 text-[10px]">
                {projectSummary.optimizations.length}
              </span>
            )}
          </button>

          <button
            onClick={() => setActiveView('security')}
            className={`flex items-center gap-2 py-2 px-3.5 rounded-lg transition-colors whitespace-nowrap ${
              activeView === 'security'
                ? 'bg-indigo-50 text-indigo-700 font-bold'
                : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
            }`}
          >
            <ShieldAlert className="w-3.5 h-3.5 text-purple-600" />
            <span>Security & Modularity</span>
            {projectSummary && (
              <span className="px-1.5 py-0.2 rounded-full bg-purple-100 text-purple-800 text-[10px]">
                {projectSummary.security_findings.length + projectSummary.architecture_findings.length}
              </span>
            )}
          </button>
        </div>
      </nav>

      {/* MAIN VIEW CONTENT */}
      <main className="flex-1 max-w-7xl w-full mx-auto p-4 sm:p-6 lg:p-8">
        {activeView === 'upload' && (
          <ProjectUploadHub
            onProjectLoaded={handleProjectLoaded}
            onSnippetLoaded={handleSnippetLoaded}
            isProcessing={isProcessing}
            setIsProcessing={setIsProcessing}
            progressMessage={progressMessage}
            setProgressMessage={setProgressMessage}
            showNotification={showNotification}
          />
        )}

        {activeView === 'dashboard' && (
          projectSummary ? (
            <ProjectOverviewDashboard
              summary={projectSummary}
              onSelectFile={(f) => {
                setActiveView('patches');
              }}
            />
          ) : (
            <div className="bg-white border border-slate-200 rounded-2xl p-12 text-center shadow-xs">
              <FolderOpen className="w-12 h-12 text-slate-400 mx-auto mb-3" />
              <h3 className="text-base font-bold text-slate-800 mb-1">No Project Loaded</h3>
              <p className="text-xs text-slate-500 mb-4 max-w-sm mx-auto">
                Upload a project ZIP, clone a GitHub repository, or paste code to generate complete architecture intelligence.
              </p>
              <button
                onClick={() => setActiveView('upload')}
                className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl text-xs font-semibold shadow-xs transition-all"
              >
                Go to Project Hub
              </button>
            </div>
          )
        )}

        {activeView === 'agents' && (
          <AgentsPanel summary={projectSummary} showNotification={showNotification} />
        )}

        {activeView === 'patches' && (
          <PatchStudio
            bugs={projectSummary?.bugs || []}
            selectedBug={selectedBug}
            onSelectBug={(b) => setSelectedBug(b)}
            onReviewAction={handleReviewAction}
            isProcessingAction={isProcessingAction}
            showNotification={showNotification}
            onExportZip={handleExportZip}
          />
        )}

        {activeView === 'performance' && (
          <OptimizationsView optimizations={projectSummary?.optimizations || []} />
        )}

        {activeView === 'security' && (
          <SecurityArchView
            securityFindings={projectSummary?.security_findings || []}
            architectureFindings={projectSummary?.architecture_findings || []}
          />
        )}
      </main>

      {/* MODAL: API KEY CONFIGURATION */}
      {isApiKeyModalOpen && (
        <div className="fixed inset-0 z-50 bg-slate-900/40 backdrop-blur-xs flex items-center justify-center p-4">
          <form
            onSubmit={handleSaveApiKey}
            className="bg-white border border-slate-200 rounded-2xl max-w-md w-full p-6 shadow-xl space-y-4"
          >
            <div className="flex items-center justify-between pb-2 border-b border-slate-100">
              <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
                <Key className="w-4 h-4 text-indigo-600" /> Platform & Cloud Configuration
              </h3>
              <button
                type="button"
                onClick={() => setIsApiKeyModalOpen(false)}
                className="text-slate-400 hover:text-slate-700 text-sm"
              >
                ✕
              </button>
            </div>

            <p className="text-xs text-slate-600 leading-relaxed">
              Configure your Gemini AI credentials and optional Cloud Backend URL (for 24/7 cloud operation even when your local machine is closed).
            </p>

            <div>
              <label className="block text-xs font-bold text-slate-700 mb-1">
                Gemini API Key:
              </label>
              <input
                type="password"
                placeholder="AIzaSy... or AQ..."
                value={apiKeyInput}
                onChange={(e) => setApiKeyInput(e.target.value)}
                className="w-full bg-slate-50 border border-slate-300 rounded-xl px-4 py-2 text-slate-900 placeholder-slate-400 focus:outline-none focus:border-indigo-600 text-xs font-mono"
              />
              <span className="text-[10px] text-slate-400">Leave blank if already configured on backend.</span>
            </div>

            <div>
              <label className="block text-xs font-bold text-slate-700 mb-1 flex items-center gap-1.5">
                <Cloud className="w-3.5 h-3.5 text-indigo-600" />
                Cloud Backend Server URL (Optional / Google Colab):
              </label>
              <input
                type="text"
                placeholder="https://xxxx.trycloudflare.com or leave empty for local"
                value={cloudBackendUrl}
                onChange={(e) => setCloudBackendUrl(e.target.value)}
                className="w-full bg-slate-50 border border-slate-300 rounded-xl px-4 py-2 text-slate-900 placeholder-slate-400 focus:outline-none focus:border-indigo-600 text-xs font-mono"
              />
              <span className="text-[10px] text-slate-500">
                To run AutoPatch when laptop is closed, run the Colab backend and paste its HTTPS tunnel URL here.
              </span>
            </div>

            <div className="flex items-center justify-end gap-2 pt-2">
              <button
                type="button"
                onClick={() => setIsApiKeyModalOpen(false)}
                className="px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-xl text-xs font-semibold"
              >
                Cancel
              </button>
              <button
                type="submit"
                className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl text-xs font-semibold shadow-xs"
              >
                Save & Connect
              </button>
            </div>
          </form>
        </div>
      )}

      {/* MODAL: AUDIT & ROLLBACK HISTORY */}
      <HistoryModal
        isOpen={isHistoryOpen}
        onClose={() => setIsHistoryOpen(false)}
        history={history}
        onExportZip={handleExportZip}
        onClearAllHistory={handleClearAllHistory}
        onDeleteEntry={handleDeleteEntry}
      />
    </div>
  );
};

export default App;
