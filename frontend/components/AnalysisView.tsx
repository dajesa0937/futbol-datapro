"use client";
import Link from "next/link";
import { ReactNode, useEffect, useState } from "react";
import type { Analysis, TeamReport } from "@/lib/api";
import { AWAY_COLOR, HOME_COLOR, fecha, fechaHora, num, pct } from "@/lib/format";
import { Badge, Card, Crest, Explain, NotAvailable, ResultDot, Stat } from "@/components/ui";
import {
  CompareBars, GoalsTrend, Heatmap, IntervalBars, ProbDonut, ScoreBars, TotalGoalsBars,
} from "@/components/charts/charts";


const TABS = [
  ["resumen", "Resumen"], ["ultimos", "Últimos 20"], ["goles", "Goles"], ["tarjetas", "Tarjetas"],
  ["jugadores", "Jugadores"], ["contexto", "Contexto"], ["prob", "Probabilidades"], ["datos", "Datos y método"],
] as const;
type Tab = (typeof TABS)[number][0];

const SUFF_TONE = { insuficiente: "bad", baja: "warn", media: "info", alta: "good" } as const;

export default function AnalysisView({ a, actions, initialTab }: { a: Analysis; actions?: ReactNode; initialTab?: string | null }) {
  const valid = (v?: string | null): Tab => (TABS.some(([id]) => id === v) ? (v as Tab) : "resumen");
  const [tab, setTab] = useState<Tab>(valid(initialTab));
  useEffect(() => { setTab(valid(initialTab)); }, [initialTab]);
  const { home, away } = a.match;
  return (
    <div>
      <Card className="mb-4">
        <div className="flex flex-col items-center gap-4 sm:flex-row sm:justify-between">
          <div className="flex items-center gap-3"><Crest name={home} color={HOME_COLOR} /><div><div className="text-lg font-bold">{home}</div><div className="text-xs text-mute">Local</div></div></div>
          <div className="text-center">
            <div className="text-sm font-semibold text-mute">VS</div>
            <div className="text-sm">{fecha(a.match.date, true)}</div>
            <div className="mt-1 flex flex-wrap items-center justify-center gap-1">
              {a.source?.is_demo && <Badge tone="warn">DEMO</Badge>}
              <Badge tone={SUFF_TONE[a.data_sufficiency.level]}>Datos: {a.data_sufficiency.level}</Badge>
            </div>
          </div>
          <div className="flex items-center gap-3"><div className="text-right"><div className="text-lg font-bold">{away}</div><div className="text-xs text-mute">Visitante</div></div><Crest name={away} color={AWAY_COLOR} /></div>
        </div>
        {actions && <div className="mt-4 flex flex-wrap justify-center gap-2">{actions}</div>}
      </Card>

      <div role="tablist" aria-label="Secciones del análisis" className="mb-4 flex gap-1 overflow-x-auto rounded-xl border border-line bg-panel p-1">
        {TABS.map(([id, label]) => (
          <button key={id} role="tab" aria-selected={tab === id} onClick={() => setTab(id)}
            className={`whitespace-nowrap rounded-lg px-3 py-2 text-sm ${tab === id ? "bg-accent/20 font-semibold text-accent" : "text-mute hover:bg-panel2"}`}>{label}</button>
        ))}
      </div>

      <div role="tabpanel" className="space-y-4">
        {tab === "resumen" && <Resumen a={a} />}
        {tab === "ultimos" && <Ultimos a={a} />}
        {tab === "goles" && <Goles a={a} />}
        {tab === "tarjetas" && <Tarjetas a={a} />}
        {tab === "jugadores" && <Jugadores a={a} />}
        {tab === "contexto" && <Contexto a={a} />}
        {tab === "prob" && <Prob a={a} />}
        {tab === "datos" && <Datos a={a} />}
      </div>
      <p className="mt-6 rounded-xl border border-line bg-panel p-3 text-xs text-mute">{a.disclaimer}</p>
    </div>
  );
}

/* ---------------------------------------------------------------- Resumen */
function Unreliable({ a }: { a: Analysis }) {
  return (
    <Card title="Estimación del partido">
      <div role="alert" className="rounded-xl border border-red-400/40 bg-red-400/10 p-4 text-sm text-red-900 dark:text-red-100">
        <strong>La estimación no es fiable.</strong> {a.prediction_unavailable_reason ?? a.data_sufficiency.message}
        <br />No se muestran probabilidades porque no hay datos suficientes para calcularlas con rigor.
      </div>
    </Card>
  );
}

