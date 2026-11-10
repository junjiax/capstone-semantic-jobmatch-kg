"use client";

import { useState } from "react";
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
  Briefcase,
  User,
  RefreshCw,
  Sliders,
} from "lucide-react";
import GraphCanvas from "@/components/visualizers/GraphCanvas";
import { GraphNode, GraphLink } from "@/types";
import apiClient from "@/lib/api";

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
  const [entityId, setEntityId] = useState<number>(1);
  const [loadingGraph, setLoadingGraph] = useState(false);
  const [queryNote, setQueryNote] = useState<string | null>(null);

  const [visibleTypes, setVisibleTypes] = useState<Set<string>>(
    new Set(["Domain", "Expertise", "Skill", "JobPosition", "Candidate"])
  );

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
      if (queryType === "job") {
        // Call GET /api/v1/graph/jobs/{job_id}/skills
        const res = await apiClient.get(`/graph/jobs/${entityId}/skills`);
        const skills = res.data?.data || [];
        const jobNode: GraphNode = {
          id: `job_${entityId}`,
          label: `Job #${entityId}`,
          type: "JobPosition",
        };
        const skillNodes: GraphNode[] = skills.map((s: { name: string; id?: number }) => ({
          id: `skill_${s.name}`,
          label: s.name,
          type: "Skill",
        }));
        const newLinks: GraphLink[] = skills.map((s: { name: string }) => ({
          source: `job_${entityId}`,
          target: `skill_${s.name}`,
          relationship: "REQUIRE",
        }));

        setNodes([jobNode, ...skillNodes]);
        setLinks(newLinks);
        setQueryNote(`Đã tải thành công mạng lưới kỹ năng yêu cầu của Job #${entityId} từ Neo4j.`);
      } else {
        // Call GET /api/v1/graph/cvs/{cv_id}/skills
        const res = await apiClient.get(`/graph/cvs/${entityId}/skills`);
        const skills = res.data?.data || [];
        const cvNode: GraphNode = {
          id: `cand_${entityId}`,
          label: `Candidate #${entityId}`,
          type: "Candidate",
        };
        const skillNodes: GraphNode[] = skills.map((s: { name: string; id?: number }) => ({
          id: `skill_${s.name}`,
          label: s.name,
          type: "Skill",
        }));
        const newLinks: GraphLink[] = skills.map((s: { name: string }) => ({
          source: `cand_${entityId}`,
          target: `skill_${s.name}`,
          relationship: "HAS_SKILL",
        }));

        setNodes([cvNode, ...skillNodes]);
        setLinks(newLinks);
        setQueryNote(`Đã tải thành công mạng lưới kỹ năng của CV #${entityId} từ Neo4j.`);
      }
    } catch (err) {
      console.warn("Neo4j live query failed:", err);
      setQueryNote("Không thể tải dữ liệu đồ thị thực tế. Vui lòng kiểm tra Neo4j và quyền truy cập.");
    } finally {
      setLoadingGraph(false);
    }
  };

  const filteredNodes = nodes.filter(
    (n) =>
      visibleTypes.has(n.type) &&
      n.label.toLowerCase().includes(searchTerm.toLowerCase())
  );
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
            Knowledge Graph Lab — Neo4j LPG
          </span>
          <h1 className="text-3xl font-bold text-slate-900">
            Trực Quan Hóa Mạng Lưới Tri Thức Nghề Nghiệp
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            Truy vấn đồ thị thực tế: Domain → Expertise → Skill cùng các quan hệ REQUIRE, HAS_SKILL, RELATED_TO từ Neo4j.
          </p>
        </div>

        {/* Live Query Control Bar */}
        <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-4 mb-6">
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div className="flex flex-wrap items-center gap-3">
              <span className="text-xs font-bold text-slate-600 uppercase">Chế độ xem:</span>
              <div className="inline-flex rounded-lg border border-slate-200 bg-slate-50 p-1">
                <button
                  onClick={() => setQueryType("job")}
                  className={`px-3 py-1.5 rounded-md text-xs font-semibold transition-colors ${
                    queryType === "job" ? "bg-white text-blue-600 shadow-xs" : "text-slate-600 hover:text-slate-900"
                  }`}
                >
                  Job Skills (GET /jobs/id/skills)
                </button>
                <button
                  onClick={() => setQueryType("cv")}
                  className={`px-3 py-1.5 rounded-md text-xs font-semibold transition-colors ${
                    queryType === "cv" ? "bg-white text-blue-600 shadow-xs" : "text-slate-600 hover:text-slate-900"
                  }`}
                >
                  CV Skills (GET /cvs/id/skills)
                </button>
              </div>

              <div className="flex items-center gap-2">
                  <span className="text-xs text-slate-500 font-semibold">
                    {queryType === "job" ? "Job ID:" : "CV ID:"}
                  </span>
                  <input
                    type="number"
                    value={entityId}
                    onChange={(e) => setEntityId(Number(e.target.value))}
                    className="w-20 px-2.5 py-1 text-xs rounded-lg border border-slate-200 bg-slate-50 text-slate-900 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
              </div>
            </div>

            <button
              onClick={handleFetchGraph}
              disabled={loadingGraph}
              className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl bg-blue-600 text-white text-xs font-semibold hover:bg-blue-700 disabled:opacity-60 transition-colors shadow-xs"
            >
              {loadingGraph ? (
                <>
                  <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                  Đang truy vấn Cypher Neo4j...
                </>
              ) : (
                <>
                  <Database className="w-3.5 h-3.5" />
                  Tải Graph từ Neo4j
                </>
              )}
            </button>
          </div>

          {queryNote && (
            <div className="mt-3 p-2.5 bg-blue-50 border border-blue-200 rounded-xl text-xs text-blue-900 flex items-center gap-2">
              <Sparkles className="w-3.5 h-3.5 text-blue-600 flex-shrink-0" />
              <span>{queryNote}</span>
            </div>
          )}
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
                    onClick={() => toggleType(type)}
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
            <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden" style={{ height: "560px" }}>

              {/* Canvas toolbar */}
              <div className="border-b border-slate-200 px-4 py-2 flex items-center gap-2 bg-slate-50">
                <div className="flex items-center gap-1.5 text-xs text-slate-500">
                  <Sparkles className="h-3.5 w-3.5 text-blue-500" />
                  Cytoscape.js — Kéo để di chuyển · Scroll để zoom · Click node để xem chi tiết
                </div>
                <div className="ml-auto flex items-center gap-1">
                  <button className="p-1.5 rounded-lg hover:bg-slate-200 text-slate-600 transition-colors">
                    <ZoomIn className="h-4 w-4" />
                  </button>
                  <button className="p-1.5 rounded-lg hover:bg-slate-200 text-slate-600 transition-colors">
                    <ZoomOut className="h-4 w-4" />
                  </button>
                  <button className="p-1.5 rounded-lg hover:bg-slate-200 text-slate-600 transition-colors">
                    <Maximize2 className="h-4 w-4" />
                  </button>
                </div>
              </div>

              <GraphCanvas
                nodes={filteredNodes}
                links={filteredLinks}
                onSelectNode={(node) => setSelectedNode(node)}
              />
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
