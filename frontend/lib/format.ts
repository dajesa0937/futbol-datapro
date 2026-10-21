const dec = (x: number, digits: number) => x.toLocaleString("es-CO", { minimumFractionDigits: digits, maximumFractionDigits: digits });
export const pct = (p: number | null | undefined, digits = 0) => (p == null ? "—" : `${dec(p * 100, digits)} %`);
export const num = (x: number | null | undefined, digits = 2) => (x == null ? "—" : dec(x, digits));

const MESES = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"];
const DIAS = ["dom", "lun", "mar", "mié", "jue", "vie", "sáb"];
export function fecha(iso: string, withDay = false) {
  const [y, m, d] = iso.slice(0, 10).split("-").map(Number);
  const dt = new Date(Date.UTC(y, m - 1, d));
  return `${withDay ? DIAS[dt.getUTCDay()] + " " : ""}${d} ${MESES[m - 1]} ${y}`;
}
export function fechaHora(iso: string) {
  const d = new Date(iso);
  return d.toLocaleString("es-CO", { dateStyle: "medium", timeStyle: "short" });
}
export const initials = (name: string) =>
  name.split(/\s+/).filter(Boolean).slice(0, 2).map((w) => w[0]).join("").toUpperCase();
export const HOME_COLOR = "rgb(var(--home))";
export const AWAY_COLOR = "rgb(var(--away))";
export const DRAW_COLOR = "rgb(var(--draw))";
