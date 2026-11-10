import Link from "next/link";
import { Database, Cpu, Network } from "lucide-react";

export default function Footer() {
  return (
    <footer className="border-t border-slate-200 bg-white py-10 text-xs text-slate-500">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
          <div className="md:col-span-2 space-y-3">
            <h3 className="text-sm font-bold text-slate-800">
              Đề tài Khóa luận / Đồ án Chuyên ngành
            </h3>
            <p className="text-slate-500 max-w-lg leading-relaxed">
              Ứng dụng kết hợp Đồ thị tri thức (Knowledge Graph - Neo4j) và
              Vector Embedding (all-MiniLM-L6-v2 + pgvector) trong so khớp kỹ
              năng và hỗ trợ phát triển kỹ năng nghề nghiệp trên ngữ liệu tiếng
              Việt.
            </p>
            <div className="flex flex-wrap items-center gap-4 pt-2 text-[11px] text-slate-400">
              <span className="flex items-center gap-1">
                <Database className="h-3.5 w-3.5 text-blue-500" /> PostgreSQL 16
                + pgvector
              </span>
              <span className="flex items-center gap-1">
                <Network className="h-3.5 w-3.5 text-emerald-500" /> Neo4j LPG
                Graph
              </span>
              <span className="flex items-center gap-1">
                <Cpu className="h-3.5 w-3.5 text-violet-500" /> FastAPI + MiniLM
                384d
              </span>
            </div>
          </div>

          <div>
            <h4 className="font-semibold text-slate-800 mb-3">
              3 Bài toán Khoa học
            </h4>
            <ul className="space-y-2 text-slate-500">
              <li>
                <Link
                  href="/candidate/match"
                  className="hover:text-blue-600 transition"
                >
                  1. So khớp 1 CV vs 1 JD (Radar 5D)
                </Link>
              </li>
              <li>
                <Link
                  href="/candidate/career-matrix"
                  className="hover:text-blue-600 transition"
                >
                  2. Ma trận 8 Domains & Skill Gap
                </Link>
              </li>
              <li>
                <Link
                  href="/recruiter/hybrid-search"
                  className="hover:text-blue-600 transition"
                >
                  3. Tuyển dụng Hybrid Search (Top-K)
                </Link>
              </li>
            </ul>
          </div>

          <div>
            <h4 className="font-semibold text-slate-800 mb-3">
              Công cụ Nghiên cứu
            </h4>
            <ul className="space-y-2 text-slate-500">
              <li>
                <Link
                  href="/admin/graph-explorer"
                  className="hover:text-blue-600 transition"
                >
                  Neo4j Graph Explorer
                </Link>
              </li>
              <li>
                <Link
                  href="/admin/system-sync"
                  className="hover:text-blue-600 transition"
                >
                  Bảng điều khiển ETL Sync
                </Link>
              </li>
              <li>
                <a
                  href="http://localhost:8080/docs"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="hover:text-blue-600 transition"
                >
                  FastAPI Swagger UI ↗
                </a>
              </li>
            </ul>
          </div>
        </div>

        <div className="mt-8 border-t border-slate-200 pt-6 flex flex-col sm:flex-row justify-between items-center gap-4">
          <p>© 2026 Semantic JobMatch KG Team. Báo cáo đồ án chuyên ngành.</p>
          <p className="text-[11px] text-slate-400">
            Mô hình toán học: Hybrid Multi-Aspect Matching (0.4 Skill + 0.2
            Domain + 0.2 Expertise + 0.1 Exp + 0.1 Qual).
          </p>
        </div>
      </div>
    </footer>
  );
}
