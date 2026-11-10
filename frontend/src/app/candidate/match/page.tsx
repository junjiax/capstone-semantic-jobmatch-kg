"use client";

import { useEffect, useState } from "react";
import {
  Sparkles,
  CheckCircle2,
  XCircle,
  HelpCircle,
  ArrowRight,
  BookOpen,
  Award,
  RefreshCw,
  TrendingUp,
  AlertCircle,
  Search,
  BrainCircuit,
  FileQuestion,
} from "lucide-react";
import RadarChart5Aspects from "@/components/visualizers/RadarChart5Aspects";
import SkillGapBadge from "@/components/visualizers/SkillGapBadge";
import { MatchResultResponse } from "@/types";
import apiClient from "@/lib/api";

// Circular score ring
function CircularScore({ value }: { value: number }) {
  const pct = Math.round(value * 100);
  const r = 54;
  const circ = 2 * Math.PI * r;
  const offset = circ - (pct / 100) * circ;
  const color = pct >= 65 ? "#16a34a" : pct >= 50 ? "#d97706" : "#dc2626";

  return (
    <div className="relative inline-flex items-center justify-center">
      <svg width="140" height="140" className="-rotate-90">
        <circle cx="70" cy="70" r={r} stroke="#e2e8f0" strokeWidth="10" fill="none" />
        <circle
          cx="70"
          cy="70"
          r={r}
          stroke={color}
          strokeWidth="10"
          fill="none"
          strokeDasharray={circ}
          strokeDashoffset={offset}
          strokeLinecap="round"
          style={{ transition: "stroke-dashoffset 1s ease" }}
        />
      </svg>
      <div className="absolute text-center">
        <div className="text-3xl font-bold text-slate-900">{pct}%</div>
        <div className="text-xs text-slate-500">phù hợp</div>
      </div>
    </div>
  );
}

// Loading Skeleton Shimmer
function MatchLoadingSkeleton() {
  return (
    <div className="space-y-6 animate-pulse">
      <div className="bg-white rounded-2xl border border-slate-200 p-6 flex items-center gap-6">
        <div className="w-32 h-32 rounded-full bg-slate-200 flex-shrink-0" />
        <div className="flex-1 space-y-3">
          <div className="h-4 bg-slate-200 rounded w-1/4" />
          <div className="h-6 bg-slate-200 rounded w-3/4" />
          <div className="h-4 bg-slate-200 rounded w-1/2" />
        </div>
      </div>
      <div className="grid lg:grid-cols-2 gap-6">
        <div className="bg-white rounded-2xl border border-slate-200 p-6 h-80" />
        <div className="bg-white rounded-2xl border border-slate-200 p-6 h-80 space-y-4">
          <div className="h-4 bg-slate-200 rounded w-1/3" />
          <div className="h-4 bg-slate-200 rounded" />
          <div className="h-4 bg-slate-200 rounded" />
          <div className="h-4 bg-slate-200 rounded" />
        </div>
      </div>
    </div>
  );
}

