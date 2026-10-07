"use server";

import { revalidatePath } from "next/cache";
import { redirect } from "next/navigation";
import { apiSend } from "@/lib/api";

function fail(detail: string): never {
  redirect(`/perfil?error=${encodeURIComponent(detail)}`);
}

export async function saveProfile(formData: FormData) {
  const amount = Number(formData.get("amount"));
  const monthly = Number(formData.get("monthly_contribution"));
  const horizon = Number(formData.get("horizon_years"));
  const currency = formData.get("currency") === "USD" ? "USD" : "MXN";
  const goal = String(formData.get("goal") ?? "");
  const risk = String(formData.get("risk") ?? "");
  if (!Number.isFinite(amount) || amount <= 0 || !Number.isFinite(monthly) || monthly < 0) {
    fail("El monto tiene que ser mayor que cero");
  }
  if (!Number.isInteger(horizon) || horizon < 1 || horizon > 40) {
    fail("El plazo va de 1 a 40 años");
  }
  if (goal !== "preservar" && goal !== "crecer" && goal !== "ingreso") {
    fail("Elige una meta");
  }
  if (risk !== "bajo" && risk !== "medio" && risk !== "alto") {
    fail("Elige una tolerancia");
  }
  const result = await apiSend("PUT", "/profile", {
    currency,
    amount,
    monthly_contribution: monthly,
    horizon_years: horizon,
    goal,
    risk,
  });
  if (!result.ok) {
    fail(result.detail);
  }
  revalidatePath("/perfil");
  redirect("/perfil");
}
