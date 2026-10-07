"use server";

import { revalidatePath } from "next/cache";
import { redirect } from "next/navigation";
import { apiSend } from "@/lib/api";

function fail(detail: string): never {
  redirect(`/portafolio?error=${encodeURIComponent(detail)}`);
}

export async function addHolding(formData: FormData) {
  const assetClass = String(formData.get("asset_class") ?? "");
  const quantity = Number(formData.get("quantity"));
  const unitCost = Number(formData.get("unit_cost") ?? 1);
  const openedOn = String(formData.get("opened_on") ?? "");
  if (!Number.isFinite(quantity) || quantity <= 0 || !Number.isFinite(unitCost) || unitCost <= 0) {
    fail("La cantidad y el costo tienen que ser mayores que cero");
  }
  if (!/^\d{4}-\d{2}-\d{2}$/.test(openedOn)) {
    fail("Indica la fecha de la posición");
  }
  const result = await apiSend("POST", "/portfolio", {
    asset_class: assetClass,
    symbol: String(formData.get("symbol") ?? ""),
    market: formData.get("market") || null,
    quantity,
    unit_cost: assetClass === "cetes" || assetClass === "ahorro" ? 1 : unitCost,
    currency: formData.get("currency") || null,
    opened_on: openedOn,
  });
  if (!result.ok) {
    fail(result.detail);
  }
  revalidatePath("/portafolio");
  redirect("/portafolio");
}

export async function removeHolding(formData: FormData) {
  const id = String(formData.get("id") ?? "");
  const result = await apiSend("DELETE", `/portfolio/${id}`);
  if (!result.ok) {
    fail(result.detail);
  }
  revalidatePath("/portafolio");
  redirect("/portafolio");
}
