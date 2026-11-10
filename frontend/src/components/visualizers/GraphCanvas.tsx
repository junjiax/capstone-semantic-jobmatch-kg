"use client";

import { useEffect, useRef } from "react";
import cytoscape, { Core } from "cytoscape";
import { GraphNode, GraphLink } from "@/types";

interface GraphCanvasProps {
  nodes: GraphNode[];
  links: GraphLink[];
  onSelectNode?: (node: GraphNode | null) => void;
}

const TYPE_COLORS: Record<string, { bg: string; border: string; text: string }> = {
  Domain: { bg: "#3b82f6", border: "#1d4ed8", text: "#ffffff" },       // Blue
  Expertise: { bg: "#10b981", border: "#047857", text: "#ffffff" },    // Emerald
  Skill: { bg: "#f59e0b", border: "#b45309", text: "#ffffff" },        // Amber
  JobPosition: { bg: "#8b5cf6", border: "#6d28d9", text: "#ffffff" },  // Purple
  Candidate: { bg: "#ec4899", border: "#be185d", text: "#ffffff" },    // Pink
};

export default function GraphCanvas({
  nodes,
  links,
  onSelectNode,
}: GraphCanvasProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const cyRef = useRef<Core | null>(null);

  useEffect(() => {
    if (!containerRef.current) return;

    // Cleanup previous instance if exists
    if (cyRef.current) {
      try {
        cyRef.current.stop();
        cyRef.current.destroy();
      } catch {
        // ignore
      }
      cyRef.current = null;
    }

    const elements = [
      ...nodes.map((n) => {
        const colorCfg = TYPE_COLORS[n.type] || { bg: "#64748b", border: "#334155", text: "#ffffff" };
        return {
          data: {
            id: n.id,
            label: n.label,
            type: n.type,
            bgColor: colorCfg.bg,
            borderColor: colorCfg.border,
            textColor: colorCfg.text,
            raw: n,
          },
        };
      }),
      ...links.map((l, idx) => ({
        data: {
          id: `link-${idx}`,
          source: l.source,
          target: l.target,
          label: l.relationship,
        },
      })),
    ];

    const cy = cytoscape({
      container: containerRef.current,
      elements,
      style: [
        {
          selector: "node",
          style: {
            "background-color": "data(bgColor)",
            label: "data(label)",
            color: "#0f172a",
            "font-size": "11px",
            "font-weight": 600,
            "text-valign": "bottom",
            "text-halign": "center",
            "text-margin-y": 6,
            "text-background-opacity": 0.85,
            "text-background-color": "#ffffff",
            "text-background-padding": "3px",
            "text-background-shape": "roundrectangle",
            width: 44,
            height: 44,
            "border-width": 2,
            "border-color": "data(borderColor)",
          },
        },
        {
          selector: "node[type = 'Domain']",
          style: {
            width: 60,
            height: 60,
            "font-size": "12px",
            "border-width": 3,
          },
        },
        {
          selector: "edge",
          style: {
            width: 1.5,
            "line-color": "#cbd5e1",
            "target-arrow-color": "#94a3b8",
            "target-arrow-shape": "triangle",
            "curve-style": "bezier",
            label: "data(label)",
            "font-size": "9px",
            color: "#64748b",
            "text-rotation": "autorotate",
            "text-margin-y": -7,
            "text-background-opacity": 0.9,
            "text-background-color": "#ffffff",
            "text-background-padding": "2px",
          },
        },
        {
          selector: "node:selected",
          style: {
            "border-width": 4,
            "border-color": "#2563eb",
            "underlay-color": "#93c5fd",
            "underlay-padding": 8,
            "underlay-opacity": 0.5,
          },
        },
      ],
      layout: {
        name: "cose",
        animate: false, // Prevents background animation tick calling notify on destroyed renderer
        padding: 40,
        nodeRepulsion: () => 450000,
        idealEdgeLength: () => 110,
      },
    });

    cy.on("tap", "node", (evt) => {
      const nodeData = evt.target.data("raw") as GraphNode;
      if (onSelectNode) onSelectNode(nodeData);
    });

    cy.on("tap", (evt) => {
      if (evt.target === cy) {
        if (onSelectNode) onSelectNode(null);
      }
    });

    cyRef.current = cy;

    return () => {
      try {
        if (cyRef.current) {
          cyRef.current.stop();
          cyRef.current.removeAllListeners();
          cyRef.current.destroy();
          cyRef.current = null;
        }
      } catch {
        // safe cleanup
      }
    };
  }, [nodes, links, onSelectNode]);

  return (
    <div className="relative w-full h-[520px] rounded-2xl border border-slate-200 bg-slate-50 overflow-hidden shadow-inner">
      <div ref={containerRef} className="w-full h-full" />
      <div className="absolute bottom-3 left-3 bg-white/95 backdrop-blur-md border border-slate-200 shadow-sm px-3 py-2 rounded-xl text-[11px] text-slate-700 flex items-center gap-4">
        <span className="flex items-center gap-1.5">
          <span className="w-3 h-3 rounded-full bg-blue-500" /> Domain
        </span>
        <span className="flex items-center gap-1.5">
          <span className="w-3 h-3 rounded-full bg-emerald-500" /> Expertise
        </span>
        <span className="flex items-center gap-1.5">
          <span className="w-3 h-3 rounded-full bg-amber-500" /> Skill
        </span>
        <span className="flex items-center gap-1.5">
          <span className="w-3 h-3 rounded-full bg-purple-500" /> Job
        </span>
        <span className="flex items-center gap-1.5">
          <span className="w-3 h-3 rounded-full bg-pink-500" /> Candidate
        </span>
      </div>
    </div>
  );
}
