"use client";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import AnalysisView from "@/components/AnalysisView";
import { DemoBanner } from "@/components/DemoBanner";
import { ErrorBox, Loading } from "@/components/ui";
import { Analysis, api } from "@/lib/api";
import { fechaHora } from "@/lib/format";

export default function Guardado() {
  const { id } = useParams<{ id: string }>();
  const [rec, setRec] = useState<{ created_at: string; analysis: Analysis } | null>(null);
  const [err, setErr] = useState<string | null>(null);
  useEffect(() => {
    if (!/^\d+$/.test(id)) return setErr("Identificador no válido.");
    api<{ created_at: string; analysis: Analysis }>(`/api/history/${id}`).then(setRec).catch((e) => setErr(e.message));
  }, [id]);
  return (
    <div className="space-y-4">
      <Link href="/historial" className="text-sm text-accent underline">← Volver al historial</Link>
      {err && <ErrorBox message={err} />}
      {!rec && !err && <Loading />}
      {rec && (
        <>
          <div role="note" className="rounded-xl border border-line bg-panel p-3 text-sm text-mute">Versión guardada el {fechaHora(rec.created_at)}. Muestra los datos y probabilidades tal como se calcularon ese día.</div>
          {rec.analysis.source && <DemoBanner isDemo={rec.analysis.source.is_demo} />}
          <AnalysisView a={rec.analysis} />
        </>
      )}
    </div>
  );
}
