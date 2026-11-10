"use client";

import { useEffect, useState } from "react";
import {
  Layers,
  Sparkles,
  TrendingUp,
  RefreshCw,
  Compass,
  AlertCircle,
  Trophy,
  ArrowRight,
  BrainCircuit,
} from "lucide-react";
import DomainMatrixHeatmap from "@/components/visualizers/DomainMatrixHeatmap";
import { DomainGapMatrixResponse } from "@/types";
import apiClient from "@/lib/api";

const medalConfig = [
  { emoji: "🥇", bg: "bg-amber-50", border: "border-amber-200", text: "text-amber-700", badge: "bg-amber-100 text-amber-800" },
  { emoji: "🥈", bg: "bg-slate-50", border: "border-slate-200", text: "text-slate-700", badge: "bg-slate-100 text-slate-800" },
  { emoji: "🥉", bg: "bg-orange-50", border: "border-orange-200", text: "text-orange-700", badge: "bg-orange-100 text-orange-800" },
];

export default function CareerMatrixPage() {
  const [cvId, setCvId] = useState<number>(301);
  const [profiles, setProfiles] = useState<{ id: number; title?: string }[]>([]);
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [matrixData, setMatrixData] = useState<DomainGapMatrixResponse | null>(null);

  useEffect(() => {
    void apiClient.get("/profile/available").then((res) => {
      const items = res.data?.data || [];
      setProfiles(items);
      const stored = Number(localStorage.getItem("last_cv_id"));
      setCvId(items.some((item: { id: number }) => item.id === stored) ? stored : items[0]?.id || 0);
    }).catch(() => setErrorMsg("Không thể tải danh sách CV từ backend."));
  }, []);

  const handleAnalyze = async () => {
    setLoading(true);
    setErrorMsg(null);
    try {
      const res = await apiClient.get(`/graph/matrix/domain-gap/${cvId}`);
      if (res.data?.data) {
        setMatrixData(res.data.data);
      } else if (res.data) {
        setMatrixData(res.data);
      } else {
        setErrorMsg("API không trả về ma trận hợp lệ cho CV ID này.");
        setMatrixData(null);
      }
    } catch (err: unknown) {
      const axiosErr = err as { response?: { status?: number; data?: { detail?: string } } };
      setErrorMsg(
        axiosErr.response?.data?.detail ||
          "Không thể lấy ma trận từ API. Vui lòng đảm bảo backend FastAPI đang chạy và CV ID tồn tại trong cơ sở dữ liệu."
      );
      setMatrixData(null);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-slate-50 min-h-screen">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">

        {/* Header */}
        <div className="mb-8">
          <span className="inline-flex items-center gap-1.5 text-xs font-bold text-violet-600 tracking-wider uppercase mb-2">
            <Sparkles className="h-3.5 w-3.5" />
            Bài toán 2 — Ma trận định hướng nghề nghiệp (1 CV vs Many Domains)
          </span>
          <h1 className="text-3xl font-bold text-slate-900">
            Ma Trận Định Hướng Nghề Nghiệp CNTT
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            Gọi API trực tiếp: <code className="text-violet-600 bg-violet-50 px-1.5 py-0.5 rounded text-xs font-mono">GET /api/v1/graph/matrix/domain-gap/{`{cv_id}`}</code>
          </p>
        </div>

        {/* Controls */}
        <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6 mb-6">
          <div className="flex flex-wrap items-end gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-600 mb-1.5">CV ID (Database ID)</label>
              <select
              value={cvId}
              onChange={(e) => setCvId(Number(e.target.value))}
              disabled={profiles.length === 0}
              className="w-32 px-3 py-2 rounded-lg border border-slate-200 bg-slate-50 text-slate-900 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
              {profiles.map((profile) => <option key={profile.id} value={profile.id}>#{profile.id} {profile.title || "CV"}</option>)}
              </select>
            </div>
            <button
              onClick={handleAnalyze}
              disabled={loading || !cvId}
              className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-violet-600 text-white text-sm font-semibold hover:bg-violet-700 disabled:opacity-60 disabled:cursor-not-allowed transition-colors shadow-sm"
            >
              {loading ? (
                <>
                  <RefreshCw className="h-4 w-4 animate-spin" />
                  Đang tính toán ma trận Neo4j...
                </>
              ) : (
                <>
                  <Layers className="h-4 w-4" />
                  Phân Tích Ma Trận (GET /matrix/domain-gap)
                </>
              )}
            </button>
          </div>

          {errorMsg && (
            <div className="mt-4 flex items-start gap-2 p-3.5 bg-rose-50 border border-rose-200 rounded-xl text-sm text-rose-800">
              <AlertCircle className="h-4 w-4 text-rose-500 flex-shrink-0 mt-0.5" />
              <div>
                <strong>Lỗi từ API:</strong> {errorMsg}
              </div>
            </div>
          )}
        </div>

        {/* Loading Skeleton */}
        {loading && (
          <div className="space-y-6 animate-pulse">
            <div className="bg-white rounded-2xl border border-slate-200 p-6 h-72" />
            <div className="grid md:grid-cols-3 gap-4">
              <div className="bg-white rounded-2xl border border-slate-200 p-6 h-40" />
              <div className="bg-white rounded-2xl border border-slate-200 p-6 h-40" />
              <div className="bg-white rounded-2xl border border-slate-200 p-6 h-40" />
            </div>
          </div>
        )}

        {/* Empty State before querying */}
        {!loading && !matrixData && !errorMsg && (
          <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-12 text-center">
            <div className="w-16 h-16 rounded-2xl bg-violet-50 text-violet-600 flex items-center justify-center mx-auto mb-4 border border-violet-100 shadow-xs">
              <Compass className="w-8 h-8" />
            </div>
            <h3 className="text-lg font-bold text-slate-900 mb-1">
              Khám phá độ phù hợp đa lĩnh vực
            </h3>
            <p className="text-sm text-slate-500 max-w-md mx-auto mb-6">
              Nhập mã CV ID của bạn và nhấn <strong>Phân Tích Ma Trận</strong>. Hệ thống sẽ kết nối với đồ thị tri thức Neo4j và tính toán mức độ phù hợp của 4 thuộc tính hồ sơ trên 8 lĩnh vực CNTT trọng tâm.
            </p>
            <button
              onClick={handleAnalyze}
              className="inline-flex items-center gap-2 px-6 py-2.5 rounded-xl bg-violet-600 text-white font-semibold text-sm hover:bg-violet-700 transition-colors shadow-sm"
            >
              <Layers className="w-4 h-4" />
              Phân tích CV #{cvId}
            </button>
          </div>
        )}

        {/* Real Data Results */}
        {!loading && matrixData && (
          <div>
            {/* Heatmap + Rankings side by side */}
            <div className="grid lg:grid-cols-3 gap-6 mb-6">

              {/* Heatmap */}
              <div className="lg:col-span-2 bg-white rounded-2xl border border-slate-200 shadow-sm p-6">
                <div className="flex items-center gap-2 mb-4">
                  <Compass className="h-5 w-5 text-violet-600" />
                  <h2 className="font-semibold text-slate-900">Heatmap Độ Phù Hợp Thực Tế</h2>
                </div>
                <p className="text-xs text-slate-500 mb-4">
                  Màu đậm = tương thích cao · Hover vào ô để xem giải trình ngữ nghĩa
                </p>
                <DomainMatrixHeatmap matrix={matrixData.domainMatrix} />

                {/* Legend */}
                <div className="mt-4 flex items-center gap-3 text-xs text-slate-500">
                  <span>Thấp (&lt;35%)</span>
                  <div className="flex gap-1">
                    {["bg-slate-50 border border-slate-200", "bg-blue-50", "bg-blue-200", "bg-blue-400", "bg-blue-600"].map((c) => (
                      <div key={c} className={`w-6 h-3 rounded ${c}`} />
                    ))}
                  </div>
                  <span>Cao (≥80%)</span>
                </div>
              </div>

              {/* Top 3 Rankings */}
              <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6">
                <div className="flex items-center gap-2 mb-4">
                  <Trophy className="h-5 w-5 text-amber-500" />
                  <h2 className="font-semibold text-slate-900">Top Lĩnh Vực Tiềm Năng</h2>
                </div>
                <div className="space-y-3">
                  {matrixData.domainRankings && matrixData.domainRankings.slice(0, 3).map((d, i) => {
                    const cfg = medalConfig[i] || medalConfig[2];
                    return (
                      <div key={d.domain} className={`rounded-xl border p-4 ${cfg.bg} ${cfg.border}`}>
                        <div className="flex items-start gap-3">
                          <span className="text-xl">{cfg.emoji}</span>
                          <div className="flex-1 min-w-0">
                            <div className="font-semibold text-slate-900 text-sm">{d.domain}</div>
                            <div className="text-2xl font-bold mt-1 text-slate-900">
                              {Math.round(d.compatibilityScore * 100)}%
                            </div>
                            <div className="text-xs text-slate-500 mt-1">
                              phù hợp · skill coverage: {Math.round(d.skillCoverageRatio * 100)}%
                            </div>
                            {d.suggestedJobTitles && d.suggestedJobTitles.length > 0 && (
                              <div className="flex flex-wrap gap-1 mt-2">
                                {d.suggestedJobTitles.slice(0, 2).map((t: string) => (
                                  <span key={t} className={`text-xs px-2 py-0.5 rounded-full font-medium ${cfg.badge}`}>
                                    {t}
                                  </span>
                                ))}
                              </div>
                            )}
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            </div>

            {/* Domain details */}
            {matrixData.domainRankings && matrixData.domainRankings.length > 0 && (
              <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6">
                <h3 className="font-semibold text-slate-900 mb-4 flex items-center gap-2">
                  <TrendingUp className="h-4 w-4 text-blue-600" />
                  Xếp Hạng Đầy Đủ Các Lĩnh Vực
                </h3>
                <div className="space-y-3">
                  {matrixData.domainRankings.map((d, i) => (
                    <div key={d.domain} className="flex items-center gap-4 py-3 border-b border-slate-100 last:border-0">
                      <span className="w-6 text-center text-sm font-bold text-slate-400">#{d.rank || i + 1}</span>
                      <div className="flex-1">
                        <div className="flex items-center justify-between mb-1.5">
                          <span className="text-sm font-medium text-slate-900">{d.domain}</span>
                          <span className="text-sm font-bold text-slate-900">{Math.round(d.compatibilityScore * 100)}%</span>
                        </div>
                        <div className="h-2 bg-slate-100 rounded-full overflow-hidden">
                          <div
                            className="h-full bg-violet-600 rounded-full transition-all duration-700"
                            style={{ width: `${d.compatibilityScore * 100}%` }}
                          />
                        </div>
                      </div>
                      <div className="hidden sm:flex flex-wrap gap-1 w-48 justify-end">
                        <span className="text-xs bg-slate-100 text-slate-700 px-2 py-0.5 rounded-full">
                          Độ phủ: {Math.round(d.skillCoverageRatio * 100)}%
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

      </div>
    </div>
  );
}
