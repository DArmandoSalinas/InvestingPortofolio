import { describe, expect, it } from "vitest";
import { beatSpyLabel, setupPlain, statusPlain } from "./signal-copy";

describe("signal-copy", () => {
  it("explica impulso y retroceso en español simple", () => {
    expect(setupPlain("impulso")).toMatch(/promedio de 20/);
    expect(setupPlain("retroceso")).toMatch(/reentrada/);
  });

  it("explica cada estado sin inventar éxito", () => {
    expect(statusPlain("stop")).toMatch(/stop/i);
    expect(statusPlain("expired")).toMatch(/plazo/);
  });

  it("es honesta cuando las señales pierden frente al S&P", () => {
    const label = beatSpyLabel(0.42, 50);
    expect(label).toContain("42%");
    expect(label).toMatch(/No es un atajo seguro/);
  });

  it("no inventa porcentaje sin comparables", () => {
    expect(beatSpyLabel(null, 0)).toMatch(/Todavía no hay/);
  });
});
