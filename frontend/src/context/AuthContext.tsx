"use client";

import React, { createContext, useContext, useState, useEffect } from "react";
import apiClient from "@/lib/api";

export interface AuthUser {
  id: number;
  email: string;
  fullName: string;
  role: "applicant" | "hr" | "admin";
  phone?: string;
}

interface AuthContextType {
  user: AuthUser | null;
  token: string | null;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<{ success: boolean; error?: string }>;
  register: (data: {
    email: string;
    fullName: string;
    password: string;
    confirmPassword: string;
    phone?: string;
  }) => Promise<{ success: boolean; error?: string }>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    // Load stored token and user on client mount
    if (typeof window !== "undefined") {
      const storedToken = localStorage.getItem("access_token");
      const storedUser = localStorage.getItem("auth_user");
      if (storedToken && storedUser) {
        try {
          setToken(storedToken);
          setUser(JSON.parse(storedUser));
        } catch {
          localStorage.removeItem("auth_user");
        }
      }
      setIsLoading(false);
    }
  }, []);

  const login = async (email: string, password: string) => {
    try {
      // FastAPI OAuth2PasswordRequestForm expects form-urlencoded body
      const formData = new URLSearchParams();
      formData.append("username", email);
      formData.append("password", password);

      const res = await apiClient.post("/auth/login", formData, {
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
      });

      const data = res.data;
      const accessToken = data.access_token || data.data?.access_token;
      if (!accessToken) throw new Error("Backend không trả về access token.");
      const refreshToken = data.refresh_token || data.data?.refresh_token;

      localStorage.setItem("access_token", accessToken);
      if (refreshToken) localStorage.setItem("refresh_token", refreshToken);

      const profileResponse = await apiClient.get("/user/me", {
        headers: { Authorization: `Bearer ${accessToken}` },
      });
      const profile = profileResponse.data;
      const rawRole = profile.role || profile.Role;
      const determinedRole: "applicant" | "hr" | "admin" =
        rawRole === "admin" ? "admin" : rawRole === "hr" ? "hr" : "applicant";

      const loggedUser: AuthUser = {
        id: profile.id || profile.Id,
        email: profile.email || profile.Email || email,
        fullName: profile.full_name || profile.FullName || email.split("@")[0].toUpperCase(),
        role: determinedRole,
        phone: profile.phone || profile.Phone,
      };

      localStorage.setItem("auth_user", JSON.stringify(loggedUser));
      setToken(accessToken);
      setUser(loggedUser);

      return { success: true };
    } catch (err: unknown) {
      const axiosErr = err as { response?: { status?: number; data?: { detail?: string } } };
      if (axiosErr.response?.status === 401) {
        return {
          success: false,
          error:
            axiosErr.response.data?.detail ||
            "Email hoặc mật khẩu không chính xác. Vui lòng kiểm tra lại.",
        };
      }
      return {
        success: false,
        error: axiosErr.response?.data?.detail || "Không thể kết nối hoặc xác thực với backend.",
      };
    }
  };

  const register = async (data: {
    email: string;
    fullName: string;
    password: string;
    confirmPassword: string;
    phone?: string;
  }) => {
    try {
      const payload = {
        email: data.email,
        full_name: data.fullName,
        password: data.password,
        confirm_password: data.confirmPassword,
        phone: data.phone || null,
        is_verified: true,
      };

      await apiClient.post("/auth/register", payload);
      // Auto login after successful register
      return await login(data.email, data.password);
    } catch (err: unknown) {
      const axiosErr = err as { response?: { data?: { detail?: string } } };
      return {
        success: false,
        error: axiosErr.response?.data?.detail || "Không thể đăng ký tài khoản với backend.",
      };
    }
  };

  const logout = () => {
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
    localStorage.removeItem("auth_user");
    setToken(null);
    setUser(null);
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        isLoading,
        login,
        register,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
