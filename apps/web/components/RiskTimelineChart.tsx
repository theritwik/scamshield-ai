"use client";
import {
  CartesianGrid,
  Line,
  LineChart,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { Message } from "@/lib/api";

export function RiskTimelineChart({
  points,
  onSelect,
}: {
  points: Message[];
  onSelect?: (seq: number) => void;
}) {
  const data = points.map((p) => ({
    name: `#${p.seq + 1}`,
    seq: p.seq,
    risk: p.cumulative_risk,
    delta: p.risk_delta,
    signals: p.detected_signals.filter((s) => s.kind === "signal").length,
  }));
  return (
    <div className="h-56 w-full">
      <ResponsiveContainer>
        <LineChart
          data={data}
          margin={{ top: 8, right: 12, bottom: 0, left: -18 }}
          onClick={(e) => {
            const idx = Number(e?.activeIndex);
            if (!Number.isNaN(idx) && data[idx] && onSelect) onSelect(data[idx].seq);
          }}
        >
          <CartesianGrid stroke="#1c3059" strokeDasharray="3 3" />
          <XAxis dataKey="name" stroke="#7e90b8" fontSize={11} />
          <YAxis domain={[0, 100]} stroke="#7e90b8" fontSize={11} />
          <ReferenceLine y={75} stroke="#e02d3c" strokeDasharray="4 4" />
          <ReferenceLine y={50} stroke="#f59e0b" strokeDasharray="4 4" />
          <Tooltip
            contentStyle={{
              background: "#0e1b36",
              border: "1px solid #1c3059",
              borderRadius: 8,
              fontSize: 12,
            }}
            labelStyle={{ color: "#b9c6e3" }}
            formatter={(value, name) =>
              name === "risk" ? [`${value}%`, "Cumulative risk"] : [String(value), String(name)]
            }
          />
          <Line
            type="stepAfter"
            dataKey="risk"
            stroke="#4f8ef7"
            strokeWidth={2.5}
            dot={{ r: 4, fill: "#4f8ef7" }}
            activeDot={{ r: 6 }}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
