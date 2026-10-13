/**
 * Railway Infrastructure as Code (reemplaza railway.json / railway.toml).
 * Config as Code deja de leerse el 2026-12-01.
 *
 *   npm install   # raíz del monorepo (paquete `railway`)
 *   railway link
 *   railway config plan
 *   railway config apply
 *
 * Secretos: dashboard o preserve() — nunca en este archivo.
 */
import { defineRailway, github, preserve, project, service } from "railway/iac";

export default defineRailway(() => {
  const api = service("api", {
    // Monorepo: Dockerfile en la raíz (copia apps/api + supabase).
    source: github("DArmandoSalinas/InvestingPortofolio"),
    start: "uv run uvicorn app.main:app --host 0.0.0.0 --port $PORT",
    env: {
      REPO_ROOT: "/app",
      SUPABASE_URL: preserve(),
      SUPABASE_SERVICE_ROLE_KEY: preserve(),
      SUPABASE_ANON_KEY: preserve(),
      ADMIN_EMAIL: preserve(),
      CORS_ORIGINS: preserve(),
      SITE_URL: preserve(),
      XAI_API_KEY: preserve(),
    },
  });

  return project("investing-portfolio", {
    resources: [api],
  });
});
