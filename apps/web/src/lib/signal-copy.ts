import type { SignalRow } from "@/lib/types";

const SETUP_PLAIN: Record<SignalRow["setup"], string> = {
  impulso:
    "Impulso: el precio sube con fuerza. El cierre quedó arriba de su promedio de 20 días, y ese promedio está arriba del de 50. Busca seguir la tendencia, no adivinar el fondo.",
  retroceso:
    "Retroceso: la tendencia de fondo sigue al alza (media de 20 sobre la de 50), pero el precio volvió a tocar la media corta. Es una posible reentrada, no una garantía.",
};

const STATUS_PLAIN: Record<SignalRow["status"], string> = {
  open: "Sigue abierta: aún no tocó el stop, el objetivo ni cumplió el plazo.",
  target: "Cerró en el objetivo: el precio llegó a la meta antes que al stop.",
  stop: "Cerró en el stop: el precio tocó el límite de pérdida (si chocó con el objetivo el mismo día, también cuenta el stop).",
  expired: "Cerró por plazo: pasó el número de sesiones sin tocar stop ni objetivo.",
};

export function setupPlain(setup: SignalRow["setup"]): string {
  return SETUP_PLAIN[setup];
}

export function statusPlain(status: SignalRow["status"]): string {
  return STATUS_PLAIN[status];
}

export function beatSpyLabel(rate: number | null, compared: number): string {
  if (rate === null || compared === 0) {
    return "Todavía no hay suficientes señales cerradas con cifra del S&P 500 para comparar.";
  }
  const pct = Math.round(rate * 100);
  return `En el historial real, las señales le ganan al S&P 500 solo el ${pct}% de las veces (${compared} comparables). No es un atajo seguro.`;
}
