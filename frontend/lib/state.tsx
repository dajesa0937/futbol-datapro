"use client";
import { ReactNode, createContext, useCallback, useContext, useEffect, useState } from "react";
import { SourceInfo, api } from "@/lib/api";

type Theme = "dark" | "light";
export type Selected = { home: string; away: string; on: string };

type Ctx = {
  theme: Theme; toggleTheme: () => void;
  season: string; setSeason: (s: string) => void; seasons: string[];
  source: SourceInfo | null;
  selected: Selected | null; select: (m: Selected) => void;
};
const AppCtx = createContext<Ctx | null>(null);

// localStorage solo para comodidades del navegador: si falla, la app funciona igual.
const read = (k: string): string | null => { try { return localStorage.getItem(k); } catch { return null; } };
const write = (k: string, v: string) => { try { localStorage.setItem(k, v); } catch { /* sin almacenamiento */ } };

export function AppProvider({ children }: { children: ReactNode }) {
  const [theme, setTheme] = useState<Theme>("dark");
  const [season, setSeasonState] = useState("");
  const [seasons, setSeasons] = useState<string[]>([]);
  const [source, setSource] = useState<SourceInfo | null>(null);
  const [selected, setSelected] = useState<Selected | null>(null);

  useEffect(() => {
    const t = document.documentElement.getAttribute("data-theme");
    if (t === "light" || t === "dark") setTheme(t);
    const saved = read("datapro.match");
    if (saved) { try { const m = JSON.parse(saved); if (m?.home && m?.away) setSelected(m); } catch { /* ignora */ } }
    api<{ seasons: string[] }>("/api/seasons").then((r) => {
      setSeasons(r.seasons);
      const s = read("datapro.season");
      setSeasonState(s && r.seasons.includes(s) ? s : r.seasons[0] ?? "");
    }).catch(() => undefined);
    api<SourceInfo>("/api/source").then(setSource).catch(() => undefined);
  }, []);

  const toggleTheme = useCallback(() => {
    const next: Theme = theme === "dark" ? "light" : "dark";
    setTheme(next);
    document.documentElement.setAttribute("data-theme", next);
    write("datapro.theme", next);
  }, [theme]);
  const setSeason = useCallback((s: string) => { setSeasonState(s); write("datapro.season", s); }, []);
  const select = useCallback((m: Selected) => { setSelected(m); write("datapro.match", JSON.stringify(m)); }, []);

  return <AppCtx.Provider value={{ theme, toggleTheme, season, setSeason, seasons, source, selected, select }}>{children}</AppCtx.Provider>;
}

export function useApp(): Ctx {
  const c = useContext(AppCtx);
  if (!c) throw new Error("useApp fuera de AppProvider");
  return c;
}
