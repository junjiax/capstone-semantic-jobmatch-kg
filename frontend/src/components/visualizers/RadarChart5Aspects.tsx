"use client";

import { useEffect, useState } from "react";
import {
  Radar,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  ResponsiveContainer,
  Tooltip,
} from "recharts";
import { MatchScores } from "@/types";

interface RadarChart5AspectsProps {
  scores: MatchScores;
  jobTitle?: string;
}

export default function RadarChart5Aspects({ scores, jobTitle }: RadarChart5AspectsProps) {
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  const data = [
    { aspect: "Kỹ năng (40%)", value: Math.round(scores.skillScore * 100), fullMark: 100 },
    { aspect: "Lĩnh vực (20%)", value: Math.round(scores.domainScore * 100), fullMark: 100 },
    { aspect: "Chuyên môn (20%)", value: Math.round(scores.expertiseScore * 100), fullMark: 100 },
    { aspect: "Kinh nghiệm (10%)", value: Math.round(scores.experienceScore * 100), fullMark: 100 },
    { aspect: "Học vấn (10%)", value: Math.round(scores.qualificationScore * 100), fullMark: 100 },
  ];

  if (!mounted) {
    return (
      <div className="flex h-72 w-full items-center justify-center rounded-2xl bg-slate-50 animate-pulse">
        <span className="text-xs text-slate-400">Đang khởi tạo biểu đồ...</span>
      </div>
    );
  }

  return (
    <div className="w-full h-80">
      <ResponsiveContainer width="100%" height="100%">
        <RadarChart cx="50%" cy="50%" outerRadius="75%" data={data}>
          <PolarGrid stroke="#e2e8f0" strokeDasharray="3 3" />
          <PolarAngleAxis
            dataKey="aspect"
            tick={{ fill: "#475569", fontSize: 11, fontWeight: 600 }}
          />
          <PolarRadiusAxis
            angle={90}
            domain={[0, 100]}
            tick={{ fill: "#94a3b8", fontSize: 10 }}
          />
          <Radar
            name={jobTitle || "Mức độ phù hợp"}
            dataKey="value"
            stroke="#2563eb"
            fill="#3b82f6"
            fillOpacity={0.35}
          />
          <Tooltip
            formatter={(value: unknown) => [
              `${typeof value === "number" ? value : 0}%`,
              "Điểm thành phần",
            ]}
            contentStyle={{
              backgroundColor: "#ffffff",
              borderColor: "#e2e8f0",
              borderRadius: "12px",
              color: "#0f172a",
              fontSize: "12px",
              boxShadow: "0 4px 6px -1px rgba(0,0,0,0.1)",
            }}
          />
        </RadarChart>
      </ResponsiveContainer>
    </div>
  );
}
