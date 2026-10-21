"use client";
import Link from "next/link";
import { ReactNode } from "react";
import { CartesianGrid, Legend, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { Analysis, Fixture, Standings, TeamReport } from "@/lib/api";
import { AWAY_COLOR, DRAW_COLOR, HOME_COLOR, fecha, num, pct } from "@/lib/format";
import { Badge, Crest, ResultDot } from "@/components/ui";
import { IntervalBars } from "@/components/charts/charts";

/** Panel del mockup: encabezado del partido + 7 recuadros. Cada recuadro dice qué mide y su muestra. */

function Panel({ title, note, children, className = "" }: { title: string; note?: string; children: ReactNode; className?: string }) {
  return (
    <section className={`rounded-2xl border border-line bg-panel p-4 ${className}`}>
      <h2 className="text-base font-semibold">{title}</h2>
      {note && <p className="mb-3 mt-0.5 text-xs text-mute">{note}</p>}
      {children}
    </section>
  );
}

function Ring({ value, label, count, color }: { value: number; label: string; count: number; color: string }) {
  const r = 30, c = 2 * Math.PI * r;
  return (
    <div className="flex flex-col items-center" role="img" aria-label={`${label}: ${count} partidos, ${Math.round(value * 100)} %`}>
      <svg width="78" height="78" viewBox="0 0 78 78">
        <circle cx="39" cy="39" r={r} fill="none" stroke="rgb(var(--line))" strokeWidth="7" />
        <circle cx="39" cy="39" r={r} fill="none" stroke={color} strokeWidth="7" strokeLinecap="round"
          strokeDasharray={`${c * value} ${c}`} transform="rotate(-90 39 39)" />
        <text x="39" y="44" textAnchor="middle" fontSize="16" fontWeight="700" fill="rgb(var(--ink))">{Math.round(value * 100)}%</text>
      </svg>
      <span className="mt-1 text-sm">{label}</span>
      <span className="text-xs text-mute">{count} partidos</span>
    </div>
  );
}

function cleanSheets(t: TeamReport) { return t.matches.filter((m) => m.goals_against === 0).length; }

function Last20({ t, color }: { t: TeamReport; color: string }) {
  const n = Math.max(t.overall.n, 1);
  const cs = cleanSheets(t);
  return (
    <Panel title={`Últimos ${t.sample_size} partidos · ${t.team}`} note={`Resultados de sus ${t.sample_size} partidos más recientes (todas las competiciones).`}>
      <div className="grid grid-cols-3 gap-2">
        <Ring value={t.overall.wins / n} label="Victorias" count={t.overall.wins} color={HOME_COLOR} />
        <Ring value={t.overall.draws / n} label="Empates" count={t.overall.draws} color={DRAW_COLOR} />
        <Ring value={t.overall.losses / n} label="Derrotas" count={t.overall.losses} color={AWAY_COLOR} />
      </div>
      <dl className="mt-4 grid grid-cols-3 gap-2 border-t border-line pt-3 text-center text-sm">
        <div><dd className="text-lg font-bold tabular-nums" style={{ color }}>{t.overall.goals_for}</dd><dt className="text-xs text-mute">Goles a favor ({num(t.overall.gf_avg, 1)} p/p)</dt></div>
        <div><dd className="text-lg font-bold tabular-nums">{t.overall.goals_against}</dd><dt className="text-xs text-mute">Goles en contra ({num(t.overall.ga_avg, 1)} p/p)</dt></div>
        <div><dd className="text-lg font-bold tabular-nums">{cs}</dd><dt className="text-xs text-mute">Porterías a cero ({pct(cs / n)})</dt></div>
      </dl>
    </Panel>
  );
}

function Probabilities({ a }: { a: Analysis }) {
  const p = a.prediction;
  const { home, away } = a.match;
  if (!p) return (
    <Panel title="Probabilidades del partido">
      <div role="alert" className="rounded-xl border border-red-400/40 bg-red-400/10 p-3 text-sm">
        <strong>Estimación no fiable.</strong> {a.prediction_unavailable_reason ?? a.data_sufficiency.message}
      </div>
    </Panel>
  );
  const rows = [
    { name: home, v: p.p_home, color: HOME_COLOR }, { name: "Empate", v: p.p_draw, color: DRAW_COLOR }, { name: away, v: p.p_away, color: AWAY_COLOR },
  ];
  const top = rows.reduce((x, y) => (y.v > x.v ? y : x));
  const r = 52, c = 2 * Math.PI * r;
  let acc = 0;
  return (
    <Panel title="Probabilidades del partido" note="Estimación del resultado a los 90 min. No es una certeza.">
      <div className="flex flex-col items-center gap-3">
        <svg width="140" height="140" viewBox="0 0 140 140" role="img" aria-label={rows.map((x) => `${x.name} ${pct(x.v)}`).join(", ")} className="shrink-0">
          {rows.map((x) => {
            const len = c * x.v; const el = (
              <circle key={x.name} cx="70" cy="70" r={r} fill="none" stroke={x.color} strokeWidth="18"
                strokeDasharray={`${Math.max(len - 2, 0)} ${c}`} strokeDashoffset={-acc} transform="rotate(-90 70 70)" />);
            acc += len; return el;
          })}
          <text x="70" y="72" textAnchor="middle" fontSize="24" fontWeight="700" fill="rgb(var(--ink))">{pct(top.v)}</text>
          <text x="70" y="90" textAnchor="middle" fontSize="10" fill="rgb(var(--mute))">{top.name.length > 14 ? top.name.slice(0, 13) + "…" : top.name}</text>
        </svg>
        <ul className="w-full space-y-1.5 text-sm">
          {rows.map((x) => (
            <li key={x.name} className="flex items-center justify-between gap-2">
              <span className="flex min-w-0 items-center gap-2"><span className="h-2.5 w-2.5 shrink-0 rounded-full" style={{ background: x.color }} /><span className="truncate">{x.name === "Empate" ? "Empate" : `Gana ${x.name}`}</span></span>
              <b className="whitespace-nowrap tabular-nums">{pct(x.v)}</b>
            </li>
          ))}
        </ul>
      </div>
    </Panel>
  );
}

function Expected({ a }: { a: Analysis }) {
  const p = a.prediction;
  return (
    <Panel title="Goles esperados" note="Promedio de goles que estima el modelo para cada equipo.">
      {!p ? <p className="text-sm text-mute">No disponible: la estimación no es fiable con estos datos.</p> : (
        <>
          <div className="grid grid-cols-2 divide-x divide-line text-center">
            <div><div className="text-3xl font-bold tabular-nums" style={{ color: HOME_COLOR }}>{num(p.expected_home_goals, 1)}</div><div className="truncate px-1 text-sm">{a.match.home}</div></div>
            <div><div className="text-3xl font-bold tabular-nums" style={{ color: AWAY_COLOR }}>{num(p.expected_away_goals, 1)}</div><div className="truncate px-1 text-sm">{a.match.away}</div></div>
          </div>
          <div className="mt-4 flex items-center justify-center gap-3 border-t border-line pt-3">
            <span aria-hidden className="text-3xl">⚽</span>
            <div><div className="text-xs text-mute">Total esperado</div><div className="text-2xl font-bold tabular-nums">{num(p.expected_home_goals + p.expected_away_goals, 1)}</div></div>
          </div>
          <p className="mt-2 text-center text-xs text-mute">Rango 80 %: {p.total_goals_range_80[0]}–{p.total_goals_range_80[1]} goles · Ambos anotan: {pct(p.p_btts)}</p>
        </>
      )}
    </Panel>
  );
}

function Trend10({ a }: { a: Analysis }) {
  const take = (t: TeamReport) => [...t.matches].slice(0, 10).reverse();
  const h = take(a.home), w = take(a.away);
  const len = Math.max(h.length, w.length);
  const data = Array.from({ length: len }, (_, i) => ({ n: i + 1, h: h[i]?.goals_for ?? null, w: w[i]?.goals_for ?? null }));
  return (
    <Panel title="Rendimiento en los últimos 10 partidos" note={`Goles que marcó cada equipo en cada uno de sus últimos ${len} partidos (1 = más antiguo, ${len} = más reciente).`}>
      <div className="h-48" role="img" aria-label="Goles marcados por partido, últimos 10 partidos de cada equipo">
        <ResponsiveContainer>
          <LineChart data={data} margin={{ top: 8, right: 8, left: -22, bottom: 0 }}>
            <CartesianGrid stroke="rgb(var(--line))" vertical={false} />
            <XAxis dataKey="n" stroke="rgb(var(--line))" tick={{ fill: "rgb(var(--mute))", fontSize: 12 }} />
            <YAxis allowDecimals={false} stroke="rgb(var(--line))" tick={{ fill: "rgb(var(--mute))", fontSize: 12 }} />
            <Tooltip contentStyle={{ background: "rgb(var(--panel))", border: "1px solid rgb(var(--line))", borderRadius: 8 }} />
            <Legend wrapperStyle={{ fontSize: 12 }} />
            <Line type="monotone" dataKey="h" name={a.match.home} stroke={HOME_COLOR} strokeWidth={2.5} dot={{ r: 3 }} isAnimationActive={false} connectNulls />
            <Line type="monotone" dataKey="w" name={a.match.away} stroke={AWAY_COLOR} strokeWidth={2.5} dot={{ r: 3 }} isAnimationActive={false} connectNulls />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </Panel>
  );
}

function Intervals({ a }: { a: Analysis }) {
  const hg = a.home.goals_by_interval, ag = a.away.goals_by_interval;
  const none = hg.matches_with_data === 0 && ag.matches_with_data === 0;
  return (
    <Panel title="Goles por intervalo de tiempo" note={none ? undefined : `Goles marcados en cada tramo de 15 min. Cobertura: ${hg.matches_with_data}/${hg.of} y ${ag.matches_with_data}/${ag.of} partidos.`}>
      {none ? <p className="text-sm text-mute">No disponible: la fuente no trae el minuto de los goles.</p> :
        <IntervalBars labels={hg.labels} a={hg.for} b={ag.for} nameA={a.match.home} nameB={a.match.away} colorA={HOME_COLOR} colorB={AWAY_COLOR} />}
    </Panel>
  );
}

function Cards({ a }: { a: Analysis }) {
  const row = (t: TeamReport, color: string) => (
    <div className="rounded-xl bg-panel2 p-3">
      <div className="truncate text-sm font-semibold" style={{ color }}>{t.team}</div>
      {!t.cards ? <p className="text-xs text-mute">Sin datos de tarjetas.</p> : (
        <div className="mt-1 grid grid-cols-2 gap-2 text-center">
          <div><span aria-hidden className="mx-auto mb-1 block h-5 w-3.5 rounded-sm bg-yellow-400" /><b className="text-xl tabular-nums">{t.cards.yellow_total}</b><div className="text-[11px] text-mute">amarillas ({num(t.cards.yellow_avg, 1)} p/p)</div></div>
          <div><span aria-hidden className="mx-auto mb-1 block h-5 w-3.5 rounded-sm bg-red-500" /><b className="text-xl tabular-nums">{t.cards.red_total}</b><div className="text-[11px] text-mute">rojas ({num(t.cards.red_avg, 2)} p/p)</div></div>
        </div>
      )}
    </div>
  );
  return (
    <Panel title="Tarjetas" note={`Últimos ${a.home.sample_size} partidos de cada equipo. Cobertura: ${a.home.cards_coverage.matches_with_data}/${a.home.cards_coverage.of} y ${a.away.cards_coverage.matches_with_data}/${a.away.cards_coverage.of}.`}>
      <div className="space-y-2">{row(a.home, HOME_COLOR)}{row(a.away, AWAY_COLOR)}</div>
    </Panel>
  );
}

function Scorers({ a }: { a: Analysis }) {
  const list = [
    ...a.home.top_scorers.slice(0, 2).map((s) => ({ ...s, team: a.match.home, color: HOME_COLOR })),
    ...a.away.top_scorers.slice(0, 2).map((s) => ({ ...s, team: a.match.away, color: AWAY_COLOR })),
  ];
  return (
    <Panel title="Jugadores destacados" note="Máximos goleadores en los últimos partidos analizados.">
      {list.length === 0 ? <p className="text-sm text-mute">No disponible: la fuente no trae el autor de los goles.</p> : (
        <ul className="space-y-2">
          {list.map((s) => (
            <li key={s.team + s.player} className="flex items-center gap-3 text-sm">
              <Crest name={s.player} color={s.color} size={34} />
              <span className="min-w-0 flex-1 truncate"><b>{s.player}</b> <span className="text-mute">({s.team})</span></span>
              <span className="tabular-nums text-mute">{s.goals} goles</span>
            </li>
          ))}
        </ul>
      )}
    </Panel>
  );
}

export function MatchHero({ a, fixture, standings }: { a: Analysis; fixture?: Fixture | null; standings?: Standings | null }) {
  const pos = (team: string) => {
    const r = standings?.table.find((x) => x.team === team);
    return r ? `Posición: ${r.position}° (${r.points} pts)` : "Posición no disponible";
  };
  const side = (t: TeamReport, color: string, align: "left" | "right") => (
    <div className={`flex flex-1 flex-col items-center gap-2 ${align === "left" ? "md:flex-row" : "md:flex-row-reverse"} md:gap-4`}>
      <Crest name={t.team} color={color} size={72} />
      <div className={`text-center ${align === "left" ? "md:text-left" : "md:text-right"}`}>
        <div className="text-xl font-bold">{t.team}</div>
        <div className="text-sm text-mute">{pos(t.team)}</div>
        <div className={`mt-2 flex justify-center gap-1 ${align === "left" ? "md:justify-start" : "md:justify-end"}`}>
          {t.form.last5.split("").map((r, i) => <ResultDot key={i} r={r} />)}
        </div>
      </div>
    </div>
  );
  const q = new URLSearchParams({ home: a.match.home, away: a.match.away, on: a.match.date });
  return (
    <section className="rounded-2xl border border-line bg-panel p-4 sm:p-6">
      <div className="flex flex-col items-center gap-5 md:flex-row">
        {side(a.home, HOME_COLOR, "left")}
        <div className="text-center md:w-72">
          <div className="text-lg font-extrabold text-home">VS</div>
          <div className="text-sm font-semibold">{fecha(a.match.date, true)}</div>
          {fixture?.kickoff && <div className="text-sm">{fixture.kickoff} (hora Colombia)</div>}
          <div className="text-sm text-mute">{fixture?.venue ?? "Estadio no disponible"}</div>
          <div className="mt-2 flex flex-wrap justify-center gap-1">
            {a.source?.is_demo && <Badge tone="warn">DEMO</Badge>}
            <Badge tone={a.data_sufficiency.level === "alta" ? "good" : a.data_sufficiency.level === "insuficiente" ? "bad" : "warn"}>Datos: {a.data_sufficiency.level}</Badge>
          </div>
          <Link href={`/analisis?${q}`} className="mt-3 inline-block rounded-lg bg-accent px-5 py-2.5 text-sm font-semibold text-white hover:opacity-90">Ver análisis completo</Link>
        </div>
        {side(a.away, AWAY_COLOR, "right")}
      </div>
    </section>
  );
}

export default function Dashboard({ a, fixture, standings }: { a: Analysis; fixture?: Fixture | null; standings?: Standings | null }) {
  return (
    <div className="space-y-4">
      <MatchHero a={a} fixture={fixture} standings={standings} />
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <div className="xl:col-span-1"><Last20 t={a.home} color={HOME_COLOR} /></div>
        <div className="xl:col-span-1"><Last20 t={a.away} color={AWAY_COLOR} /></div>
        <Probabilities a={a} />
        <Expected a={a} />
      </div>
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <Trend10 a={a} />
        <Intervals a={a} />
        <Cards a={a} />
        <Scorers a={a} />
      </div>
      {standings && <p className="text-xs text-mute">{standings.note} Partidos contados en la tabla: {standings.matches_counted}.</p>}
      <p className="rounded-xl border border-line bg-panel p-3 text-xs text-mute">{a.disclaimer}</p>
    </div>
  );
}
