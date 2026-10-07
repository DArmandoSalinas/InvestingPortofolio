"use server";

import { revalidatePath } from "next/cache";
import { redirect } from "next/navigation";
import { apiSend } from "@/lib/api";

function fail(detail: string): never {
  redirect(`/admin/seguimiento?error=${encodeURIComponent(detail)}`);
}

export async function saveRules(formData: FormData) {
  const stock = Number(formData.get("stock_percent")) / 100;
  const crypto = Number(formData.get("crypto_percent")) / 100;
  const horizon = Number(formData.get("horizon_sessions"));
  if (!Number.isFinite(stock) || !Number.isFinite(crypto) || !Number.isInteger(horizon)) {
    fail("Revisa las comisiones y el horizonte");
  }
  const result = await apiSend("PUT", "/admin/settings", {
    stock_commission: stock,
    crypto_commission: crypto,
    horizon_sessions: horizon,
  });
  if (!result.ok) {
    fail(result.detail);
  }
  revalidatePath("/admin/seguimiento");
  revalidatePath("/senales");
}

export async function addWatch(formData: FormData) {
  const result = await apiSend("POST", "/admin/watchlist", {
    symbol: String(formData.get("symbol") ?? ""),
    name: String(formData.get("name") ?? ""),
    asset_class: formData.get("asset_class") === "crypto" ? "crypto" : "stock",
  });
  if (!result.ok) {
    fail(result.detail);
  }
  revalidatePath("/admin/seguimiento");
}

export async function toggleWatch(formData: FormData) {
  const result = await apiSend("PATCH", "/admin/watchlist", {
    yahoo_symbol: String(formData.get("yahoo_symbol") ?? ""),
    active: formData.get("active") === "true",
  });
  if (!result.ok) {
    fail(result.detail);
  }
  revalidatePath("/admin/seguimiento");
}
