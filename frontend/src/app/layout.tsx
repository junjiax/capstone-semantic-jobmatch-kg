import type { Metadata } from "next";
import Navbar from "@/components/common/Navbar";
import Footer from "@/components/common/Footer";
import { AuthProvider } from "@/context/AuthContext";
import AuthRequiredNotice from "@/components/common/AuthRequiredNotice";
import "./globals.css";

export const metadata: Metadata = {
  title: "JobMatch - Kết nối đúng người với đúng cơ hội",
  description:
    "Nền tảng giúp ứng viên tìm cơ hội phù hợp và nhà tuyển dụng tìm kiếm nhân tài hiệu quả hơn.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="vi" className="h-full antialiased" suppressHydrationWarning>
      <body
        className="min-h-full flex flex-col bg-slate-50 text-slate-900 font-sans antialiased"
        suppressHydrationWarning
      >
        <AuthProvider>
          <Navbar />
          <main className="flex-1">{children}</main>
          <Footer />
          <AuthRequiredNotice />
        </AuthProvider>
      </body>
    </html>
  );
}
