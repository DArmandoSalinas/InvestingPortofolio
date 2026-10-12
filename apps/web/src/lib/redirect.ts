/**
 * Valida que una URL de redirect sea segura (solo rutas relativas).
 * 
 * Permite: "/", "/dashboard", "/perfil"
 * Rechaza: "//evil.com", "/\\evil.com", "http://evil.com", "javascript:alert(1)", "mailto:x@y.com"
 * 
 * @param next - El parámetro next a validar
 * @returns Ruta segura: la original si es válida, "/" si no lo es
 */
export function safeRedirect(next: string | null): string {
  if (!next) {
    return "/";
  }

  const trimmed = next.trim();

  // Solo permitir rutas relativas que empiecen con exactamente una "/"
  if (!trimmed.startsWith("/")) {
    return "/";
  }

  // Rechazar "//" (puede convertirse a esquema) y "/\" (bypass en algunos navegadores)
  if (trimmed.startsWith("//") || trimmed.startsWith("/\\")) {
    return "/";
  }

  // Rechazar si contiene esquemas comunes o @
  const lower = trimmed.toLowerCase();
  if (
    lower.includes("://") ||
    lower.includes("javascript:") ||
    lower.includes("data:") ||
    lower.includes("vbscript:") ||
    lower.includes("@")
  ) {
    return "/";
  }

  return trimmed;
}
