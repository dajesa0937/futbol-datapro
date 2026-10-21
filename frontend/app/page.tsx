"use client";
import { useEffect, useState } from "react";
import Dashboard from "@/components/Dashboard";
import { DemoBanner } from "@/components/DemoBanner";
import MatchPicker from "@/components/MatchPicker";
import { Card, ErrorBox, Loading } from "@/components/ui";
import { Analysis, Fixture, Standings, api } from "@/lib/api";
import { useApp } from "@/lib/state";

/** Inicio: muestra el panel del partido elegido (o el próximo partido programado). */
export default function Inicio() {
  const { selected, season } = useApp();
  const [fixtures, setFixtures] = useState<Fixture[] | null>(null);
  const [a, setA] = useState<Analysis | null>(null);
  const [standings, setStandings] = useState<Standings | null>(null);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => { api<{ fixtures: Fixture[] }>("/api/fixtures").then((r) => setFixtures(r.fixtures)).catch((e) => setErr(e.message)); }, []);

  const pick = selected ?? (fixtures && fixtures[0] ? { home: fixtures[0].home, away: fixtures[0].away, on: fixtures[0].date } : null);
  const key = pick ? `${pick.home}|${pick.away}|${pick.on}` : "";
  useEffect(() => {
    if (!pick) return;
    let cancel = false;
    setA(null); setErr(null);
    api<Analysis>(`/api/analysis?${new URLSearchParams({ home: pick.home, away: pick.away, ...(pick.on ? { on: pick.on } : {}) })}`)
      .then((r) => !cancel && setA(r)).catch((e) => !cancel && setErr(e.message));
    return () => { cancel = true; };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [key]);
  const fx = a ? fixtures?.find((f) => f.home === a.match.home && f.away === a.match.away && f.date === a.match.date) : null;
  const stSeason = fx?.season ?? season;
  useEffect(() => {
    if (!a || !stSeason) return;
    api<Standings>(`/api/standings?${new URLSearchParams({ season: stSeason, on: a.match.date })}`).then(setStandings).catch(() => setStandings(null));
  }, [a, stSeason]);

  return (
    <div className="space-y-4">
      {a?.source && <DemoBanner isDemo={a.source.is_demo} />}
      {err && <ErrorBox message={err} />}
      {!a && !err && (fixtures === null || pick) && <Loading text="Calculando el panel del partido…" />}
      {fixtures && fixtures.length === 0 && !selected && (
        <Card title="Sin partidos programados"><p className="text-mute">La fuente de datos no tiene partidos próximos. Elige dos equipos para analizarlos.</p></Card>
      )}
      {a && <Dashboard a={a} fixture={fx} standings={standings} />}
      {(!pick || a) && <MatchPicker home={pick?.home} away={pick?.away} on={pick?.on} />}
    </div>
  );
}
