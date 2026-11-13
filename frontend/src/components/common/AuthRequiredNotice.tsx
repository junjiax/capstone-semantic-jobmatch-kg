"use client";

import { useEffect, useState } from "react";
import { AlertCircle, ArrowRight, X } from "lucide-react";
import { usePathname, useRouter } from "next/navigation";

export default function AuthRequiredNotice() {
  const router = useRouter();
  const pathname = usePathname();
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    let redirectTimer: number | undefined;
    setVisible(false);
    const handleAuthRequired = () => {
      if (pathname === "/auth/login" || pathname === "/auth/register") return;
      setVisible(true);
      const redirect = `${window.location.pathname}${window.location.search}`;
      sessionStorage.setItem("post_login_redirect", redirect);
      window.clearTimeout(redirectTimer);
      redirectTimer = window.setTimeout(() => {
        router.push(`/auth/login?redirect=${encodeURIComponent(redirect)}`);
      }, 1800);
    };

    window.addEventListener("jobmatch:auth-required", handleAuthRequired);
    return () => {
      window.clearTimeout(redirectTimer);
      window.removeEventListener("jobmatch:auth-required", handleAuthRequired);
    };
  }, [pathname, router]);

  if (!visible || pathname === "/auth/login" || pathname === "/auth/register") return null;

  return (
    <div
      role="alertdialog"
      aria-modal="true"
      aria-labelledby="auth-required-title"
      aria-live="assertive"
      className="fixed inset-0 z-[100] flex items-center justify-center bg-slate-950/35 p-4 backdrop-blur-[2px]"
    >
      <div className="relative w-full max-w-md rounded-2xl border border-amber-200 bg-white p-6 shadow-2xl">
        <button
          type="button"
          aria-label="Đóng thông báo"
          onClick={() => setVisible(false)}
          className="absolute right-4 top-4 rounded-lg p-1.5 text-slate-400 transition hover:bg-slate-100 hover:text-slate-700"
        >
          <X className="h-4 w-4" />
        </button>
        <div className="flex items-start gap-4">
          <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-full bg-amber-100 text-amber-600">
            <AlertCircle className="h-6 w-6" />
          </div>
          <div className="min-w-0 pr-5">
            <p id="auth-required-title" className="text-base font-bold text-slate-900">
              Bạn cần đăng nhập trước
            </p>
            <p className="mt-2 text-sm leading-relaxed text-slate-500">
              Vui lòng đăng nhập để sử dụng chức năng này. Bạn sẽ được chuyển tới trang đăng nhập.
            </p>
          </div>
        </div>
        <div className="mt-5 flex justify-end">
          <button
            type="button"
            onClick={() => {
              const redirect = `${window.location.pathname}${window.location.search}`;
              router.push(`/auth/login?redirect=${encodeURIComponent(redirect)}`);
            }}
            className="inline-flex items-center gap-1.5 rounded-xl bg-blue-600 px-4 py-2.5 text-sm font-bold text-white shadow-sm transition hover:bg-blue-700"
          >
            Đăng nhập ngay
            <ArrowRight className="h-4 w-4" />
          </button>
        </div>
      </div>
    </div>
  );
}
