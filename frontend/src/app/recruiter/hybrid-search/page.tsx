"use client";

import { useEffect, useState } from "react";
import {
  Users,
  Search,
  CheckCircle2,
  XCircle,
  Award,
  RefreshCw,
  HelpCircle,
  Mail,
  UserCheck,
  Sparkles,
  Zap,
  Network,
  TrendingUp,
  ChevronDown,
  AlertCircle,
  FileQuestion,
} from "lucide-react";
import { CandidateSearchResult } from "@/types";
import apiClient from "@/lib/api";

const TOP_K_OPTIONS = [5, 10, 15, 20];

const rankConfig = [
  { rank: 1, medal: "🥇", bg: "bg-amber-50", border: "border-amber-200" },
  { rank: 2, medal: "🥈", bg: "bg-slate-50", border: "border-slate-200" },
  { rank: 3, medal: "🥉", bg: "bg-orange-50", border: "border-orange-200" },
];

function getSkillName(skill: unknown): string {
  if (typeof skill === "string") return skill;
  if (skill && typeof skill === "object" && "name" in skill && typeof skill.name === "string") {
    return skill.name;
  }
  return "Kỹ năng chưa đặt tên";
}

function toScore(value: unknown): number {
  const score = typeof value === "number" ? value : Number(value);
  return Number.isFinite(score) ? score : 0;
}

function normalizeCandidate(candidate: Record<string, unknown>): CandidateSearchResult {
  const matchedSkills = Array.isArray(candidate.matchedSkills) ? candidate.matchedSkills : [];
  const missingSkills = Array.isArray(candidate.missingSkills) ? candidate.missingSkills : [];
  const vectorScore = toScore(candidate.vectorScore);
  const graphSkillScore = toScore(candidate.graphSkillScore);
  const totalScore = toScore(candidate.totalScore ?? candidate.hybridScore);

  return {
    cvId: Number(candidate.cvId ?? 0),
    candidateTitle: typeof candidate.candidateTitle === "string" ? candidate.candidateTitle : undefined,
    totalScore,
    vectorScore,
    graphSkillScore,
    matchedSkillsCount: Number(candidate.matchedSkillsCount ?? matchedSkills.length),
    requiredSkillsCount: Number(candidate.requiredSkillsCount ?? matchedSkills.length + missingSkills.length),
    matchedSkills: matchedSkills as CandidateSearchResult["matchedSkills"],
    missingSkills: missingSkills as CandidateSearchResult["missingSkills"],
    experienceYears: typeof candidate.experienceYears === "number" ? candidate.experienceYears : undefined,
  };
}

