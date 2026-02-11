import React, { useState, useEffect, useCallback } from 'react';
import { useAdminAuth } from '../context/AdminAuthContext';
import {
  getAnalyticsOverview, getAnalyticsEvents,
  getUsers, deleteUser,
  getAdminConversations, deleteAdminConversation,
  getPrompts, updatePrompts,
  getRagData, uploadRagData, deleteRagData,
  getIPSummary, getIPMessages, getIPBlacklist, blacklistIP, unblacklistIP,
  IPSummaryResponse, IPMessagesResponse,
  getDLQTasks, getDLQSummary, getDLQTaskDetail, retryDLQTasks, deleteDLQTasks, clearDLQ, exportDLQTasks,
  DLQTask, DLQTaskDetail, DLQSummaryResponse,
} from '../api/admin';
import {
  HiArrowRightOnRectangle, HiChartBar, HiUsers, HiChatBubbleLeftRight,
  HiCog6Tooth, HiDocumentText, HiArrowPath, HiTrash, HiArrowUpTray,
  HiClipboardDocument, HiSparkles, HiBars3, HiXMark, HiShieldCheck,
  HiNoSymbol, HiMagnifyingGlass, HiPlus, HiGlobeAlt, HiExclamationTriangle,
  HiArrowDownTray, HiEye, HiCheck, HiXCircle,
} from 'react-icons/hi2';

type Tab = 'analytics' | 'users' | 'conversations' | 'prompts' | 'ragdata' | 'ipmanagement' | 'dlq';

const AdminDashboard: React.FC = () => {
  const { logout } = useAdminAuth();
  const [activeTab, setActiveTab] = useState<Tab>('analytics');
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [isMobile, setIsMobile] = useState(false);

  // Detect screen size
  useEffect(() => {
    const checkMobile = () => {
      const mobile = window.innerWidth < 1024;
      setIsMobile(mobile);
      if (!mobile) setSidebarOpen(true);
    };
    
    checkMobile();
    window.addEventListener('resize', checkMobile);
    return () => window.removeEventListener('resize', checkMobile);
  }, []);

  const handleTabChange = (tab: Tab) => {
    setActiveTab(tab);
    if (isMobile) setSidebarOpen(false);
  };

  const tabs: { id: Tab; label: string; icon: React.ElementType }[] = [
    { id: 'analytics', label: 'Analytics', icon: HiChartBar },
    { id: 'users', label: 'Users', icon: HiUsers },
    { id: 'conversations', label: 'Conversations', icon: HiChatBubbleLeftRight },
    { id: 'prompts', label: 'Prompts', icon: HiCog6Tooth },
    { id: 'ragdata', label: 'RAG Data', icon: HiDocumentText },
    { id: 'ipmanagement', label: 'IP Management', icon: HiShieldCheck },
    { id: 'dlq', label: 'Dead Letter Queue', icon: HiExclamationTriangle },
  ];

  return (
    <div className="h-screen h-[100dvh] flex bg-black text-white overflow-hidden">
      {/* Mobile header */}
      <div className="lg:hidden fixed top-0 left-0 right-0 z-40 h-14 bg-apple-surface/95 backdrop-blur-lg border-b border-apple-border flex items-center justify-between px-4 safe-area-top">
        <button
          onClick={() => setSidebarOpen(!sidebarOpen)}
          className="w-10 h-10 flex items-center justify-center rounded-xl text-white hover:bg-apple-elevated transition-colors"
        >
          {sidebarOpen ? <HiXMark className="w-5 h-5" /> : <HiBars3 className="w-5 h-5" />}
        </button>
        <div className="flex items-center gap-2">
          <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-[#0A84FF] to-[#5E5CE6] flex items-center justify-center">
            <HiSparkles className="w-3.5 h-3.5 text-white" />
          </div>
          <span className="font-semibold text-sm">Admin</span>
        </div>
        <div className="w-10" /> {/* Spacer for centering */}
      </div>

      {/* Overlay for mobile */}
      {sidebarOpen && isMobile && (
        <div
          className="lg:hidden fixed inset-0 bg-black/60 z-30 backdrop-blur-sm"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Sidebar */}
      <div className={`
        fixed lg:relative z-40 h-full
        w-64 lg:w-56 bg-apple-surface/95 lg:bg-apple-surface/50 backdrop-blur-xl lg:backdrop-blur-none
        border-r border-apple-border flex flex-col
        transition-transform duration-300 ease-out
        ${sidebarOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}
        pt-14 lg:pt-0
      `}>
        {/* Desktop header */}
        <div className="hidden lg:flex p-4 border-b border-apple-border items-center gap-2">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-[#0A84FF] to-[#5E5CE6] flex items-center justify-center">
            <HiSparkles className="w-4 h-4 text-white" />
          </div>
          <h1 className="text-lg font-bold text-white">
            Alice Admin
          </h1>
        </div>
        <nav className="flex-1 py-2 overflow-y-auto">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => handleTabChange(tab.id)}
              className={`w-full flex items-center gap-3 px-4 py-3 lg:py-2.5 text-sm transition-colors touch-target ${
                activeTab === tab.id
                  ? 'bg-apple-accent/10 text-apple-accent border-r-2 border-apple-accent'
                  : 'text-apple-secondary hover:text-white hover:bg-apple-surface'
              }`}
            >
              <tab.icon className="w-5 h-5 lg:w-4 lg:h-4" />
              {tab.label}
            </button>
          ))}
        </nav>
        <div className="p-3 border-t border-apple-border safe-area-bottom">
          <button
            onClick={logout}
            className="w-full flex items-center gap-2 px-3 py-2.5 lg:py-2 rounded-lg text-sm text-apple-secondary hover:text-apple-red hover:bg-apple-red/10 transition-colors"
          >
            <HiArrowRightOnRectangle className="w-5 h-5 lg:w-4 lg:h-4" />
            Sign Out
          </button>
          <a href="/" className="block mt-1 px-3 py-2 rounded-lg text-xs text-apple-tertiary hover:text-apple-secondary transition-colors">
            Back to Chat
          </a>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto pt-14 lg:pt-0">
        <div className="p-4 lg:p-6">
          {activeTab === 'analytics' && <AnalyticsTab />}
          {activeTab === 'users' && <UsersTab />}
          {activeTab === 'conversations' && <ConversationsTab />}
          {activeTab === 'prompts' && <PromptsTab />}
          {activeTab === 'ragdata' && <RagDataTab />}
          {activeTab === 'ipmanagement' && <IPManagementTab />}
          {activeTab === 'dlq' && <DLQTab />}
        </div>
      </div>
    </div>
  );
};

