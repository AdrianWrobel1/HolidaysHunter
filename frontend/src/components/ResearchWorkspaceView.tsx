'use client';

import React, { useState, useEffect } from 'react';
import {
  DuplicateCheckResponse,
  MultiOfferCompareReport,
  OfferAnalysisReport,
  SessionResponse,
  WorkspaceItemResponse,
} from '@/types/api';
import {
  addWorkspaceItem,
  batchDeleteWorkspaceItems,
  batchMoveWorkspaceItems,
  compareWorkspaceOffers,
  createWorkspaceSession,
  deleteWorkspaceItem,
  fetchWorkspaceItems,
  fetchWorkspaceSessions,
  reanalyzeWorkspaceItem,
  updateWorkspaceItem,
} from '@/lib/api';
import { OfferAnalyzerView } from '@/components/OfferAnalyzerView';
import {
  FolderKanban,
  Plus,
  Pin,
  PinOff,
  Sparkles,
  Layers,
  CheckCircle2,
  AlertTriangle,
  Loader2,
  Tag as TagIcon,
  MessageSquare,
  RefreshCw,
  ExternalLink,
  Award,
  BarChart2,
  Zap,
  Check,
  X,
  FileText,
  Trash2,
  MoveRight,
  Download,
  Info,
  Maximize2,
  ArrowDownRight,
  ArrowUpRight,
  Clock,
} from 'lucide-react';

const TAG_OPTIONS = ['Favorite', 'Observe', 'Best Deal', 'High Priority', 'Rejected'];

