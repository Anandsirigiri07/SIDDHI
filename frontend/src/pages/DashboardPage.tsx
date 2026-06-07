import React, { useState, useEffect } from 'react';
import { getSessionUser, clearSession } from '../utils/auth';
import { executeQuery, fetchAuditTrail } from '../utils/api';
import type { QueryResponse } from '../utils/api';
import { exportIntelligenceReport } from '../utils/pdfExport';
import { AlertPanel } from '../components/AlertPanel';
import { QueryBar } from '../components/QueryBar';
import { PipelineStatus } from '../components/PipelineStatus';
import { ChatPanel } from '../components/ChatPanel';
import type { ChatMessage } from '../components/ChatPanel';
import { GraphPanel } from '../components/GraphPanel';
import { MapPanel } from '../components/MapPanel';
import { ProfileDrawer } from '../components/ProfileDrawer';
import { FIRDrawer } from '../components/FIRDrawer';
import {
  ShieldAlert,
  LogOut,
  LayoutDashboard,
  Database,
  User as UserIcon,
  Download,
  Loader2,
  Clock,
  Code
} from 'lucide-react';

type ViewMode = 'workspace' | 'audit';

export const DashboardPage: React.FC = () => {
  const user = getSessionUser();
  
  if (!user) {
    window.location.href = '/login';
    return null;
  }

  // Views state
  const [activeView, setActiveView] = useState<ViewMode>('workspace');
  
  // Pipeline/Query state
  const [isLoading, setIsLoading] = useState(false);
  const [queryResult, setQueryResult] = useState<QueryResponse | null>(null);
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([]);
  const [activeQuery, setActiveQuery] = useState('');

  // Active drawers state
  const [selectedAccusedId, setSelectedAccusedId] = useState<number | null>(null);
  const [selectedFirId, setSelectedFirId] = useState<number | null>(null);
  const [isAccusedDrawerOpen, setIsAccusedDrawerOpen] = useState(false);
  const [isFirDrawerOpen, setIsFirDrawerOpen] = useState(false);

  // Supervisor Audit state
  const [auditLogs, setAuditLogs] = useState<any[]>([]);
  const [isLoadingAudit, setIsLoadingAudit] = useState(false);

  // Responsive Mobile/Tablet Tabs
  const [activeLensTab, setActiveLensTab] = useState<'chat' | 'graph' | 'map'>('chat');

  useEffect(() => {
    if (activeView === 'audit' && user.role === 'Supervisor') {
      loadAuditLogs();
    }
  }, [activeView]);

  const loadAuditLogs = async () => {
    setIsLoadingAudit(true);
    try {
      const logs = await fetchAuditTrail();
      setAuditLogs(logs);
    } catch (err) {
      console.error('Failed to load audit logs', err);
    } finally {
      setIsLoadingAudit(false);
    }
  };

  const handleAsk = async (queryText: string) => {
    setIsLoading(true);
    setActiveQuery(queryText);
    
    // Add user message to Chat
    setChatMessages((prev) => [...prev, { sender: 'user', text: queryText }]);

    try {
      const result = await executeQuery({
        query: queryText,
        role: user.role,
        session_id: 'dashboard-session-' + user.username,
      });

      setQueryResult(result);
      
      // Add AI response to Chat
      setChatMessages((prev) => [
        ...prev,
        {
          sender: 'ai',
          text: result.answer,
          intent: result.intent || 'RECORD_LOOKUP',
          confidence: result.confidence !== undefined ? result.confidence : 0.9,
          citations: result.citations,
          executionMode: result.execution_mode,
        },
      ]);
    } catch (err: any) {
      console.error(err);
      const errMsg = err.response?.data?.detail || 'System execution error. The query could not be completed.';
      setChatMessages((prev) => [
        ...prev,
        { sender: 'ai', text: `⚠️ **Error: ** ${errMsg}` },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleFIRClick = (firNumberOrId: string | number) => {
    // If it's a string like 'FIR-YYYY-XXXXX', we look up the numeric ID in queryResult
    let numericId: number | null = null;
    if (typeof firNumberOrId === 'string') {
      if (queryResult) {
        // Find in nodes
        const node = queryResult.graph.nodes.find((n) => n.label === firNumberOrId);
        if (node) {
          numericId = parseInt(node.id.split('-')[1], 10);
        }
      }
    } else {
      numericId = firNumberOrId;
    }

    if (numericId) {
      setSelectedFirId(numericId);
      setIsFirDrawerOpen(true);
      // Close other drawers
      setIsAccusedDrawerOpen(false);
    }
  };

  const handleAccusedClick = (accusedId: number) => {
    setSelectedAccusedId(accusedId);
    setIsAccusedDrawerOpen(true);
    // Close other drawers
    setIsFirDrawerOpen(false);
  };

  const handleLogout = () => {
    clearSession();
    window.location.href = '/login';
  };

  const handleExportPDF = async () => {
    if (!queryResult) return;
    
    setIsLoading(true);
    try {
      await exportIntelligenceReport({
        query: activeQuery,
        answer: queryResult.answer,
        citations: queryResult.citations,
        executionMode: queryResult.execution_mode,
        totalRows: queryResult.total_rows_found,
        sqlExecuted: queryResult.evidence.sql_executed,
        explanation: queryResult.evidence.explanation,
        alerts: queryResult.alerts,
        graphElementId: 'siddhi-d3-graph',
        mapElementId: 'siddhi-leaflet-map',
        userRole: user.role,
        userName: user.name,
      });
    } catch (e) {
      console.error(e);
      alert('Failed to generate report PDF');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#03060f] flex text-slate-100 font-sans">
      {/* LEFT SIDEBAR */}
      <div className="w-16 border-r border-slate-900 bg-slate-950 flex flex-col items-center py-6 gap-6 flex-shrink-0 z-50">
        <div className="w-9 h-9 rounded-lg bg-cyan-500/10 border border-cyan-500/40 flex items-center justify-center filter drop-shadow-[0_0_6px_rgba(6,182,212,0.15)] mb-4">
          <ShieldAlert className="w-5 h-5 text-cyan-400" />
        </div>

        <button
          onClick={() => setActiveView('workspace')}
          className={`p-2.5 rounded-lg transition-colors cursor-pointer ${
            activeView === 'workspace' ? 'bg-cyan-500/10 text-cyan-400' : 'text-slate-500 hover:text-slate-300'
          }`}
          title="Analysis Workspace"
        >
          <LayoutDashboard className="w-5 h-5" />
        </button>

        {user.role === 'Supervisor' && (
          <button
            onClick={() => setActiveView('audit')}
            className={`p-2.5 rounded-lg transition-colors cursor-pointer ${
              activeView === 'audit' ? 'bg-cyan-500/10 text-cyan-400' : 'text-slate-500 hover:text-slate-300'
            }`}
            title="Supervisor Audit Log"
          >
            <Database className="w-5 h-5" />
          </button>
        )}
      </div>

      {/* RIGHT WORKSPACE BLOCK */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* TOP BAR */}
        <header className="h-14 border-b border-slate-900 bg-slate-950/80 backdrop-blur flex items-center justify-between px-6 z-40">
          <div className="flex items-center gap-3">
            <span className="font-mono font-bold tracking-widest text-slate-100 text-sm">
              SIDDHI // COMMAND PORTAL
            </span>
          </div>

          <div className="flex items-center gap-4 text-xs font-semibold">
            {/* User Metadata */}
            <div className="flex items-center gap-2 bg-slate-900/60 border border-slate-800 p-1.5 px-3 rounded-lg">
              <UserIcon className="w-3.5 h-3.5 text-cyan-500" />
              <span className="text-slate-300 font-medium">
                {user.name}
              </span>
              <span className="text-slate-600">|</span>
              <span className="text-cyan-400 font-bold uppercase tracking-wider text-[10px]">
                {user.role}
              </span>
            </div>

            {/* Export PDF */}
            {queryResult && activeView === 'workspace' && (
              <button
                onClick={handleExportPDF}
                disabled={isLoading}
                className="flex items-center gap-2 bg-cyan-600 hover:bg-cyan-500 text-slate-950 px-3 py-1.5 rounded-lg shadow-md cursor-pointer font-bold transition-all"
              >
                {isLoading ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Download className="w-3.5 h-3.5" />}
                <span>Export Report</span>
              </button>
            )}

            {/* Logout */}
            <button
              onClick={handleLogout}
              className="p-1.5 bg-slate-900 border border-slate-800 text-slate-400 hover:text-rose-400 hover:bg-slate-800 rounded-lg transition-colors cursor-pointer"
              title="Logout session"
            >
              <LogOut className="w-4 h-4" />
            </button>
          </div>
        </header>

        {/* MAIN CONTAINER */}
        <main className="flex-1 p-5 overflow-y-auto min-w-0">
          {activeView === 'workspace' ? (
            /* --- WORKSPACE MODE --- */
            <div className="flex flex-col h-full min-w-0">
              {/* Row 1: Alert Panel */}
              <AlertPanel alerts={queryResult ? queryResult.alerts : []} />

              {/* Row 2: Query Entry Bar */}
              <QueryBar onAsk={handleAsk} isLoading={isLoading} />

              {/* Responsive Tabs (Hidden on Large screens) */}
              <div className="lg:hidden flex items-center justify-between border-b border-slate-900 bg-slate-950/40 p-1 mb-4 rounded-lg">
                <button
                  onClick={() => setActiveLensTab('chat')}
                  className={`flex-1 py-2 text-xs font-bold uppercase tracking-wider text-center rounded transition-all cursor-pointer ${
                    activeLensTab === 'chat' ? 'bg-cyan-500/10 text-cyan-400' : 'text-slate-500'
                  }`}
                >
                  Summary
                </button>
                <button
                  onClick={() => setActiveLensTab('graph')}
                  className={`flex-1 py-2 text-xs font-bold uppercase tracking-wider text-center rounded transition-all cursor-pointer ${
                    activeLensTab === 'graph' ? 'bg-cyan-500/10 text-cyan-400' : 'text-slate-500'
                  }`}
                >
                  Network Graph
                </button>
                <button
                  onClick={() => setActiveLensTab('map')}
                  className={`flex-1 py-2 text-xs font-bold uppercase tracking-wider text-center rounded transition-all cursor-pointer ${
                    activeLensTab === 'map' ? 'bg-cyan-500/10 text-cyan-400' : 'text-slate-500'
                  }`}
                >
                  Hotspot Map
                </button>
              </div>

              {/* Row 3: Triple Lens Grid */}
              {/* Desktop view: 3 columns */}
              <div className="hidden lg:grid grid-cols-3 gap-4 flex-1 min-w-0">
                {/* Column 1: Chat Panel & Pipeline Checklist */}
                <div className="flex flex-col gap-4 min-w-0">
                  <ChatPanel
                    messages={chatMessages}
                    isLoading={isLoading}
                    onFIRClick={handleFIRClick}
                  />
                  <PipelineStatus isLoading={isLoading} hasResult={!!queryResult} />
                </div>

                {/* Column 2: Graph Panel */}
                <div className="min-w-0">
                  <GraphPanel
                    graphData={queryResult ? queryResult.graph : null}
                    onAccusedClick={handleAccusedClick}
                    onFIRClick={handleFIRClick}
                  />
                </div>

                {/* Column 3: Map Panel */}
                <div className="min-w-0">
                  <MapPanel
                    heatmapData={queryResult ? queryResult.heatmap : null}
                    onHotspotClick={handleAsk}
                  />
                </div>
              </div>

              {/* Mobile/Tablet Adaptive view: 1 Column based on active tab */}
              <div className="lg:hidden flex flex-col gap-4 flex-1">
                {activeLensTab === 'chat' && (
                  <div className="flex flex-col gap-4">
                    <ChatPanel
                      messages={chatMessages}
                      isLoading={isLoading}
                      onFIRClick={handleFIRClick}
                    />
                    <PipelineStatus isLoading={isLoading} hasResult={!!queryResult} />
                  </div>
                )}
                {activeLensTab === 'graph' && (
                  <GraphPanel
                    graphData={queryResult ? queryResult.graph : null}
                    onAccusedClick={handleAccusedClick}
                    onFIRClick={handleFIRClick}
                  />
                )}
                {activeLensTab === 'map' && (
                  <MapPanel
                    heatmapData={queryResult ? queryResult.heatmap : null}
                    onHotspotClick={handleAsk}
                  />
                )}
              </div>
            </div>
          ) : (
            /* --- SUPERVISOR AUDIT MODE --- */
            <div className="flex flex-col gap-5 h-full">
              <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                <div>
                  <h2 className="text-lg font-bold text-slate-200">Supervisor Audit Trail Dashboard</h2>
                  <p className="text-xs text-slate-500">Security operation log records for all analyst queries.</p>
                </div>
                <button
                  onClick={loadAuditLogs}
                  disabled={isLoadingAudit}
                  className="flex items-center gap-2 bg-slate-900 border border-slate-800 hover:bg-slate-800 px-3 py-1.5 rounded-lg text-xs font-bold cursor-pointer"
                >
                  {isLoadingAudit ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Clock className="w-3.5 h-3.5" />}
                  Refresh Logs
                </button>
              </div>

              {isLoadingAudit ? (
                <div className="flex-1 flex flex-col items-center justify-center text-slate-500 py-20">
                  <Loader2 className="w-8 h-8 animate-spin text-cyan-500 mb-2" />
                  <span className="text-xs uppercase tracking-widest">Querying Audit Records...</span>
                </div>
              ) : auditLogs.length === 0 ? (
                <div className="text-center p-12 bg-slate-900/10 border border-slate-900 rounded-lg text-slate-500 text-xs uppercase tracking-widest">
                  No audit trail records found in database.
                </div>
              ) : (
                <div className="flex-1 overflow-x-auto rounded-lg border border-slate-900">
                  <table className="w-full text-left border-collapse text-xs">
                    <thead>
                      <tr className="bg-slate-900/80 text-cyan-400 uppercase tracking-widest text-[10px] font-bold border-b border-slate-800">
                        <th className="p-3.5">ID</th>
                        <th className="p-3.5">Timestamp</th>
                        <th className="p-3.5">Operator</th>
                        <th className="p-3.5">Role</th>
                        <th className="p-3.5">Inquiry Query</th>
                        <th className="p-3.5">Intent</th>
                        <th className="p-3.5">SQL Executed</th>
                        <th className="p-3.5">Rows</th>
                        <th className="p-3.5">Time</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-900/60 bg-slate-950/20">
                      {auditLogs.map((log) => (
                        <tr key={log.log_id} className="hover:bg-slate-900/20 text-slate-300">
                          <td className="p-3.5 font-mono text-[10px] text-slate-500 font-semibold">{log.log_id}</td>
                          <td className="p-3.5 font-mono text-[10px] text-slate-400 whitespace-nowrap">{log.timestamp}</td>
                          <td className="p-3.5 font-bold text-slate-200">{log.username}</td>
                          <td className="p-3.5"><span className="text-[10px] bg-slate-900 px-1.5 py-0.5 rounded border border-slate-800 uppercase tracking-wider text-slate-400 font-semibold">{log.role}</span></td>
                          <td className="p-3.5 max-w-xs truncate" title={log.query}>{log.query}</td>
                          <td className="p-3.5"><span className="text-[10px] bg-cyan-950/40 border border-cyan-900/30 px-1.5 py-0.5 rounded text-cyan-400 font-bold tracking-wider">{log.intent}</span></td>
                          <td className="p-3.5 max-w-sm font-mono text-[10px] text-cyan-500/90 truncate flex items-center gap-1.5" title={log.generated_sql}>
                            <Code className="w-3.5 h-3.5 text-cyan-500/50 flex-shrink-0" />
                            {log.generated_sql}
                          </td>
                          <td className="p-3.5 font-mono font-bold text-slate-200">{log.rows_returned}</td>
                          <td className="p-3.5 font-mono text-[10px] text-slate-400">{log.execution_time ? `${log.execution_time.toFixed(3)}s` : '0s'}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          )}
        </main>
      </div>

      {/* DRAWERS PANEL OVERLAYS */}
      <ProfileDrawer
        isOpen={isAccusedDrawerOpen}
        onClose={() => setIsAccusedDrawerOpen(false)}
        accusedId={selectedAccusedId}
        graphData={queryResult ? queryResult.graph : null}
        onFIRClick={handleFIRClick}
      />

      <FIRDrawer
        isOpen={isFirDrawerOpen}
        onClose={() => setIsFirDrawerOpen(false)}
        firId={selectedFirId}
        onAccusedClick={handleAccusedClick}
      />
    </div>
  );
};
export default DashboardPage;
