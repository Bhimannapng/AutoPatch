import React, { useState, useRef } from 'react';
import {
  Upload,
  GitBranch,
  FolderOpen,
  Code2,
  FileArchive,
  ArrowRight,
  Play,
  CheckCircle2,
  AlertCircle,
  FileCode,
  Lock,
  Sparkles
} from 'lucide-react';
import { ProjectAnalysisSummary } from '../types';
import { apiFetch } from '../apiConfig';

interface ProjectUploadHubProps {
  onProjectLoaded: (summary: ProjectAnalysisSummary) => void;
  onSnippetLoaded: (filename: string) => void;
  isProcessing: boolean;
  setIsProcessing: (val: boolean) => void;
  progressMessage: string;
  setProgressMessage: (msg: string) => void;
  showNotification: (msg: string, type: 'success' | 'info' | 'error') => void;
}

export const ProjectUploadHub: React.FC<ProjectUploadHubProps> = ({
  onProjectLoaded,
  onSnippetLoaded,
  isProcessing,
  setIsProcessing,
  progressMessage,
  setProgressMessage,
  showNotification
}) => {
  const [activeTab, setActiveTab] = useState<'zip' | 'github' | 'folder' | 'snippet'>('zip');

  // GitHub State
  const [githubUrl, setGithubUrl] = useState('');
  const [githubBranch, setGithubBranch] = useState('');
  const [githubToken, setGithubToken] = useState('');

  // Snippet / Paste Code State
  const [snippetCode, setSnippetCode] = useState('');
  const [selectedLanguage, setSelectedLanguage] = useState<'python' | 'java' | 'javascript' | 'html'>('python');

  const zipInputRef = useRef<HTMLInputElement>(null);
  const folderInputRef = useRef<HTMLInputElement>(null);

  // 1. Handle ZIP Upload
  const handleZipUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    if (!file.name.endsWith('.zip')) {
      showNotification('Please upload a valid .zip project archive.', 'error');
      return;
    }

    setIsProcessing(true);
    setProgressMessage('Extracting archive & scanning project with LLM...');

    try {
      const formData = new FormData();
      formData.append('file', file);

      const res = await apiFetch('/api/project/upload-zip', {
        method: 'POST',
        body: formData
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: 'Upload failed' }));
        throw new Error(err.detail || 'Failed to process project archive');
      }

      const summary: ProjectAnalysisSummary = await res.json();
      onProjectLoaded(summary);
      showNotification(`Successfully indexed project: ${summary.project_name}`, 'success');
    } catch (err: any) {
      showNotification(err.message || 'Error uploading archive', 'error');
    } finally {
      setIsProcessing(false);
      if (zipInputRef.current) zipInputRef.current.value = '';
    }
  };

  // 2. Handle GitHub Clone
  const handleGithubClone = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!githubUrl.trim()) {
      showNotification('Please enter a valid GitHub repository URL.', 'error');
      return;
    }

    setIsProcessing(true);
    setProgressMessage('Cloning repository via Git & mapping architecture with LLM...');

    try {
      const res = await apiFetch('/api/project/github-clone', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          repo_url: githubUrl.trim(),
          branch: githubBranch.trim() || undefined,
          auth_token: githubToken.trim() || undefined
        })
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: 'Git clone failed' }));
        throw new Error(err.detail || 'Failed to clone repository');
      }

      const summary: ProjectAnalysisSummary = await res.json();
      onProjectLoaded(summary);
      showNotification(`Repository cloned & analyzed: ${summary.project_name}`, 'success');
    } catch (err: any) {
      showNotification(err.message || 'GitHub clone error', 'error');
    } finally {
      setIsProcessing(false);
    }
  };

  // 3. Handle Folder Upload
  const handleFolderUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (!files || files.length === 0) return;

    setIsProcessing(true);
    setProgressMessage(`Reading ${files.length} files from directory...`);

    try {
      const formData = new FormData();
      for (let i = 0; i < files.length; i++) {
        formData.append('files', files[i]);
      }
      formData.append('folder_name', files[0].webkitRelativePath?.split('/')[0] || 'Uploaded-Folder');

      const res = await apiFetch('/api/project/upload-folder', {
        method: 'POST',
        body: formData
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: 'Folder upload failed' }));
        throw new Error(err.detail || 'Failed to process folder');
      }

      const summary: ProjectAnalysisSummary = await res.json();
      onProjectLoaded(summary);
      showNotification(`Folder structure mapped: ${summary.project_name}`, 'success');
    } catch (err: any) {
      showNotification(err.message || 'Error uploading folder', 'error');
    } finally {
      setIsProcessing(false);
      if (folderInputRef.current) folderInputRef.current.value = '';
    }
  };

  // 4. Handle Snippet Analysis (Option D: Code Error Finder)
  const handleSnippetSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!snippetCode.trim()) {
      showNotification('Please paste source code first.', 'error');
      return;
    }

    setIsProcessing(true);
    setProgressMessage('Analyzing code with LLM & sandbox testing...');

    const extMap = { python: 'code_snippet.py', java: 'Main.java', javascript: 'script.js', html: 'index.html' };
    const fname = extMap[selectedLanguage];

    try {
      const formData = new FormData();
      formData.append('code', snippetCode);
      formData.append('filename', fname);

      const res = await apiFetch('/api/projects/paste-code', {
        method: 'POST',
        body: formData
      });

      if (!res.ok) throw new Error('Failed to analyze snippet');
      onSnippetLoaded(fname);
      showNotification(`Analyzed ${fname} successfully with LLM.`, 'success');
    } catch (err: any) {
      showNotification(err.message || 'Snippet analysis failed', 'error');
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <div className="w-full max-w-4xl mx-auto bg-white border border-slate-200/90 rounded-2xl p-6 sm:p-8 shadow-sm">
      {/* Header */}
      <div className="text-center mb-8">
        <div className="inline-flex items-center gap-1.5 px-3 py-1 bg-indigo-50 border border-indigo-100 rounded-full text-indigo-700 text-xs font-semibold mb-3">
          <Sparkles className="w-3.5 h-3.5 text-indigo-600" />
          <span>Autonomous Project Intelligence Platform</span>
        </div>
        <h2 className="text-2xl sm:text-3xl font-bold text-slate-900 tracking-tight">
          Upload & Analyze Any Software Project
        </h2>
        <p className="text-slate-600 text-sm sm:text-base mt-2 max-w-xl mx-auto">
          Upload a ZIP archive, GitHub repository, project folder, or paste code. AutoPatch understands the complete project structure and deploys 3 specialized AI engineering agents.
        </p>
      </div>

      {/* Tabs */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 p-1.5 bg-slate-100/80 border border-slate-200 rounded-xl mb-6">
        <button
          type="button"
          onClick={() => setActiveTab('zip')}
          className={`flex items-center justify-center gap-2 py-2.5 px-3 rounded-lg font-semibold text-xs sm:text-sm transition-all ${
            activeTab === 'zip'
              ? 'bg-white text-indigo-600 shadow-sm border border-slate-200/80'
              : 'text-slate-600 hover:text-slate-900 hover:bg-slate-200/50'
          }`}
        >
          <FileArchive className="w-4 h-4" />
          <span>Upload ZIP</span>
        </button>

        <button
          type="button"
          onClick={() => setActiveTab('github')}
          className={`flex items-center justify-center gap-2 py-2.5 px-3 rounded-lg font-semibold text-xs sm:text-sm transition-all ${
            activeTab === 'github'
              ? 'bg-white text-indigo-600 shadow-sm border border-slate-200/80'
              : 'text-slate-600 hover:text-slate-900 hover:bg-slate-200/50'
          }`}
        >
          <GitBranch className="w-4 h-4" />
          <span>GitHub Repo</span>
        </button>

        <button
          type="button"
          onClick={() => setActiveTab('folder')}
          className={`flex items-center justify-center gap-2 py-2.5 px-3 rounded-lg font-semibold text-xs sm:text-sm transition-all ${
            activeTab === 'folder'
              ? 'bg-white text-indigo-600 shadow-sm border border-slate-200/80'
              : 'text-slate-600 hover:text-slate-900 hover:bg-slate-200/50'
          }`}
        >
          <FolderOpen className="w-4 h-4" />
          <span>Project Folder</span>
        </button>

        <button
          type="button"
          onClick={() => setActiveTab('snippet')}
          className={`flex items-center justify-center gap-2 py-2.5 px-3 rounded-lg font-semibold text-xs sm:text-sm transition-all ${
            activeTab === 'snippet'
              ? 'bg-white text-indigo-600 shadow-sm border border-slate-200/80'
              : 'text-slate-600 hover:text-slate-900 hover:bg-slate-200/50'
          }`}
        >
          <Code2 className="w-4 h-4" />
          <span>Single File</span>
        </button>
      </div>

      {/* Progress Notification Banner */}
      {isProcessing && (
        <div className="mb-6 p-4 bg-indigo-50 border border-indigo-200 rounded-xl flex items-center gap-3 animate-pulse">
          <div className="w-5 h-5 border-2 border-indigo-600 border-t-transparent rounded-full animate-spin" />
          <div className="text-sm font-semibold text-indigo-900">{progressMessage || 'Processing project...'}</div>
        </div>
      )}

      {/* TAB CONTENT */}
      {/* 1. ZIP Archive */}
      {activeTab === 'zip' && (
        <div
          onClick={() => zipInputRef.current?.click()}
          className="group relative border-2 border-dashed border-slate-300 hover:border-indigo-500 bg-slate-50/70 hover:bg-indigo-50/20 rounded-2xl p-10 text-center cursor-pointer transition-all duration-200"
        >
          <input
            ref={zipInputRef}
            type="file"
            accept=".zip"
            onChange={handleZipUpload}
            className="hidden"
            disabled={isProcessing}
          />
          <div className="w-14 h-14 mx-auto mb-4 bg-indigo-100 text-indigo-600 rounded-2xl flex items-center justify-center group-hover:scale-110 transition-transform">
            <Upload className="w-7 h-7" />
          </div>
          <h3 className="text-base font-bold text-slate-900 mb-1">Click or drag a project ZIP file here</h3>
          <p className="text-slate-500 text-xs sm:text-sm max-w-md mx-auto">
            Extracts project files safely, discovers frameworks, maps dependencies, and initiates full-project LLM intelligence.
          </p>
          <div className="mt-4 inline-flex items-center gap-1.5 text-xs text-indigo-600 font-semibold">
            <span>Supports any software project or repository</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </div>
        </div>
      )}

      {/* 2. GitHub Repository */}
      {activeTab === 'github' && (
        <form onSubmit={handleGithubClone} className="bg-slate-50/70 border border-slate-200 rounded-2xl p-6 sm:p-8 space-y-4">
          <div>
            <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-2">
              GitHub Repository URL <span className="text-indigo-600">*</span>
            </label>
            <input
              type="url"
              placeholder="https://github.com/username/repository"
              value={githubUrl}
              onChange={(e) => setGithubUrl(e.target.value)}
              required
              disabled={isProcessing}
              className="w-full bg-white border border-slate-300 rounded-xl px-4 py-3 text-slate-900 placeholder-slate-400 focus:outline-none focus:border-indigo-600 focus:ring-1 focus:ring-indigo-600 text-sm font-mono"
            />
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-2">
                Branch (Optional)
              </label>
              <input
                type="text"
                placeholder="main or master (default)"
                value={githubBranch}
                onChange={(e) => setGithubBranch(e.target.value)}
                disabled={isProcessing}
                className="w-full bg-white border border-slate-300 rounded-xl px-4 py-2.5 text-slate-900 placeholder-slate-400 focus:outline-none focus:border-indigo-600 text-sm"
              />
            </div>
            <div>
              <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-2 flex items-center gap-1.5">
                <Lock className="w-3.5 h-3.5 text-slate-500" /> Private Token (Optional)
              </label>
              <input
                type="password"
                placeholder="ghp_... for private repos"
                value={githubToken}
                onChange={(e) => setGithubToken(e.target.value)}
                disabled={isProcessing}
                className="w-full bg-white border border-slate-300 rounded-xl px-4 py-2.5 text-slate-900 placeholder-slate-400 focus:outline-none focus:border-indigo-600 text-sm font-mono"
              />
            </div>
          </div>

          <div className="pt-2 flex justify-end">
            <button
              type="submit"
              disabled={isProcessing}
              className="flex items-center gap-2 bg-indigo-600 hover:bg-indigo-700 text-white font-semibold py-2.5 px-6 rounded-xl shadow-sm transition-all disabled:opacity-50 text-sm"
            >
              <GitBranch className="w-4 h-4" />
              <span>Clone & Analyze Project</span>
            </button>
          </div>
        </form>
      )}

      {/* 3. Folder Upload */}
      {activeTab === 'folder' && (
        <div
          onClick={() => folderInputRef.current?.click()}
          className="group relative border-2 border-dashed border-slate-300 hover:border-indigo-500 bg-slate-50/70 hover:bg-indigo-50/20 rounded-2xl p-10 text-center cursor-pointer transition-all duration-200"
        >
          <input
            ref={folderInputRef}
            type="file"
            // @ts-ignore
            webkitdirectory="true"
            directory="true"
            multiple
            onChange={handleFolderUpload}
            className="hidden"
            disabled={isProcessing}
          />
          <div className="w-14 h-14 mx-auto mb-4 bg-indigo-100 text-indigo-600 rounded-2xl flex items-center justify-center group-hover:scale-110 transition-transform">
            <FolderOpen className="w-7 h-7" />
          </div>
          <h3 className="text-base font-bold text-slate-900 mb-1">Select Project Folder</h3>
          <p className="text-slate-500 text-xs sm:text-sm max-w-md mx-auto">
            Upload your local project folder directly. Build caches and vendor folders are filtered automatically.
          </p>
        </div>
      )}

      {/* 4. Single File / Code Error Finder */}
      {activeTab === 'snippet' && (
        <form onSubmit={handleSnippetSubmit} className="bg-slate-50/70 border border-slate-200 rounded-2xl p-6 sm:p-8 space-y-4">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div className="flex items-center gap-2">
              <label className="text-xs font-bold text-slate-700 uppercase tracking-wider">Language:</label>
              <select
                value={selectedLanguage}
                onChange={(e) => setSelectedLanguage(e.target.value as any)}
                className="bg-white border border-slate-300 text-slate-800 text-xs font-semibold rounded-lg px-3 py-1.5 focus:outline-none focus:border-indigo-600"
              >
                <option value="python">Python (.py)</option>
                <option value="java">Java (.java)</option>
                <option value="javascript">JavaScript (.js)</option>
                <option value="html">HTML Markup</option>
              </select>
            </div>

            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={() => {
                  setSelectedLanguage('python');
                  setSnippetCode(`def calculate_grade(marks):
    # Bug: Missing validation for negative marks (<0) and values exceeding 100
    if marks >= 90:
        return "Grade A"
    elif marks >= 75:
        return "Grade B"
    elif marks >= 50:
        return "Grade C"
    elif marks >= 0:
        return "Fail"
    else:
        return "Fail"  # Negative marks return 'Fail' instead of input validation error

def main():
    print("Normal mark 85:", calculate_grade(85))
    print("Invalid negative mark -15:", calculate_grade(-15))
    print("Invalid overflow mark 150:", calculate_grade(150))

if __name__ == "__main__":
    main()`);
                }}
                className="text-xs text-indigo-600 hover:text-indigo-800 font-medium bg-indigo-50 px-2.5 py-1 rounded-md border border-indigo-200 transition-colors"
                title="Load Illustrative Hackathon Marks Calculator Example"
              >
                ⚡ Load Marks Calculator Demo
              </button>
              <button
                type="button"
                onClick={() => setSnippetCode('')}
                className="text-xs text-slate-500 hover:text-slate-800"
              >
                Clear Editor
              </button>
            </div>
          </div>

          <textarea
            rows={12}
            value={snippetCode}
            onChange={(e) => setSnippetCode(e.target.value)}
            placeholder={`// Paste your ${selectedLanguage.toUpperCase()} source code here to analyze defects, root causes, and patches...`}
            disabled={isProcessing}
            className="w-full bg-white border border-slate-300 rounded-xl p-4 text-slate-900 font-mono text-xs sm:text-sm placeholder-slate-400 focus:outline-none focus:border-indigo-600 focus:ring-1 focus:ring-indigo-600 transition-colors resize-y"
          />

          <div className="flex justify-end pt-2">
            <button
              type="submit"
              disabled={isProcessing}
              className="flex items-center gap-2 bg-indigo-600 hover:bg-indigo-700 text-white font-semibold py-2.5 px-6 rounded-xl shadow-sm transition-all text-sm disabled:opacity-50"
            >
              <Play className="w-4 h-4 fill-current" />
              <span>Analyze Code with LLM</span>
            </button>
          </div>
        </form>
      )}
    </div>
  );
};
