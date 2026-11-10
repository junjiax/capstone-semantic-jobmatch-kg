"use client";

import { useState, useRef } from "react";
import Link from "next/link";
import {
  UploadCloud,
  FileText,
  CheckCircle2,
  X,
  Plus,
  Sparkles,
  RefreshCw,
  Search,
  ArrowRight,
  Database,
  Award,
  Layers,
  GraduationCap,
  Briefcase,
} from "lucide-react";
import apiClient from "@/lib/api";

import { useAuth } from "@/context/AuthContext";

interface ExtractedCV {
  id: number;
  fullName: string;
  email: string;
  phone: string;
  domain: string;
  expertise: string;
  experienceYears: number;
  educationLevel: string;
  skills: string[];
}

const PROGRESS_STEPS = [
  "Đang tải file CV lên hệ thống...",
  "Đang đọc nội dung và cấu trúc tài liệu...",
  "Đang trích xuất thực thể bằng AI (NLP/NER)...",
  "Đang ánh xạ vào Đồ thị tri thức Neo4j...",
  "Hoàn tất bóc tách hồ sơ!",
];

export default function CandidateUploadPage() {
  const { user } = useAuth();
  const [isDragging, setIsDragging] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [stepIndex, setStepIndex] = useState(0);
  const [extractedData, setExtractedData] = useState<ExtractedCV | null>(null);
  const [newSkillInput, setNewSkillInput] = useState("");
  const [skillSuggestions, setSkillSuggestions] = useState<string[]>([]);
  const [isSearchingSkill, setIsSearchingSkill] = useState(false);
  const [isSaved, setIsSaved] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const startProcessing = async (file?: File) => {
    setUploading(true);
    setProgress(15);
    setStepIndex(0);
    try {
      if (!file) return;
      const body = new FormData();
      body.append("file", file);
      const res = await apiClient.post("/profile/upload", body, {
        headers: { "Content-Type": "multipart/form-data" },
        timeout: 120000,
      });
      const data = res.data?.data;
      if (!data?.id) throw new Error("Backend không trả về CV ID.");
      setProgress(100);
      setStepIndex(4);
      setExtractedData(data);
      localStorage.setItem("last_cv_id", String(data.id));
    } catch (err: unknown) {
      const axiosErr = err as { response?: { data?: { detail?: string } } };
      setExtractedData(null);
      alert(axiosErr.response?.data?.detail || "Không thể tải CV lên. Vui lòng thử lại.");
    } finally {
      setUploading(false);
    }
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      startProcessing(e.dataTransfer.files[0]);
    }
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      startProcessing(e.target.files[0]);
    }
  };

  const handleRemoveSkill = (skillToRemove: string) => {
    if (!extractedData) return;
    setExtractedData({
      ...extractedData,
      skills: extractedData.skills.filter((s) => s !== skillToRemove),
    });
  };

  const handleAddSkill = (skillToAdd: string) => {
    const trimmed = skillToAdd.trim();
    if (!trimmed || !extractedData) return;
    if (!extractedData.skills.includes(trimmed)) {
      setExtractedData({
        ...extractedData,
        skills: [...extractedData.skills, trimmed],
      });
    }
    setNewSkillInput("");
    setSkillSuggestions([]);
  };

  const handleSkillInputChange = async (val: string) => {
    setNewSkillInput(val);
    if (val.trim().length >= 2) {
      setIsSearchingSkill(true);
      try {
        const res = await apiClient.post("/semantic-search/skills", {
          query: val,
          top_k: 5,
        });
        const results = res.data?.data?.results || [];
        setSkillSuggestions(results.map((s: { title: string }) => s.title));
      } catch {
        setSkillSuggestions([]);
      } finally {
        setIsSearchingSkill(false);
      }
    } else {
      setSkillSuggestions([]);
    }
  };

  const handleSaveProfile = async () => {
    if (!extractedData) return;
    try {
      await apiClient.patch(`/profile/${extractedData.id}`, {
        title: extractedData.fullName,
        skills: extractedData.skills,
      });
      setIsSaved(true);
      setTimeout(() => setIsSaved(false), 3000);
    } catch (err: unknown) {
      const axiosErr = err as { response?: { data?: { detail?: string } } };
      alert(axiosErr.response?.data?.detail || "Không thể lưu thay đổi hồ sơ.");
    }
  };

  return (
    <div className="bg-slate-50 min-h-screen">
      <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-8">

        {/* Page Header */}
        <div className="mb-8">
          <span className="inline-flex items-center gap-1.5 text-xs font-bold text-blue-600 tracking-wider uppercase mb-2">
            <Sparkles className="h-3.5 w-3.5" />
            Phân hệ Ứng viên — Bóc tách & Chuẩn hóa Hồ sơ
          </span>
          <h1 className="text-3xl font-bold text-slate-900">
            Tải Lên & Quản Lý Hồ Sơ Năng Lực (CV)
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            Bóc tách thực thể tự động bằng NLP, đồng bộ trực tiếp vào Đồ thị tri thức Neo4j và hỗ trợ kiểm duyệt Human-in-the-loop.
          </p>
        </div>

        {/* Upload Dropzone */}
        {!extractedData && (
          <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-8 mb-8">
            <input
              type="file"
              ref={fileInputRef}
              onChange={handleFileSelect}
              accept=".pdf,.docx,.doc"
              className="hidden"
            />
            <div
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onDrop={handleDrop}
              onClick={() => fileInputRef.current?.click()}
              className={`border-2 border-dashed rounded-2xl p-12 text-center cursor-pointer transition-all ${
                isDragging
                  ? "border-blue-500 bg-blue-50/80 scale-[1.01]"
                  : "border-slate-300 hover:border-blue-400 hover:bg-slate-50/60"
              }`}
            >
              <div className="w-16 h-16 rounded-2xl bg-blue-50 text-blue-600 flex items-center justify-center mx-auto mb-4 border border-blue-100 shadow-sm">
                <UploadCloud className="w-8 h-8" />
              </div>
              <h3 className="text-lg font-bold text-slate-900 mb-1">
                Kéo thả file CV (PDF hoặc DOCX) vào đây
              </h3>
              <p className="text-sm text-slate-500 mb-4">
                hoặc click để chọn file từ máy tính (Dung lượng tối đa 10MB)
              </p>
              <div className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-blue-600 text-white text-sm font-semibold hover:bg-blue-700 transition-colors shadow-sm">
                <FileText className="w-4 h-4" />
                Chọn file CV
              </div>
            </div>

            {/* Real-time processing progress */}
            {uploading && (
              <div className="mt-6 p-6 bg-slate-50 rounded-2xl border border-slate-200">
                <div className="flex items-center justify-between text-sm font-semibold text-slate-700 mb-2">
                  <span className="flex items-center gap-2 text-blue-600">
                    <RefreshCw className="w-4 h-4 animate-spin" />
                    {PROGRESS_STEPS[stepIndex]}
                  </span>
                  <span>{progress}%</span>
                </div>
                <div className="h-2.5 bg-slate-200 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-blue-600 rounded-full transition-all duration-300"
                    style={{ width: `${progress}%` }}
                  />
                </div>
              </div>
            )}
          </div>
        )}

        {/* Human-in-the-loop CV Review & Editing Panel */}
        {extractedData && (
          <div className="space-y-6">
            {/* Success banner */}
            <div className="bg-emerald-50 border border-emerald-200 rounded-2xl p-4 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="w-9 h-9 rounded-xl bg-emerald-100 text-emerald-600 flex items-center justify-center flex-shrink-0">
                  <CheckCircle2 className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="font-bold text-emerald-900 text-sm">
                    Bóc tách CV thành công! (CV ID: #{extractedData.id})
                  </h3>
                  <p className="text-xs text-emerald-700">
                    Dữ liệu đã được ánh xạ vào Knowledge Graph. Bạn có thể kiểm tra và chỉnh sửa lại các thông tin bên dưới.
                  </p>
                </div>
              </div>
              <button
                onClick={() => setExtractedData(null)}
                className="text-xs text-slate-500 hover:text-slate-800 underline px-2 py-1"
              >
                Upload lại file khác
              </button>
            </div>

            {/* Profile Overview Card */}
            <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6">
              <h2 className="text-lg font-bold text-slate-900 mb-4 flex items-center gap-2">
                <FileText className="w-5 h-5 text-blue-600" />
                Thông tin chung ứng viên
              </h2>
              <div className="grid sm:grid-cols-2 gap-4 text-sm">
                <div>
                  <label className="block text-xs font-semibold text-slate-500 mb-1">Họ và tên</label>
                  <input
                    type="text"
                    value={extractedData.fullName}
                    onChange={(e) =>
                      setExtractedData({ ...extractedData, fullName: e.target.value })
                    }
                    className="w-full px-3 py-2 rounded-lg border border-slate-200 bg-slate-50 text-slate-900 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-500 mb-1">Email</label>
                  <input
                    type="email"
                    value={extractedData.email}
                    onChange={(e) =>
                      setExtractedData({ ...extractedData, email: e.target.value })
                    }
                    className="w-full px-3 py-2 rounded-lg border border-slate-200 bg-slate-50 text-slate-900 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-500 mb-1">Lĩnh vực (Domain)</label>
                  <div className="flex items-center gap-2 px-3 py-2 rounded-lg border border-slate-200 bg-slate-50 text-slate-900">
                    <Layers className="w-4 h-4 text-blue-600" />
                    <span>{extractedData.domain}</span>
                  </div>
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-500 mb-1">Chuyên môn (Expertise)</label>
                  <div className="flex items-center gap-2 px-3 py-2 rounded-lg border border-slate-200 bg-slate-50 text-slate-900">
                    <Database className="w-4 h-4 text-emerald-600" />
                    <span>{extractedData.expertise}</span>
                  </div>
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-500 mb-1">Số năm kinh nghiệm</label>
                  <div className="flex items-center gap-2 px-3 py-2 rounded-lg border border-slate-200 bg-slate-50 text-slate-900">
                    <Briefcase className="w-4 h-4 text-amber-600" />
                    <span>{extractedData.experienceYears} năm</span>
                  </div>
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-500 mb-1">Trình độ học vấn</label>
                  <div className="flex items-center gap-2 px-3 py-2 rounded-lg border border-slate-200 bg-slate-50 text-slate-900">
                    <GraduationCap className="w-4 h-4 text-purple-600" />
                    <span>{extractedData.educationLevel}</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Human-in-the-loop Skill Tagging Card */}
            <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6">
              <div className="flex items-center justify-between mb-4">
                <div>
                  <h2 className="text-lg font-bold text-slate-900 flex items-center gap-2">
                    <Award className="w-5 h-5 text-amber-500" />
                    Kỹ năng bóc tách & Chuẩn hóa ({extractedData.skills.length})
                  </h2>
                  <p className="text-xs text-slate-500 mt-0.5">
                    Click dấu × để xóa, hoặc gõ tên kỹ năng mới bên dưới (có gợi ý từ Knowledge Graph).
                  </p>
                </div>
              </div>

              {/* Skills Badge List */}
              <div className="flex flex-wrap gap-2 mb-6 min-h-[50px] p-3 bg-slate-50 rounded-xl border border-slate-200">
                {extractedData.skills.map((skill) => (
                  <span
                    key={skill}
                    className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-semibold bg-white text-slate-800 border border-slate-300 shadow-xs group"
                  >
                    <span>{skill}</span>
                    <button
                      type="button"
                      onClick={() => handleRemoveSkill(skill)}
                      className="text-slate-400 hover:text-rose-600 hover:bg-rose-50 rounded-full p-0.5 transition-colors"
                      title="Xóa kỹ năng này"
                    >
                      <X className="w-3.5 h-3.5" />
                    </button>
                  </span>
                ))}
              </div>

              {/* Add New Skill with Autocomplete */}
              <div className="relative">
                <label className="block text-xs font-semibold text-slate-600 mb-1.5">
                  Thêm kỹ năng mới (Human-in-the-loop)
                </label>
                <div className="flex gap-2">
                  <div className="relative flex-1">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                    <input
                      type="text"
                      value={newSkillInput}
                      onChange={(e) => handleSkillInputChange(e.target.value)}
                      onKeyDown={(e) => {
                        if (e.key === "Enter") {
                          e.preventDefault();
                          handleAddSkill(newSkillInput);
                        }
                      }}
                      placeholder="Gõ tên kỹ năng (ví dụ: Kubernetes, Kafka, CI/CD)..."
                      className="w-full pl-9 pr-4 py-2 rounded-lg border border-slate-200 bg-slate-50 text-slate-900 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                    {isSearchingSkill && (
                      <RefreshCw className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-blue-500 animate-spin" />
                    )}
                  </div>
                  <button
                    type="button"
                    onClick={() => handleAddSkill(newSkillInput)}
                    className="inline-flex items-center gap-1.5 px-4 py-2 rounded-lg bg-slate-900 text-white text-sm font-semibold hover:bg-slate-800 transition-colors shadow-sm"
                  >
                    <Plus className="w-4 h-4" />
                    Thêm
                  </button>
                </div>

                {/* Autocomplete Dropdown */}
                {skillSuggestions.length > 0 && (
                  <div className="absolute top-full left-0 mt-1 w-full bg-white rounded-xl shadow-lg border border-slate-200 py-1 z-30">
                    <div className="text-[10px] font-bold text-slate-400 uppercase px-3 py-1">
                      Gợi ý từ Ontology Knowledge Graph
                    </div>
                    {skillSuggestions.map((sug) => (
                      <button
                        key={sug}
                        type="button"
                        onClick={() => handleAddSkill(sug)}
                        className="w-full text-left px-3 py-1.5 text-xs text-slate-700 hover:bg-blue-50 hover:text-blue-700 flex items-center justify-between"
                      >
                        <span>{sug}</span>
                        <span className="text-[10px] text-slate-400">Knowledge Graph Node</span>
                      </button>
                    ))}
                  </div>
                )}
              </div>
            </div>

            {/* Action Bar */}
            <div className="flex flex-wrap items-center justify-between gap-4 pt-2">
              <button
                type="button"
                onClick={handleSaveProfile}
                className="inline-flex items-center gap-2 px-6 py-3 rounded-xl bg-blue-600 text-white font-semibold hover:bg-blue-700 transition-colors shadow-md"
              >
                <CheckCircle2 className="w-4 h-4" />
                Lưu & Cập nhật Hồ sơ vào Graph
              </button>

              <div className="flex gap-3">
                <Link
                  href="/candidate/match"
                  className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-white border border-slate-200 text-slate-700 font-semibold hover:bg-slate-50 transition-colors shadow-sm text-sm"
                >
                  Tiến hành So khớp 1-1
                  <ArrowRight className="w-4 h-4" />
                </Link>
              </div>
            </div>

            {isSaved && (
              <div className="p-4 bg-green-50 border border-green-200 rounded-xl text-sm text-green-800 flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 text-green-600" />
                Hồ sơ đã được lưu và cập nhật thành công vào Knowledge Graph Neo4j!
              </div>
            )}
          </div>
        )}

      </div>
    </div>
  );
}
