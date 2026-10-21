"use client";
import Link from "next/link";
import { usePathname, useSearchParams } from "next/navigation";
import { ReactNode, Suspense, useEffect, useState } from "react";
import { fechaHora } from "@/lib/format";
import { AppProvider, useApp } from "@/lib/state";

type Item = { href: string; label: string; icon: string; vista?: string };
const MAIN: Item[] = [
  { href: "/", label: "Inicio", icon: "🏠" },
  { href: "/partidos", label: "Partidos", icon: "📅" },
  { href: "/analisis?vista=resumen", label: "Comparador de equipos", icon: "⚖️", vista: "resumen" },
  { href: "/analisis?vista=ultimos", label: "Análisis de 20 partidos", icon: "📋", vista: "ultimos" },
  { href: "/analisis?vista=goles", label: "Goles por minuto", icon: "⏱️", vista: "goles" },
  { href: "/analisis?vista=jugadores", label: "Jugadores", icon: "👤", vista: "jugadores" },
  { href: "/analisis?vista=tarjetas", label: "Tarjetas", icon: "🟨", vista: "tarjetas" },
  { href: "/analisis?vista=contexto", label: "Clima y contexto", icon: "☁️", vista: "contexto" },
  { href: "/analisis?vista=prob", label: "Probabilidades", icon: "🎯", vista: "prob" },
];
const BOTTOM: Item[] = [
  { href: "/historial", label: "Historial", icon: "🕘" },
  { href: "/fuentes", label: "Configuración y fuentes", icon: "⚙️" },
];
const MOBILE: Item[] = [
  { href: "/", label: "Inicio", icon: "🏠" },
  { href: "/partidos", label: "Partidos", icon: "📅" },
  { href: "/analisis?vista=resumen", label: "Análisis", icon: "📈", vista: "resumen" },
  { href: "/historial", label: "Historial", icon: "🕘" },
  { href: "/fuentes", label: "Fuentes", icon: "⚙️" },
];

function Logo() {
  return (
    <Link href="/" className="flex items-center gap-3">
      <span aria-hidden className="flex h-10 w-10 items-center justify-center rounded-full border-2 border-home text-lg">⚽</span>
      <span>
        <span className="block text-lg font-extrabold leading-tight">Fútbol <span className="text-accent">DataPro</span></span>
        <span className="block text-[10px] text-mute">Análisis · Estadísticas · Predicción</span>
      </span>
    </Link>
  );
}

function NavLinks({ items, compact = false }: { items: Item[]; compact?: boolean }) {
  const path = usePathname();
  const sp = useSearchParams();
  const vista = sp.get("vista");
  const isActive = (i: Item) => {
    const base = i.href.split("?")[0];
    if (base === "/") return path === "/";
    if (base === "/analisis") return path === "/analisis" && (compact ? true : vista === (i.vista ?? "resumen") || (!vista && i.vista === "resumen"));
    return path.startsWith(base);
  };
  return (
    <>
      {items.map((i) => (
        <Link key={i.label} href={i.href} aria-current={isActive(i) ? "page" : undefined}
          className={compact
            ? `flex flex-col items-center gap-0.5 py-2 text-[11px] ${isActive(i) ? "text-accent" : "text-mute"}`
            : `flex items-center gap-3 rounded-lg px-3 py-2 text-sm ${isActive(i) ? "bg-accent font-semibold text-white" : "text-mute hover:bg-panel2 hover:text-ink"}`}>
          <span aria-hidden className={compact ? "text-lg" : ""}>{i.icon}</span>{i.label}
        </Link>
      ))}
    </>
  );
}

function TopBar() {
  const { theme, toggleTheme, season, setSeason, seasons, source } = useApp();
  return (
    <header className="sticky top-0 z-10 flex flex-wrap items-center gap-x-4 gap-y-2 border-b border-line bg-panel/95 px-4 py-2.5 backdrop-blur">
      <div className="md:hidden"><Logo /></div>
      <div className="hidden items-center gap-3 text-sm md:flex">
        <span className="font-semibold">Liga BetPlay Dimayor</span>
      </div>
      <label className="ml-auto flex items-center gap-2 text-sm text-mute md:ml-0">
        <span className="hidden sm:inline">Temporada</span>
        <select aria-label="Temporada" value={season} onChange={(e) => setSeason(e.target.value)}
          className="rounded-lg border border-line bg-panel2 px-2 py-1.5 text-ink">
          {seasons.length === 0 && <option value="">—</option>}
          {seasons.map((s) => <option key={s}>{s}</option>)}
        </select>
      </label>
      <div className="hidden text-xs text-mute md:ml-auto md:block" aria-live="polite">
        {source ? <>Última actualización de datos: {fechaHora(source.updated_at)}{source.is_demo && <b className="ml-2 rounded bg-amber-400/20 px-1.5 py-0.5 text-amber-800 dark:text-amber-200">DEMO</b>}</> : "Conectando con la fuente de datos…"}
      </div>
      <button onClick={toggleTheme} aria-label={theme === "dark" ? "Cambiar a tema claro" : "Cambiar a tema oscuro"}
        className="rounded-lg border border-line bg-panel2 px-2.5 py-1.5 text-sm">{theme === "dark" ? "☀️" : "🌙"}</button>
    </header>
  );
}

export default function Shell({ children }: { children: ReactNode }) {
  const [, setReady] = useState(false);
  useEffect(() => {
    setReady(true);
    if (process.env.NODE_ENV === "production" && "serviceWorker" in navigator) {
      navigator.serviceWorker.register("/sw.js").catch(() => undefined);
    }
  }, []);
  return (
    <AppProvider>
      <div className="min-h-screen md:flex">
        <aside className="sticky top-0 hidden h-screen w-64 shrink-0 flex-col overflow-y-auto border-r border-line bg-panel p-4 md:flex">
          <div className="mb-5"><Logo /></div>
          <Suspense fallback={null}>
            <nav aria-label="Principal" className="space-y-1"><NavLinks items={MAIN} /></nav>
            <nav aria-label="Secundaria" className="mt-4 space-y-1 border-t border-line pt-4"><NavLinks items={BOTTOM} /></nav>
          </Suspense>
          <div className="mt-4 border-t border-line pt-4">
            <p className="mb-2 px-3 text-xs font-semibold uppercase tracking-wide text-mute">Próximamente</p>
            {["Informe PDF", "Cuenta y suscripción"].map((s) => (
              <div key={s} aria-disabled="true" className="flex items-center justify-between rounded-lg px-3 py-2 text-sm text-mute/60">{s}<span className="text-[10px]">pronto</span></div>
            ))}
          </div>
        </aside>
        <div className="min-w-0 flex-1 pb-20 md:pb-0">
          <TopBar />
          <main className="mx-auto w-full max-w-[1400px] p-4 sm:p-6">{children}</main>
        </div>
        <nav aria-label="Principal móvil" className="fixed inset-x-0 bottom-0 z-20 grid grid-cols-5 border-t border-line bg-panel md:hidden">
          <Suspense fallback={null}><NavLinks items={MOBILE} compact /></Suspense>
        </nav>
      </div>
    </AppProvider>
  );
}
