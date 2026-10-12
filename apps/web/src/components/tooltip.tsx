"use client";

import { useState } from "react";
import { createPortal } from "react-dom";

interface TooltipProps {
  term: string;
  children: React.ReactNode;
}

const GLOSSARY: Record<string, string> = {
  crecimiento:
    "Crecimiento anual de ingresos y utilidades de la empresa. Un puntaje de 50 significa 0% de crecimiento, 100 significa +30% o más, y 0 significa -20% o peor.",
  valor:
    "Qué tan barata está la empresa comparada con otras del mismo sector. Usa P/E (precio/utilidad), P/S (precio/ventas) y EV/EBITDA. Más puntos = más barata.",
  momentum:
    "Tendencia reciente del precio. Combina rendimientos de 3, 6 y 12 meses, más la posición actual vs. su promedio de 200 días.",
  general:
    "Promedio simple de Crecimiento, Valor y Momentum (solo si los tres existen). Va de 0 a 100.",
  "pe":
    "Price-to-Earnings. Precio de la acción dividido entre sus utilidades anuales. Menor = potencialmente más barata.",
  "ps":
    "Price-to-Sales. Precio dividido entre ventas. Útil cuando las empresas aún no son rentables.",
  "ev/ebitda":
    "Enterprise Value / EBITDA. Valora la empresa completa (deuda incluida) contra sus ganancias operativas.",
  sesiones:
    "Días de cotización en el mercado (sin contar fines de semana ni festivos). Una señal de 10 sesiones dura aproximadamente 2 semanas.",
  confianza:
    "Qué tan fuerte es la señal, de 0 a 100. Basado en la tendencia y el volumen reciente. Más alto = más confiable.",
  neto:
    "Rendimiento después de descontar comisiones. Verde = ganancia, rojo = pérdida.",
  "media de 200 días":
    "Promedio del precio de cierre de los últimos 200 días de cotización. Un precio arriba de su media indica tendencia alcista.",
  "altas en los tres":
    "Empresas con puntuación de 70 o más en Crecimiento, Valor y Momentum al mismo tiempo. Combinan las tres cualidades.",
  entrada:
    "Precio al que la señal indica comprar.",
  stop:
    "Precio de salida si baja (límite de pérdida). Si toca este nivel, la señal cierra con pérdida.",
  objetivo:
    "Precio de salida si sube (meta de ganancia). Si toca este nivel, la señal cierra con ganancia.",
};

export function Tooltip({ term, children }: TooltipProps) {
  const [show, setShow] = useState(false);
  const definition = GLOSSARY[term.toLowerCase()];

  if (!definition) {
    return <>{children}</>;
  }

  return (
    <span
      className="group relative cursor-help border-b border-dotted border-muted/40"
      onMouseEnter={() => setShow(true)}
      onMouseLeave={() => setShow(false)}
    >
      {children}
      {show && typeof document !== "undefined" &&
        createPortal(
          <div
            className="pointer-events-none fixed z-50"
            style={{
              left: "50%",
              top: "50%",
              transform: "translate(-50%, -50%)",
            }}
          >
            <div className="max-w-xs rounded-2xl border border-line bg-surface px-4 py-3 text-xs leading-5 text-ink shadow-2xl">
              <div className="mb-1 font-medium text-accent">{term}</div>
              {definition}
            </div>
          </div>,
          document.body
        )}
    </span>
  );
}
