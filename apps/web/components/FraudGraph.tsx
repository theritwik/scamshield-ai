"use client";
/** Lightweight force-directed fraud-graph view (no external graph library). */
import { useEffect, useMemo, useRef, useState } from "react";
import type { GraphPayload } from "@/lib/api";

const TYPE_COLORS: Record<string, string> = {
  complaint: "#4f8ef7",
  phone: "#f59e0b",
  upi_id: "#e02d3c",
  bank_account: "#f97316",
  email: "#a78bfa",
  url: "#ec4899",
  ifsc: "#94a3b8",
  officer_name: "#22d3ee",
  remote_tool: "#facc15",
};

interface SimNode {
  id: string;
  x: number;
  y: number;
  vx: number;
  vy: number;
}

export function FraudGraph({
  data,
  height = 480,
  onSelect,
}: {
  data: GraphPayload;
  height?: number;
  onSelect?: (nodeId: string) => void;
}) {
  const width = 860;
  const [filter, setFilter] = useState("");
  const [typeFilter, setTypeFilter] = useState("all");
  const [positions, setPositions] = useState<Map<string, SimNode>>(new Map());
  const [selected, setSelected] = useState<string | null>(null);
  const animRef = useRef<number>(0);

  const { nodes, edges } = data;

  // Run a small force simulation once per graph payload.
  useEffect(() => {
    const sim = new Map<string, SimNode>();
    const n = nodes.length || 1;
    nodes.forEach((node, i) => {
      const angle = (i / n) * Math.PI * 2;
      const rad = 150 + (i % 5) * 30;
      sim.set(node.id, {
        id: node.id,
        x: width / 2 + rad * Math.cos(angle),
        y: height / 2 + rad * Math.sin(angle),
        vx: 0,
        vy: 0,
      });
    });
    let ticks = 0;
    const step = () => {
      ticks++;
      const arr = [...sim.values()];
      // Repulsion
      for (let i = 0; i < arr.length; i++) {
        for (let j = i + 1; j < arr.length; j++) {
          const a = arr[i];
          const b = arr[j];
          let dx = a.x - b.x;
          let dy = a.y - b.y;
          const d2 = Math.max(80, dx * dx + dy * dy);
          const f = 2600 / d2;
          const d = Math.sqrt(d2);
          dx /= d;
          dy /= d;
          a.vx += dx * f;
          a.vy += dy * f;
          b.vx -= dx * f;
          b.vy -= dy * f;
        }
      }
      // Springs
      for (const e of edges) {
        const a = sim.get(e.source);
        const b = sim.get(e.target);
        if (!a || !b) continue;
        const dx = b.x - a.x;
        const dy = b.y - a.y;
        const d = Math.max(1, Math.sqrt(dx * dx + dy * dy));
        const f = (d - 90) * 0.02;
        a.vx += (dx / d) * f;
        a.vy += (dy / d) * f;
        b.vx -= (dx / d) * f;
        b.vy -= (dy / d) * f;
      }
      // Centering + integrate
      for (const p of arr) {
        p.vx += (width / 2 - p.x) * 0.002;
        p.vy += (height / 2 - p.y) * 0.002;
        p.vx *= 0.82;
        p.vy *= 0.82;
        p.x = Math.min(width - 20, Math.max(20, p.x + p.vx));
        p.y = Math.min(height - 20, Math.max(20, p.y + p.vy));
      }
      setPositions(new Map(sim));
      if (ticks < 140) animRef.current = requestAnimationFrame(step);
    };
    animRef.current = requestAnimationFrame(step);
    return () => cancelAnimationFrame(animRef.current);
  }, [nodes, edges, height]);

  const visible = useMemo(() => {
    const q = filter.toLowerCase();
    const ids = new Set(
      nodes
        .filter(
          (n) =>
            (typeFilter === "all" || n.type === typeFilter) &&
            (!q || n.label.toLowerCase().includes(q) || n.id.toLowerCase().includes(q)),
        )
        .map((n) => n.id),
    );
    if (q || typeFilter !== "all") {
      // Include direct neighbours of matches for context.
      for (const e of edges) {
        if (ids.has(e.source)) ids.add(e.target);
        if (ids.has(e.target)) ids.add(e.source);
      }
    }
    return ids;
  }, [nodes, edges, filter, typeFilter]);

  const types = useMemo(() => [...new Set(nodes.map((n) => n.type))], [nodes]);

  if (nodes.length === 0) {
    return (
      <div className="card grid h-64 place-items-center text-sm text-ink-500">
        No graph data yet — analyse cases with phone numbers, UPI IDs or accounts to build the network.
      </div>
    );
  }

  return (
    <div className="space-y-3">
      <div className="flex flex-wrap items-center gap-2">
        <input
          className="input max-w-56"
          placeholder="Search nodes…"
          value={filter}
          onChange={(e) => setFilter(e.target.value)}
        />
        <select
          className="input max-w-44"
          value={typeFilter}
          onChange={(e) => setTypeFilter(e.target.value)}
          aria-label="Filter node type"
        >
          <option value="all">All types</option>
          {types.map((t) => (
            <option key={t} value={t}>
              {t.replace("_", " ")}
            </option>
          ))}
        </select>
        <div className="flex flex-wrap gap-2 text-[11px] text-ink-500">
          {types.map((t) => (
            <span key={t} className="inline-flex items-center gap-1">
              <span className="h-2.5 w-2.5 rounded-full" style={{ background: TYPE_COLORS[t] ?? "#888" }} />
              {t.replace("_", " ")}
            </span>
          ))}
        </div>
      </div>

      <div className="card overflow-x-auto">
        <svg width={width} height={height} className="mx-auto block" role="img" aria-label="Fraud network graph">
          {edges.map((e, i) => {
            const a = positions.get(e.source);
            const b = positions.get(e.target);
            if (!a || !b || !visible.has(e.source) || !visible.has(e.target)) return null;
            return (
              <line
                key={i}
                x1={a.x}
                y1={a.y}
                x2={b.x}
                y2={b.y}
                stroke="#1c3059"
                strokeWidth={selected && (e.source === selected || e.target === selected) ? 2.5 : 1.2}
              />
            );
          })}
          {nodes.map((n) => {
            const p = positions.get(n.id);
            if (!p || !visible.has(n.id)) return null;
            const r = n.type === "complaint" ? 9 : 6 + Math.min(6, n.degree);
            const risky = n.risk >= 75;
            return (
              <g
                key={n.id}
                transform={`translate(${p.x},${p.y})`}
                className="cursor-pointer"
                onClick={() => {
                  setSelected(n.id);
                  onSelect?.(n.id);
                }}
              >
                {risky && <circle r={r + 4} fill="none" stroke="#e02d3c" strokeWidth={1.5} opacity={0.6} />}
                <circle
                  r={r}
                  fill={TYPE_COLORS[n.type] ?? "#888"}
                  stroke={selected === n.id ? "#fff" : "#0a1428"}
                  strokeWidth={selected === n.id ? 2.5 : 1.5}
                />
                <title>{`${n.type}: ${n.label}\nrisk ${Math.round(n.risk)} · degree ${n.degree} · centrality ${n.centrality}`}</title>
                <text
                  y={r + 12}
                  textAnchor="middle"
                  fontSize={9.5}
                  fill="#7e90b8"
                  style={{ pointerEvents: "none" }}
                >
                  {n.label.length > 18 ? n.label.slice(0, 17) + "…" : n.label}
                </text>
              </g>
            );
          })}
        </svg>
      </div>

      {data.insights.length > 0 && (
        <div className="card space-y-2 p-4">
          <div className="label">Network insights</div>
          {data.insights.map((ins) => (
            <p key={ins} className="text-sm text-ink-300">
              ⚑ {ins}
            </p>
          ))}
          <p className="text-[11px] text-ink-500">{data.disclaimer}</p>
        </div>
      )}
    </div>
  );
}
