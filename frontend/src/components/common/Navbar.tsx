"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";
import {
  Menu,
  X,
  BrainCircuit,
  ChevronDown,
  Search,
  User,
  LogOut,
  Shield,
  Briefcase,
  Sparkles,
} from "lucide-react";
import { useAuth } from "@/context/AuthContext";

const navGroups = [
  {
    label: "Ứng viên",
    items: [
      { href: "/candidate/upload", label: "Upload & Bóc tách CV" },
      { href: "/candidate/match", label: "So khớp 1-1 (BT1)" },
      { href: "/candidate/career-matrix", label: "Ma trận nghề nghiệp (BT2)" },
    ],
  },
  {
    label: "Nhà tuyển dụng",
    items: [
      { href: "/recruiter/jobs", label: "Quản lý JD & Trọng số" },
      { href: "/recruiter/hybrid-search", label: "Tìm ứng viên (BT3)" },
    ],
  },
  {
    label: "Admin Lab",
    items: [
      { href: "/admin/graph-explorer", label: "Neo4j Graph Explorer" },
      { href: "/admin/system-sync", label: "Bảng điều khiển ETL" },
    ],
  },
];

export default function Navbar() {
  const pathname = usePathname();
  const { user, logout } = useAuth();
  const [mobileOpen, setMobileOpen] = useState(false);
  const [openGroup, setOpenGroup] = useState<string | null>(null);

  const getRoleBadge = (role: string) => {
    switch (role) {
      case "admin":
        return <span className="bg-violet-100 text-violet-700 text-[10px] px-1.5 py-0.5 rounded-full font-bold">Admin</span>;
      case "hr":
        return <span className="bg-emerald-100 text-emerald-700 text-[10px] px-1.5 py-0.5 rounded-full font-bold">HR</span>;
      default:
        return <span className="bg-blue-100 text-blue-700 text-[10px] px-1.5 py-0.5 rounded-full font-bold">Ứng viên</span>;
    }
  };

  return (
    <header className="sticky top-0 z-50 w-full bg-white border-b border-slate-200 shadow-sm">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex h-16 items-center justify-between">

          {/* Logo */}
          <Link href="/" className="flex items-center gap-2.5 group flex-shrink-0">
            <div className="w-8 h-8 rounded-lg bg-blue-600 flex items-center justify-center shadow-sm group-hover:bg-blue-700 transition-colors">
              <BrainCircuit className="w-5 h-5 text-white" />
            </div>
            <div className="hidden sm:block">
              <span className="font-bold text-slate-900 text-sm leading-tight block">
                JobMatch KG
              </span>
              <span className="text-[11px] text-slate-500 leading-tight block">
                Knowledge Graph + pgvector
              </span>
            </div>
          </Link>

          {/* Desktop Nav */}
          <nav className="hidden md:flex items-center gap-1">
            {navGroups.map((group) => (
              <div key={group.label} className="relative">
                <button
                  onClick={() =>
                    setOpenGroup(openGroup === group.label ? null : group.label)
                  }
                  onBlur={() => setTimeout(() => setOpenGroup(null), 180)}
                  className={`flex items-center gap-1 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                    group.items.some((i) => pathname === i.href)
                      ? "bg-blue-50 text-blue-700"
                      : "text-slate-600 hover:text-slate-900 hover:bg-slate-100"
                  }`}
                >
                  {group.label}
                  <ChevronDown
                    className={`w-3.5 h-3.5 transition-transform ${
                      openGroup === group.label ? "rotate-180" : ""
                    }`}
                  />
                </button>
                {openGroup === group.label && (
                  <div className="absolute top-full left-0 mt-1 w-52 bg-white rounded-xl shadow-lg border border-slate-200 py-1.5 z-50">
                    {group.items.map((item) => (
                      <Link
                        key={item.href}
                        href={item.href}
                        className={`block px-4 py-2 text-sm transition-colors ${
                          pathname === item.href
                            ? "bg-blue-50 text-blue-700 font-semibold"
                            : "text-slate-700 hover:bg-slate-50 hover:text-slate-900"
                        }`}
                      >
                        {item.label}
                      </Link>
                    ))}
                  </div>
                )}
              </div>
            ))}

            {/* Semantic Search Direct Link */}
            <Link
              href="/semantic-search"
              className={`flex items-center gap-1.5 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                pathname === "/semantic-search"
                  ? "bg-blue-50 text-blue-700 font-semibold"
                  : "text-slate-600 hover:text-slate-900 hover:bg-slate-100"
              }`}
            >
              <Search className="w-3.5 h-3.5 text-blue-600" />
              Tìm kiếm Ngữ nghĩa
            </Link>
          </nav>

          {/* Right side: Auth Controls */}
          <div className="hidden md:flex items-center gap-2.5">
            {user ? (
              <div className="flex items-center gap-3">
                <div className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-slate-50 border border-slate-200">
                  <div className="w-6 h-6 rounded-full bg-blue-600 text-white flex items-center justify-center text-xs font-bold">
                    {user.fullName.charAt(0)}
                  </div>
                  <div className="text-left">
                    <div className="text-xs font-semibold text-slate-800 leading-tight">
                      {user.fullName}
                    </div>
                    <div className="leading-tight">{getRoleBadge(user.role)}</div>
                  </div>
                </div>
                <button
                  onClick={logout}
                  title="Đăng xuất"
                  className="p-2 rounded-lg text-slate-500 hover:text-rose-600 hover:bg-rose-50 transition-colors"
                >
                  <LogOut className="w-4 h-4" />
                </button>
              </div>
            ) : (
              <div className="flex items-center gap-2">
                <Link
                  href="/auth/login"
                  className="px-3.5 py-1.5 rounded-lg border border-slate-200 text-slate-700 text-sm font-semibold hover:bg-slate-50 transition-colors shadow-xs"
                >
                  Đăng nhập
                </Link>
                <Link
                  href="/auth/register"
                  className="px-3.5 py-1.5 rounded-lg bg-blue-600 text-white text-sm font-semibold hover:bg-blue-700 transition-colors shadow-xs"
                >
                  Đăng ký
                </Link>
              </div>
            )}
          </div>

          {/* Mobile toggle */}
          <button
            className="md:hidden p-2 rounded-lg text-slate-500 hover:bg-slate-100 transition-colors"
            onClick={() => setMobileOpen(!mobileOpen)}
          >
            {mobileOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
          </button>
        </div>
      </div>

      {/* Mobile menu */}
      {mobileOpen && (
        <div className="md:hidden border-t border-slate-200 bg-white px-4 py-3 space-y-2">
          {/* Mobile Auth */}
          {user ? (
            <div className="flex items-center justify-between p-3 bg-slate-50 rounded-xl mb-3">
              <div className="flex items-center gap-2">
                <div className="w-7 h-7 rounded-full bg-blue-600 text-white flex items-center justify-center text-xs font-bold">
                  {user.fullName.charAt(0)}
                </div>
                <div>
                  <div className="text-sm font-bold text-slate-900">{user.fullName}</div>
                  <div className="text-xs text-slate-500">{user.email}</div>
                </div>
              </div>
              <button
                onClick={() => {
                  logout();
                  setMobileOpen(false);
                }}
                className="text-xs text-rose-600 font-semibold p-1.5"
              >
                Đăng xuất
              </button>
            </div>
          ) : (
            <div className="grid grid-cols-2 gap-2 pb-3 border-b border-slate-100">
              <Link
                href="/auth/login"
                onClick={() => setMobileOpen(false)}
                className="text-center py-2 rounded-lg border border-slate-200 text-slate-700 text-sm font-semibold hover:bg-slate-50"
              >
                Đăng nhập
              </Link>
              <Link
                href="/auth/register"
                onClick={() => setMobileOpen(false)}
                className="text-center py-2 rounded-lg bg-blue-600 text-white text-sm font-semibold hover:bg-blue-700"
              >
                Đăng ký
              </Link>
            </div>
          )}

          {/* Search link */}
          <Link
            href="/semantic-search"
            onClick={() => setMobileOpen(false)}
            className="flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium text-slate-700 hover:bg-slate-50"
          >
            <Search className="w-4 h-4 text-blue-600" />
            Tìm kiếm Ngữ nghĩa (Skills & Jobs)
          </Link>

          {/* Groups */}
          {navGroups.map((group) => (
            <div key={group.label}>
              <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider px-2 pt-2 pb-1">
                {group.label}
              </p>
              {group.items.map((item) => (
                <Link
                  key={item.href}
                  href={item.href}
                  onClick={() => setMobileOpen(false)}
                  className={`block px-3 py-1.5 rounded-lg text-sm transition-colors ${
                    pathname === item.href
                      ? "bg-blue-50 text-blue-700 font-semibold"
                      : "text-slate-700 hover:bg-slate-50"
                  }`}
                >
                  {item.label}
                </Link>
              ))}
            </div>
          ))}
        </div>
      )}
    </header>
  );
}
