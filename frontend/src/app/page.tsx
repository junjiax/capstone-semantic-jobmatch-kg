import Link from "next/link";
import {
  ArrowRight,
  BrainCircuit,
  CheckCircle2,
  FileText,
  Search,
  ShieldCheck,
  Sparkles,
  TrendingUp,
  Users,
  Upload,
} from "lucide-react";

const highlights = [
  {
    icon: BrainCircuit,
    title: "Hiểu đúng năng lực",
    description: "Đọc CV và tin tuyển dụng theo ngữ cảnh, không chỉ dựa vào từ khóa.",
    color: "bg-blue-100 text-blue-600",
  },
  {
    icon: TrendingUp,
    title: "Ra quyết định nhanh",
    description: "Nhìn thấy mức độ phù hợp, điểm mạnh và khoảng cách kỹ năng trong một lần xem.",
    color: "bg-emerald-100 text-emerald-600",
  },
  {
    icon: ShieldCheck,
    title: "Minh bạch, dễ giải thích",
    description: "Kết quả có lý do rõ ràng để ứng viên và nhà tuyển dụng cùng tin tưởng.",
    color: "bg-violet-100 text-violet-600",
  },
];

const steps = [
  { number: "01", title: "Tải hồ sơ hoặc chọn vị trí", description: "Bắt đầu bằng CV của bạn hoặc một tin tuyển dụng đang cần tìm người." },
  { number: "02", title: "Phân tích mức độ phù hợp", description: "Hệ thống đối chiếu kỹ năng, kinh nghiệm, lĩnh vực và yêu cầu công việc." },
  { number: "03", title: "Chọn bước tiếp theo", description: "Nhận gợi ý rõ ràng để ứng tuyển, bổ sung kỹ năng hoặc shortlist ứng viên." },
];