function Resumen({ a }: { a: Analysis }) {
  const { home, away } = a.match;
  const p = a.prediction;
  const cmp = [
    { label: "Goles a favor", home: a.home.overall.gf_avg, away: a.away.overall.gf_avg },
    { label: "Goles en contra", home: a.home.overall.ga_avg, away: a.away.overall.ga_avg },
    { label: "Puntos", home: a.home.overall.points_per_match, away: a.away.overall.points_per_match },
  ].map((r) => ({ ...r, home: r.home == null ? null : +r.home.toFixed(2), away: r.away == null ? null : +r.away.toFixed(2) }));
  return (
    <>
      {a.data_sufficiency.level !== "alta" && a.data_sufficiency.level !== "insuficiente" && (
        <div role="note" className="rounded-xl border border-amber-400/40 bg-amber-400/10 p-3 text-sm text-amber-900 dark:text-amber-100">{a.data_sufficiency.message}</div>
      )}
      {!p ? <Unreliable a={a} /> : (
        <>
          <Card title="¿Quién tiene más probabilidades de ganar?">
            <ProbDonut home={home} away={away} p={{ home: p.p_home, draw: p.p_draw, away: p.p_away }} />
            <Explain>Cada porción es la probabilidad estimada de cada resultado al final de los 90 minutos. Se calculó con un modelo estadístico de goles ajustado con {a.model?.trained_on_matches} partidos oficiales previos. Es una estimación, no una certeza: un resultado poco probable puede ocurrir.</Explain>
          </Card>
          <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
            <Stat label={`Goles esperados ${home}`} value={num(p.expected_home_goals)} color={HOME_COLOR} sub="promedio estimado" />
            <Stat label={`Goles esperados ${away}`} value={num(p.expected_away_goals)} color={AWAY_COLOR} sub="promedio estimado" />
            <Stat label="Ambos equipos anotan" value={pct(p.p_btts)} sub="probabilidad" />
            <Stat label="Más de 2,5 goles" value={pct(p.over_under["2.5"].over)} sub="probabilidad" />
          </div>
        </>
      )}
      <Card title="Comparación de los últimos partidos">
        <CompareBars data={cmp} home={home} away={away} />
        <Explain>Promedios POR PARTIDO (goles a favor, goles en contra y puntos) en los últimos {a.home.sample_size} ({home}) y {a.away.sample_size} ({away}) partidos anteriores a la fecha del encuentro, de todas las competiciones. Más goles a favor y menos en contra es mejor.</Explain>
      </Card>
      <div className="grid gap-4 md:grid-cols-2">
        {[a.home, a.away].map((t, i) => (
          <Card key={t.team} title={`Forma de ${t.team}`}>
            <div className="flex items-center gap-1">{t.form.last5.split("").map((r, k) => <ResultDot key={k} r={r} />)}</div>
            <p className="mt-2 text-sm text-mute">Últimos 5 (de izquierda a derecha: más reciente a más antiguo). G = ganó, E = empató, P = perdió.</p>
            <div className="mt-3 grid grid-cols-3 gap-2 text-center">
              <Stat label="Victorias" value={t.overall.wins} color={i ? AWAY_COLOR : HOME_COLOR} sub={`de ${t.overall.n}`} />
              <Stat label="Empates" value={t.overall.draws} />
              <Stat label="Derrotas" value={t.overall.losses} />
            </div>
          </Card>
        ))}
      </div>
    </>
  );
}

/* ---------------------------------------------------------------- Últimos 20 */
function TeamToggle({ a, render }: { a: Analysis; render: (t: TeamReport, color: string) => ReactNode }) {
  const [side, setSide] = useState<"home" | "away">("home");
  const t = a[side];
  return (
    <div>
      <div className="mb-3 inline-flex rounded-lg border border-line bg-panel p-1" role="group" aria-label="Elegir equipo">
        {(["home", "away"] as const).map((s) => (
          <button key={s} aria-pressed={side === s} onClick={() => setSide(s)}
            className={`rounded-md px-3 py-1.5 text-sm ${side === s ? "bg-accent/20 font-semibold" : "text-mute"}`}>{a[s].team}</button>
        ))}
      </div>
      {render(t, side === "home" ? HOME_COLOR : AWAY_COLOR)}
    </div>
  );
}

