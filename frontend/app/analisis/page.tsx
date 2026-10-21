"use client";
import { Suspense, useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import AnalysisView from "@/components/AnalysisView";
import { DemoBanner } from "@/components/DemoBanner";
import MatchPicker from "@/components/MatchPicker";
import { ErrorBox, Loading } from "@/components/ui";
import { Analysis, api } from "@/lib/api";
import { useApp } from "@/lib/state";

function Inner() {
  const sp = useSearchParams();
  const { selected, select } = useApp();
  const vista = sp.get("vista");
  const home = sp.get("home") ?? selected?.home ?? "", away = sp.get("away") ?? selected?.away ?? "", on = sp.get("on") ?? selected?.on ?? "";
  const [a, setA] = useState<Analysis | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [saved, setSaved] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    setA(null); setErr(null); setSaved(null);
    if (!home || !away) return;
    const q = new URLSearchParams({ home, away });
    if (on) q.set("on", on);
    let cancel = false;
    api<Analysis>(`/api/analysis?${q}`).then((r) => { if (!cancel) { setA(r); select({ home: r.match.home, away: r.match.away, on: r.match.date }); } }).catch((e) => !cancel && setErr(e.message));
    return () => { cancel = true; };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [home, away, on]);

  async function save() {
    if (!a) return;
    setSaving(true); setSaved(null);
    try {
      await api("/api/history", { method: "POST", body: JSON.stringify({ home: a.match.home, away: a.match.away, date: a.match.date }) });
      setSaved("Guardado en el historial.");
    } catch (e) { setSaved(`No se pudo guardar: ${(e as Error).message}`); }
    finally { setSaving(false); }
  }

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-extrabold">Analizar partido</h1>
      {a?.source && <DemoBanner isDemo={a.source.is_demo} />}
      <MatchPicker home={home} away={away} on={on} />
      {!home && !away && <p className="text-mute">Elige dos equipos para ver el informe.</p>}
      {home && away && !a && !err && <Loading text="Calculando análisis…" />}
      {err && <ErrorBox message={err} />}
      {a && (
        <AnalysisView a={a} initialTab={vista} actions={<>
          <button onClick={save} disabled={saving} className="rounded-lg border border-line bg-panel2 px-4 py-2 text-sm font-semibold hover:bg-line disabled:opacity-50">{saving ? "Guardando…" : "Guardar en historial"}</button>
          <button disabled title="Disponible en una próxima etapa" className="cursor-not-allowed rounded-lg border border-dashed border-line px-4 py-2 text-sm text-mute/60">Informe PDF (próximamente)</button>
          {saved && <span role="status" className="self-center text-sm text-mute">{saved}</span>}
        </>} />
      )}
    </div>
  );
}

export default function Page() {
  return <Suspense fallback={<Loading />}><Inner /></Suspense>;
}
