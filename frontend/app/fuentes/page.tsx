"use client";
import { useEffect, useState } from "react";
import { CalibrationChart } from "@/components/charts/charts";
import { DemoBanner } from "@/components/DemoBanner";
import { Badge, Card, Explain, ErrorBox, Loading, NotAvailable, Stat } from "@/components/ui";
import { SourceInfo, ValidationResult, api } from "@/lib/api";
import { fechaHora, num, pct } from "@/lib/format";

const NAMES: Record<string, string> = { dixon_coles: "Modelo Dixon-Coles", frecuencias: "Referencia: frecuencias históricas", poisson_liga: "Referencia: Poisson de liga" };

export default function Fuentes() {
  const [src, setSrc] = useState<SourceInfo | null>(null);
  const [val, setVal] = useState<ValidationResult | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [valErr, setValErr] = useState<string | null>(null);
  useEffect(() => {
    api<SourceInfo>("/api/source").then(setSrc).catch((e) => setErr(e.message));
    api<ValidationResult>("/api/model/validation").then(setVal).catch((e) => setValErr(e.message));
  }, []);
  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-extrabold">Fuentes de datos y calidad del modelo</h1>
      {src && <DemoBanner isDemo={src.is_demo} />}
      {err && <ErrorBox message={err} />}
      {!src && !err && <Loading />}
      {src && (
        <Card title="Fuente activa">
          <p className="font-semibold">{src.name} {src.is_demo && <Badge tone="warn">DEMO</Badge>}</p>
          <p className="text-sm text-mute">Actualizada: {fechaHora(src.updated_at)} · {src.license_note}</p>
          <div className="mt-3 grid grid-cols-2 gap-2 md:grid-cols-4">
            {Object.entries(src.coverage).map(([k, v]) => (
              <div key={k} className="rounded-lg bg-panel2 p-3 text-sm"><div className="text-xs uppercase text-mute">{k.replaceAll("_", " ")}</div><div className="font-semibold">{v == null ? "no disponible" : String(v)}</div></div>
            ))}
          </div>
          <ul className="mt-3 list-disc pl-5 text-sm text-mute">{src.notes.map((n) => <li key={n}>{n}</li>)}</ul>
          <Explain>El cambio de fuente (importación de CSV/Excel o un proveedor de pago) se configura en el servidor con variables de entorno; ver README. La conexión a API-Football está pendiente de verificar su cobertura de la Liga BetPlay.</Explain>
        </Card>
      )}
      <Card title="Validación retrospectiva del modelo">
        {valErr && <ErrorBox message={valErr} />}
        {!val && !valErr && <Loading text="Calculando validación (puede tardar unos segundos)…" />}
        {val?.status === "insufficient_data" && <NotAvailable>{val.message}</NotAvailable>}
        {val?.status === "ok" && val.metrics && (
          <>
            {val.warning && <div role="note" className="mb-3 rounded-xl border border-amber-400/40 bg-amber-400/10 p-3 text-sm text-amber-900 dark:text-amber-100"><strong>Atención:</strong> {val.warning}</div>}
            <div className="grid gap-3 md:grid-cols-3">
              {Object.entries(val.metrics).map(([k, m]) => (
                <div key={k} className="rounded-xl bg-panel2 p-3">
                  <div className="text-sm font-semibold">{NAMES[k] ?? k}</div>
                  <div className="mt-2 text-xs text-mute">Brier (menor es mejor)</div><div className="text-2xl font-bold tabular-nums">{num(m.brier, 4)}</div>
                  <div className="mt-1 text-xs text-mute">Log loss</div><div className="tabular-nums">{num(m.log_loss, 4)}</div>
                </div>
              ))}
            </div>
            <div className="mt-3 grid grid-cols-2 gap-3 md:grid-cols-3">
              <Stat label="Partidos evaluados" value={val.n_evaluated} sub={`${val.period?.from} → ${val.period?.to}`} />
              <Stat label="Mejora del Brier" value={pct(val.brier_improvement_vs_best_baseline, 1)} sub="frente a la mejor referencia" />
            </div>
            <Explain>Para cada semana se reajustó el modelo usando solo partidos anteriores y se predijo esa semana (sin fuga de información). El Brier mide el error de las probabilidades: 0 sería perfecto y 0,667 equivale a repartir siempre 1/3 para cada resultado. Una mejora pequeña frente a las referencias es normal en fútbol; lo importante es que sea medible, honesta y se vigile en el tiempo. Método: {val.method}.</Explain>
            <h3 className="mt-4 mb-1 text-sm font-semibold">Calibración</h3>
            <CalibrationChart rows={val.calibration ?? []} />
            <Explain>Si el modelo dice «30 %», idealmente eso ocurre cerca de 3 de cada 10 veces. Cuanto más cerca de la línea punteada, mejor calibrado. Solo se dibujan tramos con 5 o más observaciones.</Explain>
          </>
        )}
      </Card>
    </div>
  );
}
