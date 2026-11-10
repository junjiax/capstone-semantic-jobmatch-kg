import Link from "next/link";
import {
  BrainCircuit,
  Network,
  Search,
  ChevronRight,
  Layers,
  TrendingUp,
  Users,
  ArrowRight,
  CheckCircle2,
  Sparkles,
  Database,
  GitMerge,
} from "lucide-react";

const features = [
  {
    icon: BrainCircuit,
    color: "bg-blue-100 text-blue-600",
    title: "So khớp ngữ nghĩa 1-1",
    desc: "Phân tích CV và JD bằng mô hình embedding tiếng Việt, so khớp 5 chiều: Kỹ năng, Lĩnh vực, Chuyên môn, Kinh nghiệm, Học vấn.",
    href: "/candidate/match",
    badge: "Bài toán 1",
  },
  {
    icon: Layers,
    color: "bg-violet-100 text-violet-600",
    title: "Ma trận định hướng nghề",
    desc: "Heatmap trực quan hóa mức độ phù hợp của ứng viên với 8 Domain CNTT, gợi ý Top 3 lĩnh vực tiềm năng nhất.",
    href: "/candidate/career-matrix",
    badge: "Bài toán 2",
  },
  {
    icon: Search,
    color: "bg-emerald-100 text-emerald-600",
    title: "Hybrid Search HR thông minh",
    desc: "Kết hợp ANN vector search (pgvector) và graph traversal (Neo4j) để xếp hạng ứng viên tiềm năng cho vị trí tuyển dụng.",
    href: "/recruiter/hybrid-search",
    badge: "Bài toán 3",
  },
];

const techStack = [
  { icon: Network, label: "Neo4j", sub: "Knowledge Graph" },
  { icon: Database, label: "pgvector", sub: "Vector Embedding" },
  { icon: Sparkles, label: "FastAPI", sub: "Python Backend" },
  { icon: GitMerge, label: "Next.js 16", sub: "React Frontend" },
];

const stats = [
  { value: "5 chiều", label: "Phân tích so khớp" },
  { value: "8 Domain", label: "Lĩnh vực CNTT" },
  { value: "Hybrid", label: "Vector + Graph" },
  { value: "Real-time", label: "Cập nhật đồ thị" },
];

