import React, { useState } from 'react';
import {
  Bug,
  Cpu,
  ShieldAlert,
  Bot,
  Send,
  Sparkles,
  FileText,
  User,
  ArrowRight,
  CheckCircle2,
  AlertCircle
} from 'lucide-react';
import { AgentInfo, AgentChatMessage, ProjectAnalysisSummary } from '../types';
import { apiFetch } from '../apiConfig';

interface AgentsPanelProps {
  summary: ProjectAnalysisSummary | null;
  showNotification: (msg: string, type: 'success' | 'info' | 'error') => void;
}

export const AgentsPanel: React.FC<AgentsPanelProps> = ({ summary, showNotification }) => {
  const [selectedAgentId, setSelectedAgentId] = useState<string>('orchestrator');
  const [chatInput, setChatInput] = useState<string>('');
  const [isSending, setIsSending] = useState<boolean>(false);
  const [messages, setMessages] = useState<AgentChatMessage[]>([
    {
      role: 'agent',
      content:
        'Welcome! We are your specialized AI engineering team. Select Dr. Patch for bug investigation, Nova for RAM & CPU profiling, or Aegis for security and architecture audits.',
      timestamp: 'Just now',
      agent_id: 'orchestrator'
    }
  ]);

  const agents: AgentInfo[] = [
    {
      id: 'agent_bugs',
      name: 'Dr. Patch',
      role: 'Software Debugging Specialist',
      avatar: 'Bug',
      specialization: 'Defects, Syntax/Logic Errors & Verified Code Patches',
      status: summary ? 'Ready' : 'Awaiting Project',
      key_findings_count: summary?.bugs.length || 0,
      summary: `${summary?.bugs.length || 0} defects analyzed with root causes.`
    },
    {
      id: 'agent_ram',
      name: 'Nova',
      role: 'RAM & Performance Engineer',
      avatar: 'Cpu',
      specialization: 'Memory Allocations, O(N²) Loops & Complexity Reduction',
      status: summary ? 'Ready' : 'Awaiting Project',
      key_findings_count: summary?.optimizations.length || 0,
      summary: `${summary?.optimizations.length || 0} RAM & CPU optimizations identified.`
    },
    {
      id: 'agent_arch',
      name: 'Aegis',
      role: 'Architecture & Security Auditor',
      avatar: 'ShieldAlert',
      specialization: 'OWASP Security Risks, Secret Exposure & Modularity',
      status: summary ? 'Ready' : 'Awaiting Project',
      key_findings_count: (summary?.security_findings.length || 0) + (summary?.architecture_findings.length || 0),
      summary: `${summary?.security_findings.length || 0} security & ${summary?.architecture_findings.length || 0} architectural notices.`
    },
    {
      id: 'orchestrator',
      name: 'Lead Orchestrator',
      role: 'Autonomous Engineering Lead',
      avatar: 'Bot',
      specialization: 'Multi-Agent Synthesis, Project Coordination & High-Level Strategy',
      status: 'Active',
      key_findings_count: (summary?.bugs.length || 0) + (summary?.optimizations.length || 0),
      summary: 'Coordinates Dr. Patch, Nova, and Aegis across the project.'
    }
  ];

  const handleSendMessage = async (customText?: string) => {
    const textToSend = customText || chatInput;
    if (!textToSend.trim() || isSending) return;

    const userMsg: AgentChatMessage = {
      role: 'user',
      content: textToSend.trim(),
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };

    setMessages((prev) => [...prev, userMsg]);
    if (!customText) setChatInput('');
    setIsSending(true);

    try {
      const res = await apiFetch('/api/agents/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          agent_id: selectedAgentId,
          message: textToSend.trim(),
          conversation_history: messages.slice(-6)
        })
      });

      if (!res.ok) throw new Error('Agent service unreachable');
      const data = await res.json();

      const agentMsg: AgentChatMessage = {
        role: 'agent',
        content: data.reply,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        agent_id: data.agent_id,
        references: data.referenced_files
      };

      setMessages((prev) => [...prev, agentMsg]);
    } catch (err: any) {
      showNotification('Agent communication error', 'error');
      setMessages((prev) => [
        ...prev,
        {
          role: 'agent',
          content: 'I encountered an error retrieving project context. Please try again or re-run the scan.',
          timestamp: 'Just now',
          agent_id: selectedAgentId
        }
      ]);
    } finally {
      setIsSending(false);
    }
  };

  const currentAgent = agents.find((a) => a.id === selectedAgentId) || agents[3];

  return (
    <div className="space-y-6">
      {/* 4 Agent Selector Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {agents.map((agent) => {
          const isSelected = selectedAgentId === agent.id;
          return (
            <div
              key={agent.id}
              onClick={() => setSelectedAgentId(agent.id)}
              className={`p-5 rounded-2xl border cursor-pointer transition-all duration-200 relative overflow-hidden bg-white ${
                isSelected
                  ? 'border-indigo-600 shadow-md ring-2 ring-indigo-500/10'
                  : 'border-slate-200 hover:border-slate-300 shadow-xs'
              }`}
            >
              <div className="flex items-center justify-between mb-3">
                <div
                  className={`w-10 h-10 rounded-xl flex items-center justify-center ${
                    agent.id === 'agent_bugs'
                      ? 'bg-rose-50 text-rose-600 border border-rose-100'
                      : agent.id === 'agent_ram'
                      ? 'bg-amber-50 text-amber-600 border border-amber-100'
                      : agent.id === 'agent_arch'
                      ? 'bg-purple-50 text-purple-600 border border-purple-100'
                      : 'bg-indigo-50 text-indigo-600 border border-indigo-100'
                  }`}
                >
                  {agent.id === 'agent_bugs' && <Bug className="w-5 h-5" />}
                  {agent.id === 'agent_ram' && <Cpu className="w-5 h-5" />}
                  {agent.id === 'agent_arch' && <ShieldAlert className="w-5 h-5" />}
                  {agent.id === 'orchestrator' && <Bot className="w-5 h-5" />}
                </div>

                <span
                  className={`text-[10px] font-bold px-2.5 py-0.5 rounded-full ${
                    isSelected ? 'bg-indigo-600 text-white' : 'bg-slate-100 text-slate-600'
                  }`}
                >
                  {agent.key_findings_count} Findings
                </span>
              </div>

              <h3 className="font-bold text-slate-900 text-sm sm:text-base">{agent.name}</h3>
              <p className="text-xs text-indigo-600 font-semibold mb-1.5">{agent.role}</p>
              <p className="text-xs text-slate-500 line-clamp-2">{agent.specialization}</p>

              {isSelected && (
                <div className="mt-3 pt-3 border-t border-slate-100 flex items-center gap-1.5 text-xs text-indigo-600 font-bold">
                  <Sparkles className="w-3.5 h-3.5" />
                  <span>Active Assistant</span>
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Main Interactive Chat Panel */}
      <div className="bg-white border border-slate-200 rounded-2xl flex flex-col h-[560px] shadow-xs overflow-hidden">
        {/* Chat Header */}
        <div className="p-4 px-6 bg-slate-50/70 border-b border-slate-200 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div
              className={`w-9 h-9 rounded-xl flex items-center justify-center font-bold text-sm ${
                currentAgent.id === 'agent_bugs'
                  ? 'bg-rose-50 text-rose-600 border border-rose-100'
                  : currentAgent.id === 'agent_ram'
                  ? 'bg-amber-50 text-amber-600 border border-amber-100'
                  : currentAgent.id === 'agent_arch'
                  ? 'bg-purple-50 text-purple-600 border border-purple-100'
                  : 'bg-indigo-50 text-indigo-600 border border-indigo-100'
              }`}
            >
              {currentAgent.name.charAt(0)}
            </div>
            <div>
              <div className="text-sm font-bold text-slate-900 flex items-center gap-2">
                <span>{currentAgent.name}</span>
                <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
              </div>
              <div className="text-xs text-slate-500">{currentAgent.role}</div>
            </div>
          </div>

          <div className="text-xs text-slate-400 font-mono hidden sm:block">
            Project: {summary?.project_name || 'No project loaded'}
          </div>
        </div>

        {/* Chat Message List */}
        <div className="flex-1 overflow-y-auto p-6 space-y-4 scrollbar-thin">
          {messages.map((msg, i) => {
            const isUser = msg.role === 'user';
            return (
              <div key={i} className={`flex gap-3 ${isUser ? 'justify-end' : 'justify-start'}`}>
                {!isUser && (
                  <div className="w-8 h-8 rounded-lg bg-indigo-50 border border-indigo-100 flex items-center justify-center text-indigo-700 shrink-0 text-xs font-bold">
                    AI
                  </div>
                )}
                <div
                  className={`max-w-[85%] rounded-2xl p-4 text-xs sm:text-sm whitespace-pre-wrap leading-relaxed ${
                    isUser
                      ? 'bg-indigo-600 text-white rounded-br-none shadow-xs'
                      : 'bg-slate-50 border border-slate-200 text-slate-800 rounded-bl-none shadow-xs'
                  }`}
                >
                  {msg.content}
                  {msg.references && msg.references.length > 0 && (
                    <div className="mt-2.5 pt-2 border-t border-slate-200/80 text-[11px] text-slate-500 flex flex-wrap gap-1.5 items-center">
                      <span className="font-semibold text-slate-600">Referenced:</span>
                      {msg.references.map((f) => (
                        <span key={f} className="px-2 py-0.5 bg-white border border-slate-200 rounded font-mono text-indigo-700">
                          {f}
                        </span>
                      ))}
                    </div>
                  )}
                  <div className={`text-[10px] mt-1 ${isUser ? 'text-indigo-200 text-right' : 'text-slate-400'}`}>
                    {msg.timestamp}
                  </div>
                </div>
                {isUser && (
                  <div className="w-8 h-8 rounded-lg bg-indigo-100 flex items-center justify-center text-indigo-700 shrink-0 text-xs">
                    <User className="w-4 h-4" />
                  </div>
                )}
              </div>
            );
          })}
          {isSending && (
            <div className="flex items-center gap-2 text-xs text-indigo-600 p-2 font-medium">
              <div className="w-3 h-3 rounded-full bg-indigo-600 animate-ping" />
              <span>{currentAgent.name} is reviewing project context...</span>
            </div>
          )}
        </div>

        {/* Quick Question Prompts */}
        <div className="p-2.5 px-6 bg-slate-50/80 border-t border-slate-200 flex items-center gap-2 overflow-x-auto scrollbar-none text-xs">
          <span className="text-slate-500 font-semibold shrink-0">Quick Queries:</span>
          {selectedAgentId === 'agent_bugs' && (
            <>
              <button
                onClick={() => handleSendMessage('Which bug should I fix first and why?')}
                className="px-2.5 py-1 bg-white hover:bg-slate-100 text-slate-700 rounded-md border border-slate-200 shrink-0 transition-colors shadow-2xs"
              >
                Which bug to fix first?
              </button>
              <button
                onClick={() => handleSendMessage('Explain the root cause of the primary defect.')}
                className="px-2.5 py-1 bg-white hover:bg-slate-100 text-slate-700 rounded-md border border-slate-200 shrink-0 transition-colors shadow-2xs"
              >
                Explain primary root cause
              </button>
            </>
          )}
          {selectedAgentId === 'agent_ram' && (
            <>
              <button
                onClick={() => handleSendMessage('How can I reduce unnecessary memory usage in this project?')}
                className="px-2.5 py-1 bg-white hover:bg-slate-100 text-slate-700 rounded-md border border-slate-200 shrink-0 transition-colors shadow-2xs"
              >
                How to reduce RAM footprint?
              </button>
              <button
                onClick={() => handleSendMessage('Are there any O(N²) or nested loops that can be optimized?')}
                className="px-2.5 py-1 bg-white hover:bg-slate-100 text-slate-700 rounded-md border border-slate-200 shrink-0 transition-colors shadow-2xs"
              >
                Identify slow loops
              </button>
            </>
          )}
          {selectedAgentId === 'agent_arch' && (
            <>
              <button
                onClick={() => handleSendMessage('Are there any security vulnerabilities or exposed credentials?')}
                className="px-2.5 py-1 bg-white hover:bg-slate-100 text-slate-700 rounded-md border border-slate-200 shrink-0 transition-colors shadow-2xs"
              >
                Security vulnerability audit
              </button>
              <button
                onClick={() => handleSendMessage('Is my project architecture modular and clean?')}
                className="px-2.5 py-1 bg-white hover:bg-slate-100 text-slate-700 rounded-md border border-slate-200 shrink-0 transition-colors shadow-2xs"
              >
                Modularity & coupling review
              </button>
            </>
          )}
          {selectedAgentId === 'orchestrator' && (
            <>
              <button
                onClick={() => handleSendMessage('Give me a full engineering health summary of this project.')}
                className="px-2.5 py-1 bg-white hover:bg-slate-100 text-slate-700 rounded-md border border-slate-200 shrink-0 transition-colors shadow-2xs"
              >
                Executive Health Summary
              </button>
            </>
          )}
        </div>

        {/* Chat Input Bar */}
        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleSendMessage();
          }}
          className="p-4 bg-white border-t border-slate-200 flex items-center gap-3"
        >
          <input
            type="text"
            placeholder={`Ask ${currentAgent.name} about your project...`}
            value={chatInput}
            onChange={(e) => setChatInput(e.target.value)}
            disabled={isSending}
            className="flex-1 bg-slate-50 border border-slate-200 rounded-xl px-4 py-2.5 text-slate-900 placeholder-slate-400 focus:outline-none focus:border-indigo-600 focus:bg-white text-xs sm:text-sm"
          />
          <button
            type="submit"
            disabled={isSending || !chatInput.trim()}
            className="bg-indigo-600 hover:bg-indigo-700 text-white p-2.5 rounded-xl disabled:opacity-40 transition-colors shrink-0 shadow-xs"
          >
            <Send className="w-4 h-4" />
          </button>
        </form>
      </div>
    </div>
  );
};