// ===== Analytics Tab =====
const AnalyticsTab: React.FC = () => {
  const [overview, setOverview] = useState<any>(null);
  const [events, setEvents] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeView, setActiveView] = useState<'overview' | 'events' | 'metrics'>('overview');

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const [ov, ev] = await Promise.all([
        getAnalyticsOverview(),
        getAnalyticsEvents(undefined, 0, 100),
      ]);
      setOverview(ov);
      setEvents(ev.events || []);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { fetchData(); }, [fetchData]);

  if (loading) return <LoadingState />;

  // Calculate metrics summary from analytics_events (not metrics)
  // Events use event_type: "LLM_RESPONSE" and token_total field
  const llmEvents = events.filter(e => e.event_type === 'LLM_RESPONSE');
  // Avg latency based on last 5 responses
  const last5Events = llmEvents.slice(0, 5);
  const avgLatency = last5Events.length > 0 
    ? Math.round(last5Events.reduce((sum, e) => sum + (e.latency_ms || 0), 0) / last5Events.length)
    : 0;
  const successRate = llmEvents.length > 0
    ? Math.round((llmEvents.filter(e => e.success !== false).length / llmEvents.length) * 100)
    : 100;
  const avgTokens = llmEvents.length > 0
    ? Math.round(llmEvents.reduce((sum, e) => sum + (e.token_total || 0), 0) / llmEvents.length)
    : 0;
  const totalTokens = llmEvents.reduce((sum, e) => sum + (e.token_total || 0), 0);

  // Group events by hour for chart
  const eventsByHour: Record<string, number> = {};
  events.forEach(ev => {
    const hour = new Date(ev.timestamp).toLocaleString('en-US', { 
      month: 'short', day: 'numeric', hour: '2-digit' 
    });
    eventsByHour[hour] = (eventsByHour[hour] || 0) + 1;
  });
  const chartData = Object.entries(eventsByHour).slice(-12).reverse();
  const maxCount = Math.max(...chartData.map(([, count]) => count), 1);

  return (
    <div>
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-4 lg:mb-6">
        <h2 className="text-lg lg:text-xl font-semibold">Analytics Dashboard</h2>
        <div className="flex items-center gap-2">
          <div className="flex bg-apple-surface rounded-lg p-1 border border-apple-border">
            {(['overview', 'events', 'metrics'] as const).map(view => (
              <button
                key={view}
                onClick={() => setActiveView(view)}
                className={`px-3 py-1.5 rounded-md text-xs font-medium transition-colors capitalize ${
                  activeView === view
                    ? 'bg-apple-accent text-white'
                    : 'text-apple-secondary hover:text-white'
                }`}
              >
                {view}
              </button>
            ))}
          </div>
          <button onClick={fetchData} className="p-2 rounded-lg hover:bg-apple-surface text-apple-secondary hover:text-white transition-colors touch-target">
            <HiArrowPath className="w-5 h-5" />
          </button>
        </div>
      </div>

      {activeView === 'overview' && (
        <>
          {/* Stats Cards */}
          {overview && (
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 lg:gap-4 mb-6">
              <StatCard label="Total Users" value={overview.users_total || 0} />
              <StatCard label="Conversations" value={overview.conversations_total || 0} />
              <StatCard label="LLM Requests" value={overview.llm_events || 0} />
              <StatCard label="RAG Files" value={overview.files_total || 0} />
            </div>
          )}

          {/* Performance Metrics from analytics_metrics */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 mb-6">
            <div className="bg-apple-surface rounded-xl border border-apple-border p-4">
              <p className="text-apple-tertiary text-xs mb-1">Avg Response Time</p>
              <p className="text-2xl font-bold text-apple-accent">{avgLatency}ms</p>
              <p className="text-[10px] text-apple-tertiary mt-1">Based on last 5 requests</p>
            </div>
            <div className="bg-apple-surface rounded-xl border border-apple-border p-4">
              <p className="text-apple-tertiary text-xs mb-1">Success Rate</p>
              <p className="text-2xl font-bold text-green-400">{successRate}%</p>
              <div className="mt-2 h-2 bg-apple-elevated rounded-full overflow-hidden">
                <div 
                  className="h-full bg-green-400 rounded-full transition-all"
                  style={{ width: `${successRate}%` }}
                />
              </div>
            </div>
            <div className="bg-apple-surface rounded-xl border border-apple-border p-4">
              <p className="text-apple-tertiary text-xs mb-1">Total Tokens Used</p>
              <p className="text-2xl font-bold text-purple-400">{totalTokens.toLocaleString()}</p>
              <p className="text-[10px] text-apple-tertiary mt-1">Avg {avgTokens} tokens/request</p>
            </div>
          </div>

          {/* Activity Chart */}
          <div className="bg-apple-surface rounded-xl border border-apple-border p-4 mb-6">
            <h3 className="text-sm font-medium mb-4">Recent Activity (by hour)</h3>
            {chartData.length > 0 ? (
              <div className="flex items-end gap-2 h-32">
                {chartData.map(([label, count], i) => (
                  <div key={i} className="flex-1 flex flex-col items-center gap-1">
                    <span className="text-[10px] text-apple-tertiary">{count}</span>
                    <div 
                      className="w-full bg-apple-accent/80 rounded-t transition-all hover:bg-apple-accent"
                      style={{ height: `${(count / maxCount) * 100}%`, minHeight: '4px' }}
                    />
                    <span className="text-[8px] text-apple-tertiary truncate w-full text-center">
                      {label.split(' ').pop()}
                    </span>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-center text-apple-tertiary text-sm py-8">No data available</p>
            )}
          </div>

          {/* Recent Events Preview */}
          <h3 className="text-sm font-medium mb-3">Latest 5 Events</h3>
          <div className="space-y-2">
            {events.slice(0, 5).map((ev, i) => (
              <div key={i} className="flex items-center justify-between bg-apple-surface rounded-lg border border-apple-border p-3">
                <div className="flex items-center gap-3">
                  <span className={`px-2 py-0.5 rounded text-xs ${
                    ev.event_type === 'LLM_RESPONSE' ? 'bg-blue-500/10 text-blue-400' :
                    ev.event_type === 'FILE_PROCESSED' ? 'bg-purple-500/10 text-purple-400' :
                    'bg-apple-accent/10 text-apple-accent'
                  }`}>
                    {ev.event_type}
                  </span>
                  <span className="text-sm text-apple-secondary">{ev.user_id || 'system'}</span>
                </div>
                <div className="flex items-center gap-3 text-xs text-apple-tertiary">
                  {ev.latency_ms && <span>{ev.latency_ms}ms</span>}
                  <span>{new Date(ev.timestamp).toLocaleTimeString('en-US')}</span>
                </div>
              </div>
            ))}
            {events.length === 0 && (
              <p className="text-center text-apple-tertiary text-sm py-4">No events recorded</p>
            )}
          </div>
        </>
      )}

      {activeView === 'events' && (
        <>
          <h3 className="text-base font-medium mb-3">All Events ({events.length})</h3>
          
          {/* Mobile: Card layout */}
          <div className="lg:hidden space-y-3">
            {events.map((ev, i) => (
              <div key={i} className="bg-apple-surface rounded-xl border border-apple-border p-3">
                <div className="flex items-center justify-between mb-2">
                  <span className={`px-2 py-0.5 rounded text-xs ${
                    ev.event_type === 'LLM_RESPONSE' ? 'bg-blue-500/10 text-blue-400' :
                    ev.event_type === 'FILE_PROCESSED' ? 'bg-purple-500/10 text-purple-400' :
                    'bg-apple-accent/10 text-apple-accent'
                  }`}>
                    {ev.event_type}
                  </span>
                  <span className="text-[10px] text-apple-tertiary">
                    {new Date(ev.timestamp).toLocaleString('en-US')}
                  </span>
                </div>
                <p className="text-sm text-apple-secondary truncate">{ev.user_id || '-'}</p>
                <div className="flex items-center gap-2 mt-1 text-xs text-apple-tertiary">
                  {ev.latency_ms && <span>{ev.latency_ms}ms</span>}
                  {ev.token_total && <span>{ev.token_total} tokens</span>}
                  {ev.success === false && <span className="text-apple-red">failed</span>}
                </div>
              </div>
            ))}
            {events.length === 0 && (
              <div className="text-center py-8 text-apple-tertiary text-sm">No events recorded</div>
            )}
          </div>

          {/* Desktop: Table layout */}
          <div className="hidden lg:block bg-apple-surface rounded-xl border border-apple-border overflow-hidden">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-apple-border text-apple-secondary text-xs">
                  <th className="px-4 py-3 text-left">Type</th>
                  <th className="px-4 py-3 text-left">User</th>
                  <th className="px-4 py-3 text-left">Latency</th>
                  <th className="px-4 py-3 text-left">Tokens</th>
                  <th className="px-4 py-3 text-left">Status</th>
                  <th className="px-4 py-3 text-left">Timestamp</th>
                </tr>
              </thead>
              <tbody>
                {events.map((ev, i) => (
                  <tr key={i} className="border-b border-apple-border/50 hover:bg-apple-elevated/30">
                    <td className="px-4 py-2.5">
                      <span className={`px-2 py-0.5 rounded text-xs ${
                        ev.event_type === 'LLM_RESPONSE' ? 'bg-blue-500/10 text-blue-400' :
                        ev.event_type === 'FILE_PROCESSED' ? 'bg-purple-500/10 text-purple-400' :
                        'bg-apple-accent/10 text-apple-accent'
                      }`}>
                        {ev.event_type}
                      </span>
                    </td>
                    <td className="px-4 py-2.5 text-apple-secondary">{ev.user_id || '-'}</td>
                    <td className="px-4 py-2.5">{ev.latency_ms ? `${ev.latency_ms}ms` : '-'}</td>
                    <td className="px-4 py-2.5">{ev.token_total || '-'}</td>
                    <td className="px-4 py-2.5">
                      {ev.success === false ? (
                        <span className="text-apple-red">Failed</span>
                      ) : (
                        <span className="text-green-400">OK</span>
                      )}
                    </td>
                    <td className="px-4 py-2.5 text-apple-tertiary text-xs">
                      {new Date(ev.timestamp).toLocaleString('en-US')}
                    </td>
                  </tr>
                ))}
                {events.length === 0 && (
                  <tr><td colSpan={6} className="px-4 py-8 text-center text-apple-tertiary">No events recorded</td></tr>
                )}
              </tbody>
            </table>
          </div>
        </>
      )}

      {activeView === 'metrics' && (
        <>
          <h3 className="text-base font-medium mb-3">LLM Performance Metrics ({llmEvents.length} requests)</h3>
          
          {/* Latency Distribution */}
          <div className="bg-apple-surface rounded-xl border border-apple-border p-4 mb-4">
            <h4 className="text-sm font-medium mb-3">Latency Distribution</h4>
            <div className="grid grid-cols-4 gap-2 text-center">
              {[
                { label: '< 1s', count: llmEvents.filter(e => (e.latency_ms || 0) < 1000).length, color: 'bg-green-400' },
                { label: '1-2s', count: llmEvents.filter(e => (e.latency_ms || 0) >= 1000 && (e.latency_ms || 0) < 2000).length, color: 'bg-yellow-400' },
                { label: '2-5s', count: llmEvents.filter(e => (e.latency_ms || 0) >= 2000 && (e.latency_ms || 0) < 5000).length, color: 'bg-orange-400' },
                { label: '> 5s', count: llmEvents.filter(e => (e.latency_ms || 0) >= 5000).length, color: 'bg-red-400' },
              ].map((bucket, i) => (
                <div key={i} className="bg-apple-elevated rounded-lg p-3">
                  <div className={`w-3 h-3 rounded-full ${bucket.color} mx-auto mb-2`} />
                  <p className="text-lg font-bold">{bucket.count}</p>
                  <p className="text-[10px] text-apple-tertiary">{bucket.label}</p>
                </div>
              ))}
            </div>
          </div>

          {/* Token Usage Summary */}
          <div className="bg-apple-surface rounded-xl border border-apple-border p-4 mb-4">
            <h4 className="text-sm font-medium mb-3">Token Usage Summary</h4>
            <div className="grid grid-cols-3 gap-4 text-center">
              <div>
                <p className="text-2xl font-bold text-apple-accent">{totalTokens.toLocaleString()}</p>
                <p className="text-xs text-apple-tertiary">Total Tokens</p>
              </div>
              <div>
                <p className="text-2xl font-bold text-purple-400">{avgTokens}</p>
                <p className="text-xs text-apple-tertiary">Avg per Request</p>
              </div>
              <div>
                <p className="text-2xl font-bold text-green-400">
                  {Math.max(...llmEvents.map(e => e.token_total || 0), 0)}
                </p>
                <p className="text-xs text-apple-tertiary">Max Tokens</p>
              </div>
            </div>
          </div>

          {/* Metrics Table */}
          <div className="bg-apple-surface rounded-xl border border-apple-border overflow-hidden">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-apple-border text-apple-secondary text-xs">
                  <th className="px-4 py-3 text-left">User</th>
                  <th className="px-4 py-3 text-left">Model</th>
                  <th className="px-4 py-3 text-left">Latency</th>
                  <th className="px-4 py-3 text-left">Tokens</th>
                  <th className="px-4 py-3 text-left">Status</th>
                  <th className="px-4 py-3 text-left">Timestamp</th>
                </tr>
              </thead>
              <tbody>
                {llmEvents.slice(0, 30).map((e, i) => (
                  <tr key={i} className="border-b border-apple-border/50 hover:bg-apple-elevated/30">
                    <td className="px-4 py-2.5 text-apple-secondary truncate max-w-[150px]">{e.user_id || '-'}</td>
                    <td className="px-4 py-2.5 text-xs text-apple-tertiary">{e.model || '-'}</td>
                    <td className="px-4 py-2.5">
                      <span className={`${
                        (e.latency_ms || 0) < 1000 ? 'text-green-400' :
                        (e.latency_ms || 0) < 3000 ? 'text-yellow-400' :
                        'text-red-400'
                      }`}>
                        {e.latency_ms}ms
                      </span>
                    </td>
                    <td className="px-4 py-2.5">{e.token_total || '-'}</td>
                    <td className="px-4 py-2.5">
                      {e.success === false ? (
                        <span className="text-apple-red">Failed</span>
                      ) : (
                        <span className="text-green-400">OK</span>
                      )}
                    </td>
                    <td className="px-4 py-2.5 text-apple-tertiary text-xs">
                      {new Date(e.timestamp).toLocaleString('en-US')}
                    </td>
                  </tr>
                ))}
                {llmEvents.length === 0 && (
                  <tr><td colSpan={6} className="px-4 py-8 text-center text-apple-tertiary">No LLM events recorded</td></tr>
                )}
              </tbody>
            </table>
          </div>
        </>
      )}
    </div>
  );
};

// ===== Users Tab =====
const UsersTab: React.FC = () => {
  const [users, setUsers] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchUsers = useCallback(async () => {
    setLoading(true);
    try {
      const data = await getUsers();
      setUsers(data.users || []);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { fetchUsers(); }, [fetchUsers]);

  const handleDelete = async (id: string) => {
    if (!window.confirm('Delete this user?')) return;
    try {
      await deleteUser(id);
      fetchUsers();
    } catch (e) {
      console.error(e);
    }
  };

  if (loading) return <LoadingState />;

  return (
    <div>
      <div className="flex items-center justify-between mb-4 lg:mb-6">
        <h2 className="text-lg lg:text-xl font-semibold">Users</h2>
        <button onClick={fetchUsers} className="p-2 rounded-lg hover:bg-apple-surface text-apple-secondary hover:text-white transition-colors touch-target">
          <HiArrowPath className="w-5 h-5" />
        </button>
      </div>

      {/* Mobile: Card layout */}
      <div className="lg:hidden space-y-3">
        {users.map((u) => (
          <div key={u.id} className="bg-apple-surface rounded-xl border border-apple-border p-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                {u.picture ? (
                  <img src={u.picture} alt="" className="w-10 h-10 rounded-full" />
                ) : (
                  <div className="w-10 h-10 rounded-full bg-apple-elevated flex items-center justify-center text-apple-secondary">
                    {u.name?.charAt(0) || '?'}
                  </div>
                )}
                <div>
                  <p className="font-medium text-sm">{u.name || 'Unknown'}</p>
                  <p className="text-xs text-apple-secondary truncate max-w-[180px]">{u.email}</p>
                </div>
              </div>
              <button onClick={() => handleDelete(u.id)} className="p-2 rounded-lg hover:bg-apple-red/10 text-apple-tertiary hover:text-apple-red transition-colors touch-target">
                <HiTrash className="w-5 h-5" />
              </button>
            </div>
            <p className="text-[10px] text-apple-tertiary mt-2">
              Created: {u.created_at ? new Date(u.created_at).toLocaleDateString() : '-'}
            </p>
          </div>
        ))}
        {users.length === 0 && (
          <div className="text-center py-8 text-apple-tertiary text-sm">No users found</div>
        )}
      </div>

      {/* Desktop: Table layout */}
      <div className="hidden lg:block bg-apple-surface rounded-xl border border-apple-border overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-apple-border text-apple-secondary text-xs">
              <th className="px-4 py-3 text-left">User</th>
              <th className="px-4 py-3 text-left">Email</th>
              <th className="px-4 py-3 text-left">Created</th>
              <th className="px-4 py-3 text-right">Actions</th>
            </tr>
          </thead>
          <tbody>
            {users.map((u) => (
              <tr key={u.id} className="border-b border-apple-border/50 hover:bg-apple-elevated/30">
                <td className="px-4 py-2.5 flex items-center gap-3">
                  {u.picture ? (
                    <img src={u.picture} alt="" className="w-8 h-8 rounded-full" />
                  ) : (
                    <div className="w-8 h-8 rounded-full bg-apple-elevated flex items-center justify-center text-apple-secondary text-xs">
                      {u.name?.charAt(0) || '?'}
                    </div>
                  )}
                  <span>{u.name || 'Unknown'}</span>
                </td>
                <td className="px-4 py-2.5 text-apple-secondary">{u.email}</td>
                <td className="px-4 py-2.5 text-apple-tertiary text-xs">
                  {u.created_at ? new Date(u.created_at).toLocaleDateString() : '-'}
                </td>
                <td className="px-4 py-2.5 text-right">
                  <button onClick={() => handleDelete(u.id)} className="p-1.5 rounded-lg hover:bg-apple-red/10 text-apple-tertiary hover:text-apple-red transition-colors">
                    <HiTrash className="w-4 h-4" />
                  </button>
                </td>
              </tr>
            ))}
            {users.length === 0 && (
              <tr><td colSpan={4} className="px-4 py-8 text-center text-apple-tertiary">No users found</td></tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};

// ===== Conversations Tab =====
const ConversationsTab: React.FC = () => {
  const [conversations, setConversations] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchConversations = useCallback(async () => {
    setLoading(true);
    try {
      const data = await getAdminConversations();
      setConversations(data.conversations || []);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { fetchConversations(); }, [fetchConversations]);

  const handleDelete = async (id: string) => {
    if (!window.confirm('Delete this conversation?')) return;
    try {
      await deleteAdminConversation(id);
      fetchConversations();
    } catch (e) {
      console.error(e);
    }
  };

  if (loading) return <LoadingState />;

  return (
    <div>
      <div className="flex items-center justify-between mb-4 lg:mb-6">
        <h2 className="text-lg lg:text-xl font-semibold">Conversations</h2>
        <button onClick={fetchConversations} className="p-2 rounded-lg hover:bg-apple-surface text-apple-secondary hover:text-white transition-colors touch-target">
          <HiArrowPath className="w-5 h-5" />
        </button>
      </div>

      {/* Mobile: Card layout */}
      <div className="lg:hidden space-y-3">
        {conversations.map((c) => (
          <div key={c.id} className="bg-apple-surface rounded-xl border border-apple-border p-3">
            <div className="flex items-start justify-between gap-2">
              <div className="flex-1 min-w-0">
                <p className="font-medium text-sm truncate">{c.title}</p>
                <p className="text-xs text-apple-secondary truncate mt-0.5">{c.user_id}</p>
              </div>
              <button onClick={() => handleDelete(c.id)} className="p-2 rounded-lg hover:bg-apple-red/10 text-apple-tertiary hover:text-apple-red transition-colors touch-target flex-shrink-0">
                <HiTrash className="w-5 h-5" />
              </button>
            </div>
            <div className="flex items-center justify-between mt-2 text-[10px] text-apple-tertiary">
              <span>{c.message_count} messages</span>
              <span>{new Date(c.updated_at).toLocaleDateString()}</span>
            </div>
          </div>
        ))}
        {conversations.length === 0 && (
          <div className="text-center py-8 text-apple-tertiary text-sm">No conversations found</div>
        )}
      </div>

      {/* Desktop: Table layout */}
      <div className="hidden lg:block bg-apple-surface rounded-xl border border-apple-border overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-apple-border text-apple-secondary text-xs">
              <th className="px-4 py-3 text-left">Title</th>
              <th className="px-4 py-3 text-left">User</th>
              <th className="px-4 py-3 text-left">Messages</th>
              <th className="px-4 py-3 text-left">Updated</th>
              <th className="px-4 py-3 text-right">Actions</th>
            </tr>
          </thead>
          <tbody>
            {conversations.map((c) => (
              <tr key={c.id} className="border-b border-apple-border/50 hover:bg-apple-elevated/30">
                <td className="px-4 py-2.5 max-w-[200px] truncate">{c.title}</td>
                <td className="px-4 py-2.5 text-apple-secondary text-xs">{c.user_id}</td>
                <td className="px-4 py-2.5">{c.message_count}</td>
                <td className="px-4 py-2.5 text-apple-tertiary text-xs">
                  {new Date(c.updated_at).toLocaleString()}
                </td>
                <td className="px-4 py-2.5 text-right">
                  <button onClick={() => handleDelete(c.id)} className="p-1.5 rounded-lg hover:bg-apple-red/10 text-apple-tertiary hover:text-apple-red transition-colors">
                    <HiTrash className="w-4 h-4" />
                  </button>
                </td>
              </tr>
            ))}
            {conversations.length === 0 && (
              <tr><td colSpan={5} className="px-4 py-8 text-center text-apple-tertiary">No conversations found</td></tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};

// ===== Prompts Tab =====
const PromptsTab: React.FC = () => {
  const [systemPrompt, setSystemPrompt] = useState('');
  const [ragTemplate, setRagTemplate] = useState('');
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState('');

  const fetchPrompts = useCallback(async () => {
    setLoading(true);
    try {
      const data = await getPrompts();
      setSystemPrompt(data.system_prompt || '');
      setRagTemplate(data.rag_prompt_template || '');
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { fetchPrompts(); }, [fetchPrompts]);

  const handleSave = async () => {
    setSaving(true);
    setMessage('');
    try {
      await updatePrompts(systemPrompt, ragTemplate);
      setMessage('Prompts saved successfully');
      setTimeout(() => setMessage(''), 3000);
    } catch (e) {
      setMessage('Failed to save prompts');
    } finally {
      setSaving(false);
    }
  };

  if (loading) return <LoadingState />;

  return (
    <div className="max-w-3xl">
      <div className="flex items-center justify-between mb-4 lg:mb-6">
        <h2 className="text-lg lg:text-xl font-semibold">System Prompts</h2>
      </div>

      <div className="space-y-4 lg:space-y-6">
        <div>
          <label className="block text-sm text-apple-secondary mb-2">System Prompt</label>
          <textarea
            value={systemPrompt}
            onChange={(e) => setSystemPrompt(e.target.value)}
            rows={6}
            className="w-full px-3 lg:px-4 py-3 rounded-xl bg-apple-surface border border-apple-border text-white text-sm focus:outline-none focus:border-apple-accent/50 transition-colors resize-none mobile-input"
            placeholder="You are Alice, a helpful AI assistant..."
          />
        </div>

        <div>
          <label className="block text-sm text-apple-secondary mb-2">RAG Prompt Template</label>
          <p className="text-xs text-apple-tertiary mb-2">Use {'{context}'} as placeholder for retrieved context</p>
          <textarea
            value={ragTemplate}
            onChange={(e) => setRagTemplate(e.target.value)}
            rows={6}
            className="w-full px-3 lg:px-4 py-3 rounded-xl bg-apple-surface border border-apple-border text-white text-sm focus:outline-none focus:border-apple-accent/50 transition-colors resize-none font-mono mobile-input"
            placeholder="Context:\n---\n{context}\n---\nAnswer the user's question."
          />
        </div>

        <div className="flex flex-col sm:flex-row items-start sm:items-center gap-3 sm:gap-4">
          <button
            onClick={handleSave}
            disabled={saving}
            className="w-full sm:w-auto px-6 py-3 lg:py-2.5 rounded-xl bg-gradient-to-r from-[#0A84FF] to-[#5E5CE6] text-white font-medium text-sm hover:opacity-90 transition-opacity disabled:opacity-50 touch-target"
          >
            {saving ? 'Saving...' : 'Save Prompts'}
          </button>
          {message && (
            <span className={`text-sm ${message.includes('success') ? 'text-green-400' : 'text-apple-red'}`}>
              {message}
            </span>
          )}
        </div>
      </div>
    </div>
  );
};

// ===== RAG Data Tab =====
const RagDataTab: React.FC = () => {
  const [files, setFiles] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);

  const fetchFiles = useCallback(async () => {
    setLoading(true);
    try {
      const data = await getRagData();
      setFiles(data.files || []);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { fetchFiles(); }, [fetchFiles]);

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploading(true);
    setUploadError(null);
    try {
      await uploadRagData(file);
      fetchFiles();
    } catch (err: any) {
      console.error(err);
      setUploadError(err?.response?.data?.detail || err?.message || 'Upload failed');
    } finally {
      setUploading(false);
      e.target.value = '';
    }
  };

  const handleDelete = async (id: string) => {
    if (!window.confirm('Delete this RAG data file?')) return;
    try {
      await deleteRagData(id);
      fetchFiles();
    } catch (e) {
      console.error(e);
    }
  };

  if (loading) return <LoadingState />;

  return (
    <div>
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-4 lg:mb-6">
        <h2 className="text-lg lg:text-xl font-semibold">RAG Knowledge Base</h2>
        <div className="flex items-center gap-2">
          <button onClick={fetchFiles} className="p-2 rounded-lg hover:bg-apple-surface text-apple-secondary hover:text-white transition-colors touch-target">
            <HiArrowPath className="w-5 h-5" />
          </button>
          <label className={`flex items-center gap-2 px-4 py-2.5 lg:py-2 rounded-xl bg-gradient-to-r from-[#0A84FF] to-[#5E5CE6] text-white text-sm font-medium cursor-pointer hover:opacity-90 transition-opacity touch-target ${uploading ? 'opacity-50 pointer-events-none' : ''}`}>
            <HiArrowUpTray className="w-4 h-4" />
            {uploading ? 'Uploading...' : 'Upload'}
            <input type="file" accept=".pdf,.docx,.txt,.csv,.xlsx" onChange={handleUpload} className="hidden" />
          </label>
        </div>
      </div>

      <p className="text-xs lg:text-sm text-apple-tertiary mb-4">
        Upload PDF, DOCX, TXT, CSV, or XLSX files to add to the global knowledge base.
      </p>

      {uploadError && (
        <div className="mb-4 p-3 rounded-lg bg-red-500/10 border border-red-500/20 text-red-400 text-sm">
          {uploadError}
        </div>
      )}

      {/* Mobile: Card layout */}
      <div className="lg:hidden space-y-3">
        {files.map((f) => (
          <div key={f.id} className="bg-apple-surface rounded-xl border border-apple-border p-3">
            <div className="flex items-start justify-between gap-2">
              <div className="flex items-center gap-2 flex-1 min-w-0">
                <HiClipboardDocument className="w-5 h-5 text-apple-accent flex-shrink-0" />
                <div className="min-w-0">
                  <p className="font-medium text-sm truncate">{f.original_name}</p>
                  <div className="flex items-center gap-2 mt-0.5 text-[10px] text-apple-tertiary">
                    <span className="uppercase">{f.file_type}</span>
                    <span>{(f.file_size / 1024).toFixed(1)} KB</span>
                    <span>{f.chunk_count} chunks</span>
                  </div>
                </div>
              </div>
              <button onClick={() => handleDelete(f.id)} className="p-2 rounded-lg hover:bg-apple-red/10 text-apple-tertiary hover:text-apple-red transition-colors touch-target flex-shrink-0">
                <HiTrash className="w-5 h-5" />
              </button>
            </div>
            <div className="mt-2">
              <span className={`px-2 py-0.5 rounded text-xs ${
                f.status === 'completed' ? 'bg-green-500/10 text-green-400' : 
                f.status === 'failed' ? 'bg-red-500/10 text-red-400' :
                'bg-yellow-500/10 text-yellow-400'
              }`}>
                {f.status}
              </span>
              {f.error && <p className="text-xs text-apple-red mt-1 truncate">{f.error}</p>}
            </div>
          </div>
        ))}
        {files.length === 0 && (
          <div className="text-center py-8 text-apple-tertiary text-sm">No RAG data files uploaded yet</div>
        )}
      </div>

      {/* Desktop: Table layout */}
      <div className="hidden lg:block bg-apple-surface rounded-xl border border-apple-border overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-apple-border text-apple-secondary text-xs">
              <th className="px-4 py-3 text-left">File Name</th>
              <th className="px-4 py-3 text-left">Type</th>
              <th className="px-4 py-3 text-left">Size</th>
              <th className="px-4 py-3 text-left">Chunks</th>
              <th className="px-4 py-3 text-left">Status</th>
              <th className="px-4 py-3 text-right">Actions</th>
            </tr>
          </thead>
          <tbody>
            {files.map((f) => (
              <tr key={f.id} className="border-b border-apple-border/50 hover:bg-apple-elevated/30">
                <td className="px-4 py-2.5 flex items-center gap-2">
                  <HiClipboardDocument className="w-4 h-4 text-apple-accent flex-shrink-0" />
                  <span className="truncate max-w-[200px]">{f.original_name}</span>
                </td>
                <td className="px-4 py-2.5 text-apple-secondary uppercase text-xs">{f.file_type}</td>
                <td className="px-4 py-2.5 text-apple-secondary">{(f.file_size / 1024).toFixed(1)} KB</td>
                <td className="px-4 py-2.5">{f.chunk_count}</td>
                <td className="px-4 py-2.5">
                  <span className={`px-2 py-0.5 rounded text-xs ${
                    f.status === 'completed' ? 'bg-green-500/10 text-green-400' : 
                    f.status === 'failed' ? 'bg-red-500/10 text-red-400' :
                    'bg-yellow-500/10 text-yellow-400'
                  }`}>
                    {f.status}
                  </span>
                  {f.error && <p className="text-xs text-apple-red mt-1 truncate max-w-[150px]" title={f.error}>{f.error}</p>}
                </td>
                <td className="px-4 py-2.5 text-right">
                  <button onClick={() => handleDelete(f.id)} className="p-1.5 rounded-lg hover:bg-apple-red/10 text-apple-tertiary hover:text-apple-red transition-colors">
                    <HiTrash className="w-4 h-4" />
                  </button>
                </td>
              </tr>
            ))}
            {files.length === 0 && (
              <tr><td colSpan={6} className="px-4 py-8 text-center text-apple-tertiary">No RAG data files uploaded yet</td></tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};

// ===== IP Management Tab =====
const IPManagementTab: React.FC = () => {
  const [summary, setSummary] = useState<IPSummaryResponse | null>(null);
  const [messages, setMessages] = useState<IPMessagesResponse | null>(null);
  const [blacklist, setBlacklist] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeView, setActiveView] = useState<'summary' | 'messages' | 'blacklist'>('summary');
  const [ipFilter, setIpFilter] = useState('');
  const [newBlockIP, setNewBlockIP] = useState('');
  const [newBlockReason, setNewBlockReason] = useState('');
  const [newBlockTTL, setNewBlockTTL] = useState('24');
  const [actionLoading, setActionLoading] = useState(false);

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const [summaryData, messagesData, blacklistData] = await Promise.all([
        getIPSummary(),
        getIPMessages(ipFilter || undefined),
        getIPBlacklist(),
      ]);
      setSummary(summaryData);
      setMessages(messagesData);
      setBlacklist(blacklistData.blacklisted_ips || []);
    } catch (e) {
      console.error('Failed to fetch IP data:', e);
    } finally {
      setLoading(false);
    }
  }, [ipFilter]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const handleBlockIP = async () => {
    if (!newBlockIP.trim()) return;
    setActionLoading(true);
    try {
      await blacklistIP(newBlockIP.trim(), newBlockReason, parseInt(newBlockTTL) || 24);
      setNewBlockIP('');
      setNewBlockReason('');
      setNewBlockTTL('24');
      await fetchData();
    } catch (e) {
      console.error('Failed to block IP:', e);
      alert('Failed to block IP');
    } finally {
      setActionLoading(false);
    }
  };

  const handleUnblockIP = async (ip: string) => {
    if (!confirm(`Unblock IP ${ip}?`)) return;
    setActionLoading(true);
    try {
      await unblacklistIP(ip);
      await fetchData();
    } catch (e) {
      console.error('Failed to unblock IP:', e);
      alert('Failed to unblock IP');
    } finally {
      setActionLoading(false);
    }
  };

  const handleSearchIP = async () => {
    setLoading(true);
    try {
      const messagesData = await getIPMessages(ipFilter || undefined);
      setMessages(messagesData);
    } catch (e) {
      console.error('Failed to search messages:', e);
    } finally {
      setLoading(false);
    }
  };

  if (loading && !summary) return <LoadingState />;

  return (
    <div className="space-y-4 lg:space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
        <h2 className="text-xl lg:text-2xl font-bold">IP Management</h2>
        <button onClick={fetchData} className="flex items-center justify-center gap-2 px-4 py-2 bg-apple-surface rounded-lg text-sm hover:bg-apple-elevated transition-colors">
          <HiArrowPath className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          Refresh
        </button>
      </div>

      {/* Stats Cards */}
      {summary && (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 lg:gap-4">
          <StatCard label="Messages Today" value={summary.total_messages_today} />
          <StatCard label="Unique IPs Today" value={summary.unique_ips_today} />
          <StatCard label="Blacklisted IPs" value={blacklist.length} />
          <StatCard label="Active IPs" value={summary.ip_activity?.length || 0} />
        </div>
      )}

      {/* View Toggle */}
      <div className="flex gap-2 overflow-x-auto pb-2">
        {(['summary', 'messages', 'blacklist'] as const).map((view) => (
          <button
            key={view}
            onClick={() => setActiveView(view)}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors whitespace-nowrap ${
              activeView === view
                ? 'bg-apple-accent text-white'
                : 'bg-apple-surface text-apple-secondary hover:bg-apple-elevated'
            }`}
          >
            {view === 'summary' ? 'IP Activity' : view === 'messages' ? 'Messages by IP' : 'Blacklist'}
          </button>
        ))}
      </div>

      {/* Summary View */}
      {activeView === 'summary' && summary && (
        <div className="space-y-4">
          <h3 className="text-lg font-semibold">Top IP Activity Today</h3>
          
          {/* Mobile Cards */}
          <div className="lg:hidden space-y-3">
            {summary.ip_activity?.map((item) => (
              <div key={item.ip} className="bg-apple-surface rounded-xl border border-apple-border p-4">
                <div className="flex justify-between items-start mb-2">
                  <div className="flex items-center gap-2">
                    <HiGlobeAlt className="w-4 h-4 text-apple-accent" />
                    <span className="font-mono text-sm">{item.ip}</span>
                  </div>
                  {blacklist.includes(item.ip) && (
                    <span className="px-2 py-0.5 bg-red-500/10 text-red-400 text-xs rounded">Blocked</span>
                  )}
                </div>
                <div className="grid grid-cols-2 gap-2 text-sm">
                  <div>
                    <span className="text-apple-tertiary">Messages: </span>
                    <span className="font-semibold">{item.message_count}</span>
                  </div>
                  <div>
                    <span className="text-apple-tertiary">Users: </span>
                    <span className="font-semibold">{item.unique_users_count}</span>
                  </div>
                </div>
                <div className="text-xs text-apple-tertiary mt-2">
                  Last: {new Date(item.last_activity).toLocaleString()}
                </div>
                {!blacklist.includes(item.ip) && (
                  <button
                    onClick={() => {
                      setNewBlockIP(item.ip);
                      setActiveView('blacklist');
                    }}
                    className="mt-2 w-full py-1.5 bg-red-500/10 text-red-400 rounded text-xs hover:bg-red-500/20 transition-colors"
                  >
                    Block IP
                  </button>
                )}
              </div>
            ))}
            {(!summary.ip_activity || summary.ip_activity.length === 0) && (
              <div className="text-center py-8 text-apple-tertiary">No IP activity recorded today</div>
            )}
          </div>

          {/* Desktop Table */}
          <div className="hidden lg:block bg-apple-surface rounded-xl border border-apple-border overflow-hidden">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-apple-border text-apple-secondary text-xs">
                  <th className="px-4 py-3 text-left">IP Address</th>
                  <th className="px-4 py-3 text-left">Messages</th>
                  <th className="px-4 py-3 text-left">Unique Users</th>
                  <th className="px-4 py-3 text-left">Last Activity</th>
                  <th className="px-4 py-3 text-left">Status</th>
                  <th className="px-4 py-3 text-right">Actions</th>
                </tr>
              </thead>
              <tbody>
                {summary.ip_activity?.map((item) => (
                  <tr key={item.ip} className="border-b border-apple-border/50 hover:bg-apple-elevated/30">
                    <td className="px-4 py-2.5 font-mono">{item.ip}</td>
                    <td className="px-4 py-2.5">{item.message_count}</td>
                    <td className="px-4 py-2.5">{item.unique_users_count}</td>
                    <td className="px-4 py-2.5 text-apple-secondary">{new Date(item.last_activity).toLocaleString()}</td>
                    <td className="px-4 py-2.5">
                      {blacklist.includes(item.ip) ? (
                        <span className="px-2 py-0.5 bg-red-500/10 text-red-400 text-xs rounded">Blocked</span>
                      ) : (
                        <span className="px-2 py-0.5 bg-green-500/10 text-green-400 text-xs rounded">Active</span>
                      )}
                    </td>
                    <td className="px-4 py-2.5 text-right">
                      {!blacklist.includes(item.ip) && (
                        <button
                          onClick={() => {
                            setNewBlockIP(item.ip);
                            setActiveView('blacklist');
                          }}
                          className="p-1.5 rounded-lg hover:bg-red-500/10 text-apple-tertiary hover:text-red-400 transition-colors"
                          title="Block IP"
                        >
                          <HiNoSymbol className="w-4 h-4" />
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
                {(!summary.ip_activity || summary.ip_activity.length === 0) && (
                  <tr><td colSpan={6} className="px-4 py-8 text-center text-apple-tertiary">No IP activity recorded today</td></tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Messages View */}
      {activeView === 'messages' && (
        <div className="space-y-4">
          <div className="flex gap-2">
            <div className="flex-1 relative">
              <HiMagnifyingGlass className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-apple-tertiary" />
              <input
                type="text"
                placeholder="Filter by IP address..."
                value={ipFilter}
                onChange={(e) => setIpFilter(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleSearchIP()}
                className="w-full pl-10 pr-4 py-2.5 bg-apple-surface border border-apple-border rounded-lg text-sm focus:outline-none focus:border-apple-accent"
              />
            </div>
            <button
              onClick={handleSearchIP}
              className="px-4 py-2.5 bg-apple-accent rounded-lg text-sm font-medium hover:bg-blue-600 transition-colors"
            >
              Search
            </button>
          </div>

          {/* Messages List */}
          <div className="bg-apple-surface rounded-xl border border-apple-border overflow-hidden">
            <div className="p-3 border-b border-apple-border text-sm text-apple-secondary">
              {messages?.total || 0} messages found
            </div>
            <div className="divide-y divide-apple-border/50 max-h-[500px] overflow-y-auto">
              {messages?.messages?.map((msg) => (
                <div key={msg.id} className="p-4 hover:bg-apple-elevated/30">
                  <div className="flex justify-between items-start mb-2">
                    <div className="flex items-center gap-2">
                      <HiGlobeAlt className="w-4 h-4 text-apple-accent" />
                      <span className="font-mono text-sm">{msg.ip}</span>
                      {blacklist.includes(msg.ip) && (
                        <span className="px-1.5 py-0.5 bg-red-500/10 text-red-400 text-xs rounded">Blocked</span>
                      )}
                    </div>
                    <span className="text-xs text-apple-tertiary">{new Date(msg.timestamp).toLocaleString()}</span>
                  </div>
                  <div className="text-sm text-apple-secondary mb-1">
                    <span className="text-apple-tertiary">User: </span>{msg.user_id}
                  </div>
                  <p className="text-sm text-white/90 bg-apple-elevated/50 p-2 rounded-lg">
                    {msg.message_preview || '(empty message)'}
                  </p>
                </div>
              ))}
              {(!messages?.messages || messages.messages.length === 0) && (
                <div className="p-8 text-center text-apple-tertiary">No messages found</div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Blacklist View */}
      {activeView === 'blacklist' && (
        <div className="space-y-4">
          {/* Add to Blacklist Form */}
          <div className="bg-apple-surface rounded-xl border border-apple-border p-4">
            <h3 className="text-sm font-semibold mb-3 flex items-center gap-2">
              <HiPlus className="w-4 h-4" />
              Add IP to Blacklist
            </h3>
            <div className="grid grid-cols-1 sm:grid-cols-4 gap-3">
              <input
                type="text"
                placeholder="IP Address *"
                value={newBlockIP}
                onChange={(e) => setNewBlockIP(e.target.value)}
                className="px-3 py-2 bg-apple-elevated border border-apple-border rounded-lg text-sm focus:outline-none focus:border-apple-accent"
              />
              <input
                type="text"
                placeholder="Reason (optional)"
                value={newBlockReason}
                onChange={(e) => setNewBlockReason(e.target.value)}
                className="px-3 py-2 bg-apple-elevated border border-apple-border rounded-lg text-sm focus:outline-none focus:border-apple-accent"
              />
              <input
                type="number"
                placeholder="TTL Hours"
                value={newBlockTTL}
                onChange={(e) => setNewBlockTTL(e.target.value)}
                className="px-3 py-2 bg-apple-elevated border border-apple-border rounded-lg text-sm focus:outline-none focus:border-apple-accent"
              />
              <button
                onClick={handleBlockIP}
                disabled={!newBlockIP.trim() || actionLoading}
                className="px-4 py-2 bg-red-500 text-white rounded-lg text-sm font-medium hover:bg-red-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {actionLoading ? 'Blocking...' : 'Block IP'}
              </button>
            </div>
          </div>

          {/* Blacklisted IPs List */}
          <div className="bg-apple-surface rounded-xl border border-apple-border overflow-hidden">
            <div className="p-3 border-b border-apple-border text-sm text-apple-secondary">
              {blacklist.length} IP{blacklist.length !== 1 ? 's' : ''} blacklisted
            </div>
            <div className="divide-y divide-apple-border/50">
              {blacklist.map((ip) => (
                <div key={ip} className="p-4 flex items-center justify-between hover:bg-apple-elevated/30">
                  <div className="flex items-center gap-3">
                    <HiNoSymbol className="w-5 h-5 text-red-400" />
                    <span className="font-mono">{ip}</span>
                  </div>
                  <button
                    onClick={() => handleUnblockIP(ip)}
                    disabled={actionLoading}
                    className="px-3 py-1.5 bg-green-500/10 text-green-400 rounded text-sm hover:bg-green-500/20 transition-colors disabled:opacity-50"
                  >
                    Unblock
                  </button>
                </div>
              ))}
              {blacklist.length === 0 && (
                <div className="p-8 text-center text-apple-tertiary">No IPs are currently blacklisted</div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

// ===== Dead Letter Queue Tab =====
const DLQTab: React.FC = () => {
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);
  const [summary, setSummary] = useState<DLQSummaryResponse | null>(null);
  const [tasks, setTasks] = useState<DLQTask[]>([]);
  const [total, setTotal] = useState(0);
  const [skip, setSkip] = useState(0);
  const [selectedTasks, setSelectedTasks] = useState<Set<string>>(new Set());
  const [selectedTask, setSelectedTask] = useState<DLQTaskDetail | null>(null);
  const [showDetailModal, setShowDetailModal] = useState(false);
  
  // Filters
  const [filterStatus, setFilterStatus] = useState<string>('');
  const [filterTaskType, setFilterTaskType] = useState<string>('');
  const [filterDateFrom, setFilterDateFrom] = useState<string>('');
  const [filterDateTo, setFilterDateTo] = useState<string>('');
  
  // Clear modal
  const [showClearModal, setShowClearModal] = useState(false);
  const [clearStatus, setClearStatus] = useState<string>('');
  const [clearOlderThanDays, setClearOlderThanDays] = useState<string>('30');

  const limit = 20;

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const [summaryData, tasksData] = await Promise.all([
        getDLQSummary(),
        getDLQTasks(
          filterStatus || undefined,
          filterTaskType || undefined,
          filterDateFrom || undefined,
          filterDateTo || undefined,
          skip,
          limit
        ),
      ]);
      setSummary(summaryData);
      setTasks(tasksData.tasks);
      setTotal(tasksData.total);
    } catch (err) {
      console.error('Failed to fetch DLQ data:', err);
    } finally {
      setLoading(false);
    }
  }, [filterStatus, filterTaskType, filterDateFrom, filterDateTo, skip]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const handleSelectAll = () => {
    if (selectedTasks.size === tasks.length) {
      setSelectedTasks(new Set());
    } else {
      setSelectedTasks(new Set(tasks.map(t => t.id)));
    }
  };

  const handleSelectTask = (taskId: string) => {
    const newSelected = new Set(selectedTasks);
    if (newSelected.has(taskId)) {
      newSelected.delete(taskId);
    } else {
      newSelected.add(taskId);
    }
    setSelectedTasks(newSelected);
  };

  const handleViewDetail = async (taskId: string) => {
    try {
      const detail = await getDLQTaskDetail(taskId);
      setSelectedTask(detail);
      setShowDetailModal(true);
    } catch (err) {
      console.error('Failed to fetch task detail:', err);
    }
  };

  const handleRetrySelected = async () => {
    if (selectedTasks.size === 0) return;
    setActionLoading(true);
    try {
      await retryDLQTasks(Array.from(selectedTasks));
      setSelectedTasks(new Set());
      await fetchData();
    } catch (err) {
      console.error('Failed to retry tasks:', err);
    } finally {
      setActionLoading(false);
    }
  };

  const handleDeleteSelected = async () => {
    if (selectedTasks.size === 0) return;
    if (!confirm(`Delete ${selectedTasks.size} task(s)? This cannot be undone.`)) return;
    setActionLoading(true);
    try {
      await deleteDLQTasks(Array.from(selectedTasks));
      setSelectedTasks(new Set());
      await fetchData();
    } catch (err) {
      console.error('Failed to delete tasks:', err);
    } finally {
      setActionLoading(false);
    }
  };

  const handleClearDLQ = async () => {
    setActionLoading(true);
    try {
      await clearDLQ(
        clearStatus || undefined,
        clearOlderThanDays ? parseInt(clearOlderThanDays) : undefined
      );
      setShowClearModal(false);
      await fetchData();
    } catch (err) {
      console.error('Failed to clear DLQ:', err);
    } finally {
      setActionLoading(false);
    }
  };

  const handleExport = async () => {
    try {
      const data = await exportDLQTasks(filterStatus || undefined, filterTaskType || undefined);
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `dlq-export-${new Date().toISOString().split('T')[0]}.json`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (err) {
      console.error('Failed to export DLQ:', err);
    }
  };

  const formatDate = (dateStr: string) => {
    if (!dateStr) return '-';
    return new Date(dateStr).toLocaleString();
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'failed': return 'text-red-400 bg-red-400/10';
      case 'pending_retry': return 'text-yellow-400 bg-yellow-400/10';
      case 'resolved': return 'text-green-400 bg-green-400/10';
      default: return 'text-apple-tertiary bg-apple-elevated';
    }
  };

  if (loading && !summary) return <LoadingState />;

  return (
    <div className="space-y-4 lg:space-y-6">
      {/* Summary Cards */}
      {summary && (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 lg:gap-4">
          <div className="bg-apple-surface rounded-xl border border-apple-border p-3 lg:p-4">
            <p className="text-apple-tertiary text-[10px] lg:text-xs mb-1">Total Tasks</p>
            <p className="text-xl lg:text-2xl font-bold">{summary.total.toLocaleString()}</p>
          </div>
          <div className="bg-apple-surface rounded-xl border border-red-500/30 p-3 lg:p-4">
            <p className="text-red-400 text-[10px] lg:text-xs mb-1">Failed (24h)</p>
            <p className="text-xl lg:text-2xl font-bold text-red-400">{summary.recent_failures_24h.toLocaleString()}</p>
          </div>
          <div className="bg-apple-surface rounded-xl border border-yellow-500/30 p-3 lg:p-4">
            <p className="text-yellow-400 text-[10px] lg:text-xs mb-1">Pending Retry</p>
            <p className="text-xl lg:text-2xl font-bold text-yellow-400">{summary.pending_retry.toLocaleString()}</p>
          </div>
          <div className="bg-apple-surface rounded-xl border border-apple-border p-3 lg:p-4">
            <p className="text-apple-tertiary text-[10px] lg:text-xs mb-1">Task Types</p>
            <p className="text-xl lg:text-2xl font-bold">{Object.keys(summary.by_task_type).length}</p>
          </div>
        </div>
      )}

      {/* Stats by Type */}
      {summary && Object.keys(summary.by_error_type).length > 0 && (
        <div className="bg-apple-surface rounded-xl border border-apple-border p-4">
          <h3 className="text-sm font-medium mb-3">Errors by Type</h3>
          <div className="flex flex-wrap gap-2">
            {Object.entries(summary.by_error_type).map(([type, count]) => (
              <span key={type} className="px-3 py-1.5 bg-red-400/10 text-red-400 rounded-lg text-xs">
                {type}: {count}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Filters & Actions */}
      <div className="bg-apple-surface rounded-xl border border-apple-border p-4">
        <div className="flex flex-col lg:flex-row gap-3 lg:items-center lg:justify-between">
          <div className="flex flex-wrap gap-2">
            <select
              value={filterStatus}
              onChange={(e) => { setFilterStatus(e.target.value); setSkip(0); }}
              className="px-3 py-2 bg-apple-elevated border border-apple-border rounded-lg text-sm focus:outline-none focus:border-apple-accent"
            >
              <option value="">All Status</option>
              <option value="failed">Failed</option>
              <option value="pending_retry">Pending Retry</option>
              <option value="resolved">Resolved</option>
            </select>
            <input
              type="text"
              placeholder="Task Type"
              value={filterTaskType}
              onChange={(e) => { setFilterTaskType(e.target.value); setSkip(0); }}
              className="px-3 py-2 bg-apple-elevated border border-apple-border rounded-lg text-sm focus:outline-none focus:border-apple-accent w-32"
            />
            <input
              type="date"
              value={filterDateFrom}
              onChange={(e) => { setFilterDateFrom(e.target.value); setSkip(0); }}
              className="px-3 py-2 bg-apple-elevated border border-apple-border rounded-lg text-sm focus:outline-none focus:border-apple-accent"
            />
            <input
              type="date"
              value={filterDateTo}
              onChange={(e) => { setFilterDateTo(e.target.value); setSkip(0); }}
              className="px-3 py-2 bg-apple-elevated border border-apple-border rounded-lg text-sm focus:outline-none focus:border-apple-accent"
            />
          </div>
          <div className="flex gap-2">
            <button
              onClick={fetchData}
              className="px-3 py-2 bg-apple-elevated border border-apple-border rounded-lg text-sm hover:bg-apple-surface transition-colors flex items-center gap-1"
            >
              <HiArrowPath className="w-4 h-4" /> Refresh
            </button>
            <button
              onClick={handleExport}
              className="px-3 py-2 bg-apple-elevated border border-apple-border rounded-lg text-sm hover:bg-apple-surface transition-colors flex items-center gap-1"
            >
              <HiArrowDownTray className="w-4 h-4" /> Export
            </button>
            <button
              onClick={() => setShowClearModal(true)}
              className="px-3 py-2 bg-red-500/10 text-red-400 border border-red-500/30 rounded-lg text-sm hover:bg-red-500/20 transition-colors flex items-center gap-1"
            >
              <HiTrash className="w-4 h-4" /> Clear
            </button>
          </div>
        </div>
      </div>

      {/* Bulk Actions */}
      {selectedTasks.size > 0 && (
        <div className="bg-apple-accent/10 border border-apple-accent/30 rounded-xl p-4 flex items-center justify-between">
          <span className="text-sm">{selectedTasks.size} task(s) selected</span>
          <div className="flex gap-2">
            <button
              onClick={handleRetrySelected}
              disabled={actionLoading}
              className="px-4 py-2 bg-yellow-500 text-black rounded-lg text-sm font-medium hover:bg-yellow-400 transition-colors disabled:opacity-50 flex items-center gap-1"
            >
              <HiArrowPath className="w-4 h-4" /> Retry Selected
            </button>
            <button
              onClick={handleDeleteSelected}
              disabled={actionLoading}
              className="px-4 py-2 bg-red-500 text-white rounded-lg text-sm font-medium hover:bg-red-600 transition-colors disabled:opacity-50 flex items-center gap-1"
            >
              <HiTrash className="w-4 h-4" /> Delete Selected
            </button>
          </div>
        </div>
      )}

      {/* Tasks Table */}
      <div className="bg-apple-surface rounded-xl border border-apple-border overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-apple-elevated border-b border-apple-border">
              <tr>
                <th className="p-3 text-left">
                  <input
                    type="checkbox"
                    checked={selectedTasks.size === tasks.length && tasks.length > 0}
                    onChange={handleSelectAll}
                    className="rounded border-apple-border"
                  />
                </th>
                <th className="p-3 text-left text-apple-secondary font-medium">Job ID</th>
                <th className="p-3 text-left text-apple-secondary font-medium">Type</th>
                <th className="p-3 text-left text-apple-secondary font-medium">Status</th>
                <th className="p-3 text-left text-apple-secondary font-medium">Retries</th>
                <th className="p-3 text-left text-apple-secondary font-medium">Error</th>
                <th className="p-3 text-left text-apple-secondary font-medium">Failed At</th>
                <th className="p-3 text-left text-apple-secondary font-medium">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-apple-border/50">
              {tasks.map((task) => (
                <tr key={task.id} className="hover:bg-apple-elevated/30">
                  <td className="p-3">
                    <input
                      type="checkbox"
                      checked={selectedTasks.has(task.id)}
                      onChange={() => handleSelectTask(task.id)}
                      className="rounded border-apple-border"
                    />
                  </td>
                  <td className="p-3 font-mono text-xs">{task.job_id.slice(0, 8)}...</td>
                  <td className="p-3">
                    <span className="px-2 py-1 bg-apple-elevated rounded text-xs">{task.task_type}</span>
                  </td>
                  <td className="p-3">
                    <span className={`px-2 py-1 rounded text-xs ${getStatusColor(task.status)}`}>
                      {task.status}
                    </span>
                  </td>
                  <td className="p-3">
                    <span className="text-apple-tertiary">{task.retry_count}/{task.max_retry}</span>
                  </td>
                  <td className="p-3 max-w-xs truncate text-red-400 text-xs">{task.error_message || '-'}</td>
                  <td className="p-3 text-apple-tertiary text-xs">{formatDate(task.failed_at)}</td>
                  <td className="p-3">
                    <button
                      onClick={() => handleViewDetail(task.id)}
                      className="p-1.5 hover:bg-apple-elevated rounded transition-colors"
                      title="View Details"
                    >
                      <HiEye className="w-4 h-4" />
                    </button>
                  </td>
                </tr>
              ))}
              {tasks.length === 0 && (
                <tr>
                  <td colSpan={8} className="p-8 text-center text-apple-tertiary">
                    <HiCheck className="w-12 h-12 mx-auto mb-2 text-green-400" />
                    No failed tasks in the Dead Letter Queue
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        {total > limit && (
          <div className="p-3 border-t border-apple-border flex items-center justify-between">
            <span className="text-sm text-apple-tertiary">
              Showing {skip + 1}-{Math.min(skip + limit, total)} of {total}
            </span>
            <div className="flex gap-2">
              <button
                onClick={() => setSkip(Math.max(0, skip - limit))}
                disabled={skip === 0}
                className="px-3 py-1.5 bg-apple-elevated rounded text-sm disabled:opacity-50"
              >
                Previous
              </button>
              <button
                onClick={() => setSkip(skip + limit)}
                disabled={skip + limit >= total}
                className="px-3 py-1.5 bg-apple-elevated rounded text-sm disabled:opacity-50"
              >
                Next
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Detail Modal */}
      {showDetailModal && selectedTask && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-apple-surface rounded-2xl border border-apple-border max-w-2xl w-full max-h-[80vh] overflow-hidden">
            <div className="p-4 border-b border-apple-border flex items-center justify-between">
              <h3 className="font-semibold">Task Details</h3>
              <button
                onClick={() => setShowDetailModal(false)}
                className="p-2 hover:bg-apple-elevated rounded-lg transition-colors"
              >
                <HiXMark className="w-5 h-5" />
              </button>
            </div>
            <div className="p-4 overflow-y-auto max-h-[60vh] space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-xs text-apple-tertiary mb-1">Job ID</p>
                  <p className="font-mono text-sm">{selectedTask.job_id}</p>
                </div>
                <div>
                  <p className="text-xs text-apple-tertiary mb-1">Task Type</p>
                  <p className="text-sm">{selectedTask.task_type}</p>
                </div>
                <div>
                  <p className="text-xs text-apple-tertiary mb-1">Status</p>
                  <span className={`px-2 py-1 rounded text-xs ${getStatusColor(selectedTask.status)}`}>
                    {selectedTask.status}
                  </span>
                </div>
                <div>
                  <p className="text-xs text-apple-tertiary mb-1">Retry Count</p>
                  <p className="text-sm">{selectedTask.retry_count} / {selectedTask.max_retry}</p>
                </div>
                <div>
                  <p className="text-xs text-apple-tertiary mb-1">Failed At</p>
                  <p className="text-sm">{formatDate(selectedTask.failed_at)}</p>
                </div>
                <div>
                  <p className="text-xs text-apple-tertiary mb-1">Last Retry</p>
                  <p className="text-sm">{formatDate(selectedTask.last_retry_at)}</p>
                </div>
              </div>

              <div>
                <p className="text-xs text-apple-tertiary mb-1">Error Type</p>
                <p className="text-sm text-red-400">{selectedTask.error_type || '-'}</p>
              </div>

              <div>
                <p className="text-xs text-apple-tertiary mb-1">Error Message</p>
                <p className="text-sm text-red-400 bg-red-400/5 p-3 rounded-lg">{selectedTask.error_message || '-'}</p>
              </div>

              {selectedTask.error_stack_trace && (
                <div>
                  <p className="text-xs text-apple-tertiary mb-1">Stack Trace</p>
                  <pre className="text-xs bg-apple-elevated p-3 rounded-lg overflow-x-auto whitespace-pre-wrap">
                    {selectedTask.error_stack_trace}
                  </pre>
                </div>
              )}

              <div>
                <p className="text-xs text-apple-tertiary mb-1">Original Payload</p>
                <pre className="text-xs bg-apple-elevated p-3 rounded-lg overflow-x-auto">
                  {JSON.stringify(selectedTask.original_payload, null, 2)}
                </pre>
              </div>

              {selectedTask.retry_history && selectedTask.retry_history.length > 0 && (
                <div>
                  <p className="text-xs text-apple-tertiary mb-1">Retry History</p>
                  <div className="space-y-2">
                    {selectedTask.retry_history.map((retry, idx) => (
                      <div key={idx} className="text-xs bg-apple-elevated p-2 rounded flex justify-between">
                        <span>Attempt {retry.attempt} - {retry.type}</span>
                        <span className="text-apple-tertiary">{formatDate(retry.requested_at)}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
            <div className="p-4 border-t border-apple-border flex justify-end gap-2">
              <button
                onClick={async () => {
                  await retryDLQTasks([selectedTask.id]);
                  setShowDetailModal(false);
                  fetchData();
                }}
                className="px-4 py-2 bg-yellow-500 text-black rounded-lg text-sm font-medium hover:bg-yellow-400 transition-colors"
              >
                Retry Task
              </button>
              <button
                onClick={() => setShowDetailModal(false)}
                className="px-4 py-2 bg-apple-elevated rounded-lg text-sm hover:bg-apple-border transition-colors"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Clear Modal */}
      {showClearModal && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-apple-surface rounded-2xl border border-apple-border max-w-md w-full">
            <div className="p-4 border-b border-apple-border">
              <h3 className="font-semibold text-red-400 flex items-center gap-2">
                <HiExclamationTriangle className="w-5 h-5" />
                Clear Dead Letter Queue
              </h3>
            </div>
            <div className="p-4 space-y-4">
              <p className="text-sm text-apple-secondary">
                This will archive and delete tasks from the DLQ. Use filters to target specific tasks.
              </p>
              <div>
                <label className="text-xs text-apple-tertiary mb-1 block">Filter by Status</label>
                <select
                  value={clearStatus}
                  onChange={(e) => setClearStatus(e.target.value)}
                  className="w-full px-3 py-2 bg-apple-elevated border border-apple-border rounded-lg text-sm focus:outline-none focus:border-apple-accent"
                >
                  <option value="">All Status</option>
                  <option value="failed">Failed</option>
                  <option value="pending_retry">Pending Retry</option>
                  <option value="resolved">Resolved</option>
                </select>
              </div>
              <div>
                <label className="text-xs text-apple-tertiary mb-1 block">Older than (days)</label>
                <input
                  type="number"
                  value={clearOlderThanDays}
                  onChange={(e) => setClearOlderThanDays(e.target.value)}
                  className="w-full px-3 py-2 bg-apple-elevated border border-apple-border rounded-lg text-sm focus:outline-none focus:border-apple-accent"
                  placeholder="Leave empty to clear all matching"
                />
              </div>
            </div>
            <div className="p-4 border-t border-apple-border flex justify-end gap-2">
              <button
                onClick={() => setShowClearModal(false)}
                className="px-4 py-2 bg-apple-elevated rounded-lg text-sm hover:bg-apple-border transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleClearDLQ}
                disabled={actionLoading}
                className="px-4 py-2 bg-red-500 text-white rounded-lg text-sm font-medium hover:bg-red-600 transition-colors disabled:opacity-50"
              >
                {actionLoading ? 'Clearing...' : 'Clear Tasks'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

// ===== Shared Components =====
const StatCard: React.FC<{ label: string; value: number }> = ({ label, value }) => (
  <div className="bg-apple-surface rounded-xl border border-apple-border p-3 lg:p-4">
    <p className="text-apple-tertiary text-[10px] lg:text-xs mb-1">{label}</p>
    <p className="text-xl lg:text-2xl font-bold">{value.toLocaleString()}</p>
  </div>
);

const LoadingState: React.FC = () => (
  <div className="flex items-center justify-center py-20">
    <div className="w-8 h-8 border-2 border-apple-accent border-t-transparent rounded-full animate-spin" />
  </div>
);

export default AdminDashboard;
