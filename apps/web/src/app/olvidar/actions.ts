"use server";

import { redirect } from "next/navigation";

function apiUrl() {
  return (process.env.NEXT_PUBLIC_API_URL ?? "").replace(/\/$/, "");
}

export async function requestReset(formData: FormData) {
  const email = String(formData.get("email") ?? "")
    .trim()
    .toLowerCase();
  if (!email.includes("@")) {
    redirect("/olvidar?error=correo");
  }

  const base = apiUrl();
  if (!base) {
    redirect("/olvidar?error=servicio");
  }

  try {
    await fetch(`${base}/auth/forgot-password`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email }),
      cache: "no-store",
    });
  } catch {
    redirect("/olvidar?error=servicio");
  }

  redirect("/login?enviado=1");
}
