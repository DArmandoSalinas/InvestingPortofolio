import { describe, it, expect } from "vitest";
import { safeRedirect } from "../redirect";

describe("safeRedirect", () => {
  describe("rutas válidas", () => {
    it("permite ruta raíz", () => {
      expect(safeRedirect("/")).toBe("/");
    });

    it("permite rutas relativas simples", () => {
      expect(safeRedirect("/dashboard")).toBe("/dashboard");
      expect(safeRedirect("/perfil")).toBe("/perfil");
      expect(safeRedirect("/admin/acceso")).toBe("/admin/acceso");
    });

    it("permite rutas con query params", () => {
      expect(safeRedirect("/login?error=credentials")).toBe("/login?error=credentials");
    });

    it("permite rutas con hash", () => {
      expect(safeRedirect("/dashboard#section")).toBe("/dashboard#section");
    });
  });

  describe("valores nulos o vacíos", () => {
    it("retorna / para null", () => {
      expect(safeRedirect(null)).toBe("/");
    });

    it("retorna / para string vacío", () => {
      expect(safeRedirect("")).toBe("/");
    });

    it("retorna / para solo espacios", () => {
      expect(safeRedirect("   ")).toBe("/");
    });
  });

  describe("rechaza rutas inseguras", () => {
    it("rechaza URLs con doble slash //", () => {
      expect(safeRedirect("//evil.com")).toBe("/");
      expect(safeRedirect("//evil.com/path")).toBe("/");
    });

    it("rechaza URLs con /\\", () => {
      expect(safeRedirect("/\\evil.com")).toBe("/");
    });

    it("rechaza URLs absolutas con esquema", () => {
      expect(safeRedirect("http://evil.com")).toBe("/");
      expect(safeRedirect("https://evil.com")).toBe("/");
      expect(safeRedirect("ftp://evil.com")).toBe("/");
    });

    it("rechaza javascript:", () => {
      expect(safeRedirect("javascript:alert(1)")).toBe("/");
      expect(safeRedirect("JavaScript:alert(1)")).toBe("/");
    });

    it("rechaza data:", () => {
      expect(safeRedirect("data:text/html,<script>alert(1)</script>")).toBe("/");
    });

    it("rechaza vbscript:", () => {
      expect(safeRedirect("vbscript:alert(1)")).toBe("/");
    });

    it("rechaza URLs con @", () => {
      expect(safeRedirect("http://attacker.com@victim.com")).toBe("/");
      expect(safeRedirect("//@attacker.com")).toBe("/");
    });

    it("rechaza rutas relativas sin /", () => {
      expect(safeRedirect("dashboard")).toBe("/");
      expect(safeRedirect("../etc/passwd")).toBe("/");
    });

    it("rechaza esquema dentro de ruta", () => {
      expect(safeRedirect("/path?redirect=http://evil.com")).toBe("/");
    });
  });
});
