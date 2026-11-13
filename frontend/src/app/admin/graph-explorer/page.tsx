"use client";

import { useEffect, useState } from "react";
import {
  Network,
  Search,
  ZoomIn,
  ZoomOut,
  Maximize2,
  Info,
  Sparkles,
  X,
  Database,
  RefreshCw,
  Sliders,
  Check,
} from "lucide-react";
import GraphCanvas from "@/components/visualizers/GraphCanvas";
import { GraphNode, GraphLink } from "@/types";
import apiClient, { isUnauthorizedError } from "@/lib/api";

const NODE_TYPE_COLORS: Record<string, { dot: string; badge: string; text: string }> = {
  Domain: { dot: "bg-blue-500", badge: "bg-blue-100 text-blue-700", text: "Lĩnh vực" },
  Expertise: { dot: "bg-emerald-500", badge: "bg-emerald-100 text-emerald-700", text: "Chuyên môn" },
  Skill: { dot: "bg-amber-500", badge: "bg-amber-100 text-amber-700", text: "Kỹ năng" },
  JobPosition: { dot: "bg-violet-500", badge: "bg-violet-100 text-violet-700", text: "Vị trí việc làm" },
  Candidate: { dot: "bg-rose-500", badge: "bg-rose-100 text-rose-700", text: "Ứng viên" },
};

