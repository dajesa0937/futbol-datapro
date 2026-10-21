"use client";
import { useRouter } from "next/navigation";
import { useEffect, useMemo, useState } from "react";
import { DemoBanner } from "@/components/DemoBanner";
import { Badge, Card, Crest, ErrorBox, Loading } from "@/components/ui";
import { Fixture, api } from "@/lib/api";
import { AWAY_COLOR, HOME_COLOR, fecha } from "@/lib/format";
import { useApp } from "@/lib/state";

/** Selección de partidos: filtra por temporada y fecha y abre el panel del partido elegido. */
export default function Partidos() {
  const router = useRouter();
  const { season, seasons, setSeason, select } = useApp();
  const [data, setData] = useState<{ fixtures: Fixture[]; is_demo: boolean } | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [day, setDay] = useState("");
  useEffect(() => { api<{ fixtures: Fixture[]; is_demo: boolean }>("/api/fixtures").then(setData).catch((e) => setErr(e.message)); }, []);

  const list = useMemo(() => (data?.fixtures ?? []).filter((f) => (!season || f.season === season) && (!day || f.date === day)), [data, season, day]);
  const hasOtherSeasons = (data?.fixtures ?? []).some((f) => f.season !== season);

  function open(f: Fixture) {
    select({ home: f.home, away: f.away, on: f.date });
    router.push("/");
  }
  const sel = "w-full rounded-lg border border-line bg-panel2 px-3 py-2.5 text-ink";
  return (
    <div className="mx-auto max-w-3xl space-y-4">
      <h1 className="text-2xl font-extrabold">Selección de partidos</h1>
      {data && <DemoBanner isDemo={data.is_demo} />}
      <Card>
        <div className="grid gap-3 sm:grid-cols-2">
          <label className="text-sm text-mute">Temporada
            <select className={sel} value={season} onChange={(e) => setSeason(e.target.value)}>{seasons.map((s) => <option key={s}>{s}</option>)}</select>
          </label>
          <label className="text-sm text-mute">Fecha
            <div className="flex gap-2"><input type="date" className={sel} value={day} onChange={(e) => setDay(e.target.value)} />
              {day && <button onClick={() => setDay("")} className="rounded-lg border border-line px-3 text-sm">Todas</button>}</div>
          </label>
        </div>
      </Card>
      {err && <ErrorBox message={err} />}
      {!data && !err && <Loading />}
      {data && list.length === 0 && (
        <Card><p className="text-mute">No hay partidos programados{season ? ` en la temporada ${season}` : ""}{day ? " para esa fecha" : ""}.
          {hasOtherSeasons ? " Prueba con otra temporada o quita el filtro de fecha." : ""} También puedes elegir dos equipos manualmente en <b>Analizar</b>.</p></Card>
      )}
      <ul className="space-y-3">
        {list.map((f) => (
          <li key={f.id}><Card>
            <div className="mb-3 flex items-center justify-between text-sm text-mute"><span>{fecha(f.date, true)} · {f.kickoff ?? "hora por confirmar"}</span><Badge>{f.competition === "liga_betplay" ? "Liga BetPlay" : f.competition}</Badge></div>
            <div className="grid grid-cols-[1fr_auto_1fr] items-center gap-3">
              <div className="flex items-center gap-3"><Crest name={f.home} color={HOME_COLOR} size={44} /><b className="min-w-0 break-words">{f.home}</b></div>
              <span className="text-mute">vs</span>
              <div className="flex flex-row-reverse items-center gap-3 text-right"><Crest name={f.away} color={AWAY_COLOR} size={44} /><b className="min-w-0 break-words">{f.away}</b></div>
            </div>
            <div className="mt-3 flex items-center justify-between gap-3">
              <span className="truncate text-xs text-mute">{f.venue ?? "Estadio no disponible"}</span>
              <button onClick={() => open(f)} className="rounded-lg bg-accent px-5 py-2 text-sm font-semibold text-white hover:opacity-90">Analizar</button>
            </div>
          </Card></li>
        ))}
      </ul>
    </div>
  );
}
