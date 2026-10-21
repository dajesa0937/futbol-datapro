export const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export class ApiError extends Error {
  status: number;
  constructor(message: string, status: number) {
    super(message);
    this.status = status;
  }
}

export async function api<T>(path: string, init?: RequestInit): Promise<T> {
  let res: Response;
  try {
    res = await fetch(`${API_URL}${path}`, { ...init, headers: { "Content-Type": "application/json", ...(init?.headers ?? {}) } });
  } catch {
    throw new ApiError("No se pudo conectar con el servidor de análisis. ¿Está en ejecución?", 0);
  }
  if (!res.ok) {
    let detail = `Error ${res.status}`;
    try {
      const body = await res.json();
      if (typeof body.detail === "string") detail = body.detail;
      else if (Array.isArray(body.detail)) detail = "Solicitud no válida. Revisa los datos ingresados.";
    } catch { /* cuerpo no JSON */ }
    if (res.status === 429) detail = "Demasiadas solicitudes. Espera un momento e inténtalo de nuevo.";
    throw new ApiError(detail, res.status);
  }
  return res.json() as Promise<T>;
}

/* ---------- Tipos (reflejan la respuesta de la API) ---------- */
export type SourceInfo = {
  name: string; kind: string; is_demo: boolean; updated_at: string; license_note: string;
  coverage: Record<string, number | string | null>; notes: string[]; validation?: Record<string, unknown> | null;
};
export type Fixture = {
  id: string; date: string; kickoff: string | null; competition: string; season: string;
  home: string; away: string; venue: string | null;
};
export type Split = {
  n: number; wins: number; draws: number; losses: number; goals_for: number; goals_against: number;
  gf_avg: number | null; ga_avg: number | null; points_per_match: number | null; label?: string;
};
export type MatchRow = {
  id: string; date: string; competition: string; competition_label: string; season: string;
  venue_role: "local" | "visitante"; opponent: string; goals_for: number; goals_against: number;
  result: "G" | "E" | "P"; yellow: number | null; red: number | null; referee: string | null;
};
export type TeamReport = {
  team: string; sample_size: number; requested: number; enough_data: boolean;
  overall: Split; home: Split; away: Split;
  form: { last5: string; ppm_last5: number | null; ppm_previous: number | null };
  by_competition: Record<string, Split>;
  cards: { n: number; yellow_total: number; red_total: number; yellow_avg: number; red_avg: number } | null;
  cards_coverage: { matches_with_data: number; of: number };
  goals_by_interval: { labels: string[]; for: number[]; against: number[]; matches_with_data: number; of: number };
  top_scorers: { player: string; goals: number; position: string | null }[];
  goals_by_position: Record<string, number>;
  team_goals_with_scorer_detail: number;
  days_since_last_match: number | null;
  matches: MatchRow[];
};
export type Line = { over: number; under: number };
export type Prediction = {
  p_home: number; p_draw: number; p_away: number;
  expected_home_goals: number; expected_away_goals: number; p_btts: number;
  over_under: Record<string, Line>; total_goals_range_80: [number, number];
  top_scores: { home: number; away: number; prob: number }[];
  total_goals_distribution: number[];
  lambda_home: number; lambda_away: number;
  monte_carlo: { n_sims: number; seed: number; p_home: { prob: number; std_error: number }; p_draw: { prob: number; std_error: number }; p_away: { prob: number; std_error: number } };
  factors: { name: string; value: number; text: string }[];
  goals_by_interval_expected: { home: { labels: string[]; expected: number[] } | null; away: { labels: string[]; expected: number[] } | null };
  scorer_probabilities: { team: string; player: string; position: string | null; p_scores: number; based_on_goals: number; team_goals_sample: number; caveat: string }[];
};
export type CardsEstimate = {
  reliable: boolean; reason: string | null; home_expected?: number; away_expected?: number; total_expected?: number;
  over_under?: Record<string, Line>; league_mean_per_team?: number; kind?: string;
};
export type Analysis = {
  match: { home: string; away: string; date: string };
  generated_at: string; data_cutoff: string;
  source: { name: string; kind: string; is_demo: boolean; updated_at: string } | null;
  home: TeamReport; away: TeamReport;
  prediction: Prediction | null; prediction_unavailable_reason: string | null;
  data_sufficiency: { level: "insuficiente" | "baja" | "media" | "alta"; message: string; matches_home: number; matches_away: number };
  model: { version: string; type: string; trained_on_matches: number; as_of: string; home_advantage: number; rho: number; converged: boolean; training_competitions: string[] } | null;
  cards_estimate: CardsEstimate;
  context: { rest_days: { home: number | null; away: number | null }; weather: { available: boolean; reason: string }; lineups: { available: boolean; reason: string } };
  disclaimer: string;
};
export type ValidationResult = {
  status: "ok" | "insufficient_data"; message?: string; n_evaluated?: number; data_is_demo?: boolean; warning?: string;
  period?: { from: string; to: string }; method?: string;
  metrics?: Record<string, { brier: number; log_loss: number; mae_total_goals: number | null }>;
  brier_improvement_vs_best_baseline?: number;
  calibration?: { bin: string; n: number; mean_predicted: number | null; observed_freq: number | null }[];
  outcome_rates?: { local: number; empate: number; visitante: number };
};
export type HistoryItem = {
  id: number; created_at: string; home: string; away: string; match_date: string; model_version: string;
  source_name: string; is_demo: boolean; p_home: number | null; p_draw: number | null; p_away: number | null;
};
export type Standings = {
  season: string; matches_counted: number; note: string;
  table: { position: number; team: string; played: number; points: number; gf: number; ga: number }[];
};
