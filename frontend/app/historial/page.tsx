"use client";
import Link from "next/link";
import { useEffect, useState } from "react";
import { Badge, Card, ErrorBox, Loading } from "@/components/ui";
import { HistoryItem, api } from "@/lib/api";
import { fecha, fechaHora, pct } from "@/lib/format";

export default function Historial() {
  const [items, setItems] = useState<HistoryItem[] | null>(null);
  const [err, setErr] = useState<string | null>(null);
  useEffect(() => { api<{ items: HistoryItem[] }>("/api/history").then((r) => setItems(r.items)).catch((e) => setErr(e.message)); }, []);
  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-extrabold">Historial de análisis</h1>
      <p className="text-mute">Cada análisis guardado conserva sus probabilidades, la fecha y hora en que se generó y la fuente de datos, para compararlo después con el resultado real.</p>
      {err && <ErrorBox message={err} />}
      {!items && !err && <Loading />}
      {items && items.length === 0 && <Card><p className="text-mute">Aún no has guardado análisis. Abre un partido y pulsa «Guardar en historial».</p></Card>}
      <ul className="space-y-2">
        {items?.map((i) => (
          <li key={i.id}>
            <Link href={`/historial/${i.id}`} className="block rounded-xl border border-line bg-panel p-4 hover:bg-panel2">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <div className="font-semibold">{i.home} vs {i.away}</div>
                <div className="flex gap-1">{i.is_demo && <Badge tone="warn">DEMO</Badge>}<Badge>{i.model_version}</Badge></div>
              </div>
              <div className="mt-1 text-sm text-mute">Partido: {fecha(i.match_date)} · Guardado: {fechaHora(i.created_at)}</div>
              <div className="mt-1 text-sm">Local {pct(i.p_home)} · Empate {pct(i.p_draw)} · Visitante {pct(i.p_away)}</div>
            </Link>
          </li>
        ))}
      </ul>
    </div>
  );
}
