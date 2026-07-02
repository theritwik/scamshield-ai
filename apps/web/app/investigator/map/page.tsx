"use client";
/** Synthetic geographic hotspot view. Schematic India projection, no map tiles. */
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";

const CITY_COORDS: Record<string, { lat: number; lon: number }> = {
  Mumbai: { lat: 19.08, lon: 72.88 },
  Delhi: { lat: 28.61, lon: 77.21 },
  Bengaluru: { lat: 12.97, lon: 77.59 },
  Hyderabad: { lat: 17.38, lon: 78.48 },
  Lucknow: { lat: 26.85, lon: 80.95 },
  Kolkata: { lat: 22.57, lon: 88.36 },
  Chennai: { lat: 13.08, lon: 80.27 },
};

// Rough schematic outline of India (lon, lat) — demo visual, not survey-accurate.
const INDIA_OUTLINE: [number, number][] = [
  [68.2, 23.6], [70.5, 22.0], [72.6, 21.0], [72.8, 19.2], [73.5, 16.0],
  [74.9, 13.0], [76.0, 10.5], [77.5, 8.1], [78.2, 8.9], [79.9, 10.3],
  [80.3, 13.5], [80.1, 15.8], [82.3, 17.0], [84.8, 19.1], [86.9, 20.7],
  [88.1, 21.6], [89.0, 22.1], [89.8, 25.3], [92.4, 24.9], [94.6, 25.2],
  [95.8, 27.1], [96.9, 28.4], [94.5, 29.3], [91.7, 27.8], [88.8, 27.1],
  [85.8, 28.3], [83.0, 29.5], [80.5, 30.5], [78.9, 32.2], [76.9, 34.0],
  [74.4, 34.8], [73.9, 33.0], [74.5, 30.9], [71.9, 27.9], [70.2, 26.5],
  [69.5, 24.7], [68.2, 23.6],
];

function project(lon: number, lat: number, w: number, h: number) {
  const x = ((lon - 66) / (98 - 66)) * w;
  const y = h - ((lat - 6) / (36 - 6)) * h;
  return { x, y };
}

export default function HotspotMapPage() {
  const router = useRouter();
  const [cities, setCities] = useState<{ city: string; cases: number; avg_risk: number }[]>([]);
  const [loaded, setLoaded] = useState(false);
  const w = 560;
  const h = 600;

  useEffect(() => {
    api
      .hotspots()
      .then((r) => {
        setCities(r.cities);
        setLoaded(true);
      })
      .catch(() => router.push("/investigator"));
  }, [router]);

  const path =
    INDIA_OUTLINE.map(([lon, lat], i) => {
      const { x, y } = project(lon, lat, w, h);
      return `${i === 0 ? "M" : "L"}${x.toFixed(1)},${y.toFixed(1)}`;
    }).join(" ") + " Z";

  return (
    <div className="space-y-4">
      <header>
        <h1 className="text-2xl font-bold">Complaint hotspots</h1>
        <p className="mt-1 text-sm text-ink-500">
          Synthetic location data · schematic projection for the demo
        </p>
      </header>

      {!loaded ? (
        <div className="skeleton h-[560px]" />
      ) : (
        <div className="grid gap-5 lg:grid-cols-[1fr_300px]">
          <div className="card overflow-x-auto p-4">
            <svg width={w} height={h} className="mx-auto block" role="img" aria-label="India complaint hotspot map">
              <path d={path} fill="#0e1b36" stroke="#2a4374" strokeWidth={1.5} />
              {cities.map((c) => {
                const coord = CITY_COORDS[c.city];
                if (!coord) return null;
                const { x, y } = project(coord.lon, coord.lat, w, h);
                const r = 8 + Math.min(26, c.cases * 3.5);
                const color = c.avg_risk >= 75 ? "#e02d3c" : c.avg_risk >= 50 ? "#f97316" : "#f59e0b";
                return (
                  <g key={c.city} transform={`translate(${x},${y})`}>
                    <circle r={r} fill={color} opacity={0.22} />
                    <circle r={4.5} fill={color} />
                    <title>{`${c.city}: ${c.cases} complaints, avg risk ${c.avg_risk}`}</title>
                    <text y={-r - 4} textAnchor="middle" fontSize={11} fontWeight={600} fill="#e8eefc">
                      {c.city}
                    </text>
                    <text y={-r + 10} textAnchor="middle" fontSize={9} fill="#7e90b8">
                      {c.cases} cases
                    </text>
                  </g>
                );
              })}
            </svg>
          </div>

          <div className="space-y-3">
            {[...cities]
              .sort((a, b) => b.cases - a.cases)
              .map((c) => (
                <div key={c.city} className="card flex items-center justify-between p-4">
                  <div>
                    <div className="font-semibold">{c.city}</div>
                    <div className="text-[11px] text-ink-500">{c.cases} complaints</div>
                  </div>
                  <div
                    className="text-xl font-black tabular-nums"
                    style={{ color: c.avg_risk >= 75 ? "#e02d3c" : c.avg_risk >= 50 ? "#f97316" : "#f59e0b" }}
                  >
                    {c.avg_risk}
                  </div>
                </div>
              ))}
            {cities.length === 0 && (
              <div className="card p-6 text-sm text-ink-500">No location data. Run the seed script.</div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
