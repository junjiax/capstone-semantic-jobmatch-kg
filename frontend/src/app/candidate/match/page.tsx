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
  Check,
  Grid2X2,
  X,
} from "lucide-react";
import RadarChart5Aspects from "@/components/visualizers/RadarChart5Aspects";
import SkillGapBadge from "@/components/visualizers/SkillGapBadge";
import { MatchResultResponse } from "@/types";
import apiClient, { isUnauthorizedError } from "@/lib/api";

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
  const [profiles, setProfiles] = useState<{
    id: number;
    title?: string;
    skills?: string[];
  }[]>([]);
  const [jobs, setJobs] = useState<{
    id: number;
    title: string;
    domain?: string;
    expertise?: string;
    experience?: number;
  }[]>([]);
  const [optionsLoading, setOptionsLoading] = useState(true);
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [matchData, setMatchData] = useState<MatchResultResponse | null>(null);
  const [viewMode, setViewMode] = useState<"single" | "matrix">("single");
  const [selectedProfileIds, setSelectedProfileIds] = useState<number[]>([]);
  const [selectedJobIds, setSelectedJobIds] = useState<number[]>([]);
  const [profileFilter, setProfileFilter] = useState("");
  const [jobFilter, setJobFilter] = useState("");
  const [matrixLoading, setMatrixLoading] = useState(false);
  const [matrixResults, setMatrixResults] = useState<Record<string, number>>({});
  const [selectedCell, setSelectedCell] = useState<{ cvId: number; jdId: number } | null>(null);
  const [cellDetail, setCellDetail] = useState<{
    matched: string[];
    missing: string[];
    loading: boolean;
  } | null>(null);

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
        setSelectedProfileIds(nextProfiles.slice(0, 1).map((item: { id: number }) => item.id));
        setSelectedJobIds(nextJobs.slice(0, 1).map((item: { id: number }) => item.id));
      } catch (error: unknown) {
        if (!isUnauthorizedError(error)) {
          setErrorMsg("Không thể tải danh sách CV/JD từ backend.");
        }
      } finally {
        setOptionsLoading(false);
      }
    };
    void loadOptions();
  }, []);

  const toggleSelection = (
    id: number,
    selected: number[],
    setSelected: React.Dispatch<React.SetStateAction<number[]>>,
  ) => {
    setSelected((current) =>
      current.includes(id) ? current.filter((value) => value !== id) : current.length < 6 ? [...current, id] : current,
    );
  };

  const handleRunMatrix = async () => {
    if (!selectedProfileIds.length || !selectedJobIds.length) {
      setErrorMsg("Hãy chọn ít nhất một CV và một JD để so sánh.");
      return;
    }
    setMatrixLoading(true);
    setErrorMsg(null);
    setMatrixResults({});
    try {
      const pairs = selectedProfileIds.flatMap((profileId) =>
        selectedJobIds.map((jobId) => ({ profileId, jobId })),
      );
      const results = await Promise.all(
        pairs.map(async ({ profileId, jobId }) => {
          const response = await apiClient.get(
            `/graph/match-similarity?profile_id=${profileId}&jd_id=${jobId}`,
          );
          const data = response.data?.data || response.data;
          return {
            key: `${profileId}-${jobId}`,
            score: Number(data?.match_score ?? 0),
          };
        }),
      );
      setMatrixResults(Object.fromEntries(results.map((result) => [result.key, result.score])));
    } catch (err: unknown) {
      if (isUnauthorizedError(err)) return;
      const axiosErr = err as { response?: { data?: { detail?: string } } };
      setErrorMsg(axiosErr.response?.data?.detail || "Không thể tạo bảng so sánh. Vui lòng kiểm tra quyền truy cập và dữ liệu.");
    } finally {
      setMatrixLoading(false);
    }
  };

  const handleMatrixCellClick = async (cvId: number, jobId: number) => {
    setSelectedCell({ cvId, jdId: jobId });
    setCellDetail({ matched: [], missing: [], loading: true });
    try {
      const response = await apiClient.get(`/skill-gap/profile/${cvId}/jd/${jobId}`);
      const data = response.data?.data || response.data;
      setCellDetail({
        matched: (data?.matched_skills || []).map((item: { skill_name?: string }) => item.skill_name || ""),
        missing: (data?.missing_skills || []).map((item: { skill_name?: string }) => item.skill_name || ""),
        loading: false,
      });
    } catch (error: unknown) {
      if (!isUnauthorizedError(error)) {
        setCellDetail({ matched: [], missing: [], loading: false });
      }
    }
  };

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
            jobTitle: `JD #${data.jd_id || jdId}`,
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
              jobTitle: `JD #${data.jd_id || jdId}`,
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
        if (isUnauthorizedError(smartErr)) throw smartErr;
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
      if (isUnauthorizedError(err)) return;
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
        if (isUnauthorizedError(sgErr)) throw sgErr;
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
                explanation: res.data.data.explanation || "Phân tích khoảng cách kỹ năng hoàn tất.",
              }
        );
      } else {
        setErrorMsg("Không tìm thấy dữ liệu Skill Gap cho cặp ID này.");
      }
    } catch (err: unknown) {
      if (isUnauthorizedError(err)) return;
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
          </span>
          <h1 className="text-3xl font-bold text-slate-900">
            Chi Tiết So Khớp Năng Lực Đa Khía Cạnh
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            So sánh hồ sơ ứng viên với yêu cầu của vị trí để đánh giá mức độ phù hợp.
          </p>
        </div>

        {/* Controls */}
        <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6 mb-6">
          <div className="mb-5 flex flex-wrap items-center justify-between gap-3 border-b border-slate-100 pb-4">
            <div>
              <h2 className="font-bold text-slate-900">Chọn cách xem kết quả</h2>
              <p className="mt-1 text-xs text-slate-500">So khớp một cặp hoặc so sánh nhanh nhiều CV và JD.</p>
            </div>
            <div className="inline-flex rounded-xl border border-slate-200 bg-slate-50 p-1">
              <button onClick={() => setViewMode("single")} className={`rounded-lg px-3 py-2 text-xs font-semibold ${viewMode === "single" ? "bg-white text-blue-600 shadow-sm" : "text-slate-500"}`}>Một cặp</button>
              <button onClick={() => setViewMode("matrix")} className={`inline-flex items-center gap-1.5 rounded-lg px-3 py-2 text-xs font-semibold ${viewMode === "matrix" ? "bg-white text-blue-600 shadow-sm" : "text-slate-500"}`}><Grid2X2 className="h-3.5 w-3.5" />So sánh nhóm</button>
            </div>
          </div>
          {viewMode === "matrix" && (
            <div className="mb-5 grid gap-4 rounded-xl border border-blue-100 bg-blue-50/40 p-4 lg:grid-cols-2">
              <div>
                <div className="mb-2 flex items-center justify-between">
                  <label className="text-xs font-bold text-slate-700">Chọn CV (tối đa 6)</label>
                  <span className="text-xs text-blue-600">{selectedProfileIds.length}/6</span>
                </div>
                <input value={profileFilter} onChange={(event) => setProfileFilter(event.target.value)} placeholder="Tìm theo tên CV..." className="mb-2 w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-xs outline-none focus:ring-2 focus:ring-blue-500" />
                <div className="max-h-36 space-y-1 overflow-y-auto rounded-lg bg-white p-2">
                  {profiles.filter((profile) => (profile.title || "").toLowerCase().includes(profileFilter.toLowerCase())).slice(0, 30).map((profile) => (
                    <label key={profile.id} className="flex cursor-pointer items-center gap-2 rounded-md px-2 py-1.5 text-xs hover:bg-blue-50">
                      <input type="checkbox" checked={selectedProfileIds.includes(profile.id)} onChange={() => toggleSelection(profile.id, selectedProfileIds, setSelectedProfileIds)} />
                      <span className="truncate">{profile.title || `CV #${profile.id}`}</span>
                    </label>
                  ))}
                </div>
              </div>
              <div>
                <div className="mb-2 flex items-center justify-between">
                  <label className="text-xs font-bold text-slate-700">Chọn JD (tối đa 6)</label>
                  <span className="text-xs text-blue-600">{selectedJobIds.length}/6</span>
                </div>
                <input value={jobFilter} onChange={(event) => setJobFilter(event.target.value)} placeholder="Tìm theo tên vị trí..." className="mb-2 w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-xs outline-none focus:ring-2 focus:ring-blue-500" />
                <div className="max-h-36 space-y-1 overflow-y-auto rounded-lg bg-white p-2">
                  {jobs.filter((job) => job.title.toLowerCase().includes(jobFilter.toLowerCase())).slice(0, 30).map((job) => (
                    <label key={job.id} className="flex cursor-pointer items-center gap-2 rounded-md px-2 py-1.5 text-xs hover:bg-blue-50">
                      <input type="checkbox" checked={selectedJobIds.includes(job.id)} onChange={() => toggleSelection(job.id, selectedJobIds, setSelectedJobIds)} />
                      <span className="truncate">{job.title}</span>
                    </label>
                  ))}
                </div>
              </div>
              <button onClick={() => void handleRunMatrix()} disabled={matrixLoading} className="inline-flex w-fit items-center gap-2 rounded-lg bg-blue-600 px-4 py-2 text-xs font-bold text-white hover:bg-blue-700 disabled:opacity-60 lg:col-span-2">
                <Grid2X2 className="h-3.5 w-3.5" />{matrixLoading ? "Đang tạo bảng so sánh..." : "Tạo bảng so sánh"}
              </button>
            </div>
          )}
          {viewMode === "matrix" && Object.keys(matrixResults).length > 0 && (
            <div className="mb-5 overflow-x-auto rounded-xl border border-slate-200 bg-white">
              <div className="border-b border-slate-100 px-4 py-3 text-sm font-bold text-slate-900">Bảng mức độ phù hợp</div>
              <table className="min-w-full text-xs">
                <thead><tr className="bg-slate-50"><th className="px-4 py-3 text-left font-semibold text-slate-500">CV / Vị trí</th>{selectedJobIds.map((id) => <th key={id} className="max-w-40 px-4 py-3 text-left font-semibold text-slate-600">{jobs.find((job) => job.id === id)?.title || `JD #${id}`}</th>)}</tr></thead>
                <tbody>{selectedProfileIds.map((id) => <tr key={id} className="border-t border-slate-100"><td className="px-4 py-3 font-semibold text-slate-700">{profiles.find((profile) => profile.id === id)?.title || `CV #${id}`}</td>{selectedJobIds.map((jobId) => { const score = matrixResults[`${id}-${jobId}`] ?? 0; const pct = Math.round(score * 100); return <td key={jobId} className="px-4 py-3"><button onClick={() => void handleMatrixCellClick(id, jobId)} className={`min-w-16 rounded-lg border px-3 py-2 font-bold transition hover:scale-105 ${pct >= 80 ? "border-emerald-200 bg-emerald-100 text-emerald-700" : pct >= 50 ? "border-amber-200 bg-amber-100 text-amber-700" : "border-rose-200 bg-rose-100 text-rose-700"}`}>{pct}%</button></td>; })}</tr>)}</tbody>
              </table>
            </div>
          )}
          {selectedCell && cellDetail && (
            <div className="mb-5 rounded-xl border border-violet-100 bg-violet-50/50 p-4">
              <div className="mb-3 flex items-center justify-between"><div className="text-sm font-bold text-slate-900">Chi tiết khoảng cách kỹ năng</div><button onClick={() => { setSelectedCell(null); setCellDetail(null); }} className="rounded-md p-1 text-slate-400 hover:bg-white hover:text-slate-700"><X className="h-4 w-4" /></button></div>
              {cellDetail.loading ? <p className="text-xs text-slate-500">Đang tải phân tích...</p> : <div className="grid gap-3 text-xs sm:grid-cols-2"><div><div className="mb-1 font-bold text-emerald-700">Đang đáp ứng</div><div className="flex flex-wrap gap-1">{cellDetail.matched.length ? cellDetail.matched.map((skill) => <span key={skill} className="rounded-full bg-emerald-100 px-2 py-1 text-emerald-700">{skill}</span>) : <span className="text-slate-500">Chưa có dữ liệu</span>}</div></div><div><div className="mb-1 font-bold text-rose-700">Cần bổ sung</div><div className="flex flex-wrap gap-1">{cellDetail.missing.length ? cellDetail.missing.map((skill) => <span key={skill} className="rounded-full bg-rose-100 px-2 py-1 text-rose-700">{skill}</span>) : <span className="text-slate-500">Không có kỹ năng thiếu</span>}</div></div></div>}
            </div>
          )}
          {viewMode === "single" && (
          <div className="flex flex-wrap items-end gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-600 mb-1.5">Chọn CV</label>
              <select
                value={cvId}
                onChange={(e) => setCvId(Number(e.target.value))}
                disabled={optionsLoading || profiles.length === 0}
                className="w-32 px-3 py-2 rounded-lg border border-slate-200 bg-slate-50 text-slate-900 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                {profiles.map((profile) => <option key={profile.id} value={profile.id}>{profile.title || "CV"} · Mã #{profile.id}</option>)}
              </select>
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-600 mb-1.5">Chọn JD</label>
              <select
                value={jdId}
                onChange={(e) => setJdId(Number(e.target.value))}
                disabled={optionsLoading || jobs.length === 0}
                className="min-w-52 px-3 py-2 rounded-lg border border-slate-200 bg-slate-50 text-slate-900 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                {jobs.map((job) => <option key={job.id} value={job.id}>{job.title} · Mã #{job.id}</option>)}
              </select>
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-600 mb-1.5">Mã vị trí</label>
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
                  Đang phân tích độ phù hợp...
                </>
              ) : (
                <>
                  <TrendingUp className="h-4 w-4" />
                  Phân tích độ phù hợp
                </>
              )}
            </button>
            <button
              onClick={handleRunSkillGapOnly}
              disabled={loading}
              className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl bg-white border border-slate-200 text-slate-700 text-sm font-semibold hover:bg-slate-50 disabled:opacity-60 disabled:cursor-not-allowed transition-colors shadow-xs"
            >
              <BookOpen className="h-4 w-4 text-emerald-600" />
              Xem khoảng cách kỹ năng
            </button>
          </div>
          )}

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
              Chọn hồ sơ và vị trí tuyển dụng, sau đó nhấn <strong>Phân tích độ phù hợp</strong> để xem kết quả chi tiết.
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
            <div className={`bg-white rounded-2xl border shadow-sm p-8 mb-8 ${isPass ? "border-green-200" : pct < 35 ? "border-rose-200" : "border-amber-200"}`}>
              <div className="flex flex-col sm:flex-row items-center gap-6">
                <CircularScore value={matchData.totalResult} />
                <div className="flex-1 text-center sm:text-left">
                  <div className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold mb-3 ${isPass ? "bg-green-100 text-green-700" : pct < 35 ? "bg-rose-100 text-rose-700" : "bg-amber-100 text-amber-700"}`}>
                    {isPass ? <CheckCircle2 className="h-3.5 w-3.5" /> : <HelpCircle className="h-3.5 w-3.5" />}
                    {isPass ? "Mức độ phù hợp tốt" : pct < 35 ? "Cần bổ sung nhiều năng lực" : "Có thể cải thiện thêm"}
                  </div>
                  <h2 className="text-2xl font-bold text-slate-900 mb-2">{matchData.jobTitle}</h2>
                  <p className="text-base leading-relaxed text-slate-600">
                    {pct < 35
                      ? "Hồ sơ hiện chưa đáp ứng nhiều yêu cầu chính của vị trí. Hãy xem phần khoảng cách kỹ năng để biết nên ưu tiên bổ sung nội dung nào."
                      : pct < 65
                        ? "Hồ sơ có một số điểm phù hợp nhưng vẫn còn khoảng cách cần cải thiện trước khi ứng tuyển."
                        : "Hồ sơ đang đáp ứng tốt phần lớn yêu cầu của vị trí này."}
                  </p>
                  <p className="mt-2 text-sm text-slate-500">{matchData.explanation}</p>
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
                <h3 className="font-semibold text-slate-900 mb-4">Chú thích trạng thái kỹ năng</h3>
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
                  Gợi ý phát triển kỹ năng
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
