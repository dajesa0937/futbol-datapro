"use client";
import { useRouter } from "next/navigation";
import { FormEvent, useEffect, useState } from "react";
import { api } from "@/lib/api";
import { Card } from "@/components/ui";

export default function MatchPicker({ home = "", away = "", on = "" }: { home?: string; away?: string; on?: string }) {
  const router = useRouter();
  const [teams, setTeams] = useState<string[]>([]);
  const [h, setH] = useState(home);
  const [a, setA] = useState(away);
  const [d, setD] = useState(on);
  const [err, setErr] = useState<string | null>(null);
  useEffect(() => { api<{ teams: string[] }>("/api/teams").then((r) => setTeams(r.teams)).catch((e) => setErr(e.message)); }, []);
  useEffect(() => { setH(home); setA(away); setD(on); }, [home, away, on]);

  function submit(e: FormEvent) {
    e.preventDefault();
    if (!h || !a) return setErr("Elige los dos equipos.");
    if (h === a) return setErr("Elige dos equipos distintos.");
    setErr(null);
    const q = new URLSearchParams({ home: h, away: a });
    if (d) q.set("on", d);
    router.push(`/analisis?${q.toString()}`);
  }
  const sel = "w-full rounded-lg border border-line bg-panel2 px-3 py-2.5 text-ink";
  return (
    <Card title="Elegir equipos">
      <form onSubmit={submit} className="grid gap-3 md:grid-cols-[1fr_1fr_auto_auto] md:items-end">
        <label className="text-sm text-mute">Local
          <select className={sel} value={h} onChange={(e) => setH(e.target.value)}><option value="">Seleccionar…</option>{teams.map((t) => <option key={t}>{t}</option>)}</select>
        </label>
        <label className="text-sm text-mute">Visitante
          <select className={sel} value={a} onChange={(e) => setA(e.target.value)}><option value="">Seleccionar…</option>{teams.map((t) => <option key={t}>{t}</option>)}</select>
        </label>
        <label className="text-sm text-mute">Fecha del partido (opcional)
          <input type="date" className={sel} value={d} onChange={(e) => setD(e.target.value)} />
        </label>
        <button type="submit" className="rounded-lg bg-accent px-5 py-2.5 font-semibold text-white hover:opacity-90">Analizar</button>
      </form>
      {err && <p role="alert" className="mt-2 text-sm text-red-700 dark:text-red-300">{err}</p>}
    </Card>
  );
}
