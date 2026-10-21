"use client";
import {
  Bar, BarChart, CartesianGrid, Cell, Legend, Line, LineChart, Pie, PieChart, ResponsiveContainer, Tooltip, XAxis, YAxis,
} from "recharts";
import { AWAY_COLOR, DRAW_COLOR, HOME_COLOR, pct } from "@/lib/format";

const axis = { stroke: "rgb(var(--line))", tick: { fill: "rgb(var(--mute))", fontSize: 12 } };
const tooltipStyle = { background: "rgb(var(--panel))", border: "1px solid rgb(var(--line))", borderRadius: 8, color: "rgb(var(--ink))" };

export function ProbDonut({ home, away, p }: { home: string; away: string; p: { home: number; draw: number; away: number } }) {
  const data = [
    { name: `Gana ${home}`, value: p.home, color: HOME_COLOR },
    { name: "Empate", value: p.draw, color: DRAW_COLOR },
    { name: `Gana ${away}`, value: p.away, color: AWAY_COLOR },
  ];
  const top = data.reduce((a, b) => (b.value > a.value ? b : a));
  return (
    <div role="img" aria-label={`Probabilidades: ${data.map((d) => `${d.name} ${pct(d.value)}`).join(", ")}`}
      className="flex flex-col items-center gap-4 sm:flex-row">
      <div className="relative h-52 w-52 shrink-0">
        <ResponsiveContainer>
          <PieChart>
            <Pie data={data} dataKey="value" innerRadius={62} outerRadius={92} paddingAngle={2} stroke="none" isAnimationActive={false}>
              {data.map((d) => <Cell key={d.name} fill={d.color} />)}
            </Pie>
          </PieChart>
        </ResponsiveContainer>
        <div className="pointer-events-none absolute inset-0 flex flex-col items-center justify-center">
          <span className="text-3xl font-bold tabular-nums">{pct(top.value)}</span>
          <span className="max-w-[7rem] text-center text-xs text-mute">{top.name}</span>
        </div>
      </div>
      <ul className="w-full space-y-2">
        {data.map((d) => (
          <li key={d.name} className="flex items-center justify-between gap-3 rounded-lg bg-panel2 px-3 py-2">
            <span className="flex items-center gap-2 text-sm"><span className="h-3 w-3 rounded-full" style={{ background: d.color }} />{d.name}</span>
            <span className="text-lg font-semibold tabular-nums">{pct(d.value, 1)}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}

export function CompareBars({ data, home, away, height = 260 }: { data: { label: string; home: number | null; away: number | null }[]; home: string; away: string; height?: number }) {
  return (
    <div style={{ height }} role="img" aria-label={`Comparación entre ${home} y ${away}`}>
      <ResponsiveContainer>
        <BarChart data={data} margin={{ top: 8, right: 8, left: -12, bottom: 0 }}>
          <CartesianGrid stroke="rgb(var(--line))" vertical={false} />
          <XAxis dataKey="label" {...axis} interval={0} />
          <YAxis {...axis} />
          <Tooltip contentStyle={tooltipStyle} cursor={{ fill: "rgb(var(--panel2))" }} />
          <Legend wrapperStyle={{ fontSize: 12 }} />
          <Bar dataKey="home" name={home} fill={HOME_COLOR} radius={[4, 4, 0, 0]} isAnimationActive={false} />
          <Bar dataKey="away" name={away} fill={AWAY_COLOR} radius={[4, 4, 0, 0]} isAnimationActive={false} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

export function GoalsTrend({ rows, color }: { rows: { date: string; gf: number; ga: number }[]; color: string }) {
  return (
    <div className="h-56" role="img" aria-label="Goles a favor y en contra por partido, del más antiguo al más reciente">
      <ResponsiveContainer>
        <LineChart data={rows} margin={{ top: 8, right: 8, left: -18, bottom: 0 }}>
          <CartesianGrid stroke="rgb(var(--line))" vertical={false} />
          <XAxis dataKey="date" {...axis} tickFormatter={(d: string) => d.slice(5)} />
          <YAxis {...axis} allowDecimals={false} />
          <Tooltip contentStyle={tooltipStyle} />
          <Legend wrapperStyle={{ fontSize: 12 }} />
          <Line type="monotone" dataKey="gf" name="Goles a favor" stroke={color} strokeWidth={2.5} dot={{ r: 3 }} isAnimationActive={false} />
          <Line type="monotone" dataKey="ga" name="Goles en contra" stroke="rgb(var(--bad))" strokeWidth={2} strokeDasharray="5 4" dot={{ r: 3 }} isAnimationActive={false} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}

export function IntervalBars({ labels, a, b, nameA, nameB, colorA, colorB }: {
  labels: string[]; a: number[]; b: number[]; nameA: string; nameB: string; colorA: string; colorB: string;
}) {
  const data = labels.map((l, i) => ({ l, a: a[i], b: b[i] }));
  return (
    <div className="h-60" role="img" aria-label="Goles por intervalo de minutos">
      <ResponsiveContainer>
        <BarChart data={data} margin={{ top: 8, right: 8, left: -18, bottom: 0 }}>
          <CartesianGrid stroke="rgb(var(--line))" vertical={false} />
          <XAxis dataKey="l" {...axis} interval={0} tick={{ fill: "rgb(var(--mute))", fontSize: 10 }} />
          <YAxis {...axis} allowDecimals={false} />
          <Tooltip contentStyle={tooltipStyle} cursor={{ fill: "rgb(var(--panel2))" }} />
          <Legend wrapperStyle={{ fontSize: 12 }} />
          <Bar dataKey="a" name={nameA} fill={colorA} radius={[4, 4, 0, 0]} isAnimationActive={false} />
          <Bar dataKey="b" name={nameB} fill={colorB} radius={[4, 4, 0, 0]} isAnimationActive={false} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

/** Mapa de calor: filas = series, columnas = intervalos. La intensidad es proporcional al valor máximo. */
export function Heatmap({ labels, rows, decimals = 0 }: { labels: string[]; rows: { name: string; values: number[]; color: string }[]; decimals?: number }) {
  const max = Math.max(1e-9, ...rows.flatMap((r) => r.values));
  return (
    <div className="overflow-x-auto">
      <table className="w-full min-w-[420px] border-separate border-spacing-1 text-sm">
        <thead>
          <tr>
            <th className="w-36 text-left text-xs font-medium text-mute">Minutos</th>
            {labels.map((l) => <th key={l} className="text-xs font-medium text-mute">{l}</th>)}
          </tr>
        </thead>
        <tbody>
          {rows.map((r) => (
            <tr key={r.name}>
              <th scope="row" className="pr-2 text-left text-xs font-medium text-ink">{r.name}</th>
              {r.values.map((v, i) => {
                const alpha = v / max;
                return (
                  <td key={i} className="rounded-md py-2 text-center font-semibold tabular-nums"
                    style={{ background: `color-mix(in srgb, ${r.color} ${Math.round(10 + alpha * 75)}%, transparent)`, color: "rgb(var(--ink))" }}>
                    {v.toFixed(decimals)}
                  </td>
                );
              })}
            </tr>
          ))}
        </tbody>
      </table>
      <p className="mt-1 text-xs text-mute">Más color = más goles en ese tramo (escala relativa al valor más alto de la tabla: {max.toFixed(decimals)}).</p>
    </div>
  );
}

export function ScoreBars({ scores, home, away }: { scores: { home: number; away: number; prob: number }[]; home: string; away: string }) {
  const data = scores.map((s) => ({ name: `${s.home}-${s.away}`, prob: +(s.prob * 100).toFixed(1), kind: s.home > s.away ? "h" : s.home < s.away ? "a" : "d" }));
  const col = { h: HOME_COLOR, a: AWAY_COLOR, d: DRAW_COLOR } as const;
  return (
    <div className="h-72" role="img" aria-label={`Marcadores más probables entre ${home} y ${away}`}>
      <ResponsiveContainer>
        <BarChart data={data} layout="vertical" margin={{ top: 4, right: 24, left: 0, bottom: 0 }}>
          <CartesianGrid stroke="rgb(var(--line))" horizontal={false} />
          <XAxis type="number" {...axis} unit=" %" />
          <YAxis type="category" dataKey="name" {...axis} width={48} />
          <Tooltip contentStyle={tooltipStyle} formatter={(v: number) => [`${v} %`, "Probabilidad"]} cursor={{ fill: "rgb(var(--panel2))" }} />
          <Bar dataKey="prob" isAnimationActive={false} radius={[0, 4, 4, 0]} label={{ position: "right", fill: "rgb(var(--ink))", fontSize: 12 }}>
            {data.map((d, i) => <Cell key={i} fill={col[d.kind as "h" | "a" | "d"]} />)}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

export function TotalGoalsBars({ dist }: { dist: number[] }) {
  const data = dist.map((p, i) => ({ goles: i === dist.length - 1 ? `${i}+` : `${i}`, prob: +(p * 100).toFixed(1) }));
  return (
    <div className="h-52" role="img" aria-label="Distribución de goles totales del partido">
      <ResponsiveContainer>
        <BarChart data={data} margin={{ top: 8, right: 8, left: -12, bottom: 0 }}>
          <CartesianGrid stroke="rgb(var(--line))" vertical={false} />
          <XAxis dataKey="goles" {...axis} />
          <YAxis {...axis} unit=" %" />
          <Tooltip contentStyle={tooltipStyle} formatter={(v: number) => [`${v} %`, "Probabilidad"]} cursor={{ fill: "rgb(var(--panel2))" }} />
          <Bar dataKey="prob" fill="#a78bfa" radius={[4, 4, 0, 0]} isAnimationActive={false} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

export function CalibrationChart({ rows }: { rows: { mean_predicted: number | null; observed_freq: number | null; n: number }[] }) {
  const data = rows.filter((r) => r.n >= 5 && r.mean_predicted != null).map((r) => ({
    pred: +(r.mean_predicted! * 100).toFixed(1), obs: +(r.observed_freq! * 100).toFixed(1), ideal: +(r.mean_predicted! * 100).toFixed(1), n: r.n,
  }));
  return (
    <div className="h-64" role="img" aria-label="Calibración: probabilidad predicha frente a frecuencia observada">
      <ResponsiveContainer>
        <LineChart data={data} margin={{ top: 8, right: 12, left: -8, bottom: 14 }}>
          <CartesianGrid stroke="rgb(var(--line))" />
          <XAxis dataKey="pred" type="number" domain={[0, 100]} {...axis} unit=" %" label={{ value: "Probabilidad predicha", position: "insideBottom", offset: -8, fill: "rgb(var(--mute))", fontSize: 12 }} />
          <YAxis type="number" domain={[0, 100]} {...axis} unit=" %" />
          <Tooltip contentStyle={tooltipStyle} />
          <Legend verticalAlign="top" />
          <Line dataKey="ideal" name="Calibración perfecta" stroke="#64748b" strokeDasharray="5 4" dot={false} isAnimationActive={false} />
          <Line dataKey="obs" name="Observado" stroke="#a78bfa" strokeWidth={2.5} dot={{ r: 4 }} isAnimationActive={false} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
