import React, { useState, useEffect, useMemo, useCallback } from 'react';
import { getSessionUser, clearSession } from '../utils/auth';
import { executeQuery, fetchAuditTrail, generateDossier, parseDocument, confirmIngestion } from '../utils/api';
import type { QueryResponse, IngestDraft, ConfirmIngestPayload } from '../utils/api';
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
import { TimelinePlayer } from '../components/TimelinePlayer';
import { DocumentIngestionPanel } from '../components/DocumentIngestionPanel';
import { DossierModal } from '../components/DossierModal';
import { RoleWidget } from '../components/RoleWidget';
import { ToastNotificationContainer } from '../components/ToastNotificationContainer';
import type { ToastAlert } from '../components/ToastNotificationContainer';
import {
  ShieldAlert,
  LogOut,
  LayoutDashboard,
  Database,
  User as UserIcon,
  Download,
  Loader2,
  Clock,
  Upload,
  Brain
} from 'lucide-react';

type ViewMode = 'workspace' | 'audit' | 'ingest';

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

  // Timeline Playback State
  const [playbackDate, setPlaybackDate] = useState<string>('');
  const [isPlaying, setIsPlaying] = useState<boolean>(false);
  const [playbackSpeed, setPlaybackSpeed] = useState<number>(1000); // ms per step
  const [allDates, setAllDates] = useState<string[]>([]);

  // AI Dossier Modal State
  const [isDossierOpen, setIsDossierOpen] = useState(false);
  const [dossierContent, setDossierContent] = useState('');
  const [isLoadingDossier, setIsLoadingDossier] = useState(false);

  // Ingestion Panel State
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isParsingDoc, setIsParsingDoc] = useState(false);
  const [parsedDraft, setParsedDraft] = useState<IngestDraft | null>(null);
  const [ingestMetadata, setIngestMetadata] = useState<{ filename: string } | null>(null);
  const [isConfirmingIngest, setIsConfirmingIngest] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [ingestSuccessMessage, setIngestSuccessMessage] = useState('');

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

  // Real-time toast alerts state
  const [toastAlerts, setToastAlerts] = useState<ToastAlert[]>([]);

  useEffect(() => {
    if (activeView === 'audit' && user.role === 'Supervisor') {
      loadAuditLogs();
    }
  }, [activeView]);

  // Extract unique sorted dates from queryResult
  useEffect(() => {
    if (!queryResult) {
      setAllDates([]);
      setPlaybackDate('');
      setIsPlaying(false);
      return;
    }

    const datesSet = new Set<string>();
    
    if (queryResult.graph && queryResult.graph.nodes) {
      queryResult.graph.nodes.forEach((node) => {
        if (node.type === 'FIR' && node.date) {
          datesSet.add(node.date);
        }
      });
    }

    if (queryResult.heatmap && queryResult.heatmap.features) {
      queryResult.heatmap.features.forEach((feat) => {
        if (feat.properties && feat.properties.dates) {
          feat.properties.dates.forEach((d: string) => datesSet.add(d));
        }
      });
    }

    const sortedDates = Array.from(datesSet).sort();
    setAllDates(sortedDates);
    if (sortedDates.length > 0) {
      setPlaybackDate(sortedDates[sortedDates.length - 1]);
    } else {
      setPlaybackDate('');
    }
    setIsPlaying(false);
  }, [queryResult]);

  // Handle timeline playback updates
  useEffect(() => {
    if (!isPlaying || allDates.length === 0) return;

    const interval = setInterval(() => {
      setPlaybackDate((current) => {
        const currentIdx = allDates.indexOf(current);
        if (currentIdx === -1 || currentIdx === allDates.length - 1) {
          setIsPlaying(false);
          return current;
        }
        return allDates[currentIdx + 1];
      });
    }, playbackSpeed);

    return () => clearInterval(interval);
  }, [isPlaying, allDates, playbackSpeed]);

  // MEMOIZED calculations to prevent redundant re-renders
  const filteredGraph = useMemo(() => {
    if (!queryResult || !queryResult.graph) return null;
    if (allDates.length === 0 || !playbackDate) return queryResult.graph;

    const maxAllowedDate = playbackDate;
    const validFirIds = new Set<string>();
    
    const filteredNodes = queryResult.graph.nodes.filter((node) => {
      if (node.type === 'FIR') {
        if (node.date && node.date > maxAllowedDate) {
          return false;
        }
        validFirIds.add(node.id);
        return true;
      }
      return true;
    });

    const filteredLinks = queryResult.graph.links.filter((link) => {
      const sourceId = typeof link.source === 'object' ? (link.source as any).id : link.source;
      const targetId = typeof link.target === 'object' ? (link.target as any).id : link.target;
      
      const sourceIsFir = sourceId.startsWith('fir-');
      const targetIsFir = targetId.startsWith('fir-');
      
      if (sourceIsFir && !validFirIds.has(sourceId)) return false;
      if (targetIsFir && !validFirIds.has(targetIsFir)) return false;
      return true;
    });

    const activeNodeIds = new Set<string>();
    filteredLinks.forEach((l) => {
      const sourceId = typeof l.source === 'object' ? (l.source as any).id : l.source;
      const targetId = typeof l.target === 'object' ? (l.target as any).id : l.target;
      activeNodeIds.add(sourceId);
      activeNodeIds.add(targetId);
    });

    const prunedNodes = filteredNodes.filter((node) => {
      if (node.type === 'Location' || node.type === 'Victim') {
        return activeNodeIds.has(node.id);
      }
      return true;
    });

    return {
      ...queryResult.graph,
      nodes: prunedNodes,
      links: filteredLinks
    };
  }, [queryResult, allDates, playbackDate]);

  const filteredHeatmap = useMemo(() => {
    if (!queryResult || !queryResult.heatmap) return null;
    if (allDates.length === 0 || !playbackDate) return queryResult.heatmap;

    const maxAllowedDate = playbackDate;

    const filteredFeatures = queryResult.heatmap.features.map((feat) => {
      const originalDates = feat.properties.dates || [];
      const originalFirIds = feat.properties.fir_ids || [];
      
      const validIncidents = originalDates
        .map((d: string, idx: number) => ({ date: d, firId: originalFirIds[idx] }))
        .filter((inc: any) => inc.date <= maxAllowedDate);

      if (validIncidents.length === 0) return null;

      const newFirIds = validIncidents.map((inc: any) => inc.firId);
      const newCrimeCount = validIncidents.length;
      
      const ratio = newCrimeCount / originalDates.length;
      const newRiskScore = Math.round(feat.properties.risk_score * ratio * 100) / 100;

      return {
        ...feat,
        properties: {
          ...feat.properties,
          crime_count: newCrimeCount,
          risk_score: newRiskScore,
          fir_ids: newFirIds
        }
      };
    }).filter(Boolean) as any[];

    return {
      ...queryResult.heatmap,
      features: filteredFeatures
    };
  }, [queryResult, allDates, playbackDate]);

  const accumulatedCrimeCount = useMemo(() => {
    if (!queryResult) return 0;
    if (allDates.length === 0 || !playbackDate) return queryResult.rows_returned;
    
    let count = 0;
    if (queryResult.graph && queryResult.graph.nodes) {
      queryResult.graph.nodes.forEach((n) => {
        if (n.type === 'FIR' && n.date && n.date <= playbackDate) {
          count++;
        }
      });
    }
    return count;
  }, [queryResult, allDates, playbackDate]);

  const handleFIRClick = useCallback((firNumberOrId: string | number) => {
    let numericId: number | null = null;
    if (typeof firNumberOrId === 'string') {
      if (queryResult) {
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
      setIsAccusedDrawerOpen(false);
    }
  }, [queryResult]);

  const handleAccusedClick = useCallback((accusedId: number) => {
    setSelectedAccusedId(accusedId);
    setIsAccusedDrawerOpen(true);
    setIsFirDrawerOpen(false);
  }, []);

  const handleGenerateDossier = async () => {
    if (!queryResult || !activeQuery) return;
    setIsLoadingDossier(true);
    setIsDossierOpen(true);
    try {
      const result = await generateDossier(activeQuery, 'dashboard-session-' + user.username);
      if (result.success) {
        setDossierContent(result.dossier);
      } else {
        setDossierContent("Failed to generate dossier.");
      }
    } catch (e: any) {
      console.error(e);
      const errDetail = e.response?.data?.detail || e.message || 'Server error';
      setDossierContent(`⚠️ **Error generating dossier:** ${errDetail}`);
    } finally {
      setIsLoadingDossier(false);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      setSelectedFile(e.target.files[0]);
      setParsedDraft(null);
      setIngestSuccessMessage('');
    }
  };

  const handleUploadAndParse = async () => {
    if (!selectedFile) return;
    setIsParsingDoc(true);
    setUploadProgress(10);
    
    const interval = setInterval(() => {
      setUploadProgress((prev) => (prev < 90 ? prev + 15 : prev));
    }, 150);

    try {
      const result = await parseDocument(selectedFile);
      clearInterval(interval);
      setUploadProgress(100);
      
      if (result.success) {
        setParsedDraft(result.draft);
        setIngestMetadata(result.metadata);
      }
    } catch (err: any) {
      clearInterval(interval);
      alert(err.response?.data?.detail || 'Failed to parse document');
    } finally {
      setIsParsingDoc(false);
    }
  };

  const handleConfirmAndPersist = async () => {
    if (!parsedDraft) return;
    setIsConfirmingIngest(true);
    try {
      const payload: ConfirmIngestPayload = {
        fir: {
          fir_number: parsedDraft.fir.fir_number.value,
          date: parsedDraft.fir.date.value,
          crime_type: parsedDraft.fir.crime_type.value,
          description: parsedDraft.fir.description.value + " -- Verified & Human Confirmed.",
          status: parsedDraft.fir.status.value,
          location_name: parsedDraft.fir.location_name.value,
          station_area: parsedDraft.fir.station_area.value,
          district: parsedDraft.fir.district.value
        },
        accused: parsedDraft.accused.map(a => ({
          name: a.name.value,
          age: a.age.value,
          gender: a.gender.value,
          occupation: a.occupation.value,
          address: a.address.value,
          role: a.role.value
        })),
        victims: parsedDraft.victims.map(v => ({
          name: v.name.value,
          age: v.age.value,
          gender: v.gender.value
        })),
        document_reference: ingestMetadata?.filename || selectedFile?.name || 'document_upload.png'
      };

      const result = await confirmIngestion(payload);
      if (result.success) {
        setIngestSuccessMessage(`Successfully verified and persisted case file to database under new primary ID {result.fir_id}! (${result.fir_number})`);
        setParsedDraft(null);
        setSelectedFile(null);
      }
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Persistence failed');
    } finally {
      setIsConfirmingIngest(false);
    }
  };

  // dynamic environment-driven dynamic Websocket setup
  useEffect(() => {
    const wsScheme = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    // Use VITE_WS_URL env variable if configured, otherwise calculate dynamically
    const wsHost = import.meta.env.VITE_WS_URL || 'localhost:8000';
    const wsUrl = `${wsScheme}//${wsHost}/api/ws/alerts`;
    
    let ws: WebSocket;
    let pingInterval: number;
    let reconnectTimeout: number;
    let isUnmounted = false;

    const setupWs = () => {
      if (isUnmounted) return;
      ws = new WebSocket(wsUrl);

      ws.onopen = () => {
        console.log("WebSocket connected to alerts engine");
        // Heartbeat timer (30 seconds)
        pingInterval = window.setInterval(() => {
          if (ws.readyState === WebSocket.OPEN) {
            ws.send("ping");
          }
        }, 30000);
      };

      ws.onmessage = (event) => {
        if (event.data === "pong") return;
        try {
          const alert = JSON.parse(event.data);
          if (alert.type === "SPIKE_ALERT") {
            const newToast: ToastAlert = {
              id: Math.random().toString(36).substr(2, 9),
              message: alert.message,
              severity: alert.severity,
              timestamp: alert.timestamp
            };
            setToastAlerts((prev) => [newToast, ...prev]);
            
            setTimeout(() => {
              setToastAlerts((prev) => prev.filter(t => t.id !== newToast.id));
            }, 6000);
          }
        } catch (err) {
          console.error("Error parsing WebSocket alert message", err);
        }
      };

      ws.onclose = () => {
        clearInterval(pingInterval);
        if (!isUnmounted) {
          console.log("WebSocket closed. Reconnecting in 5 seconds...");
          reconnectTimeout = window.setTimeout(setupWs, 5000);
        }
      };
    };

    setupWs();

    return () => {
      isUnmounted = true;
      clearInterval(pingInterval);
      clearTimeout(reconnectTimeout);
      if (ws) {
        ws.close();
      }
    };
  }, []);

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
    setChatMessages((prev) => [...prev, { sender: 'user', text: queryText }]);

    try {
      const result = await executeQuery({
        query: queryText,
        role: user.role,
        session_id: 'dashboard-session-' + user.username,
      });

      setQueryResult(result);
      
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

        {(user.role === 'Investigator' || user.role === 'Analyst' || user.role === 'Supervisor') && (
          <button
            onClick={() => setActiveView('ingest')}
            className={`p-2.5 rounded-lg transition-colors cursor-pointer ${
              activeView === 'ingest' ? 'bg-cyan-500/10 text-cyan-400' : 'text-slate-500 hover:text-slate-300'
            }`}
            title="Document Ingestion"
          >
            <Upload className="w-5 h-5" />
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
              <span className="text-slate-300 font-medium">{user.name}</span>
              <span className="text-slate-600">|</span>
              <span className="text-cyan-400 font-bold uppercase tracking-wider text-[10px]">
                {user.role}
              </span>
            </div>

            {/* Case Dossier */}
            {queryResult && activeView === 'workspace' && (
              <button
                onClick={handleGenerateDossier}
                className="flex items-center gap-2 bg-purple-600 hover:bg-purple-500 text-slate-100 px-3 py-1.5 rounded-lg shadow-md cursor-pointer font-bold transition-all mr-2"
              >
                <Brain className="w-3.5 h-3.5" />
                <span>AI Case Dossier</span>
              </button>
            )}

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
            <div className="flex flex-col h-full min-w-0 font-sans">
              {/* Row 1: Alert Panel */}
              <AlertPanel alerts={queryResult ? queryResult.alerts : []} />

              {/* Row 2: Query Entry Bar */}
              <QueryBar onAsk={handleAsk} isLoading={isLoading} />

              {/* Role-specific widget */}
              <RoleWidget role={user.role} onFIRClick={handleFIRClick} onAsk={handleAsk} />

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
              <div className="hidden lg:grid grid-cols-3 gap-4 flex-1 min-w-0">
                {/* Column 1: Chat Panel */}
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
                    graphData={filteredGraph}
                    onAccusedClick={handleAccusedClick}
                    onFIRClick={handleFIRClick}
                  />
                </div>

                {/* Column 3: Map Panel */}
                <div className="min-w-0">
                  <MapPanel
                    heatmapData={filteredHeatmap}
                    onHotspotClick={handleAsk}
                  />
                </div>
              </div>

              {/* Mobile Adaptive views */}
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
                    graphData={filteredGraph}
                    onAccusedClick={handleAccusedClick}
                    onFIRClick={handleFIRClick}
                  />
                )}
                {activeLensTab === 'map' && (
                  <MapPanel
                    heatmapData={filteredHeatmap}
                    onHotspotClick={handleAsk}
                  />
                )}
              </div>

              {/* Timeline Playback Slider Row */}
              <TimelinePlayer
                isPlaying={isPlaying}
                setIsPlaying={setIsPlaying}
                playbackDate={playbackDate}
                setPlaybackDate={setPlaybackDate}
                playbackSpeed={playbackSpeed}
                setPlaybackSpeed={setPlaybackSpeed}
                allDates={allDates}
                accumulatedCount={accumulatedCrimeCount}
              />
            </div>
          ) : activeView === 'ingest' ? (
            /* --- INGESTION MODE --- */
            <DocumentIngestionPanel
              selectedFile={selectedFile}
              setSelectedFile={setSelectedFile}
              isParsingDoc={isParsingDoc}
              parsedDraft={parsedDraft}
              setParsedDraft={setParsedDraft}
              ingestMetadata={ingestMetadata}
              isConfirmingIngest={isConfirmingIngest}
              uploadProgress={uploadProgress}
              ingestSuccessMessage={ingestSuccessMessage}
              onFileChange={handleFileChange}
              onUploadAndParse={handleUploadAndParse}
              onConfirmAndPersist={handleConfirmAndPersist}
            />
          ) : (
            /* --- SUPERVISOR AUDIT MODE --- */
            <div className="flex flex-col gap-5 h-full">
              <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                <div className="text-left">
                  <h2 className="text-lg font-bold text-slate-200">Security Audit Logs & Operations History</h2>
                  <p className="text-xs text-slate-500">Supervisor Command only. Logs SQL executions, intent classifications, and processing latency.</p>
                </div>
              </div>

              {isLoadingAudit ? (
                <div className="h-64 flex flex-col items-center justify-center text-slate-500 gap-2">
                  <Loader2 className="w-8 h-8 animate-spin text-cyan-500 mb-2" />
                  <span className="text-xs uppercase tracking-widest font-semibold">Decrypting secure audit logs...</span>
                </div>
              ) : (
                <div className="flex-grow overflow-x-auto border border-slate-900 rounded-xl bg-slate-950/40">
                  <table className="w-full border-collapse text-xs text-left min-w-[900px]">
                    <thead>
                      <tr className="border-b border-slate-900 bg-slate-950 text-slate-400 font-bold uppercase tracking-wider text-[10px]">
                        <th className="p-3 w-16 text-center"><Clock className="w-4 h-4 mx-auto" /></th>
                        <th className="p-3 w-32">User</th>
                        <th className="p-3 w-36">Query Intent</th>
                        <th className="p-3">Audit Details</th>
                        <th className="p-3 w-28">Latency</th>
                        <th className="p-3 w-28 text-center">Results</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-900">
                      {auditLogs.map((log) => (
                        <tr key={log.log_id} className="hover:bg-slate-900/20 transition-colors">
                          <td className="p-3 text-slate-500 font-mono text-center truncate max-w-[80px]">
                            {log.timestamp.split(' ')[1] || log.timestamp}
                          </td>
                          <td className="p-3">
                            <div className="font-semibold text-slate-300">{log.username}</div>
                            <div className="text-[9px] text-cyan-400 uppercase tracking-widest font-bold mt-0.5">{log.role}</div>
                          </td>
                          <td className="p-3 font-semibold font-mono text-[10px]">
                            <span className={`px-2 py-0.5 rounded ${
                              log.intent === 'PATTERN_ANALYSIS' ? 'bg-rose-500/10 text-rose-400 border border-rose-900/20' :
                              log.intent === 'NETWORK_ANALYSIS' ? 'bg-cyan-500/10 text-cyan-400 border border-cyan-900/20' :
                              'bg-slate-900 text-slate-400'
                            }`}>
                              {log.intent}
                            </span>
                          </td>
                          <td className="p-3 max-w-md">
                            <div className="font-medium text-slate-200 line-clamp-1">Query: "{log.query}"</div>
                            <div className="text-[10px] text-slate-500 font-mono font-bold mt-1 max-w-[400px] truncate">
                              SQL: {log.generated_sql}
                            </div>
                          </td>
                          <td className="p-3 font-mono text-slate-300 font-semibold">
                            {log.execution_time.toFixed(3)}s
                          </td>
                          <td className="p-3 text-center font-bold text-slate-400">
                            {log.rows_returned}
                          </td>
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

      {/* DRAWERS Cabinet */}
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

      {/* AI Prosecutorial Dossier Narrative Modal */}
      <DossierModal
        isOpen={isDossierOpen}
        onClose={() => setIsDossierOpen(false)}
        isLoading={isLoadingDossier}
        content={dossierContent}
        onFirClick={handleFIRClick}
      />

      {/* Real-time Toast Notifications */}
      <ToastNotificationContainer toastAlerts={toastAlerts} />
    </div>
  );
};