export default function MatchDetailPage() {
  const [cvId, setCvId] = useState<number>(301);
  const [jdId, setJdId] = useState<number>(17);
  const [profiles, setProfiles] = useState<{ id: number; title?: string }[]>([]);
  const [jobs, setJobs] = useState<{ id: number; title: string; domain?: string }[]>([]);
  const [optionsLoading, setOptionsLoading] = useState(true);
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [matchData, setMatchData] = useState<MatchResultResponse | null>(null);

  useEffect(() => {
    const loadOptions = async () => {
      try {
        const [profileRes, jobRes] = await Promise.all([
          apiClient.get("/profile/available"),
          apiClient.get("/jd/available"),
        ]);
        const nextProfiles = profileRes.data?.data || [];
        const nextJobs = jobRes.data?.data || [];
        setProfiles(nextProfiles);
        setJobs(nextJobs);
        const storedCvId = Number(localStorage.getItem("last_cv_id"));
        setCvId(nextProfiles.some((item: { id: number }) => item.id === storedCvId)
          ? storedCvId
          : nextProfiles[0]?.id || 0);
        setJdId(nextJobs[0]?.id || 0);
      } catch {
        setErrorMsg("Không thể tải danh sách CV/JD từ backend.");
      } finally {
        setOptionsLoading(false);
      }
    };
    void loadOptions();
  }, []);

  const handleRunMatch = async () => {
    setLoading(true);
    setErrorMsg(null);
    try {
      // 1. Thử gọi endpoint Smart Knowledge Graph Match mới (/graph/match-similarity)
      try {
        const smartRes = await apiClient.get(
          `/graph/match-similarity?profile_id=${cvId}&jd_id=${jdId}`
        );
        const data = smartRes.data?.data || smartRes.data;
        if (data && (data.match_score !== undefined || data.matched_skills)) {
          const matchedSkillsList = (data.matched_skills || []).map((s: string) => ({
            name: s,
            similarity: 1.0,
          }));
          const partialSkillsList = (data.transferable_skills || []).map(
            (t: { required_skill: string; candidate_skill: string; cluster_name: string }) => ({
              name: `${t.candidate_skill} ➔ ${t.required_skill} (${t.cluster_name})`,
              similarity: 0.75,
            })
          );
          const missingSkillsList = (data.missing_skills || []).map((s: string) => ({
            name: s,
            similarity: 0.0,
          }));
          const extraSkillsList = (data.bonus_skills || []).map((s: string) => ({
            name: s,
            similarity: 1.0,
          }));

          const adapted: MatchResultResponse = {
            cvId: data.profile_id || cvId,
            jdId: data.jd_id || jdId,
            jobTitle: `Vị trí tuyển dụng #${data.jd_id || jdId}`,
            totalResult: data.match_score || 0,
            isSuitable: Boolean(data.is_suitable),
            explanation:
              data.verdict ||
              `Độ phù hợp tổng hợp: ${Math.round((data.match_score || 0) * 100)}% kết hợp tri thức đồ thị và độ tương đồng ngữ nghĩa.`,
            scores: {
              totalResult: data.match_score || 0,
              skillScore: data.match_score || 0,
              domainScore: data.semantic_similarity || data.match_score || 0,
              expertiseScore: data.semantic_similarity || data.match_score || 0,
              experienceScore: data.is_suitable ? 0.9 : 0.5,
              qualificationScore: 1.0,
            },
            skillGap: {
              jobTitle: `Vị trí tuyển dụng #${data.jd_id || jdId}`,
              totalRequiredSkills: matchedSkillsList.length + missingSkillsList.length,
              totalMatchedSkills: matchedSkillsList.length,
              totalMissingSkills: missingSkillsList.length,
              skillCoverageRatio: data.match_score || 0,
              matchedSkills: matchedSkillsList,
              partiallyMatchedSkills: partialSkillsList,
              missingSkills: missingSkillsList,
              extraSkills: extraSkillsList,
              explanation: data.verdict,
            },
          };
          setMatchData(adapted);
          return;
        }
      } catch (smartErr) {
        // Fallback sang endpoint POST /graph/match/{cv_id}/{jd_id}
      }

      // 2. Fallback gọi endpoint POST /graph/match/{cv_id}/{jd_id}
      const res = await apiClient.post(`/graph/match/${cvId}/${jdId}`);
      if (res.data?.data) {
        setMatchData(res.data.data);
      } else if (res.data) {
        setMatchData(res.data);
      } else {
        setErrorMsg("API không trả về dữ liệu cho cặp CV ID và JD ID này.");
        setMatchData(null);
      }
    } catch (err: unknown) {
      const axiosErr = err as { response?: { status?: number; data?: { detail?: string } } };
      const detail = axiosErr.response?.data?.detail;
      setErrorMsg(
        detail ||
          `Không tìm thấy dữ liệu cho CV ID ${cvId} và JD ID ${jdId}. Vui lòng kiểm tra ID thực tế trong bảng PROFILE và JD của database.`
      );
      setMatchData(null);
    } finally {
      setLoading(false);
    }
  };

  const handleRunSkillGapOnly = async () => {
    setLoading(true);
    setErrorMsg(null);
    try {
      // 1. Thử gọi endpoint Skill Gap mới (/skill-gap/profile/{cv_id}/jd/{jd_id})
      try {
        const sgRes = await apiClient.get(`/skill-gap/profile/${cvId}/jd/${jdId}`);
        const data = sgRes.data?.data || sgRes.data;
        if (data?.summary) {
          const matched = (data.matched_skills || []).map((s: { skill_name: string; similarity_score?: number }) => ({
            name: s.skill_name,
            similarity: s.similarity_score ?? 1.0,
          }));
          const partial = (data.partially_matched_skills || []).map((s: { skill_name: string; closest_candidate_skill?: string; similarity_score?: number }) => ({
            name: s.closest_candidate_skill ? `${s.closest_candidate_skill} ➔ ${s.skill_name}` : s.skill_name,
            similarity: s.similarity_score ?? 0.7,
          }));
          const missing = (data.missing_skills || []).map((s: { skill_name: string }) => ({
            name: s.skill_name,
            similarity: 0.0,
          }));
          const extra = (data.extra_skills || []).map((s: { skill_name: string }) => ({
            name: s.skill_name,
            similarity: 1.0,
          }));

          const adapted: MatchResultResponse = {
            cvId,
            jdId,
            jobTitle: `Tin tuyển dụng #${jdId}`,
            totalResult: data.summary.skill_coverage_ratio || 0,
            isSuitable: (data.summary.skill_coverage_ratio || 0) >= 0.65,
            explanation: `Phân tích khoảng cách kỹ năng: Đáp ứng ${data.summary.total_matched_skills}/${data.summary.total_required_skills} kỹ năng (${Math.round((data.summary.skill_coverage_ratio || 0) * 100)}%).`,
            scores: {
              totalResult: data.summary.skill_coverage_ratio || 0,
              skillScore: data.summary.skill_coverage_ratio || 0,
              domainScore: 0.5,
              expertiseScore: 0.5,
              experienceScore: 0.5,
              qualificationScore: 1.0,
            },
            skillGap: {
              jobTitle: `Tin tuyển dụng #${jdId}`,
              totalRequiredSkills: data.summary.total_required_skills,
              totalMatchedSkills: data.summary.total_matched_skills,
              totalMissingSkills: data.summary.total_missing_skills,
              skillCoverageRatio: data.summary.skill_coverage_ratio,
              matchedSkills: matched,
              partiallyMatchedSkills: partial,
              missingSkills: missing,
              extraSkills: extra,
              recommendation: data.recommendations?.join("; "),
            },
          };
          setMatchData(adapted);
          return;
        }
      } catch (sgErr) {
        // Fallback sang endpoint cũ
      }

      // 2. Fallback gọi endpoint cũ /graph/skill-gap/{cvId}/{jdId}
      const res = await apiClient.get(`/graph/skill-gap/${cvId}/${jdId}`);
      if (res.data?.data) {
        setMatchData((prev) =>
          prev
            ? { ...prev, skillGap: res.data.data }
            : {
                cvId,
                jdId,
                jobTitle: `Job #${jdId}`,
                totalResult: res.data.data.skillCoverageRatio || 0,
                isSuitable: (res.data.data.skillCoverageRatio || 0) >= 0.65,
                scores: {
                  totalResult: res.data.data.skillCoverageRatio || 0,
                  skillScore: res.data.data.skillCoverageRatio || 0,
                  domainScore: 0,
                  expertiseScore: 0,
                  experienceScore: 0,
                  qualificationScore: 0,
                },
                skillGap: res.data.data,
                explanation: res.data.data.explanation || "Phân tích khoảng cách kỹ năng từ Neo4j.",
              }
        );
      } else {
        setErrorMsg("Không tìm thấy dữ liệu Skill Gap cho cặp ID này.");
      }
    } catch (err: unknown) {
      const axiosErr = err as { response?: { status?: number; data?: { detail?: string } } };
      setErrorMsg(
        axiosErr.response?.data?.detail ||
          "Lỗi khi gọi API phân tích Skill Gap. Vui lòng kiểm tra ID hồ sơ và tin tuyển dụng."
      );
    } finally {
      setLoading(false);
    }
  };

  const pct = matchData ? Math.round(matchData.totalResult * 100) : 0;
  const isPass = pct >= 65;

  return (
    <div className="bg-slate-50 min-h-screen">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">

        {/* Page Header */}
        <div className="mb-8">
          <span className="inline-flex items-center gap-1.5 text-xs font-bold text-blue-600 tracking-wider uppercase mb-2">
            <Sparkles className="h-3.5 w-3.5" />
            Bài toán 1 — So khớp cặp đôi cụ thể (1 CV vs 1 JD)
          </span>
          <h1 className="text-3xl font-bold text-slate-900">
            Chi Tiết So Khớp Năng Lực Đa Khía Cạnh
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            Gọi API trực tiếp: <code className="text-blue-600 bg-blue-50 px-1.5 py-0.5 rounded text-xs font-mono">POST /api/v1/graph/match/{`{cv_id}`}/{`{jd_id}`}</code>
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
                disabled={optionsLoading || profiles.length === 0}
                className="w-32 px-3 py-2 rounded-lg border border-slate-200 bg-slate-50 text-slate-900 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                {profiles.map((profile) => <option key={profile.id} value={profile.id}>#{profile.id} {profile.title || "CV"}</option>)}
              </select>
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-600 mb-1.5">Tin tuyển dụng</label>
              <select
                value={jdId}
                onChange={(e) => setJdId(Number(e.target.value))}
                disabled={optionsLoading || jobs.length === 0}
                className="min-w-52 px-3 py-2 rounded-lg border border-slate-200 bg-slate-50 text-slate-900 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                {jobs.map((job) => <option key={job.id} value={job.id}>#{job.id} {job.title}</option>)}
              </select>
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-600 mb-1.5">JD ID (Database ID)</label>
              <input
                type="number"
                min="1"
                value={jdId}
                onChange={(e) => setJdId(Number(e.target.value))}
                className="w-32 px-3 py-2 rounded-lg border border-slate-200 bg-slate-50 text-slate-900 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <button
              onClick={handleRunMatch}
              disabled={loading || optionsLoading || !cvId || !jdId}
              className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-blue-600 text-white text-sm font-semibold hover:bg-blue-700 disabled:opacity-60 disabled:cursor-not-allowed transition-colors shadow-sm"
            >
              {loading ? (
                <>
                  <RefreshCw className="h-4 w-4 animate-spin" />
                  Đang gọi API & Đồ thị Neo4j...
                </>
              ) : (
                <>
                  <TrendingUp className="h-4 w-4" />
                  Chạy So Khớp (POST /graph/match)
                </>
              )}
            </button>
            <button
              onClick={handleRunSkillGapOnly}
              disabled={loading}
              className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl bg-white border border-slate-200 text-slate-700 text-sm font-semibold hover:bg-slate-50 disabled:opacity-60 disabled:cursor-not-allowed transition-colors shadow-xs"
            >
              <BookOpen className="h-4 w-4 text-emerald-600" />
              Chỉ phân tích Skill Gap (GET /skill-gap)
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

        {/* Loading State */}
        {loading && <MatchLoadingSkeleton />}

        {/* Empty State when no match has been queried yet */}
        {!loading && !matchData && !errorMsg && (
          <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-12 text-center">
            <div className="w-16 h-16 rounded-2xl bg-blue-50 text-blue-600 flex items-center justify-center mx-auto mb-4 border border-blue-100 shadow-xs">
              <BrainCircuit className="w-8 h-8" />
            </div>
            <h3 className="text-lg font-bold text-slate-900 mb-1">
              Sẵn sàng so khớp dữ liệu thực tế
            </h3>
            <p className="text-sm text-slate-500 max-w-md mx-auto mb-6">
              Nhập mã CV ID và JD ID trong cơ sở dữ liệu của bạn, sau đó nhấn nút <strong>Chạy So Khớp</strong> để hệ thống gửi yêu cầu lên API FastAPI và tính toán thời gian thực từ Knowledge Graph Neo4j.
            </p>
            <button
              onClick={handleRunMatch}
              className="inline-flex items-center gap-2 px-6 py-2.5 rounded-xl bg-blue-600 text-white font-semibold text-sm hover:bg-blue-700 transition-colors shadow-sm"
            >
              <TrendingUp className="w-4 h-4" />
              So khớp với CV ID: {cvId} & JD ID: {jdId}
            </button>
          </div>
        )}

        {/* Real Data Results */}
        {!loading && matchData && (
          <div>
            {/* Score Header Card */}
            <div className={`bg-white rounded-2xl border shadow-sm p-6 mb-6 ${isPass ? "border-green-200" : "border-amber-200"}`}>
              <div className="flex flex-col sm:flex-row items-center gap-6">
                <CircularScore value={matchData.totalResult} />
                <div className="flex-1 text-center sm:text-left">
                  <div className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold mb-2 ${isPass ? "bg-green-100 text-green-700" : "bg-amber-100 text-amber-700"}`}>
                    {isPass ? <CheckCircle2 className="h-3.5 w-3.5" /> : <HelpCircle className="h-3.5 w-3.5" />}
                    {isPass ? "🟢 ĐÃ ĐẠT NGƯỠNG (≥65%)" : "🟡 CHƯA ĐỦ NGƯỠNG (<65%)"}
                  </div>
                  <h2 className="text-xl font-bold text-slate-900 mb-1">{matchData.jobTitle}</h2>
                  <p className="text-sm text-slate-500">{matchData.explanation}</p>
                </div>
              </div>
            </div>

            {/* Split View: Radar + Skill Breakdown */}
            <div className="grid lg:grid-cols-2 gap-6 mb-6">

              {/* Radar Chart */}
              <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6">
                <h3 className="font-semibold text-slate-900 mb-1">Biểu đồ Radar 5 Khía Cạnh</h3>
                <p className="text-xs text-slate-500 mb-4">Hover vào đỉnh để xem điểm chi tiết từ API</p>
                <RadarChart5Aspects scores={matchData.scores} />
              </div>

              {/* Score breakdown */}
              <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6">
                <h3 className="font-semibold text-slate-900 mb-4">Điểm số từng chiều</h3>
                <div className="space-y-4">
                  {[
                    { label: "Kỹ năng (Skill)", value: matchData.scores.skillScore, weight: "40%", color: "bg-blue-500" },
                    { label: "Lĩnh vực (Domain)", value: matchData.scores.domainScore, weight: "20%", color: "bg-violet-500" },
                    { label: "Chuyên môn (Expertise)", value: matchData.scores.expertiseScore, weight: "20%", color: "bg-emerald-500" },
                    { label: "Kinh nghiệm (Experience)", value: matchData.scores.experienceScore, weight: "10%", color: "bg-amber-500" },
                    { label: "Học vấn (Qualification)", value: matchData.scores.qualificationScore, weight: "10%", color: "bg-rose-500" },
                  ].map((item) => (
                    <div key={item.label}>
                      <div className="flex justify-between text-sm mb-1.5">
                        <span className="text-slate-700 font-medium">{item.label}</span>
                        <div className="flex items-center gap-2">
                          <span className="text-xs text-slate-400 bg-slate-100 px-2 py-0.5 rounded-full">{item.weight}</span>
                          <span className="font-bold text-slate-900">{Math.round(item.value * 100)}%</span>
                        </div>
                      </div>
                      <div className="h-2 bg-slate-100 rounded-full overflow-hidden">
                        <div
                          className={`h-full ${item.color} rounded-full transition-all duration-700`}
                          style={{ width: `${item.value * 100}%` }}
                        />
                      </div>
                    </div>
                  ))}
                </div>

                {/* Skill coverage stats */}
                <div className="mt-5 pt-4 border-t border-slate-100 grid grid-cols-3 gap-3 text-center">
                  <div className="bg-green-50 rounded-xl p-3">
                    <div className="text-2xl font-bold text-green-600">{matchData.skillGap?.totalMatchedSkills ?? 0}</div>
                    <div className="text-xs text-green-700">Đã đáp ứng</div>
                  </div>
                  <div className="bg-amber-50 rounded-xl p-3">
                    <div className="text-2xl font-bold text-amber-600">{matchData.skillGap?.partiallyMatchedSkills?.length ?? 0}</div>
                    <div className="text-xs text-amber-700">Một phần</div>
                  </div>
                  <div className="bg-red-50 rounded-xl p-3">
                    <div className="text-2xl font-bold text-red-600">{matchData.skillGap?.totalMissingSkills ?? 0}</div>
                    <div className="text-xs text-red-700">Còn thiếu</div>
                  </div>
                </div>
              </div>
            </div>

            {/* Skill Gap Color Map */}
            {matchData.skillGap && (
              <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6 mb-6">
                <h3 className="font-semibold text-slate-900 mb-4">Bảng Màu Phân Loại Kỹ Năng từ Neo4j</h3>
                <div className="space-y-5">

                  {/* Matched */}
                  {matchData.skillGap.matchedSkills && matchData.skillGap.matchedSkills.length > 0 && (
                    <div>
                      <div className="flex items-center gap-2 mb-2.5">
                        <CheckCircle2 className="h-4 w-4 text-green-600" />
                        <h4 className="text-xs font-bold uppercase tracking-wider text-green-700">
                          🟢 Đạt — Kỹ năng hoàn toàn trùng khớp ({matchData.skillGap.matchedSkills.length})
                        </h4>
                      </div>
                      <div className="flex flex-wrap gap-2">
                        {matchData.skillGap.matchedSkills.map((s, i) => (
                          <SkillGapBadge key={i} name={s.name} status="matched" similarity={s.similarity} />
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Partial */}
                  {(matchData.skillGap.partiallyMatchedSkills?.length ?? 0) > 0 && (
                    <div>
                      <div className="flex items-center gap-2 mb-2.5">
                        <HelpCircle className="h-4 w-4 text-amber-500" />
                        <h4 className="text-xs font-bold uppercase tracking-wider text-amber-700">
                          🟡 Đạt một phần — Tương đương ngữ nghĩa ({matchData.skillGap.partiallyMatchedSkills?.length ?? 0})
                        </h4>
                      </div>
                      <div className="flex flex-wrap gap-2">
                        {(matchData.skillGap.partiallyMatchedSkills ?? []).map((s, i) => (
                          <SkillGapBadge key={i} name={s.name} status="partial" similarity={s.similarity} />
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Missing */}
                  {matchData.skillGap.missingSkills && matchData.skillGap.missingSkills.length > 0 && (
                    <div>
                      <div className="flex items-center gap-2 mb-2.5">
                        <XCircle className="h-4 w-4 text-rose-500" />
                        <h4 className="text-xs font-bold uppercase tracking-wider text-rose-700">
                          🔴 Còn thiếu — JD yêu cầu nhưng CV không có ({matchData.skillGap.missingSkills.length})
                        </h4>
                      </div>
                      <div className="flex flex-wrap gap-2">
                        {matchData.skillGap.missingSkills.map((s, i) => (
                          <SkillGapBadge
                            key={i}
                            name={s.name}
                            status="missing"
                            similarity={s.similarity}
                            weight={s.weight ? `Trọng số: ${s.weight}` : undefined}
                          />
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Extra */}
                  {matchData.skillGap.extraSkills && matchData.skillGap.extraSkills.length > 0 && (
                    <div>
                      <div className="flex items-center gap-2 mb-2.5">
                        <Award className="h-4 w-4 text-violet-500" />
                        <h4 className="text-xs font-bold uppercase tracking-wider text-violet-700">
                          🟣 Thế mạnh bổ trợ — Ứng viên sở hữu thêm ({matchData.skillGap.extraSkills.length})
                        </h4>
                      </div>
                      <div className="flex flex-wrap gap-2">
                        {matchData.skillGap.extraSkills.map((s, i) => (
                          <SkillGapBadge key={i} name={s.name} status="extra" />
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Learning Roadmap */}
            {matchData.skillGap?.recommendation && (
              <div className="bg-blue-50 rounded-2xl border border-blue-200 p-6">
                <div className="flex items-center gap-2 text-blue-900 font-bold text-sm mb-2">
                  <BookOpen className="h-4 w-4 text-blue-600" />
                  Khuyến Nghị Bù Đắp Kỹ Năng từ Knowledge Graph
                </div>
                <p className="text-sm text-blue-800 leading-relaxed">
                  {matchData.skillGap.recommendation}
                </p>
              </div>
            )}
          </div>
        )}

      </div>
    </div>
  );
}