export default function GraphExplorerPage() {
  const [nodes, setNodes] = useState<GraphNode[]>([]);
  const [links, setLinks] = useState<GraphLink[]>([]);
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null);
  const [searchTerm, setSearchTerm] = useState("");
  const [queryType, setQueryType] = useState<"job" | "cv">("job");
  const [selectedEntityIds, setSelectedEntityIds] = useState<number[]>([1]);
  const [entityOptions, setEntityOptions] = useState<Array<{
    id: number;
    label: string;
    searchText: string;
  }>>([]);
  const [entitySearch, setEntitySearch] = useState("");
  const [selectorOpen, setSelectorOpen] = useState(false);
  const [loadingGraph, setLoadingGraph] = useState(false);
  const [queryNote, setQueryNote] = useState<string | null>(null);
  const [maxNodes, setMaxNodes] = useState(50);

  const [visibleTypes, setVisibleTypes] = useState<Set<string>>(
    new Set(["Domain", "Expertise", "Skill", "JobPosition", "Candidate"])
  );

  useEffect(() => {
    const loadEntityOptions = async () => {
      try {
        const endpoint = queryType === "job" ? "/jd/available" : "/profile/available";
        const response = await apiClient.get(endpoint);
        const items = response.data?.data || [];
        setEntityOptions(items.map((item: {
          id: number;
          title?: string;
          domain?: string;
          expertise?: string;
          skills?: string[];
        }) => ({
          id: item.id,
          label: item.title || `${queryType === "job" ? "Vị trí" : "CV"} #${item.id}`,
          searchText: [item.title, item.domain, item.expertise, ...(item.skills || [])]
            .filter(Boolean)
            .join(" ")
            .toLowerCase(),
        })));
        setSelectedEntityIds((current) => current.filter((id) =>
          items.some((item: { id: number }) => item.id === id),
        ).slice(0, 10));
      } catch (error: unknown) {
        setEntityOptions([]);
        if (!isUnauthorizedError(error)) {
          setSelectedEntityIds([]);
          setQueryNote("Không thể tải danh sách dữ liệu. Vui lòng thử lại sau.");
        }
      }
    };
    void loadEntityOptions();
  }, [queryType]);

  useEffect(() => {
    const handleEscape = (event: KeyboardEvent) => {
      if (event.key === "Escape") setSelectorOpen(false);
    };
    document.addEventListener("keydown", handleEscape);
    return () => document.removeEventListener("keydown", handleEscape);
  }, []);

  const toggleType = (type: string) => {
    setVisibleTypes((prev) => {
      const next = new Set(prev);
      if (next.has(type)) next.delete(type);
      else next.add(type);
      return next;
    });
  };

  const handleFetchGraph = async () => {
    setLoadingGraph(true);
    setQueryNote(null);

    try {
      const ids = selectedEntityIds.slice(0, 10);
      if (ids.length === 0) {
        setQueryNote("Hãy chọn ít nhất một mục trong danh sách.");
        setLoadingGraph(false);
        return;
      }

      if (queryType === "job") {
        const responses = await Promise.all(
          ids.map((id) => apiClient.get(`/graph/jobs/${id}/skills`)),
        );
        const nextNodes: GraphNode[] = [];
        const nextLinks: GraphLink[] = [];
        responses.forEach((res, index) => {
          const id = ids[index];
          const skills = res.data?.data || [];
          const jobNodeId = `job_${id}`;
          nextNodes.push({ id: jobNodeId, label: `Job #${id}`, type: "JobPosition" });
          skills.forEach((skill: { name: string }) => {
            const skillNodeId = `skill_${skill.name}`;
            if (!nextNodes.some((node) => node.id === skillNodeId)) {
              nextNodes.push({ id: skillNodeId, label: skill.name, type: "Skill" });
            }
            nextLinks.push({ source: jobNodeId, target: skillNodeId, relationship: "REQUIRE" });
          });
        });
        setNodes(nextNodes);
        setLinks(nextLinks);
        setQueryNote(`Đã tải ${ids.length} vị trí và ${nextNodes.filter((node) => node.type === "Skill").length} kỹ năng.`);
      } else {
        const responses = await Promise.all(
          ids.map((id) => apiClient.get(`/graph/cvs/${id}/skills`)),
        );
        const nextNodes: GraphNode[] = [];
        const nextLinks: GraphLink[] = [];
        responses.forEach((res, index) => {
          const id = ids[index];
          const skills = res.data?.data || [];
          const cvNodeId = `cand_${id}`;
          nextNodes.push({ id: cvNodeId, label: `CV #${id}`, type: "Candidate" });
          skills.forEach((skill: { name: string }) => {
            const skillNodeId = `skill_${skill.name}`;
            if (!nextNodes.some((node) => node.id === skillNodeId)) {
              nextNodes.push({ id: skillNodeId, label: skill.name, type: "Skill" });
            }
            nextLinks.push({ source: cvNodeId, target: skillNodeId, relationship: "HAS_SKILL" });
          });
        });
        setNodes(nextNodes);
        setLinks(nextLinks);
        setQueryNote(`Đã tải ${ids.length} CV và ${nextNodes.filter((node) => node.type === "Skill").length} kỹ năng.`);
      }
    } catch (err: unknown) {
      if (isUnauthorizedError(err)) return;
      console.warn("Neo4j live query failed:", err);
      setQueryNote("Không thể tải dữ liệu đồ thị thực tế. Vui lòng kiểm tra Neo4j và quyền truy cập.");
    } finally {
      setLoadingGraph(false);
    }
  };

  const toggleEntity = (id: number) => {
    setSelectedEntityIds((current) =>
      current.includes(id)
        ? current.filter((value) => value !== id)
        : current.length < 10
          ? [...current, id]
          : current,
    );
  };

  const applyQuickGroup = (keyword: string, limit: number) => {
    const matches = entityOptions
      .filter((item) => item.searchText.includes(keyword.toLowerCase()))
      .slice(0, limit)
      .map((item) => item.id);
    setSelectedEntityIds(matches);
    setQueryNote(matches.length
      ? `Đã chọn ${matches.length} mục theo nhóm “${keyword}”.`
      : `Chưa tìm thấy dữ liệu phù hợp với nhóm “${keyword}”.`);
  };

  const filteredEntityOptions = entityOptions
    .filter((item) => item.searchText.includes(entitySearch.toLowerCase()))
    .slice(0, 30);

  const matchingNodes = nodes.filter(
    (n) =>
      visibleTypes.has(n.type) &&
      n.label.toLowerCase().includes(searchTerm.toLowerCase())
  );
  const filteredNodes = matchingNodes.slice(0, maxNodes);
  const filteredLinks = links.filter(
    (l) =>
      filteredNodes.some((n) => n.id === l.source) &&
      filteredNodes.some((n) => n.id === l.target)
  );

  return (
    <div className="bg-slate-50 min-h-screen">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">

        {/* Header */}
        <div className="mb-6">
          <span className="inline-flex items-center gap-1.5 text-xs font-bold text-blue-600 tracking-wider uppercase mb-2">
            <Network className="h-3.5 w-3.5" />
            Khu vực quản trị — Mạng lưới nghề nghiệp
          </span>
          <h1 className="text-3xl font-bold text-slate-900">
            Trực Quan Hóa Mạng Lưới Tri Thức Nghề Nghiệp
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            Khám phá mối liên hệ giữa lĩnh vực, chuyên môn, kỹ năng và vị trí việc làm.
          </p>
        </div>

        {/* Live Query Control Bar */}
        <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-4 mb-6">
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div className="flex flex-wrap items-center gap-3">
              <span className="text-xs font-bold text-slate-600 uppercase">Chế độ xem:</span>
              <div className="inline-flex rounded-lg border border-slate-200 bg-slate-50 p-1">
                <button
                  type="button"
                  onClick={() => setQueryType("job")}
                  aria-pressed={queryType === "job"}
                  className={`px-3 py-1.5 rounded-md text-xs font-semibold transition-colors ${
                    queryType === "job" ? "bg-white text-blue-600 shadow-xs" : "text-slate-600 hover:text-slate-900"
                  }`}
                >
                  Kỹ năng của vị trí
                </button>
                <button
                  type="button"
                  onClick={() => setQueryType("cv")}
                  aria-pressed={queryType === "cv"}
                  className={`px-3 py-1.5 rounded-md text-xs font-semibold transition-colors ${
                    queryType === "cv" ? "bg-white text-blue-600 shadow-xs" : "text-slate-600 hover:text-slate-900"
                  }`}
                >
                  Kỹ năng của hồ sơ
                </button>
              </div>

              <div className="relative min-w-72">
                <span className="mb-1 block text-xs font-semibold text-slate-500">
                  {queryType === "job" ? "Chọn vị trí" : "Chọn CV"} (tối đa 10)
                </span>
                <div
                  role="button"
                  tabIndex={0}
                  onClick={() => setSelectorOpen((open) => !open)}
                  onKeyDown={(event) => {
                    if (event.key === "Enter" || event.key === " ") {
                      event.preventDefault();
                      setSelectorOpen((open) => !open);
                    }
                  }}
                  aria-expanded={selectorOpen}
                  aria-haspopup="listbox"
                  aria-label={`Chọn ${queryType === "job" ? "vị trí" : "hồ sơ"} để khám phá`}
                  className="flex min-h-9 w-full flex-wrap items-center gap-1 rounded-lg border border-slate-200 bg-slate-50 px-2 py-1 text-left focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  {selectedEntityIds.length ? selectedEntityIds.map((id) => {
                    const item = entityOptions.find((option) => option.id === id);
                    return (
                      <span key={id} className="inline-flex max-w-36 items-center gap-1 rounded-full bg-blue-100 px-2 py-1 text-[11px] font-semibold text-blue-700">
                        <span className="truncate">{item?.label || `#${id}`}</span>
                        <button
                          type="button"
                          aria-label={`Bỏ chọn ${item?.label || `mục ${id}`}`}
                          className="rounded-full hover:bg-blue-200"
                          onClick={(event) => { event.stopPropagation(); toggleEntity(id); }}
                        >
                          <X className="h-3 w-3 shrink-0" />
                        </button>
                      </span>
                    );
                  }) : <span className="px-1 text-xs text-slate-400">Chọn dữ liệu...</span>}
                </div>
                {selectorOpen && (
                  <div role="listbox" aria-label="Danh sách dữ liệu" className="absolute left-0 top-full z-30 mt-1 w-full rounded-xl border border-slate-200 bg-white p-2 shadow-xl">
                    <div className="mb-2 flex items-center justify-between px-1">
                      <span className="text-[11px] font-semibold text-slate-500">
                        Đã chọn {selectedEntityIds.length}/10
                      </span>
                      <button
                        type="button"
                        onClick={() => setSelectedEntityIds([])}
                        className="text-[11px] font-semibold text-blue-600 hover:text-blue-800"
                      >
                        Xóa tất cả
                      </button>
                    </div>
                    <input
                      autoFocus
                      value={entitySearch}
                      onChange={(event) => setEntitySearch(event.target.value)}
                      aria-label="Tìm dữ liệu theo tên, lĩnh vực hoặc kỹ năng"
                      placeholder="Tìm theo tên, domain hoặc kỹ năng..."
                      className="mb-2 w-full rounded-lg border border-slate-200 px-3 py-2 text-xs outline-none focus:ring-2 focus:ring-blue-500"
                    />
                    <div className="max-h-52 overflow-y-auto">
                      {filteredEntityOptions.map((item) => (
                        <button
                          key={item.id}
                          type="button"
                          role="option"
                          aria-selected={selectedEntityIds.includes(item.id)}
                          onClick={() => toggleEntity(item.id)}
                          className="flex w-full items-center gap-2 rounded-lg px-2 py-2 text-left text-xs hover:bg-blue-50"
                        >
                          <span className={`flex h-4 w-4 items-center justify-center rounded border ${selectedEntityIds.includes(item.id) ? "border-blue-600 bg-blue-600 text-white" : "border-slate-300"}`}>
                            {selectedEntityIds.includes(item.id) && <Check className="h-3 w-3" />}
                          </span>
                          <span className="truncate">{item.label}</span>
                          <span className="ml-auto text-[10px] text-slate-400">#{item.id}</span>
                        </button>
                      ))}
                      {!filteredEntityOptions.length && <p className="p-3 text-center text-xs text-slate-400">Không tìm thấy dữ liệu</p>}
                    </div>
                  </div>
                )}
              </div>
            </div>
            <div className="mt-3 flex flex-wrap items-center gap-2 border-t border-slate-100 pt-3">
              <span className="text-xs font-semibold text-slate-500">Chọn nhanh:</span>
              <button type="button" onClick={() => applyQuickGroup(queryType === "job" ? "cloud" : "java", 5)} className="rounded-full border border-slate-200 bg-white px-3 py-1.5 text-xs font-medium text-slate-600 hover:border-blue-300 hover:text-blue-600">
                {queryType === "job" ? "+ Nhóm Cloud / DevOps" : "+ Top 5 CV Java"}
              </button>
              <button type="button" onClick={() => applyQuickGroup(queryType === "job" ? "backend" : "data", 5)} className="rounded-full border border-slate-200 bg-white px-3 py-1.5 text-xs font-medium text-slate-600 hover:border-blue-300 hover:text-blue-600">
                {queryType === "job" ? "+ Nhóm Backend" : "+ Top 5 CV Data"}
              </button>
              <button type="button" onClick={() => setSelectedEntityIds(entityOptions.slice(0, 10).map((item) => item.id))} className="rounded-full border border-blue-100 bg-blue-50 px-3 py-1.5 text-xs font-semibold text-blue-700 hover:bg-blue-100">
                Chọn 10 mục đầu
              </button>
            </div>

            <button
              onClick={handleFetchGraph}
              disabled={loadingGraph}
              className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl bg-blue-600 text-white text-xs font-semibold hover:bg-blue-700 disabled:opacity-60 transition-colors shadow-xs"
            >
              {loadingGraph ? (
                <>
                  <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                  Đang tải dữ liệu...
                </>
              ) : (
                <>
                  <Database className="w-3.5 h-3.5" />
                  Tải mạng lưới
                </>
              )}
            </button>
          </div>

          {queryNote && (
            <div role="status" aria-live="polite" className="mt-3 p-2.5 bg-blue-50 border border-blue-200 rounded-xl text-xs text-blue-900 flex items-center gap-2">
              <Sparkles className="w-3.5 h-3.5 text-blue-600 flex-shrink-0" />
              <span>{queryNote}</span>
            </div>
          )}
          <div className="mt-3 flex flex-wrap items-center gap-3 border-t border-slate-100 pt-3">
            <label className="flex items-center gap-2 text-xs font-semibold text-slate-600">
              <Sliders className="h-3.5 w-3.5 text-blue-600" />
              Giới hạn hiển thị
              <select value={maxNodes} onChange={(event) => setMaxNodes(Number(event.target.value))} className="rounded-lg border border-slate-200 bg-white px-2 py-1 text-xs font-normal">
                <option value={20}>20 node</option>
                <option value={50}>50 node</option>
                <option value={100}>100 node</option>
                <option value={250}>250 node</option>
              </select>
            </label>
            <span role="status" className="text-xs text-slate-400">
              Đang hiển thị {filteredNodes.length}/{matchingNodes.length} node phù hợp
            </span>
          </div>
        </div>

        <div className="flex flex-col lg:flex-row gap-6">

          {/* Left: controls + legend */}
          <div className="lg:w-64 space-y-4 flex-shrink-0">

            {/* Search */}
            <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-4">
              <label className="block text-xs font-semibold text-slate-600 mb-2">Tìm Node</label>
              <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-slate-400" />
                <input
                  type="text"
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  aria-label="Tìm node trong mạng lưới"
                  placeholder="Nhập tên node..."
                  className="w-full pl-8 pr-3 py-2 rounded-lg border border-slate-200 bg-slate-50 text-slate-900 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
            </div>

            {/* Filter by type */}
            <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-4">
              <label className="block text-xs font-semibold text-slate-600 mb-3">Lọc theo loại Node</label>
              <div className="space-y-2">
                {Object.entries(NODE_TYPE_COLORS).map(([type, cfg]) => (
                  <button
                    key={type}
                    type="button"
                    onClick={() => toggleType(type)}
                    aria-pressed={visibleTypes.has(type)}
                    className={`w-full flex items-center gap-2.5 px-3 py-2 rounded-lg text-left text-sm transition-colors ${
                      visibleTypes.has(type)
                        ? "bg-slate-50 border border-slate-200"
                        : "opacity-40 bg-slate-50 border border-slate-200"
                    }`}
                  >
                    <div className={`w-3 h-3 rounded-full flex-shrink-0 ${cfg.dot}`} />
                    <span className="text-slate-700 font-medium">{type}</span>
                    <span className="ml-auto text-xs text-slate-400">{cfg.text}</span>
                  </button>
                ))}
              </div>
            </div>

            {/* Stats */}
            <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-4">
              <div className="text-xs font-semibold text-slate-600 mb-2">Thống kê Graph</div>
              <div className="space-y-1.5 text-sm">
                <div className="flex justify-between">
                  <span className="text-slate-500">Nodes hiển thị</span>
                  <span className="font-bold text-slate-900">{filteredNodes.length}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500">Edges hiển thị</span>
                  <span className="font-bold text-slate-900">{filteredLinks.length}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500">Tổng Nodes</span>
                  <span className="font-bold text-slate-900">{nodes.length}</span>
                </div>
              </div>
            </div>
          </div>

          {/* Right: Graph canvas */}
          <div className="flex-1">
            <div className="relative bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden" style={{ height: "560px" }}>

              {/* Canvas toolbar */}
              <div className="border-b border-slate-200 px-4 py-2 flex items-center gap-2 bg-slate-50">
                <div className="flex items-center gap-1.5 text-xs text-slate-500">
                  <Sparkles className="h-3.5 w-3.5 text-blue-500" />
                  Cytoscape.js — Kéo để di chuyển · Scroll để zoom · Click node để xem chi tiết
                </div>
                <div className="ml-auto flex items-center gap-1">
                  <button type="button" aria-label="Phóng to mạng lưới" title="Phóng to" className="p-1.5 rounded-lg hover:bg-slate-200 text-slate-600 transition-colors">
                    <ZoomIn className="h-4 w-4" />
                  </button>
                  <button type="button" aria-label="Thu nhỏ mạng lưới" title="Thu nhỏ" className="p-1.5 rounded-lg hover:bg-slate-200 text-slate-600 transition-colors">
                    <ZoomOut className="h-4 w-4" />
                  </button>
                  <button type="button" aria-label="Đặt lại kích thước mạng lưới" title="Đặt lại kích thước" className="p-1.5 rounded-lg hover:bg-slate-200 text-slate-600 transition-colors">
                    <Maximize2 className="h-4 w-4" />
                  </button>
                </div>
              </div>

              <GraphCanvas
                nodes={filteredNodes}
                links={filteredLinks}
                onSelectNode={(node) => setSelectedNode(node)}
              />
              {nodes.length === 0 && !loadingGraph && (
                <div className="absolute inset-x-0 bottom-0 top-11 flex items-center justify-center bg-white/90 p-6 text-center">
                  <div className="max-w-sm">
                    <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-blue-50 text-blue-600">
                      <Network className="h-7 w-7" />
                    </div>
                    <h3 className="text-base font-bold text-slate-900">Bắt đầu khám phá mạng lưới</h3>
                    <p className="mt-2 text-sm leading-relaxed text-slate-500">
                      Chọn một hoặc nhiều {queryType === "job" ? "vị trí" : "hồ sơ"} ở phía trên, sau đó nhấn <strong>Tải mạng lưới</strong> để xem các kỹ năng liên quan.
                    </p>
                  </div>
                </div>
              )}
            </div>

            {/* Node Detail Slide-over panel */}
            {selectedNode && (
              <div className="mt-4 bg-white rounded-2xl border border-blue-200 shadow-sm p-5">
                <div className="flex items-start justify-between mb-3">
                  <div className="flex items-center gap-2">
                    <div className={`w-3 h-3 rounded-full ${NODE_TYPE_COLORS[selectedNode.type]?.dot ?? "bg-slate-400"}`} />
                    <span className={`text-xs font-bold px-2 py-0.5 rounded-full ${NODE_TYPE_COLORS[selectedNode.type]?.badge ?? "bg-slate-100 text-slate-700"}`}>
                      {selectedNode.type}
                    </span>
                  </div>
                  <button
                    onClick={() => setSelectedNode(null)}
                    className="p-1 rounded-lg hover:bg-slate-100 text-slate-500"
                  >
                    <X className="h-4 w-4" />
                  </button>
                </div>
                <h3 className="text-lg font-bold text-slate-900 mb-2">{selectedNode.label}</h3>
                <div className="grid grid-cols-2 gap-3 text-sm">
                  <div>
                    <span className="text-xs text-slate-500">Node ID</span>
                    <code className="block text-xs font-mono bg-slate-100 px-2 py-1 rounded mt-0.5 text-slate-700">
                      {selectedNode.id}
                    </code>
                  </div>
                  <div>
                    <span className="text-xs text-slate-500">Loại thực thể</span>
                    <div className="text-sm font-medium text-slate-900 mt-0.5">
                      {NODE_TYPE_COLORS[selectedNode.type]?.text}
                    </div>
                  </div>
                  <div>
                    <span className="text-xs text-slate-500">Connections</span>
                    <div className="text-sm font-medium text-slate-900 mt-0.5">
                      {links.filter(
                        (l) => l.source === selectedNode.id || l.target === selectedNode.id
                      ).length} edges
                    </div>
                  </div>
                  <div>
                    <span className="text-xs text-slate-500">Embedding</span>
                    <div className="text-sm font-medium text-slate-900 mt-0.5">
                      dim=384 (MiniLM)
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Legend */}
        <div className="mt-6 bg-white rounded-2xl border border-slate-200 shadow-sm p-4">
          <div className="flex items-center gap-2 mb-3">
            <Info className="h-4 w-4 text-slate-500" />
            <span className="text-xs font-semibold text-slate-600">Chú thích màu sắc Node</span>
          </div>
          <div className="flex flex-wrap gap-4">
            {Object.entries(NODE_TYPE_COLORS).map(([type, cfg]) => (
              <div key={type} className="flex items-center gap-2 text-sm">
                <div className={`w-3 h-3 rounded-full ${cfg.dot}`} />
                <span className="text-slate-600">{type}</span>
                <span className="text-slate-400 text-xs">({cfg.text})</span>
              </div>
            ))}
          </div>
        </div>

      </div>
    </div>
  );
}