export const ResearchWorkspaceView: React.FC = () => {
  // Sessions & Items State
  const [sessions, setSessions] = useState<SessionResponse[]>([]);
  const [activeSessionId, setActiveSessionId] = useState<string>('');
  const [items, setItems] = useState<WorkspaceItemResponse[]>([]);
  const [loadingSessions, setLoadingSessions] = useState(true);
  const [loadingItems, setLoadingItems] = useState(false);
  const [loadingAdd, setLoadingAdd] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Inputs
  const [inputUrl, setInputUrl] = useState('');
  const [batchModalOpen, setBatchModalOpen] = useState(false);
  const [batchUrlsText, setBatchUrlsText] = useState('');
  const [newSessionModalOpen, setNewSessionModalOpen] = useState(false);
  const [newSessionName, setNewSessionName] = useState('');
  const [newSessionDesc, setNewSessionDesc] = useState('');

  // Duplicate Modal State
  const [duplicateInfo, setDuplicateInfo] = useState<{
    info: DuplicateCheckResponse;
    url: string;
  } | null>(null);

  // Filtering & Selection
  const [filterTag, setFilterTag] = useState<string>('all');
  const [pinnedOnly, setPinnedOnly] = useState(false);
  const [selectedItemIds, setSelectedItemIds] = useState<string[]>([]);
  const [moveModalOpen, setMoveModalOpen] = useState(false);
  const [targetMoveSessionId, setTargetMoveSessionId] = useState<string>('');

  // Modals & Active Detail Views
  const [comparisonReport, setComparisonReport] = useState<MultiOfferCompareReport | null>(null);
  const [comparing, setComparing] = useState(false);
  const [fullDashboardReport, setFullDashboardReport] = useState<OfferAnalysisReport | null>(null);
  const [dealScoreModalItem, setDealScoreModalItem] = useState<WorkspaceItemResponse | null>(null);
  const [newNoteText, setNewNoteText] = useState<Record<string, string>>({});

  // Load Sessions on Mount
  useEffect(() => {
    loadSessions();
  }, []);

  // Load Items when Active Session Changes
  useEffect(() => {
    if (activeSessionId) {
      loadSessionItems(activeSessionId);
    }
  }, [activeSessionId]);

  const loadSessions = async () => {
    try {
      setLoadingSessions(true);
      const res = await fetchWorkspaceSessions();
      setSessions(res);
      if (res.length > 0 && !activeSessionId) {
        setActiveSessionId(res[0].id);
      }
    } catch (err: any) {
      console.error('Error loading workspace sessions:', err);
      setError('Nie udało się załadować sesji badawczych.');
    } finally {
      setLoadingSessions(false);
    }
  };

  const loadSessionItems = async (sessionId: string) => {
    try {
      setLoadingItems(true);
      setError(null);
      const res = await fetchWorkspaceItems(sessionId);
      setItems(res);
      setSelectedItemIds([]);
    } catch (err: any) {
      console.error('Error loading session items:', err);
      setError('Nie udało się załadować ofert z aktywnej sesji.');
    } finally {
      setLoadingItems(false);
    }
  };

  const handleCreateSession = async () => {
    if (!newSessionName.trim()) return;
    try {
      const created = await createWorkspaceSession(newSessionName.trim(), newSessionDesc.trim());
      setSessions((prev) => [created, ...prev]);
      setActiveSessionId(created.id);
      setNewSessionName('');
      setNewSessionDesc('');
      setNewSessionModalOpen(false);
    } catch (err: any) {
      console.error('Error creating session:', err);
      setError('Nie udało się utworzyć nowej sesji.');
    }
  };

  const handleAddSingleUrl = async (force = false) => {
    if (!inputUrl.trim() || !activeSessionId) return;
    setLoadingAdd(true);
    setError(null);
    try {
      const res = await addWorkspaceItem(activeSessionId, inputUrl.trim(), ['Observe'], [], force);
      if (!res.success && res.duplicate) {
        setDuplicateInfo({ info: res.duplicate, url: inputUrl.trim() });
        setLoadingAdd(false);
        return;
      }

      if (res.item) {
        setItems((prev) => [res.item!, ...prev]);
        setInputUrl('');
        setDuplicateInfo(null);
      }
    } catch (err: any) {
      console.error('Error adding offer item:', err);
      setError(err.message || 'Błąd podczas dodawania oferty do sesji.');
    } finally {
      setLoadingAdd(false);
    }
  };

  const handleBatchAddUrls = async () => {
    if (!batchUrlsText.trim() || !activeSessionId) return;
    const urls = batchUrlsText
      .split('\n')
      .map((u) => u.trim())
      .filter((u) => u.length > 0);

    if (urls.length === 0) return;

    setLoadingAdd(true);
    setError(null);
    setBatchModalOpen(false);

    try {
      for (const url of urls) {
        try {
          const res = await addWorkspaceItem(activeSessionId, url, ['Observe'], [], true);
          if (res.item) {
            setItems((prev) => [res.item!, ...prev]);
          }
        } catch (e) {
          console.warn('Could not add URL in batch:', url, e);
        }
      }
      setBatchUrlsText('');
    } finally {
      setLoadingAdd(false);
    }
  };

  const handleTogglePin = async (item: WorkspaceItemResponse) => {
    try {
      const updated = await updateWorkspaceItem(item.id, { is_pinned: !item.is_pinned });
      setItems((prev) => prev.map((i) => (i.id === item.id ? updated : i)));
    } catch (err) {
      console.error('Error toggling pin:', err);
    }
  };

  const handleToggleTag = async (item: WorkspaceItemResponse, tag: string) => {
    const currentTags = item.tags || [];
    const newTags = currentTags.includes(tag)
      ? currentTags.filter((t) => t !== tag)
      : [...currentTags, tag];

    try {
      const updated = await updateWorkspaceItem(item.id, { tags: newTags });
      setItems((prev) => prev.map((i) => (i.id === item.id ? updated : i)));
    } catch (err) {
      console.error('Error updating tags:', err);
    }
  };

  const handleAddNote = async (item: WorkspaceItemResponse) => {
    const text = (newNoteText[item.id] || '').trim();
    if (!text) return;
    const currentNotes = item.notes || [];
    const newNotes = [...currentNotes, text];

    try {
      const updated = await updateWorkspaceItem(item.id, { notes: newNotes });
      setItems((prev) => prev.map((i) => (i.id === item.id ? updated : i)));
      setNewNoteText((prev) => ({ ...prev, [item.id]: '' }));
    } catch (err) {
      console.error('Error adding note:', err);
    }
  };

  const handleReanalyze = async (item: WorkspaceItemResponse) => {
    try {
      const updated = await reanalyzeWorkspaceItem(item.id);
      setItems((prev) => prev.map((i) => (i.id === item.id ? updated : i)));
    } catch (err) {
      console.error('Error reanalyzing item:', err);
    }
  };

  const handleDeleteItem = async (itemId: string) => {
    try {
      await deleteWorkspaceItem(itemId);
      setItems((prev) => prev.filter((i) => i.id !== itemId));
      setSelectedItemIds((prev) => prev.filter((id) => id !== itemId));
    } catch (err) {
      console.error('Error deleting item:', err);
    }
  };

  const handleToggleSelectItem = (id: string) => {
    setSelectedItemIds((prev) =>
      prev.includes(id) ? prev.filter((i) => i !== id) : [...prev, id]
    );
  };

  const handleSelectAll = () => {
    if (selectedItemIds.length === filteredItems.length) {
      setSelectedItemIds([]);
    } else {
      setSelectedItemIds(filteredItems.map((i) => i.id));
    }
  };

  const handleRunComparison = async () => {
    if (selectedItemIds.length < 2 || selectedItemIds.length > 6) {
      setError('Porównanie wymaga wyboru od 2 do 6 ofert jednocześnie.');
      return;
    }
    setComparing(true);
    setError(null);
    try {
      const rep = await compareWorkspaceOffers(selectedItemIds);
      setComparisonReport(rep);
    } catch (err: any) {
      console.error('Error comparing offers:', err);
      setError(err.message || 'Błąd podczas porównywania ofert.');
    } finally {
      setComparing(false);
    }
  };

  const handleBatchRefresh = async () => {
    if (selectedItemIds.length === 0) return;
    setLoadingItems(true);
    try {
      for (const id of selectedItemIds) {
        await reanalyzeWorkspaceItem(id);
      }
      if (activeSessionId) {
        await loadSessionItems(activeSessionId);
      }
    } catch (err) {
      console.error('Error batch refreshing:', err);
    } finally {
      setLoadingItems(false);
    }
  };

  const handleBatchDelete = async () => {
    if (selectedItemIds.length === 0) return;
    if (!confirm(`Czy na pewno chcesz usunąć ${selectedItemIds.length} zaznaczonych ofert?`)) return;
    try {
      await batchDeleteWorkspaceItems(selectedItemIds);
      setItems((prev) => prev.filter((i) => !selectedItemIds.includes(i.id)));
      setSelectedItemIds([]);
    } catch (err) {
      console.error('Error batch deleting:', err);
    }
  };

  const handleBatchMove = async () => {
    if (selectedItemIds.length === 0 || !targetMoveSessionId) return;
    try {
      await batchMoveWorkspaceItems(selectedItemIds, targetMoveSessionId);
      setItems((prev) => prev.filter((i) => !selectedItemIds.includes(i.id)));
      setSelectedItemIds([]);
      setMoveModalOpen(false);
    } catch (err) {
      console.error('Error batch moving:', err);
    }
  };

  const handleExportSelected = () => {
    const selectedItems = items.filter((i) => selectedItemIds.includes(i.id));
    const dataStr = 'data:text/json;charset=utf-8,' + encodeURIComponent(JSON.stringify(selectedItems, null, 2));
    const downloadAnchor = document.createElement('a');
    downloadAnchor.setAttribute('href', dataStr);
    downloadAnchor.setAttribute('download', `workspace_export_${new Date().toISOString().slice(0, 10)}.json`);
    document.body.appendChild(downloadAnchor);
    downloadAnchor.click();
    downloadAnchor.remove();
  };

  // Filter items
  const filteredItems = items.filter((item) => {
    if (pinnedOnly && !item.is_pinned) return false;
    if (filterTag !== 'all' && (!item.tags || !item.tags.includes(filterTag))) return false;
    return true;
  });

  return (
    <div className="space-y-8 animate-fadeIn pb-24">
      {/* Header Banner */}
      <div className="relative overflow-hidden rounded-3xl bg-gradient-to-r from-slate-950 via-indigo-950 to-purple-950 border border-slate-800 p-8 shadow-2xl">
        <div className="absolute top-0 right-0 w-96 h-96 bg-indigo-500/10 rounded-full blur-3xl pointer-events-none" />
        <div className="relative z-10 max-w-3xl space-y-3">
          <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full text-xs font-bold bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
            <FolderKanban className="w-4 h-4 text-indigo-400" />
            <span>Persistent Research Environment</span>
          </div>
          <h2 className="text-3xl sm:text-4xl font-black text-white tracking-tight">
            Research Workspace
          </h2>
          <p className="text-sm text-slate-300 leading-relaxed">
            Środowisko pracy administratora: grupuj oferty w sesjach badawczych, przypinaj kluczowe okazje, dodawaj notatki i tagi, monitoruj delty zmian cen i uruchamiaj pełne analizy Offer Analyzer.
          </p>
        </div>
      </div>

      {/* Session Manager Bar */}
      <div className="p-6 rounded-3xl bg-slate-900/80 border border-slate-800 backdrop-blur-xl shadow-xl space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <FolderKanban className="w-5 h-5 text-indigo-400" />
            <span className="text-xs font-bold text-slate-300 uppercase tracking-wider">
              Aktywna Sesja Badawcza:
            </span>
            <select
              value={activeSessionId}
              onChange={(e) => setActiveSessionId(e.target.value)}
              className="px-4 py-2 rounded-xl bg-slate-950 border border-slate-800 text-sm font-bold text-white focus:outline-none focus:border-indigo-500 cursor-pointer"
            >
              {sessions.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.name} ({s.items_count} ofert)
                </option>
              ))}
            </select>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={() => setNewSessionModalOpen(true)}
              className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-white text-xs font-bold flex items-center gap-2 transition-all border border-slate-700/60"
            >
              <Plus className="w-4 h-4" />
              <span>Nowa Sesja</span>
            </button>

            <button
              onClick={() => setBatchModalOpen(true)}
              className="px-4 py-2 rounded-xl bg-indigo-600/80 hover:bg-indigo-600 text-white text-xs font-bold flex items-center gap-2 transition-all shadow-md shadow-indigo-600/20"
            >
              <FileText className="w-4 h-4" />
              <span>Wklej wiele URL-i</span>
            </button>
          </div>
        </div>

        {/* URL Input */}
        <div className="flex flex-col sm:flex-row items-center gap-3 pt-2">
          <input
            type="text"
            value={inputUrl}
            onChange={(e) => setInputUrl(e.target.value)}
            placeholder="Dodaj ofertę do sesji: https://www.itaka.pl/wczasy/..."
            className="flex-1 w-full px-4 py-3 rounded-2xl bg-slate-950/80 border border-slate-800 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500 transition-all"
          />

          <button
            onClick={() => handleAddSingleUrl(false)}
            disabled={loadingAdd}
            className="w-full sm:w-auto px-6 py-3 rounded-2xl bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500 text-white text-xs font-bold shadow-lg shadow-indigo-600/30 flex items-center justify-center gap-2 shrink-0 disabled:opacity-50 transition-all"
          >
            {loadingAdd ? <Loader2 className="w-4 h-4 animate-spin" /> : <Plus className="w-4 h-4" />}
            <span>Dodaj do Sesji</span>
          </button>
        </div>

        {error && (
          <div className="p-4 rounded-2xl bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs flex items-center gap-3 animate-fadeIn">
            <AlertTriangle className="w-5 h-5 shrink-0 text-rose-400" />
            <span>{error}</span>
          </div>
        )}
      </div>

      {/* Toolbar & Filters */}
      <div className="flex flex-wrap items-center justify-between gap-4 p-4 rounded-2xl bg-slate-900/60 border border-slate-800 text-xs font-medium">
        <div className="flex items-center gap-2 flex-wrap">
          <button
            onClick={handleSelectAll}
            className="px-3 py-1.5 rounded-xl border border-slate-700/60 bg-slate-800/40 text-slate-300 hover:text-white font-bold transition-all"
          >
            {selectedItemIds.length === filteredItems.length && filteredItems.length > 0
              ? 'Odznacz wszystkie'
              : `Zaznacz wszystkie (${filteredItems.length})`}
          </button>

          <span className="h-4 w-px bg-slate-800 mx-1" />

          <button
            onClick={() => setPinnedOnly(!pinnedOnly)}
            className={`px-3 py-1.5 rounded-xl border flex items-center gap-1.5 transition-all ${
              pinnedOnly
                ? 'bg-amber-500/20 border-amber-500/40 text-amber-300 font-bold'
                : 'bg-slate-800/40 border-slate-700/50 text-slate-400 hover:text-white'
            }`}
          >
            <Pin className="w-3.5 h-3.5" />
            <span>Przypięte ({items.filter((i) => i.is_pinned).length})</span>
          </button>

          <span className="h-4 w-px bg-slate-800 mx-1" />

          <button
            onClick={() => setFilterTag('all')}
            className={`px-3 py-1.5 rounded-xl border transition-all ${
              filterTag === 'all'
                ? 'bg-indigo-600 text-white font-bold border-indigo-500'
                : 'bg-slate-800/40 border-slate-700/50 text-slate-400 hover:text-white'
            }`}
          >
            Wszystkie ({items.length})
          </button>

          {TAG_OPTIONS.map((tag) => (
            <button
              key={tag}
              onClick={() => setFilterTag(tag)}
              className={`px-3 py-1.5 rounded-xl border transition-all ${
                filterTag === tag
                  ? 'bg-indigo-600 text-white font-bold border-indigo-500'
                  : 'bg-slate-800/40 border-slate-700/50 text-slate-400 hover:text-white'
              }`}
            >
              {tag}
            </button>
          ))}
        </div>
      </div>

      {/* Side-by-Side Comparison Modal View */}
      {comparisonReport && (
        <div className="p-6 rounded-3xl bg-slate-900/95 border border-emerald-500/40 backdrop-blur-xl shadow-2xl space-y-6 animate-fadeIn relative">
          <button
            onClick={() => setComparisonReport(null)}
            className="absolute top-4 right-4 p-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-white transition-colors"
          >
            <X className="w-5 h-5" />
          </button>

          <div className="space-y-2">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-bold bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
              <Zap className="w-3.5 h-3.5" />
              <span>Side-by-Side Comparison Engine</span>
            </div>
            <h3 className="text-2xl font-black text-white">Porównanie Ofert ({comparisonReport.items.length})</h3>
            <p className="text-xs text-slate-300 leading-relaxed">{comparisonReport.upgrade_recommendation}</p>
          </div>

          {/* Comparison Badges Row */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <div className="p-3 rounded-2xl bg-indigo-500/10 border border-indigo-500/30 text-center space-y-0.5">
              <span className="text-[10px] font-bold uppercase text-indigo-400">Najlepsza Oferta</span>
              <p className="text-xs font-black text-white">
                Oferta #{comparisonReport.best_overall_index + 1}
              </p>
            </div>
            <div className="p-3 rounded-2xl bg-emerald-500/10 border border-emerald-500/30 text-center space-y-0.5">
              <span className="text-[10px] font-bold uppercase text-emerald-400">Stosunek Cena/Jakość</span>
              <p className="text-xs font-black text-white">
                Oferta #{comparisonReport.best_value_index + 1}
              </p>
            </div>
            <div className="p-3 rounded-2xl bg-amber-500/10 border border-amber-500/30 text-center space-y-0.5">
              <span className="text-[10px] font-bold uppercase text-amber-400">Najtańsza</span>
              <p className="text-xs font-black text-white">
                Oferta #{comparisonReport.cheapest_index + 1}
              </p>
            </div>
            <div className="p-3 rounded-2xl bg-purple-500/10 border border-purple-500/30 text-center space-y-0.5">
              <span className="text-[10px] font-bold uppercase text-purple-400">Najwyższy Standard</span>
              <p className="text-xs font-black text-white">
                Oferta #{comparisonReport.highest_standard_index + 1}
              </p>
            </div>
          </div>

          {/* Side-by-Side Matrix Table */}
          <div className="overflow-x-auto">
            <table className="w-full border-collapse text-xs text-left">
              <thead>
                <tr className="border-b border-slate-800">
                  <th className="py-3 px-4 text-slate-400 uppercase text-[10px]">Metryka Porównania</th>
                  {comparisonReport.items.map((item, idx) => (
                    <th key={item.id} className="py-3 px-4 text-slate-200 font-bold">
                      Oferta #{idx + 1} ({item.latest_report?.target_offer.provider.toUpperCase()})
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {Object.entries(comparisonReport.matrix).map(([rowKey, rowData]) => (
                  <tr key={rowKey} className="hover:bg-slate-800/30 transition-colors">
                    <td className="py-3 px-4 font-semibold text-slate-400">{rowData.label}</td>
                    {rowData.values.map((val, colIdx) => {
                      const isBest = rowData.best_indices.includes(colIdx);
                      return (
                        <td
                          key={colIdx}
                          className={`py-3 px-4 transition-colors ${
                            isBest
                              ? 'bg-emerald-500/10 font-bold text-emerald-300 border-l-2 border-emerald-500'
                              : 'text-slate-200'
                          }`}
                        >
                          <div className="flex items-center gap-1.5">
                            {isBest && <Check className="w-3.5 h-3.5 text-emerald-400 shrink-0" />}
                            <span>{String(val)}</span>
                          </div>
                        </td>
                      );
                    })}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Items Loading State */}
      {loadingItems ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {[...Array(6)].map((_, i) => (
            <div key={i} className="h-72 rounded-3xl bg-slate-900/60 border border-slate-800 animate-pulse" />
          ))}
        </div>
      ) : filteredItems.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredItems.map((item) => {
            const report = item.latest_report;
            const target = report?.target_offer;
            const isSelected = selectedItemIds.includes(item.id);

            // Extract price and score deltas if present
            const priceDelta = item.change_detection?.deltas.find((d) => d.metric.includes('Cena'));
            const scoreDelta = item.change_detection?.deltas.find((d) => d.metric.includes('Deal Score'));

            return (
              <div
                key={item.id}
                className={`p-6 rounded-3xl bg-slate-900/80 border transition-all duration-200 space-y-4 relative backdrop-blur-xl hover:scale-[1.01] hover:shadow-xl ${
                  item.is_pinned
                    ? 'border-amber-500/50 shadow-lg shadow-amber-500/10'
                    : isSelected
                    ? 'border-indigo-500 shadow-lg shadow-indigo-500/20'
                    : 'border-slate-800 hover:border-indigo-500/60'
                }`}
              >
                {/* Header Row: Checkbox, Provider Badge, Pin & Delete Toggle */}
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <input
                      type="checkbox"
                      checked={isSelected}
                      onChange={() => handleToggleSelectItem(item.id)}
                      className="w-4 h-4 rounded border-slate-700 bg-slate-950 text-indigo-600 focus:ring-indigo-500 cursor-pointer"
                    />
                    <span className="text-[10px] font-black uppercase tracking-wider px-2.5 py-1 rounded-full bg-indigo-500/10 text-indigo-300 border border-indigo-500/30">
                      {target?.provider || 'Oferta'}
                    </span>
                  </div>

                  <div className="flex items-center gap-1.5">
                    <button
                      onClick={() => handleTogglePin(item)}
                      className={`p-1.5 rounded-xl border text-xs transition-colors ${
                        item.is_pinned
                          ? 'bg-amber-500/20 border-amber-500/40 text-amber-300'
                          : 'bg-slate-800/40 border-slate-700 text-slate-500 hover:text-slate-300'
                      }`}
                      title={item.is_pinned ? 'Odpnij ofertę' : 'Przypnij ofertę'}
                    >
                      {item.is_pinned ? <Pin className="w-3.5 h-3.5" /> : <PinOff className="w-3.5 h-3.5" />}
                    </button>

                    <button
                      onClick={() => handleDeleteItem(item.id)}
                      className="p-1.5 rounded-xl border border-slate-800 bg-slate-900 text-slate-500 hover:text-rose-400 hover:border-rose-500/40 transition-colors"
                      title="Usuń ofertę"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </div>

                {/* Offer Details Card Body (Clickable to open Full Dashboard) */}
                <div
                  onClick={() => report && setFullDashboardReport(report)}
                  className="space-y-2.5 cursor-pointer group"
                >
                  <h4 className="text-base font-black text-white group-hover:text-indigo-300 transition-colors leading-snug line-clamp-2">
                    {target?.hotel_name || 'Nowa oferta w sesji'}
                  </h4>

                  <p className="text-xs text-slate-400 flex items-center gap-1">
                    <span>{target?.country}</span>
                    {target?.region && <span>• {target.region}</span>}
                    <span>({target?.duration_nights || 7} dni)</span>
                  </p>

                  <div className="flex items-baseline justify-between pt-1">
                    <div className="flex items-baseline gap-2">
                      <span className="text-2xl font-black text-emerald-400">
                        {target?.price_per_person || 0} PLN
                      </span>
                      <span className="text-[10px] text-slate-400">/os.</span>
                    </div>

                    {/* Deal Score Badge (Clickable to open component breakdown modal) */}
                    {report && (
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          setDealScoreModalItem(item);
                        }}
                        className="flex items-center gap-1.5 px-3 py-1 rounded-full bg-slate-950 border border-amber-500/40 hover:border-amber-400 text-xs font-extrabold text-amber-400 transition-all hover:scale-105 shadow-md"
                        title="Kliknij, aby zobaczyć pełne rozbicie komponentów scoringu"
                      >
                        <Award className="w-3.5 h-3.5 text-amber-400" />
                        <span>Score: {report.deal_score.total_score}</span>
                      </button>
                    )}
                  </div>
                </div>

                {/* Prominent Delta Change Indicators */}
                {(priceDelta || scoreDelta || item.history_count > 1) && (
                  <div className="flex items-center gap-2 pt-1 flex-wrap text-[11px]">
                    {priceDelta && (
                      <span
                        className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full font-extrabold ${
                          priceDelta.is_positive
                            ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/30'
                            : 'bg-rose-500/10 text-rose-400 border border-rose-500/30'
                        }`}
                      >
                        {priceDelta.is_positive ? <ArrowDownRight className="w-3 h-3" /> : <ArrowUpRight className="w-3 h-3" />}
                        <span>Cena: {priceDelta.diff_text}</span>
                      </span>
                    )}

                    {scoreDelta && (
                      <span
                        className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full font-extrabold ${
                          scoreDelta.is_positive
                            ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/30'
                            : 'bg-rose-500/10 text-rose-400 border border-rose-500/30'
                        }`}
                      >
                        <Zap className="w-3 h-3" />
                        <span>Score: {scoreDelta.diff_text}</span>
                      </span>
                    )}

                    <span className="text-[10px] text-slate-500 flex items-center gap-1 ml-auto">
                      <Clock className="w-3 h-3" />
                      <span>{item.updated_at ? new Date(item.updated_at).toLocaleDateString() : 'Dzisiaj'}</span>
                    </span>
                  </div>
                )}

                {/* High Contrast Tags */}
                <div className="space-y-1.5 pt-1">
                  <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider flex items-center gap-1">
                    <TagIcon className="w-3 h-3 text-indigo-400" />
                    Tagi:
                  </span>
                  <div className="flex flex-wrap gap-1.5">
                    {TAG_OPTIONS.map((tag) => {
                      const active = (item.tags || []).includes(tag);
                      return (
                        <button
                          key={tag}
                          onClick={() => handleToggleTag(item, tag)}
                          className={`px-2.5 py-1 rounded-lg text-xs font-bold transition-all ${
                            active
                              ? 'bg-indigo-600 text-white shadow-md shadow-indigo-600/30'
                              : 'bg-slate-800/60 text-slate-400 hover:text-slate-200 border border-slate-700/50'
                          }`}
                        >
                          {tag}
                        </button>
                      );
                    })}
                  </div>
                </div>

                {/* Admin Notes Section */}
                <div className="space-y-2 pt-1 border-t border-slate-800/60">
                  <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider flex items-center gap-1">
                    <MessageSquare className="w-3 h-3 text-indigo-400" />
                    Notatki Administratora ({item.notes?.length || 0}):
                  </span>

                  {item.notes && item.notes.length > 0 && (
                    <ul className="space-y-1 max-h-24 overflow-y-auto pr-1 custom-scrollbar">
                      {item.notes.map((note, nIdx) => (
                        <li key={nIdx} className="text-[11px] text-slate-300 p-1.5 rounded bg-slate-950/60 border border-slate-800">
                          {note}
                        </li>
                      ))}
                    </ul>
                  )}

                  <div className="flex items-center gap-1.5">
                    <input
                      type="text"
                      value={newNoteText[item.id] || ''}
                      onChange={(e) => setNewNoteText({ ...newNoteText, [item.id]: e.target.value })}
                      placeholder="Dodaj notatkę..."
                      className="flex-1 px-2.5 py-1.5 rounded-xl bg-slate-950 border border-slate-800 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500"
                    />
                    <button
                      onClick={() => handleAddNote(item)}
                      className="px-3 py-1.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-bold shrink-0"
                    >
                      +
                    </button>
                  </div>
                </div>

                {/* Bottom Actions */}
                <div className="flex items-center justify-between pt-2 border-t border-slate-800/60 text-xs">
                  <button
                    onClick={() => report && setFullDashboardReport(report)}
                    className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-indigo-300 font-bold transition-all"
                  >
                    <Maximize2 className="w-3.5 h-3.5" />
                    <span>Pełny Dashboard</span>
                  </button>

                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => handleReanalyze(item)}
                      className="flex items-center gap-1 text-slate-400 hover:text-white font-medium transition-colors"
                      title="Ponowna analiza i zapis w historii"
                    >
                      <RefreshCw className="w-3.5 h-3.5" />
                      <span>({item.history_count})</span>
                    </button>

                    {target?.offer_url && (
                      <a
                        href={target.offer_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="flex items-center gap-1 text-indigo-400 hover:text-indigo-300 font-bold"
                        title="Otwórz bezpośredni link do oferty"
                      >
                        <ExternalLink className="w-3.5 h-3.5" />
                      </a>
                    )}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      ) : (
        <div className="p-12 text-center rounded-3xl bg-slate-900/40 border border-slate-800 space-y-3">
          <FolderKanban className="w-12 h-12 text-slate-600 mx-auto stroke-[1.5]" />
          <h3 className="text-base font-bold text-slate-200">Brak ofert w tej sesji badawczej</h3>
          <p className="text-xs text-slate-400 max-w-md mx-auto">
            Wklej link oferty turystycznej powyżej lub wklej zestaw linków masowo.
          </p>
        </div>
      )}

      {/* Floating Multi-Select Action Bar */}
      {selectedItemIds.length > 0 && (
        <div className="fixed bottom-6 left-1/2 -translate-x-1/2 z-40 px-6 py-3.5 rounded-full bg-slate-900/90 border border-indigo-500/50 backdrop-blur-xl shadow-2xl flex items-center gap-4 animate-slideUp text-xs">
          <span className="font-black text-white flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping" />
            Zaznaczono {selectedItemIds.length} ofert
          </span>

          <span className="h-4 w-px bg-slate-800" />

          <button
            onClick={handleRunComparison}
            disabled={selectedItemIds.length < 2 || selectedItemIds.length > 6}
            className="px-4 py-2 rounded-full bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 text-white font-bold flex items-center gap-1.5 shadow-lg shadow-emerald-600/30 transition-all"
          >
            <BarChart2 className="w-4 h-4" />
            <span>Porównaj (2-6)</span>
          </button>

          <button
            onClick={handleBatchRefresh}
            className="px-4 py-2 rounded-full bg-slate-800 hover:bg-slate-700 text-slate-200 font-bold flex items-center gap-1.5 transition-all"
          >
            <RefreshCw className="w-4 h-4" />
            <span>Odśwież</span>
          </button>

          <button
            onClick={() => setMoveModalOpen(true)}
            className="px-4 py-2 rounded-full bg-slate-800 hover:bg-slate-700 text-slate-200 font-bold flex items-center gap-1.5 transition-all"
          >
            <MoveRight className="w-4 h-4" />
            <span>Przenieś</span>
          </button>

          <button
            onClick={handleExportSelected}
            className="px-4 py-2 rounded-full bg-slate-800 hover:bg-slate-700 text-slate-200 font-bold flex items-center gap-1.5 transition-all"
          >
            <Download className="w-4 h-4" />
            <span>Eksportuj</span>
          </button>

          <button
            onClick={handleBatchDelete}
            className="px-4 py-2 rounded-full bg-rose-500/20 hover:bg-rose-500/30 text-rose-300 font-bold flex items-center gap-1.5 transition-all border border-rose-500/30"
          >
            <Trash2 className="w-4 h-4" />
            <span>Usuń</span>
          </button>

          <button
            onClick={() => setSelectedItemIds([])}
            className="p-1.5 rounded-full hover:bg-slate-800 text-slate-400 hover:text-white"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* Duplicate Detection Dialog */}
      {duplicateInfo && (
        <div className="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-md flex items-center justify-center p-4">
          <div className="w-full max-w-md rounded-3xl bg-slate-900 border border-amber-500/50 p-6 space-y-4 shadow-2xl animate-fadeIn">
            <div className="flex items-center gap-3 text-amber-400">
              <AlertTriangle className="w-6 h-6 shrink-0" />
              <h3 className="text-lg font-black text-white">Wykryto Duplikat Oferty!</h3>
            </div>

            <p className="text-xs text-slate-300 leading-relaxed">
              Ta oferta turystyczna istnieje już w systemie w sesji{' '}
              <strong className="text-amber-300">"{duplicateInfo.info.existing_session_name}"</strong>.
            </p>

            <div className="flex flex-col gap-2 pt-2 text-xs">
              <button
                onClick={() => {
                  if (duplicateInfo.info.existing_session_id) {
                    setActiveSessionId(duplicateInfo.info.existing_session_id);
                  }
                  setDuplicateInfo(null);
                  setInputUrl('');
                }}
                className="w-full px-4 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-bold shadow-lg shadow-indigo-600/30"
              >
                Otwórz Istniejącą Ofertę
              </button>

              <button
                onClick={() => handleAddSingleUrl(true)}
                className="w-full px-4 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 font-bold border border-slate-700"
              >
                Dodaj Mimo To Jako Duplikat
              </button>

              <button
                onClick={() => setDuplicateInfo(null)}
                className="w-full px-4 py-2 rounded-xl bg-transparent hover:bg-slate-800/50 text-slate-400 text-center"
              >
                Anuluj
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Deal Score Component Breakdown Modal */}
      {dealScoreModalItem && dealScoreModalItem.latest_report && (
        <div className="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-md flex items-center justify-center p-4">
          <div className="w-full max-w-xl rounded-3xl bg-slate-900 border border-slate-800 p-6 space-y-6 shadow-2xl animate-fadeIn relative">
            <button
              onClick={() => setDealScoreModalItem(null)}
              className="absolute top-4 right-4 p-2 rounded-xl bg-slate-800 text-slate-400 hover:text-white"
            >
              <X className="w-5 h-5" />
            </button>

            <div className="space-y-1">
              <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-bold bg-amber-500/20 text-amber-300 border border-amber-500/30">
                <Award className="w-3.5 h-3.5" />
                <span>Deal Score Component Aggregator</span>
              </div>
              <h3 className="text-2xl font-black text-white">
                Rozbicie Wskaźnika Deal Score ({dealScoreModalItem.latest_report.deal_score.total_score}/100)
              </h3>
              <p className="text-xs text-slate-400 leading-relaxed">
                {dealScoreModalItem.latest_report.deal_score.summary}
              </p>
            </div>

            <div className="space-y-3">
              {dealScoreModalItem.latest_report.deal_score.components.map((c, idx) => (
                <div key={idx} className="p-3.5 rounded-2xl bg-slate-950 border border-slate-800 space-y-1.5">
                  <div className="flex items-center justify-between text-xs">
                    <span className="font-bold text-slate-200">{c.name}</span>
                    <span className="font-extrabold text-amber-400">
                      {Math.round(c.score)}/100 (Waga: {Math.round(c.weight * 100)}%)
                    </span>
                  </div>
                  <div className="w-full h-2 rounded-full bg-slate-800 overflow-hidden">
                    <div
                      className="h-full bg-gradient-to-r from-amber-500 to-emerald-500 rounded-full"
                      style={{ width: `${Math.min(100, Math.max(0, c.score))}%` }}
                    />
                  </div>
                  {c.explanation && (
                    <p className="text-[11px] text-slate-400 leading-normal">{c.explanation}</p>
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Full Offer Analyzer Dashboard Modal */}
      {fullDashboardReport && (
        <div className="fixed inset-0 z-50 bg-slate-950/90 backdrop-blur-md overflow-y-auto p-4 sm:p-8">
          <div className="max-w-6xl mx-auto space-y-6 relative">
            <button
              onClick={() => setFullDashboardReport(null)}
              className="fixed top-6 right-6 z-50 p-3 rounded-2xl bg-slate-900 border border-slate-700 text-white font-bold hover:bg-slate-800 shadow-2xl flex items-center gap-2"
            >
              <X className="w-5 h-5" />
              <span>Zamknij Analyzer</span>
            </button>

            <OfferAnalyzerView initialReport={fullDashboardReport} />
          </div>
        </div>
      )}

      {/* Move Session Modal */}
      {moveModalOpen && (
        <div className="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-md flex items-center justify-center p-4">
          <div className="w-full max-w-sm rounded-3xl bg-slate-900 border border-slate-800 p-6 space-y-4 shadow-2xl animate-fadeIn">
            <h3 className="text-lg font-bold text-white">Przenieś Oferty Do Innej Sesji</h3>
            <select
              value={targetMoveSessionId}
              onChange={(e) => setTargetMoveSessionId(e.target.value)}
              className="w-full p-3 rounded-xl bg-slate-950 border border-slate-800 text-xs text-white"
            >
              <option value="">Wybierz sesję docelową...</option>
              {sessions
                .filter((s) => s.id !== activeSessionId)
                .map((s) => (
                  <option key={s.id} value={s.id}>
                    {s.name}
                  </option>
                ))}
            </select>
            <div className="flex justify-end gap-3 pt-2">
              <button onClick={() => setMoveModalOpen(false)} className="px-4 py-2 rounded-xl bg-slate-800 text-slate-300 text-xs">
                Anuluj
              </button>
              <button onClick={handleBatchMove} className="px-4 py-2 rounded-xl bg-indigo-600 text-white text-xs font-bold">
                Przenieś
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Batch Paste URLs Modal */}
      {batchModalOpen && (
        <div className="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-md flex items-center justify-center p-4">
          <div className="w-full max-w-lg rounded-3xl bg-slate-900 border border-slate-800 p-6 space-y-4 shadow-2xl animate-fadeIn">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-bold text-white flex items-center gap-2">
                <FileText className="w-5 h-5 text-indigo-400" />
                Wklej Wiele URL-i (Po Jednym w Linii)
              </h3>
              <button onClick={() => setBatchModalOpen(false)} className="text-slate-400 hover:text-white">
                <X className="w-5 h-5" />
              </button>
            </div>

            <textarea
              rows={6}
              value={batchUrlsText}
              onChange={(e) => setBatchUrlsText(e.target.value)}
              placeholder="https://www.itaka.pl/wczasy/...\nhttps://www.tui.pl/wypoczynek/...\nhttps://r.pl/szukaj/..."
              className="w-full p-4 rounded-2xl bg-slate-950 border border-slate-800 text-xs text-white font-mono placeholder-slate-600 focus:outline-none focus:border-indigo-500"
            />

            <div className="flex justify-end gap-3 pt-2">
              <button
                onClick={() => setBatchModalOpen(false)}
                className="px-4 py-2 rounded-xl bg-slate-800 text-slate-300 text-xs font-semibold"
              >
                Anuluj
              </button>
              <button
                onClick={handleBatchAddUrls}
                className="px-5 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-bold shadow-lg shadow-indigo-600/30"
              >
                Dodaj i Przeanalizuj Wszystkie
              </button>
            </div>
          </div>
        </div>
      )}

      {/* New Session Modal */}
      {newSessionModalOpen && (
        <div className="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-md flex items-center justify-center p-4">
          <div className="w-full max-w-md rounded-3xl bg-slate-900 border border-slate-800 p-6 space-y-4 shadow-2xl animate-fadeIn">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-bold text-white flex items-center gap-2">
                <FolderKanban className="w-5 h-5 text-indigo-400" />
                Utwórz Nową Sesję Badawczą
              </h3>
              <button onClick={() => setNewSessionModalOpen(false)} className="text-slate-400 hover:text-white">
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="space-y-3 text-xs">
              <div>
                <label className="block text-slate-400 font-semibold mb-1">Nazwa Sesji</label>
                <input
                  type="text"
                  value={newSessionName}
                  onChange={(e) => setNewSessionName(e.target.value)}
                  placeholder="np. Turcja Last Minute 2026"
                  className="w-full px-3.5 py-2.5 rounded-xl bg-slate-950 border border-slate-800 text-white text-xs focus:outline-none focus:border-indigo-500"
                />
              </div>

              <div>
                <label className="block text-slate-400 font-semibold mb-1">Opis (Opcjonalnie)</label>
                <input
                  type="text"
                  value={newSessionDesc}
                  onChange={(e) => setNewSessionDesc(e.target.value)}
                  placeholder="np. Analiza ofert All Inclusive 5★ dla 2 osób"
                  className="w-full px-3.5 py-2.5 rounded-xl bg-slate-950 border border-slate-800 text-white text-xs focus:outline-none focus:border-indigo-500"
                />
              </div>
            </div>

            <div className="flex justify-end gap-3 pt-2">
              <button
                onClick={() => setNewSessionModalOpen(false)}
                className="px-4 py-2 rounded-xl bg-slate-800 text-slate-300 text-xs font-semibold"
              >
                Anuluj
              </button>
              <button
                onClick={handleCreateSession}
                className="px-5 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-bold shadow-lg shadow-indigo-600/30"
              >
                Utwórz Sesję
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
