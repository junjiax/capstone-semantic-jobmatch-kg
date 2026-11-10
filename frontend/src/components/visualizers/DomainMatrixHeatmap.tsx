"use client";

import { useState } from "react";
import { DomainMatrixData } from "@/types";
import { cn } from "@/lib/utils";

interface DomainMatrixHeatmapProps {
  matrix: DomainMatrixData;
}

export default function DomainMatrixHeatmap({ matrix }: DomainMatrixHeatmapProps) {
  const { rows, columns, data } = matrix;
  const [hoveredCell, setHoveredCell] = useState<{
    row: string;
    col: string;
    val: number;
  } | null>(null);

  const getHeatmapStyle = (val: number) => {
    if (val >= 0.8) {
      return "bg-blue-600 text-white font-bold shadow-xs";
    }
    if (val >= 0.65) {
      return "bg-blue-400 text-white font-semibold";
    }
    if (val >= 0.5) {
      return "bg-blue-200 text-blue-900 font-medium";
    }
    if (val >= 0.35) {
      return "bg-blue-50 text-blue-800 border border-blue-100";
    }
    return "bg-slate-50 text-slate-500 border border-slate-200";
  };

  const getExplanation = (row: string, col: string, val: number) => {
    const pct = Math.round(val * 100);
    if (val >= 0.75) {
      return `Độ tương thích cao (${pct}%): CV có nhiều kỹ năng và kinh nghiệm trọng tâm liên quan trực tiếp đến lĩnh vực ${col}.`;
    }
    if (val >= 0.5) {
      return `Độ tương thích trung bình (${pct}%): CV đáp ứng một số nền tảng cho ${col}, nhưng cần bổ sung các công cụ chuyên sâu.`;
    }
    return `Độ tương thích thấp (${pct}%): Hồ sơ hiện tại ít có kỹ năng hoặc kinh nghiệm giao thoa với lĩnh vực ${col}.`;
  };

  return (
    <div className="relative">
      <div className="overflow-x-auto rounded-xl border border-slate-200 shadow-sm bg-white">
        <table className="min-w-full divide-y divide-slate-200 text-xs">
          <thead className="bg-slate-50">
            <tr>
              <th className="sticky left-0 z-10 bg-slate-50 px-4 py-3 text-left font-bold text-slate-700 whitespace-nowrap border-r border-slate-200">
                Thuộc tính CV / Lĩnh vực
              </th>
              {columns.map((col, idx) => (
                <th
                  key={idx}
                  className="px-3 py-3 text-center font-bold text-slate-700 whitespace-nowrap min-w-[130px]"
                >
                  {col}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100 bg-white">
            {rows.map((rowName, rIdx) => (
              <tr key={rIdx} className="hover:bg-slate-50/70 transition">
                <td className="sticky left-0 z-10 bg-white px-4 py-3 font-semibold text-slate-800 whitespace-nowrap border-r border-slate-200">
                  {rowName}
                </td>
                {data[rIdx]?.map((val, cIdx) => {
                  const colName = columns[cIdx];
                  const isHovered =
                    hoveredCell?.row === rowName && hoveredCell?.col === colName;

                  return (
                    <td
                      key={cIdx}
                      className="px-3 py-3 text-center cursor-pointer"
                      onMouseEnter={() =>
                        setHoveredCell({ row: rowName, col: colName, val })
                      }
                      onMouseLeave={() => setHoveredCell(null)}
                    >
                      <span
                        className={cn(
                          "inline-block rounded-lg px-2.5 py-1.5 text-xs font-mono transition-transform duration-150",
                          getHeatmapStyle(val),
                          isHovered && "scale-110 ring-2 ring-blue-500 shadow-md"
                        )}
                      >
                        {(val * 100).toFixed(1)}%
                      </span>
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Dynamic Hover Tooltip Explanation Panel */}
      {hoveredCell && (
        <div className="mt-3 p-3 bg-blue-50 border border-blue-200 rounded-xl text-xs text-blue-900 transition-all flex items-start gap-2">
          <div className="w-2 h-2 rounded-full bg-blue-600 mt-1 flex-shrink-0" />
          <div>
            <strong>
              {hoveredCell.row} × {hoveredCell.col}:
            </strong>{" "}
            {getExplanation(hoveredCell.row, hoveredCell.col, hoveredCell.val)}
          </div>
        </div>
      )}
    </div>
  );
}