export default function HybridSearchPage() {
  const [jobId, setJobId] = useState<number>(0);
  const [jobs, setJobs] = useState<{ id: number; title: string }[]>([]);
  const [topK, setTopK] = useState<number>(10);
  const [loading, setLoading] = useState(false);
  const [hasSearched, setHasSearched] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [candidates, setCandidates] = useState<CandidateSearchResult[]>([]);
  const [expandedId, setExpandedId] = useState<number | null>(null);

  useEffect(() => {
    const queryJobId = Number(new URLSearchParams(window.location.search).get("jobId"));
    void apiClient.get("/jd/available").then((res) => {
      const items = res.data?.data || [];
      setJobs(items);
      setJobId(items.some((item: { id: number }) => item.id === queryJobId)
        ? queryJobId
        : items[0]?.id || 0);
    }).catch(() => setErrorMsg("Không thể tải danh sách tin tuyển dụng từ backend."));
  }, []);

  const handleSearch = async () => {
    setLoading(true);
    setErrorMsg(null);
    setHasSearched(true);
    try {
      const res = await apiClient.get(
        `/graph/jobs/${jobId}/candidates?top_k=${topK}`
      );
      const items = res.data?.data?.candidates || res.data?.data || [];
      if (Array.isArray(items)) {
        setCandidates(
          items
            .filter((item): item is Record<string, unknown> => Boolean(item && typeof item === "object"))
            .map(normalizeCandidate),
        );
      } else {
        setCandidates([]);
      }
    } catch (err: unknown) {
      const axiosErr = err as { response?: { status?: number; data?: { detail?: string } } };
      if (axiosErr.response?.status === 401) {
        setErrorMsg(
          "Yêu cầu quyền HR hoặc Admin để thực hiện tìm kiếm này. Bạn vui lòng Đăng nhập với tài khoản HR (hr1@cvsystem.com / Hr@123456) tại trang Đăng nhập."
        );
      } else {
        setErrorMsg(
          axiosErr.response?.data?.detail ||
            "Không thể kết nối với API backend hoặc Job ID này không tồn tại trong CSDL."
        );
      }
      setCandidates([]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-slate-50 min-h-screen">
      <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-8">

        {/* Header */}
        <div className="mb-8">
          <span className="inline-flex items-center gap-1.5 text-xs font-bold text-emerald-600 tracking-wider uppercase mb-2">
            <Sparkles className="h-3.5 w-3.5" />
          </span>
          <h1 className="text-3xl font-bold text-slate-900">
            Tìm Kiếm & Xếp Hạng Ứng Viên Tiềm Năng
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            Tìm và xếp hạng ứng viên dựa trên mức độ phù hợp với vị trí tuyển dụng.
          </p>
        </div>

        {/* Controls */}
        <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6 mb-6">
          <div className="flex flex-wrap items-end gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-600 mb-1.5">Vị trí tuyển dụng</label>
              <select
                value={jobId}
                onChange={(e) => setJobId(Number(e.target.value))}
                disabled={jobs.length === 0}
                className="w-32 px-3 py-2 rounded-lg border border-slate-200 bg-slate-50 text-slate-900 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                {jobs.map((job) => <option key={job.id} value={job.id}>{job.title} · Mã #{job.id}</option>)}
              </select>
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-600 mb-1.5">Số lượng (Top-K)</label>
              <select
                value={topK}
                onChange={(e) => setTopK(Number(e.target.value))}
                className="px-3 py-2 rounded-lg border border-slate-200 bg-slate-50 text-slate-900 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                {TOP_K_OPTIONS.map((k) => (
                  <option key={k} value={k}>Top {k}</option>
                ))}
              </select>
            </div>
            <button
              onClick={handleSearch}
              disabled={loading || !jobId}
              className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-blue-600 text-white text-sm font-semibold hover:bg-blue-700 disabled:opacity-60 disabled:cursor-not-allowed transition-colors shadow-sm"
            >
              {loading ? (
                <>
                  <RefreshCw className="h-4 w-4 animate-spin" />
                  Đang tìm ứng viên phù hợp...
                </>
              ) : (
                <>
                  <Search className="h-4 w-4" />
                  Tìm ứng viên phù hợp
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

        {/* Score legend */}
        <div className="flex flex-wrap gap-4 mb-6 text-xs text-slate-500">
          <div className="flex items-center gap-1.5">
            <Zap className="h-3.5 w-3.5 text-blue-500" />
            <span>Mức độ tương đồng nội dung</span>
          </div>
          <div className="flex items-center gap-1.5">
            <Network className="h-3.5 w-3.5 text-emerald-500" />
            <span>Mức độ phù hợp kỹ năng</span>
          </div>
          <div className="flex items-center gap-1.5">
            <TrendingUp className="h-3.5 w-3.5 text-violet-500" />
            <span>Điểm tổng hợp: nội dung + kỹ năng</span>
          </div>
        </div>

        {/* Loading Skeletons */}
        {loading && (
          <div className="space-y-4 animate-pulse">
            <div className="h-28 bg-white rounded-2xl border border-slate-200 p-5" />
            <div className="h-28 bg-white rounded-2xl border border-slate-200 p-5" />
            <div className="h-28 bg-white rounded-2xl border border-slate-200 p-5" />
          </div>
        )}

        {/* Empty State before search */}
        {!loading && !hasSearched && !errorMsg && (
          <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-12 text-center">
            <div className="w-16 h-16 rounded-2xl bg-emerald-50 text-emerald-600 flex items-center justify-center mx-auto mb-4 border border-emerald-100 shadow-xs">
              <Users className="w-8 h-8" />
            </div>
            <h3 className="text-lg font-bold text-slate-900 mb-1">
              Sàng lọc ứng viên kết hợp Vector & Knowledge Graph
            </h3>
            <p className="text-sm text-slate-500 max-w-md mx-auto mb-6">
              Nhập Job ID tuyển dụng và bấm nút <strong>Tìm Ứng Viên</strong> để truy vấn các hồ sơ CV phù hợp nhất từ cơ sở dữ liệu.
            </p>
            <button
              onClick={handleSearch}
              className="inline-flex items-center gap-2 px-6 py-2.5 rounded-xl bg-blue-600 text-white font-semibold text-sm hover:bg-blue-700 transition-colors shadow-sm"
            >
              <Search className="w-4 h-4" />
              Tìm ứng viên cho Job #{jobId}
            </button>
          </div>
        )}

        {/* No Candidates Found */}
        {!loading && hasSearched && candidates.length === 0 && !errorMsg && (
          <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-8 text-center text-slate-500">
            <FileQuestion className="w-10 h-10 mx-auto text-slate-400 mb-2" />
            <p className="text-sm font-semibold text-slate-700">
              Không tìm thấy ứng viên nào cho Job ID #{jobId}.
            </p>
            <p className="text-xs text-slate-400 mt-1">
              Vui lòng kiểm tra lại Job ID hoặc thử đồng bộ lại dữ liệu trong trang Admin ETL.
            </p>
          </div>
        )}

        {/* Real Candidate List */}
        {!loading && candidates.length > 0 && (
          <div className="space-y-4">
            {candidates.map((c, idx) => {
              const cfg = rankConfig[idx] ?? {
                rank: idx + 1,
                medal: `#${idx + 1}`,
                bg: "bg-white",
                border: "border-slate-200",
              };
              const isExpanded = expandedId === c.cvId;
              const totalScore = toScore(c.totalScore);
              const vectorScore = toScore(c.vectorScore);
              const graphSkillScore = toScore(c.graphSkillScore);
              const totalPct = Math.round(totalScore * 100);
              const vectorPct = Math.round(vectorScore * 100);
              const graphPct = Math.round(graphSkillScore * 100);
              const fitLabel =
                totalPct >= 75 ? "Rất phù hợp" : totalPct >= 50 ? "Có tiềm năng" : "Cần xem xét thêm";
              const fitColor =
                totalPct >= 75 ? "text-emerald-700 bg-emerald-50 border-emerald-200"
                  : totalPct >= 50 ? "text-amber-700 bg-amber-50 border-amber-200"
                    : "text-slate-600 bg-slate-100 border-slate-200";

              return (
                <div key={c.cvId} className={`rounded-2xl border shadow-sm ${cfg.bg} ${cfg.border} overflow-hidden`}>
                  <div className="p-5">
                    <div className="flex flex-col sm:flex-row sm:items-center gap-4">
                      {/* Rank + Name */}
                      <div className="flex items-center gap-3 flex-1">
                        <span className="text-2xl">{cfg.medal}</span>
                        <div>
                          <div className="flex items-center gap-2">
                            <UserCheck className="h-4 w-4 text-blue-500" />
                            <h3 className="font-bold text-slate-900">{c.candidateTitle || `CV #${c.cvId}`}</h3>
                            {totalPct >= 75 && (
                              <span className="text-xs bg-blue-100 text-blue-700 px-2 py-0.5 rounded-full font-medium">
                                Ứng viên sáng giá
                              </span>
                            )}
                          </div>
                          <p className="text-xs text-slate-500 mt-0.5">
                            CV ID: #{c.cvId} · Kinh nghiệm: {c.experienceYears ?? 0} năm
                          </p>
                        </div>
                      </div>

                      {/* Score pills */}
                      <div className="flex flex-wrap gap-2 items-center">
                        <div className="text-center bg-white rounded-xl px-3 py-1.5 border border-slate-200 shadow-sm">
                          <div className="text-lg font-bold text-slate-900">{totalPct}%</div>
                          <div className="text-[10px] text-slate-500">Tổng điểm</div>
                        </div>
                        <div className="text-center bg-blue-50 rounded-xl px-3 py-1.5 border border-blue-200">
                          <div className="text-sm font-bold text-blue-700">{vectorPct}%</div>
                          <div className="text-[10px] text-blue-600">Vector ANN</div>
                        </div>
                        <div className="text-center bg-emerald-50 rounded-xl px-3 py-1.5 border border-emerald-200">
                          <div className="text-sm font-bold text-emerald-700">{graphPct}%</div>
                          <div className="text-[10px] text-emerald-600">Graph Skill</div>
                        </div>
                      </div>
                    </div>

                    {/* Skill quick view */}
                    {c.matchedSkills && c.matchedSkills.length > 0 && (
                      <div className="mt-4 flex flex-wrap gap-1.5">
                        <span className="text-xs text-slate-400 mr-1">
                          Kỹ năng đáp ứng ({c.matchedSkillsCount ?? c.matchedSkills.length}/{c.requiredSkillsCount ?? c.matchedSkills.length}):
                        </span>
                        {c.matchedSkills.map((skill, index) => {
                          const name = getSkillName(skill);
                          return (
                          <span key={`${name}-${index}`} className="inline-flex items-center gap-1 text-xs bg-green-100 text-green-700 px-2 py-0.5 rounded-full">
                            <CheckCircle2 className="h-2.5 w-2.5" />
                            {name}
                          </span>
                          );
                        })}
                      </div>
                    )}

                    {c.missingSkills && c.missingSkills.length > 0 && (
                      <div className="mt-2 flex flex-wrap gap-1.5">
                        <span className="text-xs text-slate-400 mr-1">Còn thiếu ({c.missingSkills.length}):</span>
                        {c.missingSkills.map((skill, index) => {
                          const name = getSkillName(skill);
                          return (
                          <span key={`${name}-${index}`} className="inline-flex items-center gap-1 text-xs bg-red-100 text-red-700 px-2 py-0.5 rounded-full">
                            <XCircle className="h-2.5 w-2.5" />
                            {name}
                          </span>
                          );
                        })}
                      </div>
                    )}

                    {/* Actions */}
                    <div className="mt-4 flex flex-wrap gap-2">
                      <button
                        onClick={() => setExpandedId(isExpanded ? null : c.cvId)}
                        className="inline-flex items-center gap-1.5 text-xs text-slate-600 hover:text-blue-600 border border-slate-200 hover:border-blue-300 px-3 py-1.5 rounded-lg transition-colors bg-white"
                      >
                        <HelpCircle className="h-3.5 w-3.5" />
                        Xem giải thích Graph
                        <ChevronDown className={`h-3.5 w-3.5 transition-transform ${isExpanded ? "rotate-180" : ""}`} />
                      </button>
                    </div>
                  </div>

                  {/* Accordion: Explanation */}
                  {isExpanded && (
                    <div className="border-t border-slate-200 bg-slate-50 p-5">
                      <div className="mb-4 flex flex-wrap items-start justify-between gap-3">
                        <div className="flex items-center gap-2">
                        <Network className="h-4 w-4 text-blue-600" />
                          <div>
                            <span className="text-sm font-semibold text-slate-900">Vì sao hồ sơ này được đề xuất?</span>
                            <p className="mt-0.5 text-xs text-slate-500">Tóm tắt các yếu tố ảnh hưởng đến thứ hạng.</p>
                          </div>
                        </div>
                        <span className={`rounded-full border px-3 py-1 text-xs font-bold ${fitColor}`}>{fitLabel}</span>
                      </div>
                      <div className="mb-4 rounded-xl border border-blue-100 bg-blue-50/70 p-4">
                        <div className="flex items-start gap-3">
                          <Award className="mt-0.5 h-5 w-5 shrink-0 text-blue-600" />
                          <div>
                            <div className="text-sm font-bold text-slate-900">
                              {c.candidateTitle || `CV #${c.cvId}`} đạt mức phù hợp {totalPct}%
                            </div>
                            <p className="mt-1 text-xs leading-5 text-slate-600">
                              Hồ sơ được đánh giá dựa trên mức tương đồng nội dung, kỹ năng đáp ứng và mức độ liên quan với vị trí đang chọn.
                            </p>
                          </div>
                        </div>
                      </div>
                      <div className="grid sm:grid-cols-2 gap-4 text-sm">
                        <div className="bg-white rounded-xl border border-slate-200 p-4">
                          <div className="text-xs font-bold text-blue-600 mb-2">Mức độ phù hợp tổng quan</div>
                          <div className="space-y-1 text-xs text-slate-600">
                            <div>Nội dung hồ sơ với vị trí: <strong>{vectorPct}%</strong></div>
                            <div>Kỹ năng đáp ứng yêu cầu: <strong>{graphPct}%</strong></div>
                            <div>Số năm kinh nghiệm: <strong>{c.experienceYears ?? 0} năm</strong></div>
                          </div>
                        </div>
                        <div className="bg-white rounded-xl border border-slate-200 p-4">
                          <div className="text-xs font-bold text-emerald-600 mb-2">Gợi ý cho nhà tuyển dụng</div>
                          <div className="space-y-1 text-xs text-slate-600">
                            <div><strong>{c.matchedSkills?.length || 0}</strong> kỹ năng phù hợp</div>
                            <div><strong>{c.missingSkills?.length || 0}</strong> kỹ năng cần xem thêm</div>
                            <div className="pt-1 text-emerald-700">
                              {totalPct >= 75 ? "Nên ưu tiên xem hồ sơ này." : "Nên xem chi tiết trước khi quyết định."}
                            </div>
                          </div>
                        </div>
                      </div>
                      {c.matchedSkills?.length > 0 && (
                        <div className="mt-4 rounded-xl border border-emerald-100 bg-emerald-50/50 p-4">
                          <div className="mb-2 text-xs font-bold text-emerald-700">Điểm mạnh nổi bật</div>
                          <div className="flex flex-wrap gap-1.5">
                            {c.matchedSkills.map((skill, index) => (
                              <span key={`detail-matched-${index}`} className="rounded-full bg-white px-2.5 py-1 text-xs font-medium text-emerald-700 shadow-sm">
                                {getSkillName(skill)}
                              </span>
                            ))}
                          </div>
                        </div>
                      )}
                      {c.missingSkills?.length > 0 && (
                        <div className="mt-3 rounded-xl border border-amber-100 bg-amber-50/50 p-4">
                          <div className="mb-2 text-xs font-bold text-amber-700">Nội dung nên xác minh thêm</div>
                          <div className="flex flex-wrap gap-1.5">
                            {c.missingSkills.map((skill, index) => (
                              <span key={`detail-missing-${index}`} className="rounded-full bg-white px-2.5 py-1 text-xs font-medium text-amber-700 shadow-sm">
                                {getSkillName(skill)}
                              </span>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}

      </div>
    </div>
  );
}
