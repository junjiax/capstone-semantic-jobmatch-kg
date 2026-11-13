"use client";

import { useState } from "react";
import Link from "next/link";
import {
  Search,
  Sparkles,
  Award,
  Briefcase,
  ArrowRight,
  RefreshCw,
} from "lucide-react";
import apiClient from "@/lib/api";

interface SkillResult {
  id: number;
  title: string;
  similarity: number;
  source: string;
  entity_id?: number;
}

interface JobResult {
  jd_id: number;
  title: string;
  domain?: string;
  expertise?: string;
  matched_field: string;
  similarity: number;
}

export default function SemanticSearchPage() {
  const [activeTab, setActiveTab] = useState<"skills" | "jobs">("skills");
  const [query, setQuery] = useState("");
  const [topK, setTopK] = useState(6);
  const [minSimilarity, setMinSimilarity] = useState(0.5);
  const [source, setSource] = useState<"all" | "profile_skill" | "jd_skill">("all");

  const [loading, setLoading] = useState(false);
  const [searched, setSearched] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [skillResults, setSkillResults] = useState<SkillResult[]>([]);
  const [jobResults, setJobResults] = useState<JobResult[]>([]);

  const handleSearch = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!query.trim()) return;

    setLoading(true);
    setSearched(true);
    setErrorMsg(null);

    try {
      if (activeTab === "skills") {
        const res = await apiClient.post("/semantic-search/skills", {
          query: query.trim(),
          top_k: topK,
          min_similarity: minSimilarity,
          source: source,
        });
        const items = res.data?.data?.results || [];
        setSkillResults(items);
      } else {
        const res = await apiClient.post("/semantic-search/job-requirements", {
          query: query.trim(),
          top_k: topK,
          min_similarity: minSimilarity,
        });
        const items = res.data?.data?.results || [];
        setJobResults(items);
      }
    } catch (err: unknown) {
      const axiosErr = err as { response?: { status?: number; data?: { detail?: string } } };
      setErrorMsg(
        axiosErr.response?.data?.detail ||
          "Không thể thực hiện tìm kiếm ngữ nghĩa từ API. Vui lòng kiểm tra kết nối với backend FastAPI."
      );
      if (activeTab === "skills") {
        setSkillResults([]);
      } else {
        setJobResults([]);
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-slate-50 min-h-screen">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8">

        {/* Header */}
        <div className="mb-8">
          <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-blue-50 border border-blue-200 text-blue-700 text-xs font-semibold mb-2">
            <Sparkles className="w-3.5 h-3.5" />
            Tìm kiếm theo ngữ cảnh
          </div>
          <h1 className="text-3xl font-bold text-slate-900">
            Tìm kiếm thông minh
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            Mô tả điều bạn đang tìm kiếm bằng ngôn ngữ tự nhiên để nhận được kỹ năng và vị trí phù hợp.
          </p>
        </div>

        {/* Tabs */}
        <div className="flex border-b border-slate-200 mb-6 gap-2">
          <button
            type="button"
            role="tab"
            aria-selected={activeTab === "skills"}
            onClick={() => {
              setActiveTab("skills");
              setSearched(false);
            }}
            className={`flex items-center gap-2 py-3 px-5 text-sm font-semibold border-b-2 transition-colors ${
              activeTab === "skills"
                ? "border-blue-600 text-blue-600"
                : "border-transparent text-slate-500 hover:text-slate-800"
            }`}
          >
            <Award className="w-4 h-4" />
            Tìm kiếm Kỹ năng (Semantic Skills)
          </button>
          <button
            type="button"
            role="tab"
            aria-selected={activeTab === "jobs"}
            onClick={() => {
              setActiveTab("jobs");
              setSearched(false);
            }}
            className={`flex items-center gap-2 py-3 px-5 text-sm font-semibold border-b-2 transition-colors ${
              activeTab === "jobs"
                ? "border-blue-600 text-blue-600"
                : "border-transparent text-slate-500 hover:text-slate-800"
            }`}
          >
            <Briefcase className="w-4 h-4" />
            Tìm việc theo Yêu cầu (Job Requirements)
          </button>
        </div>

        {/* Search Input & Controls */}
        <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6 mb-8">
          <form onSubmit={handleSearch} className="space-y-4">
            <div className="relative">
              <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
              <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder={
                  activeTab === "skills"
                    ? "Nhập từ khóa kỹ năng (ví dụ: 'lập trình web backend', 'phân tích dữ liệu lớn', 'xây dựng api')..."
                    : "Mô tả mong muốn công việc hoặc năng lực (ví dụ: 'thành thạo FastAPI và PostgreSQL cần tìm vị trí backend')..."
                }
                className="w-full pl-12 pr-4 py-3.5 rounded-xl border border-slate-200 bg-slate-50 text-slate-900 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 shadow-inner"
              />
            </div>

            {/* Filter controls */}
            <div className="grid sm:grid-cols-3 gap-4 pt-2">
              <div>
                <label className="block text-xs font-semibold text-slate-600 mb-1">
                  Số lượng kết quả (Top-K): {topK}
                </label>
                <input
                  type="range"
                  min="3"
                  max="20"
                  value={topK}
                  onChange={(e) => setTopK(Number(e.target.value))}
                  className="w-full accent-blue-600 cursor-pointer"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-600 mb-1">
                  Ngưỡng tương đồng tối thiểu: {(minSimilarity * 100).toFixed(0)}%
                </label>
                <input
                  type="range"
                  min="0.0"
                  max="0.9"
                  step="0.05"
                  value={minSimilarity}
                  onChange={(e) => setMinSimilarity(Number(e.target.value))}
                  className="w-full accent-blue-600 cursor-pointer"
                />
              </div>

              {activeTab === "skills" ? (
                <div>
                  <label className="block text-xs font-semibold text-slate-600 mb-1">
                    Nguồn kỹ năng
                  </label>
                  <select
                    value={source}
                    onChange={(e) =>
                      setSource(e.target.value as "all" | "profile_skill" | "jd_skill")
                    }
                    className="w-full px-3 py-1.5 rounded-lg border border-slate-200 bg-slate-50 text-slate-900 text-xs focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="all">Tất cả nguồn (All)</option>
                    <option value="profile_skill">Kỹ năng từ CVs (Profile)</option>
                    <option value="jd_skill">Kỹ năng từ JDs tuyển dụng</option>
                  </select>
                </div>
              ) : (
                <div className="flex items-end">
                  <span className="text-xs text-slate-400">
                    Mô hình: <code className="bg-slate-100 px-1 py-0.5 rounded">all-MiniLM-L6-v2</code>
                  </span>
                </div>
              )}
            </div>

            <div className="flex justify-end pt-2">
              <button
                type="submit"
                disabled={loading || !query.trim()}
                className="inline-flex items-center gap-2 px-6 py-2.5 rounded-xl bg-blue-600 text-white font-semibold text-sm hover:bg-blue-700 disabled:opacity-60 disabled:cursor-not-allowed transition-colors shadow-sm"
              >
                {loading ? (
                  <>
                    <RefreshCw className="w-4 h-4 animate-spin" />
                    Đang nhúng vector & truy vấn HNSW...
                  </>
                ) : (
                  <>
                    <Search className="w-4 h-4" />
                    Tìm kiếm Ngữ nghĩa
                  </>
                )}
              </button>
            </div>
          </form>

          {errorMsg && (
            <div role="alert" aria-live="assertive" className="mt-4 p-3.5 bg-rose-50 border border-rose-200 rounded-xl text-sm text-rose-800">
              <strong>Lỗi từ API:</strong> {errorMsg}
            </div>
          )}
        </div>

        {/* Results */}
        {searched && (
          <div>
            <div className="flex items-center justify-between mb-4">
              <h2 className="font-bold text-slate-900 text-base">
                Kết quả tìm kiếm cho: &ldquo;{query}&rdquo;
              </h2>
              <span className="text-xs text-slate-400">
                {activeTab === "skills"
                  ? `${skillResults.length} kỹ năng tương đồng`
                  : `${jobResults.length} vị trí việc làm phù hợp`}
              </span>
            </div>

            {/* Skills Results Grid */}
            {activeTab === "skills" && (
              <div className="grid sm:grid-cols-2 md:grid-cols-3 gap-4">
                {skillResults.map((skill) => {
                  const pct = Math.round(skill.similarity * 100);
                  return (
                    <div
                      key={skill.id}
                      className="bg-white rounded-2xl border border-slate-200 shadow-sm p-4 hover:border-blue-300 transition-colors"
                    >
                      <div className="flex items-start justify-between mb-2">
                        <span className="font-bold text-slate-900 text-sm">
                          {skill.title}
                        </span>
                        <span className="text-xs font-mono font-bold bg-blue-50 text-blue-700 px-2 py-0.5 rounded-full border border-blue-200">
                          {pct}%
                        </span>
                      </div>
                      <div className="flex items-center justify-between text-xs text-slate-400 mt-3 pt-2 border-t border-slate-100">
                        <span>Nguồn: {skill.source}</span>
                        <span className="text-emerald-600 font-medium">HNSW Index</span>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
            {activeTab === "skills" && !loading && skillResults.length === 0 && (
              <div className="rounded-2xl border border-dashed border-slate-300 bg-white p-8 text-center text-sm text-slate-500">
                Chưa có kỹ năng phù hợp. Hãy thử mô tả rộng hơn hoặc giảm ngưỡng tương đồng.
              </div>
            )}

            {/* Jobs Results Grid */}
            {activeTab === "jobs" && (
              <div className="space-y-4">
                {jobResults.map((job) => {
                  const pct = Math.round(job.similarity * 100);
                  return (
                    <div
                      key={job.jd_id}
                      className="bg-white rounded-2xl border border-slate-200 shadow-sm p-5 hover:border-blue-300 transition-all flex flex-col sm:flex-row sm:items-center justify-between gap-4"
                    >
                      <div>
                        <div className="flex items-center gap-2 mb-1">
                          <h3 className="font-bold text-slate-900 text-base">
                            {job.title}
                          </h3>
                          <span className="text-xs font-mono font-bold bg-emerald-50 text-emerald-700 px-2.5 py-0.5 rounded-full border border-emerald-200">
                            {pct}% tương đồng
                          </span>
                        </div>
                        <div className="flex flex-wrap items-center gap-2 text-xs text-slate-500 mt-1">
                          <span className="bg-slate-100 px-2 py-0.5 rounded-md font-medium">
                            {job.domain || "Backend Development"}
                          </span>
                          <span>•</span>
                          <span>{job.expertise || "Web Architecture"}</span>
                          <span>•</span>
                          <span className="text-slate-400">Trường khớp: {job.matched_field}</span>
                        </div>
                      </div>
                      <Link
                        href={`/candidate/match?jdId=${job.jd_id}`}
                        className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl bg-blue-600 text-white text-xs font-semibold hover:bg-blue-700 transition-colors shadow-xs flex-shrink-0 self-start sm:self-center"
                      >
                        So khớp CV của tôi
                        <ArrowRight className="w-3.5 h-3.5" />
                      </Link>
                    </div>
                  );
                })}
              </div>
            )}
            {activeTab === "jobs" && !loading && jobResults.length === 0 && (
              <div className="rounded-2xl border border-dashed border-slate-300 bg-white p-8 text-center text-sm text-slate-500">
                Chưa tìm thấy vị trí phù hợp. Hãy thử dùng từ khóa khác.
              </div>
            )}
          </div>
        )}

      </div>
    </div>
  );
}
