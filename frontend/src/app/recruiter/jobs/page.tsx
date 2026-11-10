"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  AlertCircle,
  Briefcase,
  ChevronLeft,
  ChevronRight,
  RefreshCw,
  Search,
  Sparkles,
} from "lucide-react";
import apiClient from "@/lib/api";

interface Job {
  id: number;
  title: string;
  domain?: string;
  expertise?: string;
  experience?: number;
  createdAt: string;
}

export default function RecruiterJobsPage() {
  const PAGE_SIZE = 20;
  const [jobs, setJobs] = useState<Job[]>([]);
  const [currentPage, setCurrentPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const loadJobs = async () => {
    setLoading(true);
    setErrorMsg(null);
    try {
      const response = await apiClient.get("/jd/available");
      setJobs(response.data?.data || []);
      setCurrentPage(1);
    } catch (err: unknown) {
      const axiosErr = err as { response?: { data?: { detail?: string } } };
      setErrorMsg(axiosErr.response?.data?.detail || "Không thể tải tin tuyển dụng từ backend.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void loadJobs();
  }, []);

  const totalPages = Math.max(1, Math.ceil(jobs.length / PAGE_SIZE));
  const visibleJobs = jobs.slice(
    (currentPage - 1) * PAGE_SIZE,
    currentPage * PAGE_SIZE,
  );

  return (
    <div className="min-h-screen bg-slate-50">
      <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
        <div className="mb-8 flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <span className="mb-2 inline-flex items-center gap-1.5 text-xs font-bold uppercase tracking-wider text-blue-600">
              <Sparkles className="h-3.5 w-3.5" />
              Phân hệ Nhà tuyển dụng
            </span>
            <h1 className="text-3xl font-bold text-slate-900">Tin tuyển dụng hiện có</h1>
            <p className="mt-1 text-sm text-slate-500">
              Danh sách được đọc trực tiếp từ bảng JD trong PostgreSQL.
            </p>
          </div>
          <button
            onClick={() => void loadJobs()}
            disabled={loading}
            className="inline-flex items-center gap-2 rounded-xl bg-blue-600 px-4 py-2.5 text-sm font-semibold text-white shadow-sm transition hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-60"
          >
            <RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} />
            Làm mới dữ liệu
          </button>
        </div>

        {errorMsg && (
          <div className="mb-6 flex items-start gap-2 rounded-xl border border-rose-200 bg-rose-50 p-4 text-sm text-rose-800">
            <AlertCircle className="mt-0.5 h-4 w-4 shrink-0 text-rose-500" />
            <span>{errorMsg}</span>
          </div>
        )}

        <div className="mb-6 grid grid-cols-1 gap-4 sm:grid-cols-3">
          <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
            <div className="text-xs font-semibold text-slate-500">Tin tuyển dụng</div>
            <div className="mt-2 text-3xl font-bold text-slate-900">{jobs.length}</div>
            <div className="mt-1 text-xs text-slate-400">Đang có trên hệ thống</div>
          </div>
          <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
            <div className="text-xs font-semibold text-slate-500">Thuật toán</div>
            <div className="mt-2 text-xl font-bold text-violet-700">Tìm kiếm thông minh</div>
            <div className="mt-1 text-xs text-slate-400">Ưu tiên hồ sơ phù hợp</div>
          </div>
          <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
            <div className="text-xs font-semibold text-slate-500">Thao tác</div>
            <div className="mt-2 text-xl font-bold text-emerald-700">Sàng lọc ứng viên</div>
            <div className="mt-1 text-xs text-slate-400">Sẵn sàng tìm kiếm</div>
          </div>
        </div>

        <div className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
          <div className="flex items-center justify-between border-b border-slate-200 px-6 py-4">
            <h2 className="text-sm font-bold text-slate-900">Danh sách JD</h2>
            <span className="text-xs text-slate-400">{jobs.length} tin</span>
          </div>
          {loading ? (
            <div className="flex items-center justify-center gap-2 p-16 text-sm text-slate-500">
              <RefreshCw className="h-4 w-4 animate-spin" /> Đang tải dữ liệu thật...
            </div>
          ) : jobs.length === 0 ? (
            <div className="p-16 text-center">
              <Briefcase className="mx-auto mb-3 h-10 w-10 text-slate-300" />
              <p className="font-semibold text-slate-700">Chưa có tin tuyển dụng trong database</p>
              <p className="mt-1 text-sm text-slate-500">Chức năng tạo JD chưa có API backend nên đã được ẩn.</p>
            </div>
          ) : (
            <div className="divide-y divide-slate-100">
              {visibleJobs.map((job) => (
                <div key={job.id} className="flex flex-col gap-4 px-6 py-5 sm:flex-row sm:items-center sm:justify-between">
                  <div>
                    <div className="font-semibold text-slate-900">{job.title}</div>
                    <div className="mt-1 text-sm text-slate-500">
                      #{job.id} · {job.domain || "Chưa phân loại"} · {job.expertise || "Chưa xác định"}
                      {job.experience != null ? ` · ${job.experience} năm kinh nghiệm` : ""}
                    </div>
                  </div>
                  <Link
                    href={`/recruiter/hybrid-search?jobId=${job.id}`}
                    className="inline-flex items-center justify-center gap-2 rounded-lg border border-blue-200 px-3 py-2 text-sm font-semibold text-blue-700 transition hover:bg-blue-50"
                  >
                    <Search className="h-4 w-4" /> Tìm ứng viên
                  </Link>
                </div>
              ))}
            </div>
          )}
          {!loading && jobs.length > PAGE_SIZE && (
            <div className="flex items-center justify-between border-t border-slate-200 px-6 py-4">
              <span className="text-xs text-slate-500">
                Trang {currentPage}/{totalPages} · Hiển thị tối đa {PAGE_SIZE} tin mỗi trang
              </span>
              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={() => setCurrentPage((page) => Math.max(1, page - 1))}
                  disabled={currentPage === 1}
                  className="inline-flex items-center gap-1 rounded-lg border border-slate-200 px-3 py-2 text-sm font-semibold text-slate-700 transition hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-40"
                >
                  <ChevronLeft className="h-4 w-4" />
                  Trước
                </button>
                <button
                  type="button"
                  onClick={() => setCurrentPage((page) => Math.min(totalPages, page + 1))}
                  disabled={currentPage === totalPages}
                  className="inline-flex items-center gap-1 rounded-lg border border-slate-200 px-3 py-2 text-sm font-semibold text-slate-700 transition hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-40"
                >
                  Sau
                  <ChevronRight className="h-4 w-4" />
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
