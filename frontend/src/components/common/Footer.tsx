import Link from "next/link";

export default function Footer() {
  return (
    <footer className="border-t border-slate-200 bg-white py-10 text-xs text-slate-500">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
          <div className="md:col-span-2 space-y-3">
            <h3 className="text-sm font-bold text-slate-800">
              JobMatch
            </h3>
            <p className="text-slate-500 max-w-lg leading-relaxed">
              Nền tảng hỗ trợ ứng viên tìm cơ hội phù hợp và giúp nhà tuyển dụng tuyển người hiệu quả hơn.
            </p>
          </div>

          <div>
            <h4 className="font-semibold text-slate-800 mb-3">
            Dành cho bạn
            </h4>
            <ul className="space-y-2 text-slate-500">
              <li>
                <Link
                  href="/candidate/match"
                  className="hover:text-blue-600 transition"
                >
                  Đánh giá mức độ phù hợp
                </Link>
              </li>
              <li>
                <Link
                  href="/recruiter/hybrid-search"
                  className="hover:text-blue-600 transition"
                >
                  Tìm ứng viên tiềm năng
                </Link>
              </li>
            </ul>
          </div>

          <div>
            <h4 className="font-semibold text-slate-800 mb-3">
              Khám phá thêm
            </h4>
            <ul className="space-y-2 text-slate-500">
              <li>
                <Link
                  href="/admin/graph-explorer"
                  className="hover:text-blue-600 transition"
                >
                  Khám phá dữ liệu
                </Link>
              </li>
              <li>
                <Link
                  href="/admin/system-sync"
                  className="hover:text-blue-600 transition"
                >
                  Quản trị hệ thống
                </Link>
              </li>
            </ul>
          </div>
        </div>

        <div className="mt-8 border-t border-slate-200 pt-6 flex flex-col sm:flex-row justify-between items-center gap-4">
          <p>© 2026 JobMatch. Kết nối đúng người với đúng cơ hội.</p>
          <p className="text-[11px] text-slate-400">Đơn giản hơn cho ứng viên, hiệu quả hơn cho nhà tuyển dụng.</p>
        </div>
      </div>
    </footer>
  );
}