export default function HomePage() {
  return (
    <div className="bg-slate-50">
      {/* Hero */}
      <section className="relative overflow-hidden bg-white border-b border-slate-200">
        <div className="absolute inset-0 bg-gradient-to-br from-blue-50 via-white to-violet-50 pointer-events-none" />
        <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20 lg:py-28">
          <div className="max-w-3xl">
            <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-blue-50 border border-blue-200 text-blue-700 text-xs font-medium mb-6">
              <Sparkles className="w-3.5 h-3.5" />
              Capstone Project — Semantic JobMatch
            </div>
            <h1 className="text-4xl sm:text-5xl lg:text-6xl font-bold text-slate-900 leading-tight tracking-tight mb-6">
              Hệ thống so khớp{" "}
              <span className="text-blue-600">việc làm ngữ nghĩa</span> đa tầng
            </h1>
            <p className="text-lg text-slate-500 leading-relaxed mb-8 max-w-2xl">
              Kết hợp sức mạnh của{" "}
              <strong className="text-slate-700">Knowledge Graph Neo4j</strong>{" "}
              và{" "}
              <strong className="text-slate-700">
                Vector Embedding (pgvector)
              </strong>{" "}
              để phân tích CV, so khớp JD và định hướng nghề nghiệp trên ngữ
              liệu tiếng Việt.
            </p>
            <div className="flex flex-wrap gap-3">
              <Link
                href="/candidate/match"
                className="inline-flex items-center gap-2 px-6 py-3 rounded-xl bg-blue-600 text-white font-semibold hover:bg-blue-700 transition-colors shadow-md hover:shadow-lg"
              >
                Thử nghiệm ngay
                <ArrowRight className="w-4 h-4" />
              </Link>
              <Link
                href="/admin/graph-explorer"
                className="inline-flex items-center gap-2 px-6 py-3 rounded-xl bg-white text-slate-700 font-semibold border border-slate-200 hover:border-slate-300 hover:bg-slate-50 transition-colors shadow-sm"
              >
                <Network className="w-4 h-4" />
                Graph Explorer
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* Stats bar */}
      <section className="bg-white border-b border-slate-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-2 lg:grid-cols-4 divide-x divide-y lg:divide-y-0 divide-slate-200">
            {stats.map((s) => (
              <div key={s.label} className="px-8 py-6 text-center">
                <div className="text-2xl font-bold text-blue-600">{s.value}</div>
                <div className="text-sm text-slate-500 mt-1">{s.label}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Features */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20">
        <div className="text-center mb-12">
          <h2 className="text-3xl font-bold text-slate-900 mb-3">
            Ba bài toán cốt lõi
          </h2>
          <p className="text-slate-500 max-w-xl mx-auto">
            Giải quyết toàn bộ luồng từ ứng viên, nhà tuyển dụng đến quản trị
            hệ thống tri thức.
          </p>
        </div>
        <div className="grid md:grid-cols-3 gap-6">
          {features.map((f) => (
            <Link
              key={f.href}
              href={f.href}
              className="group bg-white rounded-2xl shadow-sm border border-slate-200 p-6 hover:shadow-md hover:border-slate-300 transition-all"
            >
              <div className="flex items-start justify-between mb-4">
                <div className={`p-2.5 rounded-xl ${f.color}`}>
                  <f.icon className="w-5 h-5" />
                </div>
                <span className="text-xs font-semibold text-slate-400 bg-slate-100 px-2.5 py-1 rounded-full">
                  {f.badge}
                </span>
              </div>
              <h3 className="font-semibold text-slate-900 mb-2 group-hover:text-blue-600 transition-colors">
                {f.title}
              </h3>
              <p className="text-sm text-slate-500 leading-relaxed mb-4">
                {f.desc}
              </p>
              <div className="flex items-center gap-1 text-blue-600 text-sm font-medium">
                Khám phá
                <ChevronRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
              </div>
            </Link>
          ))}
        </div>
      </section>

      {/* Tech Stack */}
      <section className="bg-white border-t border-b border-slate-200 py-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-10">
            <h2 className="text-2xl font-bold text-slate-900 mb-2">
              Công nghệ sử dụng
            </h2>
            <p className="text-slate-500 text-sm">
              Stack hiện đại, production-ready
            </p>
          </div>
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            {techStack.map((t) => (
              <div
                key={t.label}
                className="flex flex-col items-center gap-3 p-6 bg-slate-50 rounded-2xl border border-slate-200 hover:border-blue-200 hover:bg-blue-50 transition-colors group"
              >
                <div className="p-3 bg-white rounded-xl shadow-sm border border-slate-200 group-hover:border-blue-200">
                  <t.icon className="w-6 h-6 text-blue-600" />
                </div>
                <div className="text-center">
                  <div className="font-semibold text-slate-900 text-sm">
                    {t.label}
                  </div>
                  <div className="text-xs text-slate-500">{t.sub}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Portals */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20">
        <div className="grid md:grid-cols-3 gap-6">
          {[
            {
              icon: Users,
              color: "text-blue-600",
              bg: "bg-blue-50",
              title: "Ứng viên",
              desc: "Upload CV, xem điểm so khớp 5 chiều, lộ trình học tập được cá nhân hóa.",
              links: [
                { label: "Upload & Phân tích CV", href: "/candidate/upload" },
                { label: "So khớp 1-1 với JD", href: "/candidate/match" },
                { label: "Ma trận nghề nghiệp", href: "/candidate/career-matrix" },
              ],
            },
            {
              icon: Search,
              color: "text-emerald-600",
              bg: "bg-emerald-50",
              title: "Nhà tuyển dụng",
              desc: "Đăng JD, tìm ứng viên tiềm năng bằng Hybrid Search, xem giải thích AI.",
              links: [
                { label: "Quản lý tin tuyển dụng", href: "/recruiter/jobs" },
                { label: "Tìm ứng viên thông minh", href: "/recruiter/hybrid-search" },
              ],
            },
            {
              icon: Network,
              color: "text-violet-600",
              bg: "bg-violet-50",
              title: "Admin Lab",
              desc: "Khám phá đồ thị tri thức, đồng bộ dữ liệu ETL, quản trị hệ thống.",
              links: [
                { label: "Knowledge Graph Explorer", href: "/admin/graph-explorer" },
                { label: "Đồng bộ ETL", href: "/admin/system-sync" },
              ],
            },
          ].map((portal) => (
            <div
              key={portal.title}
              className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6"
            >
              <div className={`inline-flex p-2.5 rounded-xl ${portal.bg} mb-4`}>
                <portal.icon className={`w-5 h-5 ${portal.color}`} />
              </div>
              <h3 className="font-bold text-slate-900 mb-2">
                Phân hệ {portal.title}
              </h3>
              <p className="text-sm text-slate-500 mb-4 leading-relaxed">
                {portal.desc}
              </p>
              <ul className="space-y-2">
                {portal.links.map((l) => (
                  <li key={l.href}>
                    <Link
                      href={l.href}
                      className="flex items-center gap-2 text-sm text-slate-700 hover:text-blue-600 transition-colors"
                    >
                      <CheckCircle2 className="w-3.5 h-3.5 text-slate-300 flex-shrink-0" />
                      {l.label}
                    </Link>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      </section>

      {/* CTA */}
      <section className="bg-blue-600 py-16">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <TrendingUp className="w-10 h-10 text-blue-200 mx-auto mb-4" />
          <h2 className="text-3xl font-bold text-white mb-3">
            Bắt đầu phân tích hồ sơ của bạn
          </h2>
          <p className="text-blue-200 mb-8 max-w-lg mx-auto">
            Upload CV và nhận ngay đánh giá toàn diện từ hệ thống đồ thị tri
            thức kết hợp AI.
          </p>
          <div className="flex flex-wrap justify-center gap-3">
            <Link
              href="/candidate/match"
              className="inline-flex items-center gap-2 px-6 py-3 rounded-xl bg-white text-blue-600 font-semibold hover:bg-blue-50 transition-colors shadow-md"
            >
              <BrainCircuit className="w-4 h-4" />
              Thử so khớp ngay
            </Link>
            <Link
              href="/admin/graph-explorer"
              className="inline-flex items-center gap-2 px-6 py-3 rounded-xl bg-blue-700 text-white font-semibold hover:bg-blue-800 transition-colors border border-blue-500"
            >
              Xem đồ thị tri thức
            </Link>
          </div>
        </div>
      </section>
    </div>
  );
}
