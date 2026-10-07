"use server";

import { redirect } from "next/navigation";
import { revalidatePath } from "next/cache";
import { apiSend } from "@/lib/api";

function fail(detail: string): never {
  redirect(`/admin/acceso?error=${encodeURIComponent(detail)}`);
}

export async function invite(formData: FormData) {
  const email = String(formData.get("email") ?? "")
    .trim()
    .toLowerCase();
  const role = formData.get("role") === "admin" ? "admin" : "member";
  const result = await apiSend("POST", "/admin/access", { email, role });
  if (!result.ok) {
    fail(result.detail);
  }
  revalidatePath("/admin/acceso");
  redirect(`/admin/acceso?enviado=${delivery(result.data)}`);
}

function delivery(data: unknown) {
  if (data && typeof data === "object" && "mail" in data && data.mail === "smtp") {
    return "correo";
  }
  return "local";
}

export async function resendLink(formData: FormData) {
  const email = String(formData.get("email") ?? "")
    .trim()
    .toLowerCase();
  const result = await apiSend("POST", "/admin/access/link", { email });
  if (!result.ok) {
    fail(result.detail);
  }
  revalidatePath("/admin/acceso");
  redirect(`/admin/acceso?enviado=${delivery(result.data)}`);
}

export async function updateAccess(formData: FormData) {
  const email = String(formData.get("email") ?? "").trim().toLowerCase();
  const role = formData.get("role");
  const active = formData.get("active");
  const body: { email: string; role?: "admin" | "member"; active?: boolean } = { email };
  if (role === "admin" || role === "member") {
    body.role = role;
  }
  if (active === "true" || active === "false") {
    body.active = active === "true";
  }
  const result = await apiSend("PATCH", "/admin/access", body);
  if (!result.ok) {
    fail(result.detail);
  }
  revalidatePath("/admin/acceso");
}