export default function HomePage() {
  return (
    <main className="overflow-hidden bg-slate-50 text-slate-900">
      <section className="relative isolate">
        <div className="absolute inset-0 -z-10 bg-[radial-gradient(circle_at_top_right,_#dbeafe,_transparent_42%),linear-gradient(135deg,_#ffffff_0%,_#f8fafc_55%,_#eef2ff_100%)]" />
        <div className="absolute -right-32 top-20 -z-10 h-80 w-80 rounded-full bg-blue-200/30 blur-3xl" />
        <div className="mx-auto grid max-w-7xl items-center gap-12 px-4 py-20 sm:px-6 lg:grid-cols-[1.05fr_.95fr] lg:px-8 lg:py-28">
          <div>
            <div className="mb-6 inline-flex items-center gap-2 rounded-full border border-blue-200 bg-white/80 px-3.5 py-2 text-sm font-semibold text-blue-700 shadow-sm">
              <Sparkles className="h-4 w-4" />
              Kết nối đúng người với đúng cơ hội
            </div>
            <h1 className="max-w-3xl text-4xl font-extrabold leading-tight tracking-tight sm:text-6xl">
              Tìm công việc phù hợp.
              <span className="block text-blue-600">Tuyển đúng người.</span>
            </h1>
            <p className="mt-6 max-w-2xl text-lg leading-8 text-slate-600">
              JobMatch giúp ứng viên hiểu rõ cơ hội phù hợp và giúp nhà tuyển dụng tìm ra những hồ sơ đáng chú ý nhanh hơn.
            </p>
            <div className="mt-8 flex flex-wrap gap-3">
              <Link href="/candidate/upload" className="inline-flex items-center gap-2 rounded-xl bg-blue-600 px-5 py-3.5 font-bold text-white shadow-lg shadow-blue-600/20 transition hover:-translate-y-0.5 hover:bg-blue-700">
                <Upload className="h-4 w-4" />
                Phân tích CV của tôi
                <ArrowRight className="h-4 w-4" />
              </Link>
              <Link href="/recruiter/hybrid-search" className="inline-flex items-center gap-2 rounded-xl border border-slate-200 bg-white px-5 py-3.5 font-bold text-slate-700 shadow-sm transition hover:-translate-y-0.5 hover:border-blue-300 hover:text-blue-700">
                <Search className="h-4 w-4" />
                Tìm ứng viên
              </Link>
            </div>
            <div className="mt-8 flex flex-wrap gap-x-6 gap-y-2 text-sm text-slate-500">
              {["Phân tích theo ngữ cảnh", "Kết quả dễ hiểu", "Bảo mật thông tin"].map((item) => (
                <span key={item} className="inline-flex items-center gap-2">
                  <CheckCircle2 className="h-4 w-4 text-emerald-500" /> {item}
                </span>
              ))}
            </div>
          </div>
          <div className="relative mx-auto w-full max-w-md">
            <div className="absolute -inset-4 rounded-[2rem] bg-blue-600/10 blur-2xl" />
            <div className="relative rounded-[2rem] border border-white bg-white/90 p-5 shadow-2xl shadow-slate-300/50 backdrop-blur">
              <div className="flex items-center justify-between border-b border-slate-100 pb-4">
                <div>
                  <p className="text-xs font-semibold uppercase tracking-wider text-slate-400">Tổng quan phù hợp</p>
                  <p className="mt-1 text-lg font-bold">Ứng viên & vị trí</p>
                </div>
                <div className="rounded-xl bg-emerald-50 px-3 py-2 text-right">
                  <div className="text-2xl font-extrabold text-emerald-600">86%</div>
                  <div className="text-[11px] font-semibold text-emerald-700">Phù hợp cao</div>
                </div>
              </div>
              <div className="mt-5 space-y-4">
                {[
                  ["Kỹ năng chuyên môn", "92%", "bg-blue-500"],
                  ["Kinh nghiệm", "84%", "bg-emerald-500"],
                  ["Lĩnh vực phù hợp", "79%", "bg-violet-500"],
                ].map(([label, value, color]) => (
                  <div key={label}>
                    <div className="mb-1.5 flex justify-between text-sm font-semibold">
                      <span>{label}</span><span className="text-slate-500">{value}</span>
                    </div>
                    <div className="h-2 rounded-full bg-slate-100">
                      <div className={`h-2 rounded-full ${color}`} style={{ width: value }} />
                    </div>
                  </div>
                ))}
              </div>
              <div className="mt-6 rounded-xl bg-slate-50 p-4">
                <div className="flex items-center gap-2 text-sm font-bold"><Sparkles className="h-4 w-4 text-blue-600" /> Gợi ý tiếp theo</div>
                <p className="mt-2 text-sm leading-6 text-slate-600">Hồ sơ nổi bật nhờ kỹ năng phân tích dữ liệu và kinh nghiệm thực tế.</p>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section className="border-y border-slate-200 bg-white">
        <div className="mx-auto grid max-w-7xl gap-6 px-4 py-7 sm:grid-cols-3 sm:px-6 lg:px-8">
          {[["5+", "góc nhìn đánh giá"], ["Nhanh hơn", "khi sàng lọc hồ sơ"], ["Dễ hiểu", "cho mọi người dùng"]].map(([value, label]) => (
            <div key={label} className="text-center sm:border-r sm:border-slate-200 last:border-0">
              <div className="text-2xl font-extrabold text-blue-600">{value}</div>
              <div className="mt-1 text-sm text-slate-500">{label}</div>
            </div>
          ))}
        </div>
      </section>

      <section className="mx-auto max-w-7xl px-4 py-20 sm:px-6 lg:px-8">
        <div className="mx-auto max-w-2xl text-center">
          <p className="text-sm font-bold uppercase tracking-widest text-blue-600">Một trải nghiệm đơn giản hơn</p>
          <h2 className="mt-3 text-3xl font-extrabold tracking-tight sm:text-4xl">Mọi quyết định bắt đầu từ sự phù hợp</h2>
          <p className="mt-4 text-slate-600">Tập trung vào điều quan trọng nhất: năng lực, cơ hội và bước tiến tiếp theo.</p>
        </div>
        <div className="mt-12 grid gap-5 md:grid-cols-3">
          {highlights.map((item) => (
            <div key={item.title} className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm transition hover:-translate-y-1 hover:shadow-lg">
              <div className={`mb-5 inline-flex rounded-xl p-3 ${item.color}`}><item.icon className="h-6 w-6" /></div>
              <h3 className="text-lg font-bold">{item.title}</h3>
              <p className="mt-2 leading-7 text-slate-600">{item.description}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="bg-white py-20">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="grid gap-12 lg:grid-cols-[.8fr_1.2fr] lg:items-center">
            <div>
              <p className="text-sm font-bold uppercase tracking-widest text-emerald-600">Bắt đầu thật dễ</p>
              <h2 className="mt-3 text-3xl font-extrabold tracking-tight sm:text-4xl">Từ hồ sơ đến quyết định chỉ trong vài bước</h2>
              <p className="mt-4 leading-7 text-slate-600">Không cần hiểu thuật toán. Bạn chỉ cần chọn mục tiêu, phần còn lại để JobMatch hỗ trợ.</p>
            </div>
            <div className="grid gap-4 sm:grid-cols-3">
              {steps.map((step) => (
                <div key={step.number} className="rounded-2xl border border-slate-200 bg-slate-50 p-5">
                  <div className="text-3xl font-black text-blue-200">{step.number}</div>
                  <h3 className="mt-4 font-bold">{step.title}</h3>
                  <p className="mt-2 text-sm leading-6 text-slate-600">{step.description}</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      <section className="bg-blue-600 py-16">
        <div className="mx-auto max-w-4xl px-4 text-center sm:px-6 lg:px-8">
          <h2 className="text-3xl font-extrabold text-white sm:text-4xl">Sẵn sàng tìm đúng cơ hội?</h2>
          <p className="mx-auto mt-4 max-w-xl leading-7 text-blue-100">Tải CV hoặc bắt đầu tìm kiếm ứng viên ngay hôm nay.</p>
          <div className="mt-8 flex flex-wrap justify-center gap-3">
            <Link href="/candidate/upload" className="inline-flex items-center gap-2 rounded-xl bg-white px-5 py-3.5 font-bold text-blue-700 transition hover:bg-blue-50"><FileText className="h-4 w-4" />Tải CV ngay</Link>
            <Link href="/recruiter/hybrid-search" className="inline-flex items-center gap-2 rounded-xl border border-blue-400 bg-blue-700 px-5 py-3.5 font-bold text-white transition hover:bg-blue-800"><Users className="h-4 w-4" />Dành cho nhà tuyển dụng</Link>
          </div>
        </div>
      </section>
    </main>
  );
}
