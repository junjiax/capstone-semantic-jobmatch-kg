"use client";

import { CheckCircle2, AlertCircle, XCircle, PlusCircle } from "lucide-react";
import { cn } from "@/lib/utils";

interface SkillGapBadgeProps {
  name: string;
  status: "matched" | "partial" | "missing" | "extra";
  similarity?: number;
  weight?: string | number;
}

export default function SkillGapBadge({ name, status, similarity, weight }: SkillGapBadgeProps) {
  const configs = {
    matched: {
      bg: "bg-green-100 text-green-700 border-green-200",
      icon: CheckCircle2,
      label: "Đạt",
    },
    partial: {
      bg: "bg-yellow-100 text-yellow-700 border-yellow-200",
      icon: AlertCircle,
      label: "Một phần",
    },
    missing: {
      bg: "bg-red-100 text-red-700 border-red-200",
      icon: XCircle,
      label: "Thiếu",
    },
    extra: {
      bg: "bg-purple-100 text-purple-700 border-purple-200",
      icon: PlusCircle,
      label: "Bổ trợ",
    },
  };

  const current = configs[status];
  const Icon = current.icon;

  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium border transition hover:scale-105 cursor-default",
        current.bg
      )}
      title={`${name} (${current.label})${similarity ? ` - Cosine: ${similarity.toFixed(2)}` : ""}`}
    >
      <Icon className="h-3.5 w-3.5 shrink-0" />
      <span className="font-semibold">{name}</span>
      {similarity !== undefined && (
        <span className="text-[10px] opacity-75 font-mono">
          {(similarity * 100).toFixed(0)}%
        </span>
      )}
      {weight && (
        <span className="text-[9px] px-1 rounded bg-black/10 uppercase">
          {weight}
        </span>
      )}
    </span>
  );
}
