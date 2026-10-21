"use client";
import { Badge } from "@/components/ui";

export function DemoBanner({ isDemo }: { isDemo: boolean }) {
  if (!isDemo) return null;
  return (
    <div role="note" className="mb-4 rounded-xl border border-amber-400/50 bg-amber-400/10 p-3 text-sm text-amber-900 dark:text-amber-100">
      <Badge tone="warn">DATOS DEMOSTRATIVOS</Badge>{" "}
      Los clubes, jugadores y resultados son <strong>ficticios</strong> y generados por computador. Sirven para probar la aplicación;
      no representan a la Liga BetPlay ni deben usarse para tomar decisiones.
    </div>
  );
}