function Ultimos({ a }: { a: Analysis }) {
  return (
    <TeamToggle a={a} render={(t, color) => {
      const trend = [...t.matches].reverse().map((m) => ({ date: m.date, gf: m.goals_for, ga: m.goals_against }));
      return (
        <div className="space-y-4">
          {!t.enough_data && <div role="note" className="rounded-xl border border-amber-400/40 bg-amber-400/10 p-3 text-sm text-amber-900 dark:text-amber-100">Solo hay {t.sample_size} partidos previos disponibles (se pedían {t.requested}).</div>}
          <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
            <Stat label="Partidos analizados" value={t.sample_size} />
            <Stat label="Goles a favor" value={t.overall.goals_for} sub={`${num(t.overall.gf_avg)} por partido`} color={color} />
            <Stat label="Goles en contra" value={t.overall.goals_against} sub={`${num(t.overall.ga_avg)} por partido`} />
            <Stat label="Puntos por partido" value={num(t.overall.points_per_match)} sub="3 ganar · 1 empatar" />
          </div>
          <Card title="Localía y visita">
            <div className="grid gap-3 sm:grid-cols-2">
              {([["Como local", t.home], ["Como visitante", t.away]] as const).map(([l, s]) => (
                <div key={l} className="rounded-xl bg-panel2 p-3 text-sm">
                  <div className="font-semibold">{l} <span className="text-mute">({s.n} partidos)</span></div>
                  {s.n === 0 ? <p className="text-mute">Sin partidos en la muestra.</p> :
                    <p className="text-mute">{s.wins}G · {s.draws}E · {s.losses}P — goles {s.goals_for}:{s.goals_against} — {num(s.points_per_match)} pts/partido</p>}
                </div>
              ))}
            </div>
          </Card>
          <Card title="Por competición">
            <div className="flex flex-wrap gap-2">
              {Object.entries(t.by_competition).map(([k, s]) => (
                <div key={k} className="rounded-xl bg-panel2 px-3 py-2 text-sm"><Badge tone={k === "amistoso" ? "neutral" : "info"}>{s.label}</Badge> {s.n} partidos · {s.wins}G {s.draws}E {s.losses}P</div>
              ))}
            </div>
            <Explain>Los partidos amistosos se muestran pero NO se usan para ajustar el modelo de estimación.</Explain>
          </Card>
          <Card title="Evolución de goles">
            <GoalsTrend rows={trend} color={color} />
            <Explain>Cada punto es un partido, del más antiguo (izquierda) al más reciente (derecha), con goles marcados y recibidos. Muestra: {t.sample_size} partidos.</Explain>
          </Card>
          <Card title="Detalle partido a partido">
            <div className="overflow-x-auto">
              <table className="w-full min-w-[560px] text-sm">
                <thead className="text-left text-xs text-mute"><tr><th className="py-1">Fecha</th><th>Competición</th><th>Rival</th><th>Condición</th><th className="text-center">Marcador</th><th className="text-center">Res.</th></tr></thead>
                <tbody>
                  {t.matches.map((m) => (
                    <tr key={m.id} className="border-t border-line">
                      <td className="py-1.5 whitespace-nowrap">{fecha(m.date)}</td>
                      <td><span className="text-mute">{m.competition_label}</span><div className="text-[11px] text-mute/70">{m.season}</div></td>
                      <td>{m.opponent}</td><td className="text-mute">{m.venue_role}</td>
                      <td className="text-center font-semibold tabular-nums">{m.goals_for}–{m.goals_against}</td>
                      <td className="text-center"><ResultDot r={m.result} /></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>
        </div>
      );
    }} />
  );
}

/* ---------------------------------------------------------------- Goles */
function Goles({ a }: { a: Analysis }) {
  const { home, away } = a.match;
  const hg = a.home.goals_by_interval, ag = a.away.goals_by_interval;
  const noMinutes = hg.matches_with_data === 0 && ag.matches_with_data === 0;
  if (noMinutes) return <NotAvailable>la fuente de datos no ofrece el minuto de cada gol.</NotAvailable>;
  const exp = a.prediction?.goals_by_interval_expected;
  return (
    <>
      <Card title={`Goles a favor por minuto (últimos ${a.home.sample_size} / ${a.away.sample_size} partidos)`}>
        <IntervalBars labels={hg.labels} a={hg.for} b={ag.for} nameA={home} nameB={away} colorA={HOME_COLOR} colorB={AWAY_COLOR} />
        <Explain>Cantidad de goles que anotó cada equipo en cada tramo de 15 minutos. Cobertura de minutos: {hg.matches_with_data}/{hg.of} partidos de {home} y {ag.matches_with_data}/{ag.of} de {away}.</Explain>
      </Card>
      <Card title="Goles recibidos por minuto">
        <IntervalBars labels={hg.labels} a={hg.against} b={ag.against} nameA={home} nameB={away} colorA={HOME_COLOR} colorB={AWAY_COLOR} />
        <Explain>Los goles que recibió cada equipo, por tramo. Ayuda a ver en qué momentos es más vulnerable.</Explain>
      </Card>
      <Card title="Mapa de calor: goles anotados y recibidos">
        <Heatmap labels={hg.labels} rows={[
          { name: `${home} · a favor`, values: hg.for, color: HOME_COLOR }, { name: `${home} · en contra`, values: hg.against, color: "rgb(var(--bad))" },
          { name: `${away} · a favor`, values: ag.for, color: AWAY_COLOR }, { name: `${away} · en contra`, values: ag.against, color: "rgb(var(--bad))" },
        ]} />
      </Card>
      {exp?.home && exp?.away && (
        <Card title="Goles esperados por tramo en este partido">
          <Heatmap labels={exp.home.labels} decimals={2} rows={[
            { name: home, values: exp.home.expected, color: HOME_COLOR }, { name: away, values: exp.away.expected, color: AWAY_COLOR },
          ]} />
          <Explain>Reparte los goles esperados del partido según cómo ha marcado cada equipo por tramos, mezclado con el patrón de toda la liga para no depender de pocos goles. Estimación simple, no validada por separado.</Explain>
        </Card>
      )}
    </>
  );
}

/* ---------------------------------------------------------------- Tarjetas */
function Tarjetas({ a }: { a: Analysis }) {
  const c = a.cards_estimate;
  return (
    <>
      <div className="grid gap-4 md:grid-cols-2">
        {[a.home, a.away].map((t, i) => (
          <Card key={t.team} title={`Tarjetas de ${t.team}`}>
            {!t.cards ? <NotAvailable>la fuente no ofrece tarjetas para estos partidos.</NotAvailable> : (
              <div className="grid grid-cols-2 gap-3">
                <Stat label="Amarillas / partido" value={num(t.cards.yellow_avg)} color={i ? AWAY_COLOR : HOME_COLOR} sub={`${t.cards.yellow_total} en ${t.cards.n} partidos`} />
                <Stat label="Rojas / partido" value={num(t.cards.red_avg)} sub={`${t.cards.red_total} en ${t.cards.n} partidos`} />
              </div>
            )}
            <Explain>Cobertura: {t.cards_coverage.matches_with_data} de {t.cards_coverage.of} partidos con datos de tarjetas.</Explain>
          </Card>
        ))}
      </div>
      <Card title="Estimación de tarjetas del partido" right={<Badge tone="warn">estimación simple · sin validar</Badge>}>
        {!c.reliable ? <NotAvailable>{c.reason}</NotAvailable> : (
          <>
            <div className="grid grid-cols-3 gap-3">
              <Stat label={a.match.home} value={num(c.home_expected)} color={HOME_COLOR} />
              <Stat label={a.match.away} value={num(c.away_expected)} color={AWAY_COLOR} />
              <Stat label="Total esperado" value={num(c.total_expected)} />
            </div>
            <table className="mt-4 w-full text-sm">
              <thead className="text-left text-xs text-mute"><tr><th>Línea de tarjetas</th><th className="text-right">Más de</th><th className="text-right">Menos de</th></tr></thead>
              <tbody>{Object.entries(c.over_under ?? {}).map(([line, v]) => (
                <tr key={line} className="border-t border-line"><td className="py-1.5">{line.replace(".", ",")}</td><td className="text-right tabular-nums">{pct(v.over)}</td><td className="text-right tabular-nums">{pct(v.under)}</td></tr>
              ))}</tbody>
            </table>
            <Explain>Se cuentan amarillas y rojas. Es un promedio ajustado hacia la media de la liga, sin modelo validado. No se aplica el árbitro: esta fuente no informa el árbitro designado del próximo partido.</Explain>
          </>
        )}
      </Card>
    </>
  );
}

/* ---------------------------------------------------------------- Jugadores */
function Jugadores({ a }: { a: Analysis }) {
  const probs = a.prediction?.scorer_probabilities ?? [];
  return (
    <>
      <div className="grid gap-4 md:grid-cols-2">
        {[a.home, a.away].map((t, i) => (
          <Card key={t.team} title={`Goleadores de ${t.team}`}>
            {t.top_scorers.length === 0 ? <NotAvailable>no hay detalle de goleadores en la muestra.</NotAvailable> : (
              <ol className="space-y-2">
                {t.top_scorers.map((s) => (
                  <li key={s.player} className="flex items-center justify-between rounded-lg bg-panel2 px-3 py-2">
                    <span>{s.player} <span className="text-xs text-mute">{s.position ?? ""}</span></span>
                    <span className="text-lg font-bold tabular-nums" style={{ color: i ? AWAY_COLOR : HOME_COLOR }}>{s.goals}</span>
                  </li>
                ))}
              </ol>
            )}
            <Explain>Goles en los últimos {t.sample_size} partidos ({t.team_goals_with_scorer_detail} con detalle de autor). Posiciones de los goles: {Object.entries(t.goals_by_position).map(([k, v]) => `${k} ${v}`).join(" · ") || "sin dato"}.</Explain>
          </Card>
        ))}
      </div>
      <Card title="Probabilidad de que anoten" right={<Badge tone="warn">estimación simple</Badge>}>
        {probs.length === 0 ? <NotAvailable>no hay suficientes goles con autor registrado para estimarlo con criterio.</NotAvailable> : (
          <>
            <ul className="space-y-2">
              {probs.map((s) => (
                <li key={s.player} className="flex items-center justify-between rounded-lg bg-panel2 px-3 py-2 text-sm">
                  <span>{s.player} <span className="text-mute">({s.team})</span></span><span className="font-bold tabular-nums">{pct(s.p_scores)}</span>
                </li>
              ))}
            </ul>
            <Explain>Combina la participación del jugador en los goles de su equipo con los goles esperados del partido. <strong>Supone que juega:</strong> no se conocen alineaciones, lesiones ni suspensiones con esta fuente.</Explain>
          </>
        )}
      </Card>
    </>
  );
}

/* ---------------------------------------------------------------- Contexto */
function Contexto({ a }: { a: Analysis }) {
  const c = a.context;
  return (
    <>
      <Card title="Descanso">
        <div className="grid grid-cols-2 gap-3">
          <Stat label={a.match.home} value={c.rest_days.home ?? "—"} sub="días desde su último partido" color={HOME_COLOR} />
          <Stat label={a.match.away} value={c.rest_days.away ?? "—"} sub="días desde su último partido" color={AWAY_COLOR} />
        </div>
        <Explain>Calculado con el último partido registrado antes de la fecha del encuentro. No incluye viajes ni congestión de calendario.</Explain>
      </Card>
      <Card title="Clima"><NotAvailable>{c.weather.reason}</NotAvailable></Card>
      <Card title="Alineaciones, lesiones y suspensiones"><NotAvailable>{c.lineups.reason}</NotAvailable></Card>
    </>
  );
}

/* ---------------------------------------------------------------- Probabilidades */
function Prob({ a }: { a: Analysis }) {
  const p = a.prediction;
  if (!p) return <Unreliable a={a} />;
  const { home, away } = a.match;
  return (
    <>
      <Card title="Marcadores más probables">
        <ScoreBars scores={p.top_scores} home={home} away={away} />
        <Explain>Marcador «{home} – {away}». Ningún marcador individual supera una probabilidad moderada: incluso el más probable ocurre pocas veces de cada diez. Azul: gana el local · ámbar: gana el visitante · gris: empate.</Explain>
      </Card>
      <Card title="Goles totales del partido">
        <TotalGoalsBars dist={p.total_goals_distribution} />
        <Explain>Probabilidad de cada total de goles (suma de ambos equipos). Rango del 80 % central: entre {p.total_goals_range_80[0]} y {p.total_goals_range_80[1]} goles.</Explain>
      </Card>
      <Card title="Más / menos goles">
        <table className="w-full text-sm">
          <thead className="text-left text-xs text-mute"><tr><th>Línea</th><th className="text-right">Más de</th><th className="text-right">Menos de</th></tr></thead>
          <tbody>{Object.entries(p.over_under).map(([line, v]) => (
            <tr key={line} className="border-t border-line"><td className="py-1.5">{line.replace(".", ",")} goles</td><td className="text-right tabular-nums">{pct(v.over, 1)}</td><td className="text-right tabular-nums">{pct(v.under, 1)}</td></tr>
          ))}</tbody>
        </table>
      </Card>
      <Card title="Factores que respaldan la estimación">
        <ul className="space-y-2 text-sm">{p.factors.map((f) => <li key={f.name} className="rounded-lg bg-panel2 p-3"><strong>{f.name}.</strong> <span className="text-mute">{f.text}</span></li>)}</ul>
      </Card>
      <Card title="Comprobación por simulación">
        <p className="text-sm text-mute">Se simularon {p.monte_carlo.n_sims.toLocaleString("es-CO")} partidos (semilla {p.monte_carlo.seed}): local {pct(p.monte_carlo.p_home.prob, 1)} ± {pct(p.monte_carlo.p_home.std_error, 1)}, empate {pct(p.monte_carlo.p_draw.prob, 1)} ± {pct(p.monte_carlo.p_draw.std_error, 1)}, visitante {pct(p.monte_carlo.p_away.prob, 1)} ± {pct(p.monte_carlo.p_away.std_error, 1)}. Coincide con el cálculo exacto; la simulación solo confirma y mide el error numérico.</p>
      </Card>
    </>
  );
}

/* ---------------------------------------------------------------- Datos y método */
function Datos({ a }: { a: Analysis }) {
  return (
    <>
      <Card title="Fuente y cobertura">
        <dl className="grid gap-2 text-sm sm:grid-cols-2">
          <div><dt className="text-mute">Fuente</dt><dd>{a.source?.name ?? "—"} {a.source?.is_demo && <Badge tone="warn">DEMO</Badge>}</dd></div>
          <div><dt className="text-mute">Actualización de la fuente</dt><dd>{a.source ? fechaHora(a.source.updated_at) : "—"}</dd></div>
          <div><dt className="text-mute">Corte de datos</dt><dd>{a.data_cutoff}</dd></div>
          <div><dt className="text-mute">Análisis generado</dt><dd>{fechaHora(a.generated_at)}</dd></div>
          <div><dt className="text-mute">Partidos previos ({a.match.home})</dt><dd>{a.home.sample_size} de {a.home.requested} · tarjetas {a.home.cards_coverage.matches_with_data} · minutos de gol {a.home.goals_by_interval.matches_with_data}</dd></div>
          <div><dt className="text-mute">Partidos previos ({a.match.away})</dt><dd>{a.away.sample_size} de {a.away.requested} · tarjetas {a.away.cards_coverage.matches_with_data} · minutos de gol {a.away.goals_by_interval.matches_with_data}</dd></div>
        </dl>
        <Explain>{a.data_sufficiency.message} El nivel «{a.data_sufficiency.level}» describe cuántos datos hay, no la probabilidad de acertar.</Explain>
      </Card>
      <Card title="Modelo">
        {!a.model ? <NotAvailable>no se pudo ajustar el modelo con los datos disponibles.</NotAvailable> : (
          <>
            <ul className="space-y-1 text-sm text-mute">
              <li>Tipo: {a.model.type} (versión {a.model.version}).</li>
              <li>Entrenado con {a.model.trained_on_matches} partidos oficiales anteriores al {fecha(a.model.as_of)} ({a.model.training_competitions.join(", ")}); los amistosos se excluyen.</li>
              <li>Ventaja de local estimada: ×{Math.exp(a.model.home_advantage).toFixed(2)} en goles esperados.</li>
              <li>Convergencia del ajuste: {a.model.converged ? "correcta" : "no confirmada"}.</li>
            </ul>
            <Explain>El rendimiento del modelo frente a referencias simples se mide aparte con validación retrospectiva. <Link className="text-accent underline" href="/fuentes">Ver calidad del modelo</Link>.</Explain>
          </>
        )}
      </Card>
    </>
  );
}
