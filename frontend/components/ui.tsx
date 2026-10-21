import { ReactNode } from "react";
import { initials } from "@/lib/format";

export function Card({ title, children, className = "", right }: { title?: string; children: ReactNode; className?: string; right?: ReactNode }) {
  return (
    <section className={`rounded-2xl border border-line bg-panel p-4 sm:p-5 ${className}`}>
      {(title || right) && (
        <header className="mb-3 flex items-start justify-between gap-3">
          {title && <h2 className="text-base font-semibold text-ink">{title}</h2>}
          {right}
        </header>
      )}
      {children}
    </section>
  );
}

/** Explicación en lenguaje simple de qué muestra un gráfico o cifra. */
export function Explain({ children }: { children: ReactNode }) {
  return <p className="mt-3 text-sm leading-relaxed text-mute">{children}</p>;
}

export function Stat({ label, value, sub, color }: { label: string; value: ReactNode; sub?: ReactNode; color?: string }) {
  return (
    <div className="rounded-xl border border-line bg-panel2 p-3">
      <div className="text-xs font-medium uppercase tracking-wide text-mute">{label}</div>
      <div className="mt-1 text-3xl font-bold tabular-nums" style={color ? { color } : undefined}>{value}</div>
      {sub && <div className="mt-0.5 text-xs text-mute">{sub}</div>}
    </div>
  );
}

export function Badge({ children, tone = "neutral" }: { children: ReactNode; tone?: "neutral" | "warn" | "good" | "bad" | "info" }) {
  const tones = {
    neutral: "bg-panel2 text-mute border-line",
    warn: "bg-amber-400/15 text-amber-700 dark:text-amber-300 border-amber-400/40",
    good: "bg-emerald-400/15 text-emerald-700 dark:text-emerald-300 border-emerald-400/40",
    bad: "bg-red-400/15 text-red-700 dark:text-red-300 border-red-400/40",
    info: "bg-accent/15 text-accent border-accent/40",
  };
  return <span className={`inline-flex items-center rounded-full border px-2 py-0.5 text-xs font-medium ${tones[tone]}`}>{children}</span>;
}

export function Crest({ name, color, size = 56 }: { name: string; color: string; size?: number }) {
  // No se usan escudos reales: no hay licencia de uso. Se muestra un monograma neutro.
  return (
    <div aria-hidden className="flex shrink-0 items-center justify-center rounded-full border-2 font-bold"
      style={{ width: size, height: size, borderColor: color, color, fontSize: size * 0.34 }}>
      {initials(name)}
    </div>
  );
}

export function ResultDot({ r }: { r: "G" | "E" | "P" | string }) {
  const map: Record<string, string> = { G: "bg-home text-white", E: "bg-draw text-white", P: "bg-away text-white" };
  const label: Record<string, string> = { G: "Ganó", E: "Empató", P: "Perdió" };
  return <span title={label[r]} aria-label={label[r]} className={`inline-flex h-6 w-6 items-center justify-center rounded text-xs font-bold ${map[r]}`}>{r}</span>;
}

export function ErrorBox({ message }: { message: string }) {
  return <div role="alert" className="rounded-xl border border-red-400/40 bg-red-400/10 p-4 text-sm text-red-900 dark:text-red-100">{message}</div>;
}

export function Loading({ text = "Cargando…" }: { text?: string }) {
  return <div role="status" className="animate-pulse rounded-xl border border-line bg-panel p-6 text-mute">{text}</div>;
}

export function NotAvailable({ children }: { children: ReactNode }) {
  return <div className="rounded-xl border border-dashed border-line p-4 text-sm text-mute">No disponible: {children}</div>;
}
